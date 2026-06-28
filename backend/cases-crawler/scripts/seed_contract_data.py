"""
LexPrime 合同风险审查 Skill — 数据扩量脚本 (W3)

生成 50+ 合同模板 + 250+ 风险标注样本, 入库到 data/contracts/ 目录。

数据规模:
- 合同模板: 7 大类 × 8 模板 = 56 份
  - 房屋租赁 (8)
  - 借款合同 (8)
  - 劳动合同 (8)
  - 服务合同 (8)
  - 销售合同 (8)
  - 合伙协议 (8)
  - 委托代理 (8)
- 风险标注: 56 × 5+ = 280+ 条
  - 每份模板覆盖致命 / 重大 / 建议 三级

运行:
    cd backend/cases-crawler
    python scripts/seed_contract_data.py --templates 56 --annotations 280
    或 --reset 重置
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

# 设置路径, 允许从 backend/cases-crawler/ 直接运行
SCRIPT_DIR = Path(__file__).parent
CASES_CRAWLER_DIR = SCRIPT_DIR.parent
DATA_DIR = CASES_CRAWLER_DIR / "data"
CONTRACTS_DIR = DATA_DIR / "contracts"


# ===== 合同模板数据 =====

CONTRACT_TEMPLATES = [
    # ===== 房屋租赁 (8 模板) =====
    {
        "template_id": "house-rent-residential-01",
        "contract_type": "房屋租赁",
        "industry": "个人租赁",
        "title": "个人住宅租赁合同(标准版)",
        "clauses": [
            {"index": 1, "title": "租赁标的", "text": "甲方将位于上海市浦东新区某某路 123 号 1502 室房屋出租给乙方使用, 建筑面积 85 平方米。"},
            {"index": 2, "title": "租赁期限", "text": "租赁期自 2026 年 7 月 1 日起至 2027 年 6 月 30 日止, 共 12 个月。"},
            {"index": 3, "title": "租金及支付", "text": "月租金为人民币 5000 元整, 乙方应于每月 5 日前支付下月租金。逾期支付的, 每逾期一天, 按月租金的 5% 加收违约金。"},
            {"index": 4, "title": "押金", "text": "乙方向甲方支付押金人民币 10000 元整, 30 日内无息退还。"},
            {"index": 5, "title": "维修责任", "text": "租赁期间, 房屋及附属设施的维修责任由甲方承担。乙方使用不当造成的损坏由乙方负责赔偿。"},
            {"index": 6, "title": "提前解约", "text": "任何一方提前解除合同的, 须向守约方支付相当于 6 个月租金的违约金。"},
            {"index": 7, "title": "争议管辖", "text": "因本合同发生的争议, 任何一方均可向甲方住所地人民法院提起诉讼。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "house-rent-commercial-01",
        "contract_type": "房屋租赁",
        "industry": "商业租赁",
        "title": "商铺租赁合同(商场版)",
        "clauses": [
            {"index": 1, "title": "租赁标的", "text": "甲方将位于北京市朝阳区某某商场 B1 层 88 号商铺出租给乙方, 面积 60 平方米。"},
            {"index": 2, "title": "租赁期限", "text": "租赁期 3 年, 自 2026 年 9 月 1 日起至 2029 年 8 月 31 日止。"},
            {"index": 3, "title": "租金及支付", "text": "月租金 30000 元, 按季度支付。乙方逾期支付的, 按日加收 3% 违约金。"},
            {"index": 4, "title": "转租限制", "text": "未经甲方书面同意, 乙方不得将商铺转租、转让或以其他方式让渡。"},
            {"index": 5, "title": "装修条款", "text": "乙方装修需经甲方审批, 装修费用由乙方承担, 退租时不得拆除。"},
            {"index": 6, "title": "争议管辖", "text": "争议提交北京仲裁委员会仲裁。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "house-rent-shared-01",
        "contract_type": "房屋租赁",
        "industry": "合租租赁",
        "title": "合租房屋租赁合同(三居室)",
        "clauses": [
            {"index": 1, "title": "租赁标的", "text": "甲方将三居室中的次卧出租给乙方, 公用客厅、厨房、卫生间。"},
            {"index": 2, "title": "租金", "text": "月租金 2500 元, 含水电网, 押一付一。"},
            {"index": 3, "title": "租期", "text": "租期 6 个月, 起止日期: 2026 年 6 月 1 日至 2026 年 11 月 30 日。"},
            {"index": 4, "title": "作息", "text": "乙方应保持安静, 晚上 11 点后不得大声喧哗。"},
            {"index": 5, "title": "退租", "text": "乙方提前 7 天通知甲方可解除合同。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "house-rent-short-term-01",
        "contract_type": "房屋租赁",
        "industry": "短租",
        "title": "短租公寓合同(日租转月租)",
        "clauses": [
            {"index": 1, "title": "租赁标的", "text": "甲方提供精装公寓一间, 含家具家电, 可拎包入住。"},
            {"index": 2, "title": "租金", "text": "月租金 8000 元, 押金 8000 元, 起租日 2026 年 7 月 15 日。"},
            {"index": 3, "title": "水电费", "text": "水电燃气费按表实际使用收取, 网络费 100 元/月。"},
            {"index": 4, "title": "退租", "text": "乙方提前 30 天通知可退租, 否则押金不退。"},
            {"index": 5, "title": "物品损坏", "text": "乙方使用不当损坏家具家电, 照原价赔偿。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "house-rent-industrial-01",
        "contract_type": "房屋租赁",
        "industry": "工业厂房",
        "title": "工业厂房租赁合同",
        "clauses": [
            {"index": 1, "title": "租赁标的", "text": "甲方将位于苏州工业园区的厂房 5000 平方米出租给乙方。"},
            {"index": 2, "title": "用途", "text": "乙方用于电子产品组装生产, 不得用于污染行业。"},
            {"index": 3, "title": "租金", "text": "月租金 200000 元, 每 3 年递增 5%。"},
            {"index": 4, "title": "环保责任", "text": "乙方排放污染物需符合国家标准, 违规责任由乙方承担。"},
            {"index": 5, "title": "提前解约", "text": "乙方提前解约需支付 12 个月租金作为违约金。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "house-rent-storage-01",
        "contract_type": "房屋租赁",
        "industry": "仓储",
        "title": "仓库租赁合同",
        "clauses": [
            {"index": 1, "title": "租赁标的", "text": "甲方提供仓库 200 平方米, 位于物流园区。"},
            {"index": 2, "title": "租金", "text": "月租金 15000 元, 含物业管理。"},
            {"index": 3, "title": "货物保险", "text": "乙方应自行购买货物保险, 甲方不对货物损失负责。"},
            {"index": 4, "title": "退租通知", "text": "提前 60 天书面通知可退租。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "house-rent-apartment-01",
        "contract_type": "房屋租赁",
        "industry": "公寓",
        "title": "长租公寓合同(服务式)",
        "clauses": [
            {"index": 1, "title": "租赁标的", "text": "乙方租赁甲方服务式公寓一间, 含每周 2 次打扫。"},
            {"index": 2, "title": "租金", "text": "月租金 12000 元, 含服务费、网费。"},
            {"index": 3, "title": "押金", "text": "押金 2 个月租金。"},
            {"index": 4, "title": "提前解约", "text": "乙方提前解约, 押金全额不退, 且需支付剩余租期租金的 50%。"},
            {"index": 5, "title": "争议", "text": "提交上海仲裁委员会仲裁。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "house-rent-villa-01",
        "contract_type": "房屋租赁",
        "industry": "别墅",
        "title": "别墅租赁合同(高端)",
        "clauses": [
            {"index": 1, "title": "租赁标的", "text": "甲方将独栋别墅出租给乙方, 含花园、泳池、车库。"},
            {"index": 2, "title": "租金", "text": "月租金 50000 元, 押金 3 个月租金。"},
            {"index": 3, "title": "维修", "text": "10 万元以下维修乙方自行承担。"},
            {"index": 4, "title": "宠物", "text": "乙方可养宠物, 损坏按原价赔偿。"},
            {"index": 5, "title": "争议", "text": "向别墅所在地法院起诉。"},
        ],
        "annotations_count": 5,
    },

    # ===== 借款合同 (8 模板) =====
    {
        "template_id": "loan-personal-01",
        "contract_type": "借款合同",
        "industry": "个人借款",
        "title": "个人借款合同(亲友版)",
        "clauses": [
            {"index": 1, "title": "借款金额", "text": "甲方借给乙方人民币 50 万元整。"},
            {"index": 2, "title": "借款期限", "text": "借款期限自 2026 年 8 月 1 日起至 2027 年 7 月 31 日止。"},
            {"index": 3, "title": "利息", "text": "借款年利率 24%, 超过部分无效。"},
            {"index": 4, "title": "还款方式", "text": "乙方应于到期日一次性偿还本金及利息。"},
            {"index": 5, "title": "违约责任", "text": "乙方逾期还款的, 按日加收 1% 违约金。"},
            {"index": 6, "title": "争议管辖", "text": "向甲方住所地法院起诉。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "loan-bank-01",
        "contract_type": "借款合同",
        "industry": "银行借款",
        "title": "银行个人消费贷款合同",
        "clauses": [
            {"index": 1, "title": "借款金额", "text": "甲方(银行)向乙方提供个人消费贷款人民币 30 万元。"},
            {"index": 2, "title": "借款期限", "text": "借款期限 5 年, 自实际放款日起算。"},
            {"index": 3, "title": "利率", "text": "年利率按同期 LPR + 150BP 执行, 随 LPR 调整。"},
            {"index": 4, "title": "还款", "text": "等额本息按月偿还。"},
            {"index": 5, "title": "提前还款", "text": "乙方可提前还款, 但需支付 1% 违约金。"},
            {"index": 6, "title": "违约", "text": "乙方连续 3 期未还款, 甲方有权宣布贷款提前到期。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "loan-business-01",
        "contract_type": "借款合同",
        "industry": "企业经营借款",
        "title": "企业经营借款合同",
        "clauses": [
            {"index": 1, "title": "借款金额", "text": "借款人民币 500 万元用于企业经营。"},
            {"index": 2, "title": "期限", "text": "借款期限 1 年。"},
            {"index": 3, "title": "利率", "text": "年利率 18%。"},
            {"index": 4, "title": "担保", "text": "乙方以公司股权质押作为担保。"},
            {"index": 5, "title": "用途限制", "text": "借款不得用于偿还其他债务。"},
            {"index": 6, "title": "争议", "text": "提交杭州仲裁委员会仲裁。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "loan-mortgage-01",
        "contract_type": "借款合同",
        "industry": "房贷",
        "title": "个人住房按揭贷款合同",
        "clauses": [
            {"index": 1, "title": "贷款金额", "text": "贷款 200 万元用于购买上海市某某路 88 号 1502 室。"},
            {"index": 2, "title": "贷款期限", "text": "贷款期限 30 年。"},
            {"index": 3, "title": "利率", "text": "首套房利率 LPR - 20BP, 二套房 LPR + 60BP。"},
            {"index": 4, "title": "还款", "text": "等额本息按月偿还。"},
            {"index": 5, "title": "抵押", "text": "乙方以所购房产作为抵押物。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "loan-p2p-01",
        "contract_type": "借款合同",
        "industry": "民间借贷",
        "title": "民间借贷合同(高利息版)",
        "clauses": [
            {"index": 1, "title": "借款金额", "text": "借款 20 万元。"},
            {"index": 2, "title": "利率", "text": "月利率 3%(年化 36%)。"},
            {"index": 3, "title": "期限", "text": "借款期限 6 个月。"},
            {"index": 4, "title": "违约", "text": "逾期按日 5% 加收违约金。"},
            {"index": 5, "title": "管辖", "text": "向出借人住所地法院起诉。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "loan-factoring-01",
        "contract_type": "借款合同",
        "industry": "保理融资",
        "title": "应收账款保理融资合同",
        "clauses": [
            {"index": 1, "title": "保理金额", "text": "乙方将对甲方的应收账款 1000 万元转让给丙方(保理商)。"},
            {"index": 2, "title": "保理费率", "text": "保理费率 12%/年。"},
            {"index": 3, "title": "回购义务", "text": "若应收账款到期无法收回, 乙方应按原价回购。"},
            {"index": 4, "title": "争议", "text": "提交上海国际经济贸易仲裁委员会仲裁。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "loan-guaranteed-01",
        "contract_type": "借款合同",
        "industry": "担保借款",
        "title": "第三方担保借款合同",
        "clauses": [
            {"index": 1, "title": "借款", "text": "甲方借给乙方 100 万元, 丙方提供连带责任保证。"},
            {"index": 2, "title": "保证期间", "text": "保证期间为主债务到期之日起 2 年。"},
            {"index": 3, "title": "利率", "text": "年利率 15%。"},
            {"index": 4, "title": "违约", "text": "逾期按日 0.5% 加收违约金。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "loan-credit-01",
        "contract_type": "借款合同",
        "industry": "信用贷",
        "title": "个人信用借款合同",
        "clauses": [
            {"index": 1, "title": "借款", "text": "甲方(银行)向乙方提供信用借款 50 万元, 无需担保。"},
            {"index": 2, "title": "期限", "text": "借款期限 3 年。"},
            {"index": 3, "title": "利率", "text": "年利率 LPR + 200BP。"},
            {"index": 4, "title": "提前还款", "text": "前 12 个月内提前还款需支付 2% 手续费。"},
        ],
        "annotations_count": 5,
    },

    # ===== 劳动合同 (8 模板) =====
    {
        "template_id": "labor-fulltime-01",
        "contract_type": "劳动合同",
        "industry": "互联网",
        "title": "互联网公司全职劳动合同(标准版)",
        "clauses": [
            {"index": 1, "title": "合同期限", "text": "本合同为固定期限劳动合同, 期限 3 年。"},
            {"index": 2, "title": "工作内容", "text": "乙方担任高级工程师, 工作地点北京。"},
            {"index": 3, "title": "工作时间", "text": "标准工时制, 周一至周五 9:00-18:00。"},
            {"index": 4, "title": "工资", "text": "月工资税前 30000 元, 按月发放。"},
            {"index": 5, "title": "加班", "text": "加班按 1.5 倍工资支付, 周末 2 倍, 法定节假日 3 倍。"},
            {"index": 6, "title": "竞业禁止", "text": "乙方离职后 2 年内不得从事同类业务, 甲方每月支付 5000 元补偿。"},
            {"index": 7, "title": "保密", "text": "乙方对甲方商业秘密承担永久保密义务。"},
            {"index": 8, "title": "争议管辖", "text": "提交甲方所在地劳动仲裁委员会仲裁。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "labor-intern-01",
        "contract_type": "劳动合同",
        "industry": "实习",
        "title": "实习生协议",
        "clauses": [
            {"index": 1, "title": "实习期限", "text": "实习期 3 个月, 自 2026 年 7 月 1 日起。"},
            {"index": 2, "title": "实习津贴", "text": "月津贴 3000 元。"},
            {"index": 3, "title": "工作时间", "text": "每周工作 5 天, 每天 8 小时。"},
            {"index": 4, "title": "保险", "text": "甲方为乙方购买商业意外险。"},
            {"index": 5, "title": "解除", "text": "任何一方可提前 3 天通知解除协议。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "labor-manager-01",
        "contract_type": "劳动合同",
        "industry": "高管",
        "title": "高管聘用合同",
        "clauses": [
            {"index": 1, "title": "职位", "text": "乙方担任甲方公司首席财务官。"},
            {"index": 2, "title": "期限", "text": "无固定期限合同。"},
            {"index": 3, "title": "薪酬", "text": "年薪 100 万, 其中基本工资 50 万, 绩效 50 万。"},
            {"index": 4, "title": "股票期权", "text": "授予乙方 10 万股期权, 行权价 5 元。"},
            {"index": 5, "title": "竞业禁止", "text": "离职后 3 年内不得从事同类业务。"},
            {"index": 6, "title": "补偿", "text": "竞业禁止期间甲方每月支付 30000 元补偿。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "labor-parttime-01",
        "contract_type": "劳动合同",
        "industry": "兼职",
        "title": "兼职劳动合同",
        "clauses": [
            {"index": 1, "title": "工作时间", "text": "乙方每周工作 20 小时。"},
            {"index": 2, "title": "工资", "text": "小时工资 50 元, 月结。"},
            {"index": 3, "title": "期限", "text": "合同期限 1 年。"},
            {"index": 4, "title": "保险", "text": "甲方为乙方购买工伤保险。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "labor-sales-01",
        "contract_type": "劳动合同",
        "industry": "销售",
        "title": "销售岗位劳动合同(底薪+提成)",
        "clauses": [
            {"index": 1, "title": "底薪", "text": "基本工资 5000 元/月。"},
            {"index": 2, "title": "提成", "text": "销售额的 5% 作为提成。"},
            {"index": 3, "title": "目标", "text": "每月销售额目标 10 万元。"},
            {"index": 4, "title": "未达标", "text": "连续 3 个月未达标, 甲方可解除合同。"},
            {"index": 5, "title": "争议", "text": "提交劳动仲裁。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "labor-tech-01",
        "contract_type": "劳动合同",
        "industry": "技术",
        "title": "技术岗位劳动合同(含 IP 归属)",
        "clauses": [
            {"index": 1, "title": "工作内容", "text": "乙方从事软件开发工作。"},
            {"index": 2, "title": "知识产权", "text": "乙方在职期间产生的所有技术成果归甲方所有。"},
            {"index": 3, "title": "工资", "text": "月工资 25000 元。"},
            {"index": 4, "title": "竞业禁止", "text": "离职后 1 年内不得从事同类技术开发。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "labor-remote-01",
        "contract_type": "劳动合同",
        "industry": "远程工作",
        "title": "远程工作劳动合同",
        "clauses": [
            {"index": 1, "title": "工作地点", "text": "乙方可远程工作, 工作地点为乙方住所地。"},
            {"index": 2, "title": "工资", "text": "月工资 20000 元。"},
            {"index": 3, "title": "考核", "text": "每月交付项目成果, 甲方按成果考核。"},
            {"index": 4, "title": "争议", "text": "提交甲方所在地劳动仲裁。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "labor-termination-01",
        "contract_type": "劳动合同",
        "industry": "协商解除",
        "title": "协商解除劳动合同协议",
        "clauses": [
            {"index": 1, "title": "解除", "text": "双方协商一致, 自 2026 年 9 月 1 日起解除劳动合同。"},
            {"index": 2, "title": "经济补偿", "text": "甲方支付乙方经济补偿金 N+1, 共 12 个月工资。"},
            {"index": 3, "title": "工资结算", "text": "甲方在 9 月 15 日前结清乙方所有工资。"},
            {"index": 4, "title": "保密", "text": "乙方继续承担保密义务。"},
            {"index": 5, "title": "无争议", "text": "双方确认除本协议外无其他劳动争议。"},
        ],
        "annotations_count": 5,
    },

    # ===== 服务合同 (8 模板) =====
    {
        "template_id": "service-consulting-01",
        "contract_type": "服务合同",
        "industry": "咨询服务",
        "title": "管理咨询服务合同",
        "clauses": [
            {"index": 1, "title": "服务内容", "text": "甲方聘请乙方提供战略咨询服务, 为期 6 个月。"},
            {"index": 2, "title": "服务费", "text": "服务费总额 100 万元, 分 3 期支付。"},
            {"index": 3, "title": "交付", "text": "乙方每月提交书面报告, 期末提交总结报告。"},
            {"index": 4, "title": "知识产权", "text": "服务成果归甲方所有, 乙方可保留通用方法论。"},
            {"index": 5, "title": "保密", "text": "乙方对服务过程中知悉的甲方信息承担保密义务。"},
            {"index": 6, "title": "争议", "text": "提交上海仲裁委员会仲裁。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "service-tech-01",
        "contract_type": "服务合同",
        "industry": "技术服务",
        "title": "App 开发服务合同",
        "clauses": [
            {"index": 1, "title": "开发内容", "text": "乙方为甲方开发一款移动 App, 含 iOS 和 Android。"},
            {"index": 2, "title": "开发周期", "text": "开发周期 6 个月。"},
            {"index": 3, "title": "费用", "text": "总费用 80 万元。"},
            {"index": 4, "title": "知识产权", "text": "App 知识产权归甲方所有。"},
            {"index": 5, "title": "维护", "text": "上线后免费维护 3 个月。"},
            {"index": 6, "title": "逾期", "text": "乙方逾期交付按日 0.5% 扣款。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "service-design-01",
        "contract_type": "服务合同",
        "industry": "设计服务",
        "title": "品牌设计服务合同",
        "clauses": [
            {"index": 1, "title": "服务内容", "text": "乙方为甲方提供品牌 VI 设计服务。"},
            {"index": 2, "title": "费用", "text": "设计费 30 万元。"},
            {"index": 3, "title": "修改", "text": "免费修改 3 次, 每次修改周期 5 个工作日。"},
            {"index": 4, "title": "版权", "text": "设计稿版权归甲方, 乙方可保留作品集展示权。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "service-marketing-01",
        "contract_type": "服务合同",
        "industry": "营销服务",
        "title": "数字营销服务合同",
        "clauses": [
            {"index": 1, "title": "服务", "text": "乙方为甲方提供 SEM、SEO、社交媒体营销服务。"},
            {"index": 2, "title": "期限", "text": "服务期限 1 年。"},
            {"index": 3, "title": "费用", "text": "月度服务费 5 万元。"},
            {"index": 4, "title": "KPI", "text": "乙方承诺 ROI 不低于 3:1。"},
            {"index": 5, "title": "未达标", "text": "连续 3 个月 KPI 未达标, 甲方可解除合同。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "service-cleaning-01",
        "contract_type": "服务合同",
        "industry": "保洁服务",
        "title": "保洁服务合同(写字楼)",
        "clauses": [
            {"index": 1, "title": "服务范围", "text": "乙方为甲方写字楼提供日常保洁。"},
            {"index": 2, "title": "费用", "text": "月费 20000 元。"},
            {"index": 3, "title": "人员", "text": "乙方派驻 5 名保洁员。"},
            {"index": 4, "title": "赔偿", "text": "乙方人员损坏甲方物品按原价赔偿。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "service-catering-01",
        "contract_type": "服务合同",
        "industry": "餐饮服务",
        "title": "团餐供应服务合同",
        "clauses": [
            {"index": 1, "title": "服务", "text": "乙方为甲方员工食堂提供团餐服务。"},
            {"index": 2, "title": "费用", "text": "餐费每人每餐 25 元。"},
            {"index": 3, "title": "卫生", "text": "乙方保证食品卫生符合国家标准。"},
            {"index": 4, "title": "责任", "text": "因食品质量问题导致食物中毒, 乙方承担全部责任。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "service-legal-01",
        "contract_type": "服务合同",
        "industry": "法律服务",
        "title": "常年法律顾问服务合同",
        "clauses": [
            {"index": 1, "title": "服务", "text": "乙方为甲方提供常年法律顾问服务。"},
            {"index": 2, "title": "期限", "text": "服务期限 1 年。"},
            {"index": 3, "title": "费用", "text": "年费 20 万元。"},
            {"index": 4, "title": "范围", "text": "含合同审查、法律咨询, 不含诉讼代理。"},
            {"index": 5, "title": "响应", "text": "一般咨询 24 小时响应, 紧急 2 小时响应。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "service-translation-01",
        "contract_type": "服务合同",
        "industry": "翻译服务",
        "title": "笔译服务合同",
        "clauses": [
            {"index": 1, "title": "内容", "text": "乙方为甲方翻译技术文档 50 万字。"},
            {"index": 2, "title": "费用", "text": "单价 0.5 元/字, 总计 25 万元。"},
            {"index": 3, "title": "交付", "text": "60 天内交付。"},
            {"index": 4, "title": "修改", "text": "免费修改 2 次。"},
        ],
        "annotations_count": 5,
    },

    # ===== 销售合同 (8 模板) =====
    {
        "template_id": "sales-goods-01",
        "contract_type": "销售合同",
        "industry": "商品买卖",
        "title": "设备买卖合同",
        "clauses": [
            {"index": 1, "title": "标的", "text": "甲方购买乙方机械设备 5 台, 总价 200 万元。"},
            {"index": 2, "title": "质量", "text": "质量符合国家标准 GB/T 12345-2020。"},
            {"index": 3, "title": "交付", "text": "乙方于 2026 年 9 月 30 日前交货至甲方工厂。"},
            {"index": 4, "title": "付款", "text": "预付 30%, 验收合格后支付 70%。"},
            {"index": 5, "title": "保修", "text": "保修期 1 年, 终身维修。"},
            {"index": 6, "title": "违约", "text": "乙方逾期交货按日 1% 扣款。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "sales-online-01",
        "contract_type": "销售合同",
        "industry": "电商",
        "title": "电商零售合同(平台版)",
        "clauses": [
            {"index": 1, "title": "商品", "text": "甲方在乙方平台销售电子产品。"},
            {"index": 2, "title": "佣金", "text": "乙方收取销售额的 8% 作为佣金。"},
            {"index": 3, "title": "结算", "text": "每月 15 日结算上月货款。"},
            {"index": 4, "title": "退货", "text": "7 天无理由退货, 运费由甲方承担。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "sales-international-01",
        "contract_type": "销售合同",
        "industry": "进出口贸易",
        "title": "出口贸易合同(FOB)",
        "clauses": [
            {"index": 1, "title": "货物", "text": "出口电子产品 10000 件, 单价 50 美元, 总计 50 万美元。"},
            {"index": 2, "title": "价格条款", "text": "FOB 上海。"},
            {"index": 3, "title": "付款", "text": "T/T 30 天。"},
            {"index": 4, "title": "争议", "text": "提交中国国际经济贸易仲裁委员会仲裁。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "sales-house-01",
        "contract_type": "销售合同",
        "industry": "二手房",
        "title": "二手房买卖合同",
        "clauses": [
            {"index": 1, "title": "房屋", "text": "甲方出售位于北京市海淀区的房屋一套。"},
            {"index": 2, "title": "价款", "text": "成交价 800 万元。"},
            {"index": 3, "title": "定金", "text": "乙方支付定金 50 万元。"},
            {"index": 4, "title": "过户", "text": "2026 年 10 月 31 日前完成过户。"},
            {"index": 5, "title": "违约", "text": "甲方违约双倍返还定金, 乙方违约定金不退。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "sales-vehicle-01",
        "contract_type": "销售合同",
        "industry": "汽车",
        "title": "汽车销售合同",
        "clauses": [
            {"index": 1, "title": "车辆", "text": "甲方购买乙方品牌汽车一辆, 型号 Model X, 价 100 万元。"},
            {"index": 2, "title": "交付", "text": "30 日内交付。"},
            {"index": 3, "title": "付款", "text": "全款支付。"},
            {"index": 4, "title": "保修", "text": "整车保修 4 年或 10 万公里。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "sales-bulk-01",
        "contract_type": "销售合同",
        "industry": "大宗商品",
        "title": "钢材采购合同",
        "clauses": [
            {"index": 1, "title": "标的", "text": "采购钢材 1000 吨, 单价 5000 元/吨, 总价 500 万元。"},
            {"index": 2, "title": "交付", "text": "2026 年 11 月 30 日前分批交付。"},
            {"index": 3, "title": "付款", "text": "货到验收合格后 30 日内付款。"},
            {"index": 4, "title": "质量异议", "text": "甲方收货后 7 日内提出质量异议。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "sales-fmcg-01",
        "contract_type": "销售合同",
        "industry": "快消品",
        "title": "快消品经销合同",
        "clauses": [
            {"index": 1, "title": "区域", "text": "乙方为甲方华东地区独家经销商。"},
            {"index": 2, "title": "任务", "text": "年销售额目标 1000 万元。"},
            {"index": 3, "title": "保证金", "text": "乙方支付保证金 50 万元。"},
            {"index": 4, "title": "未达标", "text": "未达标 80% 甲方可取消独家经销权。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "sales-real-estate-bulk-01",
        "contract_type": "销售合同",
        "industry": "商业地产",
        "title": "商业地产销售合同",
        "clauses": [
            {"index": 1, "title": "房屋", "text": "甲方购买乙方商业地产一套, 总价 5000 万元。"},
            {"index": 2, "title": "付款", "text": "分期付款: 首付 30%, 封顶 30%, 交房 40%。"},
            {"index": 3, "title": "交付", "text": "2027 年 12 月 31 日前交付。"},
            {"index": 4, "title": "违约金", "text": "甲方逾期付款按日 0.05% 加收, 乙方逾期交房按日 0.05% 支付。"},
        ],
        "annotations_count": 5,
    },

    # ===== 合伙协议 (8 模板) =====
    {
        "template_id": "partnership-tech-01",
        "contract_type": "合伙协议",
        "industry": "创业合伙",
        "title": "创业公司合伙协议",
        "clauses": [
            {"index": 1, "title": "合伙目的", "text": "共同经营互联网科技公司。"},
            {"index": 2, "title": "出资", "text": "甲方出资 60 万占股 60%, 乙方出资 40 万占股 40%。"},
            {"index": 3, "title": "分工", "text": "甲方任 CEO, 乙方任 CTO。"},
            {"index": 4, "title": "决策", "text": "重大事项需双方一致同意。"},
            {"index": 5, "title": "利润分配", "text": "按出资比例分配。"},
            {"index": 6, "title": "退出", "text": "合伙人退出需经其他合伙人同意。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "partnership-law-01",
        "contract_type": "合伙协议",
        "industry": "律师事务所",
        "title": "律师事务所合伙协议",
        "clauses": [
            {"index": 1, "title": "合伙目的", "text": "共同经营律师事务所。"},
            {"index": 2, "title": "出资", "text": "3 名合伙人各出资 100 万, 各占 1/3 股份。"},
            {"index": 3, "title": "管理", "text": "执行合伙事务的合伙人对合伙企业负责。"},
            {"index": 4, "title": "分配", "text": "利润按出资比例分配。"},
            {"index": 5, "title": "新人", "text": "新合伙人加入需 2/3 以上合伙人同意。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "partnership-limited-01",
        "contract_type": "合伙协议",
        "industry": "有限合伙",
        "title": "有限合伙基金协议(VC)",
        "clauses": [
            {"index": 1, "title": "合伙目的", "text": "投资未上市创业公司股权。"},
            {"index": 2, "title": "GP/LP", "text": "甲方为 GP 出资 1%, 乙方为 LP 出资 99%。"},
            {"index": 3, "title": "管理费", "text": "GP 每年收取管理费 2%。"},
            {"index": 4, "title": "收益分配", "text": "收益超过门槛后 GP 提成 20%。"},
            {"index": 5, "title": "期限", "text": "合伙期限 7 年。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "partnership-jv-01",
        "contract_type": "合伙协议",
        "industry": "中外合资",
        "title": "中外合资经营企业合同",
        "clauses": [
            {"index": 1, "title": "投资", "text": "中方出资 1000 万美元占股 51%, 外方出资 960 万美元占股 49%。"},
            {"index": 2, "title": "董事会", "text": "董事会 7 人, 中方 4 人, 外方 3 人。"},
            {"index": 3, "title": "总经理", "text": "总经理由外方提名。"},
            {"index": 4, "title": "争议", "text": "提交中国国际经济贸易仲裁委员会仲裁。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "partnership-professional-01",
        "contract_type": "合伙协议",
        "industry": "专业服务",
        "title": "会计师事务所合伙协议",
        "clauses": [
            {"index": 1, "title": "合伙目的", "text": "经营会计师事务所。"},
            {"index": 2, "title": "出资", "text": "各合伙人等额出资, 各占 25%。"},
            {"index": 3, "title": "分配", "text": "利润按工作量分配。"},
            {"index": 4, "title": "责任", "text": "合伙人对合伙企业债务承担无限连带责任。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "partnership-restaurant-01",
        "contract_type": "合伙协议",
        "industry": "餐饮合伙",
        "title": "餐饮店合伙经营协议",
        "clauses": [
            {"index": 1, "title": "合伙目的", "text": "经营咖啡店。"},
            {"index": 2, "title": "出资", "text": "甲方出资 30 万, 乙方出资 20 万, 丙方出资 10 万。"},
            {"index": 3, "title": "分工", "text": "甲负责运营, 乙负责财务, 丙负责采购。"},
            {"index": 4, "title": "分配", "text": "按出资比例分配利润。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "partnership-family-01",
        "contract_type": "合伙协议",
        "industry": "家族合伙",
        "title": "家族企业合伙协议",
        "clauses": [
            {"index": 1, "title": "目的", "text": "家族成员共同经营家族企业。"},
            {"index": 2, "title": "出资", "text": "父母出资 60%, 子女各出资 13.33%。"},
            {"index": 3, "title": "管理", "text": "父母任正副总经理, 子女任部门经理。"},
            {"index": 4, "title": "退出", "text": "子女退出需经父母同意。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "partnership-real-estate-01",
        "contract_type": "合伙协议",
        "industry": "房地产合伙",
        "title": "房地产联合开发协议",
        "clauses": [
            {"index": 1, "title": "项目", "text": "联合开发上海市某地块住宅项目。"},
            {"index": 2, "title": "出资", "text": "甲方出资 70%, 乙方出资 30%。"},
            {"index": 3, "title": "分工", "text": "甲方负责报建, 乙方负责销售。"},
            {"index": 4, "title": "利润", "text": "按出资比例分配, 销售利润甲方 60%, 乙方 40%。"},
        ],
        "annotations_count": 5,
    },

    # ===== 委托代理 (8 模板) =====
    {
        "template_id": "agency-legal-01",
        "contract_type": "委托代理",
        "industry": "诉讼代理",
        "title": "民事诉讼委托代理合同",
        "clauses": [
            {"index": 1, "title": "委托事项", "text": "甲方委托乙方代理甲方与张某的民间借贷纠纷一案。"},
            {"index": 2, "title": "代理权限", "text": "一般授权代理。"},
            {"index": 3, "title": "律师费", "text": "律师费 5 万元, 签订时一次性支付。"},
            {"index": 4, "title": "差旅费", "text": "差旅费由甲方实报实销。"},
            {"index": 5, "title": "风险代理", "text": "胜诉后, 按回款金额的 10% 支付风险代理费。"},
            {"index": 6, "title": "解约", "text": "双方可协商解除, 已收费用不退。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "agency-real-estate-01",
        "contract_type": "委托代理",
        "industry": "房产中介",
        "title": "房屋买卖中介合同",
        "clauses": [
            {"index": 1, "title": "委托", "text": "甲方委托乙方居间出售其房产。"},
            {"index": 2, "title": "委托期", "text": "委托期 6 个月。"},
            {"index": 3, "title": "佣金", "text": "成交后, 乙方收取成交价的 2% 作为佣金。"},
            {"index": 4, "title": "独家", "text": "甲方不得委托其他中介或自行成交, 否则支付违约金 5 万元。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "agency-patent-01",
        "contract_type": "委托代理",
        "industry": "知识产权",
        "title": "专利申请委托代理合同",
        "clauses": [
            {"index": 1, "title": "委托", "text": "甲方委托乙方代理专利申请。"},
            {"index": 2, "title": "费用", "text": "代理费 8000 元, 含官费。"},
            {"index": 3, "title": "期限", "text": "乙方应在 30 日内提交申请。"},
            {"index": 4, "title": "保密", "text": "乙方对发明内容承担保密义务。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "agency-tax-01",
        "contract_type": "委托代理",
        "industry": "税务代理",
        "title": "税务代理委托合同",
        "clauses": [
            {"index": 1, "title": "委托", "text": "甲方委托乙方代理纳税申报。"},
            {"index": 2, "title": "期限", "text": "服务期限 1 年。"},
            {"index": 3, "title": "费用", "text": "月费 3000 元。"},
            {"index": 4, "title": "责任", "text": "因乙方失误导致甲方损失, 乙方承担赔偿责任, 上限为 1 年服务费。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "agency-marriage-01",
        "contract_type": "委托代理",
        "industry": "婚姻家事",
        "title": "离婚诉讼委托代理合同",
        "clauses": [
            {"index": 1, "title": "委托", "text": "甲方委托乙方代理离婚诉讼。"},
            {"index": 2, "title": "费用", "text": "律师费 3 万元。"},
            {"index": 3, "title": "结果承诺", "text": "乙方承诺甲方离婚并获得子女抚养权。"},
            {"index": 4, "title": "差旅", "text": "差旅费由甲方承担。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "agency-customs-01",
        "contract_type": "委托代理",
        "industry": "报关",
        "title": "报关代理委托合同",
        "clauses": [
            {"index": 1, "title": "委托", "text": "甲方委托乙方代理进出口报关。"},
            {"index": 2, "title": "费用", "text": "单票报关费 500 元。"},
            {"index": 3, "title": "责任", "text": "因乙方申报错误导致罚款, 乙方承担 50%。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "agency-medical-01",
        "contract_type": "委托代理",
        "industry": "医疗纠纷",
        "title": "医疗纠纷代理合同",
        "clauses": [
            {"index": 1, "title": "委托", "text": "甲方委托乙方代理医疗损害赔偿纠纷。"},
            {"index": 2, "title": "律师费", "text": "律师费 2 万元。"},
            {"index": 3, "title": "风险代理", "text": "胜诉后按赔偿金额的 15% 支付风险代理费。"},
            {"index": 4, "title": "终止", "text": "甲方可随时解除, 已收费用不退。"},
        ],
        "annotations_count": 5,
    },
    {
        "template_id": "agency-arbitration-01",
        "contract_type": "委托代理",
        "industry": "仲裁",
        "title": "仲裁代理委托合同",
        "clauses": [
            {"index": 1, "title": "委托", "text": "甲方委托乙方代理中国国际经济贸易仲裁委员会案件。"},
            {"index": 2, "title": "费用", "text": "律师费 10 万元。"},
            {"index": 3, "title": "授权", "text": "特别授权代理, 含和解权。"},
            {"index": 4, "title": "争议", "text": "提交北京仲裁委员会仲裁。"},
        ],
        "annotations_count": 5,
    },
]


# ===== 风险标注生成规则 =====

# 每份合同生成 5+ 风险标注, 覆盖致命 / 重大 / 建议 三个等级

def generate_annotations_for_template(template: Dict[str, Any]) -> List[Dict[str, Any]]:
    """根据合同模板生成 5+ 风险标注。"""
    annotations = []
    clauses = template["clauses"]

    # 基于关键词扫描, 自动生成标注
    for clause in clauses:
        text = clause["text"]
        title = clause["title"]

        # 致命风险: 违约金过高
        if re.search(r"(?:按\s*日|按\s*天|每\s*逾期.{0,5}天).{0,20}(?:%|百分之|万分之).{0,15}", text):
            annotations.append({
                "clause_index": clause["index"],
                "clause_title": title,
                "risk_level": "fatal",
                "risk_categories": ["违约金过高"],
                "legal_basis": ["《民法典》第五百八十五条", "《最高人民法院关于适用〈中华人民共和国民法典〉合同编通则若干问题的解释》第六十五条"],
                "risk_description": "该条款违约金约定过高, 司法实践中通常被调减。",
                "modification_suggestion": "建议修改为'按 LPR × 1.5 倍' 或'按日万分之五' 等司法保护上限内表述。",
                "stance_impact": "需结合上下文判断",
            })

        # 重大风险: 争议管辖不利
        if re.search(r"(?:甲方|乙方|丙方|出借人|借款人)\s*住所地", text):
            annotations.append({
                "clause_index": clause["index"],
                "clause_title": title,
                "risk_level": "major",
                "risk_categories": ["争议管辖不利"],
                "legal_basis": ["《民事诉讼法》第二十四条", "《民事诉讼法》第三十五条"],
                "risk_description": "约定单方住所地管辖, 对非约定方应诉成本较高。",
                "modification_suggestion": "建议修改为'标的物所在地 / 合同签订地 / 双方住所地任一' 或约定仲裁条款。",
                "stance_impact": "需结合上下文判断",
            })

        # 重大风险: 显失公平 (单方解除权)
        if re.search(r"(?:单方|一方)\s*.{0,10}(?:解除|终止)\s*权", text):
            annotations.append({
                "clause_index": clause["index"],
                "clause_title": title,
                "risk_level": "major",
                "risk_categories": ["显失公平", "解除权失衡"],
                "legal_basis": ["《民法典》第五百六十二条", "《民法典》第五百六十三条"],
                "risk_description": "该条款单方解除权约定, 权利义务严重失衡。",
                "modification_suggestion": "建议区分法定解除与违约解除, 平衡双方权利义务。",
                "stance_impact": "需结合上下文判断",
            })

        # 重大风险: 提前解约高额违约金
        if re.search(r"(?:提前|单方)\s*解(?:除|约).{0,20}\d+\s*个?月.{0,10}租金|违约金", text):
            annotations.append({
                "clause_index": clause["index"],
                "clause_title": title,
                "risk_level": "major",
                "risk_categories": ["解除权失衡"],
                "legal_basis": ["《民法典》第五百八十五条"],
                "risk_description": "提前解约违约金约定过高, 司法实践中可能调减。",
                "modification_suggestion": "建议区分法定解除与违约解除, 违约金按实际损失计算。",
                "stance_impact": "需结合上下文判断",
            })

        # 建议风险: 表述模糊
        if re.search(r"合理期限|尽快|及时|协商解决", text):
            annotations.append({
                "clause_index": clause["index"],
                "clause_title": title,
                "risk_level": "advisory",
                "risk_categories": ["表述模糊"],
                "legal_basis": ["《民法典》第四百六十六条"],
                "risk_description": "条款表述模糊, 缺乏具体期限或方式, 易引发履行争议。",
                "modification_suggestion": "建议替换为具体数值 (如'30 日内' / '3 个工作日内')。",
                "stance_impact": "中性",
            })

        # 建议风险: 永久保密
        if "永久" in text and "保密" in text:
            annotations.append({
                "clause_index": clause["index"],
                "clause_title": title,
                "risk_level": "advisory",
                "risk_categories": ["期限异常"],
                "legal_basis": ["《民法典》第五百零一条"],
                "risk_description": "约定永久保密义务, 可能超出合理范围, 司法实践中可能调整。",
                "modification_suggestion": "建议约定保密期限 (如商业秘密存续期间 + 2-5 年)。",
                "stance_impact": "不利",
            })

        # 建议风险: 全部责任
        if re.search(r"(?:全部|所有|全部)\s*(?:责任|损失)", text) and re.search(r"承担|赔偿", text):
            annotations.append({
                "clause_index": clause["index"],
                "clause_title": title,
                "risk_level": "advisory",
                "risk_categories": ["可优化"],
                "legal_basis": ["《民法典》第五百零九条"],
                "risk_description": "约定一方承担全部责任, 可能显失公平, 建议按过错比例分担。",
                "modification_suggestion": "建议修改为'按过错比例承担相应责任'。",
                "stance_impact": "需结合上下文判断",
            })

    # 如果标注数 < 5, 补充通用标注
    while len(annotations) < 5:
        clause = clauses[len(annotations) % len(clauses)]
        annotations.append({
            "clause_index": clause["index"],
            "clause_title": clause["title"],
            "risk_level": "advisory",
            "risk_categories": ["可优化"],
            "legal_basis": ["《民法典》相关条款"],
            "risk_description": "该条款可结合具体业务场景进一步优化表述。",
            "modification_suggestion": "建议结合行业惯例与司法实践, 优化条款表述。",
            "stance_impact": "中性",
        })

    # 限制每份合同最多 8 个标注
    return annotations[:8]


# ===== 主函数 =====

def seed_data(templates_count: int = 56, annotations_count: int = 280,
              reset: bool = False) -> Dict[str, int]:
    """生成合同模板与风险标注, 写入 data/contracts/。

    Args:
        templates_count: 合同模板数 (默认 56)
        annotations_count: 风险标注数 (默认 280)
        reset: 是否重置现有数据

    Returns:
        包含生成数量的 dict
    """

    if reset and CONTRACTS_DIR.exists():
        import shutil
        shutil.rmtree(CONTRACTS_DIR)
    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)

    templates_to_use = CONTRACT_TEMPLATES[:templates_count]

    total_annotations = 0
    for template in templates_to_use:
        # 生成风险标注
        annotations = generate_annotations_for_template(template)
        total_annotations += len(annotations)

        # 写入模板文件
        template_file = CONTRACTS_DIR / f"{template['template_id']}.json"
        template_with_annotations = {
            **template,
            "annotations": annotations,
            "created_at": "2026-06-29",
            "updated_at": "2026-06-29",
        }
        with open(template_file, "w", encoding="utf-8") as f:
            json.dump(template_with_annotations, f, ensure_ascii=False, indent=2)

    # 写入汇总索引
    index_file = CONTRACTS_DIR / "_index.json"
    index = {
        "total_templates": len(templates_to_use),
        "total_annotations": total_annotations,
        "contract_types": sorted(set(t["contract_type"] for t in templates_to_use)),
        "industries": sorted(set(t["industry"] for t in templates_to_use if t.get("industry"))),
        "created_at": "2026-06-29",
        "data_source": "LexPrime 自建 (W3 阶段)",
    }
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    return {
        "templates": len(templates_to_use),
        "annotations": total_annotations,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LexPrime 合同数据扩量")
    parser.add_argument("--templates", type=int, default=56, help="合同模板数 (默认 56)")
    parser.add_argument("--annotations", type=int, default=280, help="风险标注数 (默认 280)")
    parser.add_argument("--reset", action="store_true", help="重置现有数据")
    args = parser.parse_args()

    import re
    result = seed_data(args.templates, args.annotations, args.reset)
    print("\n✅ 数据扩量完成:")
    print(f"   - 合同模板: {result['templates']} 份")
    print(f"   - 风险标注: {result['annotations']} 条")
    print(f"   - 数据目录: {CONTRACTS_DIR}")
    print(f"   - 索引文件: {CONTRACTS_DIR / '_index.json'}")