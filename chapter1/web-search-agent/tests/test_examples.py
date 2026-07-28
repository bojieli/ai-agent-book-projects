"""Unit tests for AdvancedWebSearchAgent helpers and failure classification."""

from unittest.mock import Mock

from agent import (
    MAX_ITERATIONS_MESSAGE,
    NO_INFO_MESSAGE,
    SEARCH_ERROR_PREFIX,
    is_failure_answer,
)
from examples import AdvancedWebSearchAgent


def build_advanced(answers):
    """AdvancedWebSearchAgent without a real OpenAI client; search_and_answer mocked."""
    instance = AdvancedWebSearchAgent.__new__(AdvancedWebSearchAgent)
    instance.search_and_answer = Mock(side_effect=answers)
    instance.clear_history = Mock()
    return instance


def test_is_failure_answer_covers_every_failure_fallback():
    assert is_failure_answer(f"{SEARCH_ERROR_PREFIX}: boom") is True
    assert is_failure_answer(MAX_ITERATIONS_MESSAGE) is True
    assert is_failure_answer(NO_INFO_MESSAGE) is True
    assert is_failure_answer("北京今天多云。") is False


def test_batch_search_marks_all_failure_fallbacks_as_error():
    """search_and_answer never raises; every failure fallback prefix must map to
    status='error', not just the '搜索过程中出现错误' one."""
    answers = [
        "正常答案",
        f"{SEARCH_ERROR_PREFIX}: network down",
        MAX_ITERATIONS_MESSAGE,
        NO_INFO_MESSAGE,
    ]
    instance = build_advanced(answers)

    results = instance.batch_search(["q1", "q2", "q3", "q4"])

    assert [r["status"] for r in results] == ["success", "error", "error", "error"]
    assert instance.clear_history.call_count == 4
