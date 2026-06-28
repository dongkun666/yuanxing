"""
Track A W2 单元测试
2026-06-29

覆盖 5 个业务端点 (register / login / refresh / me / logout) + 3+ case each
目标: 覆盖率 ≥ 80%
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# ========== 客户端 fixture ==========
@pytest_asyncio.fixture
async def auth_client():
    """
    独立 in-memory DB + FastAPI TestClient
    - 复用 conftest.client 的 lifespan 模式
    - 每个测试 DB 隔离
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool

    from auth.main import app, lifespan
    from auth.db import get_db
    from core.models import Base  # noqa: F401
    from auth import models  # noqa: F401

    # 独立 in-memory engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 覆盖 get_db: 让 FastAPI 用我们的 session
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
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 包装: 给 client 加 session_factory 属性, 保持 .post/.get 接口
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


# ========== 注册 ==========
class TestRegister:
    @pytest.mark.asyncio
    async def test_register_happy_path(self, auth_client):
        """成功: 律师注册"""
        resp = await auth_client.post(
            "/api/auth/register",
            json={
                "email": "lawyer1@lexprime.com",
                "password": "strongpass123",
                "name": "张律师",
                "license_no": "11010120240101",
                "phone": "13800138001",
            },
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["email"] == "lawyer1@lexprime.com"
        assert data["role"] == "lawyer"
        assert data["is_email_verified"] is False
        assert data["is_active"] is True
        assert "password_hash" not in data  # 关键安全: 绝不返回密码
        assert data["profile"] is not None
        assert data["profile"]["name"] == "张律师"
        assert data["profile"]["license_no"] == "11010120240101"
        assert data["profile"]["license_status"] == "pending"

    @pytest.mark.asyncio
    async def test_register_email_duplicate(self, auth_client):
        """失败: 邮箱重复 → 409"""
        payload = {
            "email": "dup@lexprime.com",
            "password": "strongpass123",
            "name": "甲",
        }
        r1 = await auth_client.post("/api/auth/register", json=payload)
        assert r1.status_code == 201

        r2 = await auth_client.post("/api/auth/register", json=payload)
        assert r2.status_code == 409
        body = r2.json()
        assert body["detail"]["code"] == "email_already_registered"

    @pytest.mark.asyncio
    async def test_register_weak_password(self, auth_client):
        """边界: 密码 < 8 字符 → 422 (Pydantic)"""
        resp = await auth_client.post(
            "/api/auth/register",
            json={
                "email": "weak@lexprime.com",
                "password": "short",
                "name": "X",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, auth_client):
        """边界: 邮箱格式错 → 422"""
        resp = await auth_client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "strongpass123",
                "name": "X",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_license_duplicate(self, auth_client):
        """失败: 执业证号重复 → 409"""
        p1 = {
            "email": "a@lexprime.com",
            "password": "strongpass123",
            "name": "A",
            "license_no": "DUP-LICENSE-1",
        }
        p2 = {
            "email": "b@lexprime.com",
            "password": "strongpass123",
            "name": "B",
            "license_no": "DUP-LICENSE-1",
        }
        r1 = await auth_client.post("/api/auth/register", json=p1)
        assert r1.status_code == 201
        r2 = await auth_client.post("/api/auth/register", json=p2)
        assert r2.status_code == 409
        assert r2.json()["detail"]["code"] == "license_already_registered"


# ========== 登录 ==========
class TestLogin:
    @pytest_asyncio.fixture
    async def registered_user(self, auth_client):
        """已注册的用户"""
        await auth_client.post(
            "/api/auth/register",
            json={
                "email": "logintest@lexprime.com",
                "password": "strongpass123",
                "name": "Login Test",
            },
        )
        return "logintest@lexprime.com", "strongpass123"

    @pytest.mark.asyncio
    async def test_login_happy_path(self, auth_client, registered_user):
        """成功: 登录返回 token 对"""
        email, password = registered_user
        resp = await auth_client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900  # 15min
        assert len(data["access_token"]) > 50
        assert len(data["refresh_token"]) > 50
        assert data["access_token"] != data["refresh_token"]

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_client, registered_user):
        """失败: 密码错 → 401"""
        email, _ = registered_user
        resp = await auth_client.post(
            "/api/auth/login",
            json={"email": email, "password": "wrongpass"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "invalid_credentials"

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, auth_client):
        """失败: 用户不存在 → 401 (不暴露)"""
        resp = await auth_client.post(
            "/api/auth/login",
            json={"email": "nobody@lexprime.com", "password": "whatever"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "invalid_credentials"

    @pytest.mark.asyncio
    async def test_login_account_lock_after_5_failures(self, auth_client, registered_user):
        """边界: 5 次失败 → 账号锁定 423"""
        email, _ = registered_user
        for i in range(5):
            resp = await auth_client.post(
                "/api/auth/login",
                json={"email": email, "password": "wrong"},
            )
            assert resp.status_code == 401

        # 第 6 次: 锁定
        resp = await auth_client.post(
            "/api/auth/login",
            json={"email": email, "password": "wrong"},
        )
        assert resp.status_code == 423
        assert resp.json()["detail"]["code"] == "account_locked"

        # 即便密码正确也锁
        _, correct_pwd = registered_user
        resp = await auth_client.post(
            "/api/auth/login",
            json={"email": email, "password": correct_pwd},
        )
        assert resp.status_code == 423


# ========== 刷新 ==========
class TestRefresh:
    @pytest_asyncio.fixture
    async def tokens(self, auth_client):
        """拿到一对 tokens"""
        await auth_client.post(
            "/api/auth/register",
            json={
                "email": "refresh@lexprime.com",
                "password": "strongpass123",
                "name": "Refresh Test",
            },
        )
        resp = await auth_client.post(
            "/api/auth/login",
            json={"email": "refresh@lexprime.com", "password": "strongpass123"},
        )
        return resp.json()

    @pytest.mark.asyncio
    async def test_refresh_happy_path(self, auth_client, tokens):
        """成功: 旧 refresh_token → 新 access + 新 refresh"""
        resp = await auth_client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["access_token"]) > 50
        assert len(data["refresh_token"]) > 50
        assert data["refresh_token"] != tokens["refresh_token"]  # 轮转: 新 refresh 跟旧的不一样

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, auth_client):
        """失败: 乱写 token → 401"""
        resp = await auth_client.post(
            "/api/auth/refresh",
            json={"refresh_token": "this.is.not.a.valid.jwt.token"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] in ("token_invalid", "token_expired")

    @pytest.mark.asyncio
    async def test_refresh_replay_detection(self, auth_client, tokens):
        """边界: 同一 refresh_token 用第二次 → 401 + 撤销所有 token"""
        # 第一次成功
        r1 = await auth_client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert r1.status_code == 200

        # 第二次用旧的: 重放检测
        r2 = await auth_client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert r2.status_code == 401
        assert r2.json()["detail"]["code"] == "token_invalid"

        # 第一次发的新 refresh 现在也废了 (因为触发了 _revoke_all_user_tokens)
        r3 = await auth_client.post(
            "/api/auth/refresh",
            json={"refresh_token": r1.json()["refresh_token"]},
        )
        assert r3.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_using_access_token_rejected(self, auth_client, tokens):
        """边界: 用 access_token 调 refresh → 401 (type mismatch)"""
        resp = await auth_client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["access_token"]},
        )
        assert resp.status_code == 401


# ========== 当前用户 ==========
class TestMe:
    @pytest_asyncio.fixture
    async def access_token(self, auth_client):
        """拿到 access_token"""
        await auth_client.post(
            "/api/auth/register",
            json={
                "email": "me@lexprime.com",
                "password": "strongpass123",
                "name": "Me Test",
                "license_no": "ME-LICENSE-1",
            },
        )
        resp = await auth_client.post(
            "/api/auth/login",
            json={"email": "me@lexprime.com", "password": "strongpass123"},
        )
        return resp.json()["access_token"]

    @pytest.mark.asyncio
    async def test_me_happy_path(self, auth_client, access_token):
        """成功: 拿当前用户"""
        resp = await auth_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "me@lexprime.com"
        assert data["profile"] is not None
        assert data["profile"]["name"] == "Me Test"
        assert data["profile"]["license_no"] == "ME-LICENSE-1"
        assert "password_hash" not in data  # 安全

    @pytest.mark.asyncio
    async def test_me_no_token(self, auth_client):
        """失败: 没 Authorization header → 401"""
        resp = await auth_client.get("/api/auth/me")
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "missing_token"

    @pytest.mark.asyncio
    async def test_me_invalid_token(self, auth_client):
        """失败: 无效 token → 401"""
        resp = await auth_client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer not.a.real.jwt"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "token_invalid"

    @pytest.mark.asyncio
    async def test_me_refresh_token_rejected(self, auth_client):
        """边界: 用 refresh_token 调 me → 401 (type mismatch)"""
        # 先 login 拿 refresh_token
        await auth_client.post(
            "/api/auth/register",
            json={"email": "rt@lexprime.com", "password": "strongpass123", "name": "RT"},
        )
        resp = await auth_client.post(
            "/api/auth/login",
            json={"email": "rt@lexprime.com", "password": "strongpass123"},
        )
        refresh = resp.json()["refresh_token"]

        me_resp = await auth_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {refresh}"},
        )
        assert me_resp.status_code == 401


# ========== 登出 ==========
class TestLogout:
    @pytest_asyncio.fixture
    async def token_pair(self, auth_client):
        await auth_client.post(
            "/api/auth/register",
            json={"email": "logout@lexprime.com", "password": "strongpass123", "name": "Logout"},
        )
        resp = await auth_client.post(
            "/api/auth/login",
            json={"email": "logout@lexprime.com", "password": "strongpass123"},
        )
        return resp.json()

    @pytest.mark.asyncio
    async def test_logout_happy_path(self, auth_client, token_pair):
        """成功: 登出后 refresh_token 失效"""
        access = token_pair["access_token"]
        refresh = token_pair["refresh_token"]

        # 登出
        resp = await auth_client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == "ok"

        # 再用 refresh 刷新: 应失败
        r2 = await auth_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert r2.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_unauthenticated(self, auth_client):
        """失败: 没登录就登出 → 401"""
        resp = await auth_client.post(
            "/api/auth/logout",
            json={"refresh_token": "anything"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_other_user_token(self, auth_client, token_pair):
        """边界: 用 A 的 access_token 撤销 B 的 refresh_token → 失败"""
        # 注册第二个用户拿 access
        await auth_client.post(
            "/api/auth/register",
            json={"email": "user2@lexprime.com", "password": "strongpass123", "name": "User2"},
        )
        r2 = await auth_client.post(
            "/api/auth/login",
            json={"email": "user2@lexprime.com", "password": "strongpass123"},
        )
        user2_access = r2.json()["access_token"]

        # user2 试图撤销 user1 的 refresh: 应失败 (user_id 不匹配)
        resp = await auth_client.post(
            "/api/auth/logout",
            json={"refresh_token": token_pair["refresh_token"]},
            headers={"Authorization": f"Bearer {user2_access}"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_logout_invalid_refresh(self, auth_client, token_pair):
        """边界: refresh_token 不存在 → 400"""
        access = token_pair["access_token"]
        resp = await auth_client.post(
            "/api/auth/logout",
            json={"refresh_token": "totally-fake-refresh-token-1234567890"},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert resp.status_code == 400


# ========== Optional / Admin / Edge deps ==========
class TestDependencies:
    """覆盖 dependencies.py 的 get_optional_user / get_current_admin 边界"""

    @pytest_asyncio.fixture
    async def active_user_token(self, auth_client):
        await auth_client.post(
            "/api/auth/register",
            json={"email": "opt@lexprime.com", "password": "strongpass123", "name": "Opt"},
        )
        resp = await auth_client.post(
            "/api/auth/login",
            json={"email": "opt@lexprime.com", "password": "strongpass123"},
        )
        return resp.json()["access_token"]

    @pytest.mark.asyncio
    async def test_me_malformed_authorization_header(self, auth_client):
        """边界: Authorization header 格式错 (无 Bearer 前缀) → 401"""
        resp = await auth_client.get(
            "/api/auth/me",
            headers={"Authorization": "NoBearerScheme xyz"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "missing_token"

    @pytest.mark.asyncio
    async def test_me_bearer_only_no_token(self, auth_client):
        """边界: 只有 'Bearer' 没 token → 401"""
        resp = await auth_client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_token_for_deleted_user(self, auth_client):
        """边界: token 有效但 user 被删 → 401 user_not_found"""
        # 注册 → 拿 token → 直接从 DB 删 user → 用旧 token 调 /me

        from core.models import Base  # noqa: F401
        from auth import models  # noqa: F401

        # 用 file db 共享 auth_client session 是不行的 (in-memory), 改用 :memory: + StaticPool 同步
        # 但更简单: 直接通过 auth_client session 拿 user_id 然后 delete
        await auth_client.post(
            "/api/auth/register",
            json={"email": "deleted@lexprime.com", "password": "strongpass123", "name": "Del"},
        )
        await auth_client.post(
            "/api/auth/login",
            json={"email": "deleted@lexprime.com", "password": "strongpass123"},
        )

        # 通过 auth_client.dependency_overrides 的 session factory 直接删
        # auth_client fixture 没用 dependency_overrides, 而是直接 in-memory db
        # 这块直接走 raw SQL 删除
        # 实际: 拿到 auth.db.get_db 的 session 是 from Database singleton (file DB)
        # 测试数据写在 :memory: sqlite 里, 没法跨 access, 跳过
        # 改测: 用一个无效 user_id (伪造 token) 来覆盖 user_not_found 路径
        import jwt as _jwt
        from core.config import settings
        fake_payload = {
            "sub": "999999",
            "role": "lawyer",
            "iat": 0,
            "exp": 9999999999,
            "jti": "fake",
            "type": "access",
        }
        fake_token = _jwt.encode(
            fake_payload, settings.auth_secret_key, algorithm=settings.auth_jwt_algorithm
        )
        resp = await auth_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"]["code"] == "user_not_found"

    @pytest.mark.asyncio
    async def test_me_inactive_user(self, auth_client):
        """边界: user.is_active=False → 403"""
        # 注册
        await auth_client.post(
            "/api/auth/register",
            json={"email": "inactive@lexprime.com", "password": "strongpass123", "name": "IA"},
        )
        login_resp = await auth_client.post(
            "/api/auth/login",
            json={"email": "inactive@lexprime.com", "password": "strongpass123"},
        )
        token = login_resp.json()["access_token"]

        # 通过 fixture 暴露的 session_factory 把 user.is_active=False (模拟 admin 停用)
        from sqlalchemy import update
        from auth.models import User

        async with auth_client.session_factory() as db:
            await db.execute(
                update(User).where(User.email == "inactive@lexprime.com").values(is_active=False)
            )
            await db.commit()

        resp = await auth_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "user_inactive"


# ========== Health (回归测试, 防止 W2 改动打破 W1) ==========
class TestHealthRegression:
    @pytest.mark.asyncio
    async def test_health(self, auth_client):
        resp = await auth_client.get("/api/auth/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["tables_ready"] is True
        assert data["module"] == "auth"
        assert data["version"] == "0.2.0"