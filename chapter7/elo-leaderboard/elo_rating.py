"""
Elo Rating System Implementation
Based on Bradley-Terry model for pairwise comparison
"""
import numpy as np
from typing import Dict, Tuple, Optional


class EloRatingSystem:
    """
    Implementation of Elo rating system for model comparison.
    
    The Elo system updates ratings based on pairwise comparison outcomes,
    where the rating difference between two models determines expected win probability.
    """
    
    def __init__(self, initial_rating: float = 1000.0, k_factor: float = 4.0):
        """
        Initialize Elo rating system.
        
        Args:
            initial_rating: Starting rating for all models
            k_factor: Learning rate controlling magnitude of rating updates
        """
        self.initial_rating = initial_rating
        self.k_factor = k_factor
        self.ratings: Dict[str, float] = {}
        self.match_counts: Dict[str, int] = {}
        self.win_counts: Dict[str, float] = {}  # ties add 0.5, so this is float
    
    def get_rating(self, model: str) -> float:
        """Get current rating for a model, initializing if necessary."""
        if model not in self.ratings:
            self.ratings[model] = self.initial_rating
            self.match_counts[model] = 0
            self.win_counts[model] = 0
        return self.ratings[model]
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Calculate expected win probability for model A against model B.
        
        Uses logistic function: P(A wins) = 1 / (1 + 10^((R_B - R_A)/400))
        
        Args:
            rating_a: Rating of model A
            rating_b: Rating of model B
            
        Returns:
            Expected probability that A wins (between 0 and 1)
        """
        return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))
    
    def update_ratings(self, model_a: str, model_b: str, outcome: str) -> Tuple[float, float]:
        """
        Update ratings after a match between two models.
        
        Args:
            model_a: Identifier for first model
            model_b: Identifier for second model
            outcome: Match result ('model_a', 'model_b', or 'tie')
            
        Returns:
            Tuple of (new_rating_a, new_rating_b)
        """
        # Get current ratings
        rating_a = self.get_rating(model_a)
        rating_b = self.get_rating(model_b)
        
        # Calculate expected scores
        expected_a = self.expected_score(rating_a, rating_b)
        expected_b = 1.0 - expected_a
        
        # Determine actual scores
        if outcome == 'model_a':
            score_a, score_b = 1.0, 0.0
            self.win_counts[model_a] = self.win_counts.get(model_a, 0) + 1
        elif outcome == 'model_b':
            score_a, score_b = 0.0, 1.0
            self.win_counts[model_b] = self.win_counts.get(model_b, 0) + 1
        else:  # tie
            score_a, score_b = 0.5, 0.5
            # A tie counts as half a win for each side, keeping win_counts (and
            # the win-rate derived from it) consistent with the 0.5-per-tie
            # convention used elsewhere (leaderboard win-rate matrix, CLI stats).
            self.win_counts[model_a] = self.win_counts.get(model_a, 0) + 0.5
            self.win_counts[model_b] = self.win_counts.get(model_b, 0) + 0.5
        
        # Update ratings using Elo formula
        new_rating_a = rating_a + self.k_factor * (score_a - expected_a)
        new_rating_b = rating_b + self.k_factor * (score_b - expected_b)
        
        # Store updated ratings
        self.ratings[model_a] = new_rating_a
        self.ratings[model_b] = new_rating_b
        
        # Update match counts
        self.match_counts[model_a] = self.match_counts.get(model_a, 0) + 1
        self.match_counts[model_b] = self.match_counts.get(model_b, 0) + 1
        
        return new_rating_a, new_rating_b
    
    def get_leaderboard(self) -> list:
        """
        Get current leaderboard sorted by rating.
        
        Returns:
            List of tuples (model, rating, matches, wins) sorted by rating descending
        """
        leaderboard = []
        for model in self.ratings:
            leaderboard.append((
                model,
                self.ratings[model],
                self.match_counts.get(model, 0),
                self.win_counts.get(model, 0)
            ))
        
        # Sort by rating descending
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        return leaderboard
    
    def calculate_win_probability(self, model_a: str, model_b: str) -> float:
        """
        Calculate win probability of model_a against model_b based on current ratings.
        
        Args:
            model_a: First model identifier
            model_b: Second model identifier
            
        Returns:
            Probability that model_a wins (between 0 and 1)
        """
        rating_a = self.get_rating(model_a)
        rating_b = self.get_rating(model_b)
        return self.expected_score(rating_a, rating_b)
    
    def get_win_rate_matrix(self) -> Dict[Tuple[str, str], float]:
        """
        Calculate pairwise win probability matrix for all models.
        
        Returns:
            Dictionary mapping (model_a, model_b) to win probability of model_a
        """
        models = sorted(self.ratings.keys())
        matrix = {}
        
        for model_a in models:
            for model_b in models:
                if model_a != model_b:
                    prob = self.calculate_win_probability(model_a, model_b)
                    matrix[(model_a, model_b)] = prob
        
        return matrix
    
    def reset(self):
        """Reset all ratings to initial values."""
        self.ratings.clear()
        self.match_counts.clear()
        self.win_counts.clear()
    
    def copy(self) -> 'EloRatingSystem':
        """Create a deep copy of the current rating system."""
        new_system = EloRatingSystem(self.initial_rating, self.k_factor)
        new_system.ratings = self.ratings.copy()
        new_system.match_counts = self.match_counts.copy()
        new_system.win_counts = self.win_counts.copy()
        return new_system

