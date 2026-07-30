"""
Regression: get_time_slices must not IndexError when the tstamp span is
shorter than the requested interval (default weekly).

Chatbot Arena samples, same-second dumps, and single-row demos all produce an
empty pd.date_range for freq='W'; the old code then crashed on date_ranges[-1].
"""
import pandas as pd

from data_loader import get_time_slices


def test_identical_timestamps_return_one_slice():
    """Two battles at the same unix second (weekly interval) -> one slice."""
    ts = 1_700_000_000
    df = pd.DataFrame({
        "tstamp": [ts, ts],
        "model_a": ["a", "c"],
        "model_b": ["b", "d"],
        "winner": ["model_a", "model_b"],
    })
    slices = get_time_slices(df, interval="W")
    assert len(slices) == 1
    end_date, slice_df = slices[0]
    assert len(slice_df) == 2
    assert end_date == pd.to_datetime(ts, unit="s")


def test_empty_dataframe_returns_empty_list():
    """Empty input returns [] instead of NaT ValueError."""
    df = pd.DataFrame({"tstamp": pd.Series(dtype="float64")})
    assert get_time_slices(df, interval="W") == []


def test_multi_week_span_still_produces_buckets():
    """A span covering multiple weeks still yields intermediate buckets."""
    # ~3 weeks apart
    df = pd.DataFrame({
        "tstamp": [1_700_000_000, 1_700_000_000 + 21 * 86400],
        "model_a": ["a", "c"],
        "model_b": ["b", "d"],
        "winner": ["model_a", "model_b"],
    })
    slices = get_time_slices(df, interval="W")
    assert len(slices) >= 2
    assert all(len(s[1]) > 0 for s in slices)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
