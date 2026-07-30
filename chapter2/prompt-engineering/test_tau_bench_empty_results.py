"""
display_metrics must handle empty results list without raising ZeroDivisionError.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tau_bench"))

from run import display_metrics


def test_display_metrics_empty_results():
    """Ensure display_metrics gracefully handles empty results list."""
    display_metrics([])
