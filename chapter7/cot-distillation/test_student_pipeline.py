import json

from evaluate_student import behavior_flags, compare_binary, exact_two_sided_sign_p_value
from train_student import load_verified_messages


def test_load_verified_messages_rejects_unverified_shape(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_text(json.dumps({"messages": [{"role": "user", "content": "q"}]}) + "\n")
    try:
        load_verified_messages(path)
    except ValueError as exc:
        assert "exactly two" in str(exc)
    else:
        raise AssertionError("invalid collection row was accepted for parameter training")


def test_paired_sign_test_detects_one_sided_student_gain():
    baseline = {str(i): False for i in range(8)}
    student = {str(i): True for i in range(8)}
    result = compare_binary(baseline, student)
    assert result["student_only"] == 8
    assert result["baseline_only"] == 0
    assert result["exact_two_sided_p_value"] == exact_two_sided_sign_p_value(0, 8)
    assert result["exact_two_sided_p_value"] < 0.05


def test_behavior_flags_cover_acceptance_categories():
    flags = behavior_flags("Wait, that is not right. Use another approach, then verify by substitution.")
    assert flags == {"reflection": True, "backtracking": True, "verification": True}
