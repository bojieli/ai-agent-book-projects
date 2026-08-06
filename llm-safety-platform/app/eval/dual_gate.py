"""Alias module — prefer ``python -m app.eval.dual_gates``.

Re-exports ``run_dual_gates`` as ``run_dual_gate`` for corpus_gates / CLI compatibility.
"""

from __future__ import annotations

from app.eval.dual_gates import run_dual_gates as run_dual_gate
from app.eval.dual_gates import main

__all__ = ["run_dual_gate", "main"]

if __name__ == "__main__":
    raise SystemExit(main())
