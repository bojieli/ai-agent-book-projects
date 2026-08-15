"""Offline checkpoint-validity tests for the resumable full runner."""

import json

from run_full import required_611_cells, valid_checkpoint


def record(experiment="6-4", status="ok", system="advanced_json_cards"):
    row = {
        "experiment": experiment,
        "test_id": "case-1",
        "status": status,
        "error": None,
        "rubric_details": {
            name: {"score": 4}
            for name in ("precision", "recall", "reasoning", "proactivity")
        },
        "hallucination_detail": {"detected": False},
        "embedding": "e",
        "reranker": "none",
        "main_model": "m",
        "system": system,
    }
    if status == "error":
        row["error"] = "provider unavailable"
        row["rubric_details"] = {}
        row["hallucination_detail"] = None
    return row


def write_checkpoint(path, experiment, records):
    path.write_text(json.dumps({
        "experiment": experiment,
        "run_scope": {"requested_test_ids": ["case-1"]},
        "records": records,
    }))


def test_64_checkpoint_requires_successful_full_rubric_rows(tmp_path):
    path = tmp_path / "case.json"
    rows = [record(system=name) for name in ("advanced_json_cards", "rag", "hybrid")]
    write_checkpoint(path, "6-4", rows)
    expected = {("advanced_json_cards",), ("rag",), ("hybrid",)}
    assert valid_checkpoint(path, "case-1", "6-4", 3, expected_cells=expected)

    rows[0]["rubric_details"] = {}
    write_checkpoint(path, "6-4", rows)
    assert not valid_checkpoint(path, "case-1", "6-4", 3, expected_cells=expected)

    rows[0] = record(status="error")
    write_checkpoint(path, "6-4", rows)
    assert not valid_checkpoint(path, "case-1", "6-4", 3, expected_cells=expected)

    rows = [record(system="rag") for _ in range(3)]
    write_checkpoint(path, "6-4", rows)
    assert not valid_checkpoint(path, "case-1", "6-4", 3, expected_cells=expected)


def test_611_checkpoint_preserves_explicit_provider_errors(tmp_path):
    path = tmp_path / "case.json"
    rows = [record("6-11"), record("6-11", status="error")]
    rows[1]["embedding"] = "blocked"
    write_checkpoint(path, "6-11", rows)
    assert valid_checkpoint(path, "case-1", "6-11", 2, {("e", "none", "m")})

    rows[1]["error"] = None
    write_checkpoint(path, "6-11", rows)
    assert not valid_checkpoint(path, "case-1", "6-11", 2, {("e", "none", "m")})

    rows[1]["error"] = "transient"
    rows[1]["embedding"] = "e"
    write_checkpoint(path, "6-11", rows)
    assert not valid_checkpoint(path, "case-1", "6-11", 2, {("e", "none", "m")})


def test_required_611_cells_excludes_only_preflight_failures():
    config = {
        "experiment_6_11": {
            "embeddings": ["e-good", "e-bad"],
            "rerankers": ["none", "r-bad"],
            "main_models": ["m-good", "m-bad"],
        }
    }
    readiness = {
        "probes": [
            {"component": "embedding", "name": "e-bad", "status": "error"},
            {"component": "reranker", "name": "r-bad", "status": "error"},
            {"component": "chat", "name": "m-bad", "status": "error"},
        ]
    }
    assert required_611_cells(config, readiness) == {("e-good", "none", "m-good")}
