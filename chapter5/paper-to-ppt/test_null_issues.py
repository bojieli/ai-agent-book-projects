"""Null review issues must summarize without TypeError."""
import sys
from unittest.mock import MagicMock

# demo.py imports heavy optional deps at module import time.
sys.modules.setdefault("dotenv", MagicMock())
sys.modules.setdefault("agents", MagicMock())
sys.modules.setdefault("make_figures", MagicMock())
sys.modules.setdefault("renderer", MagicMock())

from demo import summarize_review, _review_issues


def test_null_issues_like_empty():
    assert _review_issues({"issues": None}) == []
    text = summarize_review({"overall_score": 90, "pass": True, "issues": None})
    assert "issues=0" in text
    assert "high=0" in text


def test_issues_preserved():
    issues = [{"severity": "high"}]
    assert _review_issues({"issues": issues}) == issues
    text = summarize_review({"overall_score": 50, "pass": False, "issues": issues})
    assert "high=1" in text


def test_non_dict_issue_items_dropped():
    assert _review_issues({"issues": [None, {"severity": "high"}, "x"]}) == [{"severity": "high"}]
    text = summarize_review({"overall_score": 40, "pass": False, "issues": [None, {"severity": "high"}]})
    assert "high=1" in text
    assert "issues=1" in text
