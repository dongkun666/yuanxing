"""
W15 Skill 3 律师函 v2.0 模板 + prompt 优化 回归测试 (lex-ai · 2026-06-30)

任务: W15 skill3-iterate
必读:
- W9 letter_v1.md (5d8ecdc) 起点模板
- W12 A2 doc_workflow (829d25c) 5 状态机
- W12 A2 signature_router (85278db) POST/GET
- W12 A2 reviewer.py 4 文书维度 (letter: 事实/法律意见/要求/时限/后果)

覆盖:
1. letter_v2 模板加载 + 端点 POST /api/doc-gen/letter-v2
2. 5 律师函样例 (mock 8 律师反馈场景):
   - 样例 1: 货物买卖 (L1 王律师反馈 → 时限梯度)
   - 样例 2: 物业纠纷 (L2 李律师反馈 → 法条具体引用)
   - 样例 3: 劳动关系 (L3 张律师反馈 → 三段式事实)
   - 样例 4: 知识产权 (L4 赵律师反馈 → 后果量化)
   - 样例 5: 借贷纠纷 (L6 周律师反馈 → 签字栏 + 执业证号)
3. doc_workflow 5 状态转换 (draft → ai_reviewed → lawyer_reviewed → client_signed → archived)
4. signature_router 集成 (上传签字 + 查询状态 + workflow.has_signature)
5. 5 维度风险标注 (letter: 事实/法律意见/要求/时限/后果, 阈值 0.6)
6. prompt v2.0 YAML 结构校验
7. health 端点含 letter_v2

策略:
- pytest-asyncio + httpx AsyncClient + ASGITransport
- in-memory SQLite + StaticPool
- 复用 _shared_engine fixture 模式 (W10 A1 / W12 A2)
"""
import base64
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


# ====== Fixtures ======

@pytest_asyncio.fixture(scope="function")
async def _shared_engine():
    """共享的 in-memory SQLite engine (供 client + clean 共用)"""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from core.models import Base
    # Side-effect imports: 让 review_router / doc_gen_router / signature_router / doc_workflow_router 表注册到 metadata
    from api import review_router, backlog_router, doc_gen_router  # noqa: F401
    from core import doc_workflow  # noqa: F401

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


# ====== 5 律师函样例 (mock 8 律师反馈场景) ======

# 样例 1: 货物买卖 - L1 王律师 (时限梯度)
LETTER_V2_SAMPLE_1 = {
    "letter_id": "LS-v2-2026-001",
    "lawyer_id": "L1-王律师",
    "lawyer_license_no": "LAW-2024-000001",
    "law_firm": "北京元枢律师事务所",
    "lawyer_name": "王律师",
    "lawyer_phone": "010-12345678",
    "lawyer_email": "wang@lexprime.com",
    "law_firm_addr": "北京市朝阳区建国路 1 号",
    "recipient": "上海某贸易有限公司",
    "recipient_addr": "上海市浦东新区某路 88 号",
    "sender": "北京某科技公司",
    "subject": "要求立即支付拖欠货款",
    "facts_parties": "委托人北京某科技公司与贵司上海某贸易有限公司于 2026-01-15 签订《货物买卖合同》(合同编号 GM-2026-001)",
    "facts_subject": "标的: 货物一批, 合同金额人民币 200 万元",
    "facts_breach": "贵司自 2026-04 起拖欠货款, 截至本函发出之日累计拖欠 80 万元, 经多次催告仍未支付",
    "facts": "委托人北京某科技公司与贵司于 2026-01-15 签订《货物买卖合同》, 标的 200 万元, 贵司自 2026-04 起拖欠货款 80 万元, 经多次催告仍未支付。",
    "legal_basis": "《中华人民共和国民法典》第五百七十七条 当事人一方不履行合同义务或者履行合同义务不符合约定的, 应当承担继续履行、采取补救措施或者赔偿损失等违约责任。",
    "legal_basis_civil": "民法典第五百七十七条",
    "demand_step_1": "第一步: 贵司于 2026-08-15 前一次性支付拖欠货款 80 万元",
    "demand_step_2": "第二步: 贵司书面确认付款计划并加盖公章",
    "demand_step_3": "第三步: 贵司支付逾期利息 (按 LPR 计算)",
    "demands": "1. 贵司于 2026-08-15 前一次性支付 80 万元\n2. 贵司书面确认付款计划\n3. 贵司支付逾期利息",
    "deadline_primary": "2026-08-15",
    "deadline_grad_first": "15",
    "deadline_grad_second": "30",
    "deadline_grad_final": "2026-09-15",
    "deadline": "2026-08-15",
    "consequence_other": "委托人将向相关行业协会举报贵司失信行为",
    "consequence": "1. 委托人将依法提起民事诉讼\n2. 委托人将向行业协会举报",
    "amount_in_dispute": "800000",
    "interest_rate": "年利率 12% (按 4 倍 LPR 计算)",
    "risk_dim_facts": "ok",
    "risk_dim_legal": "ok",
    "risk_dim_demand": "ok",
    "risk_dim_deadline": "ok",
    "risk_dim_consequence": "ok",
    "risk_overall": "low",
    "doc_workflow_state": "draft",
    "date": "2026 年 6 月 30 日",
}

# 样例 2: 物业纠纷 - L2 李律师 (法条具体引用)
LETTER_V2_SAMPLE_2 = {
    "letter_id": "LS-v2-2026-002",
    "lawyer_id": "L2-李律师",
    "lawyer_license_no": "LAW-2024-000002",
    "law_firm": "上海元枢律师事务所",
    "lawyer_name": "李律师",
    "lawyer_phone": "021-87654321",
    "lawyer_email": "li@lexprime.com",
    "law_firm_addr": "上海市黄浦区南京路 100 号",
    "recipient": "某物业管理有限公司",
    "recipient_addr": "上海市黄浦区某小区物业中心",
    "sender": "某小区业主委员会",
    "subject": "要求整改物业服务并赔偿损失",
    "facts_parties": "委托人某小区业主委员会代表全体业主与贵物业公司于 2025-01 签订《物业服务合同》",
    "facts_subject": "标的: 小区物业管理服务 (1200 户业主)",
    "facts_breach": "贵司自 2025-06 起多次出现设施维护不到位、安全管理缺失等问题, 已严重影响业主正常生活",
    "facts": "业主委员会代表 1200 户业主与贵物业公司签订《物业服务合同》, 贵司自 2025-06 起多次出现设施维护不到位问题, 已严重影响业主正常生活。",
    "legal_basis": "《中华人民共和国民法典》第九百四十二条 物业服务人应当按照约定和物业的使用性质, 妥善维修、养护、清洁、绿化和经营管理业主共有部分。",
    "legal_basis_civil": "民法典第九百四十二条",
    "demand_step_1": "第一步: 贵司于 2026-08-20 前完成设施全面检修",
    "demand_step_2": "第二步: 贵司书面提交整改方案并赔偿业主损失 5 万元",
    "demand_step_3": "",
    "demands": "1. 贵司完成设施全面检修\n2. 贵司提交整改方案\n3. 贵司赔偿业主损失",
    "deadline_primary": "2026-08-20",
    "deadline_grad_first": "15",
    "deadline_grad_second": "30",
    "deadline_grad_final": "2026-09-20",
    "deadline": "2026-08-20",
    "consequence_other": "委托人将代表业主向住建局投诉并申请更换物业公司",
    "consequence": "1. 委托人将代表业主向住建局投诉\n2. 委托人将申请更换物业公司\n3. 委托人将依法起诉",
    "amount_in_dispute": "50000",
    "interest_rate": "年利率 6% (按 LPR 计算)",
    "risk_dim_facts": "ok",
    "risk_dim_legal": "ok",
    "risk_dim_demand": "ok",
    "risk_dim_deadline": "ok",
    "risk_dim_consequence": "ok",
    "risk_overall": "low",
    "doc_workflow_state": "draft",
    "date": "2026 年 6 月 30 日",
}

# 样例 3: 劳动关系 - L3 张律师 (三段式事实)
LETTER_V2_SAMPLE_3 = {
    "letter_id": "LS-v2-2026-003",
    "lawyer_id": "L3-张律师",
    "lawyer_license_no": "LAW-2024-000003",
    "law_firm": "广州元枢律师事务所",
    "lawyer_name": "张律师",
    "lawyer_phone": "020-12345678",
    "lawyer_email": "zhang@lexprime.com",
    "law_firm_addr": "广州市天河区珠江路 200 号",
    "recipient": "某科技公司",
    "recipient_addr": "广州市天河区某科技园 5 号楼",
    "sender": "员工陈某",
    "subject": "要求支付拖欠工资及加班费",
    "facts_parties": "委托人陈某 (身份证 440101199001011234) 与贵司于 2024-03-01 签订《劳动合同》, 任职技术部高级工程师",
    "facts_subject": "标的: 工资 + 加班费 + 经济补偿金",
    "facts_breach": "贵司自 2026-01 起连续 6 个月拖欠工资, 累计金额 18 万元, 且未支付加班费 5 万元",
    "facts": "委托人陈某与贵司签订《劳动合同》任职高级工程师, 贵司自 2026-01 起连续 6 个月拖欠工资 18 万元, 且未支付加班费 5 万元。",
    "legal_basis": "《中华人民共和国劳动法》第五十条 工资应当以货币形式按月支付给劳动者本人。不得克扣或者无故拖欠劳动者的工资。",
    "legal_basis_civil": "劳动法第五十条",
    "demand_step_1": "第一步: 贵司于 2026-07-30 前一次性支付拖欠工资 18 万元",
    "demand_step_2": "第二步: 贵司支付加班费 5 万元",
    "demand_step_3": "第三步: 贵司支付经济补偿金 (按 N+1 标准)",
    "demands": "1. 贵司支付拖欠工资 18 万元\n2. 贵司支付加班费 5 万元\n3. 贵司支付经济补偿金",
    "deadline_primary": "2026-07-30",
    "deadline_grad_first": "15",
    "deadline_grad_second": "30",
    "deadline_grad_final": "2026-08-30",
    "deadline": "2026-07-30",
    "consequence_other": "委托人将向劳动监察部门投诉并申请劳动仲裁",
    "consequence": "1. 委托人将向劳动监察部门投诉\n2. 委托人将申请劳动仲裁\n3. 委托人将申请法院强制执行",
    "amount_in_dispute": "230000",
    "interest_rate": "年利率 6% (按 LPR 计算)",
    "risk_dim_facts": "ok",
    "risk_dim_legal": "ok",
    "risk_dim_demand": "ok",
    "risk_dim_deadline": "ok",
    "risk_dim_consequence": "ok",
    "risk_overall": "low",
    "doc_workflow_state": "draft",
    "date": "2026 年 6 月 30 日",
}

# 样例 4: 知识产权 - L4 赵律师 (后果量化)
LETTER_V2_SAMPLE_4 = {
    "letter_id": "LS-v2-2026-004",
    "lawyer_id": "L4-赵律师",
    "lawyer_license_no": "LAW-2024-000004",
    "law_firm": "深圳元枢律师事务所",
    "lawyer_name": "赵律师",
    "lawyer_phone": "0755-12345678",
    "lawyer_email": "zhao@lexprime.com",
    "law_firm_addr": "深圳市南山区科技园 100 号",
    "recipient": "某电商平台",
    "recipient_addr": "深圳市南山区某电商大厦",
    "sender": "某知名商标权利人",
    "subject": "要求立即停止商标侵权并赔偿损失",
    "facts_parties": "委托人某知名商标权利人 (注册商标号 XXXXXXXX) 与贵电商平台于 2025-12 发现大量销售侵权商品",
    "facts_subject": "标的: 商标侵权损害赔偿",
    "facts_breach": "贵平台自 2025-12 起销售侵犯委托人注册商标的商品, 累计销售金额 500 万元",
    "facts": "委托人某知名商标权利人与贵电商平台于 2025-12 发现侵权商品, 贵平台累计销售侵权商品 500 万元。",
    "legal_basis": "《中华人民共和国商标法》第五十七条 有下列行为之一的, 均属侵犯注册商标专用权: (一) 未经商标注册人的许可, 在同一种商品上使用与其注册商标相同的商标的。",
    "legal_basis_civil": "商标法第五十七条",
    "demand_step_1": "第一步: 贵平台于 2026-07-25 前下架所有侵权商品链接",
    "demand_step_2": "第二步: 贵平台提供侵权商家信息",
    "demand_step_3": "第三步: 贵平台赔偿委托人损失 100 万元",
    "demands": "1. 贵平台下架所有侵权商品\n2. 贵平台提供商家信息\n3. 贵平台赔偿损失 100 万元",
    "deadline_primary": "2026-07-25",
    "deadline_grad_first": "10",
    "deadline_grad_second": "20",
    "deadline_grad_final": "2026-08-25",
    "deadline": "2026-07-25",
    "consequence_other": "委托人将向市场监管部门举报并提起商标侵权诉讼",
    "consequence": "1. 委托人将向市场监管部门举报\n2. 委托人将提起商标侵权诉讼\n3. 委托人将申请法院禁令",
    "amount_in_dispute": "1000000",
    "interest_rate": "年利率 12% (按 4 倍 LPR 计算)",
    "risk_dim_facts": "ok",
    "risk_dim_legal": "ok",
    "risk_dim_demand": "ok",
    "risk_dim_deadline": "ok",
    "risk_dim_consequence": "ok",
    "risk_overall": "low",
    "doc_workflow_state": "draft",
    "date": "2026 年 6 月 30 日",
}

# 样例 5: 借贷纠纷 - L6 周律师 (签字栏 + 执业证号 + 期限梯度)
LETTER_V2_SAMPLE_5 = {
    "letter_id": "LS-v2-2026-005",
    "lawyer_id": "L6-周律师",
    "lawyer_license_no": "LAW-2024-000006",
    "law_firm": "杭州元枢律师事务所",
    "lawyer_name": "周律师",
    "lawyer_phone": "0571-12345678",
    "lawyer_email": "zhou@lexprime.com",
    "law_firm_addr": "杭州市西湖区文三路 50 号",
    "recipient": "刘某",
    "recipient_addr": "杭州市西湖区某小区 5 号楼 201",
    "sender": "王某",
    "subject": "要求偿还借款本金及利息",
    "facts_parties": "委托人王某与刘某系朋友关系, 于 2024-06-15 签订《借款协议》",
    "facts_subject": "标的: 借款本金 50 万元 + 利息",
    "facts_breach": "刘某自借款到期日 (2025-06-15) 起未归还任何本金及利息, 累计拖欠 12 个月",
    "facts": "委托人王某与刘某签订《借款协议》借款 50 万元, 约定年利率 10%, 2025-06-15 到期, 至今未还。",
    "legal_basis": "《中华人民共和国民法典》第六百七十五条 借款人应当按照约定的期限返还借款。",
    "legal_basis_civil": "民法典第六百七十五条",
    "demand_step_1": "第一步: 刘某于 2026-08-10 前一次性偿还借款本金 50 万元",
    "demand_step_2": "第二步: 刘某支付借款利息 (按年利率 10% 计算)",
    "demand_step_3": "第三步: 刘某支付逾期利息 (按 4 倍 LPR 计算)",
    "demands": "1. 刘某偿还本金 50 万元\n2. 刘某支付借款利息\n3. 刘某支付逾期利息",
    "deadline_primary": "2026-08-10",
    "deadline_grad_first": "15",
    "deadline_grad_second": "30",
    "deadline_grad_final": "2026-09-10",
    "deadline": "2026-08-10",
    "consequence_other": "委托人将依法提起民事诉讼并申请财产保全",
    "consequence": "1. 委托人将依法提起民事诉讼\n2. 委托人将申请财产保全\n3. 委托人将申请法院强制执行",
    "amount_in_dispute": "500000",
    "interest_rate": "年利率 10% (按 4 倍 LPR 计算)",
    "risk_dim_facts": "ok",
    "risk_dim_legal": "ok",
    "risk_dim_demand": "ok",
    "risk_dim_deadline": "ok",
    "risk_dim_consequence": "ok",
    "risk_overall": "low",
    "doc_workflow_state": "draft",
    "date": "2026 年 6 月 30 日",
}

# 模拟客户签字图片 (1x1 PNG, base64 编码)
SAMPLE_PNG_BASE64 = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
)


# ====== Health: letter_v2 加载 ======

class TestLetterV2Health:
    async def test_health_includes_letter_v2(self, client):
        """/health 端点报告 letter_v2 加载状态"""
        resp = await client.get("/api/doc-gen/health")
        assert resp.status_code == 200
        body = resp.json()
        assert "additional_versions" in body
        assert "letter_v2" in body["additional_versions"]
        v2_status = body["additional_versions"]["letter_v2"]
        assert v2_status["loaded"] is True
        assert v2_status["version"] == "v2.0-w15"
        assert v2_status["field_count"] >= 20  # 至少 20 个占位符

    async def test_health_endpoints_include_letter_v2(self, client):
        """/health 端点列表包含 POST /api/doc-gen/letter-v2"""
        resp = await client.get("/api/doc-gen/health")
        body = resp.json()
        assert "POST /api/doc-gen/letter-v2" in body["endpoints"]
        # 也保留旧端点 (backward compat)
        assert "POST /api/doc-gen/letter" in body["endpoints"]

    async def test_health_version_w15(self, client):
        """/health service version 升到 0.2.0-w15"""
        resp = await client.get("/api/doc-gen/health")
        body = resp.json()
        assert body["version"] == "0.2.0-w15"

    async def test_health_templates_v1_still_loaded(self, client):
        """W9 v1 主模板仍加载 (backward compat)"""
        resp = await client.get("/api/doc-gen/health")
        body = resp.json()
        for t in ("complaint", "defense", "contract", "letter"):
            assert body["templates"][t]["loaded"] is True


# ====== letter_v2 端点: 5 律师函样例 ======

class TestLetterV2FiveSamples:
    """5 律师函样例 (mock 8 律师反馈场景)"""

    async def test_sample1_trade_dispute_L1(self, client):
        """样例 1: 货物买卖 (L1 王律师 → 时限梯度)"""
        payload = {
            "lawyer_id": "L1-王律师",
            "case_id": "TEST-LS2-001",
            "fields": LETTER_V2_SAMPLE_1,
        }
        resp = await client.post("/api/doc-gen/letter-v2", json=payload)
        assert resp.status_code == 200, f"letter-v2 sample1 failed: {resp.text}"
        body = resp.json()

        assert body["doc_type"] == "letter_v2"
        assert body["template_id"] == "letter_v2"
        assert body["template_version"] == "v2.0-w15"
        # L1 王律师反馈: 时限梯度
        assert "15" in body["markdown"]  # deadline_grad_first
        assert "2026-08-15" in body["markdown"]  # deadline_primary
        assert "2026-09-15" in body["markdown"]  # deadline_grad_final
        # 三段式事实
        assert "北京某科技公司" in body["markdown"]
        assert "200 万元" in body["markdown"]
        assert "80 万元" in body["markdown"]
        # 后果量化
        assert "800000" in body["markdown"] or "80 万元" in body["markdown"]
        assert "LPR" in body["markdown"]
        # AI 5 维度风险标注块
        assert "AI 风险标注" in body["markdown"]
        assert "事实" in body["markdown"]
        assert "法律意见" in body["markdown"]
        assert "要求" in body["markdown"]
        assert "时限" in body["markdown"]
        assert "后果" in body["markdown"]
        # 签字栏
        assert "执业证号" in body["markdown"]
        assert "客户签字" in body["markdown"]
        # doc_workflow 集成说明
        assert "doc_workflow" in body["markdown"]
        # disclaimer v2
        assert "v2.0-w15" in body["disclaimer"]

    async def test_sample2_property_dispute_L2(self, client):
        """样例 2: 物业纠纷 (L2 李律师 → 法条具体引用)"""
        payload = {
            "lawyer_id": "L2-李律师",
            "case_id": "TEST-LS2-002",
            "fields": LETTER_V2_SAMPLE_2,
        }
        resp = await client.post("/api/doc-gen/letter-v2", json=payload)
        assert resp.status_code == 200, f"letter-v2 sample2 failed: {resp.text}"
        body = resp.json()
        # L2 李律师反馈: 法条具体引用《民法典》第 XXX 条
        assert "民法典第九百四十二条" in body["markdown"] or "第九百四十二条" in body["markdown"]
        # 三段式事实
        assert "业主委员会" in body["markdown"]
        assert "1200 户" in body["markdown"]
        assert "设施维护" in body["markdown"]

    async def test_sample3_labor_dispute_L3(self, client):
        """样例 3: 劳动关系 (L3 张律师 → 三段式事实)"""
        payload = {
            "lawyer_id": "L3-张律师",
            "case_id": "TEST-LS2-003",
            "fields": LETTER_V2_SAMPLE_3,
        }
        resp = await client.post("/api/doc-gen/letter-v2", json=payload)
        assert resp.status_code == 200, f"letter-v2 sample3 failed: {resp.text}"
        body = resp.json()
        # L3 张律师反馈: 三段式事实 (当事人/标的/违约行为)
        assert "(一) 当事人" in body["markdown"]
        assert "(二) 标的" in body["markdown"]
        assert "(三) 违约行为" in body["markdown"]
        # 标的金额
        assert "18 万元" in body["markdown"]
        assert "5 万元" in body["markdown"]

    async def test_sample4_ip_dispute_L4(self, client):
        """样例 4: 知识产权 (L4 赵律师 → 后果量化)"""
        payload = {
            "lawyer_id": "L4-赵律师",
            "case_id": "TEST-LS2-004",
            "fields": LETTER_V2_SAMPLE_4,
        }
        resp = await client.post("/api/doc-gen/letter-v2", json=payload)
        assert resp.status_code == 200, f"letter-v2 sample4 failed: {resp.text}"
        body = resp.json()
        # L4 赵律师反馈: 后果量化 (本金 + 利息 + 维权成本)
        assert "1000000" in body["markdown"] or "100 万元" in body["markdown"]
        assert "LPR" in body["markdown"]
        assert "律师费" in body["markdown"]
        assert "诉讼费" in body["markdown"]
        # 商标法引用
        assert "商标法" in body["markdown"]

    async def test_sample5_loan_dispute_L6(self, client):
        """样例 5: 借贷纠纷 (L6 周律师 → 签字栏 + 执业证号 + 期限梯度)"""
        payload = {
            "lawyer_id": "L6-周律师",
            "case_id": "TEST-LS2-005",
            "fields": LETTER_V2_SAMPLE_5,
        }
        resp = await client.post("/api/doc-gen/letter-v2", json=payload)
        assert resp.status_code == 200, f"letter-v2 sample5 failed: {resp.text}"
        body = resp.json()
        # L6 周律师反馈: 客户签字栏 + 律师执业证号
        assert "执业证号" in body["markdown"]
        assert "LAW-2024-000006" in body["markdown"]
        assert "委托人签名" in body["markdown"]
        # 时限梯度
        assert "主期限" in body["markdown"]
        assert "首期回复" in body["markdown"]
        assert "宽限期" in body["markdown"]
        assert "最终期限" in body["markdown"]
        # 借款金额
        assert "50 万元" in body["markdown"]


# ====== docx + 模板字段 ======

class TestLetterV2Docx:
    async def test_letter_v2_docx_valid(self, client):
        """letter_v2 docx 是有效 Word 文件 (PK header)"""
        payload = {"lawyer_id": "L1", "fields": LETTER_V2_SAMPLE_1}
        resp = await client.post("/api/doc-gen/letter-v2", json=payload)
        body = resp.json()
        assert body["docx_base64"] is not None
        decoded = base64.b64decode(body["docx_base64"])
        assert decoded.startswith(b"PK")  # ZIP signature
        assert body["docx_filename"].startswith("letter_v2-")
        assert body["docx_filename"].endswith(".docx")

    async def test_letter_v2_field_count(self):
        """letter_v2 模板字段数 >= 20"""
        from api.doc_gen_router import _load_template, _extract_placeholders

        md = _load_template("letter_v2")
        keys = _extract_placeholders(md)
        assert len(keys) >= 20, f"letter_v2 should have >= 20 placeholders, got {len(keys)}"

    async def test_letter_v2_field_count_in_health(self, client):
        """/health letter_v2 field_count >= 20"""
        resp = await client.get("/api/doc-gen/health")
        body = resp.json()
        assert body["additional_versions"]["letter_v2"]["field_count"] >= 20

    async def test_letter_v2_filled_and_missing(self, client):
        """letter_v2 filled/missing 字段准确"""
        # 只填部分字段
        partial = {
            "letter_id": "LS-PARTIAL-001",
            "recipient": "某公司",
            "sender": "某客户",
            "subject": "测试",
            "lawyer_name": "测试律师",
        }
        payload = {"lawyer_id": "L1", "fields": partial}
        resp = await client.post("/api/doc-gen/letter-v2", json=payload)
        body = resp.json()
        # 已填充
        assert "letter_id" in body["filled_fields"]
        assert "recipient" in body["filled_fields"]
        # 缺失字段 (新 v2.0 字段)
        assert "lawyer_license_no" in body["missing_fields"]
        assert "deadline_primary" in body["missing_fields"]
        assert "amount_in_dispute" in body["missing_fields"]
        # 缺失字段占位符保留
        assert "{{lawyer_license_no}}" in body["markdown"]
        assert "{{deadline_primary}}" in body["markdown"]


# ====== 输出格式 + 错误处理 ======

class TestLetterV2OutputFormat:
    async def test_markdown_only(self, client):
        """output_format=markdown 时, docx_base64 应为 None"""
        payload = {
            "lawyer_id": "L1",
            "fields": LETTER_V2_SAMPLE_1,
            "output_format": "markdown",
        }
        resp = await client.post("/api/doc-gen/letter-v2", json=payload)
        body = resp.json()
        assert body["docx_base64"] is None
        assert body["docx_filename"] is None
        assert body["docx_size_bytes"] is None
        # markdown 仍有内容
        assert len(body["markdown"]) > 1000  # letter_v2 内容比 v1 更丰富

    async def test_invalid_output_format(self, client):
        """非法 output_format → 422"""
        payload = {
            "lawyer_id": "L1",
            "fields": LETTER_V2_SAMPLE_1,
            "output_format": "pdf",
        }
        resp = await client.post("/api/doc-gen/letter-v2", json=payload)
        assert resp.status_code == 422

    async def test_empty_lawyer_id_rejected(self, client):
        """lawyer_id 为空 → 422"""
        payload = {"lawyer_id": "", "fields": LETTER_V2_SAMPLE_1}
        resp = await client.post("/api/doc-gen/letter-v2", json=payload)
        assert resp.status_code == 422


# ====== doc_workflow 5 状态转换集成 ======

class TestLetterV2DocWorkflowIntegration:
    """letter_v2 + doc_workflow (W12 A2 commit 829d25c) 集成验证"""

    async def test_full_5_state_transitions(self, client):
        """完整 5 状态转换: draft → ai_reviewed → lawyer_reviewed → client_signed → archived"""
        doc_id = "ls-v2-test-doc-001"

        # 1) draft → ai_reviewed (初次转换时新建 doc 记录)
        resp = await client.patch(
            f"/api/doc-gen/{doc_id}/state",
            json={
                "target_state": "ai_reviewed",
                "actor": "L1-王律师",
                "reason": "AI 风险标注完成",
                "case_id": "TEST-LS2-001",
                "doc_type": "letter",
                "risk_summary": {
                    "fatal_count": 0,
                    "major_count": 0,
                    "advisory_count": 1,
                    "ok_count": 4,
                    "overall_risk_level": "low",
                },
            },
        )
        assert resp.status_code == 200, f"ai_reviewed failed: {resp.text}"
        body = resp.json()
        assert body["state"] == "ai_reviewed"
        assert body["doc_type"] == "letter"
        assert body["history"][-1]["from_state"] == "draft"
        assert body["history"][-1]["to_state"] == "ai_reviewed"

        # 2) ai_reviewed → lawyer_reviewed
        resp = await client.patch(
            f"/api/doc-gen/{doc_id}/state",
            json={
                "target_state": "lawyer_reviewed",
                "actor": "L1-王律师",
                "reason": "律师审核通过",
                "lawyer_notes": "事实清楚, 法律依据充分, 要求具体可执行, 时限合理",
            },
        )
        assert resp.status_code == 200, f"lawyer_reviewed failed: {resp.text}"
        body = resp.json()
        assert body["state"] == "lawyer_reviewed"
        assert "事实清楚" in body["lawyer_notes"]

        # 3) lawyer_reviewed → client_signed (先上传签字)
        sig_resp = await client.post(
            f"/api/signature/{doc_id}",
            json={
                "signature_image": SAMPLE_PNG_BASE64,
                "license_no": "LAW-2024-000001",
                "client_name": "委托人王某",
                "client_id_no": "110101199001011234",
                "notes": "客户当面签字确认",
            },
        )
        assert sig_resp.status_code == 200, f"signature upload failed: {sig_resp.text}"

        resp = await client.patch(
            f"/api/doc-gen/{doc_id}/state",
            json={
                "target_state": "client_signed",
                "actor": "L1-王律师",
                "reason": "客户签字确认",
            },
        )
        assert resp.status_code == 200, f"client_signed failed: {resp.text}"
        body = resp.json()
        assert body["state"] == "client_signed"
        assert body["has_signature"] is True

        # 4) client_signed → archived
        resp = await client.patch(
            f"/api/doc-gen/{doc_id}/state",
            json={
                "target_state": "archived",
                "actor": "L1-王律师",
                "reason": "归档留痕",
            },
        )
        assert resp.status_code == 200, f"archived failed: {resp.text}"
        body = resp.json()
        assert body["state"] == "archived"
        assert len(body["history"]) == 4  # 4 次转换

    async def test_invalid_skip_transition_rejected(self, client):
        """非法跳级转换: draft → client_signed → 409"""
        doc_id = "ls-v2-test-doc-002"
        resp = await client.patch(
            f"/api/doc-gen/{doc_id}/state",
            json={
                "target_state": "client_signed",
                "actor": "L1-王律师",
                "reason": "非法跳级",
                "case_id": "TEST-LS2-002",
                "doc_type": "letter",
            },
        )
        assert resp.status_code == 409

    async def test_transition_back(self, client):
        """transition_back 回退到上一状态 (律师返工)"""
        doc_id = "ls-v2-test-doc-003"
        # 先到 ai_reviewed
        await client.patch(
            f"/api/doc-gen/{doc_id}/state",
            json={
                "target_state": "ai_reviewed",
                "actor": "L1-王律师",
                "reason": "AI 标注",
                "case_id": "TEST-LS2-003",
                "doc_type": "letter",
            },
        )
        # 再到 lawyer_reviewed
        await client.patch(
            f"/api/doc-gen/{doc_id}/state",
            json={
                "target_state": "lawyer_reviewed",
                "actor": "L1-王律师",
                "reason": "律师审核",
            },
        )
        # 回退到 ai_reviewed (返工)
        resp = await client.patch(
            f"/api/doc-gen/{doc_id}/state",
            json={
                "transition_back": True,
                "actor": "L1-王律师",
                "reason": "需要补充事实",
            },
        )
        assert resp.status_code == 200, f"transition_back failed: {resp.text}"
        body = resp.json()
        assert body["state"] == "ai_reviewed"


# ====== signature_router 集成 ======

class TestLetterV2SignatureRouterIntegration:
    """letter_v2 + signature_router (W12 A2 commit 85278db) 集成验证"""

    async def test_signature_upload_and_workflow_check(self, client):
        """上传签字 + 工作流 has_signature=True"""
        doc_id = "ls-v2-test-sig-001"
        # 1) 创建 workflow (draft → ai_reviewed)
        await client.patch(
            f"/api/doc-gen/{doc_id}/state",
            json={
                "target_state": "ai_reviewed",
                "actor": "L1-王律师",
                "reason": "AI 标注",
                "case_id": "TEST-LS2-SIG",
                "doc_type": "letter",
            },
        )
        # 2) 上传签字
        sig_resp = await client.post(
            f"/api/signature/{doc_id}",
            json={
                "signature_image": SAMPLE_PNG_BASE64,
                "license_no": "LAW-2024-000001",
                "client_name": "委托人",
                "notes": "测试签字",
            },
        )
        assert sig_resp.status_code == 200
        # 3) 查询签字状态
        get_resp = await client.get(f"/api/signature/{doc_id}")
        assert get_resp.status_code == 200
        body = get_resp.json()
        assert body["has_signature"] is True
        assert body["license_no"] == "LAW-2024-000001"
        assert body["image_size_bytes"] > 0

    async def test_signature_invalid_base64_rejected(self, client):
        """非法 base64 → 422"""
        doc_id = "ls-v2-test-sig-invalid"
        resp = await client.post(
            f"/api/signature/{doc_id}",
            json={
                "signature_image": "not-valid-base64!@#$",
                "license_no": "LAW-2024-000001",
            },
        )
        assert resp.status_code == 422


# ====== 风险标注 (5 维度 letter) ======

class TestLetterV2RiskAnnotation:
    """letter_v2 + 风险标注 (W12 A2 reviewer 扩展)"""

    async def test_risk_annotation_5_dimensions(self, client):
        """letter 风险标注: 5 维度 (事实/法律意见/要求/时限/后果)"""
        # 先用 letter_v2 模板生成 markdown
        gen_resp = await client.post(
            "/api/doc-gen/letter-v2",
            json={"lawyer_id": "L1", "fields": LETTER_V2_SAMPLE_1},
        )
        doc_markdown = gen_resp.json()["markdown"]
        doc_id = gen_resp.json()["gen_id"]

        # 调用风险标注端点
        ann_resp = await client.post(
            f"/api/doc-gen/{doc_id}/risk-annotation",
            json={
                "doc_id": doc_id,
                "doc_type": "letter",
                "doc_markdown": doc_markdown,
                "case_id": "TEST-LS2-RISK",
            },
        )
        assert ann_resp.status_code == 200, f"risk-annotation failed: {ann_resp.text}"
        body = ann_resp.json()

        # 验证 5 维度
        dimensions = [d["dimension"] for d in body["dimensions"]]
        assert "事实" in dimensions
        assert "法律意见" in dimensions
        assert "要求" in dimensions
        assert "时限" in dimensions
        assert "后果" in dimensions

        # 验证 risk_level 字段合法
        for dim in body["dimensions"]:
            assert dim["risk_level"] in ("ok", "advisory", "major", "fatal")


# ====== prompt v2.0 YAML 校验 ======

class TestPromptV2YAML:
    """prompts/skill3_letter_v2.yaml 结构校验"""

    def test_yaml_exists(self):
        """YAML 文件存在"""
        import os
        path = r"E:\元枢法智前端\yuanxing\backend\cases-crawler\prompts\skill3_letter_v2.yaml"
        assert os.path.exists(path), f"YAML not found: {path}"

    def test_yaml_top_level_keys(self):
        """YAML 顶层 keys 完整"""
        import yaml
        path = r"E:\元枢法智前端\yuanxing\backend\cases-crawler\prompts\skill3_letter_v2.yaml"
        with open(path, encoding="utf-8") as f:
            d = yaml.safe_load(f)

        required_keys = [
            "version", "based_on", "template_id", "owner", "created_at",
            "metadata", "risk_dimensions", "risk_threshold",
            "prompt_template", "disclaimer", "endpoint_integration", "validation",
        ]
        for k in required_keys:
            assert k in d, f"missing top-level key: {k}"

    def test_yaml_version_v2(self):
        """version 是 v2.0-w15"""
        import yaml
        path = r"E:\元枢法智前端\yuanxing\backend\cases-crawler\prompts\skill3_letter_v2.yaml"
        with open(path, encoding="utf-8") as f:
            d = yaml.safe_load(f)
        assert d["version"] == "2.0-w15"
        assert d["based_on"] == "v1.0-w9"
        assert d["template_id"] == "letter_v2"

    def test_yaml_risk_threshold_lowered(self):
        """风险阈值从 0.7 降到 0.6"""
        import yaml
        path = r"E:\元枢法智前端\yuanxing\backend\cases-crawler\prompts\skill3_letter_v2.yaml"
        with open(path, encoding="utf-8") as f:
            d = yaml.safe_load(f)
        assert d["risk_threshold"]["v1"] == 0.7
        assert d["risk_threshold"]["v2"] == 0.6

    def test_yaml_5_risk_dimensions(self):
        """5 风险维度 (事实/法律意见/要求/时限/后果)"""
        import yaml
        path = r"E:\元枢法智前端\yuanxing\backend\cases-crawler\prompts\skill3_letter_v2.yaml"
        with open(path, encoding="utf-8") as f:
            d = yaml.safe_load(f)
        dims = [dim["name"] for dim in d["risk_dimensions"]]
        assert "事实" in dims
        assert "法律意见" in dims
        assert "要求" in dims
        assert "时限" in dims
        assert "后果" in dims
        assert len(dims) == 5

    def test_yaml_mock_feedback_count(self):
        """mock 反馈数 = 8"""
        import yaml
        path = r"E:\元枢法智前端\yuanxing\backend\cases-crawler\prompts\skill3_letter_v2.yaml"
        with open(path, encoding="utf-8") as f:
            d = yaml.safe_load(f)
        assert d["metadata"]["mock_feedback_count"] == 8
        assert len(d["metadata"]["feedback_scenarios"]) == 8

    def test_yaml_endpoint_integration_complete(self):
        """endpoint_integration 含 4 端点 (含 doc_workflow + signature_router)"""
        import yaml
        path = r"E:\元枢法智前端\yuanxing\backend\cases-crawler\prompts\skill3_letter_v2.yaml"
        with open(path, encoding="utf-8") as f:
            d = yaml.safe_load(f)
        ep = d["endpoint_integration"]
        assert "POST /api/doc-gen/letter-v2" in ep["generation"]
        assert "PATCH /api/doc-gen/{doc_id}/state" in ep["workflow_state"]
        assert "POST /api/signature/{doc_id}" in ep["signature"]
        assert len(ep["workflow_states_5"]) == 5


# ====== 模板版本对比 (v1 vs v2) ======

class TestLetterV2VsV1:
    async def test_v2_has_more_fields_than_v1(self, client):
        """letter_v2 比 letter_v1 字段更多 (体现 8 律师反馈迭代)"""
        resp = await client.get("/api/doc-gen/health")
        body = resp.json()
        v1_count = body["templates"]["letter"]["field_count"]
        v2_count = body["additional_versions"]["letter_v2"]["field_count"]
        assert v2_count > v1_count, f"v2 ({v2_count}) should have more fields than v1 ({v1_count})"

    async def test_v1_endpoint_still_works(self, client):
        """backward compat: v1 letter 端点仍可用"""
        v1_payload = {
            "lawyer_id": "L4-赵律师",
            "fields": {
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
                "facts": "委托人于 2026-01 至 2026-05 期间, 累计向贵司供应货物价值人民币 200 万元。",
                "demands": "1. 请贵司于本函送达之日起 15 日内, 一次性支付拖欠货款 80 万元。",
                "deadline": "2026-07-15",
                "consequence": "1. 委托人将依法提起民事诉讼。",
            },
        }
        resp = await client.post("/api/doc-gen/letter", json=v1_payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["doc_type"] == "letter"
        assert body["template_id"] == "letter_v1"
        assert body["template_version"] == "v1.0-w9"
        # disclaimer 应是 v1
        assert "v0.1.0-w9" in body["disclaimer"]


# ====== pytest 配置 ======

def test_module_smoke():
    """模块 smoke 测试: 所有 imports 正常"""
    import api.doc_gen_router  # noqa: F401
    import api.doc_workflow_router  # noqa: F401
    import yaml

    # YAML 文件可加载
    path = r"E:\元枢法智前端\yuanxing\backend\cases-crawler\prompts\skill3_letter_v2.yaml"
    d = yaml.safe_load(open(path, encoding="utf-8").read())
    assert d["version"] == "2.0-w15"