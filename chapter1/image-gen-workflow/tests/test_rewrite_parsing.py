"""改写节点输出的结构校验（离线，不发真实请求）。"""

import pytest

from pipeline import parse_rewrite_output

VALID_JSON = (
    '{"prompt": "1boy, programmer, overtime, masterpiece", '
    '"negative_prompt": "lowres, bad anatomy", '
    '"style_notes": "补充了质量词与情绪词"}'
)


def test_parse_plain_json():
    out = parse_rewrite_output(VALID_JSON)
    assert out["prompt"].startswith("1boy")
    assert out["negative_prompt"] == "lowres, bad anatomy"
    assert "质量词" in out["style_notes"]


def test_parse_fenced_json():
    out = parse_rewrite_output(f"```json\n{VALID_JSON}\n```")
    assert "programmer" in out["prompt"]


def test_parse_json_with_surrounding_prose():
    out = parse_rewrite_output(f"好的，这是改写结果：\n{VALID_JSON}\n希望对你有帮助")
    assert "overtime" in out["prompt"]


def test_negative_prompt_optional_default_empty():
    out = parse_rewrite_output('{"prompt": "a plant, masterpiece"}')
    assert out["negative_prompt"] == ""
    assert out["style_notes"] == ""


def test_reject_empty():
    with pytest.raises(ValueError):
        parse_rewrite_output("")


def test_reject_non_json():
    with pytest.raises(ValueError):
        parse_rewrite_output("抱歉，我无法完成改写。")


def test_reject_missing_prompt():
    with pytest.raises(ValueError):
        parse_rewrite_output('{"negative_prompt": "lowres"}')


def test_reject_empty_prompt():
    with pytest.raises(ValueError):
        parse_rewrite_output('{"prompt": "  "}')


def test_reject_wrong_type():
    with pytest.raises(ValueError):
        parse_rewrite_output('{"prompt": "ok", "negative_prompt": 123}')
