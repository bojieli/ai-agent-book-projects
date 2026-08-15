"""回归测试：FLUX_TICK_REAL 等浮点环境变量非法时不得让模块导入崩溃。

tasks.py 原来在模块导入时用裸 float() 解析 FLUX_TICK_REAL，
FLUX_TICK_REAL=abc 会让整个演示脚本以 ValueError 崩溃；现在回退到默认值并打印警告。
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import tasks


def test_env_float_falls_back_on_malformed(monkeypatch, capsys):
    monkeypatch.setenv("FLUX_TICK_REAL", "abc")
    assert tasks._env_float("FLUX_TICK_REAL", 0.4) == 0.4
    assert "FLUX_TICK_REAL" in capsys.readouterr().out


def test_env_float_parses_valid_value(monkeypatch):
    monkeypatch.setenv("FLUX_TICK_REAL", "0.1")
    assert tasks._env_float("FLUX_TICK_REAL", 0.4) == 0.1


def test_env_float_default_when_unset(monkeypatch):
    monkeypatch.delenv("FLUX_TICK_REAL", raising=False)
    assert tasks._env_float("FLUX_TICK_REAL", 0.4) == 0.4


def test_module_reload_survives_malformed_env(monkeypatch):
    """模块级 TICK_REAL 在环境变量非法时不得抛出 ValueError。"""
    monkeypatch.setenv("FLUX_TICK_REAL", "fast")
    importlib.reload(tasks)
    assert tasks.TICK_REAL == 0.4
