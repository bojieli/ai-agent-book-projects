"""
roles.py —— 定义多个「专业角色 Agent」。

实验 10-1 的核心：一个会话里存在多个专业角色，每个角色有
  (1) 独立的系统提示词（system prompt）
  (2) 专属工具集（tools）
角色之间通过 transfer_to_agent(target_role, reason) 自主移交控制权。

与 10-1（软件开发单任务的预定义阶段流水线）不同，这里强调跨领域、
由 Agent 自主判断该切换到哪个角色——不是预先规划好的线性流程。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Role:
    name: str            # 角色标识，用作 transfer_to_agent 的 target_role
    title: str           # 中文名称（打印用）
    system_prompt: str   # 该角色的系统提示词
    tools: List[str] = field(default_factory=list)  # 该角色的专属工具名（不含 transfer）


# 所有可移交的目标角色说明（会拼进每个角色的系统提示词，让它知道有哪些同事）。
_ROSTER_DESC = (
    "- triage：前台分诊（默认角色），负责理解需求、拆解任务、把控制权移交给合适的专业角色，"
    "并在全部子任务完成后做收尾确认。\n"
    "- research：信息检索专家，擅长用 web_search 查数据、事实、资料。\n"
    "- coding：编程专家，擅长用 execute_python 写并运行代码解决逻辑/脚本问题。\n"
    "- data_analysis：数据分析专家，擅长用 calculate / descriptive_stats 做计算与统计（如增长率、均值）。\n"
    "- writing：写作专家，擅长把零散结论润色成通顺、面向特定读者的成稿。\n"
)

# 每个角色系统提示词共用的移交纪律。
_HANDOFF_RULES = (
    "\n\n【团队协作规则】\n"
    f"当前会话中有以下专业角色（同事）：\n{_ROSTER_DESC}"
    "你们共享同一段对话历史，因此移交后新同事能看到此前的全部内容。\n"
    "如果当前任务超出你的职责范围，必须调用 transfer_to_agent(target_role, reason) "
    "把控制权移交给更合适的同事，而不要勉强自己做。\n"
    "reason 里要简述『为什么移交、请对方做什么』。\n"
    "只有当属于你职责范围内的部分做完时，才移交或收尾；不要一次移交给多个角色。"
)


ROLES: Dict[str, Role] = {
    "triage": Role(
        name="triage",
        title="前台分诊",
        tools=[],  # triage 没有专业工具，只有 transfer
        system_prompt=(
            "你是通用助理系统的『前台分诊』角色，也是默认入口。\n"
            "你的职责：理解用户的整体需求，把它拆成有先后顺序的子任务，"
            "然后【一步一步】把控制权移交给合适的专业角色去完成。\n"
            "典型顺序是：先移交 research 检索数据 → 再移交 data_analysis 计算指标 → "
            "最后移交 writing 成文。因此当任务包含『查数据』时，你的第一步一般就是移交给 research。\n"
            "你自己不做检索/编程/计算/长文写作——这些都要移交。\n"
            "当所有子任务都完成、最终成稿已经在对话里产出时，由你向用户做一句话收尾确认，"
            "并把最终成稿原文再复述一遍；此时不要再移交，直接输出结束语。"
        ) + _HANDOFF_RULES,
    ),
    "research": Role(
        name="research",
        title="信息检索专家",
        tools=["web_search"],
        system_prompt=(
            "你是『信息检索专家』。你的职责：用 web_search 工具查找用户需要的数据、"
            "事实或资料，并把检索到的关键信息清晰列出来（写进对话，供后续同事使用）。\n"
            "你不做数值计算，也不写最终成稿。检索完成后，如果接下来需要计算或写作，"
            "就移交给对应角色。"
        ) + _HANDOFF_RULES,
    ),
    "coding": Role(
        name="coding",
        title="编程专家",
        tools=["execute_python"],
        system_prompt=(
            "你是『编程专家』。你的职责：用 execute_python 写并运行代码来解决"
            "偏程序逻辑/脚本类的问题，并汇报运行结果。\n"
            "纯数学指标计算更适合 data_analysis；查资料更适合 research；"
            "写成稿更适合 writing。完成你的部分后按需移交。"
        ) + _HANDOFF_RULES,
    ),
    "data_analysis": Role(
        name="data_analysis",
        title="数据分析专家",
        tools=["calculate", "descriptive_stats"],
        system_prompt=(
            "你是『数据分析专家』。你的职责：基于对话里已有的数据，用 calculate / "
            "descriptive_stats 工具做定量计算与统计（如同比增长率、年均复合增长率 CAGR、"
            "均值等），并用文字清楚说明计算过程与结果。\n"
            "你不查资料也不写最终成稿。算完后如需润色成文，移交给 writing。"
        ) + _HANDOFF_RULES,
    ),
    "writing": Role(
        name="writing",
        title="写作专家",
        tools=["count_characters"],
        system_prompt=(
            "你是『写作专家』。你的职责：综合对话历史里检索到的数据和计算结论，"
            "写出一段通顺、结构清晰、面向指定读者的成稿。\n"
            "可以【最多一次】用 count_characters 粗略检查篇幅（这里的『字』指中文字符数）；"
            "不要反复核对字数，长度大致合适即可，切勿因为差几个字就反复重算。\n"
            "写好成稿后，立即调用 transfer_to_agent 把控制权移交回 triage 做收尾确认，"
            "不要停留在自己这一步。"
        ) + _HANDOFF_RULES,
    ),
}

DEFAULT_ROLE = "triage"


def transfer_tool_schema() -> dict:
    """transfer_to_agent 工具的 OpenAI schema —— 所有角色都持有它。"""
    return {
        "type": "function",
        "function": {
            "name": "transfer_to_agent",
            "description": (
                "把当前会话的控制权移交给另一个更合适的专业角色。"
                "移交后对方会继承完整对话历史。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_role": {
                        "type": "string",
                        "enum": list(ROLES.keys()),
                        "description": "要移交到的目标角色名",
                    },
                    "reason": {
                        "type": "string",
                        "description": "为什么移交、请对方做什么（简述）",
                    },
                },
                "required": ["target_role", "reason"],
            },
        },
    }
