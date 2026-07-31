"""Regression: filter_data_parallel must tolerate n_jobs > len(df)."""
from unittest.mock import MagicMock, patch

import pandas as pd

from parallel_processing import filter_data_parallel


def test_n_jobs_larger_than_rows():
    df = pd.DataFrame({"anony": [True, False, True], "turn": [1, 2, 1]})

    def map_inline(fn, chunks):
        return [fn(c) for c in chunks]

    pool = MagicMock()
    pool.__enter__.return_value.map.side_effect = map_inline
    pool.__exit__.return_value = False

    with patch("parallel_processing.Pool", return_value=pool):
        out = filter_data_parallel(df, {"anony_only": True}, n_jobs=8)
    assert len(out) == 2
