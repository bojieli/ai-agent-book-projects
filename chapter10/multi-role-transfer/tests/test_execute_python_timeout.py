"""Regression: execute_python must not hang on infinite loops."""
import time

from tools import execute_python


def test_execute_python_timeout_on_infinite_loop():
    t0 = time.time()
    result = execute_python("while True: pass", timeout=1)
    elapsed = time.time() - t0
    assert "执行超时" in result
    assert elapsed < 3


def test_execute_python_normal_print():
    result = execute_python("print(1 + 1)", timeout=5)
    assert "2" in result
