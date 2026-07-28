"""
电话 Agent —— 一个把 PineClaw Voice（make_phone_call）当作工具的 ReAct Agent。

上层是标准的 ReAct 循环（OpenAI function calling 实现）：
    用户给一个任务（如"打电话给宽带客服，问清本月为何多扣 50 元并要求解释"）
        -> Agent 思考需要哪些参数（号码 / 目标 / 上下文）
        -> 调用 make_phone_call 工具完成整段通话
        -> 读取返回的【结构化通话记录】
        -> 若信息不足则追问/再拨，否则向用户给出最终汇报

工具 make_phone_call 由 pine_voice 模块提供（对真实 PineClaw Voice API 的本地模拟）。
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable

# 复用 pine_voice 里的统一 client/模型解析（OPENAI_API_KEY 直连，缺失则回退 OpenRouter）。
from pine_voice import make_phone_call, _get_client, default_model


def _create_chat(**kwargs):
    """推理模型（如 gpt-5.x）只接受默认 temperature，会拒绝自定义值；
    失败时移除 temperature 重试一次（同 book-translation / voice-werewolf）。"""
    try:
        return _get_client().chat.completions.create(**kwargs)
    except Exception as e:
        if "temperature" not in str(e).lower() or "temperature" not in kwargs:
            raise
        kwargs.pop("temperature", None)
        return _get_client().chat.completions.create(**kwargs)

# 最多允许 Agent 发起几次工具调用（含追问/再拨），防止死循环。
_MAX_STEPS = 6

_SYSTEM_PROMPT = (
    "你是一名『电话助理』Agent。用户会交给你一个需要打电话才能完成的任务，"
    "你要代表用户把电话打好并汇报结果。\n\n"
    "你有一个工具 make_phone_call，它会把整通电话（拨号、IVR 菜单导航、与客服多轮对话、"
    "转录）全部交给 PineClaw 语音 Agent 完成，并返回结构化通话记录。\n\n"
    "工作方式（ReAct）：\n"
    "1. 先想清楚要拨打的号码、通话目标、需要带上的上下文（账号/姓名/已知信息）。\n"
    "2. 调用 make_phone_call 完成通话。\n"
    "3. 读取返回的结构化记录（goal_achieved / key_fields / summary / transcript）。\n"
    "4. 若目标未达成或信息不足（follow_up_needed 为真），可以带着更明确的目标再拨一次"
    "（但总次数有限，不要无谓重拨）。\n"
    "5. 目标达成后，用简洁中文向用户汇报：结论 + 关键信息（金额/原因/确认号/时间等）"
    "+ 后续建议（如有）。\n\n"
    "注意：如果任务里连电话号码都没有，就用一个合理的占位号码并在汇报中说明。"
    "始终基于工具真实返回的通话记录来汇报，不要编造通话没有提到的信息。"
)

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "make_phone_call",
            "description": (
                "代表用户拨打一通真实电话。PineClaw 语音 Agent 会完成拨号、IVR 菜单导航、"
                "与对方多轮对话，并返回结构化通话记录（含 transcript、是否达成目标、"
                "抽取的关键字段）。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "被叫电话号码，如 10000 或 400-810-xxxx。",
                    },
                    "goal": {
                        "type": "string",
                        "description": "本次通话要达成的明确目标（一句话）。",
                    },
                    "context": {
                        "type": "string",
                        "description": "辅助上下文：账号、姓名、已知金额、时间等，可为空。",
                    },
                },
                "required": ["phone_number", "goal"],
            },
        },
    }
]


def run_agent(
    task: str,
    on_event: Callable[[str, Any], None] | None = None,
    *,
    model: str | None = None,
    phone_hint: str | None = None,
    goal_hint: str | None = None,
    dry_run: bool = False,
) -> str:
    """
    运行 ReAct 电话 Agent。

    参数：
        task:       用户的自然语言任务。
        on_event:   可选回调，用于外部观察 Agent 轨迹。
                    事件类型：'think'(Agent 思考文本) / 'call'(工具入参) /
                    'record'(结构化通话记录) / 'final'(最终汇报)。
        model:      覆盖使用的模型（默认取环境变量 OPENAI_MODEL）。
        phone_hint: 可选的电话号码；给定时作为已知信息交给 Agent（dry-run 下直接用作被叫号码）。
        goal_hint:  可选的通话目标；给定时作为已知信息交给 Agent（dry-run 下直接用作通话目标）。
        dry_run:    若为真，走完全离线的脚本化 ReAct 轨迹（不联网、不需要任何 API Key）。

    返回：
        Agent 面向用户的最终汇报文本。
    """

    def emit(kind: str, payload: Any) -> None:
        if on_event:
            on_event(kind, payload)

    if dry_run:
        return _run_agent_dryrun(task, emit, phone_hint, goal_hint)

    model = model or default_model()

    # 若显式给了号码/目标，就作为「已知信息」拼进用户消息，Agent 仍自行决定如何使用。
    hints = []
    if phone_hint:
        hints.append(f"已知对方电话号码：{phone_hint}")
    if goal_hint:
        hints.append(f"用户明确的通话目标：{goal_hint}")
    user_content = task if not hints else task + "\n\n（" + "；".join(hints) + "）"

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    for _ in range(_MAX_STEPS):
        resp = _create_chat(
            model=model,
            messages=messages,
            tools=_TOOLS,
            tool_choice="auto",
            temperature=0.3,
        )
        msg = resp.choices[0].message

        # 附上模型这一步返回的 assistant 消息（可能同时含思考文本与工具调用）。
        messages.append(msg.model_dump(exclude_none=True))

        if msg.content:
            emit("think", msg.content)

        if not msg.tool_calls:
            # 没有工具调用 = Agent 给出了最终答复。
            final = msg.content or ""
            emit("final", final)
            return final

        # 逐个执行工具调用（本例只有 make_phone_call）。
        for tc in msg.tool_calls:
            if tc.function.name != "make_phone_call":
                result = {"error": f"未知工具 {tc.function.name}"}
            else:
                # 模型偶尔产生截断/带杂质的 arguments；解析失败退回 {}，
                # 下方的 args.get 已带默认值，能优雅降级而不是中止整轮任务
                #（与 staged-system-prompt、multi-role-transfer 的防护一致）。
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                emit("call", args)
                result = make_phone_call(
                    phone_number=args.get("phone_number", "10000"),
                    goal=args.get("goal", task),
                    context=args.get("context", ""),
                    model=model,
                )
                emit("record", result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": "make_phone_call",
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    # 兜底：步数用尽仍未收敛，逼模型直接总结一次。
    messages.append(
        {
            "role": "user",
            "content": "请根据以上通话记录，立即给用户一份最终汇报，不要再打电话了。",
        }
    )
    resp = _create_chat(
        model=model, messages=messages, temperature=0.3
    )
    final = resp.choices[0].message.content or ""
    emit("final", final)
    return final


def _guess_phone(task: str) -> str | None:
    """从任务文本里粗略抽取一个像电话号码的数字串（>=4 位，避开『50 元』这类金额）。"""
    for m in re.finditer(r"\d{4,}", task):
        return m.group(0)
    return None


def _guess_context(task: str) -> str:
    """从任务文本里粗略抽取账号等上下文（仅用于 dry-run 的启发式，不求完备）。"""
    m = re.search(r"账[号户][^A-Za-z0-9]{0,3}([A-Za-z0-9][A-Za-z0-9\-]{2,})", task)
    if m:
        return f"账号 {m.group(1)}"
    return ""


def _run_agent_dryrun(
    task: str,
    emit: Callable[[str, Any], None],
    phone_hint: str | None,
    goal_hint: str | None,
) -> str:
    """
    完全离线的脚本化 ReAct 轨迹：不调用任何 LLM/电话 API，仅演示循环的形状——
    思考(推断参数) → 行动(make_phone_call, dry_run) → 观察(结构化记录) → 汇报。
    """
    phone = phone_hint or _guess_phone(task) or "10010"
    goal = goal_hint or task
    context = _guess_context(task)

    emit(
        "think",
        "这是一个需要打电话才能完成的任务。我先确定通话三要素——"
        f"号码={phone}；目标={goal}；上下文={context or '（无）'}。参数已足够，现在发起通话。",
    )

    call_args = {"phone_number": phone, "goal": goal, "context": context}
    emit("call", call_args)
    record = make_phone_call(**call_args, dry_run=True)
    emit("record", record)

    kf = record.get("key_fields", {}) or {}
    kf_text = "；".join(f"{k}={v}" for k, v in kf.items()) or "（无）"
    final = (
        f"已（dry-run 脚本模拟）拨打 {phone} 并完成通话。\n"
        f"结论：{record.get('summary', '')}\n"
        f"关键信息：{kf_text}。"
    )
    emit("final", final)
    return final
