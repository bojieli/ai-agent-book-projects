"""Helpers for running manual smoke scripts from tests/manual."""

from pathlib import Path
import sys


def add_project_root() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return project_root
