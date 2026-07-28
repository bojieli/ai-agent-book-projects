"""Tests for CLI parsing, offline dispatch, and JSON output."""

import json

import main as cli
from config import Config


def test_parser_defaults_to_interactive_kimi_mode():
    args = cli.build_parser().parse_args([])

    assert args.query == []
    assert args.provider == "kimi"
    assert args.model == Config.DEFAULT_MODEL
    assert args.max_steps == Config.MAX_SEARCH_ITERATIONS
    assert args.base_url == Config.KIMI_BASE_URL
    assert args.output is None
    assert args.quiet is False


def test_parser_accepts_cli_overrides():
    args = cli.build_parser().parse_args(
        [
            "first",
            "question",
            "--provider",
            "offline-demo",
            "--model",
            "custom-model",
            "--max-steps",
            "3",
            "--base-url",
            "https://provider.test/v1",
            "--api-key",
            "explicit-key",
            "--output",
            "result.json",
            "--quiet",
        ]
    )

    assert args.query == ["first", "question"]
    assert args.provider == "offline-demo"
    assert args.model == "custom-model"
    assert args.max_steps == 3
    assert args.base_url == "https://provider.test/v1"
    assert args.api_key == "explicit-key"
    assert args.output == "result.json"
    assert args.quiet is True


def test_offline_cli_writes_utf8_json_without_api_credentials(tmp_path, capsys):
    output_path = tmp_path / "offline-result.json"

    cli.main(
        [
            "한국어",
            "질문",
            "--provider",
            "offline-demo",
            "--quiet",
            "--output",
            str(output_path),
        ]
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    output = capsys.readouterr().out
    assert payload["question"] == "한국어 질문"
    assert set(payload) == {"question", "trace", "answer"}
    assert payload["trace"][-1]["type"] == "answer"
    assert payload["answer"] == payload["trace"][-1]["content"]
    assert "💭" not in output
    assert "结果已保存到" in output


def test_offline_cli_uses_default_question_when_query_is_omitted(capsys):
    cli.main(["--provider", "offline-demo", "--quiet"])

    output = capsys.readouterr().out
    assert "Moonshot AI 的 Context Caching 是什么技术？" in output
