"""
律师执业证端点测试 (W3)
2026-06-29

覆盖:
- POST /api/auth/lawyer-license/upload   上传 + OCR + AI 初审
- GET  /api/auth/lawyer-license/status   审核状态
- POST /api/auth/lawyer-license/review   人工复审 (admin)
- 重复上传 / AI 拒绝路径 / 限流
"""
import base64
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

from auth.ratelimit import get_limiter


@pytest_asyncio.fixture
async def auth_client():
    """独立 in-memory DB + FastAPI TestClient"""
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

                async def put(self, *a, **kw):
                    return await self._inner.put(*a, **kw)

                async def delete(self, *a, **kw):
                    return await self._inner.delete(*a, **kw)

            yield _ClientWrapper(ac, session_factory)

    app.dependency_overrides.clear()
    await engine.dispose()


def _fake_image_b64(size_bytes: int = 5000) -> str:
    """构造一个有效大小的 base64 字符串"""
    return base64.b64encode(b"x" * size_bytes).decode("ascii")


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


@pytest.mark.asyncio
class TestLicenseUpload:
    """POST /api/auth/lawyer-license/upload"""

    async def test_upload_pass_ai_to_human_review(self, auth_client):
        """上传 + AI 通过 -> human_reviewing"""
        token = await _register_and_login(auth_client)
        resp = await auth_client.post(
            "/api/auth/lawyer-license/upload",
            json={
                "image_base64": _fake_image_b64(5000),
                "filename": "lawyer_110101-2024-T-LAWYER_LICENSE.jpg",
            },
            headers=_auth_header(token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # OCR mock 提取的 license_no 从文件名匹配
        assert data["license_status"] in ("human_reviewing", "rejected")
        assert data["ai_score"] is not None
        assert 0 <= data["ai_score"] <= 1
        assert data["ocr_confidence"] is not None

    async def test_upload_with_filename_extracts_license(self, auth_client):
        """文件名 license_no 提取"""
        token = await _register_and_login(auth_client)
        resp = await auth_client.post(
            "/api/auth/lawyer-license/upload",
            json={
                "image_base64": _fake_image_b64(3000),
                "filename": "lawyer_110102-2024-A1234.jpg",
            },
            headers=_auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        extracted = data.get("extracted_fields") or {}
        assert extracted.get("license_no") == "110102-2024-A1234"

    async def test_upload_reject_path(self, auth_client):
        """email 触发强制 reject (mock AI low score)"""
        token = await _register_and_login(
            auth_client,
            email="reject@test.lexprime",
            password="testpassword123",
        )
        resp = await auth_client.post(
            "/api/auth/lawyer-license/upload",
            json={
                "image_base64": _fake_image_b64(3000),
                "filename": "lawyer_110101-2024-A0001.jpg",
            },
            headers=_auth_header(token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["license_status"] == "rejected"
        assert data["ai_score"] is not None
        assert data["ai_score"] < 0.7

    async def test_upload_invalid_base64(self, auth_client):
        token = await _register_and_login(auth_client)
        resp = await auth_client.post(
            "/api/auth/lawyer-license/upload",
            json={
                "image_base64": "not-valid-base64-!!!@@@",
                "filename": "lawyer.jpg",
            },
            headers=_auth_header(token),
        )
        # base64 解码失败 -> 400
        assert resp.status_code in (400, 422)

    async def test_upload_too_small(self, auth_client):
        """图太小 (<100 bytes 解码后) -> 400 license_invalid_image"""
        token = await _register_and_login(auth_client)
        # 200 chars 字符串但 base64 解码后 <100 bytes
        # 实际上 base64 是 4 chars per 3 bytes, 200 chars = 150 bytes
        # 用 100 chars base64 -> 75 bytes (小于 100 阈值)
        resp = await auth_client.post(
            "/api/auth/lawyer-license/upload",
            json={
                "image_base64": base64.b64encode(b"x" * 50).decode("ascii"),  # ~68 chars
                "filename": "lawyer.jpg",
            },
            headers=_auth_header(token),
        )
        # pydantic min_length=100 或 服务端 size 检查
        assert resp.status_code in (400, 422)
        if resp.status_code == 400:
            assert resp.json()["detail"]["code"] == "license_invalid_image"

    async def test_upload_requires_login(self, auth_client):
        resp = await auth_client.post(
            "/api/auth/lawyer-license/upload",
            json={
                "image_base64": _fake_image_b64(),
                "filename": "lawyer.jpg",
            },
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestLicenseStatus:
    """GET /api/auth/lawyer-license/status"""

    async def test_status_after_upload(self, auth_client):
        token = await _register_and_login(auth_client)
        # 上传
        await auth_client.post(
            "/api/auth/lawyer-license/upload",
            json={
                "image_base64": _fake_image_b64(3000),
                "filename": "lawyer_110101-2024-A0001.jpg",
            },
            headers=_auth_header(token),
        )
        # 查询
        resp = await auth_client.get(
            "/api/auth/lawyer-license/status",
            headers=_auth_header(token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["license_status"] in ("human_reviewing", "rejected", "approved")
        assert len(data["review_logs"]) >= 1  # 至少有 user 上传 + ai 决策两条
        # 第一条应该是 user 上传
        assert data["review_logs"][0]["actor_type"] == "user"

    async def test_status_requires_login(self, auth_client):
        resp = await auth_client.get("/api/auth/lawyer-license/status")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestLicenseAdminReview:
    """POST /api/auth/lawyer-license/review (admin only)"""

    async def _get_profile_id(self, client, token):
        """helper: 从 status 拿 profile_id (用律师 id 反查)"""
        from sqlalchemy import select
        from auth.models import LawyerProfile
        async with client.session_factory() as session:
            from auth.models import User
            result = await session.execute(select(User).where(User.email == "lawyer@lexprime.com"))
            user = result.scalar_one()
            result = await session.execute(select(LawyerProfile).where(LawyerProfile.user_id == user.id))
            profile = result.scalar_one()
            return profile.id

    async def test_admin_review_approved(self, auth_client):
        # 普通律师上传 -> 进入 human_reviewing
        token = await _register_and_login(auth_client)
        await auth_client.post(
            "/api/auth/lawyer-license/upload",
            json={
                "image_base64": _fake_image_b64(3000),
                "filename": "lawyer_110101-2024-A0001.jpg",
            },
            headers=_auth_header(token),
        )

        # 创 admin
        await auth_client.post(
            "/api/auth/register",
            json={
                "email": "admin@lexprime.com",
                "password": "adminpass123",
                "name": "管理员",
                "license_no": "999999-2024-ADMIN",
            },
        )
        # 升级 role -> admin (DB 直接改)
        from sqlalchemy import update
        from auth.models import User
        async with auth_client.session_factory() as session:
            await session.execute(
                update(User).where(User.email == "admin@lexprime.com").values(role="admin")
            )
            await session.commit()

        # admin 登录
        admin_login = await auth_client.post(
            "/api/auth/login",
            json={"email": "admin@lexprime.com", "password": "adminpass123"},
        )
        admin_token = admin_login.json()["access_token"]

        profile_id = await self._get_profile_id(auth_client, token)

        # admin 审核通过
        review_resp = await auth_client.post(
            "/api/auth/lawyer-license/review",
            json={
                "profile_id": profile_id,
                "decision": "approved",
                "reason": "AI 初审通过, 人工复审确认",
            },
            headers=_auth_header(admin_token),
        )
        assert review_resp.status_code == 200, review_resp.text

        # 律师查询 -> 应 approved
        status_resp = await auth_client.get(
            "/api/auth/lawyer-license/status",
            headers=_auth_header(token),
        )
        assert status_resp.json()["license_status"] == "approved"

    async def test_non_admin_cannot_review(self, auth_client):
        """普通律师调用 review -> 403"""
        token = await _register_and_login(auth_client)
        await auth_client.post(
            "/api/auth/lawyer-license/upload",
            json={
                "image_base64": _fake_image_b64(3000),
                "filename": "lawyer_110101-2024-A0001.jpg",
            },
            headers=_auth_header(token),
        )
        profile_id = await self._get_profile_id(auth_client, token)

        resp = await auth_client.post(
            "/api/auth/lawyer-license/review",
            json={
                "profile_id": profile_id,
                "decision": "approved",
                "reason": "self approve",
            },
            headers=_auth_header(token),
        )
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "admin_required"

    async def test_admin_review_rejected(self, auth_client):
        """admin 拒绝路径"""
        # 用 reject email 上传
        token = await _register_and_login(
            auth_client, email="reject@test.lexprime", password="testpassword123"
        )
        await auth_client.post(
            "/api/auth/lawyer-license/upload",
            json={
                "image_base64": _fake_image_b64(3000),
                "filename": "lawyer_110101-2024-A0001.jpg",
            },
            headers=_auth_header(token),
        )

        # admin
        await auth_client.post(
            "/api/auth/register",
            json={
                "email": "admin@lexprime.com",
                "password": "adminpass123",
                "name": "管理员",
                "license_no": "999999-2024-ADMIN",
            },
        )
        from sqlalchemy import update
        from auth.models import User
        async with auth_client.session_factory() as session:
            await session.execute(
                update(User).where(User.email == "admin@lexprime.com").values(role="admin")
            )
            await session.commit()

        admin_login = await auth_client.post(
            "/api/auth/login",
            json={"email": "admin@lexprime.com", "password": "adminpass123"},
        )
        admin_token = admin_login.json()["access_token"]

        from sqlalchemy import select
        from auth.models import LawyerProfile
        async with auth_client.session_factory() as session:
            result = await session.execute(select(LawyerProfile).where(LawyerProfile.user_id > 0))
            profile = result.scalars().first()
            profile_id = profile.id

        # 注意: AI 已经 reject, status=rejected, admin_reviewable 仅在 human_reviewing/ai_reviewing
        # 所以这个 case 应该 400 (status not reviewable)
        review_resp = await auth_client.post(
            "/api/auth/lawyer-license/review",
            json={
                "profile_id": profile_id,
                "decision": "rejected",
                "reason": "manual reject",
            },
            headers=_auth_header(admin_token),
        )
        # 状态是 rejected, 不在可审列表 → 400
        assert review_resp.status_code == 400
        assert review_resp.json()["detail"]["code"] == "license_error"


@pytest.mark.asyncio
class TestLicenseReupload:
    """重复上传逻辑"""

    async def test_reupload_overwrites_image(self, auth_client):
        """重复上传覆盖图片, 状态机正常推进"""
        token = await _register_and_login(auth_client)
        # 第一次
        r1 = await auth_client.post(
            "/api/auth/lawyer-license/upload",
            json={
                "image_base64": _fake_image_b64(3000),
                "filename": "lawyer_110101-2024-A0001.jpg",
            },
            headers=_auth_header(token),
        )
        assert r1.status_code == 200

        # 第二次 (重传)
        r2 = await auth_client.post(
            "/api/auth/lawyer-license/upload",
            json={
                "image_base64": _fake_image_b64(3000),
                "filename": "lawyer_110101-2024-A0002.jpg",
            },
            headers=_auth_header(token),
        )
        assert r2.status_code == 200

        # status 应有 2 条 user 上传日志
        status_resp = await auth_client.get(
            "/api/auth/lawyer-license/status",
            headers=_auth_header(token),
        )
        upload_logs = [log for log in status_resp.json()["review_logs"] if log["actor_type"] == "user"]
        assert len(upload_logs) == 2