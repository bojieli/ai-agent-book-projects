from build_aime_2024 import convert
from demo import campaign_completion, paired_statistics


def test_aime_converter_rejects_non_complete_fixture():
    row = {
        "id": 1,
        "problem": "What is 1+1?",
        "answer": "2",
        "url": "https://example.test/aime",
        "year": "2024",
    }
    try:
        convert([row])
    except ValueError as exc:
        assert "expected 30" in str(exc)
    else:
        raise AssertionError("partial AIME source must not be accepted as the full benchmark")


def test_paired_statistics_detects_code_gain():
    rows = [
        {
            "cot_ok": i < 3,
            "code_ok": i < 10,
            "used_math_library": i == 0,
            "tool_calls": 1,
        }
        for i in range(10)
    ]
    result = paired_statistics(rows)
    assert result["code_accuracy"] == 1.0
    assert result["acceptance"]["code_significantly_higher_than_cot"] is True


def test_completion_requires_exact_30_task_two_arm_evidence():
    rows = []
    for division in ("I", "II"):
        for number in range(1, 16):
            rows.append({
                "id": f"source-row-{division}-{number}",
                "source": {
                    "problem_url": (
                        "https://artofproblemsolving.com/wiki/index.php/"
                        f"2024_AIME_{division}_Problems/Problem_{number}"
                    ),
                },
                "cot_evidence": {"provider_receipts": [{"response_id": "r"}]},
                "cot_error": None,
                "code_evidence": {"provider_receipts": [{"response_id": "r"}]},
                "code_error": None,
                "tool_calls": 1,
            })
    manifest = {
        "dataset": "HuggingFaceH4/aime_2024",
        "revision": "2fe88a2f1091d5048c0f36abc874fb997b3dd99a",
        "source_sha256": "26139847601a5037c237d5928b195e7260ca8074cf4f264b794af42847f79ccf",
        "problems": 30,
        "selection": "all published AIME I and AIME II 2024 problems",
    }
    result = campaign_completion(rows, "both", manifest)
    assert result["status"] == "complete"
    rows[-1]["tool_calls"] = 0
    result = campaign_completion(rows, "both", manifest)
    assert result["status"] == "incomplete"
    assert result["checks"]["every_code_trajectory_called_real_sandbox"] is False


def test_paired_statistics_empty_rows():
    result = paired_statistics([])
    assert result["n"] == 0
    assert result["cot_accuracy"] == 0.0
    assert result["code_accuracy"] == 0.0
    assert result["math_library_use_rate"] == 0.0
