"""
LexPrime SQLAlchemy ORM 模型
2026-06-28 · 对应 db/schema.sql
"""
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import (
    BigInteger, String, Text, Date, DateTime, Boolean, Integer, SmallInteger, Numeric,
    ForeignKey, JSON, UniqueConstraint, Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# ========== 判例库 ==========
class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    doc_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True)
    case_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    case_name: Mapped[Optional[str]] = mapped_column(Text)
    court: Mapped[Optional[str]] = mapped_column(String(256), index=True)
    case_type: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    procedure: Mapped[Optional[str]] = mapped_column(String(64))
    judgment_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    public_date: Mapped[Optional[date]] = mapped_column(Date)
    parties: Mapped[Optional[str]] = mapped_column(Text)
    cause: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    cause_category: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    cause_color: Mapped[Optional[str]] = mapped_column(String(16))
    legal_basis: Mapped[Optional[str]] = mapped_column(Text)
    full_text: Mapped[Optional[str]] = mapped_column(Text)
    full_text_plain: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(32), default="cncases", index=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    region: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    year: Mapped[Optional[int]] = mapped_column(SmallInteger, index=True)
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSON)
    lex_score: Mapped[Optional[int]] = mapped_column(SmallInteger, default=0, index=True)
    lex_tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ========== 法规库 ==========
class Law(Base):
    __tablename__ = "laws"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    law_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    law_number: Mapped[Optional[str]] = mapped_column(String(128))
    law_type: Mapped[str] = mapped_column(String(64), index=True)
    issuing_organ: Mapped[Optional[str]] = mapped_column(String(256))
    issue_date: Mapped[Optional[date]] = mapped_column(Date)
    effective_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    status: Mapped[Optional[str]] = mapped_column(String(32), default="有效")
    summary: Mapped[Optional[str]] = mapped_column(Text)
    full_text: Mapped[Optional[str]] = mapped_column(Text)
    level: Mapped[Optional[int]] = mapped_column(SmallInteger, default=1)
    source: Mapped[Optional[str]] = mapped_column(String(32), default="npc_laws")
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    revised_from: Mapped[Optional[str]] = mapped_column(String(64))
    revised_to: Mapped[Optional[str]] = mapped_column(String(64))
    related_laws: Mapped[Optional[List[str]]] = mapped_column(JSON)
    related_cases_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ========== 企业征信 ==========
class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    unified_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(512), index=True)
    company_type: Mapped[Optional[str]] = mapped_column(String(64))
    legal_rep: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    registered_capital: Mapped[Optional[str]] = mapped_column(String(64))
    paid_capital: Mapped[Optional[str]] = mapped_column(String(64))
    establish_date: Mapped[Optional[date]] = mapped_column(Date)
    business_status: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    registered_address: Mapped[Optional[str]] = mapped_column(String(512))
    business_scope: Mapped[Optional[str]] = mapped_column(Text)
    industry: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    region: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    is_zxgk: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_dishonest: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[Optional[str]] = mapped_column(String(32), default="gsxt")
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ========== 律师自加判例 ==========
class LawyerAddedCase(Base):
    __tablename__ = "lawyer_added_cases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lawyer_id: Mapped[str] = mapped_column(String(64), index=True)
    firm_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    case_id: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(512))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    full_text: Mapped[Optional[str]] = mapped_column(Text)
    cause: Mapped[Optional[str]] = mapped_column(String(128))
    cause_category: Mapped[Optional[str]] = mapped_column(String(64))
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(String(16), default="private")
    related_official_case_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("cases.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ========== 律所 ==========
class Firm(Base):
    __tablename__ = "firms"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), index=True)
    unified_id: Mapped[Optional[str]] = mapped_column(String(64))
    license_no: Mapped[Optional[str]] = mapped_column(String(64))
    region: Mapped[Optional[str]] = mapped_column(String(32))
    address: Mapped[Optional[str]] = mapped_column(String(512))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(32))
    contact_email: Mapped[Optional[str]] = mapped_column(String(128))
    website: Mapped[Optional[str]] = mapped_column(String(256))
    established_date: Mapped[Optional[date]] = mapped_column(Date)
    firm_size: Mapped[str] = mapped_column(String(16), default="small")
    subscription_tier: Mapped[str] = mapped_column(String(16), default="trial", index=True)
    subscription_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lawyers: Mapped[List["Lawyer"]] = relationship(back_populates="firm")


# ========== 律师 ==========
class Lawyer(Base):
    __tablename__ = "lawyers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    firm_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("firms.id"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    license_no: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    role: Mapped[str] = mapped_column(String(16), default="lawyer", index=True)
    specialties: Mapped[Optional[List[str]]] = mapped_column(JSON)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    firm: Mapped[Optional["Firm"]] = relationship(back_populates="lawyers")


# ========== 律所案件分配 ==========
class FirmCaseAssignment(Base):
    __tablename__ = "firm_case_assignments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    firm_id: Mapped[str] = mapped_column(String(64), ForeignKey("firms.id"), index=True)
    case_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True)
    case_title: Mapped[str] = mapped_column(String(512))
    lawyer_id: Mapped[str] = mapped_column(String(64), ForeignKey("lawyers.id"), index=True)
    role: Mapped[str] = mapped_column(String(16), default="lead")
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("case_id", "lawyer_id", name="uq_case_lawyer"),)


# ========== 工时记录 ==========
class FirmTimeEntry(Base):
    __tablename__ = "firm_time_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    firm_id: Mapped[str] = mapped_column(String(64), ForeignKey("firms.id"), index=True)
    lawyer_id: Mapped[str] = mapped_column(String(64), ForeignKey("lawyers.id"), index=True)
    case_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    entry_date: Mapped[date] = mapped_column(Date, index=True)
    hours: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    description: Mapped[Optional[str]] = mapped_column(Text)
    billable: Mapped[bool] = mapped_column(Boolean, default=True)
    rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ========== 收藏 ==========
class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lawyer_id: Mapped[str] = mapped_column(String(64), index=True)
    target_type: Mapped[str] = mapped_column(String(16))
    target_id: Mapped[str] = mapped_column(String(64), index=True)
    note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("lawyer_id", "target_type", "target_id", name="uq_favorite"),)


# ========== 爬虫运行日志 ==========
class CrawlerRun(Base):
    __tablename__ = "crawler_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source: Mapped[str] = mapped_column(String(32), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="running", index=True)
    items_total: Mapped[int] = mapped_column(Integer, default=0)
    items_inserted: Mapped[int] = mapped_column(Integer, default=0)
    items_updated: Mapped[int] = mapped_column(Integer, default=0)
    items_failed: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[Optional[str]] = mapped_column(Text)
    config: Mapped[Optional[dict]] = mapped_column(JSON)
