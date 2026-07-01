"""
email_verify 端点测试 (W3)
2026-06-29

覆盖:
- POST /api/auth/email/send   发送验证邮件
- POST /api/auth/email/verify 验证 token
- 过期 / 已用 / 不存在 token
- 限流
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone

from auth.models import EmailVerification
from auth.ratelimit import get_limiter


# ========== 客户端 fixture (W2 test_auth_endpoints.py 同款, 独立 in-memory DB) ==========
@pytest_asyncio.fixture
async def auth_client():
    """
    独立 in-memory DB + FastAPI TestClient
    - 复用 conftest.client 的 lifespan 模式
    - 每个测试 DB 隔离
    - 通过 client.session_factory 访问底层 session (用于改 DB 模拟状态)
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from httpx import AsyncClient, ASGITransport

    from auth.main import app, lifespan
    from auth.db import get_db
    from core.models import Base  # noqa: F401
    from auth import models  # noqa: F401

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def _get_db_override():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _get_db_override

    async with lifespan(app):
        get_limiter().reset()  # 每个测试重置限流器
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            class _ClientWrapper:
                def __init__(self, inner, sf):
                    self._inner = inner
                    self.session_factory = sf

                async def post(self, *a, **kw):
                    return await self._inner.post(*a, **kw)

                async def get(self, *a, **kw):
                    return await self._inner.get(*a, **kw)

                async def request(self, *a, **kw):
                    return await self._inner.request(*a, **kw)

            yield _ClientWrapper(ac, session_factory)

    app.dependency_overrides.clear()
    await engine.dispose()


# ========== helpers ==========
async def _register_and_login(client, email="lawyer@lexprime.com", password="testpassword123"):
    """注册 + 登录, 返回 access_token"""
    reg = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "name": "测试律师",
            "license_no": f"110101-2024-T-{email.split('@')[0][:4].upper()}",
        },
    )
    assert reg.status_code == 201, reg.text
    login = await client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
class TestEmailSend:
    """POST /api/auth/email/send"""

    async def test_send_returns_dev_token(self, auth_client):
        """登录用户发送, 返回 dev_only_token"""
        token = await _register_and_login(auth_client)
        resp = await auth_client.post(
            "/api/auth/email/send",
            json={"purpose": "verify_email"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["code"] == "ok"
        assert "dev_only_token" in data
        assert len(data["dev_only_token"]) >= 32

    async def test_send_revokes_previous_token(self, auth_client):
        """重复发送会撤销旧 token"""
        token = await _register_and_login(auth_client)
        resp1 = await auth_client.post(
            "/api/auth/email/send",
            json={"purpose": "verify_email"},
            headers=_auth_header(token),
        )
        token1 = resp1.json()["dev_only_token"]

        resp2 = await auth_client.post(
            "/api/auth/email/send",
            json={"purpose": "verify_email"},
            headers=_auth_header(token),
        )
        token2 = resp2.json()["dev_only_token"]

        assert token1 != token2

        # 第一个 token 验证应失败 (revoked)
        verify_resp = await auth_client.post(
            "/api/auth/email/verify",
            json={"token": token1},
        )
        assert verify_resp.status_code == 400
        assert verify_resp.json()["detail"]["code"] == "invalid_verification_token"

    async def test_send_requires_login(self, auth_client):
        """未登录 401"""
        resp = await auth_client.post(
            "/api/auth/email/send",
            json={"purpose": "verify_email"},
        )
        assert resp.status_code == 401

    async def test_send_invalid_purpose(self, auth_client):
        """purpose 不在允许列表 → 422"""
        token = await _register_and_login(auth_client)
        resp = await auth_client.post(
            "/api/auth/email/send",
            json={"purpose": "evil_purpose"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 422  # pydantic validation


@pytest.mark.asyncio
class TestEmailVerify:
    """POST /api/auth/email/verify"""

    async def test_verify_success_marks_email_verified(self, auth_client):
        """验证成功 -> user.is_email_verified = True"""
        token = await _register_and_login(auth_client)
        send_resp = await auth_client.post(
            "/api/auth/email/send",
            json={"purpose": "verify_email"},
            headers=_auth_header(token),
        )
        email_token = send_resp.json()["dev_only_token"]

        verify_resp = await auth_client.post(
            "/api/auth/email/verify",
            json={"token": email_token},
        )
        assert verify_resp.status_code == 200, verify_resp.text
        data = verify_resp.json()
        assert data["is_email_verified"] is True
        assert data["email"] == "lawyer@lexprime.com"

    async def test_verify_invalid_token(self, auth_client):
        """token 不存在 → 400 invalid_verification_token"""
        resp = await auth_client.post(
            "/api/auth/email/verify",
            json={"token": "X" * 43},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["code"] == "invalid_verification_token"

    async def test_verify_expired_token(self, auth_client):
        """token 已过期 → 400 verification_token_expired"""
        token = await _register_and_login(auth_client)
        send_resp = await auth_client.post(
            "/api/auth/email/send",
            json={"purpose": "verify_email"},
            headers=_auth_header(token),
        )
        email_token = send_resp.json()["dev_only_token"]

        # 直接改 DB 把 expires_at 改成过去
        from sqlalchemy import update

        async with auth_client.session_factory() as session:
            await session.execute(
                update(EmailVerification)
                .values(expires_at=datetime.now(tz=timezone.utc) - timedelta(hours=1))
            )
            await session.commit()

        verify_resp = await auth_client.post(
            "/api/auth/email/verify",
            json={"token": email_token},
        )
        assert verify_resp.status_code == 400
        assert verify_resp.json()["detail"]["code"] == "verification_token_expired"

    async def test_verify_used_token(self, auth_client):
        """token 已用 → 400 verification_token_used"""
        token = await _register_and_login(auth_client)
        send_resp = await auth_client.post(
            "/api/auth/email/send",
            json={"purpose": "verify_email"},
            headers=_auth_header(token),
        )
        email_token = send_resp.json()["dev_only_token"]

        first = await auth_client.post("/api/auth/email/verify", json={"token": email_token})
        assert first.status_code == 200

        second = await auth_client.post("/api/auth/email/verify", json={"token": email_token})
        assert second.status_code == 400
        assert second.json()["detail"]["code"] == "verification_token_used"

    async def test_verify_empty_token(self, auth_client):
        """空 token → 422"""
        resp = await auth_client.post(
            "/api/auth/email/verify",
            json={"token": ""},
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestEmailVerifyRateLimit:
    """限流"""

    async def test_verify_rate_limited_after_threshold(self, auth_client):
        """超过 5 次/小时/IP → 429"""
        for i in range(5):
            r = await auth_client.post(
                "/api/auth/email/verify",
                json={"token": "X" * 43},
            )
            assert r.status_code == 400  # invalid token, 不限流
        # 第 6 次
        r = await auth_client.post(
            "/api/auth/email/verify",
            json={"token": "X" * 43},
        )
        assert r.status_code == 429
        assert r.json()["detail"]["code"] == "email_rate_limited"