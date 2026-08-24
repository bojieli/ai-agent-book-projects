"""把中立轨迹渲染成某一家的线上格式。

三条臂对应三种做法：

* ``naive``   直传。把上一家原样返回的 payload 按字段名对应搬进新一家的结构，
  思考和凭证一并带过去——这是不做任何处理时最自然的写法。
* ``strip``   一刀切。删掉全部思考与凭证，只留正文、工具调用和结果。
* ``neutral`` 中立。凭证丢弃，可移植的明文或摘要以**普通文本**的身份带走，
  工具调用 id 按目标厂商重铸；遇到强制要求凭证的接收端，把历史调用拍平成文本。

三条臂只管**别家产生的**那些步骤。目标厂商自己产生的步骤一律原样回传，连同它
自己签发的凭证——切换之后模型还要接着往下跑，把它自己刚签的名删掉同样会报错。
"""

from __future__ import annotations

import json

from neutral_trace import Trace
from providers import ANTHROPIC, GEMINI, KIMI

NAIVE, STRIP, NEUTRAL = "naive", "strip", "neutral"
ARMS = (NAIVE, STRIP, NEUTRAL)

# 中立臂把上一家的思考作为普通文本带入时用的前缀。加一个来源标签，模型才知道
# 这段话是上一个模型留下的记录，而不是用户说的。
CARRY_PREFIX = "［接手前由 {issuer} 留下的思考记录］"


def _carried_text(step) -> str | None:
    r = step.reasoning
    if not r or not r.portable_text:
        return None
    return CARRY_PREFIX.format(issuer=r.issuer) + r.portable_text.strip()


def _mint(target: str, index: int) -> str:
    return {ANTHROPIC: f"toolu_x{index:04d}", GEMINI: f"call_{index}", KIMI: f"call_{index}"}[target]


def render(target: str, trace: Trace, arm: str, tools: list[dict], model: str,
           system: str | None = None) -> dict:
    if target == KIMI:
        return _kimi(trace, arm, tools, model, system)
    if target == ANTHROPIC:
        return _anthropic(trace, arm, tools, model, system)
    if target == GEMINI:
        return _gemini(trace, arm, tools, model, system)
    raise ValueError(target)


# --------------------------------------------------------------------------- Kimi
def _kimi(trace: Trace, arm: str, tools: list[dict], model: str, system: str | None) -> dict:
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    ids: dict[str, str] = {}
    for i, step in enumerate(trace.steps):
        if step.role == "user":
            messages.append({"role": "user", "content": step.text})
        elif step.role == "tool":
            messages.append({"role": "tool", "tool_call_id": ids.get(step.tool_call_id, step.tool_call_id),
                             "content": step.text})
        else:
            messages.append(_kimi_assistant(step, arm, ids, i))
    return {"model": model, "messages": messages, "tools": tools}


def _kimi_assistant(step, arm: str, ids: dict, i: int) -> dict:
    own = step.issuer == KIMI
    calls = []
    for j, c in enumerate(step.tool_calls):
        cid = c.call_id if (arm != NEUTRAL or own) else _mint(KIMI, i * 10 + j)
        ids[c.call_id] = cid
        calls.append({"id": cid, "type": "function",
                      "function": {"name": c.name, "arguments": json.dumps(c.arguments, ensure_ascii=False)}})
    msg = {"role": "assistant", "content": step.text or ""}
    if calls:
        msg["tool_calls"] = calls
    if step.reasoning and (own or arm == NAIVE):
        # 字段名对得上就照搬，凭证也一起搬——Moonshot 不校验，所以能过。
        msg["reasoning_content"] = step.reasoning.text
        if step.reasoning.credential:
            msg["signature"] = step.reasoning.credential
    elif arm == NEUTRAL:
        carried = _carried_text(step)
        if carried:
            msg["content"] = (carried + "\n\n" + (step.text or "")).strip()
    return msg


# ----------------------------------------------------------------------- Anthropic
def _anthropic(trace: Trace, arm: str, tools: list[dict], model: str, system: str | None) -> dict:
    ant_tools = [{"name": t["function"]["name"], "description": t["function"]["description"],
                  "input_schema": t["function"]["parameters"]} for t in tools]
    messages: list[dict] = []
    ids: dict[str, str] = {}
    for i, step in enumerate(trace.steps):
        if step.role == "user":
            messages.append({"role": "user", "content": step.text})
        elif step.role == "tool":
            block = {"type": "tool_result", "tool_use_id": ids.get(step.tool_call_id, step.tool_call_id),
                     "content": step.text}
            if messages and messages[-1]["role"] == "user" and isinstance(messages[-1]["content"], list):
                messages[-1]["content"].append(block)
            else:
                messages.append({"role": "user", "content": [block]})
        else:
            messages.append({"role": "assistant", "content": _anthropic_blocks(step, arm, ids, i)})
    body = {"model": model, "max_tokens": 4096, "thinking": {"type": "enabled", "budget_tokens": 2048},
            "tools": ant_tools, "messages": messages}
    if system:
        body["system"] = system
    return body


def _anthropic_blocks(step, arm: str, ids: dict, i: int) -> list[dict]:
    blocks: list[dict] = []
    own = step.issuer == ANTHROPIC
    if step.reasoning and step.reasoning.text and (own or arm == NAIVE):
        # 自己签的名原样带回；别家的思考塞进 thinking 槽位，要么缺签名、要么签名
        # 是别家签的，两种都过不了验签——直传臂测的正是这一点。
        think = {"type": "thinking", "thinking": step.reasoning.text}
        if step.reasoning.credential:
            think["signature"] = step.reasoning.credential
        blocks.append(think)
    elif arm == NEUTRAL:
        carried = _carried_text(step)
        if carried:
            blocks.append({"type": "text", "text": carried})
    if step.text:
        blocks.append({"type": "text", "text": step.text})
    for j, c in enumerate(step.tool_calls):
        cid = c.call_id if (arm != NEUTRAL or own) else _mint(ANTHROPIC, i * 10 + j)
        ids[c.call_id] = cid
        blocks.append({"type": "tool_use", "id": cid, "name": c.name, "input": c.arguments})
    return blocks or [{"type": "text", "text": "（无输出）"}]


# -------------------------------------------------------------------------- Gemini
def _gemini(trace: Trace, arm: str, tools: list[dict], model: str, system: str | None) -> dict:
    decls = [{"name": t["function"]["name"], "description": t["function"]["description"],
              "parameters": t["function"]["parameters"]} for t in tools]
    contents: list[dict] = []
    flattened: set[str] = set()

    def push(role: str, parts: list[dict]) -> None:
        if contents and contents[-1]["role"] == role:
            contents[-1]["parts"].extend(parts)
        else:
            contents.append({"role": role, "parts": parts})

    for step in trace.steps:
        if step.role == "user":
            push("user", [{"text": step.text}])
        elif step.role == "tool":
            if step.tool_call_id in flattened:
                # 发起这次调用的那一步被拍平成了文本，结果也只能以文本回去。
                push("user", [{"text": f"{step.tool_name} 的返回结果：{step.text}"}])
            else:
                push("user", [{"functionResponse": {"name": step.tool_name,
                                                    "response": {"result": step.text}}}])
        else:
            parts, flat = _gemini_parts(step, arm)
            flattened.update(flat)
            push("model", parts)

    body = {"contents": contents, "tools": [{"functionDeclarations": decls}],
            "generationConfig": {"thinkingConfig": {"includeThoughts": True}},
            "_model": model}
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    return body


def _gemini_parts(step, arm: str) -> tuple[list[dict], set[str]]:
    """返回 (parts, 被拍平成文本的 call_id 集合)。"""
    own = step.issuer == GEMINI
    if arm == NEUTRAL and not own:
        # 强制凭证的接收端拿不到别家的签名，这一步只能拍平成叙述。
        pieces = [t for t in (_carried_text(step), step.text) if t]
        for c in step.tool_calls:
            pieces.append(f"我调用了 {c.name}({json.dumps(c.arguments, ensure_ascii=False)})。")
        return [{"text": "\n".join(pieces) or "（无输出）"}], {c.call_id for c in step.tool_calls}

    parts: list[dict] = []
    usable = step.reasoning and (own or arm == NAIVE)
    if usable and step.reasoning.text:
        parts.append({"text": step.reasoning.text, "thought": True})
    if step.text:
        parts.append({"text": step.text})
    for c in step.tool_calls:
        part = {"functionCall": {"name": c.name, "args": c.arguments}}
        if usable and step.reasoning.credential:
            part["thoughtSignature"] = step.reasoning.credential
        parts.append(part)
    return (parts or [{"text": "（无输出）"}]), set()
