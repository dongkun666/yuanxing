"""
LexPrime 日程管理 API 路由 (Phase 6 · 2026-07-02)

端点:
- GET    /api/schedule                获取日程列表 (支持 date_from, date_to, type 过滤)
- POST   /api/schedule                创建日程
- PUT    /api/schedule/{schedule_id}  更新日程
- DELETE /api/schedule/{schedule_id}  删除日程
- GET    /api/schedule/conflicts      检查时间冲突 (给定日期+时间)
- GET    /api/schedule/today          获取今日日程
- GET    /api/schedule/health         健康检查

支持 mock 模式: 当数据库不可用时返回模拟日程数据, 确保前端可联调
参考 ai_router.py 的代码风格和模式
"""
from __future__ import annotations

import time
import threading
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/schedule", tags=["schedule"])


# ========== 常量 ==========

MOCK_MODE = True

# 内存存储 (mock 模式下的持久化, 进程级)
# 真实场景应使用数据库 (PostgreSQL/SQLite), 这里用线程安全的 dict 模拟
_schedules_store: Dict[int, Dict[str, Any]] = {}
_store_lock = threading.Lock()
_next_id_lock = threading.Lock()
_next_id_counter = 1000


def _next_id() -> int:
    """生成自增 ID (mock 模式下用)"""
    global _next_id_counter
    with _next_id_lock:
        _next_id_counter += 1
        return _next_id_counter


# ========== Pydantic 模型 ==========

class ScheduleBase(BaseModel):
    """日程基础字段"""
    title: str = Field(..., min_length=1, max_length=200, description="日程标题")
    date: str = Field(..., description="日期 YYYY-MM-DD")
    time: str = Field(..., description="开始时间 HH:MM")
    endTime: Optional[str] = Field(None, description="结束时间 HH:MM")
    type: str = Field("其他", description="日程类型: 开庭/会议/待办/其他")
    caseId: Optional[Any] = Field(None, description="关联案件 ID")
    caseName: Optional[str] = Field(None, description="关联案件名称")
    location: Optional[str] = Field(None, description="地点/会议链接")
    note: Optional[str] = Field(None, description="备注")
    remind: Optional[Any] = Field(None, description="提醒设置 (分钟)")


class ScheduleCreate(ScheduleBase):
    """创建日程请求"""
    completed: Optional[bool] = False


class ScheduleUpdate(BaseModel):
    """更新日程请求 (所有字段可选)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    date: Optional[str] = None
    time: Optional[str] = None
    endTime: Optional[str] = None
    type: Optional[str] = None
    caseId: Optional[Any] = None
    caseName: Optional[str] = None
    location: Optional[str] = None
    note: Optional[str] = None
    remind: Optional[Any] = None
    completed: Optional[bool] = None


class ScheduleOut(ScheduleBase):
    """日程响应"""
    id: int
    completed: bool = False


class ConflictCheckResponse(BaseModel):
    """冲突检查响应"""
    has_conflict: bool
    conflicts: List[Dict[str, Any]] = []
    checked_at: str


# ========== Mock 数据 ==========

def _today_str() -> str:
    return date.today().isoformat()


def _future_str(days: int) -> str:
    d = date.today()
    from datetime import timedelta
    return (d + timedelta(days=days)).isoformat()


def _seed_mock_schedules() -> None:
    """初始化 mock 日程数据 (仅一次)"""
    if _schedules_store:
        return
    today = _today_str()
    tomorrow = _future_str(1)
    day_after = _future_str(2)
    mock_items = [
        {
            "id": 1,
            "title": "李明诉XX公司买卖合同纠纷开庭",
            "date": today,
            "time": "09:00",
            "endTime": "11:00",
            "type": "开庭",
            "caseId": "case1",
            "caseName": "李明诉XX公司买卖合同纠纷",
            "location": "朝阳区人民法院 第3法庭",
            "note": "",
            "remind": 60,
            "completed": False,
        },
        {
            "id": 2,
            "title": "王华借贷纠纷 - 策略讨论",
            "date": today,
            "time": "14:00",
            "endTime": "15:30",
            "type": "会议",
            "caseId": "case2",
            "caseName": "王华借贷纠纷",
            "location": "线上会议",
            "note": "",
            "remind": 15,
            "completed": False,
        },
        {
            "id": 3,
            "title": "提交张三合同纠纷补充证据",
            "date": today,
            "time": "16:00",
            "endTime": "16:30",
            "type": "待办",
            "caseId": "case3",
            "caseName": "张三合同纠纷",
            "location": "",
            "note": "证据目录已整理",
            "remind": 60,
            "completed": True,
        },
        {
            "id": 4,
            "title": "律所月度合伙人会议",
            "date": today,
            "time": "10:30",
            "endTime": "11:30",
            "type": "其他",
            "caseId": None,
            "caseName": None,
            "location": "大会议室",
            "note": "",
            "remind": 1440,
            "completed": True,
        },
        {
            "id": 5,
            "title": "某科技公司股权纠纷二审开庭",
            "date": today,
            "time": "15:00",
            "endTime": "17:00",
            "type": "开庭",
            "caseId": "case4",
            "caseName": "某科技公司股权纠纷",
            "location": "北京市高级人民法院 第8法庭",
            "note": "",
            "remind": 60,
            "completed": False,
        },
        {
            "id": 6,
            "title": "赵六劳动争议仲裁开庭",
            "date": tomorrow,
            "time": "09:00",
            "endTime": "12:00",
            "type": "开庭",
            "caseId": "case5",
            "caseName": "赵六劳动争议仲裁",
            "location": "朝阳区劳动仲裁委",
            "note": "",
            "remind": 1440,
            "completed": False,
        },
        {
            "id": 7,
            "title": "张三合同纠纷证据交换",
            "date": day_after,
            "time": "14:00",
            "endTime": "16:00",
            "type": "开庭",
            "caseId": "case3",
            "caseName": "张三合同纠纷",
            "location": "海淀区人民法院",
            "note": "",
            "remind": 60,
            "completed": False,
        },
    ]
    with _store_lock:
        for item in mock_items:
            _schedules_store[item["id"]] = item


def _all_schedules() -> List[Dict[str, Any]]:
    """返回所有日程 (mock 模式)"""
    _seed_mock_schedules()
    with _store_lock:
        return list(_schedules_store.values())


def _get_schedule(schedule_id: int) -> Optional[Dict[str, Any]]:
    _seed_mock_schedules()
    with _store_lock:
        return _schedules_store.get(schedule_id)


def _save_schedule(item: Dict[str, Any]) -> Dict[str, Any]:
    with _store_lock:
        _schedules_store[item["id"]] = item
    return item


def _delete_schedule(schedule_id: int) -> bool:
    with _store_lock:
        if schedule_id in _schedules_store:
            del _schedules_store[schedule_id]
            return True
        return False


def _filter_schedules(
    items: List[Dict[str, Any]],
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    type_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """按日期范围和类型过滤日程"""
    result = items
    if date_from:
        result = [s for s in result if s.get("date", "") >= date_from]
    if date_to:
        result = [s for s in result if s.get("date", "") <= date_to]
    if type_filter:
        result = [s for s in result if s.get("type") == type_filter]
    return result


def _check_conflicts(
    items: List[Dict[str, Any]],
    check_date: str,
    check_time: str,
    exclude_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """检查给定日期+时间的冲突日程 (时间区间重叠)"""
    conflicts = []
    # 默认结束时间 = 开始时间 + 1 小时
    end_hour = int(check_time.split(":")[0]) + 1
    check_end = f"{end_hour:02d}:{check_time.split(':')[1]}"
    for s in items:
        if exclude_id is not None and s.get("id") == exclude_id:
            continue
        if s.get("date") != check_date:
            continue
        s_time = s.get("time") or ""
        s_end = s.get("endTime") or s_time
        if not s_time:
            continue
        # 区间重叠: A.start < B.end && B.start < A.end
        if s_time < check_end and check_time < s_end:
            conflicts.append(s)
    return conflicts


def _sort_schedules(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """排序: 未完成优先, 同状态按 date+time 升序"""
    return sorted(
        items,
        key=lambda s: (
            1 if s.get("completed") else 0,
            (s.get("date") or "") + " " + (s.get("time") or ""),
        ),
    )


# ========== 端点 ==========

@router.get("/health")
async def schedule_health():
    """日程服务健康检查"""
    return {
        "status": "ok",
        "service": "lexprime-schedule-service",
        "version": "1.0.0",
        "mock_mode": MOCK_MODE,
        "endpoints": [
            {"path": "/api/schedule", "method": "GET", "purpose": "获取日程列表"},
            {"path": "/api/schedule", "method": "POST", "purpose": "创建日程"},
            {"path": "/api/schedule/{schedule_id}", "method": "PUT", "purpose": "更新日程"},
            {"path": "/api/schedule/{schedule_id}", "method": "DELETE", "purpose": "删除日程"},
            {"path": "/api/schedule/conflicts", "method": "GET", "purpose": "检查时间冲突"},
            {"path": "/api/schedule/today", "method": "GET", "purpose": "获取今日日程"},
        ],
    }


@router.get("/today")
async def get_today_schedules():
    """获取今日日程"""
    t0 = time.time()
    try:
        today = _today_str()
        items = _all_schedules()
        today_items = [s for s in items if s.get("date") == today]
        today_items = _sort_schedules(today_items)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"schedule today returned {len(today_items)} items in {latency_ms}ms, "
            f"mock_mode={MOCK_MODE}"
        )
        return {
            "date": today,
            "total": len(today_items),
            "items": today_items,
            "mock_mode": MOCK_MODE,
        }
    except Exception as e:
        logger.exception(f"schedule today failed: {e}")
        raise HTTPException(500, f"获取今日日程异常: {str(e)}")


@router.get("/conflicts")
async def check_schedule_conflicts(
    date: str = Query(..., description="日期 YYYY-MM-DD"),
    time: str = Query(..., description="时间 HH:MM"),
    exclude_id: Optional[int] = Query(None, description="排除的日程 ID (编辑时用)"),
):
    """检查时间冲突

    给定日期 + 时间, 返回是否有冲突的日程
    """
    t0 = time.time()
    try:
        items = _all_schedules()
        conflicts = _check_conflicts(items, date, time, exclude_id)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"schedule conflict check date={date} time={time} "
            f"-> {len(conflicts)} conflicts in {latency_ms}ms, mock_mode={MOCK_MODE}"
        )
        return ConflictCheckResponse(
            has_conflict=len(conflicts) > 0,
            conflicts=conflicts,
            checked_at=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        logger.exception(f"schedule conflict check failed: {e}")
        raise HTTPException(500, f"冲突检查异常: {str(e)}")


@router.get("/")
async def list_schedules(
    date_from: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    type: Optional[str] = Query(None, description="日程类型: 开庭/会议/待办/其他"),
):
    """获取日程列表 (支持日期范围和类型过滤)"""
    t0 = time.time()
    try:
        items = _all_schedules()
        items = _filter_schedules(items, date_from, date_to, type)
        items = _sort_schedules(items)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"schedule list returned {len(items)} items in {latency_ms}ms, "
            f"mock_mode={MOCK_MODE}"
        )
        return {
            "total": len(items),
            "items": items,
            "mock_mode": MOCK_MODE,
        }
    except Exception as e:
        logger.exception(f"schedule list failed: {e}")
        raise HTTPException(500, f"获取日程列表异常: {str(e)}")


@router.post("/")
async def create_schedule(req: ScheduleCreate):
    """创建日程"""
    t0 = time.time()
    try:
        # 计算默认结束时间 (开始 + 1 小时)
        end_time = req.endTime
        if not end_time and req.time:
            try:
                end_hour = int(req.time.split(":")[0]) + 1
                end_time = f"{end_hour:02d}:{req.time.split(':')[1]}"
            except Exception:
                end_time = req.time

        new_id = _next_id()
        item = {
            "id": new_id,
            "title": req.title,
            "date": req.date,
            "time": req.time,
            "endTime": end_time,
            "type": req.type or "其他",
            "caseId": req.caseId,
            "caseName": req.caseName,
            "location": req.location,
            "note": req.note,
            "remind": req.remind,
            "completed": bool(req.completed),
        }
        _save_schedule(item)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"schedule created id={new_id} title={req.title!r} in {latency_ms}ms, "
            f"mock_mode={MOCK_MODE}"
        )
        return ScheduleOut(**item)
    except Exception as e:
        logger.exception(f"schedule create failed: {e}")
        raise HTTPException(500, f"创建日程异常: {str(e)}")


@router.put("/{schedule_id}")
async def update_schedule(schedule_id: int, req: ScheduleUpdate):
    """更新日程"""
    t0 = time.time()
    try:
        existing = _get_schedule(schedule_id)
        if existing is None:
            raise HTTPException(404, f"日程不存在: {schedule_id}")

        # 合并更新字段 (仅更新非 None 字段)
        update_data = req.model_dump(exclude_unset=True)
        updated = dict(existing)
        updated.update(update_data)

        # 如果 time 变了但 endTime 没变, 重新计算 endTime
        if "time" in update_data and "endTime" not in update_data:
            try:
                end_hour = int(updated["time"].split(":")[0]) + 1
                updated["endTime"] = f"{end_hour:02d}:{updated['time'].split(':')[1]}"
            except Exception:
                pass

        _save_schedule(updated)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"schedule updated id={schedule_id} fields={list(update_data.keys())} "
            f"in {latency_ms}ms, mock_mode={MOCK_MODE}"
        )
        return ScheduleOut(**updated)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"schedule update failed: {e}")
        raise HTTPException(500, f"更新日程异常: {str(e)}")


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: int):
    """删除日程"""
    t0 = time.time()
    try:
        existing = _get_schedule(schedule_id)
        if existing is None:
            raise HTTPException(404, f"日程不存在: {schedule_id}")

        ok = _delete_schedule(schedule_id)
        latency_ms = int((time.time() - t0) * 1000)
        logger.info(
            f"schedule deleted id={schedule_id} ok={ok} in {latency_ms}ms, "
            f"mock_mode={MOCK_MODE}"
        )
        return {
            "id": schedule_id,
            "deleted": ok,
            "mock_mode": MOCK_MODE,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"schedule delete failed: {e}")
        raise HTTPException(500, f"删除日程异常: {str(e)}")
