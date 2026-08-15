import pytest
from release_gate import evaluate_release_gate


def test_evaluate_release_gate_non_dict_edit_item():
    before = {"holdout": (5, 10), "boundary": (3, 5)}
    after = {"holdout": (5, 10), "boundary": (4, 5)}
    manifest = {
        "diff": "diff text",
        "edits": [None, "string_edit", {"old_str": "a", "new_str": "b"}],
        "source_case_ids": ["1"],
    }
    result = evaluate_release_gate(before, after, manifest)
    assert result["accepted"] is False
    assert result["checks"]["patch_is_auditable_old_to_new_edit"] is False
    assert result["decision"] == "reject_candidate"
