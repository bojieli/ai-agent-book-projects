"""
Bradley-Terry Model Implementation
Official Chatbot Arena leaderboard calculation method
"""
import numpy as np
import pandas as pd
import math
from typing import Dict
from sklearn.linear_model import LogisticRegression


def compute_mle_elo(df: pd.DataFrame, 
                    SCALE: int = 400, 
                    BASE: int = 10, 
                    INIT_RATING: int = 1000,
                    calibration_model: str = None,
                    calibration_rating: int = None) -> pd.Series:
    """
    Compute Elo ratings using Bradley-Terry model with Maximum Likelihood Estimation.
    
    This is the official method used by Chatbot Arena for their leaderboard.
    It uses sklearn's LogisticRegression to fit a Bradley-Terry model.
    
    Args:
        df: DataFrame with columns 'model_a', 'model_b', 'winner'
        SCALE: Elo scale parameter (default 400)
        BASE: Base for logistic function (default 10)
        INIT_RATING: Initial rating (default 1000)
        calibration_model: Model name to calibrate ratings to
        calibration_rating: Target rating for calibration model
        
    Returns:
        Series of Elo ratings indexed by model name
    """
    # Empty battle frame (e.g. --num-battles 0 or fully filtered input) is valid.
    if df is None or len(df) == 0:
        return pd.Series(dtype=float)
    # Create pivot tables for wins
    ptbl_a_win = pd.pivot_table(
        df[df["winner"] == "model_a"],
        index="model_a",
        columns="model_b",
        aggfunc="size",
        fill_value=0,
        observed=False
    )
    
    # Handle ties (including "tie (bothbad)"). Symmetrize only after aligning to
    # the full model square; (pivot + pivot.T) on a one-sided A×B pivot zeroes
    # every cell via pandas index/column alignment.
    if sum(df["winner"].isin(["tie", "tie (bothbad)"])) == 0:
        ptbl_tie = pd.DataFrame(0, index=ptbl_a_win.index, columns=ptbl_a_win.columns)
    else:
        ptbl_tie = pd.pivot_table(
            df[df["winner"].isin(["tie", "tie (bothbad)"])],
            index="model_a",
            columns="model_b",
            aggfunc="size",
            fill_value=0,
            observed=False
        )
    
    ptbl_b_win = pd.pivot_table(
        df[df["winner"] == "model_b"],
        index="model_a",
        columns="model_b",
        aggfunc="size",
        fill_value=0,
        observed=False
    )
    
    # Align pivots on the full model universe (small samples otherwise leave NaNs).
    models = sorted(set(df["model_a"]) | set(df["model_b"]))
    ptbl_a_win = ptbl_a_win.reindex(index=models, columns=models, fill_value=0)
    ptbl_b_win = ptbl_b_win.reindex(index=models, columns=models, fill_value=0)
    ptbl_tie = ptbl_tie.reindex(index=models, columns=models, fill_value=0)
    ptbl_tie = ptbl_tie + ptbl_tie.T

    # Compute win matrix (A wins * 2 + B wins * 2 + ties)
    ptbl_win = (ptbl_a_win * 2 + ptbl_b_win.T * 2 + ptbl_tie).fillna(0)
    
    # Map models to indices
    models = pd.Series(np.arange(len(ptbl_win.index)), index=ptbl_win.index)
    
    p = len(models)
    X = np.zeros([p * (p - 1) * 2, p])
    Y = np.zeros(p * (p - 1) * 2)
    
    cur_row = 0
    sample_weights = []
    
    for m_a in ptbl_win.index:
        for m_b in ptbl_win.columns:
            if m_a == m_b:
                continue
            # Skip if nan
            if math.isnan(ptbl_win.loc[m_a, m_b]) or math.isnan(ptbl_win.loc[m_b, m_a]):
                continue
            
            X[cur_row, models[m_a]] = +math.log(BASE)
            X[cur_row, models[m_b]] = -math.log(BASE)
            Y[cur_row] = 1.0
            sample_weights.append(ptbl_win.loc[m_a, m_b])
            
            X[cur_row + 1, models[m_a]] = math.log(BASE)
            X[cur_row + 1, models[m_b]] = -math.log(BASE)
            Y[cur_row + 1] = 0.0
            sample_weights.append(ptbl_win.loc[m_b, m_a])
            cur_row += 2
    
    X = X[:cur_row]
    Y = Y[:cur_row]
    
    # Fit logistic regression
    lr = LogisticRegression(fit_intercept=False, penalty=None, tol=1e-6)
    lr.fit(X, Y, sample_weight=sample_weights)
    
    # Convert to Elo scores
    elo_scores = SCALE * lr.coef_[0] + INIT_RATING
    
    # Calibrate to reference model if provided
    if calibration_model and calibration_model in models.index:
        elo_scores += calibration_rating - elo_scores[models[calibration_model]]
    
    return pd.Series(elo_scores, index=models.index).sort_values(ascending=False)


def predict_win_rate(elo_ratings: Dict[str, float], 
                     SCALE: int = 400, 
                     BASE: int = 10) -> pd.DataFrame:
    """
    Predict win rates between all model pairs using Elo ratings.
    
    Args:
        elo_ratings: Dictionary of model names to Elo ratings
        SCALE: Elo scale parameter
        BASE: Base for logistic function
        
    Returns:
        DataFrame with predicted win rates (row vs column)
    """
    from collections import defaultdict
    
    names = sorted(list(elo_ratings.keys()))
    wins = defaultdict(lambda: defaultdict(lambda: 0))
    
    for a in names:
        for b in names:
            ea = 1 / (1 + BASE ** ((elo_ratings[b] - elo_ratings[a]) / SCALE))
            wins[a][b] = ea
            wins[b][a] = 1 - ea
    
    data = {
        # np.nan, not np.NAN: the upper-case aliases were removed in NumPy 2.0
        # and requirements.txt allows numpy>=1.24 (i.e. 2.x).
        a: [wins[a][b] if a != b else np.nan for b in names]
        for a in names
    }
    
    df = pd.DataFrame(data, index=names)
    df.index.name = "model_a"
    df.columns.name = "model_b"
    return df.T


def get_bootstrap_result(battles: pd.DataFrame, 
                        func_compute_elo, 
                        num_round: int = 100) -> pd.DataFrame:
    """
    Compute bootstrap confidence intervals for Elo ratings.
    
    Args:
        battles: DataFrame with battle data
        func_compute_elo: Function to compute Elo ratings
        num_round: Number of bootstrap rounds
        
    Returns:
        DataFrame with ratings from each bootstrap round
    """
    from tqdm import tqdm
    
    rows = []
    for i in tqdm(range(num_round), desc="Bootstrap sampling"):
        rows.append(func_compute_elo(battles.sample(frac=1.0, replace=True)))
    df = pd.DataFrame(rows)
    return df[df.median().sort_values(ascending=False).index]


def compute_bradley_terry_leaderboard(df: pd.DataFrame,
                                      bootstrap_rounds: int = 0) -> pd.DataFrame:
    """
    Compute leaderboard using Bradley-Terry model (official Chatbot Arena method).
    
    Args:
        df: DataFrame with columns 'model_a', 'model_b', 'winner'
        bootstrap_rounds: Number of bootstrap rounds for confidence intervals (0 = no bootstrap)
        
    Returns:
        DataFrame with model ratings (and confidence intervals if bootstrap > 0)
    """
    print(f"Computing Bradley-Terry model ratings...")
    
    # Compute MLE Elo ratings
    elo_ratings = compute_mle_elo(df)
    
    if bootstrap_rounds > 0:
        print(f"Computing {bootstrap_rounds} bootstrap samples for confidence intervals...")
        bootstrap_df = get_bootstrap_result(df, compute_mle_elo, bootstrap_rounds)
        
        # Compute confidence intervals
        result = pd.DataFrame({
            'rating': bootstrap_df.quantile(0.5),
            'lower_ci': bootstrap_df.quantile(0.025),
            'upper_ci': bootstrap_df.quantile(0.975)
        }).sort_values('rating', ascending=False)
    else:
        result = pd.DataFrame({
            'rating': elo_ratings
        }).sort_values('rating', ascending=False)
    
    result.index.name = 'model'
    return result.reset_index()

