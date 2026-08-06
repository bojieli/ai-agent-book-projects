"""One-shot Phase / Production gates."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    cmds = [
        [sys.executable, "-m", "app.eval.smoke"],
        [sys.executable, "-m", "app.eval.verify_architecture"],
        [sys.executable, "-m", "app.eval.verify_production"],
        [sys.executable, "-m", "pytest", str(ROOT / "tests"), "-q"],
        # Handbook + OSS corpora shim gates (thresholds in corpus_gates.SHIM_GATES)
        [sys.executable, "-m", "app.eval.corpus_gates"],
        # Dual-gate release slice: smoke attack + FP suite + EXPANDED_LIMIT=20
        [sys.executable, "-m", "app.eval.dual_gates", "--profile", "release"],
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
