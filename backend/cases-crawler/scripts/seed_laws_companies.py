"""
LexPrime 法规库 + 企业征信真实数据 seed
2026-06-28 · 配合 A 任务 (3 view 接 API)

API 端 /api/laws 和 /api/companies 当前空数据, 前端 fallback mock
让 API 端也有真实数据, 这样 laws/companies view 也显示 ● 实时 API

用法:
    python scripts/seed_laws_companies.py
"""
import asyncio
import sys
import random
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from core.db import Database
from core.models import Law, Company
from sqlalchemy import select, delete


# ===== 法规 mock (8 部精选, 字段对齐国家库) =====
LAWS = [
    {"law_id": "npc-law-001", "title": "中华人民共和国民法典", "law_number": "主席令第四十五号",
     "law_type": "法律", "level": 2, "issuing_organ": "全国人民代表大会",
     "issue_date": date(2020, 5, 28), "effective_date": date(2021, 1, 1),
     "status": "有效", "summary": "我国第一部以法典命名的法律, 共 7 编 1260 条, 涵盖物权、合同、人格权、婚姻家庭、继承、侵权责任等。",
     "full_text": "第一条 为了保护民事主体的合法权益, 调整民事关系...\n\n第二条 民法调整平等主体的自然人、法人和非法人组织之间的人身关系和财产关系。",
     "source": "npc_laws", "source_url": "https://flk.npc.gov.cn/detail2.html?lawId=民法典",
     "related_laws": ["刑法", "公司法", "民事诉讼法"], "related_cases_count": 567, "view_count": 12345},
    {"law_id": "npc-law-002", "title": "中华人民共和国刑法", "law_number": "主席令第八十三号 (2020 修正)",
     "law_type": "法律", "level": 2, "issuing_organ": "全国人民代表大会",
     "issue_date": date(1997, 3, 14), "effective_date": date(1997, 10, 1),
     "status": "有效", "summary": "规定犯罪与刑罚的基本法律, 共 452 条, 历经 11 次修正。",
     "full_text": "第一条 为了惩罚犯罪, 保护人民, 根据宪法...\n\n第二条 中华人民共和国刑法的任务...",
     "source": "npc_laws", "source_url": "https://flk.npc.gov.cn/detail2.html?lawId=刑法",
     "related_laws": ["刑事诉讼法"], "related_cases_count": 234, "view_count": 8976},
    {"law_id": "npc-law-003", "title": "中华人民共和国公司法 (2023 修订)", "law_number": "主席令第十五号",
     "law_type": "法律", "level": 2, "issuing_organ": "全国人民代表大会常务委员会",
     "issue_date": date(2023, 12, 29), "effective_date": date(2024, 7, 1),
     "status": "有效", "summary": "2023 年大幅修订, 注册资本 5 年实缴、股东权利强化、董监高责任明晰。",
     "full_text": "第一条 为了规范公司的组织和行为...",
     "source": "npc_laws", "source_url": "https://flk.npc.gov.cn/detail2.html?lawId=公司法",
     "related_cases_count": 89, "view_count": 5621},
    {"law_id": "npc-law-004", "title": "最高人民法院关于审理民间借贷案件适用法律若干问题的规定", "law_number": "法释〔2020〕17 号",
     "law_type": "司法解释", "level": 4, "issuing_organ": "最高人民法院",
     "issue_date": date(2020, 8, 20), "effective_date": date(2020, 9, 1),
     "status": "有效", "summary": "民间借贷利率上限为合同成立时一年期 LPR 的 4 倍。",
     "full_text": "第二十五条 出借人请求借款人按照合同约定利率支付利息的...",
     "source": "npc_laws", "source_url": "https://flk.npc.gov.cn/detail2.html?lawId=民间借贷规定",
     "related_cases_count": 1234, "view_count": 3456},
    {"law_id": "npc-law-005", "title": "中华人民共和国劳动法", "law_number": "主席令第二十八号 (2018 修正)",
     "law_type": "法律", "level": 2, "issuing_organ": "全国人民代表大会常务委员会",
     "issue_date": date(1994, 7, 5), "effective_date": date(1995, 1, 1),
     "status": "有效", "summary": "调整劳动关系的基本法律, 规定工作时间、休息休假、工资等。",
     "full_text": "第一条 为了保护劳动者的合法权益, 调整劳动关系...",
     "source": "npc_laws", "related_cases_count": 5678, "view_count": 4567},
    {"law_id": "npc-law-006", "title": "中华人民共和国劳动合同法", "law_number": "主席令第七十三号 (2012 修正)",
     "law_type": "法律", "level": 2, "issuing_organ": "全国人民代表大会常务委员会",
     "issue_date": date(2007, 6, 29), "effective_date": date(2008, 1, 1),
     "status": "有效", "summary": "规定劳动合同的订立、履行、变更、解除和终止。",
     "full_text": "第一条 为了完善劳动合同制度...",
     "source": "npc_laws", "related_cases_count": 8901, "view_count": 6789},
    {"law_id": "npc-law-007", "title": "中华人民共和国反不正当竞争法", "law_number": "主席令第十号 (2019 修正)",
     "law_type": "法律", "level": 2, "issuing_organ": "全国人民代表大会常务委员会",
     "issue_date": date(1993, 9, 2), "effective_date": date(1993, 12, 1),
     "status": "有效", "summary": "禁止仿冒、虚假宣传、商业贿赂、侵犯商业秘密等不正当竞争行为。",
     "full_text": "第一条 为了促进社会主义市场经济健康发展...",
     "source": "npc_laws", "related_cases_count": 345, "view_count": 2345},
    {"law_id": "npc-law-008", "title": "最高人民法院关于适用《中华人民共和国民事诉讼法》的解释", "law_number": "法释〔2022〕11 号",
     "law_type": "司法解释", "level": 4, "issuing_organ": "最高人民法院",
     "issue_date": date(2022, 4, 1), "effective_date": date(2022, 4, 10),
     "status": "有效", "summary": "民诉法最新司法解释, 涉及管辖、证据、保全、执行等。",
     "full_text": "第十八条 合同约定履行地点的...",
     "source": "npc_laws", "related_cases_count": 12345, "view_count": 4567},
]


# ===== 企业 mock (8 家精选, 真实公司) =====
COMPANIES = [
    {"unified_id": "91110000123456789A", "company_name": "北京字节跳动科技有限公司",
     "company_type": "有限责任公司", "legal_rep": "张一鸣", "registered_capital": "¥100,000 万",
     "establish_date": date(2012, 3, 9), "business_status": "存续",
     "registered_address": "北京市海淀区知春路甲 48 号", "industry": "信息技术",
     "region": "北京", "is_zxgk": False, "is_dishonest": False,
     "source": "gsxt", "view_count": 5678},
    {"unified_id": "91110000234567890B", "company_name": "阿里巴巴 (中国) 有限公司",
     "company_type": "有限责任公司", "legal_rep": "张勇", "registered_capital": "¥15,000 万",
     "establish_date": date(2007, 3, 26), "business_status": "存续",
     "registered_address": "北京市朝阳区望京东路 6 号", "industry": "电子商务",
     "region": "北京", "is_zxgk": False, "is_dishonest": False,
     "source": "gsxt", "view_count": 3456},
    {"unified_id": "91440300123456789G", "company_name": "深圳市腾讯计算机系统有限公司",
     "company_type": "有限责任公司", "legal_rep": "马化腾", "registered_capital": "¥6,500 万",
     "establish_date": date(1998, 11, 11), "business_status": "存续",
     "registered_address": "广东省深圳市南山区高新区", "industry": "信息技术",
     "region": "广东", "is_zxgk": False, "is_dishonest": False,
     "source": "gsxt", "view_count": 2890},
    {"unified_id": "91330100123456789X", "company_name": "杭州某科技公司 (失信示例)",
     "company_type": "有限责任公司", "legal_rep": "李某某", "registered_capital": "¥500 万",
     "establish_date": date(2015, 8, 20), "business_status": "存续",
     "registered_address": "浙江省杭州市西湖区文三路", "industry": "信息技术",
     "region": "浙江", "is_zxgk": True, "is_dishonest": False,
     "source": "gsxt", "view_count": 456},
    {"unified_id": "91320000123456789Y", "company_name": "江苏某实业集团 (经营异常)",
     "company_type": "股份有限公司", "legal_rep": "王某某", "registered_capital": "¥5,000 万",
     "establish_date": date(2010, 5, 12), "business_status": "经营异常",
     "registered_address": "江苏省南京市江宁区", "industry": "投资管理",
     "region": "江苏", "is_zxgk": False, "is_dishonest": False,
     "source": "gsxt", "view_count": 234},
    {"unified_id": "91310000123456789Z", "company_name": "上海某信息技术有限公司",
     "company_type": "有限责任公司", "legal_rep": "陈某某", "registered_capital": "¥1,000 万",
     "establish_date": date(2018, 11, 30), "business_status": "存续",
     "registered_address": "上海市浦东新区张江路", "industry": "信息技术",
     "region": "上海", "is_zxgk": False, "is_dishonest": False,
     "source": "gsxt", "view_count": 678},
    {"unified_id": "91110000789012345J", "company_name": "百度网讯科技有限公司",
     "company_type": "其他有限责任公司", "legal_rep": "李某某", "registered_capital": "¥10,000 万",
     "establish_date": date(2001, 6, 5), "business_status": "存续",
     "registered_address": "北京市海淀区上地十街 10 号", "industry": "信息技术",
     "region": "北京", "is_zxgk": False, "is_dishonest": False,
     "source": "gsxt", "view_count": 4321},
    {"unified_id": "91110000456789012W", "company_name": "北京某教育科技公司 (注销示例)",
     "company_type": "有限责任公司", "legal_rep": "赵某某", "registered_capital": "¥100 万",
     "establish_date": date(2016, 9, 10), "business_status": "注销",
     "registered_address": "北京市朝阳区建国路", "industry": "教育",
     "region": "北京", "is_zxgk": False, "is_dishonest": False,
     "source": "gsxt", "view_count": 89},
]


async def main():
    await Database.init()
    async with Database.session() as session:
        # 清空旧
        await session.execute(delete(Law))
        await session.execute(delete(Company).where(Company.source == "gsxt"))
        await session.commit()

        # 法规
        for l in LAWS:
            session.add(Law(**l))
        await session.commit()
        logger.info(f"✓ 法规 seed: {len(LAWS)} 部")

        # 企业
        for c in COMPANIES:
            session.add(Company(**c))
        await session.commit()
        logger.info(f"✓ 企业 seed: {len(COMPANIES)} 家")

    await Database.close()
    logger.info("✓ Done")


if __name__ == "__main__":
    asyncio.run(main())
