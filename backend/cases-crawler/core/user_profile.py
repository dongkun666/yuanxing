"""
LexPrime 用户画像系统
提供用户行为收集、兴趣标签提取、用户分层、使用频率分析和功能偏好分析

主要功能:
- 用户行为收集：记录用户的各种操作行为
- 兴趣标签提取：从行为数据中提取用户兴趣标签
- 用户分层：根据活跃度将用户分为新手/活跃/资深
- 使用频率分析：分析用户的使用频率和习惯
- 功能偏好分析：分析用户对各功能的使用偏好
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum
from collections import defaultdict, Counter
from loguru import logger
from pydantic import BaseModel, Field


# ============================================================================
# 枚举定义
# ============================================================================

class UserTier(str, Enum):
    """用户分层"""
    NEWBIE = "newbie"
    ACTIVE = "active"
    EXPERT = "expert"


class BehaviorType(str, Enum):
    """行为类型"""
    PAGE_VIEW = "page_view"
    SEARCH = "search"
    CASE_VIEW = "case_view"
    CASE_FAVORITE = "case_favorite"
    LAW_VIEW = "law_view"
    COMPANY_VIEW = "company_view"
    CONTRACT_REVIEW = "contract_review"
    DOC_GENERATE = "doc_generate"
    AI_CHAT = "ai_chat"
    SCHEDULE_CREATE = "schedule_create"
    CLIENT_CREATE = "client_create"
    LOGIN = "login"
    LOGOUT = "logout"
    SUBSCRIPTION_UPGRADE = "subscription_upgrade"
    SETTINGS_CHANGE = "settings_change"


class FeatureType(str, Enum):
    """功能类型"""
    CASE_SEARCH = "case_search"
    LAW_SEARCH = "law_search"
    COMPANY_SEARCH = "company_search"
    CONTRACT_REVIEW = "contract_review"
    DOC_GENERATION = "doc_generation"
    AI_CONSULTATION = "ai_consultation"
    SCHEDULE_MANAGEMENT = "schedule_management"
    CLIENT_MANAGEMENT = "client_management"
    CASE_MANAGEMENT = "case_management"
    KNOWLEDGE_BASE = "knowledge_base"
    MARKETPLACE = "marketplace"
    ANALYTICS = "analytics"


# ============================================================================
# Pydantic 模型
# ============================================================================

class UserBehavior(BaseModel):
    """用户行为记录"""
    id: str = Field(..., description="行为记录ID")
    user_id: str = Field(..., description="用户ID")
    behavior_type: BehaviorType = Field(..., description="行为类型")
    feature: Optional[FeatureType] = Field(None, description="关联功能")
    page: Optional[str] = Field(None, description="页面路径")
    search_query: Optional[str] = Field(None, description="搜索关键词")
    target_id: Optional[str] = Field(None, description="目标对象ID")
    target_type: Optional[str] = Field(None, description="目标对象类型")
    duration_seconds: Optional[int] = Field(None, description="停留时长(秒)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="行为时间")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserInterestTag(BaseModel):
    """用户兴趣标签"""
    tag: str = Field(..., description="标签名称")
    weight: float = Field(0.0, description="标签权重 0-1")
    count: int = Field(0, description="关联次数")
    category: Optional[str] = Field(None, description="标签分类")
    last_updated: datetime = Field(default_factory=datetime.now)


class UserProfile(BaseModel):
    """用户画像"""
    user_id: str = Field(..., description="用户ID")
    tier: UserTier = Field(UserTier.NEWBIE, description="用户分层")
    total_logins: int = Field(0, description="总登录次数")
    total_sessions: int = Field(0, description="总会话数")
    last_active: Optional[datetime] = Field(None, description="最后活跃时间")
    registration_date: Optional[datetime] = Field(None, description="注册时间")
    days_active: int = Field(0, description="活跃天数")
    avg_session_duration: float = Field(0.0, description="平均会话时长(分钟)")
    interest_tags: List[UserInterestTag] = Field(default_factory=list, description="兴趣标签")
    feature_usage: Dict[str, float] = Field(default_factory=dict, description="功能使用频率")
    usage_frequency: Dict[str, int] = Field(default_factory=dict, description="使用频率分布")
    preferred_categories: List[str] = Field(default_factory=list, description="偏好分类")
    behavior_summary: Dict[str, int] = Field(default_factory=dict, description="行为统计摘要")
    calculated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class UserProfileStats(BaseModel):
    """用户画像统计"""
    total_users: int = Field(0, description="总用户数")
    newbie_users: int = Field(0, description="新手用户数")
    active_users: int = Field(0, description="活跃用户数")
    expert_users: int = Field(0, description="资深用户数")
    avg_days_active: float = Field(0.0, description="平均活跃天数")
    top_features: List[Dict[str, Any]] = Field(default_factory=list, description="热门功能排行")
    top_interest_tags: List[Dict[str, Any]] = Field(default_factory=list, description="热门兴趣标签")


# ============================================================================
# 用户画像引擎
# ============================================================================

class UserProfileEngine:
    """用户画像引擎 - 核心实现"""

    _behaviors: Dict[str, List[UserBehavior]] = defaultdict(list)
    _profiles: Dict[str, UserProfile] = {}

    @classmethod
    def record_behavior(
        cls,
        user_id: str,
        behavior_type: BehaviorType,
        feature: Optional[FeatureType] = None,
        page: Optional[str] = None,
        search_query: Optional[str] = None,
        target_id: Optional[str] = None,
        target_type: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserBehavior:
        """记录用户行为"""
        behavior_id = f"beh-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(cls._behaviors[user_id])}"
        behavior = UserBehavior(
            id=behavior_id,
            user_id=user_id,
            behavior_type=behavior_type,
            feature=feature,
            page=page,
            search_query=search_query,
            target_id=target_id,
            target_type=target_type,
            duration_seconds=duration_seconds,
            metadata=metadata or {}
        )

        cls._behaviors[user_id].append(behavior)

        profile = cls._profiles.get(user_id)
        if profile:
            profile.last_active = datetime.now()

        logger.debug(f"记录用户行为: {user_id} - {behavior_type.value}")
        return behavior

    @classmethod
    def get_user_behaviors(
        cls,
        user_id: str,
        behavior_type: Optional[BehaviorType] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[UserBehavior]:
        """获取用户行为记录"""
        behaviors = cls._behaviors.get(user_id, [])

        if behavior_type:
            behaviors = [b for b in behaviors if b.behavior_type == behavior_type]

        if days:
            cutoff = datetime.now() - timedelta(days=days)
            behaviors = [b for b in behaviors if b.timestamp >= cutoff]

        if limit:
            behaviors = behaviors[-limit:]

        return behaviors

    @classmethod
    def calculate_user_profile(cls, user_id: str) -> UserProfile:
        """计算用户画像"""
        behaviors = cls._behaviors.get(user_id, [])
        profile = UserProfile(user_id=user_id)

        if not behaviors:
            cls._profiles[user_id] = profile
            return profile

        profile.behavior_summary = cls._calculate_behavior_summary(behaviors)
        profile.total_logins = profile.behavior_summary.get(BehaviorType.LOGIN.value, 0)
        profile.total_sessions = max(profile.total_logins, 1)

        login_behaviors = [b for b in behaviors if b.behavior_type == BehaviorType.LOGIN]
        if login_behaviors:
            profile.registration_date = login_behaviors[0].timestamp
            profile.last_active = login_behaviors[-1].timestamp

            active_days = set()
            for b in login_behaviors:
                active_days.add(b.timestamp.date())
            profile.days_active = len(active_days)

        profile.interest_tags = cls._extract_interest_tags(behaviors)
        profile.feature_usage = cls._calculate_feature_usage(behaviors)
        profile.usage_frequency = cls._calculate_usage_frequency(behaviors)
        profile.preferred_categories = cls._extract_preferred_categories(behaviors)
        profile.tier = cls._determine_user_tier(profile)
        profile.calculated_at = datetime.now()

        cls._profiles[user_id] = profile
        logger.info(f"用户画像已更新: {user_id} ({profile.tier.value})")
        return profile

    @classmethod
    def get_user_profile(cls, user_id: str) -> Optional[UserProfile]:
        """获取用户画像"""
        profile = cls._profiles.get(user_id)
        if not profile:
            return cls.calculate_user_profile(user_id)
        return profile

    @classmethod
    def _calculate_behavior_summary(cls, behaviors: List[UserBehavior]) -> Dict[str, int]:
        """计算行为统计摘要"""
        summary: Dict[str, int] = defaultdict(int)
        for behavior in behaviors:
            summary[behavior.behavior_type.value] += 1
        return dict(summary)

    @classmethod
    def _extract_interest_tags(cls, behaviors: List[UserBehavior]) -> List[UserInterestTag]:
        """提取兴趣标签"""
        tag_counter: Counter = Counter()
        tag_metadata: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"category": None, "count": 0})

        for behavior in behaviors:
            if behavior.behavior_type == BehaviorType.SEARCH and behavior.search_query:
                query = behavior.search_query.strip()
                if query:
                    tag_counter[query] += 1
                    tag_metadata[query]["count"] += 1
                    tag_metadata[query]["category"] = "搜索关键词"

            if behavior.behavior_type == BehaviorType.CASE_VIEW:
                cause = behavior.metadata.get("cause")
                cause_category = behavior.metadata.get("cause_category")
                if cause:
                    tag_counter[cause] += 2
                    tag_metadata[cause]["count"] += 1
                    tag_metadata[cause]["category"] = cause_category or "案由"

            if behavior.behavior_type == BehaviorType.CASE_FAVORITE:
                cause = behavior.metadata.get("cause")
                cause_category = behavior.metadata.get("cause_category")
                if cause:
                    tag_counter[cause] += 3
                    tag_metadata[cause]["count"] += 1
                    tag_metadata[cause]["category"] = cause_category or "案由"

            if behavior.feature:
                feature_name = behavior.feature.value
                tag_counter[feature_name] += 1
                tag_metadata[feature_name]["count"] += 1
                tag_metadata[feature_name]["category"] = "功能"

        if not tag_counter:
            return []

        max_count = max(tag_counter.values()) if tag_counter else 1
        tags = []
        for tag, count in tag_counter.most_common(20):
            weight = min(count / max_count, 1.0)
            tags.append(UserInterestTag(
                tag=tag,
                weight=round(weight, 2),
                count=tag_metadata[tag]["count"],
                category=tag_metadata[tag]["category"]
            ))

        return tags

    @classmethod
    def _calculate_feature_usage(cls, behaviors: List[UserBehavior]) -> Dict[str, float]:
        """计算功能使用频率"""
        feature_counts: Dict[str, int] = defaultdict(int)
        total_actions = 0

        for behavior in behaviors:
            if behavior.feature:
                feature_counts[behavior.feature.value] += 1
                total_actions += 1

        if total_actions == 0:
            return {}

        feature_usage = {}
        for feature, count in feature_counts.items():
            feature_usage[feature] = round(count / total_actions * 100, 1)

        return dict(sorted(feature_usage.items(), key=lambda x: x[1], reverse=True))

    @classmethod
    def _calculate_usage_frequency(cls, behaviors: List[UserBehavior]) -> Dict[str, int]:
        """计算使用频率分布"""
        hour_distribution: Dict[int, int] = defaultdict(int)
        weekday_distribution: Dict[str, int] = defaultdict(int)

        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for behavior in behaviors:
            hour = behavior.timestamp.hour
            hour_distribution[hour] += 1

            weekday = behavior.timestamp.weekday()
            weekday_distribution[weekday_names[weekday]] += 1

        frequency = {
            "hour_" + str(h): hour_distribution.get(h, 0)
            for h in range(24)
        }
        for day in weekday_names:
            frequency[day] = weekday_distribution.get(day, 0)

        return frequency

    @classmethod
    def _extract_preferred_categories(cls, behaviors: List[UserBehavior]) -> List[str]:
        """提取偏好分类"""
        category_counts: Dict[str, int] = defaultdict(int)

        for behavior in behaviors:
            cause_category = behavior.metadata.get("cause_category")
            if cause_category:
                if behavior.behavior_type == BehaviorType.CASE_VIEW:
                    category_counts[cause_category] += 1
                elif behavior.behavior_type == BehaviorType.CASE_FAVORITE:
                    category_counts[cause_category] += 2

            if behavior.feature:
                category_counts[behavior.feature.value] += 1

        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        return [cat for cat, _ in sorted_categories[:10]]

    @classmethod
    def _determine_user_tier(cls, profile: UserProfile) -> UserTier:
        """确定用户分层"""
        score = 0

        score += min(profile.days_active * 2, 40)
        score += min(profile.total_logins, 30)

        feature_count = len(profile.feature_usage)
        score += min(feature_count * 5, 20)

        avg_weight = 0
        if profile.interest_tags:
            avg_weight = sum(t.weight for t in profile.interest_tags) / len(profile.interest_tags)
        score += int(avg_weight * 10)

        if score >= 60:
            return UserTier.EXPERT
        elif score >= 25:
            return UserTier.ACTIVE
        else:
            return UserTier.NEWBIE

    @classmethod
    def get_profile_stats(cls) -> UserProfileStats:
        """获取用户画像统计"""
        stats = UserProfileStats()
        profiles = list(cls._profiles.values())

        stats.total_users = len(profiles)
        stats.newbie_users = sum(1 for p in profiles if p.tier == UserTier.NEWBIE)
        stats.active_users = sum(1 for p in profiles if p.tier == UserTier.ACTIVE)
        stats.expert_users = sum(1 for p in profiles if p.tier == UserTier.EXPERT)

        if profiles:
            stats.avg_days_active = round(
                sum(p.days_active for p in profiles) / len(profiles), 1
            )

        all_features: Dict[str, float] = defaultdict(float)
        for profile in profiles:
            for feature, usage in profile.feature_usage.items():
                all_features[feature] += usage

        sorted_features = sorted(all_features.items(), key=lambda x: x[1], reverse=True)
        stats.top_features = [
            {"feature": f, "usage": round(u, 1)}
            for f, u in sorted_features[:10]
        ]

        all_tags: Dict[str, float] = defaultdict(float)
        for profile in profiles:
            for tag in profile.interest_tags:
                all_tags[tag.tag] += tag.weight

        sorted_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)
        stats.top_interest_tags = [
            {"tag": t, "weight": round(w, 2)}
            for t, w in sorted_tags[:10]
        ]

        return stats

    @classmethod
    def export_profile_data(cls, user_id: str, format: str = "json") -> Dict[str, Any]:
        """导出用户画像数据"""
        profile = cls.get_user_profile(user_id)
        if not profile:
            return {}

        behaviors = cls.get_user_behaviors(user_id)

        return {
            "profile": json.loads(profile.json()),
            "behaviors_count": len(behaviors),
            "exported_at": datetime.now().isoformat(),
            "format": format
        }

    @classmethod
    def get_recommendations(cls, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """基于用户画像生成推荐"""
        profile = cls.get_user_profile(user_id)
        if not profile:
            return []

        recommendations = []
        for tag in profile.interest_tags[:5]:
            recommendations.append({
                "type": "case_category",
                "title": f"{tag.tag}相关案件",
                "reason": f"基于您的兴趣标签：{tag.tag}",
                "confidence": tag.weight
            })

        for feature, usage in list(profile.feature_usage.items())[:3]:
            if usage > 20:
                recommendations.append({
                    "type": "feature_tip",
                    "title": f"{feature} 使用技巧",
                    "reason": f"您经常使用{feature}功能",
                    "confidence": usage / 100
                })

        return recommendations[:limit]


# ============================================================================
# 初始化
# ============================================================================

def init_user_profile_engine() -> None:
    """初始化用户画像引擎"""
    logger.info("用户画像引擎初始化完成")
