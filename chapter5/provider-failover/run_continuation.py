"""实验 5-2：输出到一半断掉之后的接续。

流式请求在三个位置被切断——思考中途、正文中途、工具调用参数 JSON 中途——再用
三种方式恢复：整轮重发、以半截输出为前缀续写、追加元指令让模型从断点继续。

    python run_continuation.py
    python run_continuation.py --providers kimi --repeats 1
"""

from __future__ import annotations

import argparse
import json
import pathlib
import time

import judging
import providers
import streaming
import tools
from neutral_trace import Step, ToolCall, Trace
from providers import ANTHROPIC, DEFAULT_MODELS, GEMINI, KIMI
from renderers import NEUTRAL, render
from streaming import BREAK_POINTS, REASONING, TEXT, TOOL_ARGS

RESEND, PREFILL, META = "resend", "prefill", "meta"
STRATEGIES = (RESEND, PREFILL, META)

# 第一轮已经执行过的调用。恢复时如果又调一次，就是重复副作用。
EXECUTED = ToolCall(name="get_flight_price", arguments={"city": "东京"}, call_id="call_seed")


def pre_state(break_point: str) -> Trace:
    """构造断点发生之前的轨迹。

    思考和工具参数两个断点发生在“还要接着调工具”的时候，正文断点发生在“数据齐
    了该写总结”的时候。这段轨迹是实验的输入，直接拼出来即可，不必先让模型跑。
    """
    trace = Trace()
    trace.user(tools.TASK)
    seeded = [(EXECUTED, tools.execute(EXECUTED.name, EXECUTED.arguments))]
    if break_point == TEXT:
        for name in ("get_hotel_price", "get_meal_budget", "get_exchange_rate"):
            args = {"currency": "JPY"} if name == "get_exchange_rate" else {"city": "东京"}
            call = ToolCall(name=name, arguments=args, call_id=f"call_{name}")
            seeded.append((call, tools.execute(name, args)))
    for call, result in seeded:
        trace.add(Step(role="assistant", text=None, tool_calls=[call]))
        trace.tool_result(call.call_id, call.name, result)
    return trace


def _base_payload(provider: str, trace: Trace, with_tools: bool = True) -> dict:
    return render(provider, trace, NEUTRAL, tools.TOOLS if with_tools else [],
                  DEFAULT_MODELS[provider], tools.SYSTEM)


def _append_assistant_prefix(provider: str, payload: dict, prefix: str) -> dict:
    """把半截输出作为末尾的 assistant 消息挂上去，让模型接着写。"""
    body = json.loads(json.dumps(payload))
    if provider == KIMI:
        # Moonshot 需要显式标记 partial，否则它会另起一句而不是接着写。
        body["messages"].append({"role": "assistant", "content": prefix, "partial": True})
    elif provider == ANTHROPIC:
        body["messages"].append({"role": "assistant", "content": prefix})
    else:
        body["contents"].append({"role": "model", "parts": [{"text": prefix}]})
    return body


def _append_user(provider: str, payload: dict, text: str) -> dict:
    body = json.loads(json.dumps(payload))
    if provider == GEMINI:
        body["contents"].append({"role": "user", "parts": [{"text": text}]})
    else:
        body["messages"].append({"role": "user", "content": text})
    return body


# 续写请求要告诉模型它在接一段被截断的输出，否则它会另起炉灶或者顺手多加字段。
# 工具定义保留：schema 一旦从上下文里拿掉，模型补参数时就会开始编字段。
RECOVERY_HINT = ("上一次回复在传输中被截断了。请紧接着已经输出的内容往下写，把剩下的部分补完；"
                 "不要重复已输出的字符，不要新增字段，也不要改写已经输出的部分。")


def _with_hint(provider: str, payload: dict, hint: str) -> dict:
    body = json.loads(json.dumps(payload))
    if provider == GEMINI:
        parts = body.setdefault("systemInstruction", {"parts": [{"text": ""}]})["parts"]
        parts.append({"text": hint})
    elif provider == ANTHROPIC:
        body["system"] = (body.get("system") or "") + "\n" + hint
        body.pop("thinking", None)  # 续写不需要再思考一遍
        body["max_tokens"] = 1024
    else:
        if body["messages"] and body["messages"][0]["role"] == "system":
            body["messages"][0]["content"] += "\n" + hint
        else:
            body["messages"].insert(0, {"role": "system", "content": hint})
    return body


def _text_of(provider: str, response: dict) -> str:
    step = providers.capture(provider, response)
    return step.text or ""


def _calls_of(provider: str, response: dict) -> list[ToolCall]:
    return providers.capture(provider, response).tool_calls


def recover(provider: str, break_point: str, strategy: str, partial: streaming.Partial,
            trace: Trace) -> dict:
    payload = _base_payload(provider, trace)
    out = {"strategy": strategy, "applicable": True, "note": None}

    if strategy == RESEND:
        response = providers.call(provider, payload)
    elif strategy == META:
        shown = partial.get("tool_args") if break_point == TOOL_ARGS else (
            partial.get("text") or partial.get("reasoning"))
        response = providers.call(provider, _append_user(
            provider, payload,
            f"你上一次的回复在这里被截断了：「{shown}」。请从断点继续，不要重复已经输出的部分。"))
    else:  # PREFILL
        if break_point == REASONING:
            # 半截思考没法作为前缀回传：Claude 要验签，Moonshot 的 partial 走的是
            # 正文槽位，Gemini 干脆没有这个接口。只能丢掉重来。
            out.update(applicable=False, note="半截思考无法作为前缀回传，退化为整轮重发")
            response = providers.call(provider, payload)
        elif break_point == TEXT:
            response = providers.call(provider, _append_assistant_prefix(
                provider, _with_hint(provider, payload, RECOVERY_HINT), partial["text"]))
        else:
            # 半截的工具调用没法以原生结构回传，先文本化再让模型把 JSON 补完。
            prefix = f'我需要调用 {partial["tool_name"]}，参数是 {partial["tool_args"]}'
            response = providers.call(provider, _append_assistant_prefix(
                provider, _with_hint(provider, payload, RECOVERY_HINT), prefix))

    out["usage"] = providers.usage_of(provider, response)
    out["raw"] = response
    out["text"] = _text_of(provider, response)
    out["tool_calls"] = [{"name": c.name, "arguments": c.arguments} for c in _calls_of(provider, response)]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--providers", nargs="*", default=[KIMI, ANTHROPIC, GEMINI])
    ap.add_argument("--breaks", nargs="*", default=list(BREAK_POINTS))
    ap.add_argument("--strategies", nargs="*", default=list(STRATEGIES))
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_dir = pathlib.Path(args.out or f"validation/runs/exp5-2-continuation-{stamp}")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    for provider in args.providers:
        for break_point in args.breaks:
            trace = pre_state(break_point)
            for repeat in range(args.repeats):
                try:
                    partial = streaming.stream_until(provider, _base_payload(provider, trace), break_point)
                except Exception as e:
                    rows.append({"provider": provider, "break_point": break_point, "repeat": repeat,
                                 "reproducible": False, "failed": f"{type(e).__name__}: {e}"[:300]})
                    print(f"[{provider}/{break_point}#{repeat}] 取流失败：{type(e).__name__}", flush=True)
                    continue
                cut = {"reasoning_chars": len(partial["reasoning"]), "text_chars": len(partial["text"]),
                       "tool_name": partial["tool_name"], "tool_args": partial["tool_args"],
                       "truncated": partial["truncated"], "closed": partial["tool_args_closed"]}
                if not partial["truncated"]:
                    rows.append({"provider": provider, "break_point": break_point, "repeat": repeat,
                                 "reproducible": False, "cut": cut,
                                 "note": "这一路流没有在该断点上给出半截内容"})
                    print(f"[{provider}/{break_point}#{repeat}] 断点不可复现：{cut}", flush=True)
                    continue
                for strategy in args.strategies:
                    try:
                        result = recover(provider, break_point, strategy, partial, trace)
                    except Exception as e:  # 一格挂掉不该带走整场活动
                        rows.append({"provider": provider, "break_point": break_point,
                                     "repeat": repeat, "reproducible": True, "strategy": strategy,
                                     "cut": cut, "failed": f"{type(e).__name__}: {e}"[:300]})
                        print(f"[{provider}/{break_point}#{repeat}] {strategy}: 失败 {type(e).__name__}", flush=True)
                        continue
                    verdict = judging.judge(break_point, strategy, partial, result,
                                            EXECUTED.fingerprint())
                    row = {"provider": provider, "break_point": break_point, "repeat": repeat,
                           "reproducible": True, "strategy": strategy, "cut": cut,
                           "applicable": result["applicable"], "note": result["note"],
                           "output_tokens": result["usage"].get("output"), **verdict}
                    rows.append(row)
                    (out_dir / f"{provider}-{break_point}-{repeat}-{strategy}.json").write_text(
                        json.dumps({"row": row, "partial": dict(partial), "result": result},
                                   ensure_ascii=False, indent=2))
                    print(f"[{provider}/{break_point}#{repeat}] {strategy}: 恢复 {verdict['recovered']}"
                          f" | token {result['usage'].get('output')}"
                          f" | 重复副作用 {verdict['duplicate_side_effects']}"
                          f"{'' if result['applicable'] else ' | ' + result['note']}", flush=True)

    (out_dir / "summary.json").write_text(json.dumps(
        {"experiment": "5-2", "generated_at": stamp, "models": DEFAULT_MODELS,
         "executed_before_break": EXECUTED.fingerprint(), "rows": rows},
        ensure_ascii=False, indent=2))
    print(f"\n结果写入 {out_dir}")


if __name__ == "__main__":
    main()
