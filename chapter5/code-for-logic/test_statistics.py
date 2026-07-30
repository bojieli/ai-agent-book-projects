from demo import campaign_completion, paired_statistics


def test_paired_statistics_detects_clear_code_gain():
    pure = [{"id": str(i), "correct": i < 2} for i in range(20)]
    code = [
        {"id": str(i), "correct": i < 19, "used_python_constraint": True}
        for i in range(20)
    ]
    result = paired_statistics(pure, code)
    assert result["code_accuracy"] == 0.95
    assert result["acceptance"]["code_accuracy_over_90_percent"] is True
    assert result["acceptance"]["code_significantly_higher_than_pure"] is True


def test_campaign_completion_requires_both_full_real_arms():
    puzzles = [{"id": f"p-{i}"} for i in range(84)]
    pure = [
        {"id": p["id"], "provider_receipts": [{"response_id": "r"}],
         "provider_error": None}
        for p in puzzles
    ]
    code = [
        {"id": p["id"], "provider_receipts": [{"response_id": "r"}],
         "provider_error": None, "used_python_constraint": True}
        for p in puzzles
    ]
    manifest = {
        "dataset": "K-and-K/perturbed-knights-and-knaves",
        "revision": "bc7ee75a15ee8196ccbdb7df3ab46284340412e2",
        "sampling": {"total": 84, "cells": 42, "per_cell": 2},
        "source_files": [{} for _ in range(42)],
        "label_validation": "all rows independently solved with python-constraint",
    }
    result = campaign_completion(
        {"pure": pure, "code": code}, puzzles, manifest, "both"
    )
    assert result["status"] == "complete"
    code[-1]["used_python_constraint"] = False
    assert campaign_completion(
        {"pure": pure, "code": code}, puzzles, manifest, "both"
    )["status"] == "incomplete"
