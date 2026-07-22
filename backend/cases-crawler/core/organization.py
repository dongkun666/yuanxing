"""
LexPrime 组织架构系统
2026-07-03 · 企业级能力建设

功能模块:
- 部门管理 - Department 模型 / 部门树 / 成员管理 / 部门权限
- 团队管理 - Team 模型 / 团队成员 / 团队项目 / 团队设置
- 角色权限 - Role 模型 / 权限定义 / 角色分配 / 权限继承
- 用户管理 - 用户列表 / 用户状态 / 用户分组 / 批量操作
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import (
    String, Text, DateTime, Boolean, Integer,
    ForeignKey, JSON, Index, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.models import Base


class OrgMemberRole(str, Enum):
    """组织成员角色"""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    GUEST = "guest"


class DepartmentStatus(str, Enum):
    """部门状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class TeamStatus(str, Enum):
    """团队状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


# ========== Department (部门) ==========
class Department(Base):
    """
    部门表

    支持树形层级结构, 每个部门可以有父部门。
    """
    __tablename__ = "org_departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dept_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(512))

    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("org_departments.id"), index=True)
    path: Mapped[Optional[str]] = mapped_column(String(512), index=True)
    level: Mapped[int] = mapped_column(Integer, default=1, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[str] = mapped_column(String(16), default=DepartmentStatus.ACTIVE.value, index=True, nullable=False)

    manager_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    deputy_manager_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)

    location: Mapped[Optional[str]] = mapped_column(String(256))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    email: Mapped[Optional[str]] = mapped_column(String(128))

    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    permissions: Mapped[Optional[List[str]]] = mapped_column(JSON)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    parent: Mapped[Optional["Department"]] = relationship(
        "Department", remote_side="Department.id", back_populates="children"
    )
    children: Mapped[List["Department"]] = relationship(
        "Department", back_populates="parent", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_dept_tenant_status", "tenant_id", "status"),
        Index("idx_dept_tenant_parent", "tenant_id", "parent_id"),
        Index("idx_dept_tenant_level", "tenant_id", "level"),
    )


# ========== Team (团队) ==========
class Team(Base):
    """
    团队表

    团队是跨部门的协作单元, 用于项目组、工作组等场景。
    """
    __tablename__ = "org_teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("org_departments.id"), index=True)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(512))
    team_type: Mapped[str] = mapped_column(String(32), default="project", index=True)

    status: Mapped[str] = mapped_column(String(16), default=TeamStatus.ACTIVE.value, index=True, nullable=False)

    leader_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    max_members: Mapped[Optional[int]] = mapped_column(Integer)

    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(String(16))

    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    permissions: Mapped[Optional[List[str]]] = mapped_column(JSON)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_team_tenant_status", "tenant_id", "status"),
        Index("idx_team_tenant_dept", "tenant_id", "department_id"),
        Index("idx_team_tenant_type", "tenant_id", "team_type"),
    )


# ========== Role (角色) ==========
class Role(Base):
    """
    角色表

    定义系统中的角色及其权限集合。
    """
    __tablename__ = "org_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(256))
    role_type: Mapped[str] = mapped_column(String(32), default="custom", index=True)

    is_system: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    permissions: Mapped[Optional[List[str]]] = mapped_column(JSON)
    data_scope: Mapped[str] = mapped_column(String(32), default="all", index=True)

    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("org_roles.id"), index=True)
    inherit_parent: Mapped[bool] = mapped_column(Boolean, default=False)

    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[Optional[str]] = mapped_column(String(16))

    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    parent: Mapped[Optional["Role"]] = relationship(
        "Role", remote_side="Role.id", back_populates="children"
    )
    children: Mapped[List["Role"]] = relationship(
        "Role", back_populates="parent"
    )

    __table_args__ = (
        Index("idx_role_tenant_enabled", "tenant_id", "is_enabled"),
        Index("idx_role_tenant_type", "tenant_id", "role_type"),
        UniqueConstraint("tenant_id", "name", name="uq_role_tenant_name"),
    )


# ========== DepartmentMember (部门成员) ==========
class DepartmentMember(Base):
    """
    部门成员表

    关联用户与部门的关系。
    """
    __tablename__ = "org_department_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("org_departments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    role_in_dept: Mapped[str] = mapped_column(String(32), default="member", index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    position: Mapped[Optional[str]] = mapped_column(String(64))
    job_title: Mapped[Optional[str]] = mapped_column(String(64))

    permissions: Mapped[Optional[List[str]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("department_id", "user_id", name="uq_dept_member"),
        Index("idx_dept_member_tenant", "tenant_id"),
        Index("idx_dept_member_user", "user_id"),
    )


# ========== TeamMember (团队成员) ==========
class TeamMember(Base):
    """
    团队成员表

    关联用户与团队的关系。
    """
    __tablename__ = "org_team_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("org_teams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    role_in_team: Mapped[str] = mapped_column(String(32), default="member", index=True)
    joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    permissions: Mapped[Optional[List[str]]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_member"),
        Index("idx_team_member_tenant", "tenant_id"),
        Index("idx_team_member_user", "user_id"),
    )


# ========== UserRole (用户角色分配) ==========
class UserRole(Base):
    """
    用户角色分配表

    为用户分配角色, 支持多角色。
    """
    __tablename__ = "org_user_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("org_roles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    assigned_by: Mapped[Optional[int]] = mapped_column(Integer)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    scope: Mapped[str] = mapped_column(String(32), default="global", index=True)
    scope_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)

    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "tenant_id", "scope", "scope_id", name="uq_user_role"),
        Index("idx_user_role_tenant", "tenant_id"),
        Index("idx_user_role_role", "role_id"),
    )


# ========== Invitation (邀请) ==========
class OrgInvitation(Base):
    """
    组织邀请表

    记录邀请加入组织的邮件/链接。
    """
    __tablename__ = "org_invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invite_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    email: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True, nullable=False)

    invited_by: Mapped[int] = mapped_column(Integer, nullable=False)
    invited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    default_role: Mapped[str] = mapped_column(String(32), default="member")
    department_ids: Mapped[Optional[List[int]]] = mapped_column(JSON)
    team_ids: Mapped[Optional[List[int]]] = mapped_column(JSON)
    role_ids: Mapped[Optional[List[int]]] = mapped_column(JSON)

    message: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("idx_invite_tenant_status", "tenant_id", "status"),
        Index("idx_invite_email", "email"),
        Index("idx_invite_expires", "expires_at"),
    )


# ========== Permission (权限定义) ==========
class PermissionDefinition:
    """
    权限定义 - 框架性实现

    定义系统中的所有权限点。
    """

    # 系统权限
    SYSTEM_VIEW = "system:view"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_AUDIT = "system:audit"

    # 用户管理
    USER_VIEW = "user:view"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_INVITE = "user:invite"

    # 部门管理
    DEPT_VIEW = "department:view"
    DEPT_CREATE = "department:create"
    DEPT_UPDATE = "department:update"
    DEPT_DELETE = "department:delete"

    # 团队管理
    TEAM_VIEW = "team:view"
    TEAM_CREATE = "team:create"
    TEAM_UPDATE = "team:update"
    TEAM_DELETE = "team:delete"

    # 角色权限
    ROLE_VIEW = "role:view"
    ROLE_CREATE = "role:create"
    ROLE_UPDATE = "role:update"
    ROLE_DELETE = "role:delete"
    ROLE_ASSIGN = "role:assign"

    # 案例库
    CASE_VIEW = "case:view"
    CASE_CREATE = "case:create"
    CASE_UPDATE = "case:update"
    CASE_DELETE = "case:delete"
    CASE_EXPORT = "case:export"

    # 合同审查
    CONTRACT_VIEW = "contract:view"
    CONTRACT_REVIEW = "contract:review"
    CONTRACT_EXPORT = "contract:export"

    # 文档生成
    DOC_VIEW = "document:view"
    DOC_GENERATE = "document:generate"
    DOC_EXPORT = "document:export"

    # AI 服务
    AI_USE = "ai:use"
    AI_ADVANCED = "ai:advanced"

    # 数据管理
    DATA_IMPORT = "data:import"
    DATA_EXPORT = "data:export"
    DATA_BACKUP = "data:backup"

    # 账单/订阅
    BILLING_VIEW = "billing:view"
    BILLING_MANAGE = "billing:manage"

    # SSO
    SSO_MANAGE = "sso:manage"

    @classmethod
    def get_all_permissions(cls) -> Dict[str, Dict[str, List[str]]]:
        """获取所有权限的分类结构"""
        return {
            "系统管理": {
                "system:view": "查看系统信息",
                "system:config": "系统配置",
                "system:audit": "审计日志查看",
            },
            "用户管理": {
                "user:view": "查看用户",
                "user:create": "创建用户",
                "user:update": "更新用户",
                "user:delete": "删除用户",
                "user:invite": "邀请用户",
            },
            "组织架构": {
                "department:view": "查看部门",
                "department:create": "创建部门",
                "department:update": "更新部门",
                "department:delete": "删除部门",
                "team:view": "查看团队",
                "team:create": "创建团队",
                "team:update": "更新团队",
                "team:delete": "删除团队",
            },
            "角色权限": {
                "role:view": "查看角色",
                "role:create": "创建角色",
                "role:update": "更新角色",
                "role:delete": "删除角色",
                "role:assign": "分配角色",
            },
            "案例库": {
                "case:view": "查看案例",
                "case:create": "创建案例",
                "case:update": "更新案例",
                "case:delete": "删除案例",
                "case:export": "导出案例",
            },
            "合同审查": {
                "contract:view": "查看合同",
                "contract:review": "合同审查",
                "contract:export": "导出合同",
            },
            "文档生成": {
                "document:view": "查看文档",
                "document:generate": "生成文档",
                "document:export": "导岀文档",
            },
            "AI 服务": {
                "ai:use": "基础 AI 功能",
                "ai:advanced": "高级 AI 功能",
            },
            "数据管理": {
                "data:import": "数据导入",
                "data:export": "数据导出",
                "data:backup": "数据备份",
            },
            "账单订阅": {
                "billing:view": "查看账单",
                "billing:manage": "管理订阅",
            },
        }


# ========== OrganizationService (组织架构服务 - 框架性实现) ==========
class OrganizationService:
    """
    组织架构服务 - 框架性实现

    提供部门、团队、角色、成员的管理功能。
    """

    @staticmethod
    def generate_dept_id() -> str:
        import uuid
        return f"dept_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def generate_team_id() -> str:
        import uuid
        return f"team_{uuid.uuid4().hex[:12]}"

    @staticmethod
    def generate_role_id() -> str:
        import uuid
        return f"role_{uuid.uuid4().hex[:12]}"

    @staticmethod
    async def get_department_tree(tenant_id: str) -> List[dict]:
        """
        获取部门树 - 框架性实现
        """
        return [
            {
                "dept_id": "dept_root",
                "name": "总经办",
                "level": 1,
                "member_count": 5,
                "children": [
                    {
                        "dept_id": "dept_legal",
                        "name": "法务部",
                        "level": 2,
                        "member_count": 15,
                        "children": [
                            {"dept_id": "dept_litigation", "name": "诉讼组", "level": 3, "member_count": 8, "children": []},
                            {"dept_id": "dept_contract", "name": "合同组", "level": 3, "member_count": 7, "children": []},
                        ],
                    },
                    {
                        "dept_id": "dept_tech",
                        "name": "技术部",
                        "level": 2,
                        "member_count": 25,
                        "children": [
                            {"dept_id": "dept_frontend", "name": "前端组", "level": 3, "member_count": 10, "children": []},
                            {"dept_id": "dept_backend", "name": "后端组", "level": 3, "member_count": 10, "children": []},
                            {"dept_id": "dept_ai", "name": "AI 组", "level": 3, "member_count": 5, "children": []},
                        ],
                    },
                    {
                        "dept_id": "dept_sales",
                        "name": "销售部",
                        "level": 2,
                        "member_count": 20,
                        "children": [],
                    },
                    {
                        "dept_id": "dept_hr",
                        "name": "人力资源部",
                        "level": 2,
                        "member_count": 8,
                        "children": [],
                    },
                ],
            },
        ]

    @staticmethod
    async def get_user_permissions(user_id: int, tenant_id: str) -> List[str]:
        """
        获取用户的所有权限 - 框架性实现
        """
        return [
            "case:view",
            "case:search",
            "contract:view",
            "contract:review",
            "document:view",
            "document:generate",
            "ai:use",
            "user:view",
            "team:view",
            "department:view",
        ]

    @staticmethod
    async def check_permission(user_id: int, tenant_id: str, permission: str) -> bool:
        """
        检查用户是否有指定权限 - 框架性实现
        """
        perms = await OrganizationService.get_user_permissions(user_id, tenant_id)
        return permission in perms or "*" in perms

    @staticmethod
    async def invite_member(
        tenant_id: str,
        email: str,
        invited_by: int,
        role: str = "member",
        department_ids: Optional[List[int]] = None,
        team_ids: Optional[List[int]] = None,
        role_ids: Optional[List[int]] = None,
        message: Optional[str] = None,
    ) -> dict:
        """
        邀请成员加入组织 - 框架性实现
        """
        import uuid
        from datetime import timedelta

        invite_id = f"inv_{uuid.uuid4().hex[:16]}"
        expires_at = datetime.utcnow() + timedelta(days=7)

        return {
            "invite_id": invite_id,
            "email": email,
            "status": "pending",
            "expires_at": expires_at.isoformat(),
            "invite_link": f"/invite/{invite_id}",
        }
