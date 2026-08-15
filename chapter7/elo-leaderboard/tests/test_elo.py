"""
Unit tests for Elo rating system
"""
import math

import pytest

from _bootstrap import bootstrap_experiment_root

bootstrap_experiment_root()

from elo_rating import EloRatingSystem


def test_initial_rating():
    """Test that models start with initial rating."""
    elo = EloRatingSystem(initial_rating=1000.0)
    assert elo.get_rating("model_a") == 1000.0
    assert elo.get_rating("model_b") == 1000.0


def test_expected_score():
    """Test expected score calculation."""
    elo = EloRatingSystem()
    
    # Equal ratings should give 50% probability
    assert elo.expected_score(1000, 1000) == 0.5
    
    # Higher rated player should have > 50% probability
    assert elo.expected_score(1200, 1000) > 0.5
    assert elo.expected_score(1000, 1200) < 0.5
    
    # 400 point difference should give ~91% probability
    prob = elo.expected_score(1400, 1000)
    assert 0.90 < prob < 0.92


def test_rating_update_win():
    """Test rating update when model_a wins."""
    elo = EloRatingSystem(initial_rating=1000.0, k_factor=32.0)
    
    new_a, new_b = elo.update_ratings("model_a", "model_b", "model_a")
    
    # Winner should gain rating, loser should lose rating
    assert new_a > 1000.0
    assert new_b < 1000.0
    
    # Total rating should be conserved (zero-sum)
    assert abs((new_a + new_b) - 2000.0) < 0.01


def test_rating_update_tie():
    """Test rating update for a tie."""
    elo = EloRatingSystem(initial_rating=1000.0, k_factor=32.0)
    
    new_a, new_b = elo.update_ratings("model_a", "model_b", "tie")
    
    # With equal ratings, tie should not change ratings much
    assert abs(new_a - 1000.0) < 0.01
    assert abs(new_b - 1000.0) < 0.01


def test_upset_gives_larger_change():
    """Test that unexpected results cause larger rating changes."""
    elo = EloRatingSystem(initial_rating=1000.0, k_factor=32.0)
    
    # Give model_a higher rating
    elo.ratings["model_a"] = 1200.0
    elo.ratings["model_b"] = 1000.0
    
    # If weaker model wins (upset), changes should be larger
    new_a_upset, new_b_upset = elo.update_ratings("model_a", "model_b", "model_b")
    
    # Reset
    elo.ratings["model_a"] = 1200.0
    elo.ratings["model_b"] = 1000.0
    
    # If stronger model wins (expected), changes should be smaller
    new_a_expected, new_b_expected = elo.update_ratings("model_a", "model_b", "model_a")
    
    # Upset should cause larger change
    change_upset = abs(new_a_upset - 1200.0)
    change_expected = abs(new_a_expected - 1200.0)
    
    assert change_upset > change_expected


def test_leaderboard_sorting():
    """Test that leaderboard is sorted by rating."""
    elo = EloRatingSystem(initial_rating=1000.0, k_factor=32.0)
    
    # Create some matches to differentiate ratings
    elo.update_ratings("model_a", "model_b", "model_a")
    elo.update_ratings("model_a", "model_c", "model_a")
    elo.update_ratings("model_b", "model_c", "model_b")
    
    leaderboard = elo.get_leaderboard()
    
    # Check descending order
    for i in range(len(leaderboard) - 1):
        assert leaderboard[i][1] >= leaderboard[i+1][1]
    
    # model_a should be first (won all matches)
    assert leaderboard[0][0] == "model_a"


def test_win_probability_symmetry():
    """Test that win probabilities sum to 1."""
    elo = EloRatingSystem()
    elo.ratings["model_a"] = 1200.0
    elo.ratings["model_b"] = 1000.0
    
    prob_a = elo.calculate_win_probability("model_a", "model_b")
    prob_b = elo.calculate_win_probability("model_b", "model_a")
    
    # Should sum to 1
    assert abs(prob_a + prob_b - 1.0) < 0.001


def test_match_counting():
    """Test that match and win counts are tracked correctly."""
    elo = EloRatingSystem(initial_rating=1000.0, k_factor=32.0)
    
    elo.update_ratings("model_a", "model_b", "model_a")  # model_a wins
    elo.update_ratings("model_a", "model_c", "model_b")  # model_a loses (2nd slot wins)
    elo.update_ratings("model_a", "model_b", "tie")      # tie -> 0.5 each
    
    # model_a played 3 matches
    assert elo.match_counts["model_a"] == 3
    
    # model_a won 1 match and tied 1 (1.5 total)
    assert elo.win_counts["model_a"] == 1.5
    
    # model_b played 2 matches
    assert elo.match_counts["model_b"] == 2


def test_copy():
    """Test that copy creates independent instance."""
    elo1 = EloRatingSystem(initial_rating=1000.0, k_factor=32.0)
    elo1.update_ratings("model_a", "model_b", "model_a")
    
    elo2 = elo1.copy()
    
    # Modify elo2
    elo2.update_ratings("model_a", "model_b", "model_b")
    
    # elo1 should be unchanged
    assert elo1.ratings["model_a"] != elo2.ratings["model_a"]


def test_reset():
    """Test that reset clears all data."""
    elo = EloRatingSystem(initial_rating=1000.0, k_factor=32.0)
    
    elo.update_ratings("model_a", "model_b", "model_a")
    elo.update_ratings("model_a", "model_c", "model_a")
    
    assert len(elo.ratings) > 0
    
    elo.reset()
    
    assert len(elo.ratings) == 0
    assert len(elo.match_counts) == 0
    assert len(elo.win_counts) == 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
