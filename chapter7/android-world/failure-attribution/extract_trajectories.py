"""Split the saved AndroidWorld T3A logs into per-task trajectories.

Companion tool for Experiment 7-3 (failure attribution). Offline only: it reads
the retained `t3a_failed.md` / `t3a.md` logs and emits one record per episode so
that attribution can cite exact step numbers.

    python extract_trajectories.py --log ../t3a_failed.md --out trajectories.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

STEP_RE = re.compile(
    r"----------step (\d+)\n"
    r"Action: (.*?)\n"
    r"Reason: (.*?)\n"
    r"(?:Summary: (.*?)\n)?"
    r"Completed step",
    re.S,
)
GOAL_RE = re.compile(r'with goal "(.*?)"', re.S)


def parse(log_text: str) -> list[dict]:
    episodes = []
    for block in re.split(r"\nRunning task: ", log_text)[1:]:
        name = block.split("\n", 1)[0].strip()
        goal = GOAL_RE.search(block)
        steps = [
            {
                "step": int(num),
                "action": action.strip(),
                "reason": reason.strip(),
                "summary": (summary or "").strip(),
            }
            for num, action, reason, summary in STEP_RE.findall(block)
        ]
        if "Task Failed" in block:
            verdict = "failed"
        elif "Task Successful" in block:
            verdict = "successful"
        else:
            verdict = "unknown"
        if "Reached max number of steps" in block:
            termination = "max_steps"
        elif "Agent indicates task is done" in block:
            termination = "declared_done"
        else:
            termination = "other"
        episodes.append(
            {
                "task": name,
                "goal": goal.group(1).strip() if goal else "",
                "num_steps": len(steps),
                "verdict": verdict,
                "termination": termination,
                "answers": re.findall(r"Agent answered with: (.*)", block),
                "steps": steps,
            }
        )
    return episodes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", default="../t3a_failed.md")
    parser.add_argument("--out", default="trajectories.json")
    args = parser.parse_args()

    episodes = parse(Path(args.log).read_text(encoding="utf-8"))
    Path(args.out).write_text(
        json.dumps(episodes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    failed = sum(e["verdict"] == "failed" for e in episodes)
    print(f"{len(episodes)} episodes parsed, {failed} failed -> {args.out}")


if __name__ == "__main__":
    main()
