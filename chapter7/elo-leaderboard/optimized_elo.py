"""
Optimized Elo rating system using NumPy vectorization and Numba JIT
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple, List
from numba import jit
from tqdm import tqdm


@jit(nopython=True)
def expected_score_fast(rating_a: float, rating_b: float) -> float:
    """
    Fast expected score calculation using Numba JIT.
    
    Args:
        rating_a: Rating of model A
        rating_b: Rating of model B
        
    Returns:
        Expected probability that A wins
    """
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


@jit(nopython=True)
def process_elo_updates_vectorized(ratings: np.ndarray,
                                   model_a_indices: np.ndarray,
                                   model_b_indices: np.ndarray,
                                   outcomes: np.ndarray,
                                   k_factor: float,
                                   match_counts: np.ndarray,
                                   win_counts: np.ndarray) -> np.ndarray:
    """
    Process Elo updates using vectorized NumPy operations with Numba JIT.
    
    This is the core hot loop optimized with Numba for maximum performance.
    
    Args:
        ratings: Array of current ratings for all models
        model_a_indices: Indices of model A for each match
        model_b_indices: Indices of model B for each match
        outcomes: Match outcomes (1.0 = A wins, 0.0 = B wins, 0.5 = tie)
        k_factor: Elo K-factor
        match_counts: Array to track match counts per model
        win_counts: Array to track win counts per model
        
    Returns:
        Updated ratings array
    """
    n_matches = len(model_a_indices)
    
    for i in range(n_matches):
        idx_a = model_a_indices[i]
        idx_b = model_b_indices[i]
        outcome = outcomes[i]
        
        # Get current ratings
        rating_a = ratings[idx_a]
        rating_b = ratings[idx_b]
        
        # Calculate expected scores
        expected_a = 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))
        expected_b = 1.0 - expected_a
        
        # Update ratings
        ratings[idx_a] += k_factor * (outcome - expected_a)
        ratings[idx_b] += k_factor * ((1.0 - outcome) - expected_b)
        
        # Update counts
        match_counts[idx_a] += 1
        match_counts[idx_b] += 1
        win_counts[idx_a] += outcome
        win_counts[idx_b] += (1.0 - outcome)
    
    return ratings


@jit(nopython=True)
def calculate_expected_scores_vectorized(ratings_a: np.ndarray, 
                                        ratings_b: np.ndarray) -> np.ndarray:
    """
    Vectorized calculation of expected scores for multiple matches.
    
    Args:
        ratings_a: Array of ratings for model A
        ratings_b: Array of ratings for model B
        
    Returns:
        Array of expected scores for model A
    """
    return 1.0 / (1.0 + np.power(10.0, (ratings_b - ratings_a) / 400.0))


class NumpyEloRatingSystem:
    """
    Highly optimized Elo rating system using NumPy arrays and Numba JIT.
    
    Optimizations:
    - NumPy arrays for O(1) indexing instead of dictionary lookups
    - Numba JIT compilation of hot loops
    - Pre-allocated arrays to avoid memory reallocation
    - Integer indexing for models instead of string lookups
    """
    
    def __init__(self, initial_rating: float = 1000.0, k_factor: float = 4.0):
        """Initialize NumPy-based Elo system."""
        self.initial_rating = initial_rating
        self.k_factor = k_factor
        
        # Model name to index mapping
        self.model_to_idx: Dict[str, int] = {}
        self.idx_to_model: Dict[int, str] = {}
        
        # NumPy arrays for fast access
        self.ratings: np.ndarray = None
        self.match_counts: np.ndarray = None
        self.win_counts: np.ndarray = None
        
        self.n_models = 0
    
    def _prepare_data(self, df: pd.DataFrame):
        """
        Prepare NumPy arrays from DataFrame for fast processing.
        
        Args:
            df: DataFrame with columns 'model_a', 'model_b', 'winner'
        """
        print("Preparing data structures...")
        
        # Get all unique models
        all_models = sorted(set(df['model_a'].unique()) | set(df['model_b'].unique()))
        self.n_models = len(all_models)
        
        print(f"Found {self.n_models} unique models")
        
        # Create model mappings
        for idx, model in enumerate(all_models):
            self.model_to_idx[model] = idx
            self.idx_to_model[idx] = model
        
        # Initialize arrays
        self.ratings = np.full(self.n_models, self.initial_rating, dtype=np.float64)
        self.match_counts = np.zeros(self.n_models, dtype=np.int32)
        self.win_counts = np.zeros(self.n_models, dtype=np.float64)
        
        # Convert DataFrame columns to NumPy arrays with integer indices
        print("Converting model names to indices...")
        model_a_indices = df['model_a'].map(self.model_to_idx).values.astype(np.int32)
        model_b_indices = df['model_b'].map(self.model_to_idx).values.astype(np.int32)
        
        # Convert outcomes to numeric (1.0 for A wins, 0.0 for B wins, 0.5 for tie)
        print("Converting outcomes to numeric...")
        # 'tie (bothbad)' is a real Arena outcome; unmapped values become NaN and
        # would silently poison every rating they touch, so fall back to a tie
        # (same as EloRatingSystem.update_ratings).
        outcome_map = {'model_a': 1.0, 'model_b': 0.0,
                       'tie': 0.5, 'tie (bothbad)': 0.5}
        outcomes = df['winner'].map(outcome_map).fillna(0.5).values.astype(np.float64)
        
        return model_a_indices, model_b_indices, outcomes
    
    def process_matches_vectorized(self, df: pd.DataFrame, show_progress: bool = True):
        """
        Process all matches using vectorized NumPy operations and Numba JIT.
        
        This is the fastest way to compute Elo ratings for large datasets.
        
        Args:
            df: DataFrame with columns 'model_a', 'model_b', 'winner'
            show_progress: Whether to show progress bar
        """
        # Prepare data
        model_a_indices, model_b_indices, outcomes = self._prepare_data(df)
        
        print(f"\nProcessing {len(df)} matches with NumPy + Numba JIT...")
        
        # Process all matches using JIT-compiled function
        # This is where the magic happens - Numba compiles this to machine code
        if show_progress:
            # Process in chunks to show progress
            chunk_size = 50000
            n_chunks = (len(model_a_indices) + chunk_size - 1) // chunk_size
            
            for i in tqdm(range(n_chunks), desc="Processing matches"):
                start_idx = i * chunk_size
                end_idx = min((i + 1) * chunk_size, len(model_a_indices))
                
                self.ratings = process_elo_updates_vectorized(
                    self.ratings,
                    model_a_indices[start_idx:end_idx],
                    model_b_indices[start_idx:end_idx],
                    outcomes[start_idx:end_idx],
                    self.k_factor,
                    self.match_counts,
                    self.win_counts
                )
        else:
            self.ratings = process_elo_updates_vectorized(
                self.ratings,
                model_a_indices,
                model_b_indices,
                outcomes,
                self.k_factor,
                self.match_counts,
                self.win_counts
            )
        
        print("✓ Processing complete!")
    
    def get_leaderboard(self) -> List[Tuple]:
        """
        Get sorted leaderboard using NumPy's fast sorting.
        
        Returns:
            List of tuples (model, rating, matches, wins)
        """
        # Use NumPy's argsort for fast sorting
        sorted_indices = np.argsort(-self.ratings)  # Negative for descending order
        
        leaderboard = []
        for idx in sorted_indices:
            model = self.idx_to_model[idx]
            rating = float(self.ratings[idx])
            matches = int(self.match_counts[idx])
            wins = float(self.win_counts[idx])
            leaderboard.append((model, rating, matches, wins))
        
        return leaderboard
    
    def calculate_win_probability(self, model_a: str, model_b: str) -> float:
        """
        Calculate win probability using fast NumPy operations.
        
        Args:
            model_a: First model identifier
            model_b: Second model identifier
            
        Returns:
            Probability that model_a wins
        """
        if model_a not in self.model_to_idx or model_b not in self.model_to_idx:
            return 0.5
        
        idx_a = self.model_to_idx[model_a]
        idx_b = self.model_to_idx[model_b]
        
        rating_a = self.ratings[idx_a]
        rating_b = self.ratings[idx_b]
        
        return expected_score_fast(rating_a, rating_b)
    
    def get_win_rate_matrix(self) -> Dict[Tuple[str, str], float]:
        """
        Calculate pairwise win probability matrix using vectorized operations.
        
        Returns:
            Dictionary mapping (model_a, model_b) to win probability
        """
        matrix = {}
        
        # Vectorized calculation for all pairs
        for i in range(self.n_models):
            model_a = self.idx_to_model[i]
            
            # Calculate win probabilities against all other models at once
            ratings_a = np.full(self.n_models, self.ratings[i])
            win_probs = calculate_expected_scores_vectorized(ratings_a, self.ratings)
            
            for j in range(self.n_models):
                if i != j:
                    model_b = self.idx_to_model[j]
                    matrix[(model_a, model_b)] = float(win_probs[j])
        
        return matrix


def build_leaderboard_optimized(df: pd.DataFrame,
                                initial_rating: float = 1000.0,
                                k_factor: float = 4.0,
                                show_progress: bool = True) -> NumpyEloRatingSystem:
    """
    Build Elo leaderboard using highly optimized NumPy + Numba algorithm.
    
    This implementation is significantly faster than the basic version:
    - Uses NumPy arrays for O(1) indexing
    - Numba JIT compilation for hot loops
    - Pre-allocated arrays to avoid memory overhead
    - Integer-based model indexing instead of string lookups
    
    Args:
        df: DataFrame with match data (columns: model_a, model_b, winner)
        initial_rating: Starting rating for all models
        k_factor: Elo learning rate (K-factor)
        show_progress: Whether to display progress bar
        
    Returns:
        NumpyEloRatingSystem with final ratings
    """
    elo = NumpyEloRatingSystem(initial_rating=initial_rating, k_factor=k_factor)
    elo.process_matches_vectorized(df, show_progress=show_progress)
    return elo

