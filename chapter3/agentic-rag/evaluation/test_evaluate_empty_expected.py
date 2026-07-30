"""
Test suite locking out ZeroDivisionError in RAGEvaluator.evaluate_response
when test_case contains empty expected_keywords or expected_analysis lists.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from evaluate import RAGEvaluator


def test_evaluate_response_empty_expected_keywords():
    """
    Ensure evaluate_response gracefully handles empty expected_keywords without raising ZeroDivisionError.
    """
    evaluator = RAGEvaluator.__new__(RAGEvaluator)
    test_case = {
        "id": "tc1",
        "question": "Sample query?",
        "expected_keywords": []
    }
    result = evaluator.evaluate_response("Sample answer", test_case)
    assert result["metrics"]["keyword_recall"] == 1.0


def test_evaluate_response_empty_expected_analysis():
    """
    Ensure evaluate_response gracefully handles empty expected_analysis without raising ZeroDivisionError.
    """
    evaluator = RAGEvaluator.__new__(RAGEvaluator)
    test_case = {
        "id": "tc2",
        "question": "Sample query?",
        "expected_analysis": []
    }
    result = evaluator.evaluate_response("Sample answer", test_case)
    assert result["metrics"]["analysis_recall"] == 1.0
