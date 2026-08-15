"""
Parallel processing utilities for Elo rating computation
"""
import pandas as pd
import numpy as np
from multiprocessing import Pool, cpu_count
from functools import partial
from typing import List, Tuple
from tqdm import tqdm
from elo_rating import EloRatingSystem


def process_time_slice(args: Tuple) -> Tuple:
    """
    Process a single time slice to build leaderboard.
    
    Args:
        args: Tuple of (end_date, slice_df, initial_rating, k_factor)
        
    Returns:
        Tuple of (end_date, leaderboard_data)
    """
    end_date, slice_df, initial_rating, k_factor = args
    
    # Build Elo system for this time slice
    elo = EloRatingSystem(initial_rating=initial_rating, k_factor=k_factor)
    
    # Process all matches in this slice
    for _, row in slice_df.iterrows():
        elo.update_ratings(row['model_a'], row['model_b'], row['winner'])
    
    # Get leaderboard
    leaderboard = elo.get_leaderboard()
    
    # Convert to list of dicts for easier handling
    lb_data = []
    for rank, (model, rating, matches, wins) in enumerate(leaderboard, 1):
        lb_data.append({
            'model': model,
            'rating': rating,
            'matches': matches,
            'wins': wins,
            'rank': rank,
            'date': end_date
        })
    
    return (end_date, lb_data)


def build_historical_leaderboards_parallel(df: pd.DataFrame,
                                           time_slices: List[Tuple],
                                           initial_rating: float = 1000.0,
                                           k_factor: float = 32.0,
                                           n_jobs: int = -1) -> List[Tuple]:
    """
    Build historical leaderboards using parallel processing.
    
    Args:
        df: Full voting DataFrame
        time_slices: List of (end_date, slice_df) tuples
        initial_rating: Starting rating
        k_factor: Elo learning rate
        n_jobs: Number of parallel jobs (-1 for all cores)
        
    Returns:
        List of (date, leaderboard_data) tuples
    """
    if n_jobs == -1:
        n_jobs = cpu_count()
    
    print(f"Building historical leaderboards using {n_jobs} cores...")
    
    # Prepare arguments for parallel processing
    args_list = [
        (end_date, slice_df, initial_rating, k_factor)
        for end_date, slice_df in time_slices
    ]
    
    # Process in parallel
    with Pool(processes=n_jobs) as pool:
        results = list(tqdm(
            pool.imap(process_time_slice, args_list),
            total=len(args_list),
            desc="Processing time slices"
        ))
    
    # Convert results to expected format
    historical_leaderboards = []
    for end_date, lb_data in results:
        lb_df = pd.DataFrame(lb_data)
        historical_leaderboards.append((end_date, lb_df))
    
    # Sort by date
    historical_leaderboards.sort(key=lambda x: x[0])
    
    return historical_leaderboards


def calculate_pairwise_win_rates_chunk(args: Tuple) -> List[dict]:
    """
    Calculate win rates for a chunk of model pairs.
    
    Args:
        args: Tuple of (model_pairs, df)
        
    Returns:
        List of win rate dictionaries
    """
    model_pairs, df = args
    
    results = []
    for model_a, model_b in model_pairs:
        # Filter matches between these two models
        matches = df[
            ((df['model_a'] == model_a) & (df['model_b'] == model_b)) |
            ((df['model_a'] == model_b) & (df['model_b'] == model_a))
        ]
        
        if len(matches) == 0:
            continue
        
        wins_a = 0
        total = len(matches)
        
        for _, row in matches.iterrows():
            # Arena data has four winner values; any non-win outcome
            # ('tie' and 'tie (bothbad)') is worth 0.5, matching the
            # serial calculate_win_rate_matrix_from_data.
            if row['model_a'] == model_a:
                if row['winner'] == 'model_a':
                    wins_a += 1
                elif row['winner'] != 'model_b':
                    wins_a += 0.5
            else:  # model_a is model_b in the row
                if row['winner'] == 'model_b':
                    wins_a += 1
                elif row['winner'] != 'model_a':
                    wins_a += 0.5
        
        win_rate = wins_a / total if total > 0 else 0.5
        
        results.append({
            'model_a': model_a,
            'model_b': model_b,
            'win_rate': win_rate,
            'total_matches': total
        })
    
    return results


def calculate_win_rate_matrix_parallel(df: pd.DataFrame, 
                                       models: List[str] = None,
                                       n_jobs: int = -1) -> pd.DataFrame:
    """
    Calculate win rate matrix using parallel processing.
    
    Args:
        df: DataFrame with match data
        models: List of models to include (if None, use all)
        n_jobs: Number of parallel jobs
        
    Returns:
        DataFrame with win rates
    """
    if n_jobs == -1:
        n_jobs = cpu_count()
    
    if models is None:
        models = sorted(set(df['model_a'].unique()) | set(df['model_b'].unique()))
    
    print(f"Calculating win rate matrix for {len(models)} models using {n_jobs} cores...")
    
    # Generate all model pairs
    model_pairs = [(m1, m2) for i, m1 in enumerate(models) for m2 in models[i+1:]]
    
    # Split pairs into chunks for parallel processing
    chunk_size = max(1, len(model_pairs) // (n_jobs * 4))
    chunks = [model_pairs[i:i+chunk_size] for i in range(0, len(model_pairs), chunk_size)]
    
    # Prepare arguments
    args_list = [(chunk, df) for chunk in chunks]
    
    # Process in parallel
    with Pool(processes=n_jobs) as pool:
        results_chunks = list(tqdm(
            pool.imap(calculate_pairwise_win_rates_chunk, args_list),
            total=len(args_list),
            desc="Calculating win rates"
        ))
    
    # Flatten results
    all_results = [item for chunk in results_chunks for item in chunk]
    
    # Build matrix. Pairs with no data stay NaN (the serial version's
    # convention) — 0.5 would misreport "no data" as an even record;
    # the diagonal is 0.5 by definition.
    win_rates = {model: {opponent: (0.5 if opponent == model else np.nan)
                         for opponent in models} for model in models}
    
    for result in all_results:
        model_a = result['model_a']
        model_b = result['model_b']
        win_rate = result['win_rate']
        
        win_rates[model_a][model_b] = win_rate
        win_rates[model_b][model_a] = 1.0 - win_rate
    
    # Convert to DataFrame
    win_rate_df = pd.DataFrame(win_rates).T
    win_rate_df = win_rate_df[models]
    
    return win_rate_df


def filter_data_parallel(df: pd.DataFrame, 
                        filters: dict,
                        n_jobs: int = -1) -> pd.DataFrame:
    """
    Filter large DataFrame using parallel processing.
    
    Args:
        df: Input DataFrame
        filters: Dictionary of filter conditions
        n_jobs: Number of parallel jobs
        
    Returns:
        Filtered DataFrame
    """
    if n_jobs == -1:
        n_jobs = min(cpu_count(), 4)  # Cap at 4 for filtering

    if len(df) == 0:
        return df.copy()

    n_jobs = max(1, min(n_jobs, len(df)))
    
    # Split DataFrame into chunks
    chunk_size = max(1, len(df) // n_jobs)
    chunks = [df.iloc[i:i+chunk_size] for i in range(0, len(df), chunk_size)]
    
    def apply_filters(chunk):
        filtered = chunk.copy()
        
        # Apply each filter
        if 'anony_only' in filters and filters['anony_only'] and 'anony' in filtered.columns:
            filtered = filtered[filtered['anony'] == True]
        
        if 'language' in filters and filters['language'] and 'language' in filtered.columns:
            filtered = filtered[filtered['language'] == filters['language']]
        
        if 'min_turn' in filters and 'turn' in filtered.columns:
            filtered = filtered[filtered['turn'] >= filters['min_turn']]
        
        if 'min_date' in filters and 'tstamp' in filtered.columns:
            min_timestamp = pd.to_datetime(filters['min_date']).timestamp()
            filtered = filtered[filtered['tstamp'] >= min_timestamp]
        
        if 'max_date' in filters and 'tstamp' in filtered.columns:
            max_timestamp = pd.to_datetime(filters['max_date']).timestamp()
            filtered = filtered[filtered['tstamp'] <= max_timestamp]
        
        return filtered
    
    # Process chunks in parallel
    with Pool(processes=n_jobs) as pool:
        filtered_chunks = pool.map(apply_filters, chunks)
    
    # Combine results
    result = pd.concat(filtered_chunks, ignore_index=True)
    
    return result


def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize DataFrame memory usage by downcasting numeric types.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Optimized DataFrame
    """
    print("Optimizing DataFrame memory usage...")
    
    initial_memory = df.memory_usage(deep=True).sum() / 1024**2
    
    # Optimize numeric columns
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type == 'int64':
            df[col] = pd.to_numeric(df[col], downcast='integer')
        elif col_type == 'float64':
            df[col] = pd.to_numeric(df[col], downcast='float')
    
    # Convert string columns to category if they have few unique values
    for col in df.select_dtypes(include=['object']).columns:
        try:
            # Check if column contains hashable types (not dict, list, etc.)
            # Try to get unique values - will fail if unhashable
            num_unique = df[col].nunique()
            num_total = len(df[col])
            if num_total == 0:
                continue
            
            # If less than 50% unique values, convert to category
            if num_unique / num_total < 0.5:
                df[col] = df[col].astype('category')
        except (TypeError, AttributeError):
            # Column contains unhashable types (dicts, lists), skip optimization
            print(f"  Skipping column '{col}' (contains complex data types)")
            continue
    
    final_memory = df.memory_usage(deep=True).sum() / 1024**2
    reduction = 0.0 if initial_memory == 0 else (1 - final_memory / initial_memory) * 100
    
    print(f"Memory usage reduced from {initial_memory:.2f} MB to {final_memory:.2f} MB ({reduction:.1f}% reduction)")
    
    return df

