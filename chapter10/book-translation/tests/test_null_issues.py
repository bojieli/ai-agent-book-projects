"""Null proofread issues must not TypeError when building report summaries."""
from agents import _report_issues


def test_null_issues_like_empty():
    assert _report_issues({"issues": None}) == []
    summary_issues = _report_issues({"issues": None})[:5]
    assert summary_issues == []
    details = [i.get("detail", "") for i in _report_issues({"issues": None})]
    assert details == []


def test_issues_preserved():
    issues = [{"chapter": "a", "detail": "fix me"}]
    assert _report_issues({"issues": issues}) == issues
