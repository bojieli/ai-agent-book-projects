"""
Benchmark script to compare performance of different Elo implementations
"""
import time
import pandas as pd
import numpy as np
from elo_rating import EloRatingSystem
from optimized_elo import build_leaderboard_optimized
from data_loader import load_arena_data, filter_data


def benchmark_basic_elo(df: pd.DataFrame) -> float:
    """Benchmark the basic Elo implementation."""
    print("\n" + "="*80)
    print("Benchmarking Basic Elo Implementation (Python dict)")
    print("="*80)
    
    start_time = time.time()
    
    elo = EloRatingSystem(initial_rating=1000.0, k_factor=32.0)
    
    for _, row in df.iterrows():
        elo.update_ratings(row['model_a'], row['model_b'], row['winner'])
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    leaderboard = elo.get_leaderboard()
    
    print(f"✓ Processed {len(df)} matches in {elapsed:.2f} seconds")
    print(f"  Speed: {len(df)/elapsed:.0f} matches/second")
    print(f"  Top 3 models: {[m[0] for m in leaderboard[:3]]}")
    
    return elapsed


def benchmark_optimized_elo(df: pd.DataFrame) -> float:
    """Benchmark the NumPy + Numba optimized implementation."""
    print("\n" + "="*80)
    print("Benchmarking Optimized Elo Implementation (NumPy + Numba JIT)")
    print("="*80)
    
    start_time = time.time()
    
    elo = build_leaderboard_optimized(
        df,
        initial_rating=1000.0,
        k_factor=32.0,
        show_progress=False
    )
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    leaderboard = elo.get_leaderboard()
    
    print(f"✓ Processed {len(df)} matches in {elapsed:.2f} seconds")
    print(f"  Speed: {len(df)/elapsed:.0f} matches/second")
    print(f"  Top 3 models: {[m[0] for m in leaderboard[:3]]}")
    
    return elapsed


def main():
    """Run benchmark comparison."""
    print("="*80)
    print("ELO RATING COMPUTATION BENCHMARK")
    print("="*80)
    print("\nThis benchmark compares the performance of different Elo implementations")
    print("on Chatbot Arena voting data.\n")
    
    # Load data
    print("Loading data...")
    try:
        df = load_arena_data("arena_data.json")
    except FileNotFoundError:
        print("Error: arena_data.json not found. Please run main.py first to download the data.")
        return
    
    # Filter for blind votes
    print("Filtering data...")
    df_filtered = filter_data(df, anony_only=True, min_turn=1)
    
    # Use a subset for quick benchmarking (can change to full dataset)
    sample_size = 50000
    if len(df_filtered) > sample_size:
        print(f"\nUsing a sample of {sample_size} matches for benchmarking")
        print("(To benchmark on full dataset, set sample_size = len(df_filtered))")
        df_sample = df_filtered.head(sample_size).copy()
    else:
        df_sample = df_filtered.copy()
    
    print(f"\nBenchmark dataset: {len(df_sample)} matches")
    print(f"Unique models: {len(set(df_sample['model_a'].unique()) | set(df_sample['model_b'].unique()))}")
    
    # Warm up Numba JIT (first run compiles the functions)
    print("\n" + "-"*80)
    print("Warming up Numba JIT compiler (first run)...")
    print("-"*80)
    df_tiny = df_sample.head(1000)
    build_leaderboard_optimized(df_tiny, show_progress=False)
    print("✓ JIT compilation complete")
    
    # Run benchmarks
    time_basic = benchmark_basic_elo(df_sample)
    time_optimized = benchmark_optimized_elo(df_sample)
    
    # Results summary
    print("\n" + "="*80)
    print("BENCHMARK RESULTS")
    print("="*80)
    
    speedup = time_basic / time_optimized if time_optimized > 0 else 0
    
    print(f"\nBasic Implementation:     {time_basic:8.2f} seconds")
    print(f"Optimized Implementation: {time_optimized:8.2f} seconds")
    print(f"\nSpeedup: {speedup:.1f}x faster")
    pct_reduction = (1 - time_optimized / time_basic) * 100 if time_basic > 0 else 0.0
    print(f"Time saved: {time_basic - time_optimized:.2f} seconds ({pct_reduction:.1f}% reduction)")
    
    # Extrapolate to full dataset
    if len(df_sample) > 0 and len(df_sample) < len(df_filtered):
        full_time_basic = time_basic * (len(df_filtered) / len(df_sample))
        full_time_optimized = time_optimized * (len(df_filtered) / len(df_sample))
        
        print(f"\nExtrapolated times for full dataset ({len(df_filtered)} matches):")
        print(f"  Basic:     ~{full_time_basic/60:.1f} minutes")
        print(f"  Optimized: ~{full_time_optimized/60:.1f} minutes")
        print(f"  Time saved: ~{(full_time_basic - full_time_optimized)/60:.1f} minutes")
    
    print("\n" + "="*80)
    print("\nOptimization Techniques Applied:")
    print("  • NumPy arrays instead of Python dicts (O(1) integer indexing)")
    print("  • Numba JIT compilation (compiles hot loops to machine code)")
    print("  • Pre-allocated arrays (no dynamic memory allocation)")
    print("  • Integer model indices (no string lookups)")
    print("  • Vectorized operations where possible")
    print("\nFor the full optimized pipeline with parallel processing, run main_optimized.py")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

