import sys, os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath("chapter7/MultilingualReasoning"))
from gpt_oss_20b_sft import format_chat_template


def test_format_chat_template_handles_non_list_messages():
    mock_tokenizer = MagicMock()
    mock_tokenizer.apply_chat_template.return_value = "formatted text"

    # Example with missing / non-list messages
    example = {"messages": None}
    res = format_chat_template(example, mock_tokenizer)
    assert res["text"] == "formatted text"
    # apply_chat_template should receive [] when messages is None/invalid
    mock_tokenizer.apply_chat_template.assert_called_once_with([], tokenize=False)
