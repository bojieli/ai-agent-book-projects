"""One-shot: architecture verify + pytest all phases."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    cmds = [
        [sys.executable, "-m", "app.eval.smoke_skills"],
        [sys.executable, "-m", "app.demo.phase0_smoke"],
        [sys.executable, "-m", "app.eval.verify_architecture"],
        [sys.executable, "-m", "app.eval.verify_features"],
        [sys.executable, "-m", "app.eval.retrieval_quality"],
        [sys.executable, "-m", "app.eval.story_gates"],
        [sys.executable, "-m", "app.eval.fault_matrix"],  # M5 强制故障矩阵（离线）
        [sys.executable, "-m", "app.eval.m6_quality_gates"],  # M6 语料规模+负例+性能
        [sys.executable, "-m", "pytest", str(ROOT / "tests"), "-q"],
    ]
    for cmd in cmds:
        print("\n>>>", " ".join(cmd))
        r = subprocess.run(cmd, cwd=ROOT)
        if r.returncode != 0:
            print("FAILED", cmd)
            return r.returncode
    print("\nALL PHASE GATES PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
