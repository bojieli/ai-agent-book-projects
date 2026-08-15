import pytest

from demo import load_cases, matches_expected


def test_expected_match_uses_word_boundaries():
    assert matches_expected("The answer is 79.", ["79"])
    assert matches_expected("FAST", ["fast"])
    assert not matches_expected("The answer is 179.", ["79"])


def test_case_manifest_validation(tmp_path):
    empty = tmp_path / "cases.json"
    empty.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed"):
        load_cases(empty)
