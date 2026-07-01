"""
TOTP 端点测试 (W3)
2026-06-29

覆盖:
- POST /api/auth/totp/setup     绑定第一步 (生成 secret + QR + backup codes)
- POST /api/auth/totp/verify    启用 2FA / 登录验证
- POST /api/auth/totp/disable   关闭 2FA
- backup code 一次性使用
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from auth.ratelimit import get_limiter
from auth.totp import (
    generate_totp_secret,
    provisioning_uri,
    qr_code_data_uri,
    verify_totp_code,
)


@pytest_asyncio.fixture
async def auth_client():
    """独立 in-memory DB + FastAPI TestClient (同 email_verify 测试模式)"""
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
        get_limiter().reset()
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


async def _register_and_login(client, email="lawyer@lexprime.com", password="testpassword123"):
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


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ========== Unit Tests for helpers ==========
class TestTotpHelpers:
    def test_generate_secret(self):
        s = generate_totp_secret()
        assert len(s) >= 16
        # base32 chars
        import string
        valid_chars = string.ascii_uppercase + "234567"
        assert all(c in valid_chars for c in s)

    def test_provisioning_uri(self):
        uri = provisioning_uri("JBSWY3DPEHPK3PXP", "test@example.com")
        assert uri.startswith("otpauth://totp/")
        assert "test%40example.com" in uri or "test@example.com" in uri
        assert "LexPrime" in uri

    def test_qr_code_data_uri(self):
        uri = provisioning_uri("JBSWY3DPEHPK3PXP", "test@example.com")
        qr = qr_code_data_uri(uri)
        assert qr.startswith("data:image/png;base64,")
        assert len(qr) > 100  # 实际 base64 字符串

    def test_verify_totp_code_correct(self):
        secret = generate_totp_secret()
        import pyotp
        code = pyotp.TOTP(secret).now()
        assert verify_totp_code(secret, code) is True

    def test_verify_totp_code_wrong(self):
        secret = generate_totp_secret()
        assert verify_totp_code(secret, "000000") is False
        assert verify_totp_code(secret, "abcdef") is False
        assert verify_totp_code(secret, "") is False


# ========== Endpoint Tests ==========
@pytest.mark.asyncio
class TestTotpSetup:
    """POST /api/auth/totp/setup"""

    async def test_setup_returns_secret_qr_backup_codes(self, auth_client):
        token = await _register_and_login(auth_client)
        resp = await auth_client.post(
            "/api/auth/totp/setup",
            json={"password": "testpassword123"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "secret" in data and len(data["secret"]) >= 16
        assert data["qr_code_data_uri"].startswith("data:image/png;base64,")
        assert data["provisioning_uri"].startswith("otpauth://totp/")
        assert len(data["backup_codes"]) == 10
        assert all(len(c) == 8 for c in data["backup_codes"])
        # setup 阶段 is_2fa_enabled 应该是 False (要 verify 后才 True)
        assert data["is_2fa_enabled"] is False

    async def test_setup_wrong_password(self, auth_client):
        token = await _register_and_login(auth_client)
        resp = await auth_client.post(
            "/api/auth/totp/setup",
            json={"password": "wrongpassword"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "invalid_credentials"

    async def test_setup_requires_login(self, auth_client):
        resp = await auth_client.post(
            "/api/auth/totp/setup",
            json={"password": "testpassword123"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestTotpVerify:
    """POST /api/auth/totp/verify (启用 2FA / 登录验证)"""

    async def test_verify_enables_2fa(self, auth_client):
        """setup 后 verify 启用 2FA"""
        token = await _register_and_login(auth_client)
        # setup
        setup_resp = await auth_client.post(
            "/api/auth/totp/setup",
            json={"password": "testpassword123"},
            headers=_auth_header(token),
        )
        secret = setup_resp.json()["secret"]

        # 用 secret 生成当前 code
        import pyotp
        code = pyotp.TOTP(secret).now()

        # verify
        verify_resp = await auth_client.post(
            "/api/auth/totp/verify",
            json={"code": code},
            headers=_auth_header(token),
        )
        assert verify_resp.status_code == 200, verify_resp.text
        data = verify_resp.json()
        assert data["verified"] is True
        assert data["is_2fa_enabled"] is True
        assert data["method"] == "totp"

    async def test_verify_wrong_code(self, auth_client):
        token = await _register_and_login(auth_client)
        # setup
        await auth_client.post(
            "/api/auth/totp/setup",
            json={"password": "testpassword123"},
            headers=_auth_header(token),
        )

        verify_resp = await auth_client.post(
            "/api/auth/totp/verify",
            json={"code": "000000"},  # 错
            headers=_auth_header(token),
        )
        assert verify_resp.status_code == 400
        assert verify_resp.json()["detail"]["code"] == "invalid_totp_code"

    async def test_verify_already_enabled_blocks_setup(self, auth_client):
        """已启用 2FA 再 setup → 409"""
        token = await _register_and_login(auth_client)
        setup_resp = await auth_client.post(
            "/api/auth/totp/setup",
            json={"password": "testpassword123"},
            headers=_auth_header(token),
        )
        secret = setup_resp.json()["secret"]
        import pyotp
        code = pyotp.TOTP(secret).now()
        await auth_client.post(
            "/api/auth/totp/verify",
            json={"code": code},
            headers=_auth_header(token),
        )

        # 第二次 setup 应该 409
        resp = await auth_client.post(
            "/api/auth/totp/setup",
            json={"password": "testpassword123"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 409
        assert resp.json()["detail"]["code"] == "totp_already_enabled"

    async def test_verify_backup_code_login(self, auth_client):
        """登录验证场景: backup code 一次性使用"""
        token = await _register_and_login(auth_client)
        setup_resp = await auth_client.post(
            "/api/auth/totp/setup",
            json={"password": "testpassword123"},
            headers=_auth_header(token),
        )
        secret = setup_resp.json()["secret"]
        backup_codes = setup_resp.json()["backup_codes"]

        # 用 TOTP 启用 2FA
        import pyotp
        code = pyotp.TOTP(secret).now()
        await auth_client.post(
            "/api/auth/totp/verify",
            json={"code": code},
            headers=_auth_header(token),
        )

        # 用 backup code 验证 (登录场景)
        backup = backup_codes[0]
        verify_resp = await auth_client.post(
            "/api/auth/totp/verify",
            json={"code": backup},
            headers=_auth_header(token),
        )
        assert verify_resp.status_code == 200, verify_resp.text
        data = verify_resp.json()
        assert data["verified"] is True
        assert data["method"] == "backup_code"

        # 第二次用同 backup code → 应失败 (一次性)
        verify_resp2 = await auth_client.post(
            "/api/auth/totp/verify",
            json={"code": backup},
            headers=_auth_header(token),
        )
        assert verify_resp2.status_code == 401
        assert verify_resp2.json()["detail"]["code"] == "invalid_totp_code"


@pytest.mark.asyncio
class TestTotpDisable:
    """POST /api/auth/totp/disable"""

    async def test_disable_with_correct_code(self, auth_client):
        token = await _register_and_login(auth_client)
        setup_resp = await auth_client.post(
            "/api/auth/totp/setup",
            json={"password": "testpassword123"},
            headers=_auth_header(token),
        )
        secret = setup_resp.json()["secret"]
        backup_codes = setup_resp.json()["backup_codes"]
        import pyotp
        code = pyotp.TOTP(secret).now()

        # 启用
        await auth_client.post(
            "/api/auth/totp/verify",
            json={"code": code},
            headers=_auth_header(token),
        )

        # 用 backup code 关闭
        disable_resp = await auth_client.post(
            "/api/auth/totp/disable",
            json={"password": "testpassword123", "code": backup_codes[0]},
            headers=_auth_header(token),
        )
        assert disable_resp.status_code == 200, disable_resp.text

        # me 应该 is_2fa_enabled=False
        me_resp = await auth_client.get(
            "/api/auth/me",
            headers=_auth_header(token),
        )
        assert me_resp.json()["is_2fa_enabled"] is False

    async def test_disable_wrong_password(self, auth_client):
        token = await _register_and_login(auth_client)
        setup_resp = await auth_client.post(
            "/api/auth/totp/setup",
            json={"password": "testpassword123"},
            headers=_auth_header(token),
        )
        secret = setup_resp.json()["secret"]
        backup_codes = setup_resp.json()["backup_codes"]
        import pyotp
        await auth_client.post(
            "/api/auth/totp/verify",
            json={"code": pyotp.TOTP(secret).now()},
            headers=_auth_header(token),
        )

        resp = await auth_client.post(
            "/api/auth/totp/disable",
            json={"password": "wrongpass", "code": backup_codes[0]},
            headers=_auth_header(token),
        )
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "invalid_credentials"

    async def test_disable_not_enabled(self, auth_client):
        """没启用 2FA 就 disable → 400"""
        token = await _register_and_login(auth_client)
        resp = await auth_client.post(
            "/api/auth/totp/disable",
            json={"password": "testpassword123", "code": "123456"},
            headers=_auth_header(token),
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["code"] == "totp_not_enabled"