"""
W4 合同模板补足脚本 (W4 attempt 2)
LexPrime 数据工程 (W4)

为 8 个不达标类追加 1-4 个新骨架, 让每类 >= 500 模板:
- family: +4 (从 21 → 25 骨架 × 20 = 500)
- ip: +3 (从 22 → 25)
- insurance: +3 (从 22 → 25)
- labor: +2 (从 23 → 25)
- construction: +2 (从 23 → 25)
- house: +1 (从 24 → 25)
- equity: +1 (从 24 → 25)
- partnership: 实际已 25, 不补

新增 16 骨架 × 20 变体 = 320 新模板
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

CASES_CRAWLER = Path(__file__).parent.parent.parent
SKELETONS_DIR = CASES_CRAWLER / "data" / "contracts" / "w4_skeletons"

# ============================================================
# 补足骨架 (按类别)
# ============================================================

EXTRA_SKELETONS = {
    "family": [
        {
            "name": "family_paternity",
            "title": "亲子关系确认协议",
            "contract_type": "婚姻家事合同",
            "industry": "亲子关系",
            "fatal_keywords": ["亲子", "确认"],
            "major_keywords": ["争议"],
            "clauses": [
                ["协议双方", "甲方 (父亲/母亲) 与乙方就子女{usage}的亲子关系确认事宜, 签订本协议。"],
                ["亲子确认", "双方确认, 甲方与丙方 (子女) 存在亲子关系 (父子/母子)。"],
                ["权利义务", "甲方作为丙方的法定监护人, 承担抚养、教育、保护义务。"],
                ["财产", "甲方按月支付丙方抚养费人民币 {amount}。"],
                ["探望", "乙方 (另一方) 每月可探望丙方 {commission_rate} 次。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
        {
            "name": "family_ivf",
            "title": "试管婴儿辅助生殖协议",
            "contract_type": "婚姻家事合同",
            "industry": "辅助生殖",
            "fatal_keywords": ["生殖", "伦理"],
            "major_keywords": ["争议"],
            "clauses": [
                ["协议双方", "甲方 (夫妻) 与乙方 (医疗机构) 就辅助生殖 (试管婴儿) 事宜签订本协议。"],
                ["医疗内容", "乙方为甲方提供{usage}辅助生殖技术服务。"],
                ["费用", "医疗费用人民币 {amount}, 甲方按{repayment_method}支付。"],
                ["伦理", "双方应遵守国家辅助生殖伦理规定, 不得进行代孕等违法活动。"],
                ["成功率", "乙方应向甲方充分告知辅助生殖的成功率及风险, 不得作保证性承诺。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
        {
            "name": "family_surrogate",
            "title": "意定监护协议",
            "contract_type": "婚姻家事合同",
            "industry": "意定监护",
            "fatal_keywords": ["监护", "意定"],
            "major_keywords": ["争议"],
            "clauses": [
                ["被监护人", "甲方为完全/限制民事行为能力人, 拟确定意定监护人。"],
                ["意定监护人", "乙方为甲方指定的意定监护人。"],
                ["监护范围", "乙方代为管理甲方的{usage} (生活照料/医疗决定/财产管理)。"],
                ["监护期限", "监护期限 {duration}, 自 {start_date} 起至 {end_date} 止。"],
                ["公证", "本协议经公证机关公证, 自双方签字之日起生效。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
        {
            "name": "family_sperm_donation",
            "title": "人工授精供精协议",
            "contract_type": "婚姻家事合同",
            "industry": "人工授精",
            "fatal_keywords": ["隐私", "伦理"],
            "major_keywords": ["争议"],
            "clauses": [
                ["供方", "甲方为精子提供方。"],
                ["受方", "乙方为接受精子方, 因{usage}需要人工授精。"],
                ["隐私保护", "双方应对身份信息严格保密, 不得向任何第三方披露。"],
                ["权利义务", "乙方所生子女与甲方无亲子关系, 甲方不承担抚养义务。"],
                ["伦理", "双方应遵守国家辅助生殖伦理规定。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
    ],
    "ip": [
        {
            "name": "ip_trademark_infringement_warning",
            "title": "商标侵权警告函",
            "contract_type": "知识产权合同",
            "industry": "商标警告",
            "fatal_keywords": ["警告", "侵权"],
            "major_keywords": ["争议"],
            "clauses": [
                ["警告方", "甲方为商标 (注册号 {ip_number}) 的注册人。"],
                ["被警告方", "乙方涉嫌侵犯甲方商标权。"],
                ["侵权行为", "乙方未经甲方许可, 在{usage}商品/服务上使用与甲方商标相同/近似的商标。"],
                ["要求", "甲方要求乙方立即停止侵权行为, 销毁侵权商品, 赔偿损失。"],
                ["期限", "乙方应在收到本函后 7 日内停止侵权并与甲方协商赔偿事宜。"],
                ["后果", "如乙方未在期限内停止侵权, 甲方将依法提起诉讼。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
        {
            "name": "ip_patent_infringement_warning",
            "title": "专利侵权警告函",
            "contract_type": "知识产权合同",
            "industry": "专利警告",
            "fatal_keywords": ["警告", "侵权"],
            "major_keywords": ["争议"],
            "clauses": [
                ["警告方", "甲方为{ip_type} (专利号 {ip_number}) 的专利权人。"],
                ["被警告方", "乙方涉嫌侵犯甲方专利权。"],
                ["侵权行为", "乙方未经甲方许可, 实施甲方专利, 包括制造/销售/许诺销售/进口专利产品。"],
                ["要求", "甲方要求乙方立即停止侵权, 销毁侵权产品, 赔偿损失。"],
                ["期限", "乙方应在收到本函后 15 日内停止侵权并与甲方协商赔偿事宜。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
        {
            "name": "ip_copyright_infringement_warning",
            "title": "著作权侵权警告函",
            "contract_type": "知识产权合同",
            "industry": "著作权警告",
            "fatal_keywords": ["警告", "侵权"],
            "major_keywords": ["争议"],
            "clauses": [
                ["警告方", "甲方为作品《{usage}》的著作权人。"],
                ["被警告方", "乙方涉嫌侵犯甲方著作权。"],
                ["侵权行为", "乙方未经甲方许可, 复制/发行/信息网络传播/改编/翻译甲方作品。"],
                ["要求", "甲方要求乙方立即停止侵权, 销毁侵权复制品, 赔偿损失。"],
                ["期限", "乙方应在收到本函后 7 日内停止侵权并与甲方协商赔偿事宜。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
    ],
    "insurance": [
        {
            "name": "insurance_renewal",
            "title": "保险续保协议",
            "contract_type": "保险合同",
            "industry": "保险续保",
            "fatal_keywords": ["续保", "告知"],
            "major_keywords": ["争议"],
            "clauses": [
                ["原保单", "原保单编号 {original_contract_id}, 保险期间至 {original_end_date}。"],
                ["续保", "乙方同意按本合同约定为甲方续保。"],
                ["保险责任", "续保期间保险责任范围与原保单相同 (如{usage})。"],
                ["保险金额", "续保期间保险金额人民币 {amount}。"],
                ["保险费", "续保保险费人民币 {transfer_price}。"],
                ["续保期间", "续保期间 {duration}, 自 {start_date} 起至 {end_date} 止。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
        {
            "name": "insurance_coinsurance",
            "title": "共同保险协议",
            "contract_type": "保险合同",
            "industry": "共同保险",
            "fatal_keywords": ["共保", "份额"],
            "major_keywords": ["争议"],
            "clauses": [
                ["共保人", "甲方 (首席保险人) 与乙方、丙方 (从共保人) 共同承保{usage}保险标的。"],
                ["共保份额", "甲方共保份额 {commission_rate}%, 乙方 {share_pct}%, 丙方剩余份额。"],
                ["保险金额", "保险金额人民币 {amount}。"],
                ["保险费", "保险费按共保份额分摊。"],
                ["理赔", "理赔由首席保险人 (甲方) 统一处理, 其他共保人按份额承担保险金。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
        {
            "name": "insurance_reinsurance_treaty",
            "title": "再保险合约",
            "contract_type": "保险合同",
            "industry": "再保险合约",
            "fatal_keywords": ["合约", "分保"],
            "major_keywords": ["争议"],
            "clauses": [
                ["分出方", "甲方为分出公司。"],
                ["分入方", "乙方为分入公司。"],
                ["合约方式", "本合同为{repayment_method} (临时/合约) 再保险。"],
                ["分出业务", "分出业务范围: {usage}。"],
                ["分保条件", "分保比例 {commission_rate}%, 分保手续费 {handling_fee_rate}%。"],
                ["账务", "按季度结算分保费及摊回赔款。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
    ],
    "labor": [
        {
            "name": "labor_pay_adjustment",
            "title": "调岗调薪协议",
            "contract_type": "劳动合同",
            "industry": "调岗调薪",
            "fatal_keywords": ["调岗", "协商"],
            "major_keywords": ["争议"],
            "clauses": [
                ["员工信息", "乙方 (员工) 系甲方员工, 担任原{usage}岗位。"],
                ["调整内容", "经双方协商一致, 自 {start_date} 起, 乙方调整至新岗位, 月工资调整为人民币 {amount}。"],
                ["调整依据", "本次调整基于{usage} (公司业务调整/员工绩效考核等)。"],
                ["其他待遇", "乙方其他福利待遇按甲方现行制度执行。"],
                ["协商一致", "本协议经双方协商一致, 乙方不得主张违法调岗。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
        {
            "name": "labor_work_injury",
            "title": "工伤赔偿协议",
            "contract_type": "劳动合同",
            "industry": "工伤",
            "fatal_keywords": ["工伤", "伤残"],
            "major_keywords": ["争议"],
            "clauses": [
                ["员工信息", "乙方系甲方员工, 在{usage}工作过程中发生工伤事故。"],
                ["伤残等级", "经劳动能力鉴定, 乙方伤残等级为{commission_rate}级。"],
                ["工伤待遇", "甲方按《工伤保险条例》支付乙方一次性伤残补助金等工伤待遇, 合计人民币 {amount}。"],
                ["医疗费", "工伤医疗费用由工伤保险基金按规定支付, 不足部分由甲方承担。"],
                ["劳动关系", "乙方工伤痊愈后, 双方继续履行劳动合同。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
    ],
    "construction": [
        {
            "name": "construction_pile_foundation",
            "title": "桩基工程施工合同",
            "contract_type": "工程承揽合同",
            "industry": "桩基工程",
            "fatal_keywords": ["质量", "隐蔽"],
            "major_keywords": ["争议"],
            "clauses": [
                ["工程内容", "工程内容: {usage} (钻孔灌注桩 / 预制管桩 / 人工挖孔桩)。"],
                ["工程地点", "工程地点: {property_location}。"],
                ["承包人", "承包人为乙方。"],
                ["工程价款", "工程价款人民币 {amount}, 按桩径和桩长结算。"],
                ["工期", "工期 {duration}, 自 {start_date} 起至 {end_date} 止。"],
                ["隐蔽验收", "桩基属隐蔽工程, 应在覆盖前进行验收。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
        {
            "name": "construction_curtain_wall",
            "title": "幕墙工程施工合同",
            "contract_type": "工程承揽合同",
            "industry": "幕墙工程",
            "fatal_keywords": ["安全", "保修"],
            "major_keywords": ["争议"],
            "clauses": [
                ["工程内容", "工程内容: {usage} (玻璃幕墙 / 金属幕墙 / 石材幕墙)。"],
                ["工程地点", "工程地点: {property_location}。"],
                ["承包人", "承包人为乙方。"],
                ["工程价款", "工程价款人民币 {amount}。"],
                ["工期", "工期 {duration}, 自 {start_date} 起至 {end_date} 止。"],
                ["安全", "幕墙施工属高空作业, 乙方应严格遵守安全规范。"],
                ["保修", "工程保修期 {duration}。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
    ],
    "house": [
        {
            "name": "house_business_licensing",
            "title": "营业执照代办服务合同",
            "contract_type": "房屋合同",
            "industry": "营业执照",
            "fatal_keywords": ["代办", "合法"],
            "major_keywords": ["争议"],
            "clauses": [
                ["委托事项", "甲方委托乙方代办位于{property_location}经营场所的营业执照。"],
                ["服务内容", "乙方提供工商登记材料准备、提交、跟进等服务。"],
                ["服务费用", "服务费人民币 {amount}。"],
                ["官费", "工商登记官费由甲方承担。"],
                ["合法", "乙方应确保代办过程合法合规, 不得办理虚假注册。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
    ],
    "equity": [
        {
            "name": "equity_pledge_release",
            "title": "股权质押解除协议",
            "contract_type": "股权合同",
            "industry": "股权质押解除",
            "fatal_keywords": ["解除", "登记"],
            "major_keywords": ["争议"],
            "clauses": [
                ["原质押", "原质押合同编号 {original_contract_id}, 甲方将目标公司 {commission_rate}% 股权质押给乙方。"],
                ["主债权清偿", "主债务已清偿, 乙方同意解除股权质押。"],
                ["解除登记", "双方应于本合同签订后 15 日内办理股权出质注销登记。"],
                ["配合义务", "乙方应配合甲方办理出质注销登记手续。"],
                ["争议解决", "争议由{jurisdiction}管辖。"],
            ],
        },
    ],
}


def append_skeletons():
    """追加新骨架到现有 JSON"""
    for category, new_skeletons in EXTRA_SKELETONS.items():
        skel_path = SKELETONS_DIR / f"{category}.json"
        if not skel_path.exists():
            log.warning(f"骨架文件不存在: {skel_path}")
            continue
        existing = json.loads(skel_path.read_text(encoding="utf-8"))
        # 检查是否已追加 (避免重复)
        existing_names = {s["name"] for s in existing}
        to_add = [s for s in new_skeletons if s["name"] not in existing_names]
        if not to_add:
            log.info(f"[{category}] 无新骨架追加 (已有)")
            continue
        merged = existing + to_add
        skel_path.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        log.info(f"[{category}] +{len(to_add)} 骨架 ({len(existing)} → {len(merged)})")


if __name__ == "__main__":
    append_skeletons()
    log.info("补足完成。下一步: 重跑 generate_contracts.py → dedupe → build_fts_index → validate")
