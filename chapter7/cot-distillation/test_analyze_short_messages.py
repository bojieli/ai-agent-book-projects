"""SFT rows with messages shorter than 2 must not IndexError in analyze_data."""

import json
import sys
from pathlib import Path

import analyze_data as ad


def test_short_messages_skipped_without_index_error(tmp_path, monkeypatch, capsys):
    sft = tmp_path / "sft.jsonl"
    rows = [
        {"messages": [{"role": "user", "content": "only user"}]},
        {"messages": []},
        {
            "messages": [
                {"role": "user", "content": "q"},
                {
                    "role": "assistant",
                    "content": "<think>\n验算一遍\n</think>\nFinal Answer: 1",
                },
            ]
        },
    ]
    sft.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["analyze_data.py", "--sft", str(sft), "--raw", str(tmp_path / "missing.jsonl")],
    )
    ad.main()
    out = capsys.readouterr().out
    assert "SFT 样本数：3" in out
    assert "跳过 messages 不足 2 条的样本：2" in out
    assert "含反思/验算行为的样本：1/1" in out


def test_normal_two_message_row_still_scored(tmp_path, monkeypatch, capsys):
    sft = tmp_path / "sft.jsonl"
    sft.write_text(
        json.dumps(
            {
                "messages": [
                    {"role": "user", "content": "q"},
                    {"role": "assistant", "content": "<think>\nok\n</think>\n1"},
                ]
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["analyze_data.py", "--sft", str(sft), "--raw", str(tmp_path / "missing.jsonl")],
    )
    ad.main()
    out = capsys.readouterr().out
    assert "跳过" not in out
    assert "含反思/验算行为的样本：0/1" in out
