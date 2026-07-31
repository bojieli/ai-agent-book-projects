"""Regenerate this edition's Chapter 2 figures from the Chinese golden layouts.

The shared synchronizer owns the current Chapter 2 figure numbering, localized
labels, and authoritative context-compression measurements.
"""
import subprocess
import sys
from pathlib import Path


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, root / "scripts" / "sync_chapter2_figures.py", "--locale", "id"],
        check=True,
    )
