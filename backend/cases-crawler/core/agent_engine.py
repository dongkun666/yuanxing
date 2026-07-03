"""
LexPrime Agent 引擎模块
========================

提供 Agent 定义、工具调用、多步推理等能力。

支持 Mock 模式：当真实 Agent 服务不可用时，返回模拟数据。
"""
from __future__ import annotations

import re
import time
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from loguru import logger


class AgentRole(str, Enum):
    """Agent 角色"""
    GENERAL_ASSISTANT = "general_assistant"
    CASE_RESEARCHER = "case_researcher"
    CONTRACT_REVIEWER = "contract_reviewer"
    DOCUMENT_DRAFTER = "document_drafter"
    LEGAL_CONSULTANT = "legal_consultant"
    TRIAL_LAWYER = "trial_lawyer"


class ToolType(str, Enum):
    """工具类型"""
    CASE_SEARCH = "case_search"
    LAW_SEARCH = "law_search"
    CONTRACT_REVIEW = "contract_review"
    DOCUMENT_GENERATE = "document_generate"
    CALCULATOR = "calculator"
    WEB_SEARCH = "web_search"
    DATABASE_QUERY = "database_query"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    THINKING = "thinking"
    PLANNING = "planning"
    EXECUTING = "executing"
    TOOL_CALLING = "tool_calling"
    OBSERVING = "observing"
    REFLECTING = "reflecting"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentDefinition:
    """Agent 定义"""
    agent_id: str
    name: str
    role: AgentRole
    description: str
    system_prompt: str
    tools: List[str]
    temperature: float = 0.7
    max_tokens: int = 2048
    max_iterations: int = 10
    enable_memory: bool = True
    enable_reflection: bool = True
    avatar: str = ""
    created_at: str = ""


@dataclass
class ToolDefinition:
    """工具定义"""
    tool_id: str
    name: str
    type: ToolType
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class ToolCall:
    """工具调用"""
    call_id: str
    tool_name: str
    arguments: Dict[str, Any]
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ThoughtStep:
    """思考步骤"""
    step_id: str
    iteration: int
    action: str
    thought: str
    tool_call: Optional[ToolCall] = None
    observation: Optional[str] = None
    timestamp: str = ""


@dataclass
class AgentMemory:
    """Agent 记忆"""
    short_term: List[Dict[str, Any]] = field(default_factory=list)
    long_term: List[Dict[str, Any]] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AgentResponse:
    """Agent 响应"""
    conversation_id: str
    agent_id: str
    final_answer: str
    thoughts: List[ThoughtStep]
    tool_calls: List[ToolCall]
    status: str
    total_iterations: int
    total_time_ms: int
    confidence: float = 0.0


class AgentEngine:
    """Agent 引擎

    提供完整的 Agent 能力：
    - 角色设定和工具集
    - 记忆系统
    - 任务分解和规划
    - 工具调用
    - 反思机制
    - 自我修正
    - 结果验证
    """

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self._agents: Dict[str, AgentDefinition] = {}
        self._tools: Dict[str, ToolDefinition] = {}
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}
        self._memories: Dict[str, AgentMemory] = {}
        self._init_agents()
        self._init_tools()

    def _init_agents(self):
        """初始化预设 Agent"""
        now = datetime.now().isoformat()

        self._agents = {
            "agent-general": AgentDefinition(
                agent_id="agent-general",
                name="通用法律助手",
                role=AgentRole.GENERAL_ASSISTANT,
                description="通用法律咨询助手，可处理各类基础法律问题",
                system_prompt="你是 LexPrime 通用法律助手，擅长解答各类法律问题，提供专业的法律建议和分析。",
                tools=["case_search", "law_search", "calculator"],
                temperature=0.7,
                max_tokens=2048,
                max_iterations=8,
                enable_memory=True,
                enable_reflection=True,
                avatar="🤖",
                created_at=now,
            ),
            "agent-researcher": AgentDefinition(
                agent_id="agent-researcher",
                name="案例研究员",
                role=AgentRole.CASE_RESEARCHER,
                description="专注于案例检索和法律研究，擅长类案检索和法规查询",
                system_prompt="你是 LexPrime 案例研究员，专注于案例检索和法律研究工作。",
                tools=["case_search", "law_search", "web_search"],
                temperature=0.3,
                max_tokens=4096,
                max_iterations=15,
                enable_memory=True,
                enable_reflection=True,
                avatar="🔍",
                created_at=now,
            ),
            "agent-contract": AgentDefinition(
                agent_id="agent-contract",
                name="合同审查专家",
                role=AgentRole.CONTRACT_REVIEWER,
                description="专业合同审查，识别风险点并提供修改建议",
                system_prompt="你是 LexPrime 合同审查专家，擅长审查各类合同，识别法律风险并提供专业修改建议。",
                tools=["contract_review", "law_search", "document_generate"],
                temperature=0.5,
                max_tokens=4096,
                max_iterations=10,
                enable_memory=True,
                enable_reflection=True,
                avatar="📋",
                created_at=now,
            ),
            "agent-drafter": AgentDefinition(
                agent_id="agent-drafter",
                name="文书起草助手",
                role=AgentRole.DOCUMENT_DRAFTER,
                description="专业法律文书起草，包括起诉状、答辩状、合同等",
                system_prompt="你是 LexPrime 文书起草助手，擅长起草各类法律文书，确保文书格式规范、逻辑清晰。",
                tools=["document_generate", "law_search", "case_search"],
                temperature=0.6,
                max_tokens=8192,
                max_iterations=12,
                enable_memory=True,
                enable_reflection=True,
                avatar="✍️",
                created_at=now,
            ),
            "agent-trial": AgentDefinition(
                agent_id="agent-trial",
                name="诉讼策略顾问",
                role=AgentRole.TRIAL_LAWYER,
                description="诉讼策略制定和庭审准备顾问",
                system_prompt="你是 LexPrime 诉讼策略顾问，擅长制定诉讼策略，准备庭审方案。",
                tools=["case_search", "law_search", "calculator", "document_generate"],
                temperature=0.7,
                max_tokens=4096,
                max_iterations=15,
                enable_memory=True,
                enable_reflection=True,
                avatar="⚖️",
                created_at=now,
            ),
        }

    def _init_tools(self):
        """初始化工具"""
        self._tools = {
            "case_search": ToolDefinition(
                tool_id="case_search",
                name="案例检索",
                type=ToolType.CASE_SEARCH,
                description="检索相关判例和案例",
                parameters={
                    "query": {"type": "string", "description": "检索关键词"},
                    "filters": {"type": "object", "description": "筛选条件"},
                    "top_k": {"type": "integer", "description": "返回数量", "default": 10},
                },
                enabled=True,
            ),
            "law_search": ToolDefinition(
                tool_id="law_search",
                name="法规查询",
                type=ToolType.LAW_SEARCH,
                description="查询法律法规和司法解释",
                parameters={
                    "query": {"type": "string", "description": "查询关键词"},
                    "law_type": {"type": "string", "description": "法规类型"},
                    "top_k": {"type": "integer", "description": "返回数量", "default": 10},
                },
                enabled=True,
            ),
            "contract_review": ToolDefinition(
                tool_id="contract_review",
                name="合同审查",
                type=ToolType.CONTRACT_REVIEW,
                description="审查合同风险点",
                parameters={
                    "contract_text": {"type": "string", "description": "合同文本"},
                    "review_type": {"type": "string", "description": "审查类型"},
                },
                enabled=True,
            ),
            "document_generate": ToolDefinition(
                tool_id="document_generate",
                name="文书生成",
                type=ToolType.DOCUMENT_GENERATE,
                description="生成法律文书",
                parameters={
                    "doc_type": {"type": "string", "description": "文书类型"},
                    "context": {"type": "object", "description": "文书内容信息"},
                },
                enabled=True,
            ),
            "calculator": ToolDefinition(
                tool_id="calculator",
                name="法律计算器",
                type=ToolType.CALCULATOR,
                description="计算利息、违约金、诉讼费等",
                parameters={
                    "calc_type": {"type": "string", "description": "计算类型"},
                    "params": {"type": "object", "description": "计算参数"},
                },
                enabled=True,
            ),
            "web_search": ToolDefinition(
                tool_id="web_search",
                name="网络搜索",
                type=ToolType.WEB_SEARCH,
                description="搜索最新法律资讯和案例",
                parameters={
                    "query": {"type": "string", "description": "搜索关键词"},
                    "num_results": {"type": "integer", "description": "结果数量", "default": 10},
                },
                enabled=True,
            ),
        }

    def list_agents(self) -> List[AgentDefinition]:
        """获取 Agent 列表"""
        return list(self._agents.values())

    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        """获取 Agent 详情"""
        return self._agents.get(agent_id)

    def list_tools(self) -> List[ToolDefinition]:
        """获取工具列表"""
        return list(self._tools.values())

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        """获取工具详情"""
        return self._tools.get(tool_id)

    def chat(self, agent_id: str, message: str,
             conversation_id: Optional[str] = None) -> AgentResponse:
        """与 Agent 对话

        Args:
            agent_id: Agent ID
            message: 用户消息
            conversation_id: 对话 ID

        Returns:
            Agent 响应
        """
        t0 = time.time()

        agent = self._agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")

        conv_id = conversation_id or f"conv-{uuid.uuid4().hex[:12]}"

        if conv_id not in self._conversations:
            self._conversations[conv_id] = []
            self._memories[conv_id] = AgentMemory()

        if self.mock_mode:
            response = self._mock_agent_response(agent, message, conv_id, t0)
        else:
            response = self._real_agent_response(agent, message, conv_id, t0)

        self._conversations[conv_id].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat(),
        })
        self._conversations[conv_id].append({
            "role": "assistant",
            "content": response.final_answer,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
        })

        return response

    def _mock_agent_response(self, agent: AgentDefinition, message: str,
                             conversation_id: str, start_time: float) -> AgentResponse:
        """Mock Agent 响应"""
        message_lower = message.lower()
        thoughts = []
        tool_calls = []

        plan = self._plan_task(agent, message)
        thoughts.append(ThoughtStep(
            step_id=f"step-{uuid.uuid4().hex[:8]}",
            iteration=1,
            action="plan",
            thought=f"分析用户需求，确定任务类型：{plan['task_type']}。需要执行 {len(plan['steps'])} 个步骤。",
            timestamp=datetime.now().isoformat(),
        ))

        if plan["need_case_search"]:
            tool_call = ToolCall(
                call_id=f"call-{uuid.uuid4().hex[:8]}",
                tool_name="case_search",
                arguments={"query": message, "top_k": 5},
                status="completed",
                result={
                    "found": 5,
                    "cases": [
                        {"title": "张三诉李四借款合同纠纷案", "court": "北京市第一中级人民法院"},
                        {"title": "王五诉赵六民间借贷案", "court": "上海市高级人民法院"},
                        {"title": "钱七诉孙八合同违约案", "court": "广东省深圳市中级人民法院"},
                    ],
                },
                started_at=datetime.now().isoformat(),
                finished_at=datetime.now().isoformat(),
            )
            tool_calls.append(tool_call)
            thoughts.append(ThoughtStep(
                step_id=f"step-{uuid.uuid4().hex[:8]}",
                iteration=2,
                action="tool_call",
                thought="需要检索相关案例作为参考依据。",
                tool_call=tool_call,
                observation="找到 5 个相关案例，其中 3 个具有较高参考价值。",
                timestamp=datetime.now().isoformat(),
            ))

        if plan["need_law_search"]:
            tool_call = ToolCall(
                call_id=f"call-{uuid.uuid4().hex[:8]}",
                tool_name="law_search",
                arguments={"query": message, "top_k": 5},
                status="completed",
                result={
                    "found": 5,
                    "laws": [
                        {"title": "中华人民共和国民法典", "article": "第五百七十七条"},
                        {"title": "最高人民法院关于审理民间借贷案件适用法律若干问题的规定"},
                    ],
                },
                started_at=datetime.now().isoformat(),
                finished_at=datetime.now().isoformat(),
            )
            tool_calls.append(tool_call)
            thoughts.append(ThoughtStep(
                step_id=f"step-{uuid.uuid4().hex[:8]}",
                iteration=3,
                action="tool_call",
                thought="需要查询相关法律法规作为法律依据。",
                tool_call=tool_call,
                observation="找到 5 部相关法律法规，其中《民法典》相关条款最为关键。",
                timestamp=datetime.now().isoformat(),
            ))

        reflection_thought = self._reflect(agent, message, thoughts)
        thoughts.append(ThoughtStep(
            step_id=f"step-{uuid.uuid4().hex[:8]}",
            iteration=len(thoughts) + 1,
            action="reflect",
            thought=reflection_thought,
            timestamp=datetime.now().isoformat(),
        ))

        final_answer = self._generate_final_answer(agent, message, thoughts)

        total_time = int((time.time() - start_time) * 1000)

        return AgentResponse(
            conversation_id=conversation_id,
            agent_id=agent.agent_id,
            final_answer=final_answer,
            thoughts=thoughts,
            tool_calls=tool_calls,
            status="completed",
            total_iterations=len(thoughts),
            total_time_ms=total_time,
            confidence=0.85,
        )

    def _plan_task(self, agent: AgentDefinition, message: str) -> Dict[str, Any]:
        """任务分解和规划"""
        msg_lower = message.lower()

        task_type = "general_consultation"
        need_case_search = False
        need_law_search = False
        need_contract_review = False
        need_document_gen = False

        if any(kw in message for kw in ["借款", "合同", "违约", "赔偿", "纠纷"]):
            task_type = "contract_dispute"
            need_case_search = True
            need_law_search = True
        elif any(kw in message for kw in ["审查", "风险", "合同条款"]):
            task_type = "contract_review"
            need_contract_review = True
            need_law_search = True
        elif any(kw in message for kw in ["起草", "写", "起诉状", "答辩状", "合同"]):
            task_type = "document_generation"
            need_document_gen = True
            need_law_search = True
        elif any(kw in message for kw in ["案例", "判例", "检索", "查找"]):
            task_type = "case_research"
            need_case_search = True
            need_law_search = True

        steps = [
            {"step": 1, "description": "理解用户需求", "status": "completed"},
            {"step": 2, "description": "制定执行计划", "status": "completed"},
        ]

        if need_case_search:
            steps.append({"step": len(steps) + 1, "description": "检索相关案例", "status": "in_progress"})
        if need_law_search:
            steps.append({"step": len(steps) + 1, "description": "查询法律法规", "status": "pending"})
        if need_contract_review:
            steps.append({"step": len(steps) + 1, "description": "审查合同风险", "status": "pending"})

        steps.append({"step": len(steps) + 1, "description": "整合分析结果", "status": "pending"})
        steps.append({"step": len(steps) + 1, "description": "生成最终回答", "status": "pending"})

        return {
            "task_type": task_type,
            "steps": steps,
            "need_case_search": need_case_search,
            "need_law_search": need_law_search,
            "need_contract_review": need_contract_review,
            "need_document_gen": need_document_gen,
        }

    def _reflect(self, agent: AgentDefinition, message: str,
                 thoughts: List[ThoughtStep]) -> str:
        """反思机制"""
        if not agent.enable_reflection:
            return "反思功能已禁用"

        case_info = ""
        law_info = ""
        for t in thoughts:
            if t.observation and "案例" in t.observation:
                case_info = t.observation
            if t.observation and "法规" in t.observation:
                law_info = t.observation

        reflection = (
            "【反思过程】\n"
            "1. 信息完整性检查：已获取案例和法规信息，信息源充足。\n"
            "2. 推理逻辑验证：从法律依据到结论的推导过程符合法律逻辑。\n"
            "3. 潜在风险评估：需要提醒用户具体案件需结合实际情况判断。\n"
            "4. 回答质量检查：回答结构清晰，引用准确，建议实用。\n\n"
            "结论：回答质量良好，可以输出给用户。"
        )

        return reflection

    def _generate_final_answer(self, agent: AgentDefinition, message: str,
                               thoughts: List[ThoughtStep]) -> str:
        """生成最终回答"""
        msg_lower = message.lower()

        if any(kw in message for kw in ["借款", "利息", "民间借贷"]):
            return (
                "根据您的问题，我为您整理了关于民间借贷利息的法律分析：\n\n"
                "**一、法律依据**\n"
                "根据《最高人民法院关于审理民间借贷案件适用法律若干问题的规定》第二十五条规定，"
                "出借人请求借款人按照合同约定利率支付利息的，人民法院应予支持，"
                "但是双方约定的利率超过合同成立时一年期贷款市场报价利率四倍的除外。\n\n"
                "**二、利率上限**\n"
                "- 法定保护上限：合同成立时一年期 LPR 的 4 倍\n"
                "- 当前（2026年）1年期 LPR 约为 3.45%，4 倍约为 13.8%\n"
                "- 超过部分不受法律保护\n\n"
                "**三、相关案例参考**\n"
                "1. 张三诉李四借款合同纠纷案：法院支持了 LPR 4 倍以内的利息请求\n"
                "2. 王五诉赵六民间借贷案：约定利率 24%，法院调整为 LPR 4 倍\n\n"
                "**四、律师建议**\n"
                "1. 借款时明确约定利率，但不要超过法定上限\n"
                "2. 保留借款凭证（借条、转账记录等）\n"
                "3. 注意诉讼时效（3年）\n\n"
                "⚠️ 以上分析仅供参考，具体案件需结合实际情况和证据综合判断。"
            )

        if any(kw in message for kw in ["合同", "审查", "风险"]):
            return (
                "根据您的合同审查需求，我为您提供以下审查要点：\n\n"
                "**一、主体资格审查**\n"
                "- 核对对方营业执照、法定代表人身份证明\n"
                "- 确认签约人是否有合法授权\n"
                "- 核实对方履约能力和资信状况\n\n"
                "**二、合同条款风险点**\n"
                "1. **标的条款**：是否明确具体，避免歧义\n"
                "2. **价款支付**：金额、币种、支付方式、账期是否清晰\n"
                "3. **违约责任**：违约金比例是否合理，损失赔偿计算方式\n"
                "4. **争议解决**：管辖法院约定是否有效，仲裁条款是否规范\n"
                "5. **合同解除**：解除条件和程序是否明确\n\n"
                "**三、常见风险提示**\n"
                "- 格式条款提示说明义务\n"
                "- 不可抗力条款覆盖范围\n"
                "- 保密条款和竞业限制\n\n"
                "如需详细审查，请提供完整合同文本。"
            )

        if any(kw in message for kw in ["起草", "写", "起诉状", "答辩状"]):
            return (
                "好的，我可以帮您起草法律文书。为了确保文书质量，请提供以下信息：\n\n"
                "**起诉状需要的信息**\n"
                "1. 原被告基本信息（姓名/名称、地址、联系方式等）\n"
                "2. 诉讼请求（明确具体的诉求）\n"
                "3. 事实与理由（案件事实经过和法律依据）\n"
                "4. 证据清单（证据名称、来源、证明目的）\n"
                "5. 受理法院\n\n"
                "**答辩状需要的信息**\n"
                "1. 答辩人基本信息\n"
                "2. 针对原告诉求的逐项答辩意见\n"
                "3. 事实与理由\n"
                "4. 证据清单\n\n"
                "您可以先告诉我：\n"
                "- 需要起草什么类型的文书？\n"
                "- 案件大致情况是什么？\n\n"
                "我会根据您提供的信息，按照规范格式为您起草专业的法律文书。"
            )

        return (
            f"您好！我是 {agent.name}。\n\n"
            f"针对您的问题「{message}」，我进行了如下分析：\n\n"
            "**一、问题定性**\n"
            "您的问题涉及法律事务咨询，需要结合具体情况和相关法律规定进行分析。\n\n"
            "**二、关键要点**\n"
            "1. 首先需要明确具体的法律关系和争议焦点\n"
            "2. 检索相关法律法规和司法解释作为依据\n"
            "3. 参考类似案例的裁判观点\n"
            "4. 结合实际情况给出专业建议\n\n"
            "**三、下一步建议**\n"
            "为了给您更准确的解答，请补充以下信息：\n"
            "- 案件的具体背景和经过\n"
            "- 您的主要诉求是什么\n"
            "- 目前掌握哪些证据材料\n\n"
            "您可以详细描述一下情况，我会为您提供更有针对性的法律分析。"
        )

    def _real_agent_response(self, agent: AgentDefinition, message: str,
                             conversation_id: str, start_time: float) -> AgentResponse:
        """真实 Agent 响应（待实现）"""
        return AgentResponse(
            conversation_id=conversation_id,
            agent_id=agent.agent_id,
            final_answer="Agent 服务暂未配置，请使用 Mock 模式。",
            thoughts=[],
            tool_calls=[],
            status="failed",
            total_iterations=0,
            total_time_ms=int((time.time() - start_time) * 1000),
            confidence=0.0,
        )

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self._conversations.get(conversation_id, [])

    def get_agent_memory(self, conversation_id: str) -> Optional[AgentMemory]:
        """获取 Agent 记忆"""
        return self._memories.get(conversation_id)

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool not found: {tool_name}"}

        if not tool.enabled:
            return {"success": False, "error": f"Tool disabled: {tool_name}"}

        if self.mock_mode:
            return self._mock_tool_execute(tool_name, arguments)
        else:
            return {"success": False, "error": "Real tool execution not implemented"}

    def _mock_tool_execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Mock 工具执行"""
        if tool_name == "case_search":
            query = arguments.get("query", "")
            return {
                "success": True,
                "data": {
                    "total": 5,
                    "items": [
                        {"id": "case-001", "title": "张三诉李四借款合同纠纷案", "court": "北京市第一中级人民法院", "score": 0.95},
                        {"id": "case-002", "title": "王五诉赵六民间借贷案", "court": "上海市高级人民法院", "score": 0.88},
                        {"id": "case-003", "title": "钱七诉孙八合同违约案", "court": "深圳市中级人民法院", "score": 0.82},
                    ],
                },
            }

        if tool_name == "law_search":
            query = arguments.get("query", "")
            return {
                "success": True,
                "data": {
                    "total": 5,
                    "items": [
                        {"id": "law-001", "title": "中华人民共和国民法典", "level": "法律", "effective": True},
                        {"id": "law-002", "title": "最高人民法院关于审理民间借贷案件适用法律若干问题的规定", "level": "司法解释", "effective": True},
                    ],
                },
            }

        if tool_name == "calculator":
            calc_type = arguments.get("calc_type", "")
            params = arguments.get("params", {})
            result = {}
            if calc_type == "interest":
                principal = float(params.get("principal", 0))
                rate = float(params.get("rate", 0))
                days = int(params.get("days", 0))
                interest = principal * rate / 100 * days / 365
                result = {"interest": round(interest, 2), "total": round(principal + interest, 2)}
            return {"success": True, "data": result}

        return {"success": True, "data": {"message": f"Tool {tool_name} executed (mock)"}}


_agent_instance: Optional[AgentEngine] = None


def get_agent_engine() -> AgentEngine:
    """获取 Agent 引擎单例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AgentEngine(mock_mode=True)
    return _agent_instance
