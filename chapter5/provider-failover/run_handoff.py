"""实验 5-1：跨厂商的轨迹接管。

一条需要四次工具调用的任务，跑到第二次调用之后把当前厂商打成不可用，换另一家
接着跑完。三条臂（直传 / 剥离 / 中立）各跑一遍，比较切换后的报错、完成情况和
重复调用。

    python run_handoff.py                      # 六种厂商组合 × 三条臂
    python run_handoff.py --pairs kimi:gemini  # 只跑一种组合
"""

from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import providers
import tools
from neutral_trace import Trace
from providers import ANTHROPIC, GEMINI, KIMI, DEFAULT_MODELS, ProviderError
from renderers import ARMS, render

SWITCH_AFTER = 2  # 前两次工具调用由源厂商完成，之后切换
MAX_ROUNDS = 10
# 熔断由人为注入触发：厂商不会配合我们宕机。跨厂商的格式报错才是真实的。
INJECTED_OUTAGE = {"injected": True, "statuses": [429, 429, 503],
                   "note": "人为注入的连续过载，用来触发熔断；非厂商真实故障"}


def step_once(provider: str, trace: Trace, arm: str, log: list) -> dict:
    payload = render(provider, trace, arm, tools.TOOLS, DEFAULT_MODELS[provider], tools.SYSTEM)
    request_snapshot = json.loads(json.dumps(payload))
    try:
        response = providers.call(provider, payload)
    except ProviderError as e:
        log.append({"provider": provider, "arm": arm, "request": request_snapshot,
                    "status": e.status, "error_body": e.body})
        raise
    log.append({"provider": provider, "arm": arm, "request": request_snapshot,
                "status": 200, "response": response})
    return response


def run_pair(source: str, target: str, arm: str) -> dict:
    trace = Trace()
    trace.user(tools.TASK)
    log: list = []
    record = {"source": source, "target": target, "arm": arm,
              "models": {source: DEFAULT_MODELS[source], target: DEFAULT_MODELS[target]},
              "outage": INJECTED_OUTAGE, "handoff": None,
              "data_complete": False, "answer_correct": False,
              "repeated_calls": [], "rounds_after_switch": 0, "tokens_after_switch": 0,
              "final_text": None, "error": None}

    calls_done = 0
    before_switch: set[str] = set()
    current = source
    switched = False

    for _ in range(MAX_ROUNDS):
        if calls_done >= SWITCH_AFTER and not switched:
            current, switched = target, True

        try:
            response = step_once(current, trace, arm, log)
        except RuntimeError as e:  # 连接层的问题，重试过了还是不行
            record["error"] = str(e)[:300]
            break
        except ProviderError as e:
            if switched and record["handoff"] is None:
                # 切换后的第一个请求就被目标厂商拒了：这正是要测的那一类报错。
                record["handoff"] = {"status": e.status, "error_body": e.body[:2000]}
            record["error"] = f"{e.status}: {e.body[:300]}"
            break

        if switched and record["handoff"] is None:
            record["handoff"] = {"status": 200}
        step = providers.capture(current, response)
        trace.add(step)

        if switched:
            record["rounds_after_switch"] += 1
            record["tokens_after_switch"] += providers.usage_of(current, response).get("output") or 0
            for call in step.tool_calls:
                if call.fingerprint() in before_switch:
                    record["repeated_calls"].append(call.fingerprint())

        if not step.tool_calls:
            # 接管成功与否看数据齐不齐；总额对不对另记一项，那受模型算术水平影响，
            # 不该和接管质量混为一谈。
            called = {c.name for st in trace.steps for c in st.tool_calls}
            record["final_text"] = step.text
            record["data_complete"] = called >= {t["function"]["name"] for t in tools.TOOLS}
            record["answer_correct"] = tools.answer_is_correct(step.text or "")
            break

        for call in step.tool_calls:
            if not switched:
                before_switch.add(call.fingerprint())
            trace.tool_result(call.call_id, call.name, tools.execute(call.name, call.arguments))
            calls_done += 1

    record["trace"] = trace.to_json()
    record["exchanges"] = log
    record["tool_calls_total"] = len(trace.called_fingerprints())
    return record


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="*", default=None, help="形如 kimi:gemini，默认跑全部六种组合")
    ap.add_argument("--arms", nargs="*", default=list(ARMS))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    pairs = ([tuple(p.split(":")) for p in args.pairs] if args.pairs
             else list(itertools.permutations((KIMI, ANTHROPIC, GEMINI), 2)))
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = pathlib.Path(args.out or f"validation/runs/exp5-1-handoff-{stamp}")
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for source, target in pairs:
        for arm in args.arms:
            print(f"[{source} -> {target}] {arm} ...", flush=True)
            record = run_pair(source, target, arm)
            (out / f"{source}-to-{target}-{arm}.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2))
            status = (record["handoff"] or {}).get("status")
            print(f"    切换后首个请求 {status} | 数据齐备 {record['data_complete']} | "
                  f"总额正确 {record['answer_correct']} | "
                  f"重复调用 {len(record['repeated_calls'])} | "
                  f"切换后 {record['rounds_after_switch']} 轮 / {record['tokens_after_switch']} token", flush=True)
            rows.append({k: record[k] for k in ("source", "target", "arm", "handoff",
                                                "data_complete", "answer_correct",
                                                "rounds_after_switch", "tokens_after_switch")}
                        | {"repeated_calls": len(record["repeated_calls"]),
                           "error": record["error"]})

    summary = {"experiment": "5-1", "generated_at": stamp, "switch_after_tool_calls": SWITCH_AFTER,
               "outage": INJECTED_OUTAGE, "models": DEFAULT_MODELS, "rows": rows}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n结果写入 {out}")


if __name__ == "__main__":
    main()
