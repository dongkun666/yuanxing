-- LexPrime PostgreSQL Schema
-- 2026-06-28 · 3 库 (cases / laws / companies) + 律所内部数据 (firm_*) + 律师自加 (user_*)
-- 设计: 中文列名 (兼容 cncases) + lex_id 律师标注 + 数据来源溯源

-- 启用扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 模糊检索
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- JSONB GIN 索引

-- ================== 1. 判例库 (cncases 兼容 + 增强) ==================
-- 字段对齐 cncases/cases 仓库的 Case struct, 保留中文列名
CREATE TABLE IF NOT EXISTS cases (
    id BIGSERIAL PRIMARY KEY,
    doc_id VARCHAR(64) UNIQUE,              -- 原始链接 ID (Wenshu docId)
    case_id VARCHAR(128),                  -- 案号
    case_name TEXT,                         -- 案件名称
    court VARCHAR(256),                     -- 法院
    case_type VARCHAR(64),                  -- 案件类型 (民事/刑事/行政/执行)
    procedure VARCHAR(64),                  -- 审理程序 (一审/二审/再审/执行)
    judgment_date DATE,                     -- 裁判日期
    public_date DATE,                       -- 公开日期
    parties TEXT,                           -- 当事人
    cause VARCHAR(128),                     -- 案由
    legal_basis TEXT,                       -- 法律依据
    full_text TEXT,                         -- 全文 (HTML, 脱敏后)
    full_text_plain TEXT,                   -- 全文纯文本 (供 ES 索引)
    cause_category VARCHAR(64),             -- 案由分类 (LexPrime 自动归类, 8 大类)
    cause_color VARCHAR(16),                -- UI 配色
    source VARCHAR(32) NOT NULL DEFAULT 'cncases', -- 数据来源 (cncases / court_cases / lawyer_added)
    source_url TEXT,                        -- 原文链接
    region VARCHAR(32),                     -- 地区 (脱敏: 省/直辖市, 不到市)
    year SMALLINT,                          -- 裁判年份
    keywords TEXT[],                        -- 关键词 (LLM 提取)
    lex_score SMALLINT,                     -- LexPrime 推荐度 (0-100, LLM 评分)
    lex_tags TEXT[],                        -- LexPrime 标签
    view_count INTEGER DEFAULT 0,           -- 律师查看次数
    favorite_count INTEGER DEFAULT 0,       -- 收藏次数
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cases_doc_id ON cases(doc_id);
CREATE INDEX IF NOT EXISTS idx_cases_case_id ON cases(case_id);
CREATE INDEX IF NOT EXISTS idx_cases_cause ON cases(cause);
CREATE INDEX IF NOT EXISTS idx_cases_cause_category ON cases(cause_category);
CREATE INDEX IF NOT EXISTS idx_cases_court ON cases(court);
CREATE INDEX IF NOT EXISTS idx_cases_judgment_date ON cases(judgment_date);
CREATE INDEX IF NOT EXISTS idx_cases_year ON cases(year);
CREATE INDEX IF NOT EXISTS idx_cases_case_type ON cases(case_type);
CREATE INDEX IF NOT EXISTS idx_cases_source ON cases(source);
CREATE INDEX IF NOT EXISTS idx_cases_lex_score ON cases(lex_score DESC);
CREATE INDEX IF NOT EXISTS idx_cases_full_text_search ON cases USING gin(to_tsvector('simple', coalesce(full_text_plain, '')));
CREATE INDEX IF NOT EXISTS idx_cases_cause_trgm ON cases USING gin(cause gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_cases_keywords ON cases USING gin(keywords);

COMMENT ON TABLE cases IS '判例库 · LexPrime 核心资产 · 字段对齐 cncases + LexPrime 增强';

-- ================== 2. 法规库 (国家库 + 司法解释 + 复函) ==================
CREATE TABLE IF NOT EXISTS laws (
    id BIGSERIAL PRIMARY KEY,
    law_id VARCHAR(64) UNIQUE NOT NULL,     -- 法规 ID (国家库 ID 或自生成)
    title VARCHAR(512) NOT NULL,            -- 法规标题
    law_number VARCHAR(128),                -- 法规编号 (如 "主席令第 X 号")
    law_type VARCHAR(64) NOT NULL,          -- 法规类型 (法律/行政法规/地方性法规/司法解释/部门规章/复函)
    issuing_organ VARCHAR(256),             -- 制定机关
    issue_date DATE,                        -- 公布日期
    effective_date DATE,                    -- 生效日期
    status VARCHAR(32) DEFAULT '有效',      -- 有效 / 已废止 / 已修订
    summary TEXT,                           -- 摘要
    full_text TEXT,                         -- 全文
    level SMALLINT DEFAULT 1,               -- 法规层级 (1 宪法 / 2 法律 / 3 行政法规 / 4 司法解释 / 5 部门规章)
    source VARCHAR(32) DEFAULT 'npc_laws',  -- 数据来源 (npc_laws / sppc / lawyer_added)
    source_url TEXT,                        -- 原文链接
    revised_from VARCHAR(64),               -- 修订自哪部法规
    revised_to VARCHAR(64),                 -- 修订为哪部法规
    related_laws TEXT[],                    -- 关联法规
    related_cases_count INTEGER DEFAULT 0,  -- 关联判例数
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_laws_law_id ON laws(law_id);
CREATE INDEX IF NOT EXISTS idx_laws_law_type ON laws(law_type);
CREATE INDEX IF NOT EXISTS idx_laws_status ON laws(status);
CREATE INDEX IF NOT EXISTS idx_laws_effective_date ON laws(effective_date DESC);
CREATE INDEX IF NOT EXISTS idx_laws_title_search ON laws USING gin(to_tsvector('simple', title));
CREATE INDEX IF NOT EXISTS idx_laws_full_text_search ON laws USING gin(to_tsvector('simple', coalesce(full_text, '')));

COMMENT ON TABLE laws IS '法规库 · 主源国家库 + LexPrime 增强';

-- ================== 3. 企业征信库 (国家库 + 启信宝/天眼查公开数据) ==================
CREATE TABLE IF NOT EXISTS companies (
    id BIGSERIAL PRIMARY KEY,
    unified_id VARCHAR(64) UNIQUE NOT NULL, -- 统一社会信用代码
    company_name VARCHAR(512) NOT NULL,     -- 公司名称
    company_type VARCHAR(64),               -- 公司类型 (有限责任公司/股份有限公司/个体工商户)
    legal_rep VARCHAR(64),                  -- 法定代表人 (脱敏: 姓 + **)
    registered_capital VARCHAR(64),         -- 注册资本
    paid_capital VARCHAR(64),               -- 实缴资本
    establish_date DATE,                    -- 成立日期
    business_status VARCHAR(32),            -- 经营状态 (存续/注销/吊销/迁出)
    registered_address VARCHAR(512),        -- 注册地址 (脱敏: 到区)
    business_scope TEXT,                    -- 经营范围
    industry VARCHAR(64),                   -- 行业
    region VARCHAR(32),                     -- 地区
    is_zxgk BOOLEAN DEFAULT FALSE,          -- 是否失信被执行
    is_dishonest BOOLEAN DEFAULT FALSE,     -- 是否严重违法
    source VARCHAR(32) DEFAULT 'gsxt',     -- 数据来源
    source_url TEXT,                        -- 原文链接
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_companies_unified_id ON companies(unified_id);
CREATE INDEX IF NOT EXISTS idx_companies_company_name ON companies(company_name);
CREATE INDEX IF NOT EXISTS idx_companies_legal_rep ON companies(legal_rep);
CREATE INDEX IF NOT EXISTS idx_companies_business_status ON companies(business_status);
CREATE INDEX IF NOT EXISTS idx_companies_region ON companies(region);
CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry);
CREATE INDEX IF NOT EXISTS idx_companies_is_zxgk ON companies(is_zxgk) WHERE is_zxgk = TRUE;
CREATE INDEX IF NOT EXISTS idx_companies_name_trgm ON companies USING gin(company_name gin_trgm_ops);

COMMENT ON TABLE companies IS '企业征信库 · 公开数据 + LexPrime 脱敏';

-- ================== 4. 律师自加判例 (内部判例) ==================
CREATE TABLE IF NOT EXISTS lawyer_added_cases (
    id BIGSERIAL PRIMARY KEY,
    lawyer_id VARCHAR(64) NOT NULL,         -- 律师 ID (对应 auth.users.id)
    firm_id VARCHAR(64),                    -- 律所 ID
    case_id VARCHAR(64),                    -- 律师自加判例 ID (UUID)
    title VARCHAR(512) NOT NULL,
    summary TEXT,
    full_text TEXT,
    cause VARCHAR(128),
    cause_category VARCHAR(64),
    tags TEXT[],
    notes TEXT,                             -- 律师笔记
    visibility VARCHAR(16) DEFAULT 'private', -- private (仅自己) / firm (律所共享) / public (公开)
    related_official_case_id BIGINT REFERENCES cases(id), -- 关联到公开判例
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lawyer_cases_lawyer ON lawyer_added_cases(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_cases_firm ON lawyer_added_cases(firm_id);
CREATE INDEX IF NOT EXISTS idx_lawyer_cases_visibility ON lawyer_added_cases(visibility);
CREATE INDEX IF NOT EXISTS idx_lawyer_cases_official ON lawyer_added_cases(related_official_case_id);

COMMENT ON TABLE lawyer_added_cases IS '律师自加判例 · 内部数据护城河 · 律所共享是核心功能';

-- ================== 5. 收藏 (跨 3 库) ==================
CREATE TABLE IF NOT EXISTS favorites (
    id BIGSERIAL PRIMARY KEY,
    lawyer_id VARCHAR(64) NOT NULL,
    target_type VARCHAR(16) NOT NULL,        -- 'case' / 'law' / 'company' / 'judicial_point'
    target_id VARCHAR(64) NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(lawyer_id, target_type, target_id)
);

CREATE INDEX IF NOT EXISTS idx_favorites_lawyer ON favorites(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_favorites_target ON favorites(target_type, target_id);

-- ================== 6. 律所 (firm) - 律所版 0.1 基础 ==================
CREATE TABLE IF NOT EXISTS firms (
    id VARCHAR(64) PRIMARY KEY,              -- 律所 ID (UUID)
    name VARCHAR(256) NOT NULL,              -- 律所名称
    unified_id VARCHAR(64),                  -- 律所执业证号 / 统一社会信用代码
    license_no VARCHAR(64),                  -- 执业许可证号
    region VARCHAR(32),                      -- 所在地区
    address VARCHAR(512),
    contact_phone VARCHAR(32),
    contact_email VARCHAR(128),
    website VARCHAR(256),
    established_date DATE,
    firm_size VARCHAR(16) DEFAULT 'small',   -- solo (1-5) / small (6-20) / medium (21-100) / large (100+)
    subscription_tier VARCHAR(16) DEFAULT 'trial', -- trial / pro / enterprise
    subscription_started_at TIMESTAMPTZ,
    subscription_expires_at TIMESTAMPTZ,
    settings JSONB DEFAULT '{}'::jsonb,      -- 律所配置 (行业偏好/默认模板/品牌色等)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_firms_name ON firms(name);
CREATE INDEX IF NOT EXISTS idx_firms_subscription ON firms(subscription_tier, subscription_expires_at);

COMMENT ON TABLE firms IS '律所档案 · 律所版 0.1 基础表';

-- 律师档案 (关联律所)
CREATE TABLE IF NOT EXISTS lawyers (
    id VARCHAR(64) PRIMARY KEY,              -- 律师 ID (UUID, 对应 auth.users.id)
    firm_id VARCHAR(64) REFERENCES firms(id),
    name VARCHAR(64) NOT NULL,
    license_no VARCHAR(64) UNIQUE,           -- 律师执业证号
    email VARCHAR(128) UNIQUE NOT NULL,
    phone VARCHAR(32),
    role VARCHAR(16) DEFAULT 'lawyer',      -- partner (合伙人) / senior (高级律师) / lawyer (律师) / assistant (律师助理) / admin (行政)
    specialties TEXT[],                      -- 专业领域 (民商/刑事/知产/婚姻等)
    avatar_url TEXT,
    bio TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lawyers_firm ON lawyers(firm_id);
CREATE INDEX IF NOT EXISTS idx_lawyers_email ON lawyers(email);
CREATE INDEX IF NOT EXISTS idx_lawyers_role ON lawyers(role);

COMMENT ON TABLE lawyers IS '律师档案 · 关联律所 · 律所版核心';

-- 律所案件分配 (案件 → 律师)
CREATE TABLE IF NOT EXISTS firm_case_assignments (
    id BIGSERIAL PRIMARY KEY,
    firm_id VARCHAR(64) NOT NULL REFERENCES firms(id),
    case_id BIGINT,                         -- 关联到主系统的案件 ID (TODO: 跨服务引用)
    case_title VARCHAR(512) NOT NULL,        -- 案件名 (冗余, 方便查询)
    lawyer_id VARCHAR(64) NOT NULL REFERENCES lawyers(id),
    role VARCHAR(16) DEFAULT 'lead',         -- lead (主办) / assist (协办) / review (审核)
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(case_id, lawyer_id)
);

CREATE INDEX IF NOT EXISTS idx_assignments_firm ON firm_case_assignments(firm_id);
CREATE INDEX IF NOT EXISTS idx_assignments_lawyer ON firm_case_assignments(lawyer_id);

-- 律所工时记录
CREATE TABLE IF NOT EXISTS firm_time_entries (
    id BIGSERIAL PRIMARY KEY,
    firm_id VARCHAR(64) NOT NULL REFERENCES firms(id),
    lawyer_id VARCHAR(64) NOT NULL REFERENCES lawyers(id),
    case_id BIGINT,                         -- 关联案件
    entry_date DATE NOT NULL,
    hours NUMERIC(5, 2) NOT NULL,            -- 工时 (小时)
    description TEXT,
    billable BOOLEAN DEFAULT TRUE,           -- 是否可计费
    rate NUMERIC(8, 2),                      -- 费率 (元/小时)
    amount NUMERIC(12, 2) GENERATED ALWAYS AS (hours * rate) STORED,
    status VARCHAR(16) DEFAULT 'draft',      -- draft / submitted / approved / invoiced
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_time_entries_firm ON firm_time_entries(firm_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_lawyer ON firm_time_entries(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_date ON firm_time_entries(entry_date DESC);
CREATE INDEX IF NOT EXISTS idx_time_entries_status ON firm_time_entries(status);

COMMENT ON TABLE firm_time_entries IS '工时记录 · 律所版时钟计费基础';

-- ================== 7. 爬虫运行日志 (运维) ==================
CREATE TABLE IF NOT EXISTS crawler_runs (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(32) NOT NULL,             -- npc_laws / court_cases / zhixing / gsxt / cncases
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status VARCHAR(16) DEFAULT 'running',    -- running / success / failed / partial
    items_total INTEGER DEFAULT 0,
    items_inserted INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    error_log TEXT,
    config JSONB
);

CREATE INDEX IF NOT EXISTS idx_crawler_runs_source ON crawler_runs(source);
CREATE INDEX IF NOT EXISTS idx_crawler_runs_status ON crawler_runs(status);

-- ================== 触发器: updated_at 自动更新 ==================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN SELECT unnest(ARRAY['cases', 'laws', 'companies', 'lawyer_added_cases', 'firms', 'lawyers'])
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
