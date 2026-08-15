"""Regression test: malformed AGENT_PORT must not crash server startup.

Both server variants parsed AGENT_PORT with bare int() (one inside
build_parser's default, one in main), so AGENT_PORT=abc crashed with an
unhandled ValueError at startup. They now fall back to 8000 with a warning.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import server
import server_fastapi


def test_env_int_falls_back_on_malformed(monkeypatch):
    monkeypatch.setenv("AGENT_PORT", "abc")
    assert server._env_int("AGENT_PORT", 8000) == 8000
    assert server_fastapi._env_int("AGENT_PORT", 8000) == 8000


def test_env_int_parses_valid_value(monkeypatch):
    monkeypatch.setenv("AGENT_PORT", "9000")
    assert server._env_int("AGENT_PORT", 8000) == 9000
    assert server_fastapi._env_int("AGENT_PORT", 8000) == 9000


def test_env_int_default_when_unset(monkeypatch):
    monkeypatch.delenv("AGENT_PORT", raising=False)
    assert server._env_int("AGENT_PORT", 8000) == 8000


def test_build_parser_survives_malformed_env(monkeypatch):
    monkeypatch.setenv("AGENT_PORT", "not-a-port")
    args = server.build_parser().parse_args([])
    assert args.port == 8000
