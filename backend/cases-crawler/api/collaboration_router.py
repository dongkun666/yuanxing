"""
LexPrime 团队协作 API 路由
提供团队成员管理、任务分配、评论讨论、文件共享、权限管理等协作功能接口

端点:
- GET    /api/collaboration/members              团队成员列表
- POST   /api/collaboration/members/invite       邀请成员
- PUT    /api/collaboration/members/{member_id}  更新成员信息
- DELETE /api/collaboration/members/{member_id}  移除成员
- GET    /api/collaboration/tasks                任务列表
- POST   /api/collaboration/tasks                创建任务
- PUT    /api/collaboration/tasks/{task_id}      更新任务
- DELETE /api/collaboration/tasks/{task_id}      删除任务
- GET    /api/collaboration/comments             评论列表
- POST   /api/collaboration/comments             添加评论
- GET    /api/collaboration/files                文件列表
- POST   /api/collaboration/files/upload         上传文件
- DELETE /api/collaboration/files/{file_id}      删除文件
- GET    /api/collaboration/permissions          权限列表
- PUT    /api/collaboration/permissions          更新权限
- GET    /api/collaboration/stats                协作统计
- GET    /api/collaboration/health               健康检查
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/collaboration", tags=["collaboration"])


# ============================================================================
# 常量
# ============================================================================

COLLABORATION_DISCLAIMER = """
**团队协作声明**
本模块提供的协作功能仅供律所内部团队使用，所有数据传输均经过加密处理。
用户需对其账号下的所有操作负责，敏感信息请妥善保管。
"""

MOCK_MODE = True


# ============================================================================
# Pydantic 模型
# ============================================================================

class TeamMember(BaseModel):
    """团队成员"""
    id: str = Field(..., description="成员ID")
    name: str = Field(..., description="姓名")
    email: str = Field(..., description="邮箱")
    role: str = Field("member", description="角色: owner/admin/member")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    specialties: List[str] = Field(default_factory=list, description="专业领域")
    status: str = Field("active", description="状态: active/pending/inactive")
    joined_at: str = Field(..., description="加入时间")
    last_active: Optional[str] = Field(None, description="最后活跃时间")
    task_count: int = Field(0, description="进行中任务数")
    case_count: int = Field(0, description="协作案件数")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "M001",
                "name": "张明",
                "email": "zhangming@lexprime.com",
                "role": "owner",
                "avatar_url": "/assets/images/avatar.jpg",
                "specialties": ["民商事诉讼", "合同纠纷"],
                "status": "active",
                "joined_at": "2025-01-15T09:00:00Z",
                "last_active": "2026-07-01T14:30:00Z",
                "task_count": 8,
                "case_count": 12
            }
        }


class MemberInviteRequest(BaseModel):
    """邀请成员请求"""
    email: str = Field(..., description="邮箱")
    name: Optional[str] = Field(None, description="姓名")
    role: str = Field("member", description="角色")
    message: Optional[str] = Field(None, description="邀请消息")


class TaskBase(BaseModel):
    """任务基础字段"""
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    assignee_id: Optional[str] = Field(None, description="负责人ID")
    case_id: Optional[str] = Field(None, description="关联案件ID")
    case_name: Optional[str] = Field(None, description="关联案件名称")
    priority: str = Field("medium", pattern="^(low|medium|high|urgent)$", description="优先级")
    status: str = Field("todo", pattern="^(todo|in_progress|review|done)$", description="状态")
    due_date: Optional[str] = Field(None, description="截止日期")
    tags: List[str] = Field(default_factory=list, description="标签")


class TaskCreateRequest(TaskBase):
    """创建任务请求"""
    pass


class TaskUpdateRequest(TaskBase):
    """更新任务请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    status: Optional[str] = Field(None, pattern="^(todo|in_progress|review|done)$")


class Task(TaskBase):
    """任务响应"""
    id: str = Field(..., description="任务ID")
    creator_id: str = Field(..., description="创建者ID")
    creator_name: str = Field(..., description="创建者姓名")
    assignee_name: Optional[str] = Field(None, description="负责人姓名")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    comment_count: int = Field(0, description="评论数")
    attachment_count: int = Field(0, description="附件数")


class Comment(BaseModel):
    """评论"""
    id: str = Field(..., description="评论ID")
    task_id: Optional[str] = Field(None, description="任务ID")
    case_id: Optional[str] = Field(None, description="案件ID")
    author_id: str = Field(..., description="作者ID")
    author_name: str = Field(..., description="作者姓名")
    author_avatar: Optional[str] = Field(None, description="作者头像")
    content: str = Field(..., description="评论内容")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    reply_to: Optional[str] = Field(None, description="回复的评论ID")
    mentions: List[str] = Field(default_factory=list, description="@提及的用户ID")


class CommentCreateRequest(BaseModel):
    """创建评论请求"""
    task_id: Optional[str] = Field(None, description="任务ID")
    case_id: Optional[str] = Field(None, description="案件ID")
    content: str = Field(..., min_length=1, description="评论内容")
    reply_to: Optional[str] = Field(None, description="回复的评论ID")


class SharedFile(BaseModel):
    """共享文件"""
    id: str = Field(..., description="文件ID")
    name: str = Field(..., description="文件名")
    size: int = Field(0, description="文件大小 (字节)")
    type: str = Field("file", description="类型: file/folder")
    file_type: Optional[str] = Field(None, description="文件类型: doc/pdf/img等")
    uploader_id: str = Field(..., description="上传者ID")
    uploader_name: str = Field(..., description="上传者姓名")
    case_id: Optional[str] = Field(None, description="关联案件ID")
    task_id: Optional[str] = Field(None, description="关联任务ID")
    folder_id: Optional[str] = Field(None, description="父文件夹ID")
    created_at: str = Field(..., description="上传时间")
    download_count: int = Field(0, description="下载次数")


class Permission(BaseModel):
    """权限"""
    id: str = Field(..., description="权限ID")
    name: str = Field(..., description="权限名称")
    code: str = Field(..., description="权限代码")
    description: Optional[str] = Field(None, description="权限描述")
    category: str = Field("general", description="权限分类")


class RolePermission(BaseModel):
    """角色权限"""
    role: str = Field(..., description="角色")
    permissions: List[str] = Field(default_factory=list, description="权限代码列表")


class PermissionUpdateRequest(BaseModel):
    """更新权限请求"""
    member_id: str = Field(..., description="成员ID")
    role: Optional[str] = Field(None, description="角色")
    permissions: Optional[List[str]] = Field(None, description="自定义权限列表")


class CollaborationStats(BaseModel):
    """协作统计"""
    total_members: int = Field(0, description="团队成员数")
    active_members: int = Field(0, description="活跃成员数")
    total_tasks: int = Field(0, description="总任务数")
    completed_tasks: int = Field(0, description="已完成任务数")
    in_progress_tasks: int = Field(0, description="进行中任务数")
    total_cases: int = Field(0, description="协作案件数")
    total_files: int = Field(0, description="共享文件数")
    total_comments: int = Field(0, description="评论总数")
    disclaimer: str = Field("", description="免责声明")


# ============================================================================
# Mock 数据
# ============================================================================

def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


_MOCK_MEMBERS: List[Dict[str, Any]] = [
    {
        "id": "M001",
        "name": "张明",
        "email": "zhangming@lexprime.com",
        "role": "owner",
        "avatar_url": "/assets/images/avatar.jpg",
        "specialties": ["民商事诉讼", "合同纠纷", "知识产权"],
        "status": "active",
        "joined_at": "2025-01-15T09:00:00Z",
        "last_active": "2026-07-01T14:30:00Z",
        "task_count": 8,
        "case_count": 12
    },
    {
        "id": "M002",
        "name": "李华",
        "email": "lihua@lexprime.com",
        "role": "admin",
        "avatar_url": None,
        "specialties": ["公司法", "投融资", "并购重组"],
        "status": "active",
        "joined_at": "2025-03-20T10:00:00Z",
        "last_active": "2026-07-01T13:15:00Z",
        "task_count": 12,
        "case_count": 18
    },
    {
        "id": "M003",
        "name": "王芳",
        "email": "wangfang@lexprime.com",
        "role": "member",
        "avatar_url": None,
        "specialties": ["婚姻家事", "遗产继承", "财富管理"],
        "status": "active",
        "joined_at": "2025-06-01T09:30:00Z",
        "last_active": "2026-06-30T16:45:00Z",
        "task_count": 5,
        "case_count": 8
    },
    {
        "id": "M004",
        "name": "陈伟",
        "email": "chenwei@lexprime.com",
        "role": "member",
        "avatar_url": None,
        "specialties": ["刑事辩护", "行政诉讼"],
        "status": "active",
        "joined_at": "2025-08-15T11:00:00Z",
        "last_active": "2026-07-01T10:20:00Z",
        "task_count": 6,
        "case_count": 9
    },
    {
        "id": "M005",
        "name": "刘洋",
        "email": "liuyang@lexprime.com",
        "role": "member",
        "avatar_url": None,
        "specialties": ["劳动争议", "交通事故"],
        "status": "pending",
        "joined_at": "2026-06-28T14:00:00Z",
        "last_active": None,
        "task_count": 0,
        "case_count": 0
    }
]

_MOCK_TASKS: List[Dict[str, Any]] = [
    {
        "id": "T001",
        "title": "起草起诉状 - 借款合同纠纷案",
        "description": "根据客户提供的证据材料，起草起诉状并准备立案材料",
        "assignee_id": "M001",
        "assignee_name": "张明",
        "case_id": "C001",
        "case_name": "张三诉李四借款合同纠纷案",
        "priority": "high",
        "status": "in_progress",
        "due_date": "2026-07-05",
        "tags": ["诉讼", "合同纠纷", "立案"],
        "creator_id": "M002",
        "creator_name": "李华",
        "created_at": "2026-06-28T09:00:00Z",
        "updated_at": "2026-07-01T11:30:00Z",
        "comment_count": 3,
        "attachment_count": 2
    },
    {
        "id": "T002",
        "title": "合同审查 - 技术服务合同",
        "description": "审查客户提供的技术服务合同，识别风险点并提出修改建议",
        "assignee_id": "M002",
        "assignee_name": "李华",
        "case_id": None,
        "case_name": None,
        "priority": "medium",
        "status": "review",
        "due_date": "2026-07-03",
        "tags": ["合同审查", "技术合同"],
        "creator_id": "M001",
        "creator_name": "张明",
        "created_at": "2026-06-29T14:00:00Z",
        "updated_at": "2026-07-01T09:15:00Z",
        "comment_count": 5,
        "attachment_count": 1
    },
    {
        "id": "T003",
        "title": "证据整理 - 劳动争议案",
        "description": "整理劳动争议案件的证据材料，制作证据目录",
        "assignee_id": "M003",
        "assignee_name": "王芳",
        "case_id": "C002",
        "case_name": "王某诉某公司劳动争议案",
        "priority": "medium",
        "status": "todo",
        "due_date": "2026-07-08",
        "tags": ["劳动争议", "证据"],
        "creator_id": "M001",
        "creator_name": "张明",
        "created_at": "2026-06-30T10:00:00Z",
        "updated_at": "2026-06-30T10:00:00Z",
        "comment_count": 0,
        "attachment_count": 0
    },
    {
        "id": "T004",
        "title": "客户访谈纪要 - 股权纠纷案",
        "description": "整理昨天与客户的访谈纪要，确认案件关键事实",
        "assignee_id": "M004",
        "assignee_name": "陈伟",
        "case_id": "C003",
        "case_name": "某公司股权确认纠纷案",
        "priority": "urgent",
        "status": "done",
        "due_date": "2026-07-01",
        "tags": ["公司法", "股权", "访谈"],
        "creator_id": "M002",
        "creator_name": "李华",
        "created_at": "2026-06-27T16:00:00Z",
        "updated_at": "2026-06-30T15:00:00Z",
        "comment_count": 2,
        "attachment_count": 1
    },
    {
        "id": "T005",
        "title": "法律意见书 - 知识产权侵权",
        "description": "就客户的商标侵权问题出具法律意见书",
        "assignee_id": "M001",
        "assignee_name": "张明",
        "case_id": "C004",
        "case_name": "某品牌商标侵权案",
        "priority": "high",
        "status": "in_progress",
        "due_date": "2026-07-10",
        "tags": ["知识产权", "商标", "法律意见"],
        "creator_id": "M001",
        "creator_name": "张明",
        "created_at": "2026-06-25T11:00:00Z",
        "updated_at": "2026-07-01T14:00:00Z",
        "comment_count": 4,
        "attachment_count": 3
    }
]

_MOCK_COMMENTS: List[Dict[str, Any]] = [
    {
        "id": "C001",
        "task_id": "T001",
        "case_id": None,
        "author_id": "M002",
        "author_name": "李华",
        "author_avatar": None,
        "content": "起诉状初稿已经完成，请查阅附件，有问题随时沟通。",
        "created_at": "2026-06-29T10:00:00Z",
        "updated_at": None,
        "reply_to": None,
        "mentions": ["M001"]
    },
    {
        "id": "C002",
        "task_id": "T001",
        "case_id": None,
        "author_id": "M001",
        "author_name": "张明",
        "author_avatar": "/assets/images/avatar.jpg",
        "content": "收到，我看一下，下午给你反馈。",
        "created_at": "2026-06-29T11:30:00Z",
        "updated_at": None,
        "reply_to": "C001",
        "mentions": []
    },
    {
        "id": "C003",
        "task_id": "T002",
        "case_id": None,
        "author_id": "M001",
        "author_name": "张明",
        "author_avatar": "/assets/images/avatar.jpg",
        "content": "合同第8条违约责任条款需要修改，建议增加违约金计算方式。",
        "created_at": "2026-06-30T09:00:00Z",
        "updated_at": None,
        "reply_to": None,
        "mentions": ["M002"]
    }
]

_MOCK_FILES: List[Dict[str, Any]] = [
    {
        "id": "F001",
        "name": "起诉状-借款合同纠纷.docx",
        "size": 24576,
        "type": "file",
        "file_type": "doc",
        "uploader_id": "M001",
        "uploader_name": "张明",
        "case_id": "C001",
        "task_id": "T001",
        "folder_id": None,
        "created_at": "2026-06-29T10:00:00Z",
        "download_count": 5
    },
    {
        "id": "F002",
        "name": "证据材料",
        "size": 0,
        "type": "folder",
        "file_type": None,
        "uploader_id": "M002",
        "uploader_name": "李华",
        "case_id": "C001",
        "task_id": "T001",
        "folder_id": None,
        "created_at": "2026-06-28T15:00:00Z",
        "download_count": 0
    },
    {
        "id": "F003",
        "name": "技术服务合同.pdf",
        "size": 102400,
        "type": "file",
        "file_type": "pdf",
        "uploader_id": "M002",
        "uploader_name": "李华",
        "case_id": None,
        "task_id": "T002",
        "folder_id": None,
        "created_at": "2026-06-29T14:00:00Z",
        "download_count": 8
    },
    {
        "id": "F004",
        "name": "劳动合同.pdf",
        "size": 51200,
        "type": "file",
        "file_type": "pdf",
        "uploader_id": "M003",
        "uploader_name": "王芳",
        "case_id": "C002",
        "task_id": "T003",
        "folder_id": None,
        "created_at": "2026-06-30T10:30:00Z",
        "download_count": 3
    }
]

_MOCK_PERMISSIONS: List[Dict[str, Any]] = [
    {"id": "P001", "name": "查看案件", "code": "case:view", "description": "查看案件详情和列表", "category": "case"},
    {"id": "P002", "name": "创建案件", "code": "case:create", "description": "创建新案件", "category": "case"},
    {"id": "P003", "name": "编辑案件", "code": "case:edit", "description": "编辑案件信息", "category": "case"},
    {"id": "P004", "name": "删除案件", "code": "case:delete", "description": "删除案件", "category": "case"},
    {"id": "P005", "name": "查看任务", "code": "task:view", "description": "查看任务列表和详情", "category": "task"},
    {"id": "P006", "name": "创建任务", "code": "task:create", "description": "创建新任务", "category": "task"},
    {"id": "P007", "name": "分配任务", "code": "task:assign", "description": "分配任务给成员", "category": "task"},
    {"id": "P008", "name": "上传文件", "code": "file:upload", "description": "上传共享文件", "category": "file"},
    {"id": "P009", "name": "下载文件", "code": "file:download", "description": "下载共享文件", "category": "file"},
    {"id": "P010", "name": "删除文件", "code": "file:delete", "description": "删除共享文件", "category": "file"},
    {"id": "P011", "name": "邀请成员", "code": "member:invite", "description": "邀请新成员加入团队", "category": "member"},
    {"id": "P012", "name": "管理成员", "code": "member:manage", "description": "管理团队成员和权限", "category": "member"},
]

_MOCK_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "owner": ["case:view", "case:create", "case:edit", "case:delete",
              "task:view", "task:create", "task:assign",
              "file:upload", "file:download", "file:delete",
              "member:invite", "member:manage"],
    "admin": ["case:view", "case:create", "case:edit",
              "task:view", "task:create", "task:assign",
              "file:upload", "file:download",
              "member:invite"],
    "member": ["case:view", "task:view", "task:create",
               "file:upload", "file:download"]
}


def _measure_latency_ms(start_time: float) -> float:
    return round((time.time() - start_time) * 1000, 2)


# ============================================================================
# 端点
# ============================================================================

@router.get("/health", summary="团队协作 API 健康检查")
async def collaboration_health():
    """检查团队协作 API 是否可用"""
    return {
        "status": "ok",
        "service": "collaboration",
        "version": "1.0.0",
        "mock_mode": MOCK_MODE,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "disclaimer": COLLABORATION_DISCLAIMER.strip()
    }


@router.get("/stats", response_model=CollaborationStats, summary="协作统计")
async def get_collaboration_stats(
    firm_id: Optional[str] = Query(None, description="律所ID"),
):
    """获取团队协作统计数据"""
    start_time = time.time()
    logger.info(f"[Collaboration] 获取协作统计, firm_id={firm_id}")

    try:
        active_count = sum(1 for m in _MOCK_MEMBERS if m["status"] == "active")
        completed_count = sum(1 for t in _MOCK_TASKS if t["status"] == "done")
        in_progress_count = sum(1 for t in _MOCK_TASKS if t["status"] == "in_progress")

        stats = CollaborationStats(
            total_members=len(_MOCK_MEMBERS),
            active_members=active_count,
            total_tasks=len(_MOCK_TASKS),
            completed_tasks=completed_count,
            in_progress_tasks=in_progress_count,
            total_cases=15,
            total_files=len(_MOCK_FILES),
            total_comments=len(_MOCK_COMMENTS),
            disclaimer=COLLABORATION_DISCLAIMER.strip()
        )

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Collaboration] 协作统计获取完成, 耗时={latency}ms")

        return stats

    except Exception as e:
        logger.error(f"[Collaboration] 获取协作统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取协作统计失败: {str(e)}")


@router.get("/members", summary="团队成员列表")
async def list_members(
    firm_id: Optional[str] = Query(None, description="律所ID"),
    role: Optional[str] = Query(None, description="角色筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取团队成员列表"""
    start_time = time.time()
    logger.info(f"[Collaboration] 获取成员列表, role={role}, status={status}, keyword={keyword}")

    try:
        members = _MOCK_MEMBERS.copy()

        if role:
            members = [m for m in members if m["role"] == role]
        if status:
            members = [m for m in members if m["status"] == status]
        if keyword:
            kw = keyword.lower()
            members = [m for m in members if kw in m["name"].lower() or kw in m["email"].lower()]

        total = len(members)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = members[start:end]

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Collaboration] 成员列表获取完成, 共{total}条, 耗时={latency}ms")

        return {
            "items": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "mock_mode": MOCK_MODE
        }

    except Exception as e:
        logger.error(f"[Collaboration] 获取成员列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取成员列表失败: {str(e)}")


@router.post("/members/invite", summary="邀请成员")
async def invite_member(
    req: MemberInviteRequest,
    firm_id: Optional[str] = Query(None, description="律所ID"),
):
    """邀请新成员加入团队"""
    start_time = time.time()
    logger.info(f"[Collaboration] 邀请成员, email={req.email}")

    try:
        new_member = {
            "id": "M" + str(len(_MOCK_MEMBERS) + 1).zfill(3),
            "name": req.name or req.email.split("@")[0],
            "email": req.email,
            "role": req.role or "member",
            "avatar_url": None,
            "specialties": [],
            "status": "pending",
            "joined_at": _now_iso(),
            "last_active": None,
            "task_count": 0,
            "case_count": 0
        }
        _MOCK_MEMBERS.append(new_member)

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Collaboration] 成员邀请成功, 耗时={latency}ms")

        return {
            "status": "success",
            "member": new_member,
            "message": "邀请已发送"
        }

    except Exception as e:
        logger.error(f"[Collaboration] 邀请成员失败: {e}")
        raise HTTPException(status_code=500, detail=f"邀请成员失败: {str(e)}")


@router.get("/tasks", summary="任务列表")
async def list_tasks(
    firm_id: Optional[str] = Query(None, description="律所ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    assignee_id: Optional[str] = Query(None, description="负责人筛选"),
    case_id: Optional[str] = Query(None, description="案件筛选"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取任务列表"""
    start_time = time.time()
    logger.info(f"[Collaboration] 获取任务列表, status={status}, priority={priority}")

    try:
        tasks = _MOCK_TASKS.copy()

        if status:
            tasks = [t for t in tasks if t["status"] == status]
        if priority:
            tasks = [t for t in tasks if t["priority"] == priority]
        if assignee_id:
            tasks = [t for t in tasks if t.get("assignee_id") == assignee_id]
        if case_id:
            tasks = [t for t in tasks if t.get("case_id") == case_id]
        if keyword:
            kw = keyword.lower()
            tasks = [t for t in tasks if kw in t["title"].lower()]

        total = len(tasks)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = tasks[start:end]

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Collaboration] 任务列表获取完成, 共{total}条, 耗时={latency}ms")

        return {
            "items": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "mock_mode": MOCK_MODE
        }

    except Exception as e:
        logger.error(f"[Collaboration] 获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.post("/tasks", summary="创建任务")
async def create_task(
    req: TaskCreateRequest,
    firm_id: Optional[str] = Query(None, description="律所ID"),
):
    """创建新任务"""
    start_time = time.time()
    logger.info(f"[Collaboration] 创建任务, title={req.title}")

    try:
        now = _now_iso()
        assignee_name = None
        if req.assignee_id:
            member = next((m for m in _MOCK_MEMBERS if m["id"] == req.assignee_id), None)
            if member:
                assignee_name = member["name"]

        new_task = {
            "id": "T" + str(len(_MOCK_TASKS) + 1).zfill(3),
            "title": req.title,
            "description": req.description,
            "assignee_id": req.assignee_id,
            "assignee_name": assignee_name,
            "case_id": req.case_id,
            "case_name": req.case_name,
            "priority": req.priority,
            "status": req.status,
            "due_date": req.due_date,
            "tags": req.tags,
            "creator_id": "M001",
            "creator_name": "张明",
            "created_at": now,
            "updated_at": now,
            "comment_count": 0,
            "attachment_count": 0
        }
        _MOCK_TASKS.append(new_task)

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Collaboration] 任务创建成功, 耗时={latency}ms")

        return {
            "status": "success",
            "task": new_task,
            "message": "任务创建成功"
        }

    except Exception as e:
        logger.error(f"[Collaboration] 创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.put("/tasks/{task_id}", summary="更新任务")
async def update_task(
    task_id: str,
    req: TaskUpdateRequest,
):
    """更新任务"""
    start_time = time.time()
    logger.info(f"[Collaboration] 更新任务, task_id={task_id}")

    try:
        task = next((t for t in _MOCK_TASKS if t["id"] == task_id), None)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        update_data = req.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                task[key] = value

        if "assignee_id" in update_data and update_data["assignee_id"]:
            member = next((m for m in _MOCK_MEMBERS if m["id"] == update_data["assignee_id"]), None)
            if member:
                task["assignee_name"] = member["name"]

        task["updated_at"] = _now_iso()

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Collaboration] 任务更新成功, 耗时={latency}ms")

        return {
            "status": "success",
            "task": task,
            "message": "任务更新成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Collaboration] 更新任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新任务失败: {str(e)}")


@router.get("/comments", summary="评论列表")
async def list_comments(
    task_id: Optional[str] = Query(None, description="任务ID"),
    case_id: Optional[str] = Query(None, description="案件ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取评论列表"""
    start_time = time.time()
    logger.info(f"[Collaboration] 获取评论列表, task_id={task_id}, case_id={case_id}")

    try:
        comments = _MOCK_COMMENTS.copy()

        if task_id:
            comments = [c for c in comments if c.get("task_id") == task_id]
        if case_id:
            comments = [c for c in comments if c.get("case_id") == case_id]

        total = len(comments)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = comments[start:end]

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Collaboration] 评论列表获取完成, 共{total}条, 耗时={latency}ms")

        return {
            "items": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "mock_mode": MOCK_MODE
        }

    except Exception as e:
        logger.error(f"[Collaboration] 获取评论列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取评论列表失败: {str(e)}")


@router.post("/comments", summary="添加评论")
async def create_comment(
    req: CommentCreateRequest,
):
    """添加评论"""
    start_time = time.time()
    logger.info(f"[Collaboration] 添加评论, task_id={req.task_id}")

    try:
        now = _now_iso()
        new_comment = {
            "id": "C" + str(len(_MOCK_COMMENTS) + 1).zfill(3),
            "task_id": req.task_id,
            "case_id": req.case_id,
            "author_id": "M001",
            "author_name": "张明",
            "author_avatar": "/assets/images/avatar.jpg",
            "content": req.content,
            "created_at": now,
            "updated_at": None,
            "reply_to": req.reply_to,
            "mentions": []
        }
        _MOCK_COMMENTS.append(new_comment)

        if req.task_id:
            task = next((t for t in _MOCK_TASKS if t["id"] == req.task_id), None)
            if task:
                task["comment_count"] = task.get("comment_count", 0) + 1

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Collaboration] 评论添加成功, 耗时={latency}ms")

        return {
            "status": "success",
            "comment": new_comment,
            "message": "评论添加成功"
        }

    except Exception as e:
        logger.error(f"[Collaboration] 添加评论失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加评论失败: {str(e)}")


@router.get("/files", summary="文件列表")
async def list_files(
    firm_id: Optional[str] = Query(None, description="律所ID"),
    case_id: Optional[str] = Query(None, description="案件ID"),
    task_id: Optional[str] = Query(None, description="任务ID"),
    folder_id: Optional[str] = Query(None, description="文件夹ID"),
    file_type: Optional[str] = Query(None, description="文件类型"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取共享文件列表"""
    start_time = time.time()
    logger.info(f"[Collaboration] 获取文件列表, case_id={case_id}, task_id={task_id}")

    try:
        files = _MOCK_FILES.copy()

        if case_id:
            files = [f for f in files if f.get("case_id") == case_id]
        if task_id:
            files = [f for f in files if f.get("task_id") == task_id]
        if folder_id:
            files = [f for f in files if f.get("folder_id") == folder_id]
        elif folder_id is None:
            files = [f for f in files if f.get("folder_id") is None]
        if file_type:
            files = [f for f in files if f.get("file_type") == file_type]
        if keyword:
            kw = keyword.lower()
            files = [f for f in files if kw in f["name"].lower()]

        total = len(files)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = files[start:end]

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Collaboration] 文件列表获取完成, 共{total}条, 耗时={latency}ms")

        return {
            "items": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "mock_mode": MOCK_MODE
        }

    except Exception as e:
        logger.error(f"[Collaboration] 获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")


@router.get("/permissions", summary="权限列表")
async def list_permissions(
    firm_id: Optional[str] = Query(None, description="律所ID"),
    category: Optional[str] = Query(None, description="权限分类"),
):
    """获取权限列表和角色权限配置"""
    start_time = time.time()
    logger.info(f"[Collaboration] 获取权限列表, category={category}")

    try:
        permissions = _MOCK_PERMISSIONS.copy()
        if category:
            permissions = [p for p in permissions if p["category"] == category]

        role_permissions = []
        for role, perms in _MOCK_ROLE_PERMISSIONS.items():
            role_permissions.append({
                "role": role,
                "permissions": perms
            })

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Collaboration] 权限列表获取完成, 耗时={latency}ms")

        return {
            "permissions": permissions,
            "role_permissions": role_permissions,
            "mock_mode": MOCK_MODE
        }

    except Exception as e:
        logger.error(f"[Collaboration] 获取权限列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取权限列表失败: {str(e)}")


@router.put("/permissions", summary="更新权限")
async def update_permissions(
    req: PermissionUpdateRequest,
    firm_id: Optional[str] = Query(None, description="律所ID"),
):
    """更新成员权限"""
    start_time = time.time()
    logger.info(f"[Collaboration] 更新权限, member_id={req.member_id}")

    try:
        member = next((m for m in _MOCK_MEMBERS if m["id"] == req.member_id), None)
        if not member:
            raise HTTPException(status_code=404, detail="成员不存在")

        if req.role:
            member["role"] = req.role

        latency = _measure_latency_ms(start_time)
        logger.info(f"[Collaboration] 权限更新成功, 耗时={latency}ms")

        return {
            "status": "success",
            "member": member,
            "message": "权限更新成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Collaboration] 更新权限失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新权限失败: {str(e)}")
