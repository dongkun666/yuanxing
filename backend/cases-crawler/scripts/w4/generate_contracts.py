"""
W4 合同模板生成器 (核心引擎)
LexPrime 数据工程 (W4)

读取骨架 JSON (w4_skeletons/*.json) + 参数化变体, 生成 5000+ 合同模板

输入: backend/cases-crawler/data/contracts/w4_skeletons/{category}.json
输出: backend/cases-crawler/data/contracts/w4_extended/{category}/*.json
"""
from __future__ import annotations

import json
import logging
import random
import sys
from datetime import date, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ============================================================
# 路径配置
# ============================================================
CASES_CRAWLER = Path(__file__).parent.parent.parent  # backend/cases-crawler
SKELETONS_DIR = CASES_CRAWLER / "data" / "contracts" / "w4_skeletons"
OUTPUT_DIR = CASES_CRAWLER / "data" / "contracts" / "w4_extended"

# ============================================================
# 池
# ============================================================
CITIES = ["北京市", "上海市", "广州市", "深圳市", "杭州市", "成都市", "武汉市", "南京市", "苏州市", "重庆市", "西安市", "天津市", "长沙市", "青岛市", "宁波市", "无锡市", "佛山市", "东莞市", "厦门市", "福州市", "济南市", "合肥市", "郑州市", "昆明市"]
DISTRICTS = ["朝阳区", "海淀区", "浦东新区", "黄浦区", "天河区", "南山区", "西湖区", "武侯区"]
CURRENCY_AMOUNTS = ["5000 元", "1 万元", "3 万元", "5 万元", "8 万元", "10 万元", "15 万元", "20 万元", "30 万元", "50 万元", "80 万元", "100 万元", "150 万元", "200 万元", "300 万元", "500 万元"]
DURATIONS = ["1 个月", "3 个月", "6 个月", "1 年", "18 个月", "2 年", "3 年", "5 年", "10 年"]
INTEREST_RATES = ["12%", "15%", "18%", "24%", "36%"]
LPR_MULTIPLIERS = ["LPR", "LPR × 1.3", "LPR × 1.5", "LPR × 2", "LPR × 3", "LPR × 4"]
PENALTY_RATES = ["日万分之五", "日万分之三", "日千分之一", "日千分之三", "月 1%", "月 2%", "月 3%"]
JURISDICTIONS = ["甲方住所地", "乙方住所地", "丙方住所地", "合同签订地", "标的物所在地", "标的物所在地或合同签订地", "北京仲裁委员会", "上海国际仲裁中心", "中国国际经济贸易仲裁委员会"]
PAYMENT_METHODS = ["一次性支付", "分期支付 (3 期)", "分期支付 (6 期)", "分期支付 (12 期)", "按月支付", "按季支付", "按里程碑支付", "预付 30% + 验收 70%"]
GUARANTEE_TYPES = ["保证担保", "抵押担保", "质押担保", "第三方担保", "无担保", "组合担保 (保证+抵押)"]
INDUSTRY_SCENARIOS = ["互联网", "制造业", "金融", "医疗", "教育", "房地产", "物流", "零售", "餐饮", "建筑工程", "法律服务", "咨询服务", "广告", "文化娱乐", "新能源", "农业", "汽车", "化工", "纺织", "电子", "软件", "通信", "能源", "环保", "媒体"]

# 风险标注基础库 (按 clause_title 关键字匹配)
RISK_TEMPLATES = {
    "fatal": {
        "categories": ["显失公平", "违法条款", "重大遗漏", "违约金过高", "金额异常", "隐含义务"],
        "legal_basis_pool": [
            ["《民法典》第五百八十五条 (违约金)"],
            ["《民法典》合同编通则解释第六十五条"],
            ["《民法典》第六百八十条 (禁止高利放贷)"],
            ["《最高人民法院关于审理民间借贷案件适用法律若干问题的规定》第二十五条"],
            ["《劳动合同法》第二十六条 (劳动合同无效)"],
            ["《消费者权益保护法》第二十四条"],
        ],
        "descriptions": [
            "该条款违约金约定过高, 司法实践中通常被调减。",
            "该条款单方加重对方义务, 涉嫌显失公平。",
            "该条款违反法律强制性规定, 可能被认定无效。",
            "该条款存在重大遗漏, 缺乏必要保障机制。",
            "该条款金额异常, 远超合理范围。",
        ],
        "modifications": [
            "建议修改为按 LPR × 1.5 倍 或按日万分之五 等司法保护上限内表述。",
            "建议增加对等权利义务条款, 平衡双方利益。",
            "建议删除违反法律强制性规定的表述, 改为合法替代方案。",
            "建议增加违约金 / 担保 / 争议解决等必备条款。",
            "建议参考行业惯例与司法实践, 调整金额至合理范围。",
        ],
    },
    "major": {
        "categories": ["争议管辖不利", "解除权失衡", "表述模糊", "举证困难", "管辖连接点异常"],
        "legal_basis_pool": [
            ["《民事诉讼法》第二十四条", "《民事诉讼法》第三十五条"],
            ["《民法典》第五百六十三条 (法定解除)"],
            ["《民法典》合同编通则解释"],
        ],
        "descriptions": [
            "该条款约定单方住所地管辖, 对非约定方应诉成本较高。",
            "该条款解除权失衡, 一方解约成本过低或过高。",
            "该条款表述模糊, 关键权利义务不明确。",
            "该条款可能导致举证困难, 建议增加书面确认机制。",
            "该条款管辖连接点异常, 存在被认定无效的风险。",
        ],
        "modifications": [
            "建议修改为标的物所在地 / 合同签订地 / 双方住所地任一 或约定仲裁条款。",
            "建议区分法定解除与违约解除, 违约金按实际损失计算。",
            "建议细化关键概念定义, 附操作细则。",
            "建议增加邮件 / 签收 / 第三方见证等证据保全机制。",
            "建议选择合同履行地或与合同有实际联系地点的法院。",
        ],
    },
    "advisory": {
        "categories": ["可优化", "期限异常"],
        "legal_basis_pool": [
            ["《民法典》相关条款"],
            ["《民法典》合同编通则解释"],
        ],
        "descriptions": [
            "该条款可结合具体业务场景进一步优化表述。",
            "该条款期限设置可参考行业惯例进一步优化。",
        ],
        "modifications": [
            "建议结合行业惯例与司法实践, 优化条款表述。",
            "建议参考同类合同常用期限范围调整。",
        ],
    },
}


def random_date_pair() -> tuple[str, str]:
    start_offset = random.randint(30, 365)
    duration_days = random.choice([30, 90, 180, 365, 540, 730, 1095, 1825])
    start = date(2026, 7, 1) + timedelta(days=start_offset)
    end = start + timedelta(days=duration_days)
    return start.isoformat(), end.isoformat()


def gen_params() -> dict[str, str]:
    """生成一批随机参数"""
    # 期限与期数协同: 1年=12期, 3年=36期, 5年=60期 等
    duration_to_installments = {
        "1 个月": 1, "3 个月": 3, "6 个月": 6, "1 年": 12,
        "18 个月": 18, "2 年": 24, "3 年": 36, "5 年": 60, "10 年": 120,
    }
    duration = random.choice(DURATIONS)
    installments = duration_to_installments.get(duration, 12)
    return {
        "amount": random.choice(CURRENCY_AMOUNTS),
        "amount_yuan": random.choice(CURRENCY_AMOUNTS).replace(" 元", "").replace(" 万", "0000"),
        "amount_cn": random.choice(["伍万元整", "壹拾万元整", "伍拾万元整", "壹佰万元整"]),
        "duration": duration,
        "start_date": random_date_pair()[0],
        "end_date": random_date_pair()[1],
        "interest_rate": random.choice(INTEREST_RATES),
        "LPR_basis": random.choice(LPR_MULTIPLIERS),
        "interest_basis": random.choice(["上浮 10%", "上浮 20%", "下浮 5%", "不浮动"]),
        "penalty_rate": random.choice(PENALTY_RATES),
        "jurisdiction": random.choice(JURISDICTIONS),
        "guarantee_type": random.choice(GUARANTEE_TYPES),
        "repayment_method": random.choice(PAYMENT_METHODS),
        "usage": random.choice(["经营周转", "购房", "购车", "装修", "教育", "医疗", "技术升级", "项目执行", "原材料采购"]),
        "repay_day": str(random.choice([5, 10, 15, 20, 25])),
        "installment_count": str(installments),
        "down_payment": random.choice(CURRENCY_AMOUNTS[:6]),
        "interest_owed": "1 万元",
        "waiver_amount": "5000 元",
        "deadline": (date(2027, 6, 30)).isoformat(),
        "settlement_date": (date(2026, 12, 31)).isoformat(),
        "irr_cap": "36%",
        "prepayment_penalty": random.choice(["未结清本金的 1%", "未结清本金的 3%", "未结清本金的 5%"]),
        "overdue_fee": random.choice(["500 元", "1000 元", "2000 元"]),
        "overdue_lpr": random.choice(LPR_MULTIPLIERS),
        "interest_pay": random.choice(["月", "季", "年"]),
        "notify_days": str(random.choice([3, 5, 7, 15, 30])),
        "register_days": str(random.choice([15, 30, 60])),
        "guarantee_period": random.choice(["3 个月", "6 个月", "1 年", "2 年"]),
        "debtor_name": random.choice(["XX 有限公司", "XX 医院", "XX 学校", "XX 集团"]),
        "recycling_type": random.choice(["有追索权", "无追索权"]),
        "financing_amount": random.choice(CURRENCY_AMOUNTS),
        "financing_ratio": random.choice(["60%", "70%", "80%", "90%"]),
        "factoring_rate": random.choice(INTEREST_RATES),
        "due_date": (date(2027, 6, 30)).isoformat(),
        "original_contract_id": f"LX-{random.randint(100000, 999999)}",
        "original_date": "2025-12-31",
        "old_balance": random.choice(CURRENCY_AMOUNTS),
        "old_balance_date": "2026-06-30",
        "new_end_date": (date(2028, 6, 30)).isoformat(),
        "original_end_date": (date(2026, 12, 31)).isoformat(),
        "transfer_price": random.choice(CURRENCY_AMOUNTS),
        "monthly_rate": random.choice(["0.5%", "1%", "1.5%", "2%", "3%"]),
        "fee_cap": "综合费率不超过 4.7%",
        "pawn_subject": random.choice(["黄金首饰", "名表", "珠宝", "古董字画", "汽车"]),
        "repayment_source": random.choice(["新项目回款", "银行新贷款", "应收账款回款"]),
        "purpose_detail": random.choice(["偿还到期债务", "股权收购付款", "项目过桥", "工程款支付"]),
        "handling_fee_rate": random.choice(["0.6%", "0.75%", "0.9%"]),
        "course_name": random.choice(["职业技能培训", "学历教育", "语言培训", "IT 培训"]),
        "treatment_type": random.choice(["口腔正畸", "近视手术", "美容整形", "辅助生殖"]),
        "vehicle_brand": random.choice(["特斯拉", "比亚迪", "蔚来", "理想", "奔驰", "宝马"]),
        "vehicle_type": random.choice(["Model Y", "汉 EV", "ES6", "L9", "C 级", "5 系"]),
        "property_location": random.choice(CITIES) + random.choice(DISTRICTS) + "某路 88 号",
        "trip_destination": random.choice(["日本", "泰国", "欧洲", "美国", "澳洲"]),
        "trip_duration": random.choice(["7 日", "10 日", "15 日"]),
        "ip_type": random.choice(["发明专利", "实用新型专利", "外观设计专利", "商标", "著作权"]),
        "ip_number": f"ZL{random.randint(10000000, 99999999)}.X",
        "main_contract_id": f"LX-{random.randint(100000, 999999)}",
        "commission_rate": str(random.choice([1, 2, 3, 5, 8, 10, 15, 20])),
        "share_pct": str(random.choice([25, 30, 40, 50, 60, 70, 75])),
        "adjust_pct": str(random.choice([5, 8, 10, 15, 20])),
        "industry_scenario": random.choice(INDUSTRY_SCENARIOS),
    }


def gen_clauses(skeleton_clauses: list, params: dict) -> list[dict]:
    """骨架条款模板 + 参数 → 完整条款列表"""
    clauses = []
    for i, (title, template) in enumerate(skeleton_clauses, 1):
        try:
            text = template.format(**params)
        except KeyError:
            # 缺少的占位符用 XX 替换 (脱敏)
            text = template
            for k in params:
                text = text.replace("{" + k + "}", "XX")
        clauses.append({"index": i, "title": title, "text": text})
    return clauses


def gen_annotations(clauses: list, fatal_keywords: list[str], major_keywords: list[str]) -> list[dict]:
    """基于骨架预定义的风险模式 + 通用 major/advisory, 生成 5+ 风险标注"""
    annotations = []
    used = set()
    n = len(clauses)

    def _add(level, clause_idx, fallback_idx=0):
        if clause_idx is None or clause_idx in used:
            return False
        tmpl = RISK_TEMPLATES[level]
        idx_to_use = clause_idx if clause_idx else (fallback_idx if fallback_idx else 1)
        if idx_to_use in used:
            return False
        clause_title = next((c["title"] for c in clauses if c["index"] == idx_to_use), "")
        annotations.append({
            "clause_index": idx_to_use,
            "clause_title": clause_title,
            "risk_level": level,
            "risk_categories": random.sample(tmpl["categories"], k=min(2, len(tmpl["categories"]))),
            "legal_basis": random.choice(tmpl["legal_basis_pool"]),
            "risk_description": random.choice(tmpl["descriptions"]),
            "modification_suggestion": random.choice(tmpl["modifications"]),
            "stance_impact": "需结合上下文判断" if level == "fatal" else ("不利" if level == "major" else "中性"),
        })
        used.add(idx_to_use)
        return True

    # 致命风险
    for kw in fatal_keywords[:2]:
        idx = next((c["index"] for c in clauses if kw in c["title"]), None)
        _add("fatal", idx)
    # 重大风险
    for kw in major_keywords[:2]:
        idx = next((c["index"] for c in clauses if kw in c["title"]), None)
        _add("major", idx)
    # 通用重大: 争议/违约
    for kw in ["争议", "违约", "管辖", "解除"]:
        idx = next((c["index"] for c in clauses if kw in c["title"]), None)
        _add("major", idx)
    # 通用建议
    while len(annotations) < 5:
        idx = random.randint(1, n)
        if idx not in used:
            if _add("advisory", idx):
                continue
    return annotations


def build_template(category: str, skeleton: dict, variant_idx: int, params: dict) -> dict:
    """组装一份合同模板"""
    clauses = gen_clauses(skeleton["clauses"], params)
    annotations = gen_annotations(clauses, skeleton.get("fatal_keywords", []), skeleton.get("major_keywords", []))

    template_id = f"{category}-{skeleton['name']}-{variant_idx:03d}"

    return {
        "template_id": template_id,
        "contract_type": skeleton["contract_type"],
        "industry": skeleton["industry"],
        "title": skeleton["title"],
        "clauses": clauses,
        "annotations_count": len(annotations),
        "annotations": annotations,
        "applicable_scenarios": [
            skeleton["title"],
            f"{skeleton['industry']}常见场景",
            "律师实务高频合同",
        ],
        "lawyer_notes": (
            f"本模板适用于{skeleton['title']}场景, 基于律师实务高频结构整理, 风险标注已参考《民法典》及司法解释。"
            f"使用前请根据实际案情调整金额、期限、管辖地等关键参数, 并审查风险标注项, 必要时咨询专业律师。"
        ),
        "metadata": {
            "category": category,
            "skeleton": skeleton["name"],
            "variant_idx": variant_idx,
            "source": "LexPrime W4 程序化生成",
            "generated_at": "2026-06-29",
        },
        "created_at": "2026-06-29",
        "updated_at": "2026-06-29",
    }


def generate_category(category: str, variants_per_skeleton: int = 20) -> int:
    """为某类生成所有变体"""
    skel_path = SKELETONS_DIR / f"{category}.json"
    if not skel_path.exists():
        log.warning(f"骨架文件不存在: {skel_path}")
        return 0
    skeletons = json.loads(skel_path.read_text(encoding="utf-8"))
    out_dir = OUTPUT_DIR / category
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for skel in skeletons:
        for v in range(1, variants_per_skeleton + 1):
            # 基于 (category, skeleton, variant) 独立随机
            random.seed(hash((category, skel["name"], v)) & 0x7fffffff)
            params = gen_params()
            template = build_template(category, skel, v, params)
            out_path = out_dir / f"{template['template_id']}.json"
            out_path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
            count += 1
    log.info(f"[{category}] {count} 模板生成完成 ({len(skeletons)} 骨架 × {variants_per_skeleton} 变体)")
    return count


if __name__ == "__main__":
    # 默认生成所有类别
    categories = sys.argv[1:] if len(sys.argv) > 1 else [
        "loan", "house", "labor", "service", "sales", "partnership",
        "agency", "equity", "ip", "family", "insurance", "construction"
    ]
    total = 0
    for cat in categories:
        n = generate_category(cat, variants_per_skeleton=20)
        total += n
    log.info(f"总计: {total} 模板")
