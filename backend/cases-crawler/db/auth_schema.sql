-- ===================================================================
-- LexPrime Auth Schema (Track A · Phase 4 P0)
-- 2026-06-28 · W1 脚手架
--
-- 4 表:
--   auth_users              认证实体 (email/password/role)
--   auth_lawyer_profiles    律师扩展档案 (执业证/律所/审核)
--   auth_tokens             Refresh Token 持久化
--   auth_otp_logs           邮箱/手机验证码日志
--
-- 与 cases-crawler/db/schema.sql 的关系:
--   - 字段对齐 auth.models.py (SQLAlchemy ORM 单一来源)
--   - PostgreSQL 12+ 兼容 (用 TEXT[] / JSONB / TIMESTAMPTZ)
--   - SQLite dev 模式: SQLAlchemy 会自动降级 JSONB → JSON, TEXT[] → JSON
--     (JSONB/数组特性只在 PG 生效, dev demo 不影响)
-- ===================================================================

-- ===================================================================
-- 1. auth_users (用户认证实体)
-- ===================================================================
CREATE TABLE IF NOT EXISTS auth_users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(128) UNIQUE NOT NULL,
    phone VARCHAR(32) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,        -- bcrypt 哈希 (W2)
    role VARCHAR(16) NOT NULL DEFAULT 'lawyer', -- lawyer / firm_admin / admin
    subscription_tier VARCHAR(16) DEFAULT 'trial', -- trial / pro / enterprise

    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_phone_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_2fa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    totp_secret VARCHAR(64),                    -- W2: TOTP 密钥 (加密存储)

    last_login_at TIMESTAMPTZ,
    last_login_ip VARCHAR(64),
    failed_login_count INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,                   -- 失败 5 次锁 15 分钟

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email);
CREATE INDEX IF NOT EXISTS idx_auth_users_phone ON auth_users(phone) WHERE phone IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_auth_users_role ON auth_users(role);
CREATE INDEX IF NOT EXISTS idx_auth_users_subscription ON auth_users(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_auth_users_active ON auth_users(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_auth_users_locked ON auth_users(locked_until) WHERE locked_until IS NOT NULL;

COMMENT ON TABLE auth_users IS '认证用户表 · Auth 模块核心 · 邮箱为主账号';

-- ===================================================================
-- 2. auth_lawyer_profiles (律师扩展档案, 1:1 with auth_users)
-- ===================================================================
CREATE TABLE IF NOT EXISTS auth_lawyer_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,

    name VARCHAR(64) NOT NULL,
    license_no VARCHAR(64) UNIQUE,              -- 律师执业证号
    firm_id VARCHAR(64) REFERENCES firms(id) ON DELETE SET NULL, -- 关联律所
    firm_role VARCHAR(16) DEFAULT 'lawyer',     -- partner / senior / lawyer / assistant

    -- 执业证审核状态机 (W3 实现)
    license_status VARCHAR(16) NOT NULL DEFAULT 'pending', -- pending / ai_reviewing / human_reviewing / approved / rejected
    license_image_url TEXT,                     -- 执业证图片 (本地路径, 不上云)
    license_ocr_data JSONB,                     -- PaddleOCR 提取的 JSON
    license_submitted_at TIMESTAMPTZ,
    license_reviewed_at TIMESTAMPTZ,
    license_reviewed_by BIGINT REFERENCES auth_users(id) ON DELETE SET NULL,
    license_reject_reason TEXT,

    specialties TEXT[],                         -- 专业领域 (民商/刑事/知产/婚姻等)
    bio TEXT,
    avatar_url TEXT,
    region VARCHAR(32),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_lawyer_profiles_user ON auth_lawyer_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_lawyer_profiles_license ON auth_lawyer_profiles(license_no) WHERE license_no IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_auth_lawyer_profiles_firm ON auth_lawyer_profiles(firm_id) WHERE firm_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_auth_lawyer_profiles_status ON auth_lawyer_profiles(license_status);
CREATE INDEX IF NOT EXISTS idx_auth_lawyer_profiles_specialties ON auth_lawyer_profiles USING gin(specialties);

COMMENT ON TABLE auth_lawyer_profiles IS '律师扩展档案 · 1:1 with auth_users · 执业证审核工作流承载表';

-- ===================================================================
-- 3. auth_tokens (Refresh Token 持久化)
-- ===================================================================
CREATE TABLE IF NOT EXISTS auth_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES auth_users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,    -- token 哈希, 不存明文
    token_type VARCHAR(16) NOT NULL DEFAULT 'refresh', -- refresh / access_blacklist (W2: 强制吊销)

    device_info VARCHAR(512),
    ip_address VARCHAR(64),
    user_agent TEXT,

    issued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,            -- Refresh 7d
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,                     -- 非空 = 已撤销
    revoked_reason VARCHAR(64)                  -- logout / device_change / security_alert / admin
);

CREATE INDEX IF NOT EXISTS idx_auth_tokens_user ON auth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_hash ON auth_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires ON auth_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_tokens_revoked ON auth_tokens(revoked_at) WHERE revoked_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_auth_tokens_user_active ON auth_tokens(user_id, expires_at, revoked_at);

COMMENT ON TABLE auth_tokens IS 'Refresh Token 持久化 · 用于登出/换设备/异常撤销 · UEBA 数据源';

-- ===================================================================
-- 4. auth_otp_logs (邮箱/手机验证码)
-- ===================================================================
CREATE TABLE IF NOT EXISTS auth_otp_logs (
    id BIGSERIAL PRIMARY KEY,
    target VARCHAR(128) NOT NULL,               -- 邮箱地址或手机号
    target_type VARCHAR(16) NOT NULL DEFAULT 'email', -- email / phone
    purpose VARCHAR(32) NOT NULL,               -- register / login / reset_password / verify_email / verify_phone / 2fa / license_verify

    code_hash VARCHAR(255) NOT NULL,            -- 验证码哈希, 不存明文
    sent_to VARCHAR(128) NOT NULL,              -- 冗余: 实际发送目标 (邮件可能是 +alias)

    expires_at TIMESTAMPTZ NOT NULL,            -- 默认 10 分钟
    consumed_at TIMESTAMPTZ,                    -- 用一次即失效
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 5,

    ip_address VARCHAR(64),
    user_agent TEXT,
    related_user_id BIGINT REFERENCES auth_users(id) ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_otp_target_purpose ON auth_otp_logs(target, purpose);
CREATE INDEX IF NOT EXISTS idx_auth_otp_expires ON auth_otp_logs(expires_at);
CREATE INDEX IF NOT EXISTS idx_auth_otp_consumed ON auth_otp_logs(consumed_at) WHERE consumed_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_auth_otp_user ON auth_otp_logs(related_user_id) WHERE related_user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_auth_otp_purpose_created ON auth_otp_logs(purpose, created_at DESC);

COMMENT ON TABLE auth_otp_logs IS 'OTP 验证码日志 · 邮箱/手机双通道 · 全链路可追溯';

-- ===================================================================
-- 触发器: updated_at 自动更新 (跟 cases-crawler/db/schema.sql 保持一致)
-- ===================================================================
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN SELECT unnest(ARRAY['auth_users', 'auth_lawyer_profiles', 'auth_tokens'])
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_%I_updated_at ON %I;
            CREATE TRIGGER update_%I_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        ', t, t, t, t);
    END LOOP;
END $$;
