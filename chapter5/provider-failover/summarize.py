"""把一次正式运行的结果汇总成 manifest 和一张表。

两个实验共用：``python summarize.py validation/runs/<run_id>``
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import judging


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tokens(record: dict) -> dict:
    """切换之后目标厂商实际吃进去和吐出来的 token。"""
    after = [e for e in record.get("exchanges", []) if e.get("status") == 200
             and e["provider"] == record["target"]]
    total_in = total_out = 0
    for exchange in after:
        usage = exchange["response"].get("usage") or exchange["response"].get("usageMetadata") or {}
        total_in += usage.get("input_tokens") or usage.get("prompt_tokens") or usage.get("promptTokenCount") or 0
        total_out += (usage.get("output_tokens") or usage.get("completion_tokens")
                      or ((usage.get("candidatesTokenCount") or 0) + (usage.get("thoughtsTokenCount") or 0)) or 0)
    return {"input": total_in, "output": total_out}


def handoff_summary(run_dir: pathlib.Path) -> dict:
    cells = sorted(p for p in run_dir.glob("*-to-*.json"))
    rows, by_arm = [], {}
    for path in cells:
        record = json.loads(path.read_text())
        tokens = _tokens(record)
        row = {"pair": f"{record['source']}→{record['target']}", "arm": record["arm"],
               "handoff_status": (record["handoff"] or {}).get("status"),
               "error": (record["handoff"] or {}).get("error_body", "")[:160] or None,
               "data_complete": record["data_complete"], "answer_correct": record["answer_correct"],
               "repeated_calls": len(record["repeated_calls"]),
               "rounds_after_switch": record["rounds_after_switch"],
               "tokens_after_switch": tokens, "file": path.name, "sha256": sha256(path)}
        rows.append(row)
        agg = by_arm.setdefault(record["arm"], {"cells": 0, "handoff_ok": 0, "data_complete": 0,
                                                "answer_correct": 0, "repeated_calls": 0,
                                                "input_tokens": 0, "output_tokens": 0})
        agg["cells"] += 1
        agg["handoff_ok"] += int(row["handoff_status"] == 200)
        agg["data_complete"] += int(row["data_complete"])
        agg["answer_correct"] += int(row["answer_correct"])
        agg["repeated_calls"] += row["repeated_calls"]
        agg["input_tokens"] += tokens["input"]
        agg["output_tokens"] += tokens["output"]

    gates = {
        "中立臂在全部厂商组合上切换成功": all(r["handoff_status"] == 200 for r in rows if r["arm"] == "neutral"),
        "直传臂的失败都是厂商真实报错": all(r["error"] for r in rows if r["arm"] == "naive" and r["handoff_status"] != 200),
        "每个单元都留下了原始响应": all(r["sha256"] for r in rows),
        "三条臂各覆盖六种厂商组合": all(v["cells"] == 6 for v in by_arm.values()),
    }
    return {"experiment": "5-1", "run": run_dir.name, "rows": rows, "by_arm": by_arm, "gates": gates}


def continuation_summary(run_dir: pathlib.Path) -> dict:
    summary = json.loads((run_dir / "summary.json").read_text())
    rows = _rejudge(run_dir, summary)
    by_cell = {}
    for row in rows:
        if not row.get("reproducible"):
            continue
        key = (row["provider"], row["break_point"], row["strategy"])
        agg = by_cell.setdefault(key, {"n": 0, "recovered": 0, "json_valid": 0, "args_correct": 0,
                                       "duplicate_side_effects": 0, "output_tokens": []})
        agg["n"] += 1
        agg["recovered"] += int(bool(row.get("recovered")))
        agg["json_valid"] += int(bool(row.get("json_valid")))
        agg["args_correct"] += int(bool(row.get("args_correct")))
        agg["duplicate_side_effects"] += row.get("duplicate_side_effects") or 0
        if row.get("output_tokens"):
            agg["output_tokens"].append(row["output_tokens"])

    table = []
    for (provider, break_point, strategy), agg in sorted(by_cell.items()):
        tokens = agg["output_tokens"]
        table.append({"provider": provider, "break_point": break_point, "strategy": strategy,
                      "n": agg["n"], "recovered": agg["recovered"],
                      "json_valid": agg["json_valid"], "args_correct": agg["args_correct"],
                      "duplicate_side_effects": agg["duplicate_side_effects"],
                      "mean_output_tokens": round(sum(tokens) / len(tokens), 1) if tokens else None})

    # 续写省下多少：同一 provider / 断点下，和整轮重发比。
    saving = {}
    for row in table:
        base = next((r for r in table if r["provider"] == row["provider"]
                     and r["break_point"] == row["break_point"] and r["strategy"] == "resend"), None)
        if base and base["mean_output_tokens"] and row["mean_output_tokens"] and row["strategy"] != "resend":
            saving[f"{row['provider']}/{row['break_point']}/{row['strategy']}"] = round(
                1 - row["mean_output_tokens"] / base["mean_output_tokens"], 3)

    not_reproducible = [{"provider": r["provider"], "break_point": r["break_point"], "note": r.get("note")}
                        for r in rows if not r.get("reproducible")]
    reproduced = {r["break_point"] for r in rows if r.get("reproducible")}
    gates = {
        "三类断点都真的切断过流": reproduced == {"reasoning", "text", "tool_args"},
        "成功的单元都有原始响应留存": all(
            (run_dir / f"{r['provider']}-{r['break_point']}-{r['repeat']}-{r['strategy']}.json").exists()
            for r in rows if r.get("reproducible") and not r.get("failed")),
        "失败的单元都记下了原因": all(r.get("failed") for r in rows if r.get("strategy") and not
                                      (run_dir / f"{r['provider']}-{r['break_point']}-{r['repeat']}-{r['strategy']}.json").exists()),
    }
    return {"experiment": "5-2", "run": run_dir.name, "cells": table,
            "token_saving_vs_resend": saving, "not_reproducible": not_reproducible,
            "gates": {k: bool(v) for k, v in gates.items()},
            "summary_sha256": sha256(run_dir / "summary.json")}


def _rejudge(run_dir: pathlib.Path, summary: dict) -> list[dict]:
    """从留下的原始数据重新判一遍。

    判定口径后来改过（续写和元指令都要和断点处那一截拼起来再看），重跑一整场
    活动只为换个口径不划算，原始请求和响应都在，重判即可。
    """
    executed = summary.get("executed_before_break", "")
    rows = []
    for row in summary["rows"]:
        if not row.get("reproducible") or row.get("failed"):
            rows.append(row)
            continue
        cell = run_dir / f"{row['provider']}-{row['break_point']}-{row['repeat']}-{row['strategy']}.json"
        if not cell.exists():
            rows.append(row)
            continue
        saved = json.loads(cell.read_text())
        verdict = judging.judge(row["break_point"], row["strategy"], saved["partial"],
                                saved["result"], executed)
        rows.append({**row, **verdict})
    return rows


def main() -> None:
    run_dir = pathlib.Path(sys.argv[1])
    is_handoff = any(run_dir.glob("*-to-*.json"))
    result = handoff_summary(run_dir) if is_handoff else continuation_summary(run_dir)
    (run_dir / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result.get("by_arm") or result.get("cells"), ensure_ascii=False, indent=2))
    print("\ngates:", json.dumps(result["gates"], ensure_ascii=False))
    print("manifest ->", run_dir / "manifest.json")


if __name__ == "__main__":
    main()
