from coding_agent import _apply_edits_from_args, _apply_one


def test_null_edits_like_empty():
    working, applied, errors, edits = _apply_edits_from_args("hello world", {"edits": None})
    assert working == "hello world"
    assert applied == 0
    assert errors == []
    assert edits == []


def test_apply_edits_normal():
    working, applied, errors, edits = _apply_edits_from_args(
        "hello world",
        {"edits": [{"old_str": "hello", "new_str": "hi"}]},
    )
    assert working == "hi world"
    assert applied == 1
    assert errors == []
    assert len(edits) == 1


def test_apply_one_still_rejects_null_strings():
    content, err = _apply_one("hello", None, "x")
    assert err is not None
