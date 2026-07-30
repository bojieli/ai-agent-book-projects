"""Helpers for direct execution of tests moved under tests/."""

from pathlib import Path
import sys


def bootstrap_experiment_root() -> None:
    experiment_root = Path(__file__).resolve().parents[1]
    if str(experiment_root) not in sys.path:
        sys.path.insert(0, str(experiment_root))
