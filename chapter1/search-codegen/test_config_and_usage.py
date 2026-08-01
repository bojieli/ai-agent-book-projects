import os
from pathlib import Path
import subprocess
import sys

import example_request


ROOT = Path(__file__).parent


def _import_config_with(value: str | None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if value is None:
        env.pop("DEFAULT_MAX_TOKENS", None)
    else:
        env["DEFAULT_MAX_TOKENS"] = value
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "from config import Config; print(repr(Config.DEFAULT_MAX_TOKENS))",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=False,
        text=True,
    )


def test_default_max_tokens_import_accepts_only_values_int_can_parse():
    for value in (None, "", "   ", "4000.0", "abc", "²", "-1", "+1"):
        result = _import_config_with(value)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "None"

    result = _import_config_with(" 4000 ")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "4000"


def test_chat_completions_usage_uses_chat_token_and_detail_keys(monkeypatch, capsys):
    payload = {
        "usage": {
            "prompt_tokens": 123,
            "completion_tokens": 45,
            "total_tokens": 168,
            "prompt_tokens_details": {"cached_tokens": 7},
            "completion_tokens_details": {"reasoning_tokens": 9},
        }
    }

    class FakeResponse:
        status_code = 200

        def json(self):
            return payload

    monkeypatch.setattr(
        example_request.requests,
        "post",
        lambda *args, **kwargs: FakeResponse(),
    )

    result = example_request.make_gpt5_openrouter_request("key", "system", "user")
    output = capsys.readouterr().out

    assert result == payload
    assert "Input: 123 tokens (cached: 7)" in output
    assert "Output: 45 tokens (reasoning: 9)" in output
    assert "Total: 168" in output

    payload = {
        "usage": {
            "input_tokens": 210,
            "output_tokens": 34,
            "total_tokens": 244,
            "input_tokens_details": {"cached_tokens": 11},
            "output_tokens_details": {"reasoning_tokens": 13},
        }
    }
    result = example_request.make_gpt5_openrouter_request("key", "system", "user")
    output = capsys.readouterr().out

    assert result == payload
    assert "Input: 210 tokens (cached: 11)" in output
    assert "Output: 34 tokens (reasoning: 13)" in output
    assert "Total: 244" in output
