import json
from pathlib import Path


ROOT = Path(__file__).parent / "validation"


def test_real_parallel_serial_evidence_closes_every_context_and_measures_speedup():
    data = json.loads((ROOT / "real_parallel_serial_2026-07-29.json").read_text())
    assert data["overall_status"] == "pass"
    assert data["parallel"]["contexts_created"] == data["parallel"]["contexts_closed"] == 10
    assert data["serial"]["contexts_created"] == data["serial"]["contexts_closed"] == 10
    assert data["parallel"]["errors"] == {}
    assert data["measured_speedup"] > 1


def test_real_cascade_evidence_has_one_broadcast_all_acks_and_no_leaks():
    data = json.loads((ROOT / "real_cascade_2026-07-29.json").read_text())
    assert data["terminate_broadcasts"] == 1
    assert len(data["loser_acknowledgements"]) == data["workers"] - 1
    assert data["contexts_created"] == data["contexts_closed"]
    assert data["errors"] == {}
