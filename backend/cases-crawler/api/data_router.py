"""
LexPrime 数据管理 API 路由
提供数据批量导入、统计、清理和初始化示例数据的接口

端点:
- POST /api/data/import - 批量导入数据
- GET /api/data/stats - 数据统计
- POST /api/data/clean - 数据清理
- POST /api/data/seed - 初始化示例数据
- GET /api/data/health - 健康检查
"""
from __future__ import annotations

import random
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from loguru import logger
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from core.models import Case, Law, Company, Lawyer
from core.db import Database

router = APIRouter(prefix="/api/data", tags=["data"])


# ============================================================================
# Pydantic 模型
# ============================================================================

class DataImportItem(BaseModel):
    """数据导入项"""
    type: str = Field(..., description="数据类型: cases/laws/companies/lawyers")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="数据列表")


class DataImportRequest(BaseModel):
    """批量导入请求"""
    items: List[DataImportItem] = Field(default_factory=list, description="导入项列表")
    mode: str = Field("append", description="导入模式: append(追加)/replace(替换)")


class DataImportResponse(BaseModel):
    """数据导入响应"""
    success: bool = Field(True, description="是否成功")
    imported: Dict[str, int] = Field(default_factory=dict, description="各类型导入数量")
    failed: Dict[str, int] = Field(default_factory=dict, description="各类型失败数量")
    message: Optional[str] = Field(None, description="消息")


class DataStatsResponse(BaseModel):
    """数据统计响应"""
    total_cases: int = Field(0, description="判例总数")
    total_laws: int = Field(0, description="法规总数")
    total_companies: int = Field(0, description="企业总数")
    total_lawyers: int = Field(0, description="律师总数")
    case_by_category: Dict[str, int] = Field(default_factory=dict, description="按案由分类的案件数")
    case_by_year: Dict[str, int] = Field(default_factory=dict, description="按年份分类的案件数")
    law_by_type: Dict[str, int] = Field(default_factory=dict, description="按类型分类的法规数")
    company_by_industry: Dict[str, int] = Field(default_factory=dict, description="按行业分类的企业数")
    company_by_region: Dict[str, int] = Field(default_factory=dict, description="按地区分类的企业数")


class DataCleanRequest(BaseModel):
    """数据清理请求"""
    types: List[str] = Field(default_factory=list, description="要清理的数据类型，空表示全部")
    confirm: bool = Field(False, description="确认清理")


class DataCleanResponse(BaseModel):
    """数据清理响应"""
    success: bool = Field(True, description="是否成功")
    cleaned: Dict[str, int] = Field(default_factory=dict, description="各类型清理数量")
    message: Optional[str] = Field(None, description="消息")


class DataSeedRequest(BaseModel):
    """初始化示例数据请求"""
    cases_count: int = Field(100, ge=0, le=1000, description="判例数量")
    laws_count: int = Field(50, ge=0, le=500, description="法规数量")
    companies_count: int = Field(50, ge=0, le=500, description="企业数量")
    lawyers_count: int = Field(30, ge=0, le=200, description="律师数量")


class DataSeedResponse(BaseModel):
    """初始化示例数据响应"""
    success: bool = Field(True, description="是否成功")
    created: Dict[str, int] = Field(default_factory=dict, description="各类型创建数量")
    message: Optional[str] = Field(None, description="消息")


# ============================================================================
# 辅助函数 - 数据生成器
# ============================================================================

CASE_NAMES = [
    '借款合同纠纷案', '买卖合同纠纷案', '租赁合同纠纷案', '承揽合同纠纷案',
    '建设工程施工合同纠纷案', '物业服务合同纠纷案', '股权转让纠纷案',
    '劳动合同纠纷案', '交通事故责任纠纷案', '医疗损害责任纠纷案',
    '知识产权侵权纠纷案', '不正当竞争纠纷案', '公司决议效力确认纠纷案',
    '股东知情权纠纷案', '合伙协议纠纷案', '保险合同纠纷案'
]

COURTS = [
    '北京市第一中级人民法院', '北京市第二中级人民法院', '上海市第一中级人民法院',
    '上海市第二中级人民法院', '广州市中级人民法院', '深圳市中级人民法院',
    '杭州市中级人民法院', '南京市中级人民法院', '成都市中级人民法院',
    '北京市朝阳区人民法院', '上海市浦东新区人民法院', '广州市天河区人民法院'
]

CAUSES = [
    {'name': '借款合同纠纷', 'category': '合同纠纷', 'color': '#ef4444'},
    {'name': '买卖合同纠纷', 'category': '合同纠纷', 'color': '#f97316'},
    {'name': '租赁合同纠纷', 'category': '合同纠纷', 'color': '#eab308'},
    {'name': '承揽合同纠纷', 'category': '合同纠纷', 'color': '#22c55e'},
    {'name': '建设工程施工合同纠纷', 'category': '合同纠纷', 'color': '#14b8a6'},
    {'name': '股权转让纠纷', 'category': '与公司有关的纠纷', 'color': '#8b5cf6'},
    {'name': '劳动合同纠纷', 'category': '劳动争议', 'color': '#ec4899'},
    {'name': '交通事故责任纠纷', 'category': '侵权责任纠纷', 'color': '#f43f5e'},
    {'name': '医疗损害责任纠纷', 'category': '侵权责任纠纷', 'color': '#6366f1'}
]

LAW_TITLES = [
    {'title': '中华人民共和国民法典', 'type': '法律', 'level': 1},
    {'title': '中华人民共和国刑法', 'type': '法律', 'level': 1},
    {'title': '中华人民共和国民事诉讼法', 'type': '法律', 'level': 1},
    {'title': '中华人民共和国公司法', 'type': '法律', 'level': 1},
    {'title': '中华人民共和国劳动合同法', 'type': '法律', 'level': 1},
    {'title': '中华人民共和国保险法', 'type': '法律', 'level': 1},
    {'title': '中华人民共和国专利法', 'type': '法律', 'level': 1},
    {'title': '中华人民共和国商标法', 'type': '法律', 'level': 1},
    {'title': '中华人民共和国著作权法', 'type': '法律', 'level': 1},
    {'title': '中华人民共和国反不正当竞争法', 'type': '法律', 'level': 1}
]

COMPANY_NAMES = [
    '北京科技有限公司', '上海信息技术有限公司', '广州电子科技有限公司',
    '深圳软件开发有限公司', '杭州网络科技有限公司', '南京智能科技有限公司',
    '成都数据科技有限公司', '武汉云计算有限公司', '西安人工智能有限公司',
    '重庆区块链技术有限公司', '天津生物科技有限公司', '苏州新材料有限公司'
]

INDUSTRIES = [
    '软件和信息技术服务业', '互联网和相关服务', '计算机、通信和其他电子设备制造业',
    '医药制造业', '专业技术服务业', '商务服务业', '金融业', '房地产业',
    '建筑业', '批发和零售业'
]

REGIONS = [
    '北京市', '上海市', '广东省', '江苏省', '浙江省', '四川省', '湖北省',
    '山东省', '河南省', '福建省', '陕西省', '重庆市', '天津市', '辽宁省'
]

LAWYER_NAMES = [
    '张明', '李华', '王芳', '刘强', '陈静', '杨帆', '赵磊', '黄敏',
    '周涛', '吴婷', '徐鹏', '孙丽', '马超', '朱琳', '胡军', '郭燕'
]

SPECIALTIES = [
    '民商事诉讼', '刑事辩护', '公司法律事务', '知识产权', '劳动法',
    '房地产与建筑工程', '金融与银行', '婚姻家庭', '交通事故', '合同纠纷'
]


def _random_int(min_val: int, max_val: int) -> int:
    return random.randint(min_val, max_val)


def _random_date(start_year: int, end_year: int) -> date:
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return date(year, month, day)


def _generate_cases(count: int, start_index: int = 0) -> List[Case]:
    cases = []
    for i in range(count):
        cause = random.choice(CAUSES)
        year = random.randint(2018, 2025)
        idx = start_index + i
        cases.append(Case(
            doc_id=f"case-seed-{idx}",
            case_id=f"({year})京{random.randint(1, 5)}民初{1000 + idx}号",
            case_name=f"张三诉李四{random.choice(CASE_NAMES)}",
            court=random.choice(COURTS),
            cause=cause['name'],
            cause_category=cause['category'],
            cause_color=cause['color'],
            judgment_date=_random_date(2018, 2025),
            year=year,
            lex_score=_random_int(60, 95),
            view_count=_random_int(10, 500),
            favorite_count=_random_int(1, 50),
            parties='原告：张三；被告：李四',
            legal_basis='《民法典》第五百七十七条',
            full_text='原告张三与被告李四签订了借款合同...',
            source='seed_data',
            keywords=[cause['name'].replace('纠纷', ''), '合同', '违约']
        ))
    return cases


def _generate_laws(count: int, start_index: int = 0) -> List[Law]:
    laws = []
    for i in range(count):
        law_info = random.choice(LAW_TITLES)
        idx = start_index + i
        laws.append(Law(
            law_id=f"law-seed-{idx}",
            title=law_info['title'],
            law_type=law_info['type'],
            status='现行有效',
            issue_date=_random_date(1990, 2020),
            effective_date=_random_date(1991, 2021),
            level=law_info['level'],
            source='seed_data',
            summary=f"{law_info['title']}的简要说明...",
            full_text='第一章 总则\n\n第一条 为了规范...'
        ))
    return laws


def _generate_companies(count: int, start_index: int = 0) -> List[Company]:
    companies = []
    for i in range(count):
        idx = start_index + i
        base_name = random.choice(COMPANY_NAMES)
        companies.append(Company(
            unified_id=f"91{random.randint(100000, 999999)}MA01ABC{idx:03d}",
            company_name=base_name.replace('有限公司', '股份有限公司'),
            company_type='股份有限公司',
            legal_rep=random.choice(LAWYER_NAMES),
            registered_capital=f"{_random_int(100, 10000)}万元",
            paid_capital=f"{_random_int(50, 8000)}万元",
            establish_date=_random_date(2000, 2023),
            business_status=random.choice(['存续', '在业', '存续', '存续']),
            registered_address=f"{random.choice(REGIONS)}{random.choice(['朝阳区', '海淀区', '浦东新区', '天河区'])}{random.randint(1, 999)}号",
            business_scope='技术开发、技术咨询、技术服务、技术转让；软件开发；',
            industry=random.choice(INDUSTRIES),
            region=random.choice(REGIONS),
            is_zxgk=random.random() < 0.1,
            is_dishonest=random.random() < 0.05,
            source='seed_data',
            view_count=_random_int(5, 200)
        ))
    return companies


def _generate_lawyers(count: int, start_index: int = 0) -> List[Lawyer]:
    lawyers = []
    for i in range(count):
        idx = start_index + i
        name = random.choice(LAWYER_NAMES)
        spec_count = _random_int(1, 3)
        lawyer_specialties = []
        for _ in range(spec_count):
            spec = random.choice(SPECIALTIES)
            if spec not in lawyer_specialties:
                lawyer_specialties.append(spec)
        lawyers.append(Lawyer(
            id=f"lawyer-seed-{idx}",
            name=name,
            email=f"lawyer{idx}@example.com",
            phone=f"138{random.randint(10000000, 99999999)}",
            role=random.choice(['合伙人', '资深律师', '律师', '律师']),
            specialties=lawyer_specialties,
            firm_id='firm-seed-001',
            is_active=True,
            region=random.choice(REGIONS)
        ))
    return lawyers


# ============================================================================
# 端点
# ============================================================================

@router.get("/health", summary="健康检查", description="检查数据管理服务状态")
async def health():
    return {
        "status": "ok",
        "service": "data-management",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/import", response_model=DataImportResponse, summary="批量导入数据",
             description="批量导入判例、法规、企业、律师数据")
async def import_data(req: DataImportRequest):
    imported = {}
    failed = {}

    async with Database.session() as session:
        for item in req.items:
            data_type = item.type
            data_list = item.data
            imported[data_type] = 0
            failed[data_type] = 0

            try:
                if data_type == 'cases':
                    for data in data_list:
                        try:
                            case = Case(
                                doc_id=data.get('doc_id'),
                                case_id=data.get('case_id'),
                                case_name=data.get('case_name'),
                                court=data.get('court'),
                                cause=data.get('cause'),
                                cause_category=data.get('cause_category'),
                                cause_color=data.get('cause_color'),
                                judgment_date=date.fromisoformat(data['judgment_date']) if data.get('judgment_date') else None,
                                year=data.get('year'),
                                lex_score=data.get('lex_score'),
                                view_count=data.get('view_count', 0),
                                favorite_count=data.get('favorite_count', 0),
                                parties=data.get('parties'),
                                legal_basis=data.get('legal_basis'),
                                full_text=data.get('full_text'),
                                source=data.get('source', 'import'),
                                source_url=data.get('source_url'),
                                keywords=data.get('keywords')
                            )
                            session.add(case)
                            imported[data_type] += 1
                        except Exception as e:
                            logger.warning(f"导入判例失败: {e}")
                            failed[data_type] += 1

                elif data_type == 'laws':
                    for data in data_list:
                        try:
                            law = Law(
                                law_id=data.get('law_id', ''),
                                title=data.get('title', ''),
                                law_type=data.get('law_type', ''),
                                status=data.get('status'),
                                issue_date=date.fromisoformat(data['issue_date']) if data.get('issue_date') else None,
                                effective_date=date.fromisoformat(data['effective_date']) if data.get('effective_date') else None,
                                level=data.get('level'),
                                source=data.get('source', 'import'),
                                source_url=data.get('source_url'),
                                summary=data.get('summary'),
                                full_text=data.get('full_text')
                            )
                            session.add(law)
                            imported[data_type] += 1
                        except Exception as e:
                            logger.warning(f"导入法规失败: {e}")
                            failed[data_type] += 1

                elif data_type == 'companies':
                    for data in data_list:
                        try:
                            company = Company(
                                unified_id=data.get('unified_id', ''),
                                company_name=data.get('company_name', ''),
                                company_type=data.get('company_type'),
                                legal_rep=data.get('legal_rep'),
                                registered_capital=data.get('registered_capital'),
                                paid_capital=data.get('paid_capital'),
                                establish_date=date.fromisoformat(data['establish_date']) if data.get('establish_date') else None,
                                business_status=data.get('business_status'),
                                registered_address=data.get('registered_address'),
                                business_scope=data.get('business_scope'),
                                industry=data.get('industry'),
                                region=data.get('region'),
                                is_zxgk=data.get('is_zxgk', False),
                                is_dishonest=data.get('is_dishonest', False),
                                source=data.get('source', 'import'),
                                source_url=data.get('source_url'),
                                view_count=data.get('view_count', 0)
                            )
                            session.add(company)
                            imported[data_type] += 1
                        except Exception as e:
                            logger.warning(f"导入企业失败: {e}")
                            failed[data_type] += 1

                elif data_type == 'lawyers':
                    for data in data_list:
                        try:
                            lawyer = Lawyer(
                                id=data.get('id', ''),
                                name=data.get('name', ''),
                                email=data.get('email'),
                                phone=data.get('phone'),
                                role=data.get('role'),
                                specialties=data.get('specialties'),
                                firm_id=data.get('firm_id'),
                                is_active=data.get('is_active', True),
                                region=data.get('region')
                            )
                            session.add(lawyer)
                            imported[data_type] += 1
                        except Exception as e:
                            logger.warning(f"导入律师失败: {e}")
                            failed[data_type] += 1

                else:
                    failed[data_type] = len(data_list)
                    logger.warning(f"未知数据类型: {data_type}")

            except Exception as e:
                logger.error(f"导入 {data_type} 数据异常: {e}")

        await session.commit()

    return DataImportResponse(
        success=True,
        imported=imported,
        failed=failed,
        message="数据导入完成"
    )


@router.get("/stats", response_model=DataStatsResponse, summary="数据统计",
            description="获取各类数据的统计信息")
async def get_stats():
    async with Database.session() as session:
        total_cases = (await session.execute(select(func.count(Case.id)))).scalar() or 0
        total_laws = (await session.execute(select(func.count(Law.id)))).scalar() or 0
        total_companies = (await session.execute(select(func.count(Company.id)))).scalar() or 0
        total_lawyers = (await session.execute(select(func.count(Lawyer.id)))).scalar() or 0

        case_by_category = {}
        try:
            result = await session.execute(
                select(Case.cause_category, func.count(Case.id))
                .where(Case.cause_category.isnot(None))
                .group_by(Case.cause_category)
            )
            for row in result:
                case_by_category[row[0] or '未知'] = row[1]
        except Exception as e:
            logger.warning(f"获取案件分类统计失败: {e}")

        case_by_year = {}
        try:
            result = await session.execute(
                select(Case.year, func.count(Case.id))
                .where(Case.year.isnot(None))
                .group_by(Case.year)
                .order_by(Case.year)
            )
            for row in result:
                case_by_year[str(row[0])] = row[1]
        except Exception as e:
            logger.warning(f"获取案件年份统计失败: {e}")

        law_by_type = {}
        try:
            result = await session.execute(
                select(Law.law_type, func.count(Law.id))
                .group_by(Law.law_type)
            )
            for row in result:
                law_by_type[row[0] or '未知'] = row[1]
        except Exception as e:
            logger.warning(f"获取法规类型统计失败: {e}")

        company_by_industry = {}
        try:
            result = await session.execute(
                select(Company.industry, func.count(Company.id))
                .where(Company.industry.isnot(None))
                .group_by(Company.industry)
                .order_by(func.count(Company.id).desc())
                .limit(10)
            )
            for row in result:
                company_by_industry[row[0] or '未知'] = row[1]
        except Exception as e:
            logger.warning(f"获取企业行业统计失败: {e}")

        company_by_region = {}
        try:
            result = await session.execute(
                select(Company.region, func.count(Company.id))
                .where(Company.region.isnot(None))
                .group_by(Company.region)
                .order_by(func.count(Company.id).desc())
                .limit(10)
            )
            for row in result:
                company_by_region[row[0] or '未知'] = row[1]
        except Exception as e:
            logger.warning(f"获取企业地区统计失败: {e}")

    return DataStatsResponse(
        total_cases=total_cases,
        total_laws=total_laws,
        total_companies=total_companies,
        total_lawyers=total_lawyers,
        case_by_category=case_by_category,
        case_by_year=case_by_year,
        law_by_type=law_by_type,
        company_by_industry=company_by_industry,
        company_by_region=company_by_region
    )


@router.post("/clean", response_model=DataCleanResponse, summary="数据清理",
             description="清理指定类型的数据，需要确认操作")
async def clean_data(req: DataCleanRequest):
    if not req.confirm:
        return DataCleanResponse(
            success=False,
            cleaned={},
            message="需要确认清理操作，请设置 confirm=true"
        )

    cleaned = {}
    all_types = ['cases', 'laws', 'companies', 'lawyers']
    types_to_clean = req.types if req.types else all_types

    async with Database.session() as session:
        for data_type in types_to_clean:
            try:
                if data_type == 'cases':
                    result = await session.execute(select(Case))
                    cases = result.scalars().all()
                    for case in cases:
                        await session.delete(case)
                    cleaned[data_type] = len(cases)

                elif data_type == 'laws':
                    result = await session.execute(select(Law))
                    laws = result.scalars().all()
                    for law in laws:
                        await session.delete(law)
                    cleaned[data_type] = len(laws)

                elif data_type == 'companies':
                    result = await session.execute(select(Company))
                    companies = result.scalars().all()
                    for company in companies:
                        await session.delete(company)
                    cleaned[data_type] = len(companies)

                elif data_type == 'lawyers':
                    result = await session.execute(select(Lawyer))
                    lawyers = result.scalars().all()
                    for lawyer in lawyers:
                        await session.delete(lawyer)
                    cleaned[data_type] = len(lawyers)

                else:
                    cleaned[data_type] = 0
                    logger.warning(f"未知数据类型: {data_type}")

            except Exception as e:
                logger.error(f"清理 {data_type} 数据异常: {e}")
                cleaned[data_type] = 0

        await session.commit()

    return DataCleanResponse(
        success=True,
        cleaned=cleaned,
        message="数据清理完成"
    )


@router.post("/seed", response_model=DataSeedResponse, summary="初始化示例数据",
             description="生成并导入模拟的示例数据，用于演示和测试")
async def seed_data(req: DataSeedRequest):
    created = {}

    async with Database.session() as session:
        try:
            if req.cases_count > 0:
                cases = _generate_cases(req.cases_count)
                for case in cases:
                    session.add(case)
                created['cases'] = len(cases)
                logger.info(f"已生成 {len(cases)} 条判例数据")
        except Exception as e:
            logger.error(f"生成判例数据失败: {e}")
            created['cases'] = 0

        try:
            if req.laws_count > 0:
                laws = _generate_laws(req.laws_count)
                for law in laws:
                    session.add(law)
                created['laws'] = len(laws)
                logger.info(f"已生成 {len(laws)} 条法规数据")
        except Exception as e:
            logger.error(f"生成法规数据失败: {e}")
            created['laws'] = 0

        try:
            if req.companies_count > 0:
                companies = _generate_companies(req.companies_count)
                for company in companies:
                    session.add(company)
                created['companies'] = len(companies)
                logger.info(f"已生成 {len(companies)} 条企业数据")
        except Exception as e:
            logger.error(f"生成企业数据失败: {e}")
            created['companies'] = 0

        try:
            if req.lawyers_count > 0:
                lawyers = _generate_lawyers(req.lawyers_count)
                for lawyer in lawyers:
                    session.add(lawyer)
                created['lawyers'] = len(lawyers)
                logger.info(f"已生成 {len(lawyers)} 条律师数据")
        except Exception as e:
            logger.error(f"生成律师数据失败: {e}")
            created['lawyers'] = 0

        await session.commit()

    return DataSeedResponse(
        success=True,
        created=created,
        message="示例数据初始化完成"
    )
