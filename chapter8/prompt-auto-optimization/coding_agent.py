"""
Coding Agent：读取系统提示词文件 → 定位相关规则 → 生成精确的搜索/替换编辑 → 真的改写文件。

它的工作方式和真实的编程 Agent（如 Claude Code / Cursor）一致：
不是让模型整篇重写，而是让模型产出一组 (old_str -> new_str) 的精确编辑，
由代码逐条做"精确字符串替换"落到文件里；若某条编辑的 old_str 匹配不上，
把错误反馈回模型让它重试。这样修改是"代码级"的、可审计的（能直接出 diff）。
"""

import difflib
import json
from config import get_client, get_model, get_temperature

# 暴露给 Coding Agent 的"文件编辑工具"
EDIT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "apply_edits",
            "description": (
                "对提示词文件应用一组精确的搜索/替换编辑。每条编辑给出 old_str "
                "（文件中唯一存在的原文片段）和 new_str（替换后的新文本）。"
                "old_str 必须与文件内容逐字符完全一致。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "edits": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "old_str": {"type": "string"},
                                "new_str": {"type": "string"},
                            },
                            "required": ["old_str", "new_str"],
                        },
                    },
                    "rationale": {
                        "type": "string",
                        "description": "简述本次改动如何回应人类反馈。",
                    },
                },
                "required": ["edits"],
            },
        },
    }
]


def _apply_one(content: str, old_str: str, new_str: str) -> tuple[str, str | None]:
    """尝试应用一条编辑。成功返回(新内容, None)，失败返回(原内容, 错误信息)。"""
    if old_str is None or new_str is None:
        return content, "old_str/new_str 不能为 null"
    count = content.count(old_str)
    if count == 0:
        return content, f"old_str 在文件中未找到：{old_str[:60]!r}"
    if count > 1:
        return content, f"old_str 在文件中出现 {count} 次（不唯一）：{old_str[:60]!r}"
    return content.replace(old_str, new_str, 1), None


def _apply_edits_from_args(working: str, args: dict) -> tuple[str, int, list, list]:
    """Apply apply_edits tool args to working text. JSON null edits like omit ([])."""
    edits = args.get("edits")
    if edits is None:
        edits = []
    errors = []
    applied = 0
    for e in edits:
        working, err = _apply_one(working, e.get("old_str", ""), e.get("new_str", ""))
        if err:
            errors.append(err)
        else:
            applied += 1
    return working, applied, errors, edits


def optimize_prompt(prompt_path: str, feedback, max_rounds: int = 3, verbose: bool = True) -> dict:
    """
    让 Coding Agent 根据 human feedback 改写 prompt_path 指向的文件（原地覆盖）。

    返回 {"before": 原文, "after": 新文, "diff": 统一 diff 文本, "rationale": 说明}。
    """
    client = get_client()
    model = get_model()

    with open(prompt_path, "r", encoding="utf-8") as f:
        original = f.read()

    feedback_text = json.dumps(feedback, ensure_ascii=False, indent=2) if isinstance(feedback, dict) else str(feedback)

    system = (
        "你是一名资深的提示词工程 Coding Agent。你会收到一份航空客服 Agent 的"
        "系统提示词文件，以及从失败轨迹生成的结构化诊断。请定位与'人工转接'相关的规则，"
        "生成精确的搜索/替换编辑来改进它，然后调用 apply_edits 工具落地修改。\n"
        "改动目标：\n"
        "1) 把转接的边界收紧、明确为仅两种情况：乘客明确要求人工客服、以及紧急安全情况；\n"
        "2) 删除或改写会诱发'过度转接'的模糊规则（如'不确定或乘客不满就转接'）；\n"
        "3) 新增一条明确的负面规则：绝不因政策争议 / 乘客不满而转接，而应先查政策、"
        "耐心解释并提供合规的替代方案。\n"
        "只修改与转接策略相关的部分，尽量保留其余内容不动。"
    )

    messages = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                f"【失败轨迹诊断】\n{feedback_text}\n\n"
                f"【当前系统提示词文件内容】\n---\n{original}\n---\n\n"
                "请调用 apply_edits 提交你的精确编辑。"
            ),
        },
    ]

    working = original
    rationale = ""

    for round_idx in range(max_rounds):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=EDIT_TOOLS,
            tool_choice={"type": "function", "function": {"name": "apply_edits"}},
            temperature=get_temperature(),
        )
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            break

        # 处理（唯一的）apply_edits 调用
        tc = msg.tool_calls[0]
        try:
            args = json.loads(tc.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        rationale = args.get("rationale", rationale)
        working, applied, errors, edits = _apply_edits_from_args(working, args)

        if verbose:
            print(f"  [round {round_idx + 1}] 提交 {len(edits)} 条编辑，成功 {applied}，失败 {len(errors)}")

        if not errors:
            # 全部编辑成功，落盘
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": "所有编辑已成功应用。"}
            )
            break
        else:
            # 有失败：回滚到原文，把错误反馈给模型重试（保持编辑的原子性）
            working = original
            feedback_msg = (
                "以下编辑未能应用，请修正后重新提交完整的编辑列表（注意 old_str 必须与文件逐字符一致）：\n"
                + "\n".join(f"- {er}" for er in errors)
            )
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": feedback_msg})

    # 落盘（原地覆盖 prompt 文件）
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(working)

    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            working.splitlines(keepends=True),
            fromfile="system_prompt.txt (before)",
            tofile="system_prompt.txt (after)",
        )
    )

    return {"before": original, "after": working, "diff": diff, "rationale": rationale}
