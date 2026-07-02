"""
合同审查规则引擎 - 内置审查规则

包含 7 大类 25+ 条内置审查规则:
- 主体资格类 (3条)
- 权利义务类 (4条)
- 违约责任类 (4条)
- 争议解决类 (4条)
- 金额期限类 (4条)
- 文字表述类 (3条)
- 法律风险类 (3条)
"""
from __future__ import annotations

from typing import List

from skills.contract_review.rule_engine.models import (
    Rule,
    RuleSeverity,
    RuleCategory,
)
from skills.contract_review.rule_engine.manager import RuleManager


def build_default_rules() -> List[Rule]:
    """构建默认规则列表"""
    rules: List[Rule] = []

    # ==================== 主体资格类 ====================

    rules.append(Rule(
        rule_id="party_001",
        name="当事人信息不完整",
        category=RuleCategory.PARTY_QUALIFICATION,
        severity=RuleSeverity.MEDIUM,
        description="合同当事人的名称/姓名、住所等基本信息不完整",
        patterns=[
            r"(?:甲方|乙方|丙方|当事人)(?:.{0,20}?)(?:信息|名称|姓名|住所|地址)(?:.{0,10}?)(?:不完整|缺失|未填写|待补充)",
            r"(?:甲方|乙方|丙方)(?:\s*[：:]\s*)(?:\n|$)",
            r"(?:住所|地址|法定代表人)(?:\s*[：:]\s*)(?:\n|$)",
        ],
        modification_suggestion="请补充完整的当事人信息，包括名称/姓名、住所/地址、法定代表人、联系方式等。",
        one_click_fix="【当事人信息】\n甲方：[公司全称]，住所地：[详细地址]，法定代表人：[姓名]，统一社会信用代码：[代码]。\n乙方：[公司全称/姓名]，住所地：[详细地址]，法定代表人/身份证号：[信息]。",
        legal_basis=[
            "《民法典》第四百七十条",
            "《民法典》第四百九十条",
        ],
    ))

    rules.append(Rule(
        rule_id="party_002",
        name="缺少法定代表人信息",
        category=RuleCategory.PARTY_QUALIFICATION,
        severity=RuleSeverity.LOW,
        description="合同中未提及法定代表人或负责人信息",
        patterns=[
            r"甲方(?:(?!法定代表人|负责人).){0,200}乙方",
            r"乙方(?:(?!法定代表人|负责人).){0,200}丙方",
        ],
        modification_suggestion="建议补充法定代表人或负责人信息，明确签约代表权限。",
        one_click_fix="法定代表人：[姓名]，职务：[职务名称]",
        legal_basis=[
            "《民法典》第六十一条",
            "《民法典》第五百零四条",
        ],
    ))

    rules.append(Rule(
        rule_id="party_003",
        name="缺少统一社会信用代码",
        category=RuleCategory.PARTY_QUALIFICATION,
        severity=RuleSeverity.LOW,
        description="企业作为当事人时未提供统一社会信用代码",
        patterns=[
            r"(?:公司|企业|有限责任|股份有限)(?:(?!统一社会信用代码|社会信用代码|信用代码).){0,100}",
        ],
        modification_suggestion="建议补充企业的统一社会信用代码，便于核实主体身份。",
        one_click_fix="统一社会信用代码：[91开头的18位代码]",
        legal_basis=[
            "《民法典》第六十六条",
        ],
    ))

    # ==================== 权利义务类 ====================

    rules.append(Rule(
        rule_id="rights_001",
        name="权利义务不对等",
        category=RuleCategory.RIGHTS_OBLIGATIONS,
        severity=RuleSeverity.HIGH,
        description="合同双方权利义务明显不对等，存在显失公平情形",
        patterns=[
            r"(?:单方|一方|甲方)(?:\s*)(?:解除|终止|变更|修改)(?:\s*)(?:权|合同|协议)",
            r"甲方(?:.{0,30}?)可(?:.{0,20}?)单方",
            r"(?:只有|仅)(?:\s*)(?:甲方|乙方)(?:\s*)(?:享有|拥有|有)(?:\s*)(?:权利|权限)",
        ],
        modification_suggestion="建议调整权利义务分配，确保双方权利义务对等，避免显失公平条款被撤销。",
        one_click_fix="任何一方均有权在对方根本违约时单方解除本合同。",
        legal_basis=[
            "《民法典》第一百五十一条",
            "《民法典》第六条",
        ],
    ))

    rules.append(Rule(
        rule_id="rights_002",
        name="模糊条款表述",
        category=RuleCategory.RIGHTS_OBLIGATIONS,
        severity=RuleSeverity.MEDIUM,
        description="合同条款表述模糊，易引发争议",
        patterns=[
            r"合理期限",
            r"(?:尽快|及时|立即|马上|适时)",
            r"(?:适当|相应)(?:\s*)(?:费用|补偿|赔偿)",
            r"重大(?:影响|变化|违约)",
        ],
        modification_suggestion="建议将模糊表述替换为具体明确的约定，如具体期限、具体金额等。",
        one_click_fix="将「合理期限」修改为「30个工作日内」",
        legal_basis=[
            "《民法典》第四百六十六条",
            "《民法典》第五百一十条",
        ],
    ))

    rules.append(Rule(
        rule_id="rights_003",
        name="缺失关键条款",
        category=RuleCategory.RIGHTS_OBLIGATIONS,
        severity=RuleSeverity.HIGH,
        description="合同缺少标的、数量、质量等关键条款",
        patterns=[
            r"(?:标的|标的物)(?:.{0,10}?)(?:未约定|待定|另行协商)",
            r"(?:数量|质量)(?:.{0,10}?)(?:未约定|待定|另行协商)",
            r"(?:履行|交付)(?:.{0,10}?)(?:时间|期限|地点)(?:.{0,10}?)(?:未约定|待定|另行协商)",
        ],
        modification_suggestion="建议补充合同必备条款，明确标的、数量、质量、履行期限等核心内容。",
        one_click_fix="【标的条款】\n合同标的：[具体描述]；数量：[具体数量]；质量标准：[国家标准/行业标准/约定标准]。",
        legal_basis=[
            "《民法典》第四百七十条",
            "《民法典》第五百一十条",
        ],
    ))

    rules.append(Rule(
        rule_id="rights_004",
        name="保密义务缺失",
        category=RuleCategory.RIGHTS_OBLIGATIONS,
        severity=RuleSeverity.LOW,
        description="合同未约定保密义务",
        patterns=[
            r"(?:合作|技术|商务)(?:(?!保密).){0,300}$",
        ],
        modification_suggestion="建议增加保密条款，明确保密范围、期限和违约责任。",
        one_click_fix="【保密条款】\n双方对在合同履行过程中知悉的对方商业秘密、技术秘密等保密信息负有保密义务，保密期限为合同终止后3年。",
        legal_basis=[
            "《民法典》第五百零一条",
            "《反不正当竞争法》第九条",
        ],
    ))

    # ==================== 违约责任类 ====================

    rules.append(Rule(
        rule_id="breach_001",
        name="违约金过高",
        category=RuleCategory.BREACH_OF_CONTRACT,
        severity=RuleSeverity.HIGH,
        description="违约金约定过高，可能超过司法保护上限",
        patterns=[
            r"违约金(?:.{0,15}?)(?:月|年|日)(?:.{0,15}?)(?:百分之|%|千分之|万分之)",
            r"逾期(?:.{0,10}?)按(?:.{0,20}?)加收(?:.{0,10}?)违约金",
            r"违约金(?:.{0,10}?)(?:相当于|为)(?:.{0,10}?)(?:总金额|总额|合同金额)(?:.{0,5}?)(?:的)?(?:30|40|50|60|70|80|90|100)%",
        ],
        modification_suggestion="建议调整违约金计算方式，以不超过实际损失的30%为宜，避免过高违约金被法院调减。",
        one_click_fix="逾期违约金按每日万分之五计算，累计不超过合同总金额的20%。",
        legal_basis=[
            "《民法典》第五百八十五条",
            "《最高人民法院关于适用〈中华人民共和国民法典〉合同编通则若干问题的解释》第六十五条",
        ],
    ))

    rules.append(Rule(
        rule_id="breach_002",
        name="违约金过低",
        category=RuleCategory.BREACH_OF_CONTRACT,
        severity=RuleSeverity.LOW,
        description="违约金约定过低，不足以弥补损失",
        patterns=[
            r"违约金(?:.{0,10}?)(?:仅为|只有|为)(?:.{0,10}?)(?:合同|总)(?:.{0,5}?)(?:金额)?(?:的)?(?:0\.[0-5]|1|2)%",
        ],
        modification_suggestion="建议适当提高违约金比例，确保违约方承担相应违约责任。",
        one_click_fix="违约金调整为合同总金额的10%。",
        legal_basis=[
            "《民法典》第五百八十五条",
        ],
    ))

    rules.append(Rule(
        rule_id="breach_003",
        name="违约责任不对等",
        category=RuleCategory.BREACH_OF_CONTRACT,
        severity=RuleSeverity.HIGH,
        description="双方违约责任约定明显不对等",
        patterns=[
            r"甲方违约(?:.{0,50}?)乙方违约(?:.{0,50}?)(?:违约金|赔偿)",
            r"(?:甲方|乙方)(?:.{0,20}?)支付违约金(?:.{0,20}?)(?:甲方|乙方)(?:.{0,20}?)支付",
        ],
        modification_suggestion="建议调整违约责任条款，确保双方违约责任对等。",
        one_click_fix="双方任何一方违约的，应向守约方支付合同总金额20%的违约金。",
        legal_basis=[
            "《民法典》第六条",
            "《民法典》第一百五十一条",
        ],
    ))

    rules.append(Rule(
        rule_id="breach_004",
        name="缺失违约条款",
        category=RuleCategory.BREACH_OF_CONTRACT,
        severity=RuleSeverity.MEDIUM,
        description="合同未约定违约责任条款",
        patterns=[
            r"(?:合同|协议)(?:(?!违约).){0,500}$",
        ],
        modification_suggestion="建议增加违约责任条款，明确违约情形和责任承担方式。",
        one_click_fix="【违约责任】\n任何一方违反本合同约定的，应向守约方支付违约金，并赔偿由此造成的全部损失。",
        legal_basis=[
            "《民法典》第五百七十七条",
            "《民法典》第五百八十四条",
        ],
    ))

    # ==================== 争议解决类 ====================

    rules.append(Rule(
        rule_id="dispute_001",
        name="管辖约定不明确",
        category=RuleCategory.DISPUTE_RESOLUTION,
        severity=RuleSeverity.MEDIUM,
        description="争议管辖条款约定不明确，可能无效",
        patterns=[
            r"争议(?:.{0,20}?)协商(?:.{0,20}?)解决(?:(?!法院|仲裁|诉讼).){0,50}",
            r"(?:向|由)(?:.{0,10}?)(?:有关|相关)(?:.{0,10}?)(?:部门|机关)(?:.{0,10}?)(?:解决|处理)",
            r"(?:管辖|法院)(?:.{0,10}?)(?:另行约定|协商确定|待定)",
        ],
        modification_suggestion="建议明确约定管辖法院或仲裁机构，避免管辖争议。",
        one_click_fix="因本合同发生的争议，双方协商不成的，任何一方均可向原告住所地人民法院提起诉讼。",
        legal_basis=[
            "《民事诉讼法》第三十五条",
            "《最高人民法院关于适用〈中华人民共和国民事诉讼法〉的解释》第三十条",
        ],
    ))

    rules.append(Rule(
        rule_id="dispute_002",
        name="仲裁机构错误",
        category=RuleCategory.DISPUTE_RESOLUTION,
        severity=RuleSeverity.HIGH,
        description="仲裁机构名称不准确或不存在，可能导致仲裁条款无效",
        patterns=[
            r"仲裁委员会(?:.{0,10}?)(?:所在地|当地|本市|本地区)",
            r"(?:经济|合同|劳动)(?:.{0,5}?)仲裁(?:.{0,5}?)委员会",
            r"向(?:.{0,10}?)仲裁(?:.{0,10}?)申请(?:仲裁|裁决)",
        ],
        modification_suggestion="建议使用准确的仲裁机构全称，如「上海仲裁委员会」、「中国国际经济贸易仲裁委员会」等。",
        one_click_fix="因本合同发生的争议，双方协商不成的，提交上海仲裁委员会，按照申请仲裁时该会现行有效的仲裁规则进行仲裁。",
        legal_basis=[
            "《仲裁法》第十六条",
            "《仲裁法》第十八条",
        ],
    ))

    rules.append(Rule(
        rule_id="dispute_003",
        name="争议解决方式缺失",
        category=RuleCategory.DISPUTE_RESOLUTION,
        severity=RuleSeverity.MEDIUM,
        description="合同未约定争议解决方式",
        patterns=[
            r"(?:合同|协议)(?:(?!争议|纠纷|管辖|法院|仲裁|诉讼).){0,300}$",
        ],
        modification_suggestion="建议增加争议解决条款，明确争议解决方式和管辖机构。",
        one_click_fix="【争议解决】\n因本合同引起的或与本合同有关的任何争议，双方应友好协商解决；协商不成的，任何一方均有权向合同签订地有管辖权的人民法院提起诉讼。",
        legal_basis=[
            "《民事诉讼法》第二十四条",
            "《民法典》第五百七十七条",
        ],
    ))

    rules.append(Rule(
        rule_id="dispute_004",
        name="约定管辖与法定管辖冲突",
        category=RuleCategory.DISPUTE_RESOLUTION,
        severity=RuleSeverity.HIGH,
        description="约定管辖法院与法律规定冲突，可能无效",
        patterns=[
            r"甲方(?:.{0,5}?)住所地(?:.{0,5}?)法院",
            r"乙方(?:.{0,5}?)住所地(?:.{0,5}?)法院",
            r"(?:不动产|建设工程|票据)(?:.{0,20}?)由(?:.{0,10}?)(?:甲方|乙方)(?:.{0,10}?)住所地",
        ],
        modification_suggestion="建议审查约定管辖是否符合法律规定，不动产纠纷、建设工程施工合同纠纷等适用专属管辖。",
        one_click_fix="因本合同发生的争议，由不动产所在地人民法院管辖。",
        legal_basis=[
            "《民事诉讼法》第三十四条",
            "《民事诉讼法》第三十五条",
        ],
    ))

    # ==================== 金额期限类 ====================

    rules.append(Rule(
        rule_id="amount_001",
        name="金额大小写不一致",
        category=RuleCategory.AMOUNT_DEADLINE,
        severity=RuleSeverity.HIGH,
        description="合同金额大写与小写不一致",
        detection_function="check_amount_mismatch",
        modification_suggestion="请核实并统一金额的大小写表述，以大写为准。",
        one_click_fix="合同总金额：人民币[大写金额]（¥[小写金额]）",
        legal_basis=[
            "《民法典》第四百六十六条",
        ],
    ))

    rules.append(Rule(
        rule_id="amount_002",
        name="期限约定模糊",
        category=RuleCategory.AMOUNT_DEADLINE,
        severity=RuleSeverity.MEDIUM,
        description="合同履行期限约定不明确",
        patterns=[
            r"期限(?:.{0,10}?)(?:待定|另行约定|协商确定|视情况)",
            r"(?:交付|履行|完成)(?:.{0,10}?)(?:尽快|及时|合理时间|适当时候)",
            r"(?:生效|有效)(?:.{0,10}?)(?:长期|永久|不定期)",
        ],
        modification_suggestion="建议明确具体的履行期限，如具体的起止日期或工作日数。",
        one_click_fix="交付期限：甲方应于2026年12月31日前完成交付。",
        legal_basis=[
            "《民法典》第五百一十条",
            "《民法典》第五百一十一条",
        ],
    ))

    rules.append(Rule(
        rule_id="amount_003",
        name="付款条件不明确",
        category=RuleCategory.AMOUNT_DEADLINE,
        severity=RuleSeverity.MEDIUM,
        description="付款条件和时间约定不明确",
        patterns=[
            r"(?:付款|支付)(?:.{0,10}?)(?:另行约定|协商确定|待定)",
            r"(?:款项|费用)(?:.{0,10}?)(?:验收合格后|交付后|完成后)(?:.{0,10}?)(?:支付|付款)(?:.{0,20}?$)",
        ],
        modification_suggestion="建议明确付款的具体条件、时间节点和支付方式。",
        one_click_fix="【付款方式】\n合同签订后3个工作日内支付30%预付款，验收合格后10个工作日内支付70%尾款。",
        legal_basis=[
            "《民法典》第五百一十条",
            "《民法典》第六百二十六条",
        ],
    ))

    rules.append(Rule(
        rule_id="amount_004",
        name="缺少价格条款",
        category=RuleCategory.AMOUNT_DEADLINE,
        severity=RuleSeverity.HIGH,
        description="合同缺少价款或报酬条款",
        patterns=[
            r"(?:合同|协议)(?:(?!价款|报酬|金额|价格|费用).){0,400}$",
        ],
        modification_suggestion="建议补充价款或报酬条款，明确金额、支付方式和时间。",
        one_click_fix="【价款条款】\n合同总价款为人民币[X]元（大写：[大写金额]）。",
        legal_basis=[
            "《民法典》第四百七十条",
            "《民法典》第五百一十一条",
        ],
    ))

    # ==================== 文字表述类 ====================

    rules.append(Rule(
        rule_id="wording_001",
        name="错别字检测",
        category=RuleCategory.WORDING,
        severity=RuleSeverity.INFO,
        description="合同中可能存在错别字",
        detection_function="check_typos",
        modification_suggestion="请核对并修正错别字。",
        one_click_fix="已修正错别字",
        legal_basis=[],
    ))

    rules.append(Rule(
        rule_id="wording_002",
        name="歧义表述",
        category=RuleCategory.WORDING,
        severity=RuleSeverity.MEDIUM,
        description="条款表述存在歧义，可能产生不同理解",
        patterns=[
            r"等等|等相关",
            r"(?:包括|包含)(?:.{0,20}?)等",
            r"(?:大概|大约|左右|上下)(?:.{0,10}?)(?:元|天|日|个)",
            r"(?:原则上|一般情况下|通常)(?:.{0,20}?)(?:应当|可以|需要)",
        ],
        modification_suggestion="建议使用更精确的表述，避免歧义。",
        one_click_fix="将「包括...等」修改为「包括但不限于...」",
        legal_basis=[
            "《民法典》第四百六十六条",
        ],
    ))

    rules.append(Rule(
        rule_id="wording_003",
        name="格式不规范",
        category=RuleCategory.WORDING,
        severity=RuleSeverity.INFO,
        description="合同格式不规范，如缺少页码、签章位置等",
        detection_function="check_format",
        modification_suggestion="建议统一格式，增加页码、签署页等。",
        one_click_fix="已调整格式",
        legal_basis=[],
    ))

    # ==================== 法律风险类 ====================

    rules.append(Rule(
        rule_id="legal_001",
        name="违法条款",
        category=RuleCategory.LEGAL_RISK,
        severity=RuleSeverity.HIGH,
        description="合同条款可能违反法律强制性规定",
        patterns=[
            r"(?:本|该)\s*合同(?:.{0,10}?)不得(?:.{0,10}?)解除",
            r"(?:造成|导致)(?:.{0,10}?)人身伤害(?:.{0,10}?)免责",
            r"(?:故意|重大过失)(?:.{0,10}?)免责",
            r"概不负责|一律免责",
        ],
        modification_suggestion="建议删除或修改违反法律强制性规定的条款，避免条款无效。",
        one_click_fix="删除违法免责条款，保留合法的责任限制约定。",
        legal_basis=[
            "《民法典》第一百五十三条",
            "《民法典》第五百零六条",
        ],
    ))

    rules.append(Rule(
        rule_id="legal_002",
        name="无效条款风险",
        category=RuleCategory.LEGAL_RISK,
        severity=RuleSeverity.HIGH,
        description="合同条款可能存在无效情形",
        patterns=[
            r"(?:排除|限制)(?:.{0,10}?)主要权利",
            r"(?:免除|减轻)(?:.{0,10}?)主要义务",
            r"最终解释权(?:.{0,10}?)归",
            r"一经售出|概不退换",
        ],
        modification_suggestion="建议审查条款是否符合公平原则，避免格式条款无效。",
        one_click_fix="调整为公平合理的条款，双方权利义务对等。",
        legal_basis=[
            "《民法典》第四百九十七条",
            "《民法典》第四百九十八条",
            "《消费者权益保护法》第二十六条",
        ],
    ))

    rules.append(Rule(
        rule_id="legal_003",
        name="缺失必要条款",
        category=RuleCategory.LEGAL_RISK,
        severity=RuleSeverity.MEDIUM,
        description="合同缺少法律规定的必要条款",
        patterns=[
            r"(?:本合同|本协议)(?:.{0,200}?)(?:未尽事宜|其他事项)(?:.{0,20}?)双方(?:协商|约定)",
        ],
        modification_suggestion="建议补充完善合同必备条款，减少履行争议。",
        one_click_fix="【其他约定】\n本合同未尽事宜，双方可另行签订补充协议，补充协议与本合同具有同等法律效力。",
        legal_basis=[
            "《民法典》第四百七十条",
        ],
    ))

    return rules


def register_default_rules(manager: RuleManager) -> None:
    """将默认规则注册到规则管理器"""
    rules = build_default_rules()
    for rule in rules:
        manager.register_rule(rule)

    # 注册自定义检测函数
    manager.register_detection_function("check_amount_mismatch", check_amount_mismatch)
    manager.register_detection_function("check_typos", check_typos)
    manager.register_detection_function("check_format", check_format)


import re


def check_amount_mismatch(text: str) -> List[dict]:
    """检测金额大小写不一致"""
    results = []
    # 匹配中文大写金额
    cn_amount_pattern = re.compile(r"人民币\s*([零壹贰叁肆伍陆柒捌玖拾佰仟万亿兆]+)\s*[圆元]")
    # 匹配阿拉伯数字金额
    num_amount_pattern = re.compile(r"[¥￥]\s*([0-9,]+(?:\.[0-9]+)?)")

    cn_matches = cn_amount_pattern.findall(text)
    num_matches = num_amount_pattern.findall(text)

    if cn_matches and num_matches and len(cn_matches) != len(num_matches):
        results.append({
            "position": 0,
            "length": len(text),
            "problem": "金额大写与小写数量不一致，建议核对。"
        })

    return results


def check_typos(text: str) -> List[dict]:
    """检测常见错别字"""
    results = []
    common_typos = {
        "签定": "签订",
        "做为": "作为",
        "帐号": "账号",
        "帐单": "账单",
        "身分证": "身份证",
        "法定代表": "法定代表人",
        "住址": "住所地",
    }

    for wrong, right in common_typos.items():
        pos = 0
        while True:
            idx = text.find(wrong, pos)
            if idx == -1:
                break
            results.append({
                "position": idx,
                "length": len(wrong),
                "problem": f"可能存在错别字「{wrong}」，建议改为「{right}」"
            })
            pos = idx + len(wrong)

    return results


def check_format(text: str) -> List[dict]:
    """检测格式问题"""
    results = []
    lines = text.split("\n")

    # 检查是否缺少页码
    if len(lines) > 50 and "第" not in text and "页" not in text:
        results.append({
            "position": 0,
            "length": 0,
            "problem": "合同较长，建议添加页码。"
        })

    # 检查是否有签署位置
    if "甲方（盖章）" not in text and "甲方(盖章)" not in text and "甲方签字" not in text:
        results.append({
            "position": len(text),
            "length": 0,
            "problem": "建议在合同末尾增加签署页。"
        })

    return results
