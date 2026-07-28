"""
Data loading and preprocessing for Chatbot Arena voting data
"""
import pandas as pd
import requests
import os
from typing import Optional
from tqdm import tqdm


def download_arena_data(output_path: str = "arena_data.json", force_download: bool = False) -> str:
    """
    Download Chatbot Arena voting data via HTTPS.
    
    Args:
        output_path: Path to save downloaded file
        force_download: If True, re-download even if file exists
        
    Returns:
        Path to downloaded file
    """
    if os.path.exists(output_path) and not force_download:
        print(f"Data file already exists at {output_path}")
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"File size: {file_size:.2f} MB")
        return output_path
    
    print("Downloading Chatbot Arena voting data...")
    url = "https://storage.googleapis.com/arena_external_data/public/clean_battle_20240814_public.json"
    
    try:
        # Stream download with progress bar
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get total file size
        total_size = int(response.headers.get('content-length', 0))
        
        # Download with progress bar
        with open(output_path, 'wb') as f, tqdm(
            desc=output_path,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\nDownloaded data to {output_path} ({file_size:.2f} MB)")
        return output_path
        
    except Exception as e:
        print(f"Error downloading data: {e}")
        print("Please ensure you have internet connection and the URL is accessible.")
        raise


def load_arena_data(filepath: str) -> pd.DataFrame:
    """
    Load and preprocess Chatbot Arena voting data.
    
    Expected columns:
    - model_a: Identifier for first model
    - model_b: Identifier for second model
    - winner: Which model won ('model_a', 'model_b', or 'tie')
    - tstamp: Unix timestamp of the vote
    - judge: User who made the vote
    - turn: Conversation turn
    - anony: Whether vote was anonymous (blind)
    - language: Language of the conversation
    
    Args:
        filepath: Path to data file
        
    Returns:
        Preprocessed DataFrame sorted by timestamp
    """
    print(f"Loading data from {filepath}...")
    print("Note: This is a large file (~2GB), loading may take 1-2 minutes...")
    
    # Try different file formats
    if filepath.endswith('.json'):
        df = pd.read_json(filepath)
    elif filepath.endswith('.jsonl'):
        df = pd.read_json(filepath, lines=True)
    elif filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        # Try JSON by default
        try:
            df = pd.read_json(filepath)
        except:
            df = pd.read_json(filepath, lines=True)
    
    print(f"Loaded {len(df)} records")
    print(f"Columns: {df.columns.tolist()}")
    
    # Sort by timestamp
    if 'tstamp' in df.columns:
        df = df.sort_values('tstamp', ascending=True).reset_index(drop=True)
        print(f"Data spans from {pd.to_datetime(df['tstamp'].min(), unit='s')} to {pd.to_datetime(df['tstamp'].max(), unit='s')}")
    
    # Basic statistics
    if 'winner' in df.columns:
        print(f"\nOutcome distribution:")
        print(df['winner'].value_counts())
    
    if 'model_a' in df.columns and 'model_b' in df.columns:
        all_models = set(df['model_a'].unique()) | set(df['model_b'].unique())
        print(f"\nTotal unique models: {len(all_models)}")
        print(f"Top 10 models by appearance:")
        model_counts = pd.concat([df['model_a'], df['model_b']]).value_counts().head(10)
        print(model_counts)
    
    return df


def filter_data(df: pd.DataFrame, 
                min_date: Optional[str] = None,
                max_date: Optional[str] = None,
                anony_only: bool = True,
                language: Optional[str] = None,
                min_turn: int = 1,
                use_dedup: bool = True) -> pd.DataFrame:
    """
    Filter voting data based on various criteria (following official Chatbot Arena method).
    
    Args:
        df: Input DataFrame
        min_date: Minimum date (YYYY-MM-DD format)
        max_date: Maximum date (YYYY-MM-DD format)
        anony_only: If True, only include anonymous (blind) votes
        language: If specified, filter by language
        min_turn: Minimum conversation turn
        use_dedup: If True, apply deduplication filter (official Arena method)
        
    Returns:
        Filtered DataFrame
    """
    filtered = df.copy()
    
    print(f"Before filtering: {len(filtered)} records")
    
    # Filter by anonymous votes only (official method)
    if anony_only and 'anony' in filtered.columns:
        filtered = filtered[filtered['anony'] == True]
        print(f"  After anony filter: {len(filtered)} records")
    
    # Apply deduplication (official method removes top 0.1% redundant prompts)
    if use_dedup and 'dedup_tag' in filtered.columns:
        try:
            filtered = filtered[filtered["dedup_tag"].apply(lambda x: x.get("sampled", False) if isinstance(x, dict) else False)]
            print(f"  After dedup filter: {len(filtered)} records")
        except Exception as e:
            print(f"  Warning: Could not apply dedup filter: {e}")
    
    # Filter by date
    if 'tstamp' in filtered.columns:
        if min_date:
            min_timestamp = pd.to_datetime(min_date).timestamp()
            filtered = filtered[filtered['tstamp'] >= min_timestamp]
        if max_date:
            max_timestamp = pd.to_datetime(max_date).timestamp()
            filtered = filtered[filtered['tstamp'] <= max_timestamp]
    
    # Filter by language
    if language and 'language' in filtered.columns:
        filtered = filtered[filtered['language'] == language]
    
    # Filter by turn
    if 'turn' in filtered.columns:
        filtered = filtered[filtered['turn'] >= min_turn]
    
    pct = (len(filtered) / len(df) * 100) if len(df) else 0.0
    print(f"After filtering: {len(filtered)} records ({pct:.1f}% of original)")
    return filtered.reset_index(drop=True)


def get_time_slices(df: pd.DataFrame, interval: str = 'W') -> list:
    """
    Split data into time slices for historical analysis.
    
    Args:
        df: Input DataFrame with 'tstamp' column
        interval: Pandas frequency string ('D' for daily, 'W' for weekly, 'M' for monthly)
        
    Returns:
        List of (end_date, dataframe_slice) tuples
    """
    if 'tstamp' not in df.columns:
        raise ValueError("DataFrame must have 'tstamp' column")

    if len(df) == 0:
        print(f"Created 0 time slices with interval '{interval}'")
        return []
    
    df['datetime'] = pd.to_datetime(df['tstamp'], unit='s')
    min_date = df['datetime'].min()
    max_date = df['datetime'].max()
    
    # Pandas 2.2+ removed 'M' (month-end); keep the documented monthly alias.
    freq = "ME" if interval == "M" else interval

    # Generate date ranges
    date_ranges = pd.date_range(start=min_date, end=max_date, freq=freq)
    
    slices = []
    for end_date in date_ranges:
        slice_df = df[df['datetime'] <= end_date].copy()
        if len(slice_df) > 0:
            slices.append((end_date, slice_df))
    
    # Empty date_ranges when span < interval; also cover trailing gap to max_date.
    if len(date_ranges) == 0 or date_ranges[-1] < max_date:
        slices.append((max_date, df.copy()))
    
    print(f"Created {len(slices)} time slices with interval '{interval}'")
    return slices

