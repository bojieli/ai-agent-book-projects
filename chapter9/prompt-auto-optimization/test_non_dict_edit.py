"""Non-dict items in edits must not cause AttributeError or roll back valid edits in optimize_prompt."""
import tempfile
from unittest.mock import MagicMock, patch
from coding_agent import _apply_edits_from_args, optimize_prompt


def test_string_edit_item_skipped_with_warning():
    working, applied, errors, warnings, edits = _apply_edits_from_args(
        "hello world",
        {"edits": ["bad", {"old_str": "hello", "new_str": "hi"}]},
    )
    assert working == "hi world"
    assert applied == 1
    assert errors == []
    assert any("跳过非对象" in w for w in warnings)
    assert len(edits) == 2


def test_null_edit_item_skipped_with_warning():
    working, applied, errors, warnings, _ = _apply_edits_from_args(
        "hello world",
        {"edits": [None]},
    )
    assert working == "hello world"
    assert applied == 0
    assert errors == []
    assert any("跳过非对象" in w for w in warnings)


def test_null_edits_list_still_empty():
    working, applied, errors, warnings, edits = _apply_edits_from_args(
        "hello world", {"edits": None}
    )
    assert working == "hello world"
    assert applied == 0
    assert errors == []
    assert warnings == []
    assert edits == []


def test_optimize_prompt_applies_valid_edits_when_non_dict_items_present():
    """optimize_prompt must write valid edits to disk even if non-dict items are in the edits array."""
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
        f.write("hello world")
        prompt_file = f.name

    mock_tool_call = MagicMock()
    mock_tool_call.id = "tc_1"
    mock_tool_call.function.arguments = '{"edits": ["invalid_string_item", {"old_str": "hello", "new_str": "greetings"}]}'

    mock_msg = MagicMock()
    mock_msg.tool_calls = [mock_tool_call]
    mock_msg.content = None

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=mock_msg)]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("coding_agent.get_client", return_value=mock_client), \
         patch("coding_agent.get_model", return_value="gpt-4o"):
        res = optimize_prompt(prompt_file, feedback="test feedback", verbose=False)

    assert res["after"] == "greetings world"
    with open(prompt_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == "greetings world"
