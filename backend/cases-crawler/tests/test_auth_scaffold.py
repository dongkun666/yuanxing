"""
W1 脚手架测试
2026-06-28

覆盖:
1. 4 张表 (auth_users / auth_lawyer_profiles / auth_tokens / auth_otp_logs) 都能创建
2. SQLAlchemy 模型基本 CRUD (User / LawyerProfile / Token / OTPLog)
3. Pydantic schemas 字段校验 (EmailStr / pattern / 长度)
4. /api/auth/health 端点能返回
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, inspect

from auth.models import User, LawyerProfile, Token, OTPLog
from auth.schemas import (
    UserCreate,
    UserOut,
    LawyerProfileBase,
    LawyerProfileOut,
    OTPSendRequest,
    OTPVerifyRequest,
    HealthOut,
)


# ========== 1. 表创建 ==========
class TestTablesCreated:
    """验证 metadata.create_all 把 4 张表都建出来"""

    @pytest.mark.asyncio
    async def test_auth_users_table_exists(self, db_session):
        from core.db import Database
        # 拿 engine 通过 session 的 bind
        engine = db_session.bind
        async with engine.connect() as conn:
            def get_table_names(sync_conn):
                return set(inspect(sync_conn).get_table_names())
            tables = await conn.run_sync(get_table_names)
        assert "auth_users" in tables

    @pytest.mark.asyncio
    async def test_auth_lawyer_profiles_table_exists(self, db_session):
        engine = db_session.bind
        async with engine.connect() as conn:
            def get_table_names(sync_conn):
                return set(inspect(sync_conn).get_table_names())
            tables = await conn.run_sync(get_table_names)
        assert "auth_lawyer_profiles" in tables

    @pytest.mark.asyncio
    async def test_auth_tokens_table_exists(self, db_session):
        engine = db_session.bind
        async with engine.connect() as conn:
            def get_table_names(sync_conn):
                return set(inspect(sync_conn).get_table_names())
            tables = await conn.run_sync(get_table_names)
        assert "auth_tokens" in tables

    @pytest.mark.asyncio
    async def test_auth_otp_logs_table_exists(self, db_session):
        engine = db_session.bind
        async with engine.connect() as conn:
            def get_table_names(sync_conn):
                return set(inspect(sync_conn).get_table_names())
            tables = await conn.run_sync(get_table_names)
        assert "auth_otp_logs" in tables


# ========== 2. SQLAlchemy 模型 CRUD ==========
class TestUserModel:
    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        user = User(
            email="test@lexprime.com",
            password_hash="$2b$12$placeholder.hash.for.testing",
            role="lawyer",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        assert user.id is not None
        assert user.email == "test@lexprime.com"
        assert user.role == "lawyer"
        assert user.is_active is True
        assert user.is_email_verified is False
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_email_unique_constraint(self, db_session):
        from sqlalchemy.exc import IntegrityError
        u1 = User(email="dup@lexprime.com", password_hash="hash1")
        u2 = User(email="dup@lexprime.com", password_hash="hash2")
        db_session.add(u1)
        await db_session.commit()
        db_session.add(u2)
        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_query_user_by_email(self, db_session):
        u = User(email="find@lexprime.com", password_hash="hash")
        db_session.add(u)
        await db_session.commit()
        result = await db_session.execute(select(User).where(User.email == "find@lexprime.com"))
        fetched = result.scalar_one()
        assert fetched.id == u.id


class TestLawyerProfileModel:
    @pytest.mark.asyncio
    async def test_create_profile_1to1_user(self, db_session):
        user = User(email="lawyer@lexprime.com", password_hash="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = LawyerProfile(
            user_id=user.id,
            name="张三律师",
            license_no="11010120240101",
            specialties=["民商", "刑事"],
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        assert profile.id is not None
        assert profile.user_id == user.id
        assert profile.license_status == "pending"
        assert profile.specialties == ["民商", "刑事"]

    @pytest.mark.asyncio
    async def test_profile_via_user_relationship(self, db_session):
        user = User(email="rel@lexprime.com", password_hash="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        profile = LawyerProfile(user_id=user.id, name="李四")
        db_session.add(profile)
        await db_session.commit()

        # 显式 await refresh 加载 profile (避免 async 上下文 lazy load 报 MissingGreenlet)
        await db_session.refresh(user, attribute_names=["profile"])
        assert user.profile is not None
        assert user.profile.name == "李四"


class TestTokenModel:
    @pytest.mark.asyncio
    async def test_create_refresh_token(self, db_session):
        user = User(email="tok@lexprime.com", password_hash="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        now = datetime.now(timezone.utc)
        token = Token(
            user_id=user.id,
            token_hash="abc123def456" * 8,  # 64+ 字符占位
            token_type="refresh",
            device_info="MacBook Pro 16 / Chrome 125",
            ip_address="127.0.0.1",
            issued_at=now,
            expires_at=now + timedelta(days=7),
        )
        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        assert token.id is not None
        assert token.token_type == "refresh"
        assert token.revoked_at is None
        # SQLite 读回 datetime 是 naive, 统一转 naive 比较
        assert token.expires_at.replace(tzinfo=None) > now.replace(tzinfo=None)

    @pytest.mark.asyncio
    async def test_revoke_token(self, db_session):
        user = User(email="rev@lexprime.com", password_hash="hash")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = Token(
            user_id=user.id,
            token_hash="placeholder" * 20,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        # 撤销
        token.revoked_at = datetime.now(timezone.utc)
        token.revoked_reason = "logout"
        await db_session.commit()
        await db_session.refresh(token)

        assert token.revoked_at is not None
        assert token.revoked_reason == "logout"


class TestOTPLogModel:
    @pytest.mark.asyncio
    async def test_create_otp(self, db_session):
        now = datetime.now(timezone.utc)
        otp = OTPLog(
            target="otp@lexprime.com",
            target_type="email",
            purpose="register",
            code_hash="bcrypt_hash_placeholder",
            sent_to="otp@lexprime.com",
            expires_at=now + timedelta(minutes=10),
            ip_address="127.0.0.1",
        )
        db_session.add(otp)
        await db_session.commit()
        await db_session.refresh(otp)

        assert otp.id is not None
        assert otp.purpose == "register"
        assert otp.attempt_count == 0
        assert otp.max_attempts == 5
        assert otp.consumed_at is None

    @pytest.mark.asyncio
    async def test_otp_attempt_count_increment(self, db_session):
        otp = OTPLog(
            target="att@lexprime.com",
            target_type="email",
            purpose="login",
            code_hash="hash",
            sent_to="att@lexprime.com",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        db_session.add(otp)
        await db_session.commit()

        # 模拟 3 次失败
        otp.attempt_count += 1
        otp.attempt_count += 1
        otp.attempt_count += 1
        await db_session.commit()
        await db_session.refresh(otp)

        assert otp.attempt_count == 3


# ========== 3. Pydantic schemas 校验 ==========
class TestSchemas:
    def test_user_create_validates_email(self):
        with pytest.raises(Exception):  # ValidationError
            UserCreate(email="not-an-email", password="validpass123")

    def test_user_create_min_password_length(self):
        with pytest.raises(Exception):
            UserCreate(email="ok@lex.com", password="short")  # < 8

    def test_user_create_happy_path(self):
        u = UserCreate(email="ok@lexprime.com", password="validpass123")
        assert u.email == "ok@lexprime.com"
        assert u.role == "lawyer"
        assert u.subscription_tier == "trial"

    def test_otp_send_request_pattern(self):
        # target_type 必须是 email 或 phone
        with pytest.raises(Exception):
            OTPSendRequest(
                target="x@x.com",
                target_type="invalid",  # type: ignore[arg-type]
                purpose="register",
            )

    def test_otp_purpose_pattern(self):
        with pytest.raises(Exception):
            OTPSendRequest(
                target="x@x.com",
                target_type="email",
                purpose="hacker_purpose",  # type: ignore[arg-type]
            )

    def test_otp_verify_code_length(self):
        # 4-8 位
        with pytest.raises(Exception):
            OTPVerifyRequest(
                target="x@x.com",
                target_type="email",
                purpose="register",
                code="ab",  # 太短
            )

    def test_lawyer_profile_name_required(self):
        with pytest.raises(Exception):
            LawyerProfileBase(name="")  # min_length=1 失败

    def test_health_out_default(self):
        h = HealthOut(tables_ready=True)
        assert h.status == "ok"
        assert h.module == "auth"
        assert h.version == "0.1.0"


# ========== 4. FastAPI 端点 ==========
class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client):
        resp = await client.get("/api/auth/health")
        # 端点会调 Database.init() → 内存 OK → 表创建 → tables_ready=True
        assert resp.status_code == 200
        data = resp.json()
        assert data["module"] == "auth"
        assert data["version"] == "0.1.0"
        assert data["tables_ready"] is True
        assert data["status"] == "ok"
