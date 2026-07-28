"""
StagedAgent：根据“执行阶段”切换系统提示词与工具集的 Coding Agent。

设计要点（对应实验 10-1 的 6 项要求）：
1) 三个阶段各有明确角色的系统提示词（STAGE_PROMPTS）。
2) 每个阶段配套独立工具集（tools.STAGE*_TOOLS）。
3) 阶段转换由“特定工具调用”触发（complete_requirements_analysis /
   submit_for_review / request_revision / approve_code）。
4) 上下文跨阶段连续：self.history 一直累加，切阶段时只换掉 system 提示词，
   历史消息（含之前的需求、代码、审查意见）全部保留。
5) 审查发现问题时 request_revision 让流程回退到实现阶段。
6) 每一步都写入 self.logs，最后能看出不同提示词导致的不同行为。
"""

from __future__ import annotations

import json
from typing import Callable, Dict, List, Optional

from openai import OpenAI

from config import Config
from simulated_user import SimulatedUser
import tools as T


# ----------------------------------------------------------------------------
# 三个阶段的系统提示词——每个阶段一个明确的“角色”。
# ----------------------------------------------------------------------------
STAGE_PROMPTS: Dict[str, str] = {
    "requirements": (
        "你是一名严谨的【需求分析师】。当前处于【需求澄清阶段】。\n"
        "你的唯一职责是把用户模糊的需求问清楚，绝对不要写任何代码。\n"
        "工作方式：\n"
        "1. 针对不明确的地方，用 ask_clarifying_question 逐个提问（一次问一个）。\n"
        "2. 每当用户确认一个点，就用 save_requirement 把它记录下来。\n"
        "3. 把关键问题（处理哪些文件类型、是否递归子目录、是否保留原文件名、"
        "移动还是复制、目标目录如何指定等）都澄清并记录后，"
        "调用 complete_requirements_analysis 结束本阶段。\n"
        "记住：你不实现、不设计代码，只负责澄清和记录需求。"
    ),
    "implementation": (
        "你是一名资深【软件工程师】。当前处于【代码实现阶段】。\n"
        "上文已经有需求分析师确认好的需求，请严格按这些需求实现，不要自行增删功能。\n"
        "工作方式：\n"
        "1. 用 write_file 写出高质量、可读、带模块与函数 docstring 的 Python 代码，"
        "避免裸 except，注意异常处理。\n"
        "2. 可用 execute_code 做自测，确认逻辑正确、能运行。\n"
        "3. 代码完成并自测通过后，调用 submit_for_review 提交审查。\n"
        "如果是被审查阶段退回来的（历史里会有问题清单），"
        "请针对每一条问题逐个修复后再重新 submit_for_review。"
    ),
    "review": (
        "你是一名挑剔的【代码审查员】。当前处于【代码审查阶段】。\n"
        "你的职责是批判性地审查实现阶段提交的代码，把关质量。\n"
        "工作方式：\n"
        "1. 依次用 run_linter、run_tests、analyze_complexity 客观检查代码。\n"
        "2. 认真解读检查结果。只要 linter 报出问题、或测试失败，"
        "就必须调用 request_revision，把问题清单退回实现阶段修复。\n"
        "3. 只有当检查干净、测试通过、复杂度合理时，才调用 approve_code 批准。\n"
        "标准要严格，不要放过 linter 报出的问题。"
    ),
}

# 阶段名 -> 该阶段暴露的工具集
STAGE_TOOLS = {
    "requirements": T.STAGE1_TOOLS,
    "implementation": T.STAGE2_TOOLS,
    "review": T.STAGE3_TOOLS,
}

# 会触发阶段转换的“信号工具”集合
T_TRANSITION_TOOLS = {
    T.COMPLETE_REQUIREMENTS,
    T.SUBMIT_FOR_REVIEW,
    T.REQUEST_REVISION,
    T.APPROVE_CODE,
}

# 阶段名 -> 角色中文名（打印用）
STAGE_ROLE = {
    "requirements": "需求分析师",
    "implementation": "软件工程师",
    "review": "代码审查员",
}

# 阶段的线性顺序与打印标题
STAGE_ORDER = ["requirements", "implementation", "review"]
STAGE_TITLE = {
    "requirements": "阶段1 需求澄清",
    "implementation": "阶段2 代码实现",
    "review": "阶段3 代码审查",
}

# 从 requirements 之后的阶段起步时，用来预置的“已确认需求”。
# 取值与 simulated_user.py 中模拟用户会给出的答案一致，因此这是对
# 需求澄清阶段产物的忠实复现，而非凭空捏造，方便单独调试后两个阶段。
CANONICAL_REQUIREMENTS: Dict[str, str] = {
    "file_types": "图片(jpg/png/gif)、文档(pdf/doc/txt)、音频(mp3/wav)、"
                  "视频(mp4/mov)、压缩包(zip/rar)，其余归 Others",
    "recursive": "不递归，只整理下载文件夹当前这一层，忽略已有子文件夹",
    "naming": "保留原文件名；同名冲突时加 _1/_2 后缀避免覆盖",
    "move_or_copy": "移动（move），整理完原位置不再保留这些文件",
    "destination": "在下载文件夹内按类别建子目录"
                   "（Images/Documents/Audio/Video/Archives/Others）；"
                   "根路径用命令行参数传入，默认 ~/Downloads",
}


def stage_overview() -> str:
    """离线打印三阶段总览（角色 / 系统提示词 / 工具集 / 转换信号），无需 API Key。"""
    lines: List[str] = ["阶段化系统提示词 · 三阶段角色切换总览（离线，无需 API Key）"]
    for stage in STAGE_ORDER:
        tool_names = [t["function"]["name"] for t in STAGE_TOOLS[stage]]
        transitions = [n for n in tool_names if n in T_TRANSITION_TOOLS]
        normal = [n for n in tool_names if n not in T_TRANSITION_TOOLS]
        lines.append("")
        lines.append("=" * 70)
        lines.append(f"{STAGE_TITLE[stage]}  |  角色：{STAGE_ROLE[stage]}")
        lines.append("=" * 70)
        lines.append("系统提示词：")
        lines.append(STAGE_PROMPTS[stage])
        lines.append(f"工作工具：{normal}")
        lines.append(f"阶段转换信号工具：{transitions}")
    lines.append("")
    lines.append("阶段转换关系：")
    lines.append("  requirements  --complete_requirements_analysis-->  implementation")
    lines.append("  implementation  --submit_for_review-->  review")
    lines.append("  review  --request_revision-->  implementation  （审查不通过，回退重写）")
    lines.append("  review  --approve_code-->  完成")
    return "\n".join(lines)


class StagedAgent:
    def __init__(
        self,
        max_revisions: int = 2,
        verbose: bool = True,
        interactive: bool = False,
    ) -> None:
        Config.validate()
        self.client = OpenAI(api_key=Config.API_KEY, base_url=Config.BASE_URL)
        self.model = Config.MODEL

        self.workspace = T.Workspace()
        self.sim_user = SimulatedUser()

        # 跨阶段共享的对话历史（不含 system 提示词，system 每阶段单独拼）
        self.history: List[dict] = []
        # 结构化执行日志：每条 = {stage, role, action, detail}
        self.logs: List[dict] = []

        self.stage = "requirements"
        self.revision_count = 0
        self.max_revisions = max_revisions
        self.verbose = verbose
        # interactive=True 时，需求澄清阶段的问题改由真人从标准输入回答；
        # 默认 False 走 SimulatedUser 预设答案，可无人值守跑通全流程。
        self.interactive = interactive

    # --- 日志与打印 ------------------------------------------------------
    def _log(self, action: str, detail: str) -> None:
        entry = {
            "stage": self.stage,
            "role": STAGE_ROLE[self.stage],
            "action": action,
            "detail": detail,
        }
        self.logs.append(entry)
        if self.verbose:
            print(f"[{STAGE_ROLE[self.stage]}] {action}: {detail}")

    def _banner(self, text: str) -> None:
        if self.verbose:
            print("\n" + "=" * 70)
            print(text)
            print("=" * 70)

    # --- 工具分发 --------------------------------------------------------
    def _dispatch_tool(self, name: str, args: dict) -> str:
        """执行普通工具（非阶段转换工具），返回给模型的工具结果字符串。"""
        if name == "ask_clarifying_question":
            # 模型偶尔对必填字段显式传 null：.get(..., "") 兜不住 None。
            question = args.get("question") or ""
            self._log("提问", question)
            if self.interactive:
                answer = input(f"  [请回答需求分析师的问题] {question}\n  > ").strip()
                answer = answer or "没有特别要求，按常识处理即可。"
                self._log("用户回答", answer)
            else:
                answer = self.sim_user.answer(question)
                self._log("模拟用户回答", answer)
            return answer
        if name == "save_requirement":
            res = self.workspace.save_requirement(args.get("key", ""), args.get("value", ""))
            self._log("记录需求", f"{args.get('key')} = {args.get('value')}")
            return res
        if name == "write_file":
            # 模型偶尔对必填字段显式传 null：.get(..., "") 兜不住 None，统一归一化为空串。
            res = self.workspace.write_file(args.get("path") or "", args.get("content") or "")
            self._log("写文件", res)
            return res
        if name == "read_file":
            self._log("读文件", args.get("path", ""))
            return self.workspace.read_file(args.get("path", ""))
        if name == "execute_code":
            code = args.get("code") or ""
            self._log("执行代码自测", code[:80].replace("\n", " ") + " ...")
            return self.workspace.execute_code(code)
        if name == "run_linter":
            res = self.workspace.run_linter(args.get("file", ""))
            self._log("run_linter", res.splitlines()[0])
            return res
        if name == "run_tests":
            res = self.workspace.run_tests(args.get("file", ""))
            self._log("run_tests", res.splitlines()[0])
            return res
        if name == "analyze_complexity":
            res = self.workspace.analyze_complexity(args.get("file", ""))
            self._log("analyze_complexity", res)
            return res
        return f"未知工具：{name}"

    # --- 主流程 ----------------------------------------------------------
    def run(self, user_task: str, start_stage: str = "requirements") -> None:
        # 用户的初始任务，作为共享上下文的第一条消息
        self.history.append({"role": "user", "content": user_task})
        self._banner(f"用户任务：{user_task}")

        # 阶段状态机：一直跑到 approve_code 或超过安全上限
        max_total_steps = 40
        steps = 0
        done = False

        if start_stage == "implementation":
            # 跳过需求澄清，直接从实现阶段起步：预置一份等价于需求澄清产物的
            # 已确认需求，方便单独调试实现/审查两个阶段而不必每次重跑澄清对话。
            self._seed_requirements()
            self._enter_stage("implementation")
        else:
            self._enter_stage("requirements")

        while not done and steps < max_total_steps:
            steps += 1
            done = self._run_one_model_turn()

        if not done:
            self._banner("达到步数上限，演示结束（未收到 approve_code）。")

    def _seed_requirements(self) -> None:
        """从 requirements 之后的阶段起步时，预置一份已确认需求并注入交接消息。"""
        self.workspace.requirements = dict(CANONICAL_REQUIREMENTS)
        reqs = "\n".join(f"- {k}: {v}" for k, v in self.workspace.requirements.items())
        self.history.append({
            "role": "user",
            "content": (
                "【阶段交接】（--start-stage 跳过了需求澄清）需求分析师已确认如下需求，"
                "请据此实现：\n" + reqs
            ),
        })
        self._log_seed(reqs)

    def _log_seed(self, reqs: str) -> None:
        if self.verbose:
            self._banner("已预置需求（跳过需求澄清阶段）")
            print(reqs)

    def _enter_stage(self, stage: str) -> None:
        self.stage = stage
        self._banner(
            f"进入阶段：{stage}  |  角色：{STAGE_ROLE[stage]}  |  "
            f"可用工具：{[t['function']['name'] for t in STAGE_TOOLS[stage]]}"
        )

    def _run_one_model_turn(self) -> bool:
        """
        调一次模型；执行它请求的所有工具调用。
        返回 True 表示整个任务结束（approve_code）。
        阶段转换工具会切换 self.stage 并立刻返回，让下一轮用新提示词+新工具。
        """
        messages = [{"role": "system", "content": STAGE_PROMPTS[self.stage]}] + self.history
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=STAGE_TOOLS[self.stage],
                temperature=Config.TEMPERATURE,
            )
        except Exception as exc:  # noqa: BLE001
            # 部分推理模型（如 gpt-5.x）只接受默认温度，显式传 temperature 会 400。
            # 识别到与温度相关的报错时，去掉 temperature 重试一次。
            if "temperature" in str(exc).lower():
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=STAGE_TOOLS[self.stage],
                )
            else:
                raise
        msg = response.choices[0].message

        # 把助手消息（可能含 tool_calls）加入共享历史
        assistant_entry: dict = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            assistant_entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]
        self.history.append(assistant_entry)

        if msg.content and msg.content.strip():
            self._log("思考/发言", msg.content.strip())

        # 没有工具调用：模型只是说话。提示它继续使用工具推进。
        if not msg.tool_calls:
            self.history.append({
                "role": "user",
                "content": "请使用当前阶段提供的工具继续推进任务。",
            })
            return False

        # 逐个处理本轮所有工具调用。
        # 注意：即使遇到“阶段转换工具”，也必须先把这条 assistant 消息里的
        # 每一个 tool_call 都回一条 tool 消息（OpenAI 协议强制要求），
        # 因此把真正的阶段切换/上下文交接推迟到所有工具都响应完之后再做。
        pending_transition: Optional[dict] = None
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            if name in T_TRANSITION_TOOLS:
                tool_result, descriptor = self._transition_result(name, args)
                # 只认第一个转换工具，其余转换工具只作普通响应
                if pending_transition is None:
                    pending_transition = descriptor
            else:
                tool_result = self._dispatch_tool(name, args)

            self.history.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_result,
            })

        # 所有 tool 消息都补齐后，再执行阶段切换与上下文交接
        if pending_transition is not None:
            return self._apply_transition(pending_transition)
        return False

    def _transition_result(self, name: str, args: dict):
        """
        计算阶段转换工具要回给模型的 tool 结果字符串，并返回一个 descriptor
        描述“稍后要执行的切换动作”。此函数只记录日志，不改动 history / 阶段。
        返回 (tool_result_str, descriptor_dict)。
        """
        if name == T.COMPLETE_REQUIREMENTS:
            summary = args.get("summary", "")
            self._log("完成需求分析 -> 转交实现", summary)
            return (
                f"需求分析完成：{summary}。即将进入代码实现阶段。",
                {"kind": "to_implementation"},
            )

        if name == T.SUBMIT_FOR_REVIEW:
            file = args.get("file", "")
            self._log("提交审查 -> 转交审查", file)
            return (
                f"已提交 {file}，即将进入审查阶段。",
                {"kind": "to_review", "file": file},
            )

        if name == T.REQUEST_REVISION:
            issues = args.get("issues")
            if issues is None:
                issues = []
            if isinstance(issues, str):
                issues = [issues]
            self.workspace.review_issues = list(issues)
            self.revision_count += 1
            self._log("审查不通过 -> 回退实现", f"第{self.revision_count}次退回：{issues}")
            return (
                "已把问题清单退回实现阶段。",
                {"kind": "request_revision", "issues": list(issues)},
            )

        if name == T.APPROVE_CODE:
            comment = args.get("comment", "")
            self._log("审查通过 -> 任务完成", comment)
            return (f"代码已批准：{comment}", {"kind": "approve"})

        return ("未知的转换工具。", {"kind": "noop"})

    def _apply_transition(self, descriptor: dict) -> bool:
        """
        真正执行阶段切换：注入跨阶段交接的 user 消息 + 切换 self.stage。
        返回 True 表示整个任务结束。
        """
        kind = descriptor["kind"]

        if kind == "to_implementation":
            reqs = "\n".join(f"- {k}: {v}" for k, v in self.workspace.requirements.items())
            self.history.append({
                "role": "user",
                "content": (
                    "【阶段交接】需求分析已完成。已确认的需求如下，请据此实现：\n"
                    + (reqs or "（无显式记录）")
                ),
            })
            self._enter_stage("implementation")
            return False

        if kind == "to_review":
            file = descriptor.get("file", "")
            self.history.append({
                "role": "user",
                "content": (
                    f"【阶段交接】实现阶段已提交文件 `{file}` 供审查。"
                    f"当前工作区文件：{list(self.workspace.files)}。请开始严格审查。"
                ),
            })
            self._enter_stage("review")
            return False

        if kind == "request_revision":
            # 安全阀：回退次数过多则强制收尾，避免无限循环烧 token
            if self.revision_count > self.max_revisions:
                self._log("回退次数达上限", "强制结束演示")
                self.history.append({
                    "role": "user",
                    "content": "【系统】回退次数已达上限，演示到此结束。",
                })
                return True
            issue_text = "\n".join(f"- {x}" for x in (descriptor.get("issues") or []))
            self.history.append({
                "role": "user",
                "content": (
                    "【阶段交接·回退】审查未通过，需修复以下问题后重新提交：\n"
                    + issue_text
                ),
            })
            self._enter_stage("implementation")
            return False

        if kind == "approve":
            return True

        return False

    # --- 演示后打印小结 --------------------------------------------------
    def print_summary(self) -> None:
        self._banner("执行小结")
        # 统计每个阶段的动作，展示“不同提示词 -> 不同行为模式”
        by_stage: Dict[str, List[str]] = {}
        for e in self.logs:
            by_stage.setdefault(e["role"], []).append(e["action"])
        for role, actions in by_stage.items():
            from collections import Counter
            counts = Counter(actions)
            summary = ", ".join(f"{a}×{n}" for a, n in counts.items())
            print(f"[{role}] 行为分布：{summary}")

        print(f"\n已确认需求条数：{len(self.workspace.requirements)}")
        print(f"产出文件：{list(self.workspace.files)}")
        print(f"审查回退次数：{self.revision_count}")
