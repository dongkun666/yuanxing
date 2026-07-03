"""
LexPrime 智能合同生成 API
==========================

基于需求描述智能匹配和生成合同模板，支持多种合同类型。

端点:
- POST /api/contract/generate    生成合同
- GET  /api/contract/templates   模板列表
- GET  /api/contract/health      健康检查

支持 mock 模式: 返回模拟合同数据
"""
from __future__ import annotations

import time
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/contract", tags=["contract-gen"])

MOCK_MODE = True

DISCLAIMER_FULL = (
    "LexPrime 智能合同生成基于模板规则引擎，生成的合同文本仅供参考，"
    "不构成正式法律文件。请根据实际情况进行调整和审核，"
    "建议由专业律师进行审查后使用。"
)


# ========== Request / Response Models ==========

class ContractTemplate(BaseModel):
    """合同模板"""
    id: str
    name: str
    category: str
    description: str
    icon: Optional[str] = None
    complexity: str = "medium"


class ContractGenerateRequest(BaseModel):
    """合同生成请求"""
    template_id: Optional[str] = None
    contract_type: Optional[str] = None
    description: str = Field(..., min_length=1, max_length=5000)
    parties: Optional[List[Dict[str, str]]] = None
    key_terms: Optional[Dict[str, Any]] = None
    options: Optional[Dict[str, bool]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "contract_type": "房屋租赁合同",
                "description": "甲方将位于北京市朝阳区的一套两居室房屋出租给乙方，租期1年，月租金5000元...",
                "parties": [
                    {"name": "张三", "role": "出租方", "id_card": "110101199001011234"},
                    {"name": "李四", "role": "承租方", "id_card": "110102199002025678"}
                ],
                "key_terms": {
                    "rent_amount": "5000元/月",
                    "lease_term": "1年",
                    "deposit": "10000元"
                }
            }
        }


class ContractClause(BaseModel):
    """合同条款"""
    title: str
    content: str
    level: int = 1


class ContractGenerateResponse(BaseModel):
    """合同生成响应"""
    contract_id: str
    title: str
    contract_type: str
    clauses: List[ContractClause]
    full_text: str
    template_used: str
    warnings: List[str]
    disclaimer: str


class TemplatesResponse(BaseModel):
    """模板列表响应"""
    templates: List[ContractTemplate]
    categories: List[str]
    total: int


# ========== Mock Data ==========

MOCK_TEMPLATES = [
    {
        "id": "tpl-rent-house",
        "name": "房屋租赁合同",
        "category": "租赁类",
        "description": "适用于住宅、商业用房的租赁协议",
        "icon": "mdi:home",
        "complexity": "low"
    },
    {
        "id": "tpl-sales-goods",
        "name": "货物买卖合同",
        "category": "买卖类",
        "description": "适用于一般货物买卖交易",
        "icon": "mdi:cart-outline",
        "complexity": "medium"
    },
    {
        "id": "tpl-labor",
        "name": "劳动合同",
        "category": "劳动类",
        "description": "适用于全日制劳动合同签订",
        "icon": "mdi:briefcase-outline",
        "complexity": "medium"
    },
    {
        "id": "tpl-loan",
        "name": "借款合同",
        "category": "借贷类",
        "description": "适用于民间借贷、企业拆借",
        "icon": "mdi:currency-cny",
        "complexity": "low"
    },
    {
        "id": "tpl-service",
        "name": "服务合同",
        "category": "服务类",
        "description": "适用于各类专业服务提供",
        "icon": "mdi:account-tie-outline",
        "complexity": "medium"
    },
    {
        "id": "tpl-agency",
        "name": "委托代理合同",
        "category": "代理类",
        "description": "适用于委托代理事务处理",
        "icon": "mdi:account-group-outline",
        "complexity": "medium"
    },
    {
        "id": "tpl-partnership",
        "name": "合伙协议",
        "category": "合伙类",
        "description": "适用于合伙企业设立与运营",
        "icon": "mdi:handshake-outline",
        "complexity": "high"
    },
    {
        "id": "tpl-nda",
        "name": "保密协议",
        "category": "保密类",
        "description": "适用于商业秘密保护约定",
        "icon": "mdi:lock-outline",
        "complexity": "low"
    },
    {
        "id": "tpl-technology-transfer",
        "name": "技术转让合同",
        "category": "知识产权类",
        "description": "适用于专利、技术秘密等转让",
        "icon": "mdi:atom-variant",
        "complexity": "high"
    },
    {
        "id": "tpl-equity-transfer",
        "name": "股权转让协议",
        "category": "投资类",
        "description": "适用于公司股权转让交易",
        "icon": "mdi:chart-line",
        "complexity": "high"
    }
]


def generate_mock_contract(req: ContractGenerateRequest) -> Dict[str, Any]:
    """生成 mock 合同"""
    desc = (req.description or "").lower()
    contract_type = req.contract_type or req.template_id or "通用合同"

    if any(kw in desc for kw in ["租赁", "租房", "房屋", "商铺"]) or "租赁" in contract_type:
        title = "房屋租赁合同"
        contract_type = "房屋租赁合同"
        clauses = [
            {"title": "第一条 合同当事人", "content": "出租方（以下简称甲方）：__________\n身份证号：__________\n联系地址：__________\n联系电话：__________\n\n承租方（以下简称乙方）：__________\n身份证号：__________\n联系地址：__________\n联系电话：__________", "level": 1},
            {"title": "第二条 租赁房屋", "content": "1. 甲方将其合法拥有的坐落于__________的房屋（以下简称\"该房屋\"）出租给乙方使用。\n2. 该房屋建筑面积约__________平方米，房屋用途为__________。\n3. 甲方保证对该房屋享有合法出租权，且房屋不存在任何权利瑕疵。", "level": 1},
            {"title": "第三条 租赁期限", "content": "1. 租赁期限自____年__月__日起至____年__月__日止，共计__个月。\n2. 租赁期满，甲方有权收回该房屋，乙方应如期交还。乙方如要求续租，则必须在租赁期满前__日书面通知甲方，经甲方同意后，重新签订租赁合同。", "level": 1},
            {"title": "第四条 租金及支付方式", "content": "1. 该房屋月租金为人民币__________元（大写：__________元整）。\n2. 租金支付方式：按□月/□季/□半年/□年支付，乙方应在每__期初的__日内将当期租金支付给甲方。\n3. 首次租金应于本合同签订之日起__日内支付。\n4. 租金支付方式：□现金 □银行转账 □其他__________", "level": 1},
            {"title": "第五条 押金", "content": "1. 乙方应于本合同签订之日向甲方支付押金人民币__________元（大写：__________元整）。\n2. 租赁期满或合同解除后，押金除抵扣应由乙方承担的费用、租金以及乙方应承担的违约赔偿责任外，剩余部分应如数返还乙方。\n3. 押金不计利息。", "level": 1},
            {"title": "第六条 相关费用", "content": "租赁期间，因使用该房屋所产生的下列费用由乙方承担：\n1. 水费、电费；\n2. 燃气费、供暖费；\n3. 物业管理费；\n4. 网络、有线电视费；\n5. 其他：__________", "level": 1},
            {"title": "第七条 房屋使用及维护", "content": "1. 乙方应合理使用并爱护该房屋及其附属设施。因乙方使用不当或不合理使用，致使该房屋及其附属设施损坏或发生故障的，乙方应负责维修或承担赔偿责任。\n2. 乙方不得擅自改变房屋结构，不得擅自拆改、变动房屋内部设施。\n3. 甲方有权在提前通知乙方的情况下，进入该房屋进行检查或维修。", "level": 1},
            {"title": "第八条 合同的解除", "content": "1. 经甲乙双方协商一致，可以解除本合同。\n2. 乙方有下列情形之一的，甲方有权单方解除合同，收回该房屋：\n（1）不支付或者不按照约定支付租金达__日以上的；\n（2）欠缴各项费用达__________元以上的；\n（3）擅自改变该房屋用途的；\n（4）擅自拆改变动或损坏房屋主体结构的；\n（5）利用该房屋从事违法活动的。", "level": 1},
            {"title": "第九条 违约责任", "content": "1. 乙方逾期支付租金的，每逾期一日，应按日租金的__%向甲方支付违约金。\n2. 租赁期内，甲方需提前收回该房屋的，或乙方需提前退租的，应提前__日通知对方，并按月租金的__%向对方支付违约金。\n3. 因乙方原因造成房屋损坏的，乙方应赔偿因此给甲方造成的全部损失。", "level": 1},
            {"title": "第十条 争议解决", "content": "本合同项下发生的争议，由双方协商解决；协商不成的，依法向该房屋所在地人民法院起诉。", "level": 1},
            {"title": "第十一条 其他约定事项", "content": "1. 本合同未尽事宜，双方可另行签订补充协议。补充协议与本合同具有同等法律效力。\n2. 本合同一式两份，甲乙双方各执一份，自双方签字（或盖章）之日起生效。\n\n补充条款：\n__________", "level": 1}
        ]
        warnings = [
            "建议核实房屋产权证明，确保甲方享有合法出租权",
            "建议明确约定押金返还的具体条件和时间",
            "建议在合同中详细列明房屋附属设施清单"
        ]
        template_used = "tpl-rent-house"
    elif any(kw in desc for kw in ["买卖", "销售", "货物", "采购"]) or "买卖" in contract_type:
        title = "货物买卖合同"
        contract_type = "货物买卖合同"
        clauses = [
            {"title": "第一条 合同双方", "content": "卖方（以下简称甲方）：__________\n法定代表人：__________\n地址：__________\n联系电话：__________\n\n买方（以下简称乙方）：__________\n法定代表人：__________\n地址：__________\n联系电话：__________", "level": 1},
            {"title": "第二条 合同标的", "content": "1. 甲方向乙方供应以下货物：\n\n| 序号 | 货物名称 | 规格型号 | 单位 | 数量 | 单价（元） | 金额（元） |\n|------|----------|----------|------|------|-----------|-----------|\n| 1    |          |          |      |      |           |           |\n| 2    |          |          |      |      |           |           |\n\n2. 货物总价款：人民币__________元（大写：__________元整）。\n3. 货物质量标准：按□国家标准 □行业标准 □双方约定标准执行。", "level": 1},
            {"title": "第三条 交货方式及期限", "content": "1. 交货方式：□送货上门 □自提 □代办托运\n2. 交货地点：__________\n3. 交货时间：____年__月__日前\n4. 运输方式：__________\n5. 运费承担：□甲方承担 □乙方承担 □双方各承担__%", "level": 1},
            {"title": "第四条 价款结算与支付", "content": "1. 付款方式：□一次性付款 □分期付款 □其他__________\n2. 付款时间：__________\n3. 付款方式：□银行转账 □承兑汇票 □现金 □其他__________\n4. 甲方应在收款后__日内向乙方开具相应金额的增值税□专用/□普通发票。", "level": 1},
            {"title": "第五条 验收标准与方法", "content": "1. 乙方应在收到货物后__日内进行验收。\n2. 验收标准：以本合同约定的质量标准和技术要求为准。\n3. 如发现货物数量、质量不符合约定，乙方应在验收后__日内向甲方提出书面异议。甲方应在收到异议后__日内作出答复。", "level": 1},
            {"title": "第六条 质量保证", "content": "1. 甲方保证所供货物符合本合同约定的质量标准，是全新的、未使用过的。\n2. 质保期：__个月，自货物验收合格之日起计算。\n3. 质保期内，如因货物质量问题发生故障，甲方应在接到乙方通知后__小时内予以响应，__小时内到达现场处理。", "level": 1},
            {"title": "第七条 违约责任", "content": "1. 甲方逾期交货的，每逾期一日，应按逾期交货部分货款的__%向乙方支付违约金。\n2. 乙方逾期付款的，每逾期一日，应按逾期付款金额的__%向甲方支付违约金。\n3. 甲方所交货物质量不符合约定的，乙方有权要求甲方更换、退货或减少价款。", "level": 1},
            {"title": "第八条 争议解决", "content": "因本合同引起的或与本合同有关的任何争议，双方应友好协商解决；协商不成的，按下列第__种方式解决：\n（1）向__________仲裁委员会申请仲裁；\n（2）向甲方所在地人民法院起诉；\n（3）向乙方所在地人民法院起诉。", "level": 1},
            {"title": "第九条 其他", "content": "1. 本合同自双方签字（或盖章）之日起生效。\n2. 本合同一式__份，甲乙双方各执__份，具有同等法律效力。\n3. 本合同未尽事宜，双方可另行签订补充协议。补充协议与本合同具有同等法律效力。", "level": 1}
        ]
        warnings = [
            "建议详细列明货物清单，包括规格、型号、数量等",
            "建议明确约定验收标准和异议期限",
            "建议根据实际情况调整违约金比例"
        ]
        template_used = "tpl-sales-goods"
    elif any(kw in desc for kw in ["借款", "借贷", "贷款"]) or "借款" in contract_type:
        title = "借款合同"
        contract_type = "借款合同"
        clauses = [
            {"title": "第一条 出借人与借款人", "content": "出借人（以下简称甲方）：__________\n身份证号：__________\n联系地址：__________\n联系电话：__________\n\n借款人（以下简称乙方）：__________\n身份证号：__________\n联系地址：__________\n联系电话：__________", "level": 1},
            {"title": "第二条 借款金额", "content": "甲方向乙方出借人民币（大写）__________元整（小写：¥__________元）。", "level": 1},
            {"title": "第三条 借款用途", "content": "乙方借款用于：__________。乙方不得将借款用于违法活动，不得擅自改变借款用途。", "level": 1},
            {"title": "第四条 借款期限", "content": "借款期限自____年__月__日起至____年__月__日止，共计__个月。", "level": 1},
            {"title": "第五条 借款利率及利息支付", "content": "1. 借款利率：年利率为__%（不超过合同成立时一年期贷款市场报价利率四倍）。\n2. 利息支付方式：□按月支付 □按季支付 □到期一次性还本付息\n3. 利息支付时间：__________\n4. 计算公式：利息 = 本金 × 年利率 × 实际借款天数 / 365", "level": 1},
            {"title": "第六条 还款方式", "content": "1. 还款方式：□到期一次性还本付息 □等额本息 □等额本金 □先息后本\n2. 还款账户：__________\n开户行：__________\n户名：__________\n账号：__________", "level": 1},
            {"title": "第七条 借款担保", "content": "（可选）为确保本合同的履行，乙方提供以下担保方式：\n□ 保证担保：保证人__________同意为乙方的债务承担连带责任保证。\n□ 抵押担保：乙方以其所有的__________提供抵押担保。\n□ 质押担保：乙方以其所有的__________提供质押担保。\n□ 无担保", "level": 1},
            {"title": "第八条 违约责任", "content": "1. 乙方逾期还款的，每逾期一日，应按逾期金额的__‰向甲方支付逾期违约金。\n2. 乙方未按约定用途使用借款的，甲方有权提前收回借款，并要求乙方支付违约金人民币__________元。\n3. 乙方有下列情形之一的，甲方有权解除合同，提前收回借款：\n（1）向甲方提供虚假情况或隐瞒重要事实；\n（2）转移财产、抽逃资金以逃避债务；\n（3）经营状况严重恶化；\n（4）丧失商业信誉。", "level": 1},
            {"title": "第九条 争议解决", "content": "因本合同引起的或与本合同有关的任何争议，双方应友好协商解决；协商不成的，依法向甲方所在地人民法院起诉。", "level": 1},
            {"title": "第十条 其他", "content": "1. 本合同自双方签字（或盖章）之日起生效。\n2. 本合同一式两份，甲乙双方各执一份，具有同等法律效力。\n3. 本合同未尽事宜，双方可另行签订补充协议。", "level": 1}
        ]
        warnings = [
            "请注意借款利率不得超过法定上限（LPR四倍）",
            "建议保留转账凭证，避免现金交付",
            "大额借款建议要求提供担保"
        ]
        template_used = "tpl-loan"
    else:
        title = "协议书"
        contract_type = "通用合同"
        clauses = [
            {"title": "第一条 协议双方", "content": "甲方：__________\n法定代表人/负责人：__________\n地址：__________\n联系电话：__________\n\n乙方：__________\n法定代表人/负责人：__________\n地址：__________\n联系电话：__________", "level": 1},
            {"title": "第二条 合作内容", "content": "甲乙双方经友好协商，就__________事宜达成如下协议：\n\n1. __________\n2. __________\n3. __________", "level": 1},
            {"title": "第三条 双方权利与义务", "content": "（一）甲方权利与义务：\n1. __________\n2. __________\n3. __________\n\n（二）乙方权利与义务：\n1. __________\n2. __________\n3. __________", "level": 1},
            {"title": "第四条 价款与支付", "content": "1. 本协议项下总费用为人民币__________元（大写：__________元整）。\n2. 支付方式：__________\n3. 支付时间：__________", "level": 1},
            {"title": "第五条 履行期限", "content": "本协议履行期限自____年__月__日起至____年__月__日止。", "level": 1},
            {"title": "第六条 保密条款", "content": "1. 双方对在履行本协议过程中知悉的对方商业秘密及其他保密信息负有保密义务。\n2. 未经对方书面同意，任何一方不得向第三方披露任何保密信息。\n3. 保密义务在本协议终止后__年内仍然有效。", "level": 1},
            {"title": "第七条 违约责任", "content": "1. 任何一方违反本协议约定，应向对方支付违约金人民币__________元。\n2. 因一方违约给对方造成损失的，违约方应承担相应的赔偿责任。", "level": 1},
            {"title": "第八条 不可抗力", "content": "1. 因不可抗力导致本协议不能履行或不能完全履行的，遭遇不可抗力一方不承担违约责任。\n2. 遭遇不可抗力一方应及时通知对方，并在合理期限内提供证明。", "level": 1},
            {"title": "第九条 争议解决", "content": "因本协议引起的或与本协议有关的任何争议，双方应友好协商解决；协商不成的，按下列第__种方式解决：\n（1）向__________仲裁委员会申请仲裁；\n（2）向__________人民法院起诉。", "level": 1},
            {"title": "第十条 其他", "content": "1. 本协议自双方签字（或盖章）之日起生效。\n2. 本协议一式__份，甲乙双方各执__份，具有同等法律效力。\n3. 本协议未尽事宜，双方可另行签订补充协议。补充协议与本协议具有同等法律效力。", "level": 1}
        ]
        warnings = [
            "本合同为通用模板，建议根据具体业务需求进行调整",
            "建议明确约定违约责任的具体计算方式",
            "建议由专业律师进行审核"
        ]
        template_used = "tpl-general"

    full_text = title + "\n\n"
    for clause in clauses:
        full_text += clause["title"] + "\n\n" + clause["content"] + "\n\n"

    return {
        "contract_id": f"contract-{int(time.time())}",
        "title": title,
        "contract_type": contract_type,
        "clauses": clauses,
        "full_text": full_text,
        "template_used": template_used,
        "warnings": warnings
    }


# ========== 端点 ==========

@router.get("/health")
async def contract_health():
    """智能合同生成服务健康检查"""
    return {
        "status": "ok",
        "service": "lexprime-contract-gen",
        "version": "1.0.0",
        "mock_mode": MOCK_MODE,
        "features": [
            "smart_template_matching",
            "contract_generation",
            "clause_customization",
            "risk_warning",
            "multi_format_export"
        ],
        "supported_types": [
            "房屋租赁合同",
            "货物买卖合同",
            "劳动合同",
            "借款合同",
            "服务合同",
            "保密协议",
            "合伙协议",
            "股权转让协议"
        ],
        "endpoints": [
            {"path": "/api/contract/generate", "method": "POST", "purpose": "生成合同"},
            {"path": "/api/contract/templates", "method": "GET", "purpose": "模板列表"}
        ]
    }


@router.get("/templates", response_model=TemplatesResponse)
async def get_templates(
    category: Optional[str] = Query(None, description="分类筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索")
):
    """获取合同模板列表"""
    try:
        templates = [ContractTemplate(**t) for t in MOCK_TEMPLATES]

        if category:
            templates = [t for t in templates if t.category == category]

        if keyword:
            kw = keyword.lower()
            templates = [t for t in templates if kw in t.name.lower() or kw in t.description.lower()]

        categories = list(set(t["category"] for t in MOCK_TEMPLATES))

        return TemplatesResponse(
            templates=templates,
            categories=categories,
            total=len(templates)
        )
    except Exception as e:
        logger.exception(f"Get templates failed: {e}")
        raise HTTPException(500, f"获取模板列表失败: {str(e)}")


@router.post("/generate", response_model=ContractGenerateResponse)
async def generate_contract(req: ContractGenerateRequest):
    """生成合同接口

    输入: 合同类型、需求描述、当事人信息、关键条款
    输出: 完整合同文本、条款列表、使用模板、风险提示
    """
    t0 = time.time()

    try:
        result = generate_mock_contract(req)

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"Contract generation processed in {latency_ms}ms, "
            f"type={result['contract_type']}, "
            f"clauses={len(result['clauses'])}, "
            f"mock_mode={MOCK_MODE}"
        )

        return ContractGenerateResponse(
            contract_id=result["contract_id"],
            title=result["title"],
            contract_type=result["contract_type"],
            clauses=[ContractClause(**c) for c in result["clauses"]],
            full_text=result["full_text"],
            template_used=result["template_used"],
            warnings=result["warnings"],
            disclaimer=DISCLAIMER_FULL
        )
    except Exception as e:
        logger.exception(f"Contract generation failed: {e}")
        raise HTTPException(500, f"合同生成服务异常: {str(e)}")
