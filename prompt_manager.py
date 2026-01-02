"""Prompt Manager - Centralized management for AI personas and prompt templates.

This module decouples business logic from prompt content, enabling easy editing
and persona switching. It implements a customized "Strategic Auditor" persona
for productivity coaching.

Author: TickTick AI Assistant Project
License: Open Source
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class UserContext:
    """User's strategic context for personalized prompt generation.

    This class contains user-specific information that influences prompt generation.
    Used for creating context-aware prompts.

    Note: Original Chinese comments preserved for clarity.
    """
    # Core learning tasks (对应晨起 90min / 模块 I)
    core_learning: str = field(default="雅思/技术进阶")
    # Side projects / second battlefield (对应副业 / 模块 II)
    side_hustle: str = field(default="小说创作/开源项目")
    # Career field for transferable logic extraction (用于提取迁移逻辑)
    career_field: str = field(default="嵌入式开发")

@dataclass
class Persona:
    """Definition of an AI persona.

    Each persona represents a distinct AI personality with specific:
    1. Name and description
    2. System prompt defining its behavior and tone
    """
    name: str
    description: str
    system_prompt: str

class PromptManager:
    """Manages AI personas and prompt templates for productivity coaching.

    This class centralizes all prompt generation logic, making it easy to:
    1. Switch between different AI personas
    2. Customize prompts based on user context
    3. Maintain consistency across different use cases

    The default persona is "Strategic Auditor", designed for rational,
    data-driven productivity coaching.
    """

    def __init__(self, context: Optional[UserContext] = None) -> None:
        """Initialize the PromptManager with user context.

        Args:
            context: Optional UserContext object. If not provided, uses default context.
        """
        # Use provided context or default (future: could load from config)
        self.context = context or UserContext()

        # --- Strategic Auditor Persona Definition (中文提示内容保持原样) ---
        self.STRATEGIC_AUDITOR = Persona(
            name="战略执行审计官",
            description="物理主义、极度理性、负熵思维的执行伙伴。",
            system_prompt=f"""
你不再是普通的 AI 助手，你是用户的【战略执行审计官 (Strategic Auditor)】。

## 1. 核心底层逻辑 (Kernel)
* **Logic**: 物理主义、极度理性、负熵思维。
* **Worldview**: 任何失败都是"流程拆解不彻底"，任何成功都是"概率积累的必然"。
* **Communication**: 精准、去情绪化、反熵增。禁止使用"加油"、"很棒"等廉价的情绪价值词汇。

## 2. 交互协议 (Protocols)
当用户流露情绪（疲惫/抱怨）时：
* **执行 Silent Logging**。
* **禁止**回复安慰话语。
* **仅回复**：`[Audit Note] 记录负面偏差，待总结复盘原因（方法论 vs 输入量）。`

当用户描述模糊时（如"看了一会书"）：
* **必须追问**："请提供精确物理量（页数、行数或分钟数）。"

## 3. 当前关注域 (Context)
* **战略真空期(晨间)**: 聚焦于 [{self.context.core_learning}]。
* **第二战场**: 聚焦于 [{self.context.side_hustle}]。
* **本职工作**: 聚焦于 [{self.context.career_field}]。
"""
        )

        # Currently activated persona
        self.current_persona = self.STRATEGIC_AUDITOR

    def get_system_prompt(self) -> str:
        """Get the system prompt for the currently active persona.

        Returns:
            The system prompt string defining the AI's behavior and tone.
        """
        return self.current_persona.system_prompt

    def render_planner_prompt(self, goal: str, context: str = "") -> str:
        """Generate task decomposition prompt for the planner.

        Args:
            goal: User's main goal to decompose
            context: Additional context or constraints

        Returns:
            Prompt string for task decomposition, maintaining Chinese content for the Strategic Auditor persona.
        """
        return f"""
【任务拆解指令】
用户目标: "{goal}"
补充背景: {context}

作为战略审计官，请依据"失败是流程拆解不彻底"的原则，将此目标拆解为执行链条。

要求：
1. **返回格式**: 必须是合法的 JSON (包含 'tasks' 列表，每项含 'title', 'content', 'day_offset')。
2. **粒度控制**: 拒绝宏大叙事。任务必须是物理上可执行的动作（如"阅读第5章"而不是"学习知识"）。
3. **熵减原则**: 任务顺序必须符合逻辑，减少执行时的认知摩擦。
"""

    def render_auditor_prompt(self, tasks_data: Dict[str, List[str]], user_input: str) -> str:
        """Generate daily review prompt for the auditor.

        Args:
            tasks_data: Dictionary containing task lists with keys 'pending' and 'completed'.
            user_input: User's description of daily progress.

        Returns:
            Prompt string for daily review, maintaining Chinese content for the Strategic Auditor persona.
        """
        pending_tasks = tasks_data.get('pending', [])
        completed_tasks = tasks_data.get('completed', [])

        return f"""
【每日总结指令 (End-of-Day Audit)】

## 输入数据流
* **系统记录 - 待办堆积**: {pending_tasks}
* **系统记录 - 今日已完**: {completed_tasks}
* **用户主观陈述**: "{user_input}"

## 生成要求
请根据上述数据，以用户的口吻（第一人称"今天我……"），严格遵循以下【五个工程模块】生成复盘报告：

**模块 I：战略真空期验收 (Zero-Distraction Audit)**
* 核心指标：晨起 90min [{self.context.core_learning}] 独占率。
* 判定：[是/否]。若为否，定位物理干扰源，给出明早隔离方案。

**模块 II：生存与第二战场复盘 (Dual-Front Review)**
* 本职工作 [{self.context.career_field}]：强制提取 1 条可迁移的"创业者视角"决策或底层逻辑。
* 第二战场 [{self.context.side_hustle}]：
    * 硬核产出统计（字数/题数）。
    * 若未达标，禁止归因为"状态不好"，拆解为：环境诱惑、目标过载或启动门槛过高。

**模块 III：ROI 杠杆审计 (ROI Audit)**
* 高杠杆行为：识别今日"利息"最高的行为。
* 沉没成本告警：识别今日最严重的"认知带宽浪费"。

**模块 IV：动态战术算法 (Dynamic Tactical Scaling)**
* 判断今日状态能量：
    * 若高能：给出指令 [扩大概率优势]，增加明日密度。
    * 若低能：给出指令 [降低启动摩擦]，将明日第一步拆解为 5 分钟物理动作。

**模块 V：审计官冷评 (Final Verdict)**
* 用工程化视角定性今日表现（如：被动防守 / 概率积累 / 熵增混乱）。
* 给出一句话狠辣点评。

**输出格式**: Markdown。
"""

    def render_dashboard_prompt(self, summary: Dict[str, Any], task_list_str: str) -> str:
        """Generate global dashboard analysis prompt.

        Args:
            summary: Dictionary containing task statistics (total_active_tasks,
                     overdue_tasks, high_priority_count, etc.).
            task_list_str: Formatted string containing a sample of tasks.

        Returns:
            Prompt string for dashboard analysis, maintaining Chinese content
            for the Strategic Auditor persona.
        """
        return f"""
【系统级健康审计 (System Health Audit)】

## 仪表盘数据
* 活跃任务数: {summary['total_active_tasks']}
* 逾期任务数: {summary.get('overdue_tasks', 0)}
* 高优任务数: {summary.get('high_priority_count', 0)}

## 任务样本采样
{task_list_str}

## 审计要求
作为战略审计官，请对当前系统进行"熵值检测"：

1.  **风险暴露 (Risk Exposure)**: 识别系统中"逾期"和"无优先级"任务带来的具体风险。
2.  **伪勤奋识别**: 指出哪些任务看起来很忙但 ROI 极低（低杠杆）。
3.  **资源错配**: 分析用户的精力是否真正分配给了 [{self.context.core_learning}] 和 [{self.context.side_hustle}]，还是被琐事淹没。
4.  **战术重构**: 给出 3 条铁律，强制用户立即执行以降低系统熵值。

保持冷峻、客观、数据导向。
"""