"""Unit checks for policy + critical render skip."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.policy import max_strict_embed_gate, policy_hooks_ok
from app.render import RenderService


def test_embed_gate_strict() -> None:
    assert max_strict_embed_gate("allow", "confirm_only") == "confirm_only"
    assert max_strict_embed_gate("confirm_only", "block") == "block"


def test_critical_policy() -> None:
    fails = policy_hooks_ok(
        classification="critical",
        continuum_write_class="wide",
        production_effect="none",
        production_effect_cap="none",
        embed_gate="block",
        maturity="L2",
    )
    assert "critical_requires_sealed_or_none" in fails


def test_critical_render_skip() -> None:
    svc = RenderService(ROOT / "app" / "render" / "default")
    view = svc.materialize_acl_view(
        view_id="v1",
        meeting_id="m1",
        artifacts=[{"artifact_kind": "draft", "payload": {}}],
        viewer_ids=["u1"],
        classification="critical",
        allowlist=None,
    )
    assert view.empty
    rr = svc.render_email(
        job_id="j1",
        acl_view=view,
        classification="critical",
        allowlist=None,
    )
    assert rr.status == "skipped"
    assert rr.skip_reason == "critical_no_allowlist"


if __name__ == "__main__":
    test_embed_gate_strict()
    test_critical_policy()
    test_critical_render_skip()
    print("UNIT OK")
