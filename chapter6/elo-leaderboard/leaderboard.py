"""
Leaderboard calculation and analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from tqdm import tqdm
from elo_rating import EloRatingSystem


def build_leaderboard(df: pd.DataFrame, 
                      initial_rating: float = 1000.0,
                      k_factor: float = 32.0,
                      show_progress: bool = True) -> EloRatingSystem:
    """
    Build Elo leaderboard from voting data.
    
    Args:
        df: DataFrame with columns 'model_a', 'model_b', 'winner'
        initial_rating: Starting rating for all models
        k_factor: Elo learning rate
        show_progress: Whether to show progress bar
        
    Returns:
        EloRatingSystem with final ratings
    """
    elo = EloRatingSystem(initial_rating=initial_rating, k_factor=k_factor)
    
    iterator = tqdm(df.iterrows(), total=len(df), desc="Processing matches") if show_progress else df.iterrows()
    
    for idx, row in iterator:
        model_a = row['model_a']
        model_b = row['model_b']
        winner = row['winner']
        
        elo.update_ratings(model_a, model_b, winner)
    
    return elo


def calculate_win_rate_matrix_from_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate empirical win rate matrix directly from vote data.
    
    Args:
        df: DataFrame with columns 'model_a', 'model_b', 'winner'
        
    Returns:
        DataFrame with win rates (rows beat columns)
    """
    # Get all unique models
    all_models = sorted(set(df['model_a'].unique()) | set(df['model_b'].unique()))
    
    # Initialize counts
    wins = {model: {opponent: 0 for opponent in all_models} for model in all_models}
    total = {model: {opponent: 0 for opponent in all_models} for model in all_models}
    
    # Count wins and totals
    for _, row in df.iterrows():
        model_a = row['model_a']
        model_b = row['model_b']
        winner = row['winner']
        
        total[model_a][model_b] += 1
        total[model_b][model_a] += 1
        
        if winner == 'model_a':
            wins[model_a][model_b] += 1
        elif winner == 'model_b':
            wins[model_b][model_a] += 1
        else:  # tie
            wins[model_a][model_b] += 0.5
            wins[model_b][model_a] += 0.5
    
    # Calculate win rates
    win_rates = {}
    for model in all_models:
        win_rates[model] = {}
        for opponent in all_models:
            if model == opponent:
                win_rates[model][opponent] = 0.5
            elif total[model][opponent] > 0:
                win_rates[model][opponent] = wins[model][opponent] / total[model][opponent]
            else:
                win_rates[model][opponent] = np.nan
    
    # Convert to DataFrame
    win_rate_df = pd.DataFrame(win_rates).T
    win_rate_df = win_rate_df[all_models]  # Ensure consistent ordering
    
    return win_rate_df


def compare_win_rates(elo_system: EloRatingSystem, empirical_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare predicted win rates from Elo with empirical win rates.
    
    Args:
        elo_system: Trained Elo rating system
        empirical_df: DataFrame with empirical win rates
        
    Returns:
        DataFrame with comparison statistics
    """
    models = empirical_df.index.tolist()
    
    comparisons = []
    for model_a in models:
        for model_b in models:
            if model_a != model_b:
                empirical = empirical_df.loc[model_a, model_b]
                if not np.isnan(empirical):
                    predicted = elo_system.calculate_win_probability(model_a, model_b)
                    error = abs(predicted - empirical)
                    comparisons.append({
                        'model_a': model_a,
                        'model_b': model_b,
                        'empirical': empirical,
                        'predicted': predicted,
                        'error': error
                    })
    
    comparison_df = pd.DataFrame(comparisons)
    return comparison_df


def build_historical_leaderboards(df: pd.DataFrame,
                                   time_slices: List[Tuple],
                                   initial_rating: float = 1000.0,
                                   k_factor: float = 32.0) -> List[Tuple]:
    """
    Build leaderboard snapshots at different time points.
    
    Args:
        df: Full voting DataFrame
        time_slices: List of (end_date, slice_df) tuples from get_time_slices
        initial_rating: Starting rating
        k_factor: Elo learning rate
        
    Returns:
        List of (date, leaderboard_data) tuples
    """
    historical_leaderboards = []
    
    for end_date, slice_df in tqdm(time_slices, desc="Building historical leaderboards"):
        elo = build_leaderboard(slice_df, initial_rating, k_factor, show_progress=False)
        leaderboard = elo.get_leaderboard()
        
        # Convert to DataFrame for easier handling
        lb_df = pd.DataFrame(leaderboard, columns=['model', 'rating', 'matches', 'wins'])
        lb_df['date'] = end_date
        lb_df['rank'] = range(1, len(lb_df) + 1)
        
        historical_leaderboards.append((end_date, lb_df))
    
    return historical_leaderboards


def get_rating_history(historical_leaderboards: List[Tuple]) -> pd.DataFrame:
    """
    Extract rating history for all models over time.
    
    Args:
        historical_leaderboards: List of (date, leaderboard_df) tuples
        
    Returns:
        DataFrame with columns: date, model, rating, rank
    """
    all_data = []
    
    for date, lb_df in historical_leaderboards:
        for _, row in lb_df.iterrows():
            all_data.append({
                'date': date,
                'model': row['model'],
                'rating': row['rating'],
                'rank': row['rank'],
                'matches': row['matches'],
                'wins': row['wins']
            })
    
    cols = ['date', 'model', 'rating', 'rank', 'matches', 'wins']
    if not all_data:
        return pd.DataFrame(columns=cols)
    history_df = pd.DataFrame(all_data)
    return history_df


def analyze_rating_changes(history_df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Analyze rating changes over time for top models.
    
    Args:
        history_df: DataFrame from get_rating_history
        top_n: Number of top models to analyze
        
    Returns:
        DataFrame with change statistics
    """
    stats_cols = [
        'model', 'final_rating', 'initial_rating', 'rating_change',
        'max_rating', 'min_rating', 'volatility', 'total_matches',
    ]
    if history_df is None or len(history_df) == 0:
        return pd.DataFrame(columns=stats_cols)

    # Get final ratings
    final_date = history_df['date'].max()
    final_ratings = history_df[history_df['date'] == final_date].nlargest(top_n, 'rating')
    top_models = final_ratings['model'].tolist()
    
    # Calculate statistics for each model
    stats = []
    for model in top_models:
        model_data = history_df[history_df['model'] == model].sort_values('date')
        
        if len(model_data) > 0:
            initial_rating = model_data.iloc[0]['rating']
            final_rating = model_data.iloc[-1]['rating']
            max_rating = model_data['rating'].max()
            min_rating = model_data['rating'].min()
            rating_change = final_rating - initial_rating
            volatility = model_data['rating'].std()
            
            stats.append({
                'model': model,
                'final_rating': final_rating,
                'initial_rating': initial_rating,
                'rating_change': rating_change,
                'max_rating': max_rating,
                'min_rating': min_rating,
                'volatility': volatility,
                'total_matches': model_data.iloc[-1]['matches']
            })
    
    if not stats:
        return pd.DataFrame(columns=stats_cols)
    stats_df = pd.DataFrame(stats).sort_values('final_rating', ascending=False)
    return stats_df

