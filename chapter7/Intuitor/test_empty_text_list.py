"""Regression: empty sample text list must not IndexError."""


def _extract_model_output(sample_data):
    text_field = sample_data.get('text', [''])
    if isinstance(text_field, list):
        return text_field[0] if text_field else ''
    return text_field if text_field is not None else ''


def test_empty_text_list():
    assert _extract_model_output({"text": []}) == ""


def test_nonempty_text_list():
    assert _extract_model_output({"text": ["hello"]}) == "hello"


def test_source_guards_empty_list():
    from pathlib import Path
    src = Path(__file__).with_name("evaluate_from_cache.py").read_text()
    assert "text_field[0] if text_field else ''" in src
