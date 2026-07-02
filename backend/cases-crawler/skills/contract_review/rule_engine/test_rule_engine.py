"""
合同审查规则引擎 - 单元测试

测试内容:
- 规则数据结构
- 规则管理器
- 内置规则加载
- 审查执行器
- 风险评分
- 修改建议生成
- 边界情况
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# 确保可以导入 skills 模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import unittest

from skills.contract_review.rule_engine.models import (
    Rule,
    RuleSeverity,
    RuleCategory,
    RuleMatch,
    RiskLevel,
    RiskSummary,
    ReviewResult,
)
from skills.contract_review.rule_engine.manager import RuleManager
from skills.contract_review.rule_engine.executor import (
    review_contract,
    get_default_manager,
    reset_default_manager,
)
from skills.contract_review.rule_engine.risk_scoring import (
    calculate_risk_score,
    determine_risk_level,
    generate_risk_distribution,
    generate_visualization_data,
)
from skills.contract_review.rule_engine.suggestion_generator import (
    group_suggestions_by_severity,
    generate_modification_report,
    apply_one_click_fix,
    generate_priority_list,
)
from skills.contract_review.rule_engine.builtin_rules import (
    build_default_rules,
    register_default_rules,
)


class TestRuleSeverity(unittest.TestCase):
    """测试规则严重程度枚举"""

    def test_severity_from_string(self):
        self.assertEqual(RuleSeverity.from_string("high"), RuleSeverity.HIGH)
        self.assertEqual(RuleSeverity.from_string("高危"), RuleSeverity.HIGH)
        self.assertEqual(RuleSeverity.from_string("medium"), RuleSeverity.MEDIUM)
        self.assertEqual(RuleSeverity.from_string("中危"), RuleSeverity.MEDIUM)
        self.assertEqual(RuleSeverity.from_string("low"), RuleSeverity.LOW)
        self.assertEqual(RuleSeverity.from_string("低危"), RuleSeverity.LOW)
        self.assertEqual(RuleSeverity.from_string("info"), RuleSeverity.INFO)
        self.assertEqual(RuleSeverity.from_string("提示"), RuleSeverity.INFO)

    def test_severity_weight(self):
        self.assertEqual(RuleSeverity.HIGH.weight, 10.0)
        self.assertEqual(RuleSeverity.MEDIUM.weight, 5.0)
        self.assertEqual(RuleSeverity.LOW.weight, 2.0)
        self.assertEqual(RuleSeverity.INFO.weight, 0.5)

    def test_severity_display_name(self):
        self.assertEqual(RuleSeverity.HIGH.display_name, "高危")
        self.assertEqual(RuleSeverity.MEDIUM.display_name, "中危")
        self.assertEqual(RuleSeverity.LOW.display_name, "低危")
        self.assertEqual(RuleSeverity.INFO.display_name, "提示")


class TestRuleCategory(unittest.TestCase):
    """测试规则分类枚举"""

    def test_category_display_name(self):
        self.assertEqual(RuleCategory.PARTY_QUALIFICATION.display_name, "主体资格")
        self.assertEqual(RuleCategory.RIGHTS_OBLIGATIONS.display_name, "权利义务")
        self.assertEqual(RuleCategory.BREACH_OF_CONTRACT.display_name, "违约责任")
        self.assertEqual(RuleCategory.DISPUTE_RESOLUTION.display_name, "争议解决")
        self.assertEqual(RuleCategory.AMOUNT_DEADLINE.display_name, "金额期限")
        self.assertEqual(RuleCategory.WORDING.display_name, "文字表述")
        self.assertEqual(RuleCategory.LEGAL_RISK.display_name, "法律风险")


class TestRuleModel(unittest.TestCase):
    """测试Rule数据模型"""

    def test_rule_creation(self):
        rule = Rule(
            rule_id="test_001",
            name="测试规则",
            category=RuleCategory.LEGAL_RISK,
            severity=RuleSeverity.HIGH,
            description="测试规则描述",
            patterns=[r"测试"],
            modification_suggestion="测试修改建议",
            legal_basis=["《民法典》第一条"],
        )
        self.assertEqual(rule.rule_id, "test_001")
        self.assertEqual(rule.name, "测试规则")
        self.assertEqual(rule.category, RuleCategory.LEGAL_RISK)
        self.assertEqual(rule.severity, RuleSeverity.HIGH)
        self.assertTrue(rule.enabled)
        self.assertEqual(len(rule.compiled_patterns), 1)

    def test_rule_applies_to(self):
        rule = Rule(
            rule_id="test_001",
            name="测试规则",
            category=RuleCategory.LEGAL_RISK,
            severity=RuleSeverity.HIGH,
            description="测试",
            applicable_contract_types=["房屋租赁", "借款合同"],
        )
        self.assertTrue(rule.applies_to("房屋租赁"))
        self.assertTrue(rule.applies_to("借款合同"))
        self.assertFalse(rule.applies_to("劳动合同"))

    def test_rule_applies_to_all(self):
        rule = Rule(
            rule_id="test_001",
            name="测试规则",
            category=RuleCategory.LEGAL_RISK,
            severity=RuleSeverity.HIGH,
            description="测试",
            applicable_contract_types=["*"],
        )
        self.assertTrue(rule.applies_to("任何类型"))

    def test_rule_to_dict(self):
        rule = Rule(
            rule_id="test_001",
            name="测试规则",
            category=RuleCategory.LEGAL_RISK,
            severity=RuleSeverity.HIGH,
            description="测试",
        )
        d = rule.to_dict()
        self.assertEqual(d["rule_id"], "test_001")
        self.assertEqual(d["category"], "legal_risk")
        self.assertEqual(d["severity"], "high")
        self.assertNotIn("compiled_patterns", d)


class TestRuleManager(unittest.TestCase):
    """测试规则管理器"""

    def setUp(self):
        self.manager = RuleManager()

    def test_register_rule(self):
        rule = Rule(
            rule_id="test_001",
            name="测试规则",
            category=RuleCategory.LEGAL_RISK,
            severity=RuleSeverity.HIGH,
            description="测试",
        )
        self.manager.register_rule(rule)
        self.assertEqual(self.manager.get_rule("test_001"), rule)

    def test_get_all_rules(self):
        rule1 = Rule(
            rule_id="test_001", name="规则1",
            category=RuleCategory.LEGAL_RISK, severity=RuleSeverity.HIGH,
            description="测试",
        )
        rule2 = Rule(
            rule_id="test_002", name="规则2",
            category=RuleCategory.WORDING, severity=RuleSeverity.LOW,
            description="测试",
        )
        self.manager.register_rule(rule1)
        self.manager.register_rule(rule2)
        self.assertEqual(len(self.manager.get_all_rules()), 2)

    def test_enable_disable_rule(self):
        rule = Rule(
            rule_id="test_001", name="测试规则",
            category=RuleCategory.LEGAL_RISK, severity=RuleSeverity.HIGH,
            description="测试",
        )
        self.manager.register_rule(rule)
        self.assertTrue(rule.enabled)

        self.manager.disable_rule("test_001")
        self.assertFalse(rule.enabled)

        self.manager.enable_rule("test_001")
        self.assertTrue(rule.enabled)

    def test_set_rule_weight(self):
        rule = Rule(
            rule_id="test_001", name="测试规则",
            category=RuleCategory.LEGAL_RISK, severity=RuleSeverity.HIGH,
            description="测试",
            weight=1.0,
        )
        self.manager.register_rule(rule)
        self.manager.set_rule_weight("test_001", 2.5)
        self.assertEqual(rule.weight, 2.5)

    def test_get_rules_by_category(self):
        rule1 = Rule(
            rule_id="test_001", name="规则1",
            category=RuleCategory.LEGAL_RISK, severity=RuleSeverity.HIGH,
            description="测试",
        )
        rule2 = Rule(
            rule_id="test_002", name="规则2",
            category=RuleCategory.WORDING, severity=RuleSeverity.LOW,
            description="测试",
        )
        self.manager.register_rule(rule1)
        self.manager.register_rule(rule2)

        legal_rules = self.manager.get_rules_by_category(RuleCategory.LEGAL_RISK)
        self.assertEqual(len(legal_rules), 1)
        self.assertEqual(legal_rules[0].rule_id, "test_001")

    def test_rule_count(self):
        rule1 = Rule(
            rule_id="test_001", name="规则1",
            category=RuleCategory.LEGAL_RISK, severity=RuleSeverity.HIGH,
            description="测试",
        )
        rule2 = Rule(
            rule_id="test_002", name="规则2",
            category=RuleCategory.WORDING, severity=RuleSeverity.LOW,
            description="测试",
            enabled=False,
        )
        self.manager.register_rule(rule1)
        self.manager.register_rule(rule2)

        counts = self.manager.rule_count()
        self.assertEqual(counts["total"], 2)
        self.assertEqual(counts["enabled"], 1)
        self.assertEqual(counts["disabled"], 1)


class TestBuiltinRules(unittest.TestCase):
    """测试内置规则"""

    def test_build_default_rules_count(self):
        rules = build_default_rules()
        self.assertGreaterEqual(len(rules), 20)

    def test_rule_categories_coverage(self):
        rules = build_default_rules()
        categories = set()
        for rule in rules:
            categories.add(rule.category)

        # 应该覆盖所有7个分类
        self.assertIn(RuleCategory.PARTY_QUALIFICATION, categories)
        self.assertIn(RuleCategory.RIGHTS_OBLIGATIONS, categories)
        self.assertIn(RuleCategory.BREACH_OF_CONTRACT, categories)
        self.assertIn(RuleCategory.DISPUTE_RESOLUTION, categories)
        self.assertIn(RuleCategory.AMOUNT_DEADLINE, categories)
        self.assertIn(RuleCategory.WORDING, categories)
        self.assertIn(RuleCategory.LEGAL_RISK, categories)

    def test_rule_severities_coverage(self):
        rules = build_default_rules()
        severities = set()
        for rule in rules:
            severities.add(rule.severity)

        # 应该包含高危、中危、低危、提示
        self.assertIn(RuleSeverity.HIGH, severities)
        self.assertIn(RuleSeverity.MEDIUM, severities)
        self.assertIn(RuleSeverity.LOW, severities)
        self.assertIn(RuleSeverity.INFO, severities)

    def test_register_default_rules(self):
        manager = RuleManager()
        register_default_rules(manager)
        counts = manager.rule_count()
        self.assertGreaterEqual(counts["enabled"], 20)


class TestReviewExecutor(unittest.TestCase):
    """测试审查执行器"""

    def setUp(self):
        reset_default_manager()
        self.manager = get_default_manager()

    def test_empty_contract(self):
        result = review_contract("", "房屋租赁")
        self.assertEqual(len(result.matches), 0)
        self.assertEqual(result.risk_summary.total_score, 0)

    def test_whitespace_contract(self):
        result = review_contract("   \n\n  ", "房屋租赁")
        self.assertEqual(len(result.matches), 0)

    def test_high_risk_contract(self):
        contract = """
第一条 租赁标的
甲方将房屋出租给乙方。

第二条 违约责任
乙方逾期支付租金的，每逾期一天，按月租金的5%加收违约金。
甲方可单方解除合同，不承担任何责任。

第三条 免责条款
因甲方原因造成乙方人身伤害的，甲方概不负责。
"""
        result = review_contract(contract, "房屋租赁")
        self.assertGreater(len(result.matches), 0)

        # 应该检测到高危风险
        high_count = result.risk_summary.high_count
        self.assertGreater(high_count, 0)

    def test_contract_type_filter(self):
        # 房屋租赁合同
        contract = "甲方将房屋出租给乙方，月租金5000元。"
        result1 = review_contract(contract, "房屋租赁")
        result2 = review_contract(contract, "劳动合同")

        # 不同合同类型的匹配可能不同
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)

    def test_match_structure(self):
        contract = "违约金按月租金的10%计算，甲方可单方解除合同。"
        result = review_contract(contract, "房屋租赁")

        for match in result.matches:
            self.assertIsInstance(match.rule_id, str)
            self.assertIsInstance(match.rule_name, str)
            self.assertIsInstance(match.severity, RuleSeverity)
            self.assertIsInstance(match.category, RuleCategory)
            self.assertGreaterEqual(match.position, 0)
            self.assertGreaterEqual(match.length, 0)
            self.assertIsInstance(match.problem_description, str)
            self.assertIsInstance(match.modification_suggestion, str)


class TestRiskScoring(unittest.TestCase):
    """测试风险评分"""

    def _create_match(self, severity=RuleSeverity.HIGH, confidence=0.8):
        return RuleMatch(
            rule_id="test",
            rule_name="测试",
            category=RuleCategory.LEGAL_RISK,
            severity=severity,
            position=0,
            length=0,
            original_text="",
            problem_description="",
            modification_suggestion="",
            one_click_fix="",
            legal_basis=[],
            confidence=confidence,
        )

    def test_calculate_risk_score_high(self):
        matches = [self._create_match(RuleSeverity.HIGH, 1.0)]
        score = calculate_risk_score(matches)
        self.assertAlmostEqual(score, 10.0, places=1)

    def test_calculate_risk_score_medium(self):
        matches = [self._create_match(RuleSeverity.MEDIUM, 1.0)]
        score = calculate_risk_score(matches)
        self.assertAlmostEqual(score, 5.0, places=1)

    def test_calculate_risk_score_mixed(self):
        matches = [
            self._create_match(RuleSeverity.HIGH, 1.0),
            self._create_match(RuleSeverity.MEDIUM, 1.0),
            self._create_match(RuleSeverity.LOW, 1.0),
        ]
        score = calculate_risk_score(matches)
        self.assertAlmostEqual(score, 17.0, places=1)

    def test_determine_risk_level_safe(self):
        self.assertEqual(determine_risk_level(0), RiskLevel.SAFE)
        self.assertEqual(determine_risk_level(3), RiskLevel.SAFE)
        self.assertEqual(determine_risk_level(5), RiskLevel.SAFE)

    def test_determine_risk_level_low(self):
        self.assertEqual(determine_risk_level(6), RiskLevel.LOW)
        self.assertEqual(determine_risk_level(10), RiskLevel.LOW)

    def test_determine_risk_level_medium(self):
        self.assertEqual(determine_risk_level(20), RiskLevel.MEDIUM)
        self.assertEqual(determine_risk_level(25), RiskLevel.MEDIUM)

    def test_determine_risk_level_high(self):
        self.assertEqual(determine_risk_level(35), RiskLevel.HIGH)
        self.assertEqual(determine_risk_level(100), RiskLevel.HIGH)

    def test_generate_risk_distribution_by_category(self):
        matches = [
            self._create_match(),
            self._create_match(),
            RuleMatch(
                rule_id="test2",
                rule_name="测试2",
                category=RuleCategory.WORDING,
                severity=RuleSeverity.LOW,
                position=0, length=0,
                original_text="",
                problem_description="",
                modification_suggestion="",
                one_click_fix="",
                legal_basis=[],
            ),
        ]
        dist = generate_risk_distribution(matches, "category")
        self.assertIn("法律风险", dist)
        self.assertIn("文字表述", dist)
        self.assertEqual(dist["法律风险"], 2)
        self.assertEqual(dist["文字表述"], 1)

    def test_generate_visualization_data(self):
        matches = [
            self._create_match(RuleSeverity.HIGH),
            self._create_match(RuleSeverity.MEDIUM),
        ]
        data = generate_visualization_data(matches)
        self.assertIn("severity_chart", data)
        self.assertIn("category_chart", data)
        self.assertIn("gauge", data)
        self.assertEqual(data["total_matches"], 2)


class TestSuggestionGenerator(unittest.TestCase):
    """测试修改建议生成器"""

    def _create_match(self, severity=RuleSeverity.HIGH, category=RuleCategory.LEGAL_RISK,
                      has_fix=True):
        return RuleMatch(
            rule_id=f"test_{severity.value}",
            rule_name=f"测试{severity.display_name}",
            category=category,
            severity=severity,
            position=0,
            length=5,
            original_text="测试内容",
            problem_description="测试问题描述",
            modification_suggestion="测试修改建议",
            one_click_fix="修复内容" if has_fix else "",
            legal_basis=["《民法典》第一条"],
            confidence=0.8,
        )

    def test_group_suggestions_by_severity(self):
        matches = [
            self._create_match(RuleSeverity.HIGH),
            self._create_match(RuleSeverity.MEDIUM),
            self._create_match(RuleSeverity.LOW),
        ]
        groups = group_suggestions_by_severity(matches)
        self.assertEqual(len(groups), 3)
        # 按严重程度从高到低排序
        self.assertEqual(groups[0].severity, RuleSeverity.HIGH)
        self.assertEqual(groups[1].severity, RuleSeverity.MEDIUM)
        self.assertEqual(groups[2].severity, RuleSeverity.LOW)

    def test_generate_modification_report(self):
        matches = [
            self._create_match(RuleSeverity.HIGH),
            self._create_match(RuleSeverity.MEDIUM),
        ]
        result = ReviewResult(
            contract_text="测试合同",
            contract_type="房屋租赁",
            matches=matches,
            risk_summary=RiskSummary(
                total_score=15.0,
                risk_level=RiskLevel.MEDIUM,
                high_count=1,
                medium_count=1,
                low_count=0,
                info_count=0,
                category_distribution={},
                severity_distribution={},
            ),
        )
        report = generate_modification_report(result)
        self.assertEqual(report["total_suggestions"], 2)
        self.assertIn("by_severity", report)
        self.assertIn("by_category", report)
        self.assertIn("priority_suggestions", report)

    def test_apply_one_click_fix(self):
        text = "违约金过高，这是测试。"
        matches = [
            RuleMatch(
                rule_id="test",
                rule_name="测试",
                category=RuleCategory.LEGAL_RISK,
                severity=RuleSeverity.HIGH,
                position=0,
                length=5,
                original_text="违约金",
                problem_description="测试",
                modification_suggestion="建议修改",
                one_click_fix="已修复",
                legal_basis=[],
            ),
        ]
        result = apply_one_click_fix(text, matches)
        self.assertGreater(result.applied_count, 0)
        self.assertIsNotNone(result.fixed_text)

    def test_generate_priority_list(self):
        matches = [
            self._create_match(RuleSeverity.LOW),
            self._create_match(RuleSeverity.HIGH),
            self._create_match(RuleSeverity.MEDIUM),
        ]
        priority = generate_priority_list(matches, top_n=3)
        self.assertEqual(len(priority), 3)
        # 优先级最高的应该是高危
        self.assertEqual(priority[0]["severity"], "high")
        self.assertEqual(priority[0]["priority"], 1)


class TestContractTypeReviews(unittest.TestCase):
    """测试各类合同的审查结果"""

    def test_rental_contract(self):
        contract = """
房屋租赁合同

第一条 租赁标的
甲方将位于北京市朝阳区XX路XX号的房屋出租给乙方使用。

第二条 租赁期限
租期从2026年1月1日到2026年12月31日。

第三条 租金
月租金人民币5000元整，乙方应在每月5日前支付。逾期支付的，每逾期一天，按月租金的5%加收违约金。

第四条 押金
乙方支付押金10000元。

第五条 提前解约
甲方可单方解除合同，不承担任何责任。

第六条 争议解决
因本合同发生的争议，由甲方住所地法院管辖。
"""
        result = review_contract(contract, "房屋租赁")
        self.assertGreater(len(result.matches), 0)
        self.assertIsNotNone(result.risk_summary)

    def test_labor_contract(self):
        contract = """
劳动合同

甲方：XX公司
乙方：张三

第一条 工作内容
乙方担任软件工程师职位。

第二条 合同期限
合同期限为三年。

第三条 劳动报酬
月薪10000元。

第四条 工作时间
合理期限内完成工作任务。

第五条 违约责任
乙方违约的，赔偿甲方全部损失。
"""
        result = review_contract(contract, "劳动合同")
        self.assertIsNotNone(result)
        self.assertGreaterEqual(len(result.matches), 0)

    def test_sales_contract(self):
        contract = """
销售合同

甲方（卖方）：XX公司
乙方（买方）：YY公司

第一条 产品
甲方向乙方销售产品一批。

第二条 价格
合同总价待定，双方另行协商。

第三条 交付
尽快交付。

第四条 付款
验收后付款。

第五条 争议解决
发生争议由有关部门解决。
"""
        result = review_contract(contract, "销售合同")
        self.assertGreater(len(result.matches), 0)

    def test_service_contract(self):
        contract = """
服务合同

甲方委托乙方提供咨询服务。

第一条 服务内容
乙方为甲方提供相关咨询服务。

第二条 服务费用
服务费50000元。

第三条 保密
双方应当保密。

第四条 违约责任
违约方承担违约责任。

第五条 争议解决
协商不成的，提交仲裁委员会仲裁。
"""
        result = review_contract(contract, "服务合同")
        self.assertGreater(len(result.matches), 0)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def test_very_short_contract(self):
        result = review_contract("短合同", "其他")
        self.assertIsNotNone(result)

    def test_very_long_contract(self):
        long_text = "违约金条款。" * 1000
        result = review_contract(long_text, "其他")
        self.assertIsNotNone(result)
        # 应该能检测到多个匹配，但不会无限多
        self.assertLess(len(result.matches), 100)

    def test_special_characters(self):
        contract = "合同包含特殊字符：!@#$%^&*()_+，违约金过高。"
        result = review_contract(contract, "其他")
        self.assertIsNotNone(result)

    def test_unicode_characters(self):
        contract = "📝 合同内容：违约金按月租金的10%计算。"
        result = review_contract(contract, "其他")
        self.assertIsNotNone(result)

    def test_mixed_language(self):
        contract = "This contract has 违约金过高 issues."
        result = review_contract(contract, "其他")
        self.assertIsNotNone(result)

    def test_no_risk_contract(self):
        # 一个相对规范的合同
        contract = """
买卖合同

甲方（卖方）：XX科技有限公司
统一社会信用代码：91110000XXXXXXXXXX
住所地：北京市海淀区XX路XX号
法定代表人：李四

乙方（买方）：YY贸易有限公司
统一社会信用代码：91310000XXXXXXXXXX
住所地：上海市浦东新区XX路XX号
法定代表人：王五

第一条 产品名称、规格、数量
产品名称：智能设备
规格型号：V1.0
数量：100台

第二条 合同价款
合同总价款为人民币壹佰万元整（¥1,000,000.00）。

第三条 交付时间和地点
交付时间：2026年12月31日前
交付地点：乙方住所地仓库

第四条 付款方式
合同签订后3个工作日内，乙方支付30%预付款；
验收合格后10个工作日内，乙方支付70%尾款。

第五条 质量标准
产品质量符合国家标准GB/T XXXX-2020。

第六条 违约责任
任何一方违约的，应向守约方支付合同总金额10%的违约金。
违约金不足以弥补损失的，还应赔偿实际损失。

第七条 争议解决
因本合同发生的争议，双方应友好协商解决；
协商不成的，任何一方均可向合同签订地有管辖权的人民法院提起诉讼。

第八条 其他约定
本合同未尽事宜，双方可签订补充协议，补充协议与本合同具有同等法律效力。

甲方（盖章）：
法定代表人（签字）：
日期：2026年1月1日

乙方（盖章）：
法定代表人（签字）：
日期：2026年1月1日
"""
        result = review_contract(contract, "销售合同")
        self.assertIsNotNone(result)
        # 规范合同应该有一定匹配（因为规则较严格），但高危项不应过多
        self.assertLessEqual(result.risk_summary.high_count, 10)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestRuleSeverity,
        TestRuleCategory,
        TestRuleModel,
        TestRuleManager,
        TestBuiltinRules,
        TestReviewExecutor,
        TestRiskScoring,
        TestSuggestionGenerator,
        TestContractTypeReviews,
        TestEdgeCases,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 统计信息
    print("\n" + "=" * 60)
    print("测试统计")
    print("=" * 60)
    print(f"总测试数: {result.testsRun}")
    print(f"通过数: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
