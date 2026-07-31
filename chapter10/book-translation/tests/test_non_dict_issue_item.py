"""Non-dict proofread issue entries must not AttributeError on .get."""
from agents import _report_issues


def test_string_issue_items_dropped():
    report = {
        "issues": [
            "术语不一致：token",
            {"chapter": "Ch1", "type": "术语不一致", "detail": "用了标记"},
        ],
    }
    issues = _report_issues(report)
    assert issues == [{"chapter": "Ch1", "type": "术语不一致", "detail": "用了标记"}]
    details = [
        i.get("detail", "") for i in issues if i.get("chapter") == "Ch1"
    ]
    assert details == ["用了标记"]


def test_null_and_dict_issues_still_work():
    assert _report_issues({"issues": None}) == []
    assert _report_issues({"issues": [{"chapter": "a", "detail": "x"}]}) == [
        {"chapter": "a", "detail": "x"}
    ]


def test_issues_scalar_like_empty():
    assert _report_issues({"issues": "not a list"}) == []
