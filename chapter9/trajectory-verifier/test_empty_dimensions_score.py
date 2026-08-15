"""
TrajectoryVerifier.evaluate must handle empty dimensions list without raising ZeroDivisionError.
"""
from unittest.mock import MagicMock
from verifier import TrajectoryVerifier


def test_trajectory_verifier_handles_empty_dimensions():
    verifier = TrajectoryVerifier()
    verifier.result_verifier.evaluate = MagicMock(return_value=[])
    verifier.process_verifier.evaluate = MagicMock(return_value=[])
    verifier.quality_judge.evaluate = MagicMock(return_value=[])

    report = verifier.evaluate({"id": "traj-empty"})
    assert report["overall_score"] == 0.0
    assert report["critical_failures"] == []
    assert report["release_recommendation"] == "review_or_accept"
