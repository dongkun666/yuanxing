"""
LexPrime 工作流引擎
提供工作流定义、状态机管理、流程追踪和自动流转功能

主要功能:
- 工作流定义：定义各种业务流程的状态和转换规则
- 状态机管理：管理实体的状态转换和验证
- 流程追踪：记录流程历史和审计日志
- 自动流转：根据条件自动触发状态转换
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from loguru import logger
from pydantic import BaseModel, Field


# ============================================================================
# 枚举定义
# ============================================================================

class WorkflowType(str, Enum):
    """工作流类型"""
    CASE_LIFECYCLE = "case_lifecycle"
    CONTRACT_REVIEW = "contract_review"
    DOC_GENERATION = "doc_generation"
    CLIENT_ONBOARDING = "client_onboarding"
    TASK_FLOW = "task_flow"


class WorkflowStatus(str, Enum):
    """工作流状态"""
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TransitionType(str, Enum):
    """转换类型"""
    MANUAL = "manual"
    AUTO = "auto"
    APPROVAL = "approval"
    TIMER = "timer"


# ============================================================================
# Pydantic 模型
# ============================================================================

class WorkflowState(BaseModel):
    """工作流状态定义"""
    name: str = Field(..., description="状态名称")
    label: str = Field(..., description="显示标签")
    description: Optional[str] = Field(None, description="状态描述")
    color: Optional[str] = Field(None, description="状态颜色")
    is_initial: bool = Field(False, description="是否初始状态")
    is_final: bool = Field(False, description="是否终态")
    entry_actions: List[str] = Field(default_factory=list, description="进入状态时执行的动作")
    exit_actions: List[str] = Field(default_factory=list, description="离开状态时执行的动作")


class WorkflowTransition(BaseModel):
    """工作流转换定义"""
    name: str = Field(..., description="转换名称")
    from_state: str = Field(..., description="起始状态")
    to_state: str = Field(..., description="目标状态")
    label: Optional[str] = Field(None, description="显示标签")
    transition_type: TransitionType = Field(TransitionType.MANUAL, description="转换类型")
    condition: Optional[str] = Field(None, description="自动转换条件表达式")
    required_roles: List[str] = Field(default_factory=list, description="执行所需角色")
    trigger_event: Optional[str] = Field(None, description="触发事件")
    actions: List[str] = Field(default_factory=list, description="转换时执行的动作")


class WorkflowDefinition(BaseModel):
    """工作流定义"""
    id: str = Field(..., description="工作流定义ID")
    name: str = Field(..., description="工作流名称")
    type: WorkflowType = Field(..., description="工作流类型")
    version: str = Field("1.0", description="版本号")
    description: Optional[str] = Field(None, description="描述")
    states: List[WorkflowState] = Field(default_factory=list, description="状态列表")
    transitions: List[WorkflowTransition] = Field(default_factory=list, description="转换列表")
    initial_state: Optional[str] = Field(None, description="初始状态名称")
    final_states: List[str] = Field(default_factory=list, description="终态名称列表")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class WorkflowInstance(BaseModel):
    """工作流实例"""
    id: str = Field(..., description="工作流实例ID")
    definition_id: str = Field(..., description="工作流定义ID")
    entity_type: str = Field(..., description="关联实体类型")
    entity_id: str = Field(..., description="关联实体ID")
    current_state: str = Field(..., description="当前状态")
    status: WorkflowStatus = Field(WorkflowStatus.IN_PROGRESS, description="工作流状态")
    started_by: Optional[str] = Field(None, description="启动者")
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    context: Dict[str, Any] = Field(default_factory=dict, description="上下文数据")
    history: List["WorkflowHistoryEntry"] = Field(default_factory=list, description="历史记录")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class WorkflowHistoryEntry(BaseModel):
    """工作流历史记录条目"""
    id: str = Field(..., description="记录ID")
    instance_id: str = Field(..., description="工作流实例ID")
    from_state: Optional[str] = Field(None, description="起始状态")
    to_state: str = Field(..., description="目标状态")
    transition: Optional[str] = Field(None, description="转换名称")
    actor: Optional[str] = Field(None, description="执行者")
    timestamp: datetime = Field(default_factory=datetime.now)
    comment: Optional[str] = Field(None, description="备注")
    data: Dict[str, Any] = Field(default_factory=dict, description="附加数据")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


WorkflowInstance.model_rebuild()


class TransitionRequest(BaseModel):
    """转换请求"""
    instance_id: str = Field(..., description="工作流实例ID")
    transition: str = Field(..., description="转换名称")
    actor: Optional[str] = Field(None, description="执行者")
    comment: Optional[str] = Field(None, description="备注")
    data: Dict[str, Any] = Field(default_factory=dict, description="附加数据")


class WorkflowStats(BaseModel):
    """工作流统计"""
    total_instances: int = Field(0, description="总实例数")
    in_progress: int = Field(0, description="进行中")
    completed: int = Field(0, description="已完成")
    cancelled: int = Field(0, description="已取消")
    avg_duration_seconds: float = Field(0.0, description="平均耗时(秒)")
    by_state: Dict[str, int] = Field(default_factory=dict, description="按状态分布")


# ============================================================================
# 内置工作流定义
# ============================================================================

def get_case_lifecycle_workflow() -> WorkflowDefinition:
    """获取案件全生命周期工作流定义"""
    states = [
        WorkflowState(name="draft", label="草稿", description="案件信息录入中", color="#9ca3af", is_initial=True, entry_actions=["notify_case_created"]),
        WorkflowState(name="accepted", label="已受理", description="案件已受理，待分配", color="#3b82f6", entry_actions=["notify_case_accepted"]),
        WorkflowState(name="reviewing", label="合同审查中", description="合同风险审查中", color="#f59e0b"),
        WorkflowState(name="processing", label="办理中", description="案件正常办理中", color="#8b5cf6"),
        WorkflowState(name="hearing", label="开庭审理", description="法院开庭审理中", color="#ec4899"),
        WorkflowState(name="judgment", label="已判决", description="法院已作出判决", color="#22c55e"),
        WorkflowState(name="closed", label="已结案", description="案件已结案归档", color="#6b7280", is_final=True, entry_actions=["archive_case"]),
        WorkflowState(name="cancelled", label="已撤销", description="案件已撤销", color="#ef4444", is_final=True)
    ]

    transitions = [
        WorkflowTransition(name="accept", from_state="draft", to_state="accepted", label="受理案件", transition_type=TransitionType.MANUAL, required_roles=["admin", "case_manager"]),
        WorkflowTransition(name="start_review", from_state="accepted", to_state="reviewing", label="开始合同审查", transition_type=TransitionType.MANUAL, required_roles=["lawyer"]),
        WorkflowTransition(name="review_done", from_state="reviewing", to_state="processing", label="审查完成", transition_type=TransitionType.AUTO, condition="contract_review_completed"),
        WorkflowTransition(name="assign_lawyer", from_state="accepted", to_state="processing", label="分配律师", transition_type=TransitionType.MANUAL, required_roles=["admin"]),
        WorkflowTransition(name="schedule_hearing", from_state="processing", to_state="hearing", label="安排开庭", transition_type=TransitionType.MANUAL, required_roles=["lawyer"]),
        WorkflowTransition(name="hearing_done", from_state="hearing", to_state="judgment", label="庭审结束", transition_type=TransitionType.MANUAL, required_roles=["lawyer"]),
        WorkflowTransition(name="close", from_state="judgment", to_state="closed", label="结案归档", transition_type=TransitionType.MANUAL, required_roles=["admin", "case_manager"]),
        WorkflowTransition(name="close_direct", from_state="processing", to_state="closed", label="直接结案", transition_type=TransitionType.MANUAL, required_roles=["admin"]),
        WorkflowTransition(name="cancel", from_state="draft", to_state="cancelled", label="撤销案件", transition_type=TransitionType.MANUAL, required_roles=["admin"]),
        WorkflowTransition(name="back_to_processing", from_state="hearing", to_state="processing", label="退回补充", transition_type=TransitionType.MANUAL, required_roles=["lawyer"])
    ]

    return WorkflowDefinition(
        id="case_lifecycle_v1",
        name="案件全生命周期",
        type=WorkflowType.CASE_LIFECYCLE,
        version="1.0",
        description="案件从录入到结案的完整生命周期管理",
        states=states,
        transitions=transitions,
        initial_state="draft",
        final_states=["closed", "cancelled"]
    )


def get_contract_review_workflow() -> WorkflowDefinition:
    """获取合同审查工作流定义"""
    states = [
        WorkflowState(name="uploaded", label="已上传", description="合同已上传，待审查", color="#9ca3af", is_initial=True),
        WorkflowState(name="ai_reviewing", label="AI审查中", description="AI自动审查中", color="#3b82f6"),
        WorkflowState(name="lawyer_reviewing", label="律师复核", description="律师人工复核中", color="#f59e0b"),
        WorkflowState(name="completed", label="审查完成", description="合同审查完成", color="#22c55e", is_final=True),
        WorkflowState(name="rejected", label="已退回", description="合同需修改后重新提交", color="#ef4444")
    ]

    transitions = [
        WorkflowTransition(name="start_ai_review", from_state="uploaded", to_state="ai_reviewing", label="开始AI审查", transition_type=TransitionType.AUTO),
        WorkflowTransition(name="ai_review_done", from_state="ai_reviewing", to_state="lawyer_reviewing", label="AI审查完成", transition_type=TransitionType.AUTO, condition="ai_review_completed"),
        WorkflowTransition(name="lawyer_approve", from_state="lawyer_reviewing", to_state="completed", label="律师确认", transition_type=TransitionType.APPROVAL, required_roles=["lawyer"]),
        WorkflowTransition(name="lawyer_reject", from_state="lawyer_reviewing", to_state="rejected", label="退回修改", transition_type=TransitionType.MANUAL, required_roles=["lawyer"]),
        WorkflowTransition(name="resubmit", from_state="rejected", to_state="uploaded", label="重新提交", transition_type=TransitionType.MANUAL)
    ]

    return WorkflowDefinition(
        id="contract_review_v1",
        name="合同审查工作流",
        type=WorkflowType.CONTRACT_REVIEW,
        version="1.0",
        description="合同上传、AI审查、律师复核的完整审查流程",
        states=states,
        transitions=transitions,
        initial_state="uploaded",
        final_states=["completed"]
    )


# ============================================================================
# 工作流引擎类
# ============================================================================

class WorkflowEngine:
    """工作流引擎 - 核心实现"""

    _definitions: Dict[str, WorkflowDefinition] = {}
    _instances: Dict[str, WorkflowInstance] = {}
    _action_handlers: Dict[str, Callable] = {}

    @classmethod
    def register_definition(cls, definition: WorkflowDefinition) -> None:
        """注册工作流定义"""
        cls._definitions[definition.id] = definition
        logger.info(f"工作流定义已注册: {definition.id} v{definition.version}")

    @classmethod
    def get_definition(cls, definition_id: str) -> Optional[WorkflowDefinition]:
        """获取工作流定义"""
        return cls._definitions.get(definition_id)

    @classmethod
    def list_definitions(cls) -> List[WorkflowDefinition]:
        """列出所有工作流定义"""
        return list(cls._definitions.values())

    @classmethod
    def register_action_handler(cls, action_name: str, handler: Callable) -> None:
        """注册动作处理器"""
        cls._action_handlers[action_name] = handler
        logger.debug(f"动作处理器已注册: {action_name}")

    @classmethod
    def start_instance(
        cls,
        definition_id: str,
        entity_type: str,
        entity_id: str,
        started_by: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> WorkflowInstance:
        """启动工作流实例"""
        definition = cls.get_definition(definition_id)
        if not definition:
            raise ValueError(f"工作流定义不存在: {definition_id}")

        if not definition.initial_state:
            raise ValueError(f"工作流定义未设置初始状态: {definition_id}")

        instance_id = f"wf-{datetime.now().strftime('%Y%m%d%H%M%S')}-{id(cls) % 10000}"
        instance = WorkflowInstance(
            id=instance_id,
            definition_id=definition_id,
            entity_type=entity_type,
            entity_id=entity_id,
            current_state=definition.initial_state,
            status=WorkflowStatus.IN_PROGRESS,
            started_by=started_by,
            context=initial_context or {}
        )

        initial_state_name = definition.initial_state
        state = next((s for s in definition.states if s.name == initial_state_name), None)
        if state:
            cls._execute_entry_actions(instance, state)

        history_entry = WorkflowHistoryEntry(
            id=f"hist-{len(instance.history) + 1}",
            instance_id=instance_id,
            from_state=None,
            to_state=definition.initial_state,
            transition="start",
            actor=started_by,
            comment="工作流启动"
        )
        instance.history.append(history_entry)

        cls._instances[instance_id] = instance
        logger.info(f"工作流实例已启动: {instance_id} ({definition.name})")

        return instance

    @classmethod
    def get_instance(cls, instance_id: str) -> Optional[WorkflowInstance]:
        """获取工作流实例"""
        return cls._instances.get(instance_id)

    @classmethod
    def list_instances(
        cls,
        definition_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None
    ) -> List[WorkflowInstance]:
        """列出工作流实例"""
        instances = list(cls._instances.values())

        if definition_id:
            instances = [i for i in instances if i.definition_id == definition_id]
        if entity_type:
            instances = [i for i in instances if i.entity_type == entity_type]
        if entity_id:
            instances = [i for i in instances if i.entity_id == entity_id]
        if status:
            instances = [i for i in instances if i.status == status]

        return instances

    @classmethod
    def get_available_transitions(cls, instance_id: str) -> List[WorkflowTransition]:
        """获取可用的转换"""
        instance = cls.get_instance(instance_id)
        if not instance:
            return []

        definition = cls.get_definition(instance.definition_id)
        if not definition:
            return []

        return [
            t for t in definition.transitions
            if t.from_state == instance.current_state
        ]

    @classmethod
    def execute_transition(cls, request: TransitionRequest) -> WorkflowInstance:
        """执行状态转换"""
        instance = cls.get_instance(request.instance_id)
        if not instance:
            raise ValueError(f"工作流实例不存在: {request.instance_id}")

        if instance.status in (WorkflowStatus.COMPLETED, WorkflowStatus.CANCELLED):
            raise ValueError(f"工作流已结束，无法转换: {instance.status.value}")

        definition = cls.get_definition(instance.definition_id)
        if not definition:
            raise ValueError(f"工作流定义不存在: {instance.definition_id}")

        transition = next(
            (t for t in definition.transitions
             if t.name == request.transition and t.from_state == instance.current_state),
            None
        )
        if not transition:
            raise ValueError(
                f"无效的转换: {request.transition} "
                f"(当前状态: {instance.current_state})"
            )

        from_state_name = instance.current_state
        from_state = next((s for s in definition.states if s.name == from_state_name), None)
        to_state = next((s for s in definition.states if s.name == transition.to_state), None)

        if from_state:
            cls._execute_exit_actions(instance, from_state)

        cls._execute_transition_actions(instance, transition)

        instance.current_state = transition.to_state
        instance.context.update(request.data)

        if to_state:
            cls._execute_entry_actions(instance, to_state)

        if to_state and to_state.is_final:
            instance.status = WorkflowStatus.COMPLETED
            instance.completed_at = datetime.now()

        history_entry = WorkflowHistoryEntry(
            id=f"hist-{len(instance.history) + 1}",
            instance_id=instance.id,
            from_state=from_state_name,
            to_state=transition.to_state,
            transition=transition.name,
            actor=request.actor,
            comment=request.comment,
            data=request.data
        )
        instance.history.append(history_entry)

        logger.info(
            f"工作流转换: {instance.id} "
            f"{from_state_name} -> {transition.to_state} "
            f"({transition.name})"
        )

        cls._check_auto_transitions(instance)

        return instance

    @classmethod
    def _check_auto_transitions(cls, instance: WorkflowInstance) -> None:
        """检查并执行自动转换"""
        definition = cls.get_definition(instance.definition_id)
        if not definition:
            return

        auto_transitions = [
            t for t in definition.transitions
            if t.from_state == instance.current_state
            and t.transition_type == TransitionType.AUTO
        ]

        for transition in auto_transitions:
            if cls._evaluate_condition(instance, transition.condition):
                logger.debug(f"触发自动转换: {transition.name}")
                try:
                    cls.execute_transition(TransitionRequest(
                        instance_id=instance.id,
                        transition=transition.name,
                        actor="system",
                        comment="自动转换"
                    ))
                except Exception as e:
                    logger.error(f"自动转换失败: {transition.name}, 错误: {e}")
                break

    @classmethod
    def _evaluate_condition(cls, instance: WorkflowInstance, condition: Optional[str]) -> bool:
        """评估条件表达式（简化实现）"""
        if not condition:
            return True

        context = instance.context
        try:
            if condition == "contract_review_completed":
                return context.get("review_completed", False)
            if condition == "ai_review_completed":
                return context.get("ai_review_done", False)
            return bool(context.get(condition))
        except Exception as e:
            logger.warning(f"条件评估失败: {condition}, 错误: {e}")
            return False

    @classmethod
    def _execute_entry_actions(cls, instance: WorkflowInstance, state: WorkflowState) -> None:
        """执行进入状态动作"""
        for action in state.entry_actions:
            cls._execute_action(instance, action)

    @classmethod
    def _execute_exit_actions(cls, instance: WorkflowInstance, state: WorkflowState) -> None:
        """执行离开状态动作"""
        for action in state.exit_actions:
            cls._execute_action(instance, action)

    @classmethod
    def _execute_transition_actions(cls, instance: WorkflowInstance, transition: WorkflowTransition) -> None:
        """执行转换动作"""
        for action in transition.actions:
            cls._execute_action(instance, action)

    @classmethod
    def _execute_action(cls, instance: WorkflowInstance, action_name: str) -> None:
        """执行单个动作"""
        handler = cls._action_handlers.get(action_name)
        if handler:
            try:
                handler(instance)
                logger.debug(f"动作执行成功: {action_name}")
            except Exception as e:
                logger.error(f"动作执行失败: {action_name}, 错误: {e}")
        else:
            logger.debug(f"未找到动作处理器: {action_name} (跳过)")

    @classmethod
    def get_stats(cls, definition_id: Optional[str] = None) -> WorkflowStats:
        """获取工作流统计"""
        instances = cls.list_instances(definition_id=definition_id)

        stats = WorkflowStats()
        stats.total_instances = len(instances)
        stats.in_progress = sum(1 for i in instances if i.status == WorkflowStatus.IN_PROGRESS)
        stats.completed = sum(1 for i in instances if i.status == WorkflowStatus.COMPLETED)
        stats.cancelled = sum(1 for i in instances if i.status == WorkflowStatus.CANCELLED)

        by_state: Dict[str, int] = {}
        durations = []
        for instance in instances:
            state = instance.current_state
            by_state[state] = by_state.get(state, 0) + 1
            if instance.completed_at and instance.started_at:
                duration = (instance.completed_at - instance.started_at).total_seconds()
                durations.append(duration)

        stats.by_state = by_state
        if durations:
            stats.avg_duration_seconds = sum(durations) / len(durations)

        return stats

    @classmethod
    def get_workflow_timeline(cls, instance_id: str) -> List[Dict[str, Any]]:
        """获取工作流时间线"""
        instance = cls.get_instance(instance_id)
        if not instance:
            return []

        timeline = []
        for entry in instance.history:
            timeline.append({
                "id": entry.id,
                "from_state": entry.from_state,
                "to_state": entry.to_state,
                "transition": entry.transition,
                "actor": entry.actor,
                "timestamp": entry.timestamp.isoformat(),
                "comment": entry.comment,
                "data": entry.data
            })

        return timeline


# ============================================================================
# 初始化 - 注册内置工作流
# ============================================================================

def init_workflow_engine() -> None:
    """初始化工作流引擎，注册内置工作流定义"""
    WorkflowEngine.register_definition(get_case_lifecycle_workflow())
    WorkflowEngine.register_definition(get_contract_review_workflow())
    logger.info("工作流引擎初始化完成")
