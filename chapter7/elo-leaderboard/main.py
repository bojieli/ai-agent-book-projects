"""
Main script for Model Leaderboard Calculation
Experiment 6-6: Building Model Leaderboard from Pairwise Comparison Data

Supports two methods (following official Chatbot Arena):
1. Online Elo (K=4) - Simple but order-dependent
2. Bradley-Terry MLE - Official leaderboard method (more stable)
"""
import os
import sys

import pandas as pd
from bradley_terry import (
    compute_bradley_terry_leaderboard,
    predict_win_rate,
)
from data_loader import download_arena_data, filter_data, load_arena_data
from elo_rating import EloRatingSystem
from parallel_processing import optimize_dataframe
from visualization import plot_leaderboard, plot_rating_distribution, plot_win_rate_matrix


def compute_online_elo_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute leaderboard using online Elo updates (K=4, official value).
    
    This method updates ratings sequentially as matches are processed.
    It's simpler but can be unstable and order-dependent.
    
    Args:
        df: DataFrame with columns 'model_a', 'model_b', 'winner'
        
    Returns:
        DataFrame with model ratings
    """
    from tqdm import tqdm
    
    print("Computing online Elo ratings (K=4)...")
    
    elo = EloRatingSystem(initial_rating=1000.0, k_factor=4.0)
    
    # Process matches sequentially
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing matches"):
        elo.update_ratings(row['model_a'], row['model_b'], row['winner'])
    
    # Get leaderboard
    leaderboard = elo.get_leaderboard()
    
    # Convert to DataFrame
    result = pd.DataFrame(leaderboard, columns=['model', 'rating', 'matches', 'wins'])
    return result


def main(method: str = 'bradley-terry'):
    """
    Run model leaderboard calculation.
    
    Args:
        method: 'bradley-terry' (default, official) or 'online-elo' (simple)
    """
    
    print("="*80)
    print("Experiment 6-6: Building Model Leaderboard from Pairwise Comparisons")
    if method == 'bradley-terry':
        print("Method: Bradley-Terry Model with MLE (Official Chatbot Arena)")
    else:
        print("Method: Online Elo Updates (K=4)")
    print("="*80)
    print()
    
    # Step 1: Download and load data
    print("Step 1: Loading Chatbot Arena voting data...")
    print("-" * 80)
    
    data_file = "arena_data.json"
    
    try:
        # Download data if not exists
        if not os.path.exists(data_file):
            data_file = download_arena_data(data_file)
        
        # Load data
        df = load_arena_data(data_file)
        
        # Optimize memory usage
        df = optimize_dataframe(df)
        
    except Exception as e:  # noqa: BLE001 - surface loader/provider diagnostics to CLI users
        print(f"Error loading data: {e}")
        print("\nNote: If the data download fails, you can manually download the file from:")
        print("https://storage.googleapis.com/arena_external_data/public/clean_battle_20240814_public.json")
        print("and save it as 'arena_data.json' in the current directory.")
        return
    
    print()
    
    # Step 2: Filter data (official Chatbot Arena method)
    print("Step 2: Filtering data (following official Arena method)...")
    print("-" * 80)
    
    df_filtered = filter_data(
        df,
        anony_only=True,  # Only anonymous/blind votes
        use_dedup=True,   # Apply deduplication (removes top 0.1% redundant prompts)
        min_turn=1
    )
    
    print()
    
    # Step 3: Compute ratings using selected method
    print(f"Step 3: Computing ratings using {method} method...")
    print("-" * 80)
    
    if method == 'bradley-terry':
        print("Note: Bradley-Terry model uses sklearn LogisticRegression for MLE.")
        print("This is the official Chatbot Arena method - more stable than online Elo.")
        print()
        
        # Compute ratings with bootstrap for confidence intervals
        leaderboard_df = compute_bradley_terry_leaderboard(df_filtered, bootstrap_rounds=100)
        
        print("\nTop 20 models by Bradley-Terry rating:")
        print("-" * 80)
        print(f"{'Rank':<6}{'Model':<35}{'Rating':<10}{'95% CI':<20}")
        print("-" * 80)
        for idx, row in leaderboard_df.head(20).iterrows():
            if 'lower_ci' in row and 'upper_ci' in row:
                ci_str = f"[{row['lower_ci']:.1f}, {row['upper_ci']:.1f}]"
            else:
                ci_str = "N/A"
            print(f"{idx+1:<6}{row['model']:<35}{row['rating']:7.1f}   {ci_str:<20}")
    
    else:  # online-elo
        print("Note: Online Elo uses K=4 (official value) for stable ratings.")
        print("Processes matches sequentially - simpler but can be order-dependent.")
        print()
        
        # Compute online Elo ratings
        leaderboard_df = compute_online_elo_leaderboard(df_filtered)
        
        print("\nTop 20 models by Online Elo rating:")
        print("-" * 80)
        print(f"{'Rank':<6}{'Model':<35}{'Rating':<10}{'Matches':<10}{'Win Rate':<10}")
        print("-" * 80)
        for idx, row in leaderboard_df.head(20).iterrows():
            win_rate = row['wins'] / row['matches'] * 100 if row['matches'] > 0 else 0
            print(f"{idx+1:<6}{row['model']:<35}{row['rating']:7.1f}   {row['matches']:<10}{win_rate:6.1f}%")
    
    print()
    
    # Step 4: Predict win rates using Bradley-Terry model
    print("Step 4: Calculating predicted win rates...")
    print("-" * 80)
    
    # Get ratings as dictionary
    ratings_dict = dict(zip(leaderboard_df['model'], leaderboard_df['rating']))
    
    # Predict win rates
    predicted_win_rates = predict_win_rate(ratings_dict)
    
    print(f"Calculated predicted win rates for {len(ratings_dict)} models")
    print()
    
    # Step 5: Create visualizations
    print("Step 5: Creating visualizations...")
    print("-" * 80)
    
    # Convert leaderboard_df to format expected by visualization functions
    leaderboard_tuples = [(row['model'], row['rating'], 0, 0) for _, row in leaderboard_df.iterrows()]
    
    plot_leaderboard(leaderboard_tuples, top_n=20, save_path="leaderboard.png")
    plot_rating_distribution(leaderboard_tuples, save_path="rating_distribution.png")
    
    # Plot win rate matrix
    top_30_models = leaderboard_df.head(30)['model'].tolist()
    plot_win_rate_matrix(predicted_win_rates.loc[top_30_models, top_30_models], 
                         top_n=30, save_path="win_rate_matrix.png")
    
    print()
    
    # Summary
    print("="*80)
    print("Analysis complete!")
    print("="*80)
    print("\nGenerated files:")
    print("  - leaderboard.png                    : Top 20 models by Bradley-Terry rating")
    print("  - rating_distribution.png            : Distribution of ratings")
    print("  - win_rate_matrix.png                : Predicted win rate matrix (top 30 models)")
    print()
    
    # Method summary
    print("Method:")
    print("-" * 80)
    if method == 'bradley-terry':
        print("  ✓ Bradley-Terry model with Maximum Likelihood Estimation")
        print("  ✓ sklearn LogisticRegression for stable rating computation")
        print("  ✓ Bootstrap confidence intervals (100 samples)")
    else:
        print("  ✓ Online Elo with K=4 (official value)")
        print("  ✓ Sequential match processing")
        print("  ✓ Simple but order-dependent")
    print("  ✓ Deduplication filter (removes top 0.1% redundant prompts)")
    print("  ✓ Anonymous votes only (blind evaluation)")
    print()
    
    # Key insights
    print("Key Insights:")
    print("-" * 80)
    print(f"  • Total models analyzed: {len(leaderboard_df)}")
    print(f"  • Total battles: {len(df_filtered):,}")
    print(f"  • Rating range: {leaderboard_df['rating'].min():.1f} - {leaderboard_df['rating'].max():.1f}")
    print(f"  • Top model: {leaderboard_df.iloc[0]['model']} ({leaderboard_df.iloc[0]['rating']:.1f})")
    
    if 'lower_ci' in leaderboard_df.columns:
        avg_ci_width = (leaderboard_df['upper_ci'] - leaderboard_df['lower_ci']).mean()
        print(f"  • Average confidence interval width: {avg_ci_width:.1f} rating points")
    
    print()
    print("This implementation matches the official Chatbot Arena leaderboard calculation!")
    print("Source: https://colab.research.google.com/drive/1KdwokPjirkTmpO_P1WByFNFiqxWQquwH")
    print()


if __name__ == "__main__":
    # Allow method selection via command line argument
    import sys
    
    method = 'bradley-terry'  # Default to official method
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['bradley-terry', 'bt', 'mle']:
            method = 'bradley-terry'
        elif sys.argv[1] in ['online-elo', 'elo', 'online']:
            method = 'online-elo'
        else:
            print(f"Unknown method: {sys.argv[1]}")
            print("Usage: python main.py [bradley-terry|online-elo]")
            print("  bradley-terry (default): Official Arena method, more stable")
            print("  online-elo: Simple Elo updates with K=4")
            sys.exit(1)
    
    main(method)
