"""SFT rows with null assistant content must not TypeError in analyze_data."""

import json
import sys

import analyze_data as ad


def test_null_assistant_content_skipped(tmp_path, monkeypatch, capsys):
    sft = tmp_path / "sft.jsonl"
    rows = [
        {
            "messages": [
                {"role": "user", "content": "q"},
                {"role": "assistant", "content": None},
            ]
        },
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
    assert "SFT 样本数：2" in out
    assert "跳过 messages 不足 2 条的样本：1" in out
    assert "含反思/验算行为的样本：1/1" in out


def test_missing_content_key_skipped(tmp_path, monkeypatch, capsys):
    sft = tmp_path / "sft.jsonl"
    sft.write_text(
        json.dumps(
            {
                "messages": [
                    {"role": "user", "content": "q"},
                    {"role": "assistant"},
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
    assert "跳过 messages 不足 2 条的样本：1" in out
