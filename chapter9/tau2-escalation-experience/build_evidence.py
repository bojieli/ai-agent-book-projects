#!/usr/bin/env python3
"""汇总三臂结果为可复核的 evidence.json。

只记录实际跑出来的数字；样本量、未完成任务数、策略哈希一并写入，
以便读者判断结论能外推到什么范围。
"""
import json, hashlib, platform, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

EXP = Path(__file__).resolve().parent
TAU = EXP.parent.parent / "chapter7" / "tau2-bench"
SIM = TAU / "data" / "simulations"
USER_TOOLS = set(Path(EXP / "tool_inventory.txt").read_text(encoding="utf-8")
                 .split("USER_TOOLS:")[1].replace("\n", " ").replace(",", " ").split())

ARMS = [
    ("armA-baseline",   "policies/baseline_main_policy.md",                                        "原始策略"),
    ("armB-evolved-v1", "validation/runs/exp9-2-tau2-escalation-v1/evolved_main_policy.md",        "原始 + v1 规则（提炼器只看失败摘要）"),
    ("armC-evolved-v2", "validation/runs/exp9-2-tau2-escalation-v2/evolved_main_policy.md",        "原始 + v2 规则（提炼器另看工具清单）"),
]

def arm_stats(name):
    f = SIM / f"{name}.json"
    if not f.exists(): return None
    sims = json.load(open(f, encoding="utf-8"))["simulations"]
    d = {"n": len(sims), "passed": 0, "escalated": 0,
         "misdirected_user_tool_calls": 0, "empty_arg_calls": 0, "tool_errors": 0,
         "per_task": {}}
    for s in sims:
        ok = s["reward_info"]["reward"] == 1.0
        d["passed"] += ok
        d["per_task"][s["task_id"]] = int(ok)
        esc = False
        for m in s["messages"]:
            # 调用方看 role：tau2 的 requestor 字段恒为 None，不能用来区分。
            for t in (m.get("tool_calls") or []):
                if t["name"] == "transfer_to_human_agents": esc = True
                if t["name"] in USER_TOOLS and m.get("role") != "user":
                    d["misdirected_user_tool_calls"] += 1
                if any(v == "" for v in (t.get("arguments") or {}).values()):
                    d["empty_arg_calls"] += 1
            if m.get("role") == "tool" and "Error" in (m.get("content") or ""):
                d["tool_errors"] += 1
        d["escalated"] += esc
    d["pass_rate"] = round(d["passed"] / d["n"], 4) if d["n"] else None
    d["escalation_rate"] = round(d["escalated"] / d["n"], 4) if d["n"] else None
    return d

def main():
    arms = {}
    for name, pol, desc in ARMS:
        st = arm_stats(name)
        if st is None: continue
        p = (EXP / pol).read_text(encoding="utf-8")
        st.update({"description": desc, "policy_file": pol,
                   "policy_sha256": hashlib.sha256(p.encode()).hexdigest(),
                   "policy_chars": len(p)})
        arms[name] = st

    common = None
    for st in arms.values():
        s = set(st["per_task"])
        common = s if common is None else (common & s)
    common = sorted(common or [])
    paired = {n: {"passed": sum(st["per_task"][t] for t in common),
                  "rate": round(sum(st["per_task"][t] for t in common) / len(common), 4) if common else None}
              for n, st in arms.items()}

    train = json.load(open(SIM / "base-train-v1.json", encoding="utf-8"))["simulations"]
    ev = {
        "schema_version": 1,
        "experiment_id": "9-2",
        "title": "从 τ²-bench 失败轨迹提炼转人工与工具使用规则",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "repository_revision": subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True,cwd=EXP).stdout.strip(),
        "host": {"python": platform.python_version(), "platform": platform.platform()},
        "provider": "volcengine-ark",
        "models": {"agent": "doubao-seed-1-6-flash-250615",
                   "user_simulator": "doubao-seed-1-6-250615",
                   "rule_derivation": "doubao-seed-1-6-250615"},
        "split": {"train_task_set": "telecom_small", "train_n": len(train),
                  "test_task_set": "telecom", "test_n_intended": 114,
                  "disjoint_by_construction": True},
        "train_baseline": {"n": len(train),
                           "passed": sum(1 for s in train if s["reward_info"]["reward"] == 1.0)},
        "arms": arms,
        "paired_on_common_tasks": {"n_common": len(common), "results": paired},
        "caveats": [
            "每条任务只运行一次（num_trials=1），未做多种子重复。",
            "τ²-bench 的 executor.map 遇任一任务异常即整体中止，本实验通过断点续跑补齐；未能补齐的任务在 n 中如实反映。",
            "样本量仅百余条、单次运行，结论只能用于判断是否值得扩大测试，不能作为方法有效性的定论。",
        ],
    }
    out = EXP / "validation" / "evidence.json"
    json.dump(ev, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"写入 {out}")
    for n, st in arms.items():
        print(f"  {n:18s} n={st['n']:3d} 通过 {st['passed']:3d} ({st['pass_rate']:.1%}) "
              f"转人工 {st['escalation_rate']:.1%} 误调用户工具 {st['misdirected_user_tool_calls']:4d}")
    print(f"  共同任务 {len(common)} 条:", {n: v["rate"] for n, v in paired.items()})

if __name__ == "__main__":
    main()
