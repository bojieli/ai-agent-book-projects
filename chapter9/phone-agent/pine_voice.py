"""
pine_voice —— PineClaw Voice API 的本地【模拟】客户端。

真实的 PineClaw Voice API（https://pineclaw.com/ ，作者团队开发）是一套生产级
电话语音 API：你把「电话号码 + 目标 + 上下文」交给它，它的语音 Agent 会自动完成
拨号、IVR 菜单导航（"查询请按 1，转人工请按 0"）、与真人多轮对话、实时转录，
最后把整段通话浓缩成一份【结构化通话记录】返回。

本文件不接触真实电话网络，也不需要 PineClaw key。它用 OpenAI 扮演「被叫方」
（IVR 语音菜单 + 人工客服）与「去电的语音 Agent」进行一段多轮对话，从而在本地
复现同样的输入/输出契约：

    record = make_phone_call(phone_number, goal, context)

返回的 record 与真实 API 的形状保持一致（transcript / goal_achieved / key_fields ...），
因此上层 ReAct Agent 的代码在切换到真实 PineClaw SDK 时几乎无需改动。

真实接入方式见本目录 README.md「真实接入 PineClaw」一节。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

from openai import OpenAI

# 默认聊天模型：当前便宜旗舰。可用 OPENAI_MODEL 覆盖（如 Moonshot 的 kimi-k3）。
_DEFAULT_MODEL = "gpt-5.6-luna"


def _map_openrouter_model(model: str) -> str:
    """把常见模型名映射为 OpenRouter 的 provider/model 形式。"""
    if "/" in model:            # 已是 provider/model，原样透传
        return model
    if model.startswith("gpt-"):
        return "openai/" + model
    if model.startswith("claude-"):
        return "anthropic/claude-opus-4.8"
    return "openai/gpt-5.6-luna"


# 延迟创建 client：缺 Key 时由 demo.py 给出友好提示，而非 import 期裸异常。
# 通用回退：优先 OPENAI_API_KEY（可选 OPENAI_BASE_URL 指向兼容网关，如 Moonshot），
# 否则用 OPENROUTER_API_KEY 走 OpenRouter，否则给出清晰错误。
# timeout + 自动重试，避免单次网络/SSL 抖动让整段模拟通话崩溃。
_client = None
_active_model = None


def _resolve() -> tuple[OpenAI, str]:
    global _client, _active_model
    if _client is not None:
        return _client, _active_model
    model = os.getenv("OPENAI_MODEL") or _DEFAULT_MODEL
    if os.getenv("OPENAI_API_KEY"):
        # 直连 OpenAI（或 OPENAI_BASE_URL 指定的兼容网关，如 Moonshot kimi-k3）。
        _client = OpenAI(
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            timeout=60.0,
            max_retries=3,
        )
        _active_model = model
    elif os.getenv("OPENROUTER_API_KEY"):
        # 回退到 OpenRouter：注意 gpt-5.6* 直连 OpenAI 需组织实名认证，走 OpenRouter 免此步。
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            timeout=60.0,
            max_retries=3,
        )
        _active_model = _map_openrouter_model(model)
    else:
        raise RuntimeError(
            "未检测到 OPENAI_API_KEY 或 OPENROUTER_API_KEY。请在 .env / 环境变量中至少配置其一"
            "（见 env.example），或用 python demo.py --dry-run 走完全离线的脚本演示。"
        )
    return _client, _active_model


def _get_client() -> OpenAI:
    return _resolve()[0]


def default_model() -> str:
    """当前生效的聊天模型名（已按 OpenRouter 映射解析）。"""
    return _resolve()[1]

# 一次模拟通话里「去电语音 Agent ↔ 被叫方」最多来回的轮数（一轮 = 双方各说一次）。
_MAX_TURNS = 8

# 结束标记：去电语音 Agent 认为通话目标已完成/无法推进时，在发言末尾附上它。
_END_TOKEN = "[END_CALL]"


# --------------------------------------------------------------------------- #
# 结构化通话记录 —— 与真实 PineClaw Voice API 返回体保持同一形状
# --------------------------------------------------------------------------- #
@dataclass
class CallRecord:
    call_id: str
    phone_number: str
    goal: str
    status: str                       # "completed" / "failed"
    goal_achieved: bool               # 是否达成通话目标
    duration_seconds: int             # 通话时长（模拟值）
    summary: str                      # 一句话通话摘要
    key_fields: dict[str, Any]        # 从通话中抽取的关键信息（确认号、金额、时间...）
    transcript: list[dict[str, str]]  # 逐轮对话：{"speaker": ..., "text": ...}
    follow_up_needed: bool            # 是否仍需追问/再拨
    follow_up_reason: str             # 若需追问，原因是什么

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# 内部：调用 OpenAI 生成一次发言
# --------------------------------------------------------------------------- #
def _chat(
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    model: str | None = None,
) -> str:
    kwargs = dict(
        model=model or default_model(),
        messages=messages,
        temperature=temperature,
    )
    try:
        resp = _get_client().chat.completions.create(**kwargs)
    except Exception as e:
        # 推理模型（如 gpt-5.x）只接受默认 temperature，会拒绝自定义值；
        # 移除该参数重试一次（同 book-translation / voice-werewolf 的做法）。
        if "temperature" not in str(e).lower():
            raise
        kwargs.pop("temperature", None)
        resp = _get_client().chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()


def _callee_system_prompt(goal: str, context: str) -> str:
    """被叫方：先当自动 IVR 语音菜单，被转人工后再扮演人工客服。"""
    return (
        "你在参与一段【电话客服】通话的角色扮演，扮演【被叫方】（企业客服热线）。\n"
        "整通电话分两个阶段，请自然衔接：\n"
        "1) 开场你是【自动语音应答（IVR）系统】：先播报欢迎语，再报一个简短的按键菜单"
        "（例如『账单查询请按 1，业务办理请按 2，人工服务请按 0』）。\n"
        "2) 当来电者选择转人工（按 0 或明确要求人工）后，你切换为【人工客服代表】，"
        "自报工号，然后正常应答。\n\n"
        "扮演要求：\n"
        "- 全程用简体中文口语，像真实电话一样简短自然，不要旁白、不要括号动作。\n"
        "- 你可以合理编造本企业的业务细节（如扣费原因、套餐、确认号），要具体、前后一致。\n"
        f"- 来电者此行的目标大致是：{goal}\n"
        "- 你不必无条件满足对方，可以先解释、再看情况处理；但对方礼貌且诉求合理时，"
        "应能给出明确结论（原因/处理结果/确认号等）。\n"
        "- 每次只说你（被叫方）这一方的一段话，不要替对方说话。"
    )


def _caller_system_prompt(phone_number: str, goal: str, context: str) -> str:
    """去电的语音 Agent：代表用户拨打电话、导航 IVR、达成目标。"""
    return (
        "你是 PineClaw 电话语音 Agent，正代表用户拨打一通真实电话去办事。\n"
        f"- 拨打号码：{phone_number}\n"
        f"- 通话目标：{goal}\n"
        f"- 已知上下文：{context or '（无额外上下文）'}\n\n"
        "行为要求：\n"
        "- 全程用简体中文口语，礼貌、简短、直奔目标。\n"
        "- 开场若遇到 IVR 按键菜单，请明确说出你的选择（如『我按 0 转人工』）来导航。\n"
        "- 接通人工后清晰说明来意，围绕目标追问，主动核对并记住关键信息"
        "（金额、原因、确认号、时间等）。\n"
        "- 目标达成、或对方明确无法处理时，礼貌道谢结束通话，并在该句结尾附上标记 "
        f"{_END_TOKEN}。\n"
        "- 每次只说你（来电者）这一方的一段话，不要替对方说话，也不要附加旁白。"
    )


def _run_dialog(
    phone_number: str, goal: str, context: str, model: str | None = None
) -> list[dict[str, str]]:
    """驱动两个 LLM 角色来回对话，产出逐轮 transcript。"""
    caller_sys = _caller_system_prompt(phone_number, goal, context)
    callee_sys = _callee_system_prompt(goal, context)

    # 各自维护自己视角的消息历史。
    caller_msgs = [{"role": "system", "content": caller_sys}]
    callee_msgs = [{"role": "system", "content": callee_sys}]

    transcript: list[dict[str, str]] = []

    # 被叫方先开口（IVR 欢迎语 + 菜单）。
    callee_msgs.append({"role": "user", "content": "（电话已接通，请开始。）"})
    callee_line = _chat(callee_msgs, model=model)
    callee_msgs.append({"role": "assistant", "content": callee_line})
    caller_msgs.append({"role": "user", "content": callee_line})
    transcript.append({"speaker": "被叫方", "text": callee_line})

    for _ in range(_MAX_TURNS):
        # 去电语音 Agent 发言
        caller_line = _chat(caller_msgs, model=model)
        ended = _END_TOKEN in caller_line
        caller_line_clean = caller_line.replace(_END_TOKEN, "").strip()
        caller_msgs.append({"role": "assistant", "content": caller_line})
        callee_msgs.append({"role": "user", "content": caller_line_clean})
        transcript.append({"speaker": "语音Agent", "text": caller_line_clean})
        if ended:
            break

        # 被叫方回应
        callee_line = _chat(callee_msgs, model=model)
        callee_msgs.append({"role": "assistant", "content": callee_line})
        caller_msgs.append({"role": "user", "content": callee_line})
        transcript.append({"speaker": "被叫方", "text": callee_line})

    return transcript


def _extract_structured(
    goal: str, transcript: list[dict[str, str]], model: str | None = None
) -> dict[str, Any]:
    """通话结束后，用一次 LLM 调用把 transcript 归纳为结构化字段。"""
    dialog_text = "\n".join(f"{t['speaker']}：{t['text']}" for t in transcript)
    prompt = (
        "下面是一段电话通话的完整转录。请你作为通话分析器，输出一个 JSON 对象，字段如下：\n"
        '  "goal_achieved": 布尔，本次通话是否达成了给定目标；\n'
        '  "summary": 字符串，一句话中文通话摘要；\n'
        '  "key_fields": 对象，从通话中抽取的关键信息键值对（如 扣费原因/涉及金额/'
        "确认号/处理结果/预约时间 等，键用中文，没有就留空对象）；\n"
        '  "follow_up_needed": 布尔，用户是否还需要进一步追问或再次拨打；\n'
        '  "follow_up_reason": 字符串，若需追问说明原因，否则空字符串。\n\n'
        f"【通话目标】{goal}\n\n"
        f"【通话转录】\n{dialog_text}\n\n"
        "只输出 JSON，不要额外解释。"
    )
    raw = _chat(
        [
            {"role": "system", "content": "你是严谨的通话记录结构化器，只输出合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        model=model,
    )
    structured = _safe_json(raw)
    # 模型偶尔输出 JSON 数组等合法但非对象的 JSON；归一化为空 dict，
    # 交给下游 .get 默认值兜底，而不是让 .get 在 list 上崩溃。
    if not isinstance(structured, dict):
        structured = {}
    return structured


def _safe_json(raw: str) -> dict[str, Any]:
    """从模型输出里稳妥地取出 JSON（容忍 ```json 包裹）。"""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {
        "goal_achieved": False,
        "summary": "（结构化解析失败，请查看原始 transcript）",
        "key_fields": {},
        "follow_up_needed": True,
        "follow_up_reason": "通话记录未能被自动结构化。",
    }


# --------------------------------------------------------------------------- #
# 离线 dry-run —— 完全不联网、不需要任何 API Key 的脚本化通话记录
# --------------------------------------------------------------------------- #
def _dryrun_record(phone_number: str, goal: str, context: str) -> dict[str, Any]:
    """
    返回一份【脚本化】的结构化通话记录，全程不调用任何 API、不联网。

    用途：当既没有电话账号、也没有 OPENAI_API_KEY 时，仍能把整条 ReAct 循环
    （思考 → 调用 make_phone_call → 读取结构化记录 → 汇报）离线跑通，展示其形状。
    transcript / key_fields 均为固定脚本，不代表任何真实通话。
    """
    ctx = context or "（无额外上下文）"
    # 由 goal 派生一个稳定、可复现的确认号（而非随机编造，便于对齐说明）。
    conf = "PC" + hashlib.sha1(goal.encode("utf-8")).hexdigest()[:8].upper()
    transcript = [
        {"speaker": "被叫方", "text": "您好，欢迎致电客服热线。业务查询请按 1，人工服务请按 0。"},
        {"speaker": "语音Agent", "text": "我按 0 转人工。"},
        {"speaker": "被叫方", "text": "您好，人工客服工号 3021，请问有什么可以帮您？"},
        {"speaker": "语音Agent", "text": f"你好，我这边的诉求是：{goal}。相关信息：{ctx}。"},
        {"speaker": "被叫方",
         "text": f"好的，已为您核实并受理，给您一个确认号 {conf}，后续可凭此查询进度。"},
        {"speaker": "语音Agent", "text": f"好的，确认号 {conf}，我记下了，谢谢，再见。"},
    ]
    record = CallRecord(
        call_id="pc_dryrun_" + hashlib.sha1((phone_number + goal).encode()).hexdigest()[:8],
        phone_number=phone_number,
        goal=goal,
        status="completed",
        goal_achieved=True,
        duration_seconds=12 * len(transcript) + 8,
        summary=f"（dry-run 脚本模拟）已就“{goal}”联系 {phone_number} 并受理，确认号 {conf}。",
        key_fields={"处理结果": "已受理", "确认号": conf, "对方号码": phone_number},
        transcript=transcript,
        follow_up_needed=False,
        follow_up_reason="",
    )
    return record.to_dict()


# --------------------------------------------------------------------------- #
# 对外唯一入口 —— 对齐真实 PineClaw Voice API 的 make_phone_call
# --------------------------------------------------------------------------- #
def make_phone_call(
    phone_number: str,
    goal: str,
    context: str = "",
    *,
    model: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    发起一通（模拟的）电话，由语音 Agent 全程完成，返回结构化通话记录（dict）。

    参数：
        phone_number: 被叫号码（本模拟不真正拨号，仅记录）。
        goal:         本次通话要达成的目标，例如
                      "查询本月宽带账单为何多扣了 50 元并要求解释"。
        context:      辅助上下文，如账号、姓名、已知信息等（可为空）。
        model:        覆盖内部模拟对话所用的 OpenAI 模型（默认取 OPENAI_MODEL）。
        dry_run:      若为真，则走完全离线的脚本化路径（不联网、不需要任何 API Key）。

    返回：
        CallRecord.to_dict()，包含 transcript / goal_achieved / key_fields 等。
    """
    if dry_run:
        return _dryrun_record(phone_number, goal, context)

    started = time.time()
    transcript = _run_dialog(phone_number, goal, context, model=model)
    structured = _extract_structured(goal, transcript, model=model)

    # 用对话轮数粗略折算一个「通话时长」，纯属演示展示用。
    duration = 12 * len(transcript) + 8

    # key_fields 可能是模型误输出的数组/标量等非对象类型，统一归一化为 dict。
    key_fields = structured.get("key_fields")
    if not isinstance(key_fields, dict):
        key_fields = {}

    record = CallRecord(
        call_id=f"pc_{uuid.uuid4().hex[:12]}",
        phone_number=phone_number,
        goal=goal,
        status="completed",
        goal_achieved=bool(structured.get("goal_achieved", False)),
        duration_seconds=duration,
        summary=str(structured.get("summary", "")),
        key_fields=key_fields,
        transcript=transcript,
        follow_up_needed=bool(structured.get("follow_up_needed", False)),
        follow_up_reason=str(structured.get("follow_up_reason", "")),
    )
    _ = started  # 真实 API 会用真实起止时间；此处 duration 为模拟值
    return record.to_dict()
