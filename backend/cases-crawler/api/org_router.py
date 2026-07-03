"""
LexPrime 组织架构 API (FastAPI)
2026-07-03 · 企业级能力建设

端点:
- GET    /api/org/departments      部门列表/部门树
- POST   /api/org/departments      创建部门
- GET    /api/org/departments/{id} 部门详情
- PUT    /api/org/departments/{id} 更新部门
- DELETE /api/org/departments/{id} 删除部门
- GET    /api/org/departments/{id}/members 部门成员列表
- POST   /api/org/departments/{id}/members 添加部门成员

- GET    /api/org/teams           团队列表
- POST   /api/org/teams           创建团队
- GET    /api/org/teams/{id}      团队详情
- PUT    /api/org/teams/{id}     更新团队
- DELETE /api/org/teams/{id}     删除团队
- GET    /api/org/teams/{id}/members 团队成员列表

- GET    /api/org/roles           角色列表
- POST   /api/org/roles           创建角色
- GET    /api/org/roles/{id}      角色详情
- PUT    /api/org/roles/{id}     更新角色
- DELETE /api/org/roles/{id}     删除角色

- GET    /api/org/members         成员列表
- POST   /api/org/members/invite  邀请成员
- GET    /api/org/permissions     权限定义列表
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Depends
from loguru import logger
from pydantic import BaseModel, Field, EmailStr, field_validator
from sqlalchemy import select, func, and_, or_

from core.db import Database
from core.organization import (
    Department, Team, Role, DepartmentMember, TeamMember, UserRole, OrgInvitation,
    DepartmentStatus, TeamStatus, PermissionDefinition, OrganizationService,
)
from auth.dependencies import get_current_admin
from auth.models import User

router = APIRouter(prefix="/api/org", tags=["organization"])


# ========== Pydantic 模型 ==========

class DepartmentOut(BaseModel):
    dept_id: str
    name: str
    description: Optional[str]
    parent_id: Optional[int]
    path: Optional[str]
    level: int
    sort_order: int
    status: str
    manager_id: Optional[int]
    member_count: int = 0
    location: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    created_at: str
    updated_at: str


class DepartmentCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    description: Optional[str] = Field(None, max_length=512)
    parent_id: Optional[int] = None
    sort_order: int = 0
    manager_id: Optional[int] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    permissions: Optional[List[str]] = None


class DepartmentUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=128)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None
    manager_id: Optional[int] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    permissions: Optional[List[str]] = None


class TeamOut(BaseModel):
    team_id: str
    name: str
    description: Optional[str]
    team_type: str
    status: str
    department_id: Optional[int]
    leader_id: Optional[int]
    member_count: int = 0
    max_members: Optional[int]
    color: Optional[str]
    created_at: str
    updated_at: str


class TeamCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    description: Optional[str] = None
    team_type: str = "project"
    department_id: Optional[int] = None
    leader_id: Optional[int] = None
    max_members: Optional[int] = None
    color: Optional[str] = None
    permissions: Optional[List[str]] = None


class TeamUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    team_type: Optional[str] = None
    status: Optional[str] = None
    department_id: Optional[int] = None
    leader_id: Optional[int] = None
    max_members: Optional[int] = None
    color: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleOut(BaseModel):
    role_id: str
    name: str
    description: Optional[str]
    role_type: str
    is_system: bool
    is_enabled: bool
    permissions: Optional[List[str]]
    data_scope: str
    parent_id: Optional[int]
    inherit_parent: bool
    sort_order: int
    color: Optional[str]
    user_count: int = 0
    created_at: str
    updated_at: str


class RoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=64)
    description: Optional[str] = None
    role_type: str = "custom"
    permissions: List[str] = []
    data_scope: str = "all"
    parent_id: Optional[int] = None
    inherit_parent: bool = False
    sort_order: int = 0
    color: Optional[str] = None


class RoleUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    permissions: Optional[List[str]] = None
    data_scope: Optional[str] = None
    parent_id: Optional[int] = None
    inherit_parent: Optional[bool] = None
    sort_order: Optional[int] = None
    color: Optional[str] = None


class MemberOut(BaseModel):
    user_id: int
    username: str
    email: str
    name: str
    avatar_url: Optional[str]
    status: str
    role: str
    department_ids: List[int] = []
    department_names: List[str] = []
    team_ids: List[int] = []
    team_names: List[str] = []
    role_ids: List[int] = []
    position: Optional[str]
    job_title: Optional[str]
    join_date: Optional[str]
    last_login_at: Optional[str]


class InviteMemberRequest(BaseModel):
    emails: List[EmailStr]
    role: str = "member"
    department_ids: Optional[List[int]] = None
    team_ids: Optional[List[int]] = None
    role_ids: Optional[List[int]] = None
    message: Optional[str] = None


class InviteResult(BaseModel):
    success: bool
    email: str
    invite_id: Optional[str] = None
    error: Optional[str] = None


class DepartmentMemberOut(BaseModel):
    user_id: int
    username: str
    name: str
    email: str
    avatar_url: Optional[str]
    role_in_dept: str
    is_primary: bool
    position: Optional[str]
    job_title: Optional[str]
    joined_at: Optional[str]


# ========== Mock 数据 ==========

MOCK_DEPARTMENTS = [
    {
        "dept_id": "dept_root",
        "name": "总经办",
        "description": "公司最高决策层",
        "parent_id": None,
        "path": "/总经办",
        "level": 1,
        "sort_order": 1,
        "status": "active",
        "manager_id": 1,
        "member_count": 5,
        "location": "北京市朝阳区",
        "phone": "010-12345678",
        "email": "ceo@example.com",
        "created_at": "2024-01-01T00:00:00+08:00",
        "updated_at": "2026-01-01T00:00:00+08:00",
    },
    {
        "dept_id": "dept_legal",
        "name": "法务部",
        "description": "负责公司法律事务",
        "parent_id": 1,
        "path": "/总经办/法务部",
        "level": 2,
        "sort_order": 1,
        "status": "active",
        "manager_id": 2,
        "member_count": 15,
        "location": "北京市朝阳区",
        "phone": "010-12345679",
        "email": "legal@example.com",
        "created_at": "2024-02-01T00:00:00+08:00",
        "updated_at": "2026-03-15T00:00:00+08:00",
    },
    {
        "dept_id": "dept_tech",
        "name": "技术部",
        "description": "负责产品研发与技术支持",
        "parent_id": 1,
        "path": "/总经办/技术部",
        "level": 2,
        "sort_order": 2,
        "status": "active",
        "manager_id": 10,
        "member_count": 25,
        "location": "北京市海淀区",
        "phone": "010-12345680",
        "email": "tech@example.com",
        "created_at": "2024-02-15T00:00:00+08:00",
        "updated_at": "2026-05-20T00:00:00+08:00",
    },
    {
        "dept_id": "dept_sales",
        "name": "销售部",
        "description": "负责市场销售与客户关系",
        "parent_id": 1,
        "path": "/总经办/销售部",
        "level": 2,
        "sort_order": 3,
        "status": "active",
        "manager_id": 20,
        "member_count": 20,
        "location": "上海市浦东新区",
        "phone": "021-12345678",
        "email": "sales@example.com",
        "created_at": "2024-03-01T00:00:00+08:00",
        "updated_at": "2026-04-10T00:00:00+08:00",
    },
    {
        "dept_id": "dept_hr",
        "name": "人力资源部",
        "description": "负责招聘、培训与员工关系",
        "parent_id": 1,
        "path": "/总经办/人力资源部",
        "level": 2,
        "sort_order": 4,
        "status": "active",
        "manager_id": 30,
        "member_count": 8,
        "location": "北京市朝阳区",
        "phone": "010-12345681",
        "email": "hr@example.com",
        "created_at": "2024-03-15T00:00:00+08:00",
        "updated_at": "2026-02-28T00:00:00+08:00",
    },
]

MOCK_TEAMS = [
    {
        "team_id": "team_litigation",
        "name": "诉讼团队",
        "description": "专注于诉讼业务",
        "team_type": "practice",
        "status": "active",
        "department_id": 2,
        "leader_id": 3,
        "member_count": 8,
        "max_members": 20,
        "color": "#1890ff",
        "created_at": "2025-01-10T00:00:00+08:00",
        "updated_at": "2026-06-01T00:00:00+08:00",
    },
    {
        "team_id": "team_contract",
        "name": "合同审查团队",
        "description": "专注于合同审查业务",
        "team_type": "practice",
        "status": "active",
        "department_id": 2,
        "leader_id": 4,
        "member_count": 7,
        "max_members": 15,
        "color": "#52c41a",
        "created_at": "2025-02-01T00:00:00+08:00",
        "updated_at": "2026-05-15T00:00:00+08:00",
    },
    {
        "team_id": "team_ai",
        "name": "AI 研发团队",
        "description": "负责 AI 功能研发",
        "team_type": "project",
        "status": "active",
        "department_id": 3,
        "leader_id": 11,
        "member_count": 5,
        "max_members": 10,
        "color": "#722ed1",
        "created_at": "2025-06-01T00:00:00+08:00",
        "updated_at": "2026-06-20T00:00:00+08:00",
    },
    {
        "team_id": "team_product",
        "name": "产品研发团队",
        "description": "负责核心产品研发",
        "team_type": "project",
        "status": "active",
        "department_id": 3,
        "leader_id": 12,
        "member_count": 20,
        "max_members": 30,
        "color": "#fa8c16",
        "created_at": "2024-06-01T00:00:00+08:00",
        "updated_at": "2026-06-25T00:00:00+08:00",
    },
]

MOCK_ROLES = [
    {
        "role_id": "role_owner",
        "name": "组织所有者",
        "description": "拥有组织的全部权限",
        "role_type": "system",
        "is_system": True,
        "is_enabled": True,
        "permissions": ["*"],
        "data_scope": "all",
        "parent_id": None,
        "inherit_parent": False,
        "sort_order": 1,
        "color": "#f5222d",
        "user_count": 1,
        "created_at": "2024-01-01T00:00:00+08:00",
        "updated_at": "2024-01-01T00:00:00+08:00",
    },
    {
        "role_id": "role_admin",
        "name": "管理员",
        "description": "负责组织管理工作",
        "role_type": "system",
        "is_system": True,
        "is_enabled": True,
        "permissions": ["user:*", "department:*", "team:*", "role:*", "system:view", "system:audit", "billing:view"],
        "data_scope": "all",
        "parent_id": None,
        "inherit_parent": False,
        "sort_order": 2,
        "color": "#fa8c16",
        "user_count": 3,
        "created_at": "2024-01-01T00:00:00+08:00",
        "updated_at": "2024-01-01T00:00:00+08:00",
    },
    {
        "role_id": "role_lawyer",
        "name": "律师",
        "description": "法律专业人员",
        "role_type": "system",
        "is_system": True,
        "is_enabled": True,
        "permissions": ["case:view", "case:search", "case:create", "case:update", "contract:view", "contract:review", "document:view", "document:generate", "ai:use"],
        "data_scope": "department",
        "parent_id": None,
        "inherit_parent": False,
        "sort_order": 3,
        "color": "#1890ff",
        "user_count": 10,
        "created_at": "2024-01-01T00:00:00+08:00",
        "updated_at": "2024-01-01T00:00:00+08:00",
    },
    {
        "role_id": "role_paralegal",
        "name": "律师助理",
        "description": "协助律师工作",
        "role_type": "system",
        "is_system": True,
        "is_enabled": True,
        "permissions": ["case:view", "case:search", "document:view", "document:generate", "ai:use"],
        "data_scope": "department",
        "parent_id": None,
        "inherit_parent": False,
        "sort_order": 4,
        "color": "#52c41a",
        "user_count": 5,
        "created_at": "2024-01-01T00:00:00+08:00",
        "updated_at": "2024-01-01T00:00:00+08:00",
    },
    {
        "role_id": "role_guest",
        "name": "访客",
        "description": "只读访问权限",
        "role_type": "system",
        "is_system": True,
        "is_enabled": True,
        "permissions": ["case:view", "case:search"],
        "data_scope": "self",
        "parent_id": None,
        "inherit_parent": False,
        "sort_order": 5,
        "color": "#8c8c8c",
        "user_count": 2,
        "created_at": "2024-01-01T00:00:00+08:00",
        "updated_at": "2024-01-01T00:00:00+08:00",
    },
]

MOCK_MEMBERS = [
    {
        "user_id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "name": "系统管理员",
        "avatar_url": None,
        "status": "active",
        "role": "owner",
        "department_ids": [1],
        "department_names": ["总经办"],
        "team_ids": [],
        "team_names": [],
        "role_ids": [1],
        "position": "CEO",
        "job_title": "首席执行官",
        "join_date": "2024-01-01",
        "last_login_at": "2026-07-03T09:00:00+08:00",
    },
    {
        "user_id": 2,
        "username": "lawyer_zhang",
        "email": "zhang@example.com",
        "name": "张律师",
        "avatar_url": None,
        "status": "active",
        "role": "admin",
        "department_ids": [2],
        "department_names": ["法务部"],
        "team_ids": [1, 2],
        "team_names": ["诉讼团队", "合同审查团队"],
        "role_ids": [2],
        "position": "法务总监",
        "job_title": "高级合伙人",
        "join_date": "2024-02-01",
        "last_login_at": "2026-07-03T08:30:00+08:00",
    },
    {
        "user_id": 3,
        "username": "lawyer_li",
        "email": "li@example.com",
        "name": "李律师",
        "avatar_url": None,
        "status": "active",
        "role": "lawyer",
        "department_ids": [2],
        "department_names": ["法务部"],
        "team_ids": [1],
        "team_names": ["诉讼团队"],
        "role_ids": [3],
        "position": "诉讼组组长",
        "job_title": "合伙人",
        "join_date": "2024-03-15",
        "last_login_at": "2026-07-02T17:45:00+08:00",
    },
    {
        "user_id": 4,
        "username": "lawyer_wang",
        "email": "wang@example.com",
        "name": "王律师",
        "avatar_url": None,
        "status": "active",
        "role": "lawyer",
        "department_ids": [2],
        "department_names": ["法务部"],
        "team_ids": [2],
        "team_names": ["合同审查团队"],
        "role_ids": [3],
        "position": "合同组组长",
        "job_title": "资深律师",
        "join_date": "2024-05-01",
        "last_login_at": "2026-07-03T10:15:00+08:00",
    },
    {
        "user_id": 5,
        "username": "para_chen",
        "email": "chen@example.com",
        "name": "陈助理",
        "avatar_url": None,
        "status": "active",
        "role": "paralegal",
        "department_ids": [2],
        "department_names": ["法务部"],
        "team_ids": [1],
        "team_names": ["诉讼团队"],
        "role_ids": [4],
        "position": "律师助理",
        "job_title": "律师助理",
        "join_date": "2025-01-10",
        "last_login_at": "2026-07-03T09:30:00+08:00",
    },
    {
        "user_id": 10,
        "username": "tech_lead",
        "email": "tech@example.com",
        "name": "技术总监",
        "avatar_url": None,
        "status": "active",
        "role": "admin",
        "department_ids": [3],
        "department_names": ["技术部"],
        "team_ids": [3, 4],
        "team_names": ["AI 研发团队", "产品研发团队"],
        "role_ids": [2],
        "position": "技术总监",
        "job_title": "CTO",
        "join_date": "2024-02-15",
        "last_login_at": "2026-07-02T23:00:00+08:00",
    },
]


# ========== 端点: 部门管理 ==========

@router.get("/departments")
async def list_departments(
    tree: bool = Query(True, description="是否返回树形结构"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    parent_id: Optional[int] = Query(None, description="父部门 ID"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    admin: User = Depends(get_current_admin),
):
    """部门列表 / 部门树"""
    if tree:
        dept_tree = await OrganizationService.get_department_tree("tenant_default")
        return {
            "type": "tree",
            "departments": dept_tree,
        }
    
    filtered = MOCK_DEPARTMENTS
    if status:
        filtered = [d for d in filtered if d["status"] == status]
    if parent_id is not None:
        filtered = [d for d in filtered if d["parent_id"] == parent_id]
    if keyword:
        filtered = [d for d in filtered if keyword.lower() in d["name"].lower()]
    
    return {
        "type": "list",
        "total": len(filtered),
        "departments": [DepartmentOut(**d) for d in filtered],
    }


@router.post("/departments", response_model=DepartmentOut)
async def create_department(
    req: DepartmentCreateRequest,
    admin: User = Depends(get_current_admin),
):
    """创建部门"""
    import uuid
    dept_id = f"dept_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    new_dept = {
        "dept_id": dept_id,
        "name": req.name,
        "description": req.description,
        "parent_id": req.parent_id,
        "path": f"/{req.name}",
        "level": 1 if not req.parent_id else 2,
        "sort_order": req.sort_order,
        "status": "active",
        "manager_id": req.manager_id,
        "member_count": 0,
        "location": req.location,
        "phone": req.phone,
        "email": req.email,
        "created_at": now,
        "updated_at": now,
    }
    
    logger.info(f"[org.dept.create] dept_id={dept_id} name={req.name}")
    return DepartmentOut(**new_dept)


@router.get("/departments/{dept_id}", response_model=DepartmentOut)
async def get_department(
    dept_id: str,
    admin: User = Depends(get_current_admin),
):
    """部门详情"""
    for dept in MOCK_DEPARTMENTS:
        if dept["dept_id"] == dept_id:
            return DepartmentOut(**dept)
    raise HTTPException(404, "部门不存在")


@router.put("/departments/{dept_id}", response_model=DepartmentOut)
async def update_department(
    dept_id: str,
    req: DepartmentUpdateRequest,
    admin: User = Depends(get_current_admin),
):
    """更新部门"""
    for dept in MOCK_DEPARTMENTS:
        if dept["dept_id"] == dept_id:
            update_data = req.model_dump(exclude_unset=True)
            for k, v in update_data.items():
                if v is not None:
                    dept[k] = v
            dept["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"[org.dept.update] dept_id={dept_id}")
            return DepartmentOut(**dept)
    raise HTTPException(404, "部门不存在")


@router.delete("/departments/{dept_id}")
async def delete_department(
    dept_id: str,
    admin: User = Depends(get_current_admin),
):
    """删除部门"""
    for dept in MOCK_DEPARTMENTS:
        if dept["dept_id"] == dept_id:
            logger.info(f"[org.dept.delete] dept_id={dept_id}")
            return {"status": "ok", "message": "部门已删除"}
    raise HTTPException(404, "部门不存在")


@router.get("/departments/{dept_id}/members")
async def get_department_members(
    dept_id: str,
    admin: User = Depends(get_current_admin),
):
    """部门成员列表"""
    members = []
    for m in MOCK_MEMBERS:
        for did in m["department_ids"]:
            target_dept = next((d for d in MOCK_DEPARTMENTS if d["dept_id"] == dept_id), None)
            if target_dept and did == target_dept.get("id"):
                members.append({
                    "user_id": m["user_id"],
                    "username": m["username"],
                    "name": m["name"],
                    "email": m["email"],
                    "avatar_url": m["avatar_url"],
                    "role_in_dept": "member" if m["role"] in ["lawyer", "paralegal"] else m["role"],
                    "is_primary": True,
                    "position": m["position"],
                    "job_title": m["job_title"],
                    "joined_at": m["join_date"],
                })
                break
    
    if not members:
        members = [
            {"user_id": 2, "username": "lawyer_zhang", "name": "张律师", "email": "zhang@example.com", "avatar_url": None, "role_in_dept": "manager", "is_primary": True, "position": "法务总监", "job_title": "高级合伙人", "joined_at": "2024-02-01"},
            {"user_id": 3, "username": "lawyer_li", "name": "李律师", "email": "li@example.com", "avatar_url": None, "role_in_dept": "member", "is_primary": True, "position": "诉讼组组长", "job_title": "合伙人", "joined_at": "2024-03-15"},
            {"user_id": 4, "username": "lawyer_wang", "name": "王律师", "email": "wang@example.com", "avatar_url": None, "role_in_dept": "member", "is_primary": True, "position": "合同组组长", "job_title": "资深律师", "joined_at": "2024-05-01"},
            {"user_id": 5, "username": "para_chen", "name": "陈助理", "email": "chen@example.com", "avatar_url": None, "role_in_dept": "member", "is_primary": True, "position": "律师助理", "job_title": "律师助理", "joined_at": "2025-01-10"},
        ]
    
    return {"total": len(members), "members": members}


# ========== 端点: 团队管理 ==========

@router.get("/teams")
async def list_teams(
    team_type: Optional[str] = Query(None, description="按类型筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    department_id: Optional[int] = Query(None, description="按部门筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    admin: User = Depends(get_current_admin),
):
    """团队列表"""
    filtered = MOCK_TEAMS
    if team_type:
        filtered = [t for t in filtered if t["team_type"] == team_type]
    if status:
        filtered = [t for t in filtered if t["status"] == status]
    if department_id is not None:
        filtered = [t for t in filtered if t["department_id"] == department_id]
    if keyword:
        filtered = [t for t in filtered if keyword.lower() in t["name"].lower()]
    
    return {
        "total": len(filtered),
        "teams": [TeamOut(**t) for t in filtered],
    }


@router.post("/teams", response_model=TeamOut)
async def create_team(
    req: TeamCreateRequest,
    admin: User = Depends(get_current_admin),
):
    """创建团队"""
    import uuid
    team_id = f"team_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    new_team = {
        "team_id": team_id,
        "name": req.name,
        "description": req.description,
        "team_type": req.team_type,
        "status": "active",
        "department_id": req.department_id,
        "leader_id": req.leader_id,
        "member_count": 0,
        "max_members": req.max_members,
        "color": req.color,
        "created_at": now,
        "updated_at": now,
    }
    
    logger.info(f"[org.team.create] team_id={team_id} name={req.name}")
    return TeamOut(**new_team)


@router.get("/teams/{team_id}", response_model=TeamOut)
async def get_team(
    team_id: str,
    admin: User = Depends(get_current_admin),
):
    """团队详情"""
    for team in MOCK_TEAMS:
        if team["team_id"] == team_id:
            return TeamOut(**team)
    raise HTTPException(404, "团队不存在")


@router.put("/teams/{team_id}", response_model=TeamOut)
async def update_team(
    team_id: str,
    req: TeamUpdateRequest,
    admin: User = Depends(get_current_admin),
):
    """更新团队"""
    for team in MOCK_TEAMS:
        if team["team_id"] == team_id:
            update_data = req.model_dump(exclude_unset=True)
            for k, v in update_data.items():
                if v is not None:
                    team[k] = v
            team["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"[org.team.update] team_id={team_id}")
            return TeamOut(**team)
    raise HTTPException(404, "团队不存在")


@router.delete("/teams/{team_id}")
async def delete_team(
    team_id: str,
    admin: User = Depends(get_current_admin),
):
    """删除团队"""
    for team in MOCK_TEAMS:
        if team["team_id"] == team_id:
            logger.info(f"[org.team.delete] team_id={team_id}")
            return {"status": "ok", "message": "团队已删除"}
    raise HTTPException(404, "团队不存在")


@router.get("/teams/{team_id}/members")
async def get_team_members(
    team_id: str,
    admin: User = Depends(get_current_admin),
):
    """团队成员列表"""
    members = [
        {"user_id": 2, "username": "lawyer_zhang", "name": "张律师", "email": "zhang@example.com", "avatar_url": None, "role_in_team": "leader", "joined_at": "2025-01-10T00:00:00+08:00"},
        {"user_id": 3, "username": "lawyer_li", "name": "李律师", "email": "li@example.com", "avatar_url": None, "role_in_team": "member", "joined_at": "2025-01-15T00:00:00+08:00"},
        {"user_id": 4, "username": "lawyer_wang", "name": "王律师", "email": "wang@example.com", "avatar_url": None, "role_in_team": "member", "joined_at": "2025-02-01T00:00:00+08:00"},
        {"user_id": 5, "username": "para_chen", "name": "陈助理", "email": "chen@example.com", "avatar_url": None, "role_in_team": "member", "joined_at": "2025-03-01T00:00:00+08:00"},
    ]
    
    return {"total": len(members), "members": members}


# ========== 端点: 角色权限 ==========

@router.get("/roles")
async def list_roles(
    role_type: Optional[str] = Query(None, description="按类型筛选"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    admin: User = Depends(get_current_admin),
):
    """角色列表"""
    filtered = MOCK_ROLES
    if role_type:
        filtered = [r for r in filtered if r["role_type"] == role_type]
    if is_enabled is not None:
        filtered = [r for r in filtered if r["is_enabled"] == is_enabled]
    if keyword:
        filtered = [r for r in filtered if keyword.lower() in r["name"].lower()]
    
    return {
        "total": len(filtered),
        "roles": [RoleOut(**r) for r in filtered],
    }


@router.post("/roles", response_model=RoleOut)
async def create_role(
    req: RoleCreateRequest,
    admin: User = Depends(get_current_admin),
):
    """创建角色"""
    import uuid
    role_id = f"role_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    new_role = {
        "role_id": role_id,
        "name": req.name,
        "description": req.description,
        "role_type": req.role_type,
        "is_system": False,
        "is_enabled": True,
        "permissions": req.permissions,
        "data_scope": req.data_scope,
        "parent_id": req.parent_id,
        "inherit_parent": req.inherit_parent,
        "sort_order": req.sort_order,
        "color": req.color,
        "user_count": 0,
        "created_at": now,
        "updated_at": now,
    }
    
    logger.info(f"[org.role.create] role_id={role_id} name={req.name}")
    return RoleOut(**new_role)


@router.get("/roles/{role_id}", response_model=RoleOut)
async def get_role(
    role_id: str,
    admin: User = Depends(get_current_admin),
):
    """角色详情"""
    for role in MOCK_ROLES:
        if role["role_id"] == role_id:
            return RoleOut(**role)
    raise HTTPException(404, "角色不存在")


@router.put("/roles/{role_id}", response_model=RoleOut)
async def update_role(
    role_id: str,
    req: RoleUpdateRequest,
    admin: User = Depends(get_current_admin),
):
    """更新角色"""
    for role in MOCK_ROLES:
        if role["role_id"] == role_id:
            update_data = req.model_dump(exclude_unset=True)
            for k, v in update_data.items():
                if v is not None:
                    role[k] = v
            role["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"[org.role.update] role_id={role_id}")
            return RoleOut(**role)
    raise HTTPException(404, "角色不存在")


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    admin: User = Depends(get_current_admin),
):
    """删除角色"""
    for role in MOCK_ROLES:
        if role["role_id"] == role_id:
            if role["is_system"]:
                raise HTTPException(400, "系统角色不可删除")
            logger.info(f"[org.role.delete] role_id={role_id}")
            return {"status": "ok", "message": "角色已删除"}
    raise HTTPException(404, "角色不存在")


@router.get("/permissions")
async def get_permissions(
    admin: User = Depends(get_current_admin),
):
    """获取权限定义列表"""
    return {
        "categories": PermissionDefinition.get_all_permissions(),
    }


# ========== 端点: 成员管理 ==========

@router.get("/members")
async def list_members(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=200, description="每页条数"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    role: Optional[str] = Query(None, description="按角色筛选"),
    department_id: Optional[int] = Query(None, description="按部门筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    admin: User = Depends(get_current_admin),
):
    """成员列表"""
    filtered = MOCK_MEMBERS
    if status:
        filtered = [m for m in filtered if m["status"] == status]
    if role:
        filtered = [m for m in filtered if m["role"] == role]
    if department_id is not None:
        filtered = [m for m in filtered if department_id in m["department_ids"]]
    if keyword:
        filtered = [m for m in filtered if keyword.lower() in m["name"].lower() or keyword.lower() in m["email"].lower() or keyword.lower() in m["username"].lower()]
    
    total = len(filtered)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "members": [MemberOut(**m) for m in filtered[start_idx:end_idx]],
    }


@router.post("/members/invite")
async def invite_members(
    req: InviteMemberRequest,
    admin: User = Depends(get_current_admin),
):
    """邀请成员"""
    results = []
    
    for email in req.emails:
        try:
            invite = await OrganizationService.invite_member(
                tenant_id="tenant_default",
                email=email,
                invited_by=admin.id,
                role=req.role,
                department_ids=req.department_ids,
                team_ids=req.team_ids,
                role_ids=req.role_ids,
                message=req.message,
            )
            results.append(InviteResult(
                success=True,
                email=email,
                invite_id=invite["invite_id"],
            ))
            logger.info(f"[org.invite] email={email} invite_id={invite['invite_id']}")
        except Exception as e:
            results.append(InviteResult(
                success=False,
                email=email,
                error=str(e),
            ))
    
    success_count = sum(1 for r in results if r.success)
    return {
        "total": len(req.emails),
        "success_count": success_count,
        "fail_count": len(req.emails) - success_count,
        "results": results,
    }
