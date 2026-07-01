"""
W9 Skill 3 文书生成 API Router 测试 (lex-coder · 2026-06-29)

C1 任务: 4 endpoint + 4 template + Word docx 生成

覆盖:
- 4 端点 happy path (complaint/defense/contract/letter)
- 模板占位符替换正确性
- 缺失字段兜底
- Word docx Base64 解码后是非空二进制
- /health 端点 (4 模板状态)
- 端点错误处理 (空 lawyer_id / 非法 output_format / 模板不存在)

策略:
- pytest-asyncio + httpx AsyncClient + ASGITransport
- in-memory SQLite + lifespan 手动触发 (复用 W2 踩过的坑)
- 复用 review_router / backlog_router 测试的 fixture pattern
"""
import base64
import pytest_asyncio

from httpx import AsyncClient, ASGITransport


# ====== 字段常量 (4 文书类型的最小必填集) ======
COMPLAINT_FIELDS = {
    "case_id": "(2026)京0105民初1234号",
    "plaintiff_name": "张三",
    "plaintiff_id": "110101199001011234",
    "plaintiff_addr": "北京市朝阳区某街道 1 号",
    "plaintiff_phone": "13800138000",
    "defendant_name": "李四",
    "defendant_id": "110101199203054321",
    "defendant_addr": "北京市海淀区某街道 2 号",
    "defendant_phone": "13900139000",
    "court": "北京市朝阳区人民法院",
    "cause": "民间借贷纠纷",
    "facts": "原告于 2023-01-01 借给被告人民币 50 万元, 约定月息 2%, 借款期限 1 年。借款到期后, 被告未按约还款。",
    "evidence": "1. 借款合同原件\n2. 转账记录\n3. 微信聊天记录",
    "claims": "1. 请求判令被告偿还借款本金 50 万元\n2. 请求判令被告支付利息 (按月息 2% 计算)\n3. 诉讼费由被告承担",
}

DEFENSE_FIELDS = {
    "case_id": "(2026)京0105民初1234号",
    "plaintiff_name": "张三",
    "defendant_name": "李四",
    "defendant_id": "110101199203054321",
    "defendant_addr": "北京市海淀区某街道 2 号",
    "defendant_phone": "13900139000",
    "court": "北京市朝阳区人民法院",
    "cause": "民间借贷纠纷",
    "facts": "被告已通过银行转账方式偿还全部借款本金及利息, 双方债权债务关系已结清。",
    "evidence": "1. 银行转账记录 5 笔\n2. 微信还款确认聊天记录\n3. 收条原件",
    "claims_response": "1. 依法驳回原告全部诉讼请求\n2. 诉讼费由原告承担",
}

CONTRACT_FIELDS = {
    "contract_id": "HT-2026-001",
    "contract_type": "服务合同",
    "party_a": "北京某科技有限公司",
    "party_a_id": "91110000XXXXXXXXXX",
    "party_a_addr": "北京市朝阳区某大厦 5 层",
    "party_a_phone": "010-12345678",
    "party_a_rep": "王经理",
    "party_b": "上海某咨询有限公司",
    "party_b_id": "91310000XXXXXXXXXX",
    "party_b_addr": "上海市浦东新区某园区 8 号",
    "party_b_phone": "021-87654321",
    "party_b_rep": "李总监",
    "subject": "甲方委托乙方提供企业战略咨询服务",
    "amount": "1000000",
    "amount_cn": "壹佰万元整",
    "payment_method": "银行转账",
    "payment_schedule": "合同签订后 7 日内支付 50%, 项目交付验收后 7 日内支付 50%",
    "start_date": "2026-07-01",
    "end_date": "2026-12-31",
    "perform_location": "北京",
    "perform_method": "现场 + 远程结合",
    "facts": "1. 乙方应在 3 个月内完成第一阶段战略诊断报告。\n2. 甲方应在每个阶段验收后支付对应款项。",
    "breach_terms": "任何一方违约, 应承担违约责任并赔偿对方损失 (不超过合同总金额的 30%)。",
    "jurisdiction": "北京",
    "misc_terms": "本合同未尽事宜, 由双方协商解决。",
}

LETTER_FIELDS = {
    "letter_id": "LS-2026-001",
    "law_firm": "北京元枢律师事务所",
    "lawyer_name": "王律师",
    "lawyer_phone": "010-12345678",
    "lawyer_email": "wang@lexprime.com",
    "law_firm_addr": "北京市朝阳区建国路 1 号",
    "recipient": "上海某科技有限公司",
    "recipient_addr": "上海市浦东新区某路 88 号",
    "sender": "北京某贸易有限公司",
    "subject": "要求立即支付拖欠货款",
    "facts": "委托人于 2026-01 至 2026-05 期间, 累计向贵司供应货物价值人民币 200 万元。截至本函发出之日, 贵司尚有 80 万元货款未支付。",
    "demands": "1. 请贵司于本函送达之日起 15 日内, 一次性支付拖欠货款 80 万元。\n2. 请贵司书面回复付款计划。",
    "deadline": "2026-07-15",
    "consequence": "1. 委托人将依法提起民事诉讼, 追讨货款及逾期利息。\n2. 委托人将向相关行业协会举报贵司失信行为。",
}


# ====== Fixtures ======
@pytest_asyncio.fixture(scope="function")
async def _shared_engine():
    """共享的 in-memory SQLite engine (供 client + clean 共用)"""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from core.models import Base
    # Side-effect imports: 让 review_router / backlog_router / doc_gen_router 表注册到 metadata
    from api import review_router, backlog_router, doc_gen_router  # noqa: F401

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 把 Database 全局指向 in-memory
    import core.db
    orig_engine = core.db.Database._engine
    orig_factory = core.db.Database._session_factory
    core.db.Database._engine = engine
    core.db.Database._session_factory = factory

    yield engine, factory

    core.db.Database._engine = orig_engine
    core.db.Database._session_factory = orig_factory
    await engine.dispose()


@pytest_asyncio.fixture
async def client(_shared_engine):
    """FastAPI TestClient (用 in-memory DB)"""
    from api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ====== Health ======
class TestHealth:
    async def test_health_ok(self, client):
        """health 端点 + 4 模板都加载"""
        resp = await client.get("/api/doc-gen/health")
        assert resp.status_code == 200, f"health failed: {resp.text}"
        body = resp.json()
        assert body["status"] in ("ok", "degraded")
        assert body["service_id"] == "lexprime.skill.doc-gen"
        assert body["template_count"] == 4
        assert body["templates_loaded"] == 4
        assert body["docx_available"] is True  # python-docx 1.2.0 已装

    async def test_health_templates_metadata(self, client):
        """4 模板含字段清单 + 元信息"""
        resp = await client.get("/api/doc-gen/health")
        body = resp.json()
        for t in ("complaint", "defense", "contract", "letter"):
            tpl = body["templates"][t]
            assert tpl["loaded"] is True
            assert tpl["field_count"] >= 5  # 至少 5 个占位符
            assert len(tpl["fields"]) == tpl["field_count"]
            assert "version" in tpl
            assert "label" in tpl
            assert "icon" in tpl

    async def test_health_doc_type_labels(self, client):
        """doc_type_labels 含中文标签"""
        resp = await client.get("/api/doc-gen/health")
        body = resp.json()
        labels = body["doc_type_labels"]
        assert labels["complaint"] == "民事起诉状"
        assert labels["defense"] == "民事答辩状"
        assert labels["contract"] == "合同"
        assert labels["letter"] == "律师函"

    async def test_health_endpoints_listed(self, client):
        """端点列表包含 4 端点 + health"""
        resp = await client.get("/api/doc-gen/health")
        body = resp.json()
        assert "POST /api/doc-gen/complaint" in body["endpoints"]
        assert "POST /api/doc-gen/defense" in body["endpoints"]
        assert "POST /api/doc-gen/contract" in body["endpoints"]
        assert "POST /api/doc-gen/letter" in body["endpoints"]
        assert "GET /api/doc-gen/health" in body["endpoints"]


# ====== Complaint ======
class TestComplaint:
    async def test_complaint_happy_path(self, client):
        """起诉状完整字段生成"""
        payload = {"lawyer_id": "L1-王律师", "case_id": "TEST-001", "fields": COMPLAINT_FIELDS}
        resp = await client.post("/api/doc-gen/complaint", json=payload)
        assert resp.status_code == 200, f"complaint failed: {resp.text}"
        body = resp.json()

        assert body["doc_type"] == "complaint"
        assert body["doc_type_label"] == "民事起诉状"
        assert body["lawyer_id"] == "L1-王律师"
        assert body["case_id"] == "TEST-001"
        assert body["template_id"] == "complaint_v1"

    async def test_complaint_markdown_rendering(self, client):
        """起诉状 Markdown 渲染正确性"""
        payload = {"lawyer_id": "L1", "fields": COMPLAINT_FIELDS}
        resp = await client.post("/api/doc-gen/complaint", json=payload)
        body = resp.json()
        md = body["markdown"]

        # 关键占位符被替换
        assert COMPLAINT_FIELDS["plaintiff_name"] in md
        assert COMPLAINT_FIELDS["defendant_name"] in md
        assert COMPLAINT_FIELDS["court"] in md
        assert COMPLAINT_FIELDS["cause"] in md
        assert COMPLAINT_FIELDS["facts"] in md
        # 不留占位符
        assert "{{plaintiff_name}}" not in md
        assert "{{defendant_name}}" not in md
        assert "{{court}}" not in md

    async def test_complaint_docx_base64(self, client):
        """docx_base64 解码后是非空二进制 (PK header 是 .docx 标志)"""
        payload = {"lawyer_id": "L1", "fields": COMPLAINT_FIELDS}
        resp = await client.post("/api/doc-gen/complaint", json=payload)
        body = resp.json()
        assert body["docx_base64"] is not None
        assert body["docx_filename"].startswith("complaint-")
        assert body["docx_filename"].endswith(".docx")
        assert body["docx_size_bytes"] > 1000  # docx 至少 1KB

        decoded = base64.b64decode(body["docx_base64"])
        assert decoded.startswith(b"PK")  # ZIP signature (docx 是 ZIP 格式)
        assert len(decoded) == body["docx_size_bytes"]

    async def test_complaint_filled_and_missing(self, client):
        """filled_fields / missing_fields 准确"""
        # 故意只填一半字段
        partial = {"plaintiff_name": "张三", "court": "北京市朝阳区人民法院"}
        payload = {"lawyer_id": "L1", "fields": partial}
        resp = await client.post("/api/doc-gen/complaint", json=payload)
        body = resp.json()
        assert "plaintiff_name" in body["filled_fields"]
        assert "court" in body["filled_fields"]
        # 缺失字段: case_id / defendant_name / facts 等
        assert "defendant_name" in body["missing_fields"]
        assert "facts" in body["missing_fields"]
        # 缺失字段的占位符应保留
        assert "{{defendant_name}}" in body["markdown"]


# ====== Defense ======
class TestDefense:
    async def test_defense_happy_path(self, client):
        """答辩状完整字段生成"""
        payload = {"lawyer_id": "L2-李律师", "fields": DEFENSE_FIELDS}
        resp = await client.post("/api/doc-gen/defense", json=payload)
        assert resp.status_code == 200, f"defense failed: {resp.text}"
        body = resp.json()
        assert body["doc_type"] == "defense"
        assert body["lawyer_id"] == "L2-李律师"
        # 关键字段在 markdown 中
        assert DEFENSE_FIELDS["defendant_name"] in body["markdown"]
        assert DEFENSE_FIELDS["plaintiff_name"] in body["markdown"]
        assert DEFENSE_FIELDS["court"] in body["markdown"]
        # 答辩响应字段替换正确
        assert "驳回原告" in body["markdown"]

    async def test_defense_docx_valid(self, client):
        """答辩状 docx 有效"""
        payload = {"lawyer_id": "L2", "fields": DEFENSE_FIELDS}
        resp = await client.post("/api/doc-gen/defense", json=payload)
        body = resp.json()
        decoded = base64.b64decode(body["docx_base64"])
        assert decoded.startswith(b"PK")


# ====== Contract ======
class TestContract:
    async def test_contract_happy_path(self, client):
        """合同完整字段生成"""
        payload = {"lawyer_id": "L3-陈律师", "fields": CONTRACT_FIELDS}
        resp = await client.post("/api/doc-gen/contract", json=payload)
        assert resp.status_code == 200, f"contract failed: {resp.text}"
        body = resp.json()
        assert body["doc_type"] == "contract"
        # 合同主体双甲方乙方
        assert CONTRACT_FIELDS["party_a"] in body["markdown"]
        assert CONTRACT_FIELDS["party_b"] in body["markdown"]
        # 金额
        assert CONTRACT_FIELDS["amount"] in body["markdown"]
        # 期限
        assert CONTRACT_FIELDS["start_date"] in body["markdown"]
        assert CONTRACT_FIELDS["end_date"] in body["markdown"]
        # 不留占位符
        assert "{{party_a}}" not in body["markdown"]
        assert "{{party_b}}" not in body["markdown"]

    async def test_contract_docx_valid(self, client):
        """合同 docx 有效 (字段最多, docx 也应该最大)"""
        payload = {"lawyer_id": "L3", "fields": CONTRACT_FIELDS}
        resp = await client.post("/api/doc-gen/contract", json=payload)
        body = resp.json()
        decoded = base64.b64decode(body["docx_base64"])
        assert decoded.startswith(b"PK")
        assert body["docx_size_bytes"] > 2000  # 合同字段多, docx 应较大

    async def test_contract_field_count(self, client):
        """合同模板字段数最多 (~28)"""
        resp = await client.get("/api/doc-gen/health")
        contract_count = resp.json()["templates"]["contract"]["field_count"]
        assert contract_count >= 20  # 至少 20 个占位符


# ====== Letter ======
class TestLetter:
    async def test_letter_happy_path(self, client):
        """律师函完整字段生成"""
        payload = {"lawyer_id": "L4-赵律师", "fields": LETTER_FIELDS}
        resp = await client.post("/api/doc-gen/letter", json=payload)
        assert resp.status_code == 200, f"letter failed: {resp.text}"
        body = resp.json()
        assert body["doc_type"] == "letter"
        # 致送人 / 委托人 / 律师信息
        assert LETTER_FIELDS["recipient"] in body["markdown"]
        assert LETTER_FIELDS["sender"] in body["markdown"]
        assert LETTER_FIELDS["law_firm"] in body["markdown"]
        # 要求 + 期限
        assert LETTER_FIELDS["deadline"] in body["markdown"]
        assert "立即支付" in body["markdown"]

    async def test_letter_docx_valid(self, client):
        """律师函 docx 有效"""
        payload = {"lawyer_id": "L4", "fields": LETTER_FIELDS}
        resp = await client.post("/api/doc-gen/letter", json=payload)
        body = resp.json()
        decoded = base64.b64decode(body["docx_base64"])
        assert decoded.startswith(b"PK")


# ====== 输出格式控制 ======
class TestOutputFormat:
    async def test_markdown_only(self, client):
        """output_format=markdown 时, docx_base64 应为 None"""
        payload = {"lawyer_id": "L1", "fields": COMPLAINT_FIELDS, "output_format": "markdown"}
        resp = await client.post("/api/doc-gen/complaint", json=payload)
        body = resp.json()
        assert body["docx_base64"] is None
        assert body["docx_filename"] is None
        assert body["docx_size_bytes"] is None
        # markdown 仍然有内容
        assert len(body["markdown"]) > 100
        assert COMPLAINT_FIELDS["plaintiff_name"] in body["markdown"]

    async def test_docx_only(self, client):
        """output_format=docx 时, markdown 仍然有 (设计上保留)"""
        payload = {"lawyer_id": "L1", "fields": COMPLAINT_FIELDS, "output_format": "docx"}
        resp = await client.post("/api/doc-gen/complaint", json=payload)
        body = resp.json()
        assert body["docx_base64"] is not None
        # markdown 仍然有内容 (前端可预览)
        assert len(body["markdown"]) > 100

    async def test_invalid_output_format(self, client):
        """output_format 非法值拒绝 (Pydantic 422)"""
        payload = {"lawyer_id": "L1", "fields": COMPLAINT_FIELDS, "output_format": "pdf"}
        resp = await client.post("/api/doc-gen/complaint", json=payload)
        assert resp.status_code == 422


# ====== 错误处理 ======
class TestErrorHandling:
    async def test_empty_lawyer_id_rejected(self, client):
        """lawyer_id 为空 → 422"""
        payload = {"lawyer_id": "", "fields": COMPLAINT_FIELDS}
        resp = await client.post("/api/doc-gen/complaint", json=payload)
        assert resp.status_code == 422

    async def test_missing_lawyer_id_rejected(self, client):
        """lawyer_id 缺失 → 422"""
        payload = {"fields": COMPLAINT_FIELDS}
        resp = await client.post("/api/doc-gen/complaint", json=payload)
        assert resp.status_code == 422

    async def test_unknown_doc_type_404(self, client):
        """未知 doc_type → 422 (路由不存在)"""
        payload = {"lawyer_id": "L1", "fields": {}}
        resp = await client.post("/api/doc-gen/bogus", json=payload)
        assert resp.status_code == 404  # FastAPI 路由未注册 → 404

    async def test_complaint_with_minimal_fields(self, client):
        """只传 lawyer_id, 模板字段全空 → 应仍返回 200, 大量 missing_fields"""
        payload = {"lawyer_id": "L1"}
        resp = await client.post("/api/doc-gen/complaint", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["docx_base64"] is not None  # 即使空, 也能生成 docx
        # missing_fields 应 >= 10
        assert len(body["missing_fields"]) >= 10
        # 占位符保留在 markdown 中
        assert "{{plaintiff_name}}" in body["markdown"]
        assert "{{defendant_name}}" in body["markdown"]


# ====== 模板内部 helper ======
class TestTemplateHelpers:
    def test_extract_placeholders(self):
        """占位符提取去重 + 保序"""
        from api.doc_gen_router import _extract_placeholders, _load_template

        md = _load_template("complaint")
        keys = _extract_placeholders(md)
        assert "plaintiff_name" in keys
        assert "defendant_name" in keys
        assert "court" in keys
        assert "facts" in keys
        assert "evidence" in keys
        assert "claims" in keys
        # 去重
        assert len(keys) == len(set(keys))

    def test_render_template_replaces_and_keeps_missing(self):
        """_render_template 返回 (渲染 md, filled, missing)"""
        from api.doc_gen_router import _render_template

        tpl = "Hello {{name}}, age {{age}}"
        rendered, filled, missing = _render_template(tpl, {"name": "张三"})
        assert "张三" in rendered
        # "age" 没传, 应该进 missing, 不进 filled
        assert "name" in filled
        assert "age" in missing
        assert "{{age}}" in rendered  # 缺失, 保留占位符
        assert "{{name}}" not in rendered  # 已填充, 不留占位符

    def test_render_template_empty_string_treated_as_missing(self):
        """空字符串字段视为缺失"""
        from api.doc_gen_router import _render_template

        tpl = "Hello {{name}}"
        rendered, filled, missing = _render_template(tpl, {"name": "  "})
        assert "name" in missing
        assert "{{name}}" in rendered


# ====== 4 端点 E2E (回归测试) ======
class TestE2EAllFour:
    async def test_all_four_endpoints_success(self, client):
        """4 端点串行调通"""
        for endpoint, fields in [
            ("complaint", COMPLAINT_FIELDS),
            ("defense", DEFENSE_FIELDS),
            ("contract", CONTRACT_FIELDS),
            ("letter", LETTER_FIELDS),
        ]:
            payload = {"lawyer_id": f"L1-{endpoint}", "fields": fields}
            resp = await client.post(f"/api/doc-gen/{endpoint}", json=payload)
            assert resp.status_code == 200, f"{endpoint} failed: {resp.text}"
            body = resp.json()
            assert body["doc_type"] == endpoint
            assert body["docx_base64"] is not None
            decoded = base64.b64decode(body["docx_base64"])
            assert decoded.startswith(b"PK")
            assert body["latency_ms"] >= 0
            assert "LexPrime 元枢法智" in body["disclaimer"]
            # 律师 ID 应出现在 markdown (兜底字段)
            assert f"L1-{endpoint}" in body["markdown"]

    async def test_gen_id_unique_per_request(self, client):
        """gen_id 每次生成 UUID, 不重复"""
        ids = set()
        for _ in range(3):
            payload = {"lawyer_id": "L1", "fields": COMPLAINT_FIELDS}
            resp = await client.post("/api/doc-gen/complaint", json=payload)
            gen_id = resp.json()["gen_id"]
            assert gen_id not in ids
            ids.add(gen_id)
            assert gen_id.startswith("dg-")

    async def test_disclaimer_in_every_response(self, client):
        """每个响应都含 AI 辅助声明"""
        for endpoint in ("complaint", "defense", "contract", "letter"):
            payload = {"lawyer_id": "L1", "fields": COMPLAINT_FIELDS}
            resp = await client.post(f"/api/doc-gen/{endpoint}", json=payload)
            assert "LexPrime 元枢法智" in resp.json()["disclaimer"]
            # 也在 markdown 末尾 (模板底部有 AI 辅助声明)
            assert "AI 辅助声明" in resp.json()["markdown"]