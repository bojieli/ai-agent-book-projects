"""
Tests for the SFT training-data quality auditor (chapter 8 CoT distillation).

Covers valid data, format errors, length outliers, exact and near duplicates,
label noise, tokenizer risks, boundary gaps, empty/single/all-duplicate
datasets, and quality-score computation. All tests are fully offline and
deterministic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
COT_DIR = HERE / "chapter8" / "cot-distillation"
if str(COT_DIR) not in sys.path:
    sys.path.insert(0, str(COT_DIR))

from sft_data_auditor import (  # noqa: E402
    AuditReport,
    QualityIssue,
    SFTDataQualityAuditor,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _example(user: str, assistant: str) -> dict:
    return {
        "messages": [
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ]
    }


def _write_jsonl(tmp_path: Path, examples: list[dict]) -> Path:
    p = tmp_path / "sft.jsonl"
    p.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in examples) + "\n",
        encoding="utf-8",
    )
    return p


def _valid_examples(n: int = 5) -> list[dict]:
    """Return ``n`` valid, diverse, non-duplicate examples."""
    out = []
    for i in range(n):
        out.append(
            _example(
                f"Question number {i}: " + " ".join(["detail"] * (i + 3)),
                f"The answer is {2 * i}. " + " ".join(["step"] * (i + 3)),
            )
        )
    return out


# --------------------------------------------------------------------------- #
# Valid data
# --------------------------------------------------------------------------- #
def test_valid_data_passes_clean(tmp_path):
    examples = _valid_examples(6)
    path = _write_jsonl(tmp_path, examples)
    report = SFTDataQualityAuditor().audit_file(path)
    assert report.total_examples == 6
    assert report.total_issues == 0
    assert report.issues == []
    assert report.duplicate_count == 0
    assert report.near_duplicate_count == 0
    assert report.overall_quality_score == pytest.approx(1.0)


def test_valid_data_length_stats_populated(tmp_path):
    examples = _valid_examples(4)
    report = SFTDataQualityAuditor().audit_lines(examples)
    assert report.length_stats["min"] > 0
    assert report.length_stats["max"] >= report.length_stats["min"]
    assert report.length_stats["mean"] >= report.length_stats["min"]
    assert report.length_stats["median"] >= 0
    assert report.length_stats["std"] >= 0


# --------------------------------------------------------------------------- #
# Format errors
# --------------------------------------------------------------------------- #
def test_format_error_missing_messages():
    report = SFTDataQualityAuditor().audit_lines([{"other": "no messages"}])
    fmt = [i for i in report.issues if i.issue_type == "format_error"]
    assert len(fmt) == 1
    assert fmt[0].severity == "error"
    assert "missing or not a list" in fmt[0].description


def test_format_error_empty_content_and_bad_role():
    example = {
        "messages": [
            {"role": "user", "content": ""},
            {"role": "user", "content": ""},
        ]
    }
    report = SFTDataQualityAuditor().audit_lines([example])
    types = [i.issue_type for i in report.issues]
    assert types.count("format_error") >= 3  # empty[0] + empty[1] + alternation break

def test_format_error_non_string_content():
    example = {
        "messages": [
            {"role": "user", "content": 123},
            {"role": "assistant", "content": "ok"},
        ]
    }
    report = SFTDataQualityAuditor().audit_lines([example])
    fmt = [i for i in report.issues if i.issue_type == "format_error"]
    assert any("not a string" in i.description for i in fmt)


def test_format_error_role_alternation_break():
    example = {
        "messages": [
            {"role": "assistant", "content": "hi"},
            {"role": "user", "content": "hello"},
        ]
    }
    report = SFTDataQualityAuditor().audit_lines([example])
    fmt = [i for i in report.issues if i.issue_type == "format_error"]
    assert any("alternation" in i.description for i in fmt)


# --------------------------------------------------------------------------- #
# Length outliers
# --------------------------------------------------------------------------- #
def test_length_outlier_too_short():
    short = _example("hi", "ok")  # 2 words total, below default min_length=10
    report = SFTDataQualityAuditor(min_length=10).audit_lines([short])
    outliers = [i for i in report.issues if i.issue_type == "length_outlier"]
    assert len(outliers) == 1
    assert outliers[0].evidence["threshold"] == "min"


def test_length_outlier_too_long():
    long_text = " ".join(["word"] * 5000)
    example = _example(long_text, long_text)
    report = SFTDataQualityAuditor(max_length=4096).audit_lines([example])
    outliers = [i for i in report.issues if i.issue_type == "length_outlier"]
    assert len(outliers) == 1
    assert outliers[0].evidence["threshold"] == "max"


def test_length_within_bounds_no_outlier():
    text = " ".join(["word"] * 50)
    example = _example(text, text)
    report = SFTDataQualityAuditor(min_length=10, max_length=4096).audit_lines([example])
    assert not any(i.issue_type == "length_outlier" for i in report.issues)


# --------------------------------------------------------------------------- #
# Duplicates
# --------------------------------------------------------------------------- #
def test_exact_duplicates_found():
    ex = _example("What is 2+2?", "The answer is 4.")
    report = SFTDataQualityAuditor().audit_lines([ex, ex, ex])
    dups = [i for i in report.issues if i.issue_type == "duplicate" and i.evidence.get("kind") == "exact"]
    assert len(dups) == 2  # lines 2 and 3 flagged against line 1
    assert report.duplicate_count == 2
    assert all(i.severity == "error" for i in dups)


def test_near_duplicates_same_user_different_assistant():
    examples = [
        _example("What is 2+2?", "The answer is 4."),
        _example("What is 2+2?", "The answer is 5."),
    ]
    report = SFTDataQualityAuditor().audit_lines(examples)
    near = [i for i in report.issues if i.issue_type == "duplicate" and i.evidence.get("kind") == "near"]
    assert len(near) == 1
    assert report.near_duplicate_count == 1
    assert near[0].severity == "warning"
    assert "label noise" in near[0].description


def test_same_user_same_assistant_not_near_duplicate():
    ex = _example("What is 2+2?", "The answer is 4.")
    report = SFTDataQualityAuditor().audit_lines([ex, ex])
    near = [i for i in report.issues if i.evidence.get("kind") == "near"]
    assert near == []  # exact duplicate, not near


# --------------------------------------------------------------------------- #
# Label noise
# --------------------------------------------------------------------------- #
def test_label_noise_placeholder_todo():
    example = _example("Write a function.", "def f():\n    TODO implement this")
    report = SFTDataQualityAuditor().audit_lines([example])
    noise = [i for i in report.issues if i.issue_type == "label_noise"]
    assert len(noise) == 1
    assert noise[0].severity == "error"
    assert "placeholder" in noise[0].description


def test_label_noise_placeholder_insert_marker():
    example = _example("Write a summary.", "Here is [insert summary here].")
    report = SFTDataQualityAuditor().audit_lines([example])
    noise = [i for i in report.issues if i.issue_type == "label_noise"]
    assert len(noise) == 1


def test_label_noise_contradiction():
    example = _example("Is the sky blue?", "Yes, the sky is blue. No, it is not.")
    report = SFTDataQualityAuditor().audit_lines([example])
    noise = [i for i in report.issues if i.issue_type == "label_noise"]
    assert any("contradiction" in i.description for i in noise)


def test_label_noise_clean_response_none():
    example = _example("Is the sky blue?", "Yes, the sky is blue on a clear day.")
    report = SFTDataQualityAuditor().audit_lines([example])
    assert not any(i.issue_type == "label_noise" for i in report.issues)


# --------------------------------------------------------------------------- #
# Tokenizer compatibility
# --------------------------------------------------------------------------- #
def test_tokenizer_risk_curly_quotes():
    example = _example("What\u2019s up?", "Not much.")
    report = SFTDataQualityAuditor().audit_lines([example])
    risks = [i for i in report.issues if i.issue_type == "tokenizer_risk"]
    assert len(risks) == 1
    assert "curly quote" in risks[0].description


def test_tokenizer_risk_zero_width_space_and_bom():
    example = _example("Hello\u200bworld", "\ufeffAnswer.")
    report = SFTDataQualityAuditor().audit_lines([example])
    risks = [i for i in report.issues if i.issue_type == "tokenizer_risk"]
    assert len(risks) == 1
    chars = risks[0].evidence["characters"]
    assert "zero-width space" in chars
    assert "BOM / zero-width no-break space" in chars


def test_tokenizer_risk_clean_ascii_none():
    example = _example("Hello world.", "Hi there.")
    report = SFTDataQualityAuditor().audit_lines([example])
    assert not any(i.issue_type == "tokenizer_risk" for i in report.issues)


# --------------------------------------------------------------------------- #
# Boundary coverage
# --------------------------------------------------------------------------- #
def test_boundary_gap_clustered_lengths():
    # Five examples all ~same length -> only one bucket occupied.
    examples = [_example("a b c d e", "f g h i j") for _ in range(5)]
    report = SFTDataQualityAuditor().audit_lines(examples)
    gaps = [i for i in report.issues if i.issue_type == "boundary_gap"]
    assert len(gaps) == 1
    assert gaps[0].evidence["occupied_buckets"] == 1


def test_boundary_gap_diverse_lengths_none():
    examples = [
        _example(" ".join(["w"] * 5), " ".join(["w"] * 5)),
        _example(" ".join(["w"] * 50), " ".join(["w"] * 50)),
        _example(" ".join(["w"] * 500), " ".join(["w"] * 500)),
        _example(" ".join(["w"] * 2000), " ".join(["w"] * 2000)),
        _example(" ".join(["w"] * 4000), " ".join(["w"] * 4000)),
    ]
    report = SFTDataQualityAuditor().audit_lines(examples)
    assert not any(i.issue_type == "boundary_gap" for i in report.issues)


# --------------------------------------------------------------------------- #
# Edge cases
# --------------------------------------------------------------------------- #
def test_empty_file(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    report = SFTDataQualityAuditor().audit_file(path)
    assert report.total_examples == 0
    assert report.total_issues == 0
    assert report.overall_quality_score == 0.0
    assert report.length_stats["min"] == 0.0


def test_single_example():
    example = _example("What is 1+1?", "The answer is 2.")
    report = SFTDataQualityAuditor().audit_lines([example])
    assert report.total_examples == 1
    # A single valid example should not trigger a boundary gap.
    assert not any(i.issue_type == "boundary_gap" for i in report.issues)


def test_all_duplicate_data():
    ex = _example("What is 2+2?", "The answer is 4.")
    report = SFTDataQualityAuditor().audit_lines([ex, ex, ex, ex])
    dups = [i for i in report.issues if i.issue_type == "duplicate"]
    assert len(dups) == 3
    assert report.duplicate_count == 3
    assert report.overall_quality_score < 1.0


def test_blank_lines_in_file_skipped(tmp_path):
    ex = _example("What is 1+1?", "The answer is 2.")
    path = tmp_path / "sft.jsonl"
    path.write_text(
        json.dumps(ex, ensure_ascii=False) + "\n\n\n" + json.dumps(ex, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report = SFTDataQualityAuditor().audit_file(path)
    assert report.total_examples == 2


# --------------------------------------------------------------------------- #
# Quality score
# --------------------------------------------------------------------------- #
def test_quality_score_perfect_for_clean_data():
    report = SFTDataQualityAuditor().audit_lines(_valid_examples(6))
    assert report.overall_quality_score == pytest.approx(1.0)


def test_quality_score_zero_for_empty():
    report = SFTDataQualityAuditor().audit_lines([])
    assert report.overall_quality_score == 0.0


def test_quality_score_decreases_with_errors():
    clean = _valid_examples(5)
    bad = [{"messages": []}]
    report_clean = SFTDataQualityAuditor().audit_lines(clean)
    report_bad = SFTDataQualityAuditor().audit_lines(clean + bad)
    assert report_bad.overall_quality_score < report_clean.overall_quality_score
    assert 0.0 <= report_bad.overall_quality_score <= 1.0


def test_quality_score_error_prevents_perfect():
    report = SFTDataQualityAuditor().audit_lines([
        _example("q", "a"),
        {"messages": []},
    ])
    assert report.overall_quality_score < 1.0


# --------------------------------------------------------------------------- #
# Report shape / constructor validation
# --------------------------------------------------------------------------- #
def test_report_dataclass_defaults():
    r = AuditReport()
    assert r.total_examples == 0
    assert r.issues == []
    assert r.issues_by_severity == {}
    assert r.issues_by_type == {}


def test_quality_issue_dataclass_fields():
    issue = QualityIssue(
        line_number=3,
        issue_type="format_error",
        severity="error",
        description="bad",
        evidence={"x": 1},
    )
    assert issue.line_number == 3
    assert issue.evidence == {"x": 1}


def test_constructor_rejects_invalid_thresholds():
    with pytest.raises(ValueError):
        SFTDataQualityAuditor(max_length=0)
    with pytest.raises(ValueError):
        SFTDataQualityAuditor(min_length=-1)
    with pytest.raises(ValueError):
        SFTDataQualityAuditor(min_length=100, max_length=50)


def test_issues_by_type_and_severity_populated():
    examples = [
        {"messages": []},  # format error
        _example("hi", "ok"),  # length outlier (too short)
    ]
    report = SFTDataQualityAuditor().audit_lines(examples)
    assert "format_error" in report.issues_by_type
    assert "length_outlier" in report.issues_by_type
    assert report.issues_by_severity.get("error", 0) >= 1
    assert report.issues_by_severity.get("warning", 0) >= 1
    assert report.total_issues == len(report.issues)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
