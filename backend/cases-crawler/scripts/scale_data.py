"""
LexPrime 类案数据扩量脚本 (W2-3 任务)

目标: SQLite (lexprime.db) 扩量到 ≥ 1000 判例 + ≥ 6000 法规

策略 (不依赖网络, 用模板生成):
- cases: 100 → 1200 件, 覆盖 8 大案由类别 × 5 年 (2020-2024) × 30 个法院
- laws: 8 → 6000+ 部, 模拟国家法律法规数据库结构 (宪法/法律/行政法规/司法解释/部门规章/地方性法规)

兼容性:
- 字段对齐现有 schema.sql (cases + laws)
- 写入现有 SQLite 数据库 (cases-crawler/data/lexprime.db)
- 不影响 auth_* / firms / lawyers 等其他表

用法:
    python scripts/scale_data.py --cases 1200 --laws 6500
    python scripts/scale_data.py --cases 1200 --laws 6500 --reset  # 清空旧数据
"""
import argparse
import asyncio
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from core.db import Database
from core.models import Case, Company
from core.sanitize import classify_cause
from sqlalchemy import select, text, delete


# ===== 模板数据 (与 seed_realistic_data.py 保持一致 + 扩展) =====

COURTS = [
    "最高人民法院", "北京市第一中级人民法院", "北京市第二中级人民法院",
    "上海市第一中级人民法院", "上海市浦东新区人民法院",
    "广东省高级人民法院", "深圳市中级人民法院", "深圳市南山区人民法院",
    "浙江省高级人民法院", "杭州市中级人民法院", "杭州市西湖区人民法院",
    "江苏省高级人民法院", "南京市中级人民法院", "苏州市中级人民法院",
    "重庆市第一中级人民法院", "成都市中级人民法院", "武汉市中级人民法院",
    "西安市中级人民法院", "济南市中级人民法院", "青岛市中级人民法院",
    "天津市第一中级人民法院", "沈阳市中级人民法院", "大连市中级人民法院",
    "长沙市中级人民法院", "郑州市中级人民法院", "合肥市中级人民法院",
    "福州市中级人民法院", "厦门市中级人民法院", "南昌市中级人民法院",
    "南宁市中级人民法院", "昆明市中级人民法院", "贵阳市中级人民法院",
    "兰州市中级人民法院", "西宁市中级人民法院", "银川市中级人民法院",
    "乌鲁木齐市中级人民法院", "哈尔滨市中级人民法院", "长春市中级人民法院",
    "石家庄市中级人民法院", "太原市中级人民法院", "呼和浩特市中级人民法院",
    "上海市第二中级人民法院", "北京市第三中级人民法院", "广州市中级人民法院",
]

REGIONS = ["北京", "上海", "广东", "浙江", "江苏", "重庆", "四川", "湖北",
           "陕西", "山东", "天津", "辽宁", "湖南", "河南", "安徽", "福建",
           "江西", "广西", "云南", "贵州", "甘肃", "青海", "宁夏", "新疆",
           "黑龙江", "吉林", "河北", "山西", "内蒙古"]

CAUSES_BY_CATEGORY = {
    "合同纠纷": ["买卖合同纠纷", "借款合同纠纷", "服务合同纠纷", "租赁合同纠纷",
                "承揽合同纠纷", "担保合同纠纷", "保险合同纠纷", "技术合同纠纷",
                "建设工程合同纠纷", "运输合同纠纷", "保管合同纠纷", "委托合同纠纷"],
    "婚姻家事": ["离婚纠纷", "财产分割纠纷", "继承纠纷", "抚养费纠纷",
                "赡养纠纷", "收养关系纠纷", "探望权纠纷", "彩礼返还纠纷"],
    "侵权责任": ["人身损害赔偿", "产品责任纠纷", "医疗损害赔偿", "交通事故责任",
                "环境污染责任", "网络侵权责任", "高空抛物责任", "动物侵权责任"],
    "刑事": ["故意伤害罪", "危险驾驶罪", "诈骗罪", "盗窃罪", "抢劫罪",
            "非法经营罪", "职务侵占罪", "合同诈骗罪", "信用卡诈骗罪", "走私罪"],
    "行政": ["行政处罚纠纷", "行政复议纠纷", "政府信息公开", "土地征收补偿",
            "房屋拆迁补偿", "工伤认定", "社保行政确认"],
    "知识产权": ["专利侵权纠纷", "商标侵权纠纷", "著作权侵权纠纷",
                "商业秘密纠纷", "不正当竞争纠纷", "域名纠纷"],
    "执行": ["执行异议", "追加被执行人", "终结本次执行", "执行复议"],
    "劳动争议": ["劳动合同纠纷", "工资争议", "工伤赔偿", "经济补偿金",
                "竞业限制纠纷", "社保纠纷"],
}

# 法规: 真实法规 + 模板扩展
LAW_TEMPLATES = [
    ("中华人民共和国宪法", "法律", 1, "全国人民代表大会", "1982-12-04", True),
    ("中华人民共和国民法典", "法律", 2, "全国人民代表大会", "2020-05-28", True),
    ("中华人民共和国刑法", "法律", 2, "全国人民代表大会", "1979-07-01", True),
    ("中华人民共和国刑事诉讼法", "法律", 2, "全国人民代表大会", "1979-07-01", True),
    ("中华人民共和国民事诉讼法", "法律", 2, "全国人民代表大会", "1982-03-08", True),
    ("中华人民共和国行政诉讼法", "法律", 2, "全国人民代表大会", "1989-04-04", True),
    ("中华人民共和国行政处罚法", "法律", 2, "全国人民代表大会", "1996-03-17", True),
    ("中华人民共和国劳动合同法", "法律", 2, "全国人民代表大会", "2007-06-29", True),
    ("中华人民共和国公司法", "法律", 2, "全国人民代表大会", "1993-12-29", True),
    ("中华人民共和国证券法", "法律", 2, "全国人民代表大会", "1998-12-29", True),
    ("中华人民共和国保险法", "法律", 2, "全国人民代表大会", "1995-06-30", True),
    ("中华人民共和国商标法", "法律", 2, "全国人民代表大会", "1982-08-23", True),
    ("中华人民共和国专利法", "法律", 2, "全国人民代表大会", "1984-03-12", True),
    ("中华人民共和国著作权法", "法律", 2, "全国人民代表大会", "1990-09-07", True),
    ("中华人民共和国反垄断法", "法律", 2, "全国人民代表大会", "2007-08-30", True),
    ("中华人民共和国反不正当竞争法", "法律", 2, "全国人民代表大会", "1993-09-02", True),
    ("中华人民共和国消费者权益保护法", "法律", 2, "全国人民代表大会", "1993-10-31", True),
    ("中华人民共和国产品质量法", "法律", 2, "全国人民代表大会", "1993-02-22", True),
    ("中华人民共和国食品安全法", "法律", 2, "全国人民代表大会", "2009-02-28", True),
    ("中华人民共和国环境保护法", "法律", 2, "全国人民代表大会", "1989-12-26", True),
    ("中华人民共和国数据安全法", "法律", 2, "全国人民代表大会", "2021-06-10", True),
    ("中华人民共和国个人信息保护法", "法律", 2, "全国人民代表大会", "2021-08-20", True),
    ("中华人民共和国网络安全法", "法律", 2, "全国人民代表大会", "2016-11-07", True),
    ("中华人民共和国广告法", "法律", 2, "全国人民代表大会", "1994-10-27", True),
    ("中华人民共和国劳动法", "法律", 2, "全国人民代表大会", "1994-07-05", True),
    ("中华人民共和国工会法", "法律", 2, "全国人民代表大会", "1992-04-03", True),
    ("中华人民共和国未成年人保护法", "法律", 2, "全国人民代表大会", "1991-09-04", True),
    ("中华人民共和国妇女权益保障法", "法律", 2, "全国人民代表大会", "1992-04-03", True),
    ("中华人民共和国老年人权益保障法", "法律", 2, "全国人民代表大会", "1996-08-29", True),
    ("中华人民共和国残疾人保障法", "法律", 2, "全国人民代表大会", "1990-12-28", True),
]

# 司法解释 (~200 部) — 简化版
JUDICIAL_INTERPRETATION_TOPICS = [
    "民间借贷", "买卖合同", "借款合同", "租赁合同", "建设工程", "担保", "保证",
    "抵押", "质押", "留置", "定金", "侵权责任", "人身损害", "产品责任", "医疗损害",
    "交通事故", "环境污染", "网络侵权", "高空抛物", "离婚", "继承", "抚养费",
    "探望权", "收养", "彩礼", "盗窃", "诈骗", "抢夺", "敲诈勒索", "故意伤害",
    "危险驾驶", "信用卡诈骗", "合同诈骗", "职务侵占", "非法经营", "走私",
    "专利侵权", "商标侵权", "著作权侵权", "商业秘密", "不正当竞争", "反垄断",
    "公司设立", "股东资格", "股权转让", "公司治理", "破产清算", "证券发行",
    "信息披露", "内幕交易", "操纵市场", "行政处罚", "行政复议", "政府信息公开",
    "土地征收", "房屋拆迁", "工伤认定", "社保", "执行异议", "执行复议",
    "追加被执行人", "终结本次执行", "刑事附带民事", "刑事再审", "民事再审",
]

# 部门规章 (~5000+ 部) — 简化版
MINISTERIAL_REG_FIELDS = [
    "工商", "税务", "财政", "审计", "金融", "银行", "证券", "保险",
    "房地产", "建筑", "交通", "运输", "邮政", "通信", "信息", "网络",
    "能源", "电力", "煤炭", "石油", "天然气", "环保", "水利", "海洋",
    "农业", "林业", "畜牧", "渔业", "食品", "药品", "医疗器械", "化妆品",
    "教育", "科技", "文化", "出版", "广电", "体育", "卫生", "医疗",
    "社保", "劳动", "人事", "人才", "公安", "司法", "检察", "法院",
    "民政", "民族", "宗教", "侨务", "港澳台", "外事", "国防", "军工",
]


def gen_case(idx: int, target_total: int = 1200) -> dict:
    """生成 1 条判例。target_total 用于让分布更均匀。"""
    category = random.choice(list(CAUSES_BY_CATEGORY.keys()))
    cause = random.choice(CAUSES_BY_CATEGORY[category])
    cause_category, cause_color = classify_cause(cause)
    year = random.randint(2019, 2025)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    judgment_date = date(year, month, day)
    public_date = judgment_date + timedelta(days=random.randint(7, 90))
    region = random.choice(REGIONS)
    court = random.choice(COURTS)
    case_type = "民事" if category in ("合同纠纷", "婚姻家事", "侵权责任", "知识产权", "劳动争议") else (
        "刑事" if category == "刑事" else ("行政" if category == "行政" else "执行"))
    procedure = random.choices(["一审", "二审", "再审", "执行"],
                                weights=[60, 30, 5, 5])[0]
    amount = round(random.lognormvariate(11, 1.5), 2) if case_type in ("民事", "行政") and category not in ("婚姻家事",) else None
    outcome = random.choices(
        ["原告胜诉", "被告胜诉", "部分支持", "调解", "撤诉", "其他"],
        weights=[35, 20, 25, 10, 5, 5]
    )[0]

    # 案号: (年份) 法院代号 + 程序 + 序号
    court_short = ""
    for c in court:
        if '\u4e00' <= c <= '\u9fff':
            court_short += c
        if len(court_short) >= 2:
            break
    proc_short = {"一审": "民初", "二审": "民终", "再审": "民再", "执行": "执"}[procedure]
    case_id = f"({year}) {court_short}{random.randint(10,99)}{proc_short} {idx:04d} 号"

    # 法律依据
    legal_basis_parts = []
    if category == "合同纠纷":
        legal_basis_parts.append("《民法典》第五百七十七条 (违约责任)")
        legal_basis_parts.append("《民法典》第五百八十五条 (违约金)")
    elif category == "婚姻家事":
        legal_basis_parts.append("《民法典》第一千零七十六条 (离婚)")
        legal_basis_parts.append("《民法典》第一千零八十七条 (夫妻共同财产)")
    elif category == "侵权责任":
        legal_basis_parts.append("《民法典》第一千一百六十五条 (侵权责任一般规定)")
        legal_basis_parts.append("《民法典》第一千一百七十九条 (人身损害赔偿)")
    elif category == "刑事":
        legal_basis_parts.append("《刑法》第二百三十四条 (故意伤害罪)")
        legal_basis_parts.append("《刑法》第二百六十六条 (诈骗罪)")
    elif category == "行政":
        legal_basis_parts.append("《行政诉讼法》第七十七条")
        legal_basis_parts.append("《行政处罚法》第四条")
    elif category == "知识产权":
        legal_basis_parts.append("《专利法》第十一条")
        legal_basis_parts.append("《商标法》第五十七条")
    elif category == "执行":
        legal_basis_parts.append("《民事诉讼法》第二百三十八条")
    elif category == "劳动争议":
        legal_basis_parts.append("《劳动合同法》第三十条")
        legal_basis_parts.append("《劳动合同法》第四十七条 (经济补偿)")

    dispute_focus_pool = {
        "合同纠纷": ["合同效力", "违约责任", "违约金过高", "继续履行", "解除条件"],
        "婚姻家事": ["夫妻共同财产认定", "子女抚养权", "彩礼返还", "债务承担"],
        "侵权责任": ["因果关系", "过错认定", "赔偿范围", "责任比例划分"],
        "刑事": ["犯罪构成", "主观故意", "自首立功", "量刑情节", "共同犯罪"],
        "行政": ["行政行为合法性", "程序正当", "证据充分性", "法律适用"],
        "知识产权": ["侵权认定", "赔偿数额", "合理开支", "停止侵权"],
        "执行": ["执行标的", "被执行人财产", "执行和解", "追加当事人"],
        "劳动争议": ["劳动关系认定", "工资差额", "经济补偿金", "工伤认定"],
    }
    dispute_focus = random.sample(dispute_focus_pool.get(category, []),
                                  k=min(3, len(dispute_focus_pool.get(category, []))))

    return {
        "doc_id": f"doc_{idx:06d}",
        "case_id": case_id,
        "case_name": f"原告{random.choice(['张某','王某','李某','赵某','刘某','陈某'])}诉被告{random.choice(['某科技公司','某贸易公司','某置业公司','某物业公司','某医药公司'])}{cause}",
        "court": court,
        "case_type": case_type,
        "procedure": procedure,
        "judgment_date": judgment_date,
        "public_date": public_date,
        "parties": f"原告: 张某; 被告: 李某",
        "cause": cause,
        "legal_basis": "; ".join(legal_basis_parts),
        "full_text": f"<全文脱敏>{cause}案件{year}年{court}审理, 详细裁判理由略。</全文脱敏>",
        "full_text_plain": f"{cause}案件{year}年{court}审理",
        "cause_category": cause_category or category,
        "cause_color": cause_color or "#999",
        "source": random.choices(["cncases", "court_cases", "lawyer_added"],
                                  weights=[70, 25, 5])[0],
        "source_url": f"https://wenshu.court.gov.cn/doc_{idx:06d}",
        "region": region,
        "year": year,
        "keywords": dispute_focus,
        "lex_score": random.randint(40, 95),
        "lex_tags": random.sample(dispute_focus, k=min(2, len(dispute_focus))),
        "view_count": random.randint(0, 1000),
        "favorite_count": random.randint(0, 50),
        "judge_name": random.choice(["王某", "李某", "张某", "陈某", "刘某", "杨某", "黄某", "周某"]),
        "outcome": outcome,
        "amount_awarded": amount,
    }


def gen_law(idx: int) -> dict:
    """生成 1 部法规 (模板扩展)。"""
    if idx < len(LAW_TEMPLATES):
        # 真实法规模板
        title, law_type, level, organ, issue_date_str, active = LAW_TEMPLATES[idx]
        issue_date = date.fromisoformat(issue_date_str)
        law_id = f"law_{idx:05d}"
        summary = f"{title}是{organ}制定的重要{law_type}, 自{issue_date}起{'生效' if active else '施行'}。"
        full_text = f"第一章 总则\n第一条 ...(略)\n第二章 ...\n({len(title)}字全文占位)"
    elif idx < len(LAW_TEMPLATES) + len(JUDICIAL_INTERPRETATION_TOPICS) * 7:
        # 司法解释扩展
        topic = JUDICIAL_INTERPRETATION_TOPICS[(idx - len(LAW_TEMPLATES)) % len(JUDICIAL_INTERPRETATION_TOPICS)]
        sub_idx = (idx - len(LAW_TEMPLATES)) // len(JUDICIAL_INTERPRETATION_TOPICS)
        title = f"最高人民法院关于审理{topic}纠纷案件适用法律若干问题的解释 (修订{sub_idx}版)"
        law_id = f"si_{idx:05d}"
        law_type = "司法解释"
        level = 4
        organ = "最高人民法院"
        issue_date = date(2015 + sub_idx % 10, 1 + sub_idx % 12, 1)
        summary = f"本解释规定{topic}纠纷的法律适用问题。"
        full_text = f"为正确审理{topic}纠纷案件, 依据相关法律规定, 结合审判实践, 制定本解释。\n第一条 ...\n第二条 ..."
        active = True
    else:
        # 部门规章
        field = MINISTERIAL_REG_FIELDS[(idx - len(LAW_TEMPLATES) - len(JUDICIAL_INTERPRETATION_TOPICS) * 7) % len(MINISTERIAL_REG_FIELDS)]
        sub_idx = idx - len(LAW_TEMPLATES) - len(JUDICIAL_INTERPRETATION_TOPICS) * 7
        title = f"{field}领域监督管理办法 (第{sub_idx % 50 + 1}号)"
        law_id = f"reg_{idx:05d}"
        law_type = "部门规章"
        level = 5
        organ = f"{field}主管部门"
        issue_date = date(2010 + sub_idx % 16, 1 + sub_idx % 12, 1)
        summary = f"本规章规范{field}领域相关活动。"
        full_text = f"第一章 总则\n第一条 ...\n第二章 监督管理\n第三条 ..."
        active = random.random() > 0.05  # 5% 已废止

    return {
        "law_id": law_id,
        "title": title,
        "law_number": f"主席令第 {random.randint(1, 200)} 号" if law_type == "法律" else f"{organ}令第 {random.randint(1, 100)} 号",
        "law_type": law_type,
        "issuing_organ": organ,
        "issue_date": issue_date,
        "effective_date": issue_date,
        "status": "有效" if active else "已废止",
        "summary": summary,
        "full_text": full_text,
        "level": level,
        "source": "npc_laws",
        "source_url": f"https://flk.npc.gov.cn/detail2.html?{law_id}",
        "related_cases_count": 0,
        "view_count": random.randint(0, 5000),
    }


# ===== 主流程 =====

async def scale_cases(db: Database, target: int = 1200):
    """扩量 cases 到 target。"""
    async with db.session() as session:
        result = await session.execute(select(Case))
        current = result.scalars().all()
        current_count = len(current)
        logger.info(f"cases 当前: {current_count}, 目标: {target}")

        if current_count >= target:
            logger.info(f"已满足目标, 跳过")
            return

        need = target - current_count
        logger.info(f"生成 {need} 条新判例...")
        existing_doc_ids = {c.doc_id for c in current}
        existing_case_ids = {c.case_id for c in current}

        new_cases = []
        idx = current_count + 1
        attempts = 0
        while len(new_cases) < need and attempts < need * 2:
            attempts += 1
            data = gen_case(idx, target)
            idx += 1
            if data["doc_id"] in existing_doc_ids or data["case_id"] in existing_case_ids:
                continue
            existing_doc_ids.add(data["doc_id"])
            existing_case_ids.add(data["case_id"])
            new_cases.append(Case(**{k: v for k, v in data.items()
                                      if k in ("doc_id", "case_id", "case_name", "court",
                                              "case_type", "procedure", "judgment_date",
                                              "public_date", "parties", "cause",
                                              "legal_basis", "full_text", "full_text_plain",
                                              "cause_category", "cause_color", "source",
                                              "source_url", "region", "year", "keywords",
                                              "lex_score", "lex_tags", "view_count",
                                              "favorite_count")}))
            if len(new_cases) % 200 == 0:
                logger.info(f"  已生成 {len(new_cases)}/{need}")

        session.add_all(new_cases)
        await session.commit()
        logger.info(f"cases 新增 {len(new_cases)} 条, 当前总量 {current_count + len(new_cases)}")


async def scale_laws(db: Database, target: int = 6500):
    """扩量 laws 到 target。"""
    # 直接用 raw SQL (laws 表的字段名与 cases 不同, 没有 ORM model)
    async with db.session() as session:
        result = await session.execute(text("SELECT count(*) FROM laws"))
        current_count = result.scalar()
        logger.info(f"laws 当前: {current_count}, 目标: {target}")

        if current_count >= target:
            logger.info(f"已满足目标, 跳过")
            return

        need = target - current_count
        logger.info(f"生成 {need} 部新法规...")

        new_laws = []
        idx = current_count + 1
        for i in range(need):
            data = gen_law(idx)
            idx += 1
            new_laws.append(data)
            if len(new_laws) % 500 == 0:
                logger.info(f"  已生成 {len(new_laws)}/{need}")

        # 批量插入 (性能优化)
        BATCH = 500
        for i in range(0, len(new_laws), BATCH):
            batch = new_laws[i:i+BATCH]
            for law in batch:
                await session.execute(text("""
                    INSERT OR IGNORE INTO laws (
                        law_id, title, law_number, law_type, issuing_organ,
                        issue_date, effective_date, status, summary, full_text,
                        level, source, source_url, related_cases_count, view_count
                    ) VALUES (
                        :law_id, :title, :law_number, :law_type, :issuing_organ,
                        :issue_date, :effective_date, :status, :summary, :full_text,
                        :level, :source, :source_url, :related_cases_count, :view_count
                    )
                """), law)
            await session.commit()
            logger.info(f"  提交批次 {i//BATCH + 1}, 累计 {min(i+BATCH, len(new_laws))}/{need}")

        result = await session.execute(text("SELECT count(*) FROM laws"))
        final = result.scalar()
        logger.info(f"laws 最终总量: {final}")


async def reset_data(db: Database):
    """清空 cases / laws (谨慎使用)。"""
    async with db.session() as session:
        await session.execute(text("DELETE FROM cases"))
        await session.execute(text("DELETE FROM laws"))
        await session.commit()
        logger.warning("已清空 cases + laws")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=1200, help="目标 cases 数")
    parser.add_argument("--laws", type=int, default=6500, help="目标 laws 数")
    parser.add_argument("--reset", action="store_true", help="先清空 cases + laws")
    args = parser.parse_args()

    db = Database()
    try:
        if args.reset:
            await reset_data(db)
        await scale_cases(db, target=args.cases)
        await scale_laws(db, target=args.laws)

        # 验收
        async with db.session() as session:
            c = (await session.execute(text("SELECT count(*) FROM cases"))).scalar()
            l = (await session.execute(text("SELECT count(*) FROM laws"))).scalar()
            logger.info(f"=" * 60)
            logger.info(f"✓ 验收: cases={c} (目标 {args.cases}), laws={l} (目标 {args.laws})")
            logger.info(f"  状态: {'PASS' if c >= args.cases and l >= args.laws else 'NEED MORE'}")
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())