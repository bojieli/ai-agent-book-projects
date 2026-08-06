"""Phase 0 smoke: eng × tech_review → envelope → mock 缺陷单 → acl_view email."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.orchestrator import Orchestrator


def main() -> int:
    orch = Orchestrator(ROOT, allow_draft_skills=True)
    out = orch.bind_and_run(scenario_code="tech_review", meeting_id="mtg_r1_smoke", hitl_passed=True)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    pipe = out["pipeline"]
    wo = pipe["work_objects"][0] if pipe["work_objects"] else {}
    ok = (
        pipe["terminal"] == "succeeded"
        and wo.get("object_type") == "defect"
        and wo.get("external_id", "").startswith("BUG-")
        and pipe["render"]
        and pipe["render"].get("status") == "completed"
        and pipe["traces"] > 0
        and pipe["usage"].get("tool_calls", 0) >= 1
        and "work_link.synced" in pipe["events"]
        and "render.completed" in pipe["events"]
        and "hitl.requested" in pipe["events"]
        and "hitl.resolved" in pipe["events"]
        and "evaluation.passed" in pipe["events"]
        and out["policy_versions"] == [1, 2]
        and out["briefing_hops"] >= 1
    )
    if not ok:
        print("SMOKE FAILED", file=sys.stderr)
        return 1
    print("SMOKE PASSED", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
