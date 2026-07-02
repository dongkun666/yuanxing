"""
LexPrime 客户管理 API (FastAPI 路由)
2026-07-02 · W31 phase6-clients-backend

端点:
- GET    /api/clients                            客户列表 (分页 / 搜索 / 类型过滤 / 等级过滤)
- GET    /api/clients/{client_id}                客户详情
- POST   /api/clients                            创建客户
- PUT    /api/clients/{client_id}                更新客户
- DELETE /api/clients/{client_id}                删除客户
- POST   /api/clients/{client_id}/conflict-check 利益冲突检查
- GET    /api/clients/stats                      客户统计 (总数 / 类型分布 / 等级分布)
- GET    /api/clients/health                     健康检查

支持 mock 模式: 当数据库不可用时返回模拟数据, 确保前端可联调 (参考 ai_router.py)
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import select, func, or_

from core.models import Base, Client


router = APIRouter(prefix="/api/clients", tags=["clients"])


# ========== 强制免责声明 ==========

DISCLAIMER = (
    "LexPrime 客户管理模块用于律所内部客户主档维护, "
    "利益冲突检索基于名称精确/模糊匹配, 不构成正式法律意见, "
    "不替代律师专业判断。具体案件冲突审查需结合实际情况、当事人范围及司法裁判进行评估。"
)

MOCK_MODE = True


# ========== Pydantic Request / Response Models ==========

class ClientBase(BaseModel):
    """客户基础字段"""
    name: str = Field(..., min_length=1, max_length=256, description="客户名称 (个人姓名 / 企业名称)")
    client_type: str = Field("personal", pattern="^(personal|enterprise)$", description="客户类型")
    id_number: Optional[str] = Field(None, max_length=64, description="身份证号 / 统一社会信用代码")
    phone: Optional[str] = Field(None, max_length=32, description="联系电话")
    email: Optional[str] = Field(None, max_length=128, description="邮箱")
    address: Optional[str] = Field(None, max_length=512, description="地址")
    grade: str = Field("C", pattern="^[A-D]$", description="客户分级 (A / B / C / D)")
    notes: Optional[str] = Field(None, description="备注")


class ClientCreateRequest(ClientBase):
    """创建客户请求"""
    firm_id: Optional[str] = Field(None, max_length=64, description="律所 ID")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "李明",
                "client_type": "personal",
                "id_number": "110101199001011234",
                "phone": "13800001234",
                "email": "liming@example.com",
                "address": "北京市海淀区中关村大街 1 号",
                "grade": "A",
                "firm_id": "firm-001",
                "notes": "重点客户, 借款合同纠纷"
            }
        }


class ClientUpdateRequest(ClientBase):
    """更新客户请求 (所有字段可选)"""
    name: Optional[str] = Field(None, min_length=1, max_length=256)
    client_type: Optional[str] = Field(None, pattern="^(personal|enterprise)$")
    grade: Optional[str] = Field(None, pattern="^[A-D]$")


class ClientResponse(BaseModel):
    """客户响应"""
    id: int
    client_id: str
    firm_id: Optional[str] = None
    name: str
    client_type: str
    id_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    grade: str
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class ClientListResponse(BaseModel):
    """客户列表响应"""
    items: List[ClientResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    mock_mode: bool = False


class ConflictCheckResponse(BaseModel):
    """利益冲突检查响应"""
    client_id: str
    name: str
    has_conflict: bool
    conflicts: List[Dict[str, Any]]
    risk_level: str  # none / low / medium / high
    disclaimer: str


class ClientStatsResponse(BaseModel):
    """客户统计响应"""
    total: int
    by_type: Dict[str, int]
    by_grade: Dict[str, int]
    mock_mode: bool = False
    disclaimer: str


# ========== Mock 数据 (与前端 clients.js / client.html 5 条 mock 对齐) ==========

def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


_MOCK_CLIENTS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "client_id": "CL-001",
        "firm_id": "firm-001",
        "name": "李明",
        "client_type": "personal",
        "id_number": "110101199001011234",
        "phone": "138****1234",
        "email": "liming@example.com",
        "address": "北京市海淀区中关村大街 1 号",
        "grade": "A",
        "notes": "重点客户, 借款合同纠纷",
        "status": "active",
        "cases": 3,
        "created_at": "2026-08-18T10:00:00Z",
        "updated_at": "2026-08-18T10:00:00Z",
    },
    {
        "id": 2,
        "client_id": "CL-002",
        "firm_id": "firm-001",
        "name": "王华",
        "client_type": "personal",
        "id_number": "110102198805056789",
        "phone": "139****5678",
        "email": "wanghua@example.com",
        "address": "北京市朝阳区建国路 88 号",
        "grade": "B",
        "notes": "借贷纠纷案客户",
        "status": "active",
        "cases": 2,
        "created_at": "2026-08-15T10:00:00Z",
        "updated_at": "2026-08-15T10:00:00Z",
    },
    {
        "id": 3,
        "client_id": "CL-003",
        "firm_id": "firm-001",
        "name": "某科技有限公司",
        "client_type": "enterprise",
        "id_number": "91110108MA01ABCDEF",
        "phone": "010-8888****",
        "email": "contact@tech-co.com",
        "address": "北京市海淀区上地十街 10 号",
        "grade": "A",
        "notes": "企业常年法律顾问",
        "status": "active",
        "cases": 5,
        "created_at": "2026-08-14T10:00:00Z",
        "updated_at": "2026-08-14T10:00:00Z",
    },
    {
        "id": 4,
        "client_id": "CL-004",
        "firm_id": "firm-001",
        "name": "赵六",
        "client_type": "personal",
        "id_number": "110103199209090123",
        "phone": "136****9012",
        "email": "zhaoliu@example.com",
        "address": "北京市西城区西直门大街 5 号",
        "grade": "C",
        "notes": "劳动争议案结案后待回访",
        "status": "pending",
        "cases": 1,
        "created_at": "2026-08-05T10:00:00Z",
        "updated_at": "2026-08-05T10:00:00Z",
    },
    {
        "id": 5,
        "client_id": "CL-005",
        "firm_id": "firm-001",
        "name": "张三",
        "client_type": "personal",
        "id_number": "110104199503033456",
        "phone": "137****3456",
        "email": "zhangsan@example.com",
        "address": "北京市东城区东直门大街 3 号",
        "grade": "C",
        "notes": "静默客户",
        "status": "inactive",
        "cases": 1,
        "created_at": "2026-07-28T10:00:00Z",
        "updated_at": "2026-07-28T10:00:00Z",
    },
]


def _mock_client_response(c: Dict[str, Any]) -> ClientResponse:
    """从 mock dict 构造 ClientResponse"""
    return ClientResponse(
        id=c["id"],
        client_id=c["client_id"],
        firm_id=c.get("firm_id"),
        name=c["name"],
        client_type=c["client_type"],
        id_number=c.get("id_number"),
        phone=c.get("phone"),
        email=c.get("email"),
        address=c.get("address"),
        grade=c["grade"],
        notes=c.get("notes"),
        created_at=c.get("created_at", _now_iso()),
        updated_at=c.get("updated_at", _now_iso()),
    )


def _row_to_response(row: Client) -> ClientResponse:
    """从 ORM 行构造 ClientResponse"""
    return ClientResponse(
        id=row.id,
        client_id=row.client_id,
        firm_id=row.firm_id,
        name=row.name,
        client_type=row.client_type,
        id_number=row.id_number,
        phone=row.phone,
        email=row.email,
        address=row.address,
        grade=row.grade,
        notes=row.notes,
        created_at=row.created_at.isoformat() if row.created_at else "",
        updated_at=row.updated_at.isoformat() if row.updated_at else "",
    )


def _gen_client_id() -> str:
    """生成 client_id: CL-<uuid8>"""
    return "CL-" + uuid.uuid4().hex[:8].upper()


def _db_session():
    """获取 Database session 上下文 (惰性 import, 失败抛异常由调用方兜底)"""
    from core.db import Database
    return Database.session()


# ========== 端点 ==========

@router.get("/health")
async def clients_health():
    """客户管理服务健康检查"""
    return {
        "status": "ok",
        "service": "lexprime-clients",
        "version": "1.0.0-w31",
        "mock_mode": MOCK_MODE,
        "endpoints": [
            {"path": "/api/clients", "method": "GET", "purpose": "客户列表 (分页 / 搜索 / 过滤)"},
            {"path": "/api/clients/{client_id}", "method": "GET", "purpose": "客户详情"},
            {"path": "/api/clients", "method": "POST", "purpose": "创建客户"},
            {"path": "/api/clients/{client_id}", "method": "PUT", "purpose": "更新客户"},
            {"path": "/api/clients/{client_id}", "method": "DELETE", "purpose": "删除客户"},
            {"path": "/api/clients/{client_id}/conflict-check", "method": "POST", "purpose": "利益冲突检查"},
            {"path": "/api/clients/stats", "method": "GET", "purpose": "客户统计"},
        ],
    }


@router.get("/stats", response_model=ClientStatsResponse)
async def get_client_stats(
    firm_id: Optional[str] = Query(None, description="按律所过滤"),
):
    """客户统计 (总数 / 类型分布 / 等级分布)

    mock 模式下基于内置 5 条 mock 数据计算。
    """
    t0 = time.time()
    mock_mode_flag = False

    by_type: Dict[str, int] = {"personal": 0, "enterprise": 0}
    by_grade: Dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0}
    total = 0

    try:
        async with _db_session() as session:
            stmt = select(Client)
            if firm_id:
                stmt = stmt.where(Client.firm_id == firm_id)
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = (await session.execute(count_stmt)).scalar() or 0

            if total > 0:
                # 类型分布
                type_base = select(Client.client_type, func.count())
                if firm_id:
                    type_base = type_base.where(Client.firm_id == firm_id)
                type_result = await session.execute(type_base.group_by(Client.client_type))
                for t, c in type_result.all():
                    by_type[t] = c

                # 等级分布
                grade_base = select(Client.grade, func.count())
                if firm_id:
                    grade_base = grade_base.where(Client.firm_id == firm_id)
                grade_result = await session.execute(grade_base.group_by(Client.grade))
                for g, c in grade_result.all():
                    if g in by_grade:
                        by_grade[g] = c
    except Exception as e:
        logger.warning(f"[clients] stats DB 查询失败, 回退 mock: {e}")
        mock_mode_flag = True

    if mock_mode_flag or total == 0:
        # 回退 mock 统计
        mock_pool = [c for c in _MOCK_CLIENTS if (not firm_id) or c.get("firm_id") == firm_id]
        total = len(mock_pool)
        by_type = {"personal": 0, "enterprise": 0}
        by_grade = {"A": 0, "B": 0, "C": 0, "D": 0}
        for c in mock_pool:
            by_type[c["client_type"]] = by_type.get(c["client_type"], 0) + 1
            by_grade[c["grade"]] = by_grade.get(c["grade"], 0) + 1
        mock_mode_flag = True

    latency_ms = int((time.time() - t0) * 1000)
    logger.info(f"[clients] stats total={total} latency={latency_ms}ms mock={mock_mode_flag}")

    return ClientStatsResponse(
        total=total,
        by_type=by_type,
        by_grade=by_grade,
        mock_mode=mock_mode_flag,
        disclaimer=DISCLAIMER,
    )


@router.get("/", response_model=ClientListResponse)
async def list_clients(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词 (名称 / 电话 / 邮箱 / 证件号)"),
    client_type: Optional[str] = Query(None, pattern="^(personal|enterprise)$", description="客户类型过滤"),
    grade: Optional[str] = Query(None, pattern="^[A-D]$", description="客户等级过滤"),
    firm_id: Optional[str] = Query(None, description="律所 ID 过滤"),
):
    """客户列表 (支持分页 / 搜索 / 类型过滤 / 等级过滤)

    DB 不可用时回退 mock 数据。
    """
    t0 = time.time()

    try:
        async with _db_session() as session:
            stmt = select(Client)
            if firm_id:
                stmt = stmt.where(Client.firm_id == firm_id)
            if client_type:
                stmt = stmt.where(Client.client_type == client_type)
            if grade:
                stmt = stmt.where(Client.grade == grade.upper())
            if search:
                kw = f"%{search}%"
                stmt = stmt.where(
                    or_(
                        Client.name.ilike(kw),
                        Client.phone.ilike(kw),
                        Client.email.ilike(kw),
                        Client.id_number.ilike(kw),
                    )
                )

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = (await session.execute(count_stmt)).scalar() or 0

            offset = (page - 1) * page_size
            stmt = stmt.order_by(Client.created_at.desc()).offset(offset).limit(page_size)
            result = await session.execute(stmt)
            rows = list(result.scalars().all())

            items = [_row_to_response(r) for r in rows]
            total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

            latency_ms = int((time.time() - t0) * 1000)
            logger.info(
                f"[clients] list page={page} size={page_size} total={total} "
                f"search={search} latency={latency_ms}ms mock=False"
            )
            return ClientListResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                mock_mode=False,
            )
    except Exception as e:
        logger.warning(f"[clients] list DB 查询失败, 回退 mock: {e}")

    # 回退 mock
    pool = list(_MOCK_CLIENTS)
    if firm_id:
        pool = [c for c in pool if c.get("firm_id") == firm_id]
    if client_type:
        pool = [c for c in pool if c["client_type"] == client_type]
    if grade:
        pool = [c for c in pool if c["grade"] == grade.upper()]
    if search:
        kw = search.lower()
        pool = [
            c for c in pool
            if kw in (c.get("name") or "").lower()
            or kw in (c.get("phone") or "").lower()
            or kw in (c.get("email") or "").lower()
            or kw in (c.get("id_number") or "").lower()
        ]

    total = len(pool)
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    offset = (page - 1) * page_size
    paged = pool[offset:offset + page_size]
    items = [_mock_client_response(c) for c in paged]

    latency_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[clients] list page={page} size={page_size} total={total} "
        f"search={search} latency={latency_ms}ms mock=True (fallback)"
    )

    return ClientListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        mock_mode=True,
    )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: str):
    """客户详情

    DB 不可用时回退 mock 数据。
    """
    t0 = time.time()

    try:
        async with _db_session() as session:
            stmt = select(Client).where(Client.client_id == client_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is not None:
                latency_ms = int((time.time() - t0) * 1000)
                logger.info(f"[clients] get client_id={client_id} latency={latency_ms}ms mock=False")
                return _row_to_response(row)
    except Exception as e:
        logger.warning(f"[clients] get DB 查询失败, 回退 mock: {e}")

    # 回退 mock
    for c in _MOCK_CLIENTS:
        if c["client_id"] == client_id:
            latency_ms = int((time.time() - t0) * 1000)
            logger.info(f"[clients] get client_id={client_id} latency={latency_ms}ms mock=True (fallback)")
            return _mock_client_response(c)

    logger.warning(f"[clients] get client_id={client_id} not found")
    raise HTTPException(404, f"client_id={client_id} 不存在")


@router.post("/", response_model=ClientResponse)
async def create_client(req: ClientCreateRequest):
    """创建客户

    DB 不可用时返回 mock 创建结果 (不入库, 仅返回带 client_id 的对象)。
    """
    t0 = time.time()
    client_id = _gen_client_id()

    try:
        async with _db_session() as session:
            # 查重 (按 name + id_number 或 phone)
            dup_stmt = select(Client).where(Client.name == req.name)
            if req.id_number:
                dup_stmt = dup_stmt.where(Client.id_number == req.id_number)
            elif req.phone:
                dup_stmt = dup_stmt.where(Client.phone == req.phone)
            dup_result = await session.execute(dup_stmt)
            if dup_result.scalar_one_or_none() is not None:
                raise HTTPException(409, f"客户已存在 (name={req.name})")

            row = Client(
                client_id=client_id,
                firm_id=req.firm_id,
                name=req.name,
                client_type=req.client_type,
                id_number=req.id_number,
                phone=req.phone,
                email=req.email,
                address=req.address,
                grade=req.grade.upper(),
                notes=req.notes,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"[clients] create client_id={client_id} name={req.name} "
            f"grade={req.grade} latency={latency_ms}ms mock=False"
        )
        return _row_to_response(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"[clients] create DB 写入失败, 返回 mock 结果: {e}")
        # 回退 mock: 返回内存对象 (不入库)
        now = _now_iso()
        mock_row = ClientResponse(
            id=int(time.time()) % 100000,
            client_id=client_id,
            firm_id=req.firm_id,
            name=req.name,
            client_type=req.client_type,
            id_number=req.id_number,
            phone=req.phone,
            email=req.email,
            address=req.address,
            grade=req.grade.upper(),
            notes=req.notes,
            created_at=now,
            updated_at=now,
        )
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"[clients] create client_id={client_id} name={req.name} "
            f"latency={latency_ms}ms mock=True (fallback)"
        )
        return mock_row


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, req: ClientUpdateRequest):
    """更新客户

    DB 不可用时返回 mock 更新结果。
    """
    t0 = time.time()

    try:
        async with _db_session() as session:
            stmt = select(Client).where(Client.client_id == client_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                raise HTTPException(404, f"client_id={client_id} 不存在")

            # 局部更新
            update_data = req.model_dump(exclude_unset=True)
            for k, v in update_data.items():
                if k == "grade" and v:
                    v = v.upper()
                setattr(row, k, v)
            await session.commit()
            await session.refresh(row)

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"[clients] update client_id={client_id} latency={latency_ms}ms mock=False")
        return _row_to_response(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"[clients] update DB 失败, 返回 mock 结果: {e}")
        # 回退 mock
        for c in _MOCK_CLIENTS:
            if c["client_id"] == client_id:
                update_data = req.model_dump(exclude_unset=True)
                merged = dict(c)
                for k, v in update_data.items():
                    if k == "grade" and v:
                        v = v.upper()
                    merged[k] = v if v is not None else merged.get(k)
                merged["updated_at"] = _now_iso()
                latency_ms = int((time.time() - t0) * 1000)
                logger.info(f"[clients] update client_id={client_id} latency={latency_ms}ms mock=True (fallback)")
                return _mock_client_response(merged)
        raise HTTPException(404, f"client_id={client_id} 不存在")


@router.delete("/{client_id}")
async def delete_client(client_id: str):
    """删除客户

    DB 不可用时返回 mock 删除结果。
    """
    t0 = time.time()

    try:
        async with _db_session() as session:
            stmt = select(Client).where(Client.client_id == client_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                raise HTTPException(404, f"client_id={client_id} 不存在")
            await session.delete(row)
            await session.commit()

        latency_ms = int((time.time() - t0) * 1000)
        logger.info(f"[clients] delete client_id={client_id} latency={latency_ms}ms mock=False")
        return {"client_id": client_id, "deleted": True, "mock_mode": False}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"[clients] delete DB 失败, 返回 mock 结果: {e}")
        # 回退 mock
        for c in _MOCK_CLIENTS:
            if c["client_id"] == client_id:
                latency_ms = int((time.time() - t0) * 1000)
                logger.info(f"[clients] delete client_id={client_id} latency={latency_ms}ms mock=True (fallback)")
                return {"client_id": client_id, "deleted": True, "mock_mode": True}
        raise HTTPException(404, f"client_id={client_id} 不存在")


@router.post("/{client_id}/conflict-check", response_model=ConflictCheckResponse)
async def conflict_check(client_id: str):
    """利益冲突检查

    检查该客户名称是否与:
    1. 已有其他客户重名 (同名/近似名)
    2. 案件当事人重名 (mock: 检查 mock 案件当事人)

    风险等级:
    - none: 无冲突
    - low: 名称部分匹配
    - medium: 同名不同证件号
    - high: 同名同证件号
    """
    t0 = time.time()

    # 取客户
    target_name: Optional[str] = None
    target_id_number: Optional[str] = None

    try:
        async with _db_session() as session:
            stmt = select(Client).where(Client.client_id == client_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is not None:
                target_name = row.name
                target_id_number = row.id_number
    except Exception as e:
        logger.warning(f"[clients] conflict-check DB 查询失败, 回退 mock: {e}")

    if not target_name:
        # 回退 mock
        for c in _MOCK_CLIENTS:
            if c["client_id"] == client_id:
                target_name = c["name"]
                target_id_number = c.get("id_number")
                break

    if not target_name:
        raise HTTPException(404, f"client_id={client_id} 不存在")

    conflicts: List[Dict[str, Any]] = []
    risk_level = "none"

    # 1. 与其他客户重名检查 (mock pool)
    for c in _MOCK_CLIENTS:
        if c["client_id"] == client_id:
            continue
        if c["name"] == target_name:
            # 同名
            if target_id_number and c.get("id_number") == target_id_number:
                risk_level = "high"
                conflicts.append({
                    "type": "client",
                    "client_id": c["client_id"],
                    "name": c["name"],
                    "reason": "同名且同证件号, 高度疑似同一主体",
                })
            else:
                if risk_level != "high":
                    risk_level = "medium"
                conflicts.append({
                    "type": "client",
                    "client_id": c["client_id"],
                    "name": c["name"],
                    "reason": "同名 (证件号不同)",
                })
        elif target_name and (target_name in c["name"] or c["name"] in target_name):
            # 部分匹配
            if risk_level not in ("high", "medium"):
                risk_level = "low"
            conflicts.append({
                "type": "client",
                "client_id": c["client_id"],
                "name": c["name"],
                "reason": "名称部分匹配",
            })

    # 2. 与案件当事人重名检查 (mock 案件当事人池)
    mock_case_parties = [
        {"case_id": "(2026)京01民初128号", "party": "李明", "role": "原告"},
        {"case_id": "(2026)京02民初256号", "party": "赵六", "role": "申请人"},
        {"case_id": "(2026)京03民初789号", "party": "张三", "role": "被告"},
        {"case_id": "(2026)京04民初345号", "party": "某科技有限公司", "role": "第三人"},
        {"case_id": "(2026)京05民初567号", "party": "王华", "role": "原告"},
    ]
    for p in mock_case_parties:
        if p["party"] == target_name:
            if risk_level not in ("high",):
                risk_level = "medium"
            conflicts.append({
                "type": "case_party",
                "case_id": p["case_id"],
                "name": p["party"],
                "role": p["role"],
                "reason": "客户名与案件当事人重名",
            })
        elif target_name and (target_name in p["party"] or p["party"] in target_name):
            if risk_level not in ("high", "medium"):
                risk_level = "low"
            conflicts.append({
                "type": "case_party",
                "case_id": p["case_id"],
                "name": p["party"],
                "role": p["role"],
                "reason": "名称与案件当事人部分匹配",
            })

    has_conflict = len(conflicts) > 0
    latency_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[clients] conflict-check client_id={client_id} name={target_name} "
        f"has_conflict={has_conflict} risk={risk_level} latency={latency_ms}ms"
    )

    return ConflictCheckResponse(
        client_id=client_id,
        name=target_name,
        has_conflict=has_conflict,
        conflicts=conflicts,
        risk_level=risk_level,
        disclaimer=DISCLAIMER,
    )
