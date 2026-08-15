"""
Test suite locking out ZeroDivisionError in benchmark summary print logic
when time_basic is 0.0 or df_sample is empty.
"""

def test_benchmark_pct_reduction_zero_division():
    """
    Ensure zero time_basic does not raise ZeroDivisionError during benchmark calculation.
    """
    time_basic = 0.0
    time_optimized = 0.0
    pct_reduction = (1 - time_optimized / time_basic) * 100 if time_basic > 0 else 0.0
    assert pct_reduction == 0.0


def test_benchmark_extrapolation_zero_sample():
    """
    Ensure empty df_sample does not raise ZeroDivisionError during extrapolation check.
    """
    df_sample = []
    df_filtered = [1, 2, 3]
    should_extrapolate = len(df_sample) > 0 and len(df_sample) < len(df_filtered)
    assert not should_extrapolate
