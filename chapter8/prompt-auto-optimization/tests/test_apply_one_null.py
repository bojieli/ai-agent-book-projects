from coding_agent import _apply_one


def test_apply_one_null_old_str():
    content, err = _apply_one("hello world", None, "x")
    assert content == "hello world"
    assert err is not None
    assert "null" in err


def test_apply_one_null_new_str():
    content, err = _apply_one("hello world", "hello", None)
    assert content == "hello world"
    assert err is not None
    assert "null" in err


def test_apply_one_normal():
    content, err = _apply_one("hello world", "hello", "hi")
    assert err is None
    assert content == "hi world"
