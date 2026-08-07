"""Regression: load_verified_messages must accept fullwidth colon and case-insensitive Final Answer."""

import json
from pathlib import Path
from train_student import load_verified_messages


def test_load_verified_messages_fullwidth_colon(tmp_path: Path):
    sample = {
        "messages": [
            {"role": "user", "content": "What is 2 + 2?"},
            {"role": "assistant", "content": "<think>\n2+2=4\n</think>\n\nFinal Answer：4"},
        ]
    }
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(json.dumps(sample) + "\n", encoding="utf-8")
    rows = load_verified_messages(dataset)
    assert len(rows) == 1
    assert rows[0][1]["content"].endswith("Final Answer：4")


def test_load_verified_messages_lowercase_colon(tmp_path: Path):
    sample = {
        "messages": [
            {"role": "user", "content": "What is 2 + 2?"},
            {"role": "assistant", "content": "<think>\n2+2=4\n</think>\n\nfinal answer: 4"},
        ]
    }
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(json.dumps(sample) + "\n", encoding="utf-8")
    rows = load_verified_messages(dataset)
    assert len(rows) == 1
