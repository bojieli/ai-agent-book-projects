"""离线测试：只验证轨迹渲染与切断逻辑，不打任何外部 API。"""

from __future__ import annotations

import json

import pytest

import streaming
import tools
from neutral_trace import PLAINTEXT, SIGNED, SUMMARY, Reasoning, Step, ToolCall, Trace
from providers import ANTHROPIC, GEMINI, KIMI
from renderers import NAIVE, NEUTRAL, STRIP, render

FOREIGN_SIG = "sig-from-another-vendor"


def foreign_trace(issuer: str = KIMI, kind: str = PLAINTEXT, credential: str | None = None) -> Trace:
    trace = Trace()
    trace.user("算一下预算")
    call = ToolCall(name="get_flight_price", arguments={"city": "东京"}, call_id="get_flight_price_0")
    trace.add(Step(role="assistant", text=None,
                   reasoning=Reasoning(text="先查机票", credential=credential, issuer=issuer, kind=kind),
                   tool_calls=[call], issuer=issuer))
    trace.tool_result(call.call_id, call.name, '{"round_trip_cny":3200}')
    return trace


def payload_text(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


# --------------------------------------------------------------- 凭证的去留
def test_neutral_drops_foreign_credential():
    trace = foreign_trace(ANTHROPIC, SIGNED, FOREIGN_SIG)
    body = render(KIMI, trace, NEUTRAL, tools.TOOLS, "kimi-k3")
    assert FOREIGN_SIG not in payload_text(body)


def test_naive_carries_foreign_credential():
    trace = foreign_trace(ANTHROPIC, SIGNED, FOREIGN_SIG)
    body = render(KIMI, trace, NAIVE, tools.TOOLS, "kimi-k3")
    assert FOREIGN_SIG in payload_text(body)


def test_naive_puts_foreign_thinking_into_the_thinking_slot():
    """直传臂之所以会被验签挡住，就是因为它把别家的思考塞回了 thinking 槽位。"""
    trace = foreign_trace(KIMI, PLAINTEXT, None)
    body = render(ANTHROPIC, trace, NAIVE, tools.TOOLS, "claude")
    blocks = body["messages"][1]["content"]
    assert blocks[0]["type"] == "thinking"
    assert "signature" not in blocks[0]  # 缺签名，真实请求会 400


def test_neutral_carries_plaintext_as_ordinary_text():
    trace = foreign_trace(KIMI, PLAINTEXT, None)
    body = render(ANTHROPIC, trace, NEUTRAL, tools.TOOLS, "claude")
    blocks = body["messages"][1]["content"]
    assert [b["type"] for b in blocks if b["type"] == "thinking"] == []
    assert blocks[0]["type"] == "text" and "先查机票" in blocks[0]["text"]
    assert "kimi" in blocks[0]["text"]  # 带上来源，模型才知道这是上一个模型留下的


def test_strip_drops_reasoning_entirely():
    trace = foreign_trace(ANTHROPIC, SIGNED, FOREIGN_SIG)
    body = render(KIMI, trace, STRIP, tools.TOOLS, "kimi-k3")
    text = payload_text(body)
    assert FOREIGN_SIG not in text and "先查机票" not in text


@pytest.mark.parametrize("arm", [STRIP, NEUTRAL])
def test_own_credential_survives_every_arm(arm):
    """目标厂商自己签发的凭证不能删——删了它接着往下跑同样会报错。"""
    trace = foreign_trace(ANTHROPIC, SIGNED, "own-signature")
    body = render(ANTHROPIC, trace, arm, tools.TOOLS, "claude")
    assert "own-signature" in payload_text(body)


# --------------------------------------------------------------- Gemini 的降级
def test_gemini_neutral_flattens_foreign_tool_calls():
    trace = foreign_trace(KIMI, PLAINTEXT, None)
    body = render(GEMINI, trace, NEUTRAL, tools.TOOLS, "gemini-3.5-flash")
    assert "functionCall" not in payload_text(body)
    assert "functionResponse" not in payload_text(body)  # 结果也得跟着拍平，否则配不上对
    assert "get_flight_price" in payload_text(body)


def test_gemini_keeps_its_own_call_native():
    trace = foreign_trace(GEMINI, SUMMARY, "own-thought-signature")
    body = render(GEMINI, trace, NEUTRAL, tools.TOOLS, "gemini-3.5-flash")
    text = payload_text(body)
    assert "functionCall" in text and "own-thought-signature" in text


def test_gemini_strip_leaves_call_without_credential():
    """剥离思考救不了 Gemini：它的凭证挂在工具调用上，不在思考里。"""
    trace = foreign_trace(KIMI, PLAINTEXT, None)
    body = render(GEMINI, trace, STRIP, tools.TOOLS, "gemini-3.5-flash")
    text = payload_text(body)
    assert "functionCall" in text and "thoughtSignature" not in text


# --------------------------------------------------------------- id 与配对
def test_neutral_remints_ids_and_keeps_pairing():
    trace = foreign_trace(KIMI, PLAINTEXT, None)
    body = render(ANTHROPIC, trace, NEUTRAL, tools.TOOLS, "claude")
    use = [b for b in body["messages"][1]["content"] if b["type"] == "tool_use"][0]
    result = body["messages"][2]["content"][0]
    assert use["id"] != "get_flight_price_0"
    assert result["tool_use_id"] == use["id"]


def test_repair_orphans_inserts_a_placeholder_result():
    trace = Trace()
    trace.user("算一下预算")
    trace.add(Step(role="assistant", tool_calls=[ToolCall("get_flight_price", {"city": "东京"}, "c1")]))
    assert trace.repair_orphans() == ["c1"]
    assert trace.steps[-1].role == "tool" and trace.steps[-1].tool_call_id == "c1"
    assert trace.repair_orphans() == []


def test_fingerprint_ignores_key_order():
    a = ToolCall("f", {"x": 1, "y": 2}, "c1").fingerprint()
    b = ToolCall("f", {"y": 2, "x": 1}, "c2").fingerprint()
    assert a == b


# --------------------------------------------------------------- 流与切断
def test_absorb_kimi_deltas():
    state = streaming.Partial.new()
    streaming._absorb(KIMI, {"choices": [{"delta": {"reasoning_content": "想"}}]}, state)
    streaming._absorb(KIMI, {"choices": [{"delta": {"tool_calls": [
        {"function": {"name": "get_hotel_price", "arguments": '{"city": "东'}}]}}]}, state)
    assert state["reasoning"] == "想" and state["tool_name"] == "get_hotel_price"
    assert state["tool_args"] == '{"city": "东'


def test_absorb_anthropic_deltas():
    state = streaming.Partial.new()
    streaming._absorb(ANTHROPIC, {"type": "content_block_start",
                                  "content_block": {"type": "tool_use", "name": "get_hotel_price"}}, state)
    streaming._absorb(ANTHROPIC, {"type": "content_block_delta",
                                  "delta": {"partial_json": '{"city"'}}, state)
    assert state["tool_name"] == "get_hotel_price" and state["tool_args"] == '{"city"'


def test_gemini_stream_never_exposes_partial_arguments():
    """Gemini 的流式接口把 functionCall 整块吐出来，所以这个断点在它上面不可复现。"""
    state = streaming.Partial.new()
    streaming._absorb(GEMINI, {"candidates": [{"content": {"parts": [
        {"functionCall": {"name": "get_hotel_price", "args": {"city": "东京"}}}]}}]}, state)
    assert state["tool_args_closed"] is True
    assert streaming._cut_here(state, streaming.TOOL_ARGS, {streaming.TOOL_ARGS: 4}) is False


def test_cut_here_thresholds():
    limits = {streaming.REASONING: 5, streaming.TEXT: 5, streaming.TOOL_ARGS: 5}
    state = streaming.Partial.new()
    state["reasoning"] = "1234"
    assert streaming._cut_here(state, streaming.REASONING, limits) is False
    state["reasoning"] = "12345"
    assert streaming._cut_here(state, streaming.REASONING, limits) is True


# --------------------------------------------------------------- 任务本身
def test_tools_are_deterministic():
    assert json.loads(tools.execute("get_exchange_rate", {"currency": "jpy"}))["cny_per_unit"] == 0.048
    assert "error" in tools.execute("get_exchange_rate", {"currency": "XYZ"})
    assert "error" in tools.execute("no_such_tool", {})


def test_answer_checker_tolerates_rounding_only():
    assert tools.answer_is_correct("总计 6,944 元")
    assert tools.answer_is_correct("大约 6950 元")
    assert not tools.answer_is_correct("总计 7,944 元")
    assert not tools.answer_is_correct("")


def test_only_the_first_tool_call_of_a_turn_is_tracked():
    """一轮里并行发出多个调用时，只跟第一个——否则参数会被串成一团。"""
    state = streaming.Partial.new()
    for index, name in ((0, "get_hotel_price"), (1, "get_meal_budget")):
        streaming._absorb(KIMI, {"choices": [{"delta": {"tool_calls": [
            {"index": index, "function": {"name": name, "arguments": '{"city":"东京"}'}}]}}]}, state)
    assert state["tool_name"] == "get_hotel_price"
    assert state["tool_args"] == '{"city":"东京"}'


# --------------------------------------------------------------- 恢复的判定
def test_spliced_arguments_can_be_valid_but_wrong():
    """续写在拼接处多出一个空格，JSON 照样合法，参数却已经错了。"""
    import judging

    partial = {"tool_args": '{"city": "东'}
    good = judging.judge("tool_args", "prefill", partial, {"text": '京"}', "tool_calls": []})
    bad = judging.judge("tool_args", "prefill", partial, {"text": ' 京"}', "tool_calls": []})
    assert good["json_valid"] and good["args_correct"]
    assert bad["json_valid"] and not bad["args_correct"]


def test_resend_is_judged_on_its_own_output_others_on_the_splice():
    import judging

    partial = {"text": "北京今天 29℃、天气晴朗，气温对跑步来说偏"}
    tail = {"text": "热。合计 6,944 元。", "tool_calls": []}
    assert judging.judge("text", "prefill", partial, tail)["answer_correct"]
    assert judging.judge("text", "meta", partial, tail)["answer_correct"]
    # 整轮重发丢掉半截重写，只看它自己写出来的部分
    assert judging.judge("text", "resend", partial, {"text": "太热了", "tool_calls": []})["recovered"] is False


def test_duplicate_side_effect_is_counted_by_fingerprint():
    import judging

    executed = ToolCall("get_flight_price", {"city": "东京"}, "c0").fingerprint()
    result = {"text": "", "tool_calls": [{"name": "get_flight_price", "arguments": {"city": "东京"}}]}
    assert judging.judge("reasoning", "resend", {}, result, executed)["duplicate_side_effects"] == 1
    assert judging.judge("reasoning", "resend", {}, result, "")["duplicate_side_effects"] == 0
