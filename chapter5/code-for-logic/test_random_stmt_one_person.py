"""Regression: one-person puzzles must not IndexError in _random_stmt."""
import random
import sys
import types

sys.modules.setdefault("constraint", types.ModuleType("constraint"))
sys.modules["constraint"].Problem = object
cs = types.ModuleType("csp_solver")
cs.render_nl = lambda *a, **k: ""
cs.solve = lambda *a, **k: [{}]
cs.solve_labeled = lambda *a, **k: {}
sys.modules["csp_solver"] = cs

from build_puzzles import _random_stmt  # noqa: E402


def test_random_stmt_one_person_returns_count():
    rng = random.Random(0)
    for _ in range(20):
        stmt = _random_stmt("A", ["A"], rng)
        assert stmt[0] == "count"
        assert stmt[1] in ("knight", "knave")
