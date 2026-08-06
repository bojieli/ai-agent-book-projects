#!/usr/bin/env python3
"""Entry point for the shared Experiment 3-9/3-11 controlled campaign."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from memory_rag_campaign import main


if __name__ == "__main__":
    raise SystemExit(main())
