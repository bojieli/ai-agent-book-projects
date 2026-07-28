"""Regression: documented interval='M' must work on modern pandas."""
import pandas as pd
from data_loader import get_time_slices


def test_monthly_interval_alias():
    df = pd.DataFrame({"tstamp": [1_700_000_000, 1_710_000_000]})
    slices = get_time_slices(df, interval="M")
    assert len(slices) >= 1
