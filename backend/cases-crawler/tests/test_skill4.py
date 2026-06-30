"""
W29 Skill 4 v1 - AI 辅助谈判 - 10 baseline 谈判场景单元测试 (lex-coder · 2026-07-01)

任务: W29 skill4-v1-impl
必读:
- W28 owner commit 8670417 (Skill 4 v1 PRD ~30KB)
- W26 ab59c49 owner commit (Skill 3 v3.0 launch 完整)
- W25 cc14045 owner commit (Skill 3 v3.0 PRD, 38KB)
- W25 1fbfe93 (Skill 3 v3.0 测试 50 测试)
- W23 phase5-5-celebration commit 432a073 (Skill 3 v2.0 全面应用)
- W22 phase5-rust-build-fix commit 2792bd0 (Rust 1.83 LTS + 5x perf)
- W21 skill3-full-rollout commit 6929cc1 (Skill 3 v2.0 全量 100% rollout 样板)
- W19 skill3-gradual commit 2cc2d3a (Skill 3 v2.0 灰度模式)
- W12 829d25c doc_workflow 5 状态机 (38 测试 + 4 文书风险标注)
- W11 PRD V5.0 § 5.4 + § 5.6 + § 11 (5 大价值主张 + 6 大模块 + 法务自检)

10 baseline 谈判场景 (PRD § 4.1):
1. 合同纠纷 - 对方违约 (3 策略 + 胜诉率 + 话术)
2. 合同纠纷 - 自己违约 (同上)
3. 民事侵权 (同上)
4. 婚姻家庭 (同上)
5. 公司股权 (同上)
6. 知识产权 (同上)
7. 劳动仲裁 (同上)
8. 行政复议 (同上)
9. 跨境贸易 (跨境框架额外)
10. 反向博弈演练 (模拟对方律师 / 当事人 / 法官 3 角色)

策略:
- pytest (无 asyncio 依赖, 纯单元测试)
- 模板 fallback 不需要联网 (LLM 调用可选)
- 状态机测试: 5 状态 (draft → ai_reviewed → lawyer_reviewed → settled → archived)
- 实时风险预警: 5 类型 (concede / evidence_miss / deadline_miss / emotional / info_leak)
- 5 维度评分: 事实 / 法律 / 主张 / 时效 / 后果
- 跨境框架: 中英双语 + 跨境法律框架
- 性能测试: 单请求 < 500ms (复用 W22 Rust 5x perf 模式)
"""
import sys
import time
from pathlib import Path

# 让脚本可直接运行 (不依赖 pytest)
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills"))
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "negotiation"))

from negotiation_models import (  # noqa: E402,F401
    NegotiationCaseType,
    OpponentRole,
    StrategyLevel,
    NegotiationState,
    RiskType,
    DimensionType,
    Language,
    NegotiationCase,
    NEGOTIATION_CASE_TYPES,
    OPPONENT_ROLES,
    RISK_TYPES,
    DIMENSION_TYPES,
    CROSS_BORDER_FRAMEWORKS,
)
from negotiation_engine import (  # noqa: E402
    generate_strategies,
    simulate_opponent,
    detect_real_time_risk,
    NegotiationEngineConfig,
)
from debrief_report import (  # noqa: E402
    compute_five_dimension_scores,
    build_debrief_report,
    DebriefReportConfig,
)


# ========== Test 1: 谈判策略生成 - 合同纠纷对方违约 ==========
class TestStrategyGenerationContractOtherPartyBreach:
    """场景 1: 合同纠纷 - 对方违约 → 3 策略 (保守/中等/激进) + 胜诉率 + 话术"""

    def test_case_other_breach_produces_three_strategies(self):
        """对方违约 → 3 策略必须都生成"""
        case = NegotiationCase(
            case_id="C-CON-001",
            case_type=NegotiationCaseType.CONTRACT_DISPUTE,
            breach_side="other",  # 对方违约
            amount_cny=500_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.LAWYER,
            case_facts="被告逾期支付货款 50 万元, 合同约定违约金日万分之五",
            lawyer_id="L001",
        )
        strategies = generate_strategies(case, NegotiationEngineConfig())
        assert len(strategies) == 3, f"期望 3 策略, 实际 {len(strategies)}"
        levels = {s.level for s in strategies}
        assert StrategyLevel.CONSERVATIVE in levels
        assert StrategyLevel.MODERATE in levels
        assert StrategyLevel.AGGRESSIVE in levels

    def test_case_other_breach_win_rate_present(self):
        """胜诉率必须存在 (不能是 '必胜' 等违规词)"""
        case = NegotiationCase(
            case_id="C-CON-002",
            case_type=NegotiationCaseType.CONTRACT_DISPUTE,
            breach_side="other",
            amount_cny=300_000,
            desired_outcome="aggressive",
            opponent_role=OpponentRole.LAWYER,
            case_facts="对方违约逾期交付货物, 合同总价 30 万元",
            lawyer_id="L002",
        )
        strategies = generate_strategies(case, NegotiationEngineConfig())
        for s in strategies:
            assert s.win_rate_estimate, f"胜诉率必填: {s.level}"
            # PRD V5.0 § 11: 禁用"必胜", 必须用类似 "近 3 年本法院 X 件支持原告 Y 件 约 Z%"
            assert "必胜" not in s.win_rate_estimate, f"禁用'必胜': {s.win_rate_estimate}"
            assert "必败" not in s.win_rate_estimate, f"禁用'必败': {s.win_rate_estimate}"

    def test_case_other_breach_advice_present(self):
        """建议话术必须非空 (律师可复制使用)"""
        case = NegotiationCase(
            case_id="C-CON-003",
            case_type=NegotiationCaseType.CONTRACT_DISPUTE,
            breach_side="other",
            amount_cny=1_000_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.LAWYER,
            case_facts="被告逾期付款 100 万元, 已发律师函未回复",
            lawyer_id="L003",
        )
        strategies = generate_strategies(case, NegotiationEngineConfig())
        for s in strategies:
            assert s.advice, f"建议话术必填: {s.level}"
            assert len(s.advice) >= 20, f"建议话术太短: {s.level}"


# ========== Test 2: 谈判策略生成 - 合同纠纷自己违约 ==========
class TestStrategyGenerationContractSelfBreach:
    """场景 2: 合同纠纷 - 自己违约 → 3 策略"""

    def test_self_breach_recommends_conservative_first(self):
        """自己违约场景: 保守策略应放第 1 位 (避免激进加大风险)"""
        case = NegotiationCase(
            case_id="C-CON-004",
            case_type=NegotiationCaseType.CONTRACT_DISPUTE,
            breach_side="self",  # 自己违约
            amount_cny=200_000,
            desired_outcome="aggressive",
            opponent_role=OpponentRole.LAWYER,
            case_facts="我方逾期交货, 合同总价 20 万元",
            lawyer_id="L004",
        )
        strategies = generate_strategies(case, NegotiationEngineConfig())
        # 自己违约时, 保守优先 (低风险)
        assert strategies[0].level == StrategyLevel.CONSERVATIVE, \
            f"自己违约时保守应放第 1, 实际 {strategies[0].level}"


# ========== Test 3: 民事侵权 ==========
class TestStrategyGenerationTort:
    """场景 3: 民事侵权 → 3 策略"""

    def test_tort_case_produces_strategies(self):
        case = NegotiationCase(
            case_id="C-TORT-001",
            case_type=NegotiationCaseType.TORT,
            breach_side="other",
            amount_cny=80_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.PARTY,
            case_facts="交通事故致人受伤, 对方全责, 索赔 8 万元",
            lawyer_id="L005",
        )
        strategies = generate_strategies(case, NegotiationEngineConfig())
        assert len(strategies) == 3
        for s in strategies:
            assert s.win_rate_estimate
            assert s.advice


# ========== Test 4: 婚姻家庭 ==========
class TestStrategyGenerationFamily:
    """场景 4: 婚姻家庭 → 3 策略"""

    def test_family_case_produces_strategies(self):
        case = NegotiationCase(
            case_id="C-FAM-001",
            case_type=NegotiationCaseType.FAMILY,
            breach_side="other",
            amount_cny=300_000,
            desired_outcome="conservative",
            opponent_role=OpponentRole.PARTY,
            case_facts="离婚财产分割, 房产价值 300 万元",
            lawyer_id="L006",
        )
        strategies = generate_strategies(case, NegotiationEngineConfig())
        assert len(strategies) == 3
        # 婚姻家庭偏好保守 (家庭和谐优先)
        assert strategies[0].level == StrategyLevel.CONSERVATIVE


# ========== Test 5: 公司股权 ==========
class TestStrategyGenerationEquity:
    """场景 5: 公司股权 → 3 策略"""

    def test_equity_case_produces_strategies(self):
        case = NegotiationCase(
            case_id="C-EQ-001",
            case_type=NegotiationCaseType.EQUITY,
            breach_side="other",
            amount_cny=5_000_000,
            desired_outcome="aggressive",
            opponent_role=OpponentRole.LAWYER,
            case_facts="股东纠纷, 涉及股权稀释, 公司估值 500 万元",
            lawyer_id="L007",
        )
        strategies = generate_strategies(case, NegotiationEngineConfig())
        assert len(strategies) == 3
        for s in strategies:
            assert "公司法" in s.legal_basis or "股东" in s.legal_basis or "股权" in s.legal_basis or s.legal_basis


# ========== Test 6: 知识产权 ==========
class TestStrategyGenerationIP:
    """场景 6: 知识产权 → 3 策略"""

    def test_ip_case_produces_strategies(self):
        case = NegotiationCase(
            case_id="C-IP-001",
            case_type=NegotiationCaseType.INTELLECTUAL_PROPERTY,
            breach_side="other",
            amount_cny=500_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.LAWYER,
            case_facts="对方侵犯我方商标权, 索赔 50 万元",
            lawyer_id="L008",
        )
        strategies = generate_strategies(case, NegotiationEngineConfig())
        assert len(strategies) == 3
        for s in strategies:
            assert s.legal_basis


# ========== Test 7: 劳动仲裁 ==========
class TestStrategyGenerationLabor:
    """场景 7: 劳动仲裁 → 3 策略"""

    def test_labor_case_produces_strategies(self):
        case = NegotiationCase(
            case_id="C-LAB-001",
            case_type=NegotiationCaseType.LABOR_ARBITRATION,
            breach_side="other",
            amount_cny=50_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.PARTY,
            case_facts="违法解除劳动合同, 索赔经济补偿金 5 万元",
            lawyer_id="L009",
        )
        strategies = generate_strategies(case, NegotiationEngineConfig())
        assert len(strategies) == 3
        # 劳动仲裁偏低额, 通常保守优先
        assert strategies[0].level == StrategyLevel.CONSERVATIVE


# ========== Test 8: 行政复议 ==========
class TestStrategyGenerationAdminReview:
    """场景 8: 行政复议 → 3 策略"""

    def test_admin_review_case_produces_strategies(self):
        case = NegotiationCase(
            case_id="C-ADM-001",
            case_type=NegotiationCaseType.ADMINISTRATIVE_REVIEW,
            breach_side="other",
            amount_cny=0,  # 行政诉讼通常无标的额
            desired_outcome="moderate",
            opponent_role=OpponentRole.JUDGE,  # 行政复议对象
            case_facts="对行政处罚决定不服, 申请行政复议",
            lawyer_id="L010",
        )
        strategies = generate_strategies(case, NegotiationEngineConfig())
        assert len(strategies) == 3
        # 行政复议对手是政府, 保守优先 (避免激化)
        assert strategies[0].level == StrategyLevel.CONSERVATIVE


# ========== Test 9: 跨境贸易 ==========
class TestStrategyGenerationCrossBorder:
    """场景 9: 跨境贸易 → 3 策略 + 跨境法律框架"""

    def test_cross_border_uses_cross_border_framework(self):
        case = NegotiationCase(
            case_id="C-CROSS-001",
            case_type=NegotiationCaseType.CROSS_BORDER_TRADE,
            breach_side="other",
            amount_cny=2_000_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.LAWYER,
            case_facts="国际贸易合同纠纷, 美方违约, 涉及 CISG",
            lawyer_id="L011",
            cross_border=True,
            jurisdiction="纽约州",
            language=Language.EN,
        )
        strategies = generate_strategies(case, NegotiationEngineConfig())
        assert len(strategies) == 3
        # 跨境必须引用跨境法律框架
        for s in strategies:
            assert any(fw in s.legal_basis for fw in ["CISG", "UNCITRAL", "PICC"])
            assert s.cross_border is True

    def test_cross_border_bilingual_support(self):
        """跨境必须支持中英双语"""
        case = NegotiationCase(
            case_id="C-CROSS-002",
            case_type=NegotiationCaseType.CROSS_BORDER_TRADE,
            breach_side="other",
            amount_cny=1_500_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.LAWYER,
            case_facts="英文合同争议, 对方英国公司",
            lawyer_id="L012",
            cross_border=True,
            jurisdiction="英国",
            language=Language.EN,
        )
        strategies = generate_strategies(case, NegotiationEngineConfig())
        # 至少 1 个策略应包含英文话术或双语
        en_or_bilingual = any(
            "negotiation" in s.advice.lower() or "settlement" in s.advice.lower() or "agreement" in s.advice.lower()
            for s in strategies
        )
        assert en_or_bilingual, "跨境场景应支持英文话术"


# ========== Test 10: 反向博弈演练 (模拟对方 3 角色) ==========
class TestOpponentSimulation:
    """场景 10: 反向博弈演练 → 模拟对方律师 / 当事人 / 法官 3 角色"""

    def test_simulate_opponent_lawyer(self):
        """模拟对方律师"""
        case = NegotiationCase(
            case_id="C-SIM-001",
            case_type=NegotiationCaseType.CONTRACT_DISPUTE,
            breach_side="other",
            amount_cny=800_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.LAWYER,
            case_facts="合同纠纷, 对方律师代理, 索赔 80 万元",
            lawyer_id="L013",
        )
        sim = simulate_opponent(case, role=OpponentRole.LAWYER, round_num=1)
        assert sim.role == OpponentRole.LAWYER
        assert sim.response  # 对方回应
        assert sim.legal_basis  # 对方援引法条
        assert sim.tactic  # 对方策略

    def test_simulate_opponent_party(self):
        """模拟对方当事人"""
        case = NegotiationCase(
            case_id="C-SIM-002",
            case_type=NegotiationCaseType.TORT,
            breach_side="other",
            amount_cny=100_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.PARTY,
            case_facts="交通事故, 对方当事人亲自谈判",
            lawyer_id="L014",
        )
        sim = simulate_opponent(case, role=OpponentRole.PARTY, round_num=1)
        assert sim.role == OpponentRole.PARTY
        assert sim.response
        # 当事人更关注心理 + 情绪
        assert sim.psychology_hint or sim.tactic

    def test_simulate_opponent_judge(self):
        """模拟法官"""
        case = NegotiationCase(
            case_id="C-SIM-003",
            case_type=NegotiationCaseType.CONTRACT_DISPUTE,
            breach_side="other",
            amount_cny=500_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.JUDGE,
            case_facts="庭审前预测法官倾向",
            lawyer_id="L015",
        )
        sim = simulate_opponent(case, role=OpponentRole.JUDGE, round_num=1)
        assert sim.role == OpponentRole.JUDGE
        assert sim.response
        # 法官视角更关注法条 + 裁判倾向
        assert sim.legal_basis
        assert sim.tendency or sim.tactic

    def test_simulate_multi_round(self):
        """多轮反向博弈演练"""
        case = NegotiationCase(
            case_id="C-SIM-004",
            case_type=NegotiationCaseType.CONTRACT_DISPUTE,
            breach_side="other",
            amount_cny=600_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.LAWYER,
            case_facts="多轮谈判演练",
            lawyer_id="L016",
        )
        sims = []
        for r in range(1, 6):
            sim = simulate_opponent(case, role=OpponentRole.LAWYER, round_num=r)
            sims.append(sim)
        assert len(sims) == 5
        # 每轮必须不同 (避免重复)
        responses = [s.response for s in sims]
        assert len(set(responses)) >= 3, f"5 轮中至少 3 个不同回应, 实际 {len(set(responses))}"


# ========== Test 11: 实时风险预警 5 类型 ==========
class TestRealTimeRiskDetection:
    """实时风险预警 5 类型: concede / evidence_miss / deadline_miss / emotional / info_leak"""

    def test_detect_concede_risk(self):
        """同意对方不合理要求"""
        text = "好的, 那我们就按您说的违约金比例来, 100% 全额支付"
        alert = detect_real_time_risk(text, risk_type=RiskType.CONCEDE)
        assert alert.triggered is True
        assert alert.risk_type == RiskType.CONCEDE

    def test_detect_evidence_miss_risk(self):
        """漏掉关键证据"""
        text = "对了, 我突然想起我方还有一份补充协议, 上面有对方签字"
        alert = detect_real_time_risk(text, risk_type=RiskType.EVIDENCE_MISS)
        # 这段话其实是发现证据, 不是漏掉; 测试反向: 律师承认没注意
        text2 = "抱歉, 我之前没注意到这份关键的鉴定报告, 请法官允许我方补交"
        alert2 = detect_real_time_risk(text2, risk_type=RiskType.EVIDENCE_MISS)
        # 至少有一个能检测到
        assert alert.triggered is True or alert2.triggered is True

    def test_detect_deadline_miss_risk(self):
        """错过 deadline"""
        text = "今天已经过了举证期限, 我们没能在期限内提交证据"
        alert = detect_real_time_risk(text, risk_type=RiskType.DEADLINE_MISS)
        assert alert.triggered is True
        assert alert.risk_type == RiskType.DEADLINE_MISS

    def test_detect_emotional_risk(self):
        """情绪失控"""
        text = "你胡说! 你这个人怎么不讲道理! 我要投诉你!"
        alert = detect_real_time_risk(text, risk_type=RiskType.EMOTIONAL)
        assert alert.triggered is True

    def test_detect_info_leak_risk(self):
        """信息泄露 (无意中暴露底牌)"""
        text = "其实我们的底线是 30 万, 不能再低了, 这是我们的极限"
        alert = detect_real_time_risk(text, risk_type=RiskType.INFO_LEAK)
        assert alert.triggered is True

    def test_safe_text_no_alert(self):
        """安全文本不触发"""
        text = "我方坚持按合同约定履行, 违约金按 LPR 四倍计算"
        # 全部 5 类型扫描
        triggered_count = 0
        for rt in RISK_TYPES:
            alert = detect_real_time_risk(text, risk_type=rt)
            if alert.triggered:
                triggered_count += 1
        assert triggered_count == 0, f"安全文本不应触发预警, 实际触发 {triggered_count}"


# ========== Test 12: 5 维度评分 + 复盘报告 ==========
class TestDebriefReport:
    """谈判复盘报告: 5 维度评分 (事实/法律/主张/时效/后果)"""

    def test_compute_five_dimension_scores(self):
        """5 维度评分必须全部在 0-1 范围"""
        traj = {
            "facts_match": 0.9,  # 事实维度
            "legal_match": 0.85,
            "demand_reasonable": 0.8,
            "timing": 0.75,
            "consequence": 0.7,
        }
        scores = compute_five_dimension_scores(traj, DebriefReportConfig())
        assert scores.facts == 0.9
        assert scores.legal == 0.85
        assert scores.demand == 0.8
        assert scores.timing == 0.75
        assert scores.consequence == 0.7

    def test_five_dimension_scores_clamped(self):
        """超出 0-1 范围必须 clamp"""
        traj = {
            "facts_match": 1.5,
            "legal_match": -0.3,
            "demand_reasonable": 0.5,
            "timing": 0.5,
            "consequence": 0.5,
        }
        scores = compute_five_dimension_scores(traj, DebriefReportConfig())
        assert 0.0 <= scores.facts <= 1.0
        assert 0.0 <= scores.legal <= 1.0

    def test_build_debrief_report(self):
        """构建谈判复盘报告"""
        traj = {
            "facts_match": 0.9,
            "legal_match": 0.85,
            "demand_reasonable": 0.8,
            "timing": 0.75,
            "consequence": 0.7,
            "key_clauses": ["违约金条款", "管辖条款"],
            "risk_points": ["未及时补充证据"],
            "improvements": ["提前准备证据清单", "演练模拟对方"],
        }
        report = build_debrief_report(
            case_id="C-DB-001",
            lawyer_id="L020",
            trajectory=traj,
            config=DebriefReportConfig(),
        )
        assert report.case_id == "C-DB-001"
        assert report.lawyer_id == "L020"
        assert report.scores.facts == 0.9
        assert len(report.key_clauses) == 2
        assert len(report.risk_points) >= 1
        assert len(report.improvements) >= 1
        assert report.disclaimer  # 必填免责声明

    def test_debrief_report_no_bypass_words(self):
        """复盘报告 narrative 不能含禁用词 (必胜/必败/一定/必定)"""
        traj = {
            "facts_match": 0.6,
            "legal_match": 0.6,
            "demand_reasonable": 0.6,
            "timing": 0.6,
            "consequence": 0.6,
            "key_clauses": ["条款A"],
            "risk_points": ["风险A"],
            "improvements": ["改进A"],
        }
        report = build_debrief_report(
            case_id="C-DB-002",
            lawyer_id="L021",
            trajectory=traj,
            config=DebriefReportConfig(),
        )
        # 检查 narrative 字段不含禁用词
        narrative = report.narrative or ""
        for banned in ["必胜", "必败", "必定", "一定无效", "一定有效", "法院一定"]:
            assert banned not in narrative, f"禁用词 '{banned}' 出现在 narrative: {narrative[:100]}"


# ========== Test 13: 谈判状态机 5 状态 (W12 doc_workflow 模式) ==========
class TestNegotiationStateMachine:
    """谈判状态机: draft → ai_reviewed → lawyer_reviewed → settled → archived"""

    def test_state_machine_initial_state(self):
        """初始状态 = draft"""
        case = NegotiationCase(
            case_id="C-SM-001",
            case_type=NegotiationCaseType.CONTRACT_DISPUTE,
            breach_side="other",
            amount_cny=100_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.LAWYER,
            case_facts="测试",
            lawyer_id="L030",
        )
        assert case.state == NegotiationState.DRAFT

    def test_state_transitions_valid(self):
        """合法状态转移"""
        case = NegotiationCase(
            case_id="C-SM-002",
            case_type=NegotiationCaseType.CONTRACT_DISPUTE,
            breach_side="other",
            amount_cny=100_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.LAWYER,
            case_facts="测试",
            lawyer_id="L031",
        )
        case.transition_to(NegotiationState.AI_REVIEWED)
        assert case.state == NegotiationState.AI_REVIEWED
        case.transition_to(NegotiationState.LAWYER_REVIEWED)
        assert case.state == NegotiationState.LAWYER_REVIEWED
        case.transition_to(NegotiationState.SETTLED)
        assert case.state == NegotiationState.SETTLED
        case.transition_to(NegotiationState.ARCHIVED)
        assert case.state == NegotiationState.ARCHIVED

    def test_state_invalid_transition_blocked(self):
        """非法状态转移必须阻止"""
        case = NegotiationCase(
            case_id="C-SM-003",
            case_type=NegotiationCaseType.CONTRACT_DISPUTE,
            breach_side="other",
            amount_cny=100_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.LAWYER,
            case_facts="测试",
            lawyer_id="L032",
        )
        # draft 不能直接跳到 settled
        try:
            case.transition_to(NegotiationState.SETTLED)
            assert False, "应该抛出异常"
        except ValueError:
            pass  # 期望行为

    def test_state_machine_terminal_states(self):
        """终态不能转移"""
        case = NegotiationCase(
            case_id="C-SM-004",
            case_type=NegotiationCaseType.CONTRACT_DISPUTE,
            breach_side="other",
            amount_cny=100_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.LAWYER,
            case_facts="测试",
            lawyer_id="L033",
        )
        case.transition_to(NegotiationState.AI_REVIEWED)
        case.transition_to(NegotiationState.LAWYER_REVIEWED)
        case.transition_to(NegotiationState.SETTLED)
        case.transition_to(NegotiationState.ARCHIVED)
        # archived 是终态
        try:
            case.transition_to(NegotiationState.SETTLED)
            assert False, "终态不能转移"
        except ValueError:
            pass


# ========== Test 14: 性能测试 (复用 W22 Rust 5x perf 模式) ==========
class TestPerformance:
    """性能基线: 单请求 < 500ms (Python fallback; 生产环境 W22 Rust 5x 后 < 100µs)"""

    def test_strategy_generation_under_500ms(self):
        """单次策略生成 < 500ms"""
        case = NegotiationCase(
            case_id="C-PERF-001",
            case_type=NegotiationCaseType.CONTRACT_DISPUTE,
            breach_side="other",
            amount_cny=500_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.LAWYER,
            case_facts="性能测试",
            lawyer_id="L040",
        )
        t0 = time.time()
        for _ in range(10):
            strategies = generate_strategies(case, NegotiationEngineConfig())
        elapsed_ms = (time.time() - t0) * 1000 / 10  # 平均
        assert elapsed_ms < 500, f"单请求平均 {elapsed_ms:.1f}ms 超 500ms"
        assert len(strategies) == 3

    def test_opponent_simulation_under_500ms(self):
        """单次模拟对方 < 500ms"""
        case = NegotiationCase(
            case_id="C-PERF-002",
            case_type=NegotiationCaseType.CONTRACT_DISPUTE,
            breach_side="other",
            amount_cny=300_000,
            desired_outcome="moderate",
            opponent_role=OpponentRole.LAWYER,
            case_facts="性能测试",
            lawyer_id="L041",
        )
        t0 = time.time()
        for _ in range(10):
            _ = simulate_opponent(case, role=OpponentRole.LAWYER, round_num=1)
        elapsed_ms = (time.time() - t0) * 1000 / 10
        assert elapsed_ms < 500, f"单请求平均 {elapsed_ms:.1f}ms 超 500ms"


# ========== Test 15: 模块图与配置 ==========
class TestModuleConstants:
    """模块常量 + 配置"""

    def test_negotiation_case_types_count(self):
        """PRD § 1.2 至少 8 谈判场景 (8 + 跨境)"""
        assert len(NEGOTIATION_CASE_TYPES) >= 8

    def test_opponent_roles_count(self):
        """PRD § 2.2 3 角色"""
        assert len(OPPONENT_ROLES) == 3
        assert OpponentRole.LAWYER in OPPONENT_ROLES
        assert OpponentRole.PARTY in OPPONENT_ROLES
        assert OpponentRole.JUDGE in OPPONENT_ROLES

    def test_risk_types_count(self):
        """PRD § 2.3 5 风险类型"""
        assert len(RISK_TYPES) == 5
        assert RiskType.CONCEDE in RISK_TYPES
        assert RiskType.EVIDENCE_MISS in RISK_TYPES
        assert RiskType.DEADLINE_MISS in RISK_TYPES
        assert RiskType.EMOTIONAL in RISK_TYPES
        assert RiskType.INFO_LEAK in RISK_TYPES

    def test_dimension_types_count(self):
        """PRD § 4.3 5 维度"""
        assert len(DIMENSION_TYPES) == 5
        assert DimensionType.FACTS in DIMENSION_TYPES
        assert DimensionType.LEGAL in DIMENSION_TYPES
        assert DimensionType.DEMAND in DIMENSION_TYPES
        assert DimensionType.TIMING in DIMENSION_TYPES
        assert DimensionType.CONSEQUENCE in DIMENSION_TYPES

    def test_cross_border_frameworks(self):
        """跨境框架: CISG / UNCITRAL / PICC"""
        assert "CISG" in CROSS_BORDER_FRAMEWORKS
        assert "UNCITRAL" in CROSS_BORDER_FRAMEWORKS or "PICC" in CROSS_BORDER_FRAMEWORKS
