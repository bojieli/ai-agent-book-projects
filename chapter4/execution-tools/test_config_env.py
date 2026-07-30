"""Regression test: malformed numeric env vars must not crash config import.

TEMPERATURE / MAX_TOKENS / MAX_OUTPUT_LENGTH were parsed with bare
float()/int() at import time, so e.g. MAX_TOKENS=abc crashed every tool with
ValueError. They now fall back to defaults with a warning.
"""
import importlib
import os
from pathlib import Path

import config as cfg


def test_env_int_falls_back_on_malformed(monkeypatch, capsys):
    monkeypatch.setenv("MAX_TOKENS", "abc")
    assert cfg._env_int("MAX_TOKENS", 4096) == 4096
    assert "invalid MAX_TOKENS" in capsys.readouterr().err


def test_env_int_parses_valid_value(monkeypatch):
    monkeypatch.setenv("MAX_TOKENS", "123")
    assert cfg._env_int("MAX_TOKENS", 4096) == 123


def test_env_float_falls_back_on_malformed(monkeypatch, capsys):
    monkeypatch.setenv("TEMPERATURE", "hot")
    assert cfg._env_float("TEMPERATURE", 0.7) == 0.7
    assert "invalid TEMPERATURE" in capsys.readouterr().err


def test_env_float_parses_valid_value(monkeypatch):
    monkeypatch.setenv("TEMPERATURE", "0.2")
    assert cfg._env_float("TEMPERATURE", 0.7) == 0.2


def test_module_import_survives_malformed_env(monkeypatch):
    """Import-time class attributes must not raise on malformed env values."""
    monkeypatch.setenv("MAX_OUTPUT_LENGTH", "lots")
    # Execute a fresh copy under a unique name without replacing the shared
    # config module that implementation modules imported during collection.
    spec = importlib.util.spec_from_file_location(
        "_execution_tools_config_malformed_test",
        Path(cfg.__file__),
    )
    assert spec is not None and spec.loader is not None
    fresh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fresh)
    assert fresh.Config.MAX_OUTPUT_LENGTH == 1000
