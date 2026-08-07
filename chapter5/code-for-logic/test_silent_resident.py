import sys
from pathlib import Path

# Ensure csp_solver module can be resolved regardless of working directory
sys.path.insert(0, str(Path(__file__).parent))

from csp_solver import solve, solve_labeled


def test_csp_solver_handles_silent_resident():
    """Verify solve handles residents in names that make no statements.

    Contract: In Knights and Knaves puzzles, residents listed in `names` may be
    silent (spoken about by others without making statements themselves).
    `solve` must skip adding speaker-statement constraints for silent residents
    rather than raising KeyError.
    """
    names = ["A", "B"]
    # A speaks about B ("B is a knave"), but B makes no statement.
    structs = {"A": ["is", "B", "knave"]}

    solutions = solve(names, structs)
    assert len(solutions) == 2
    # If A is knight (True), B must be knave (False); if A is knave (False), B must be knight (True).
    assert {"A": True, "B": False} in solutions
    assert {"A": False, "B": True} in solutions

    labeled = solve_labeled(names, structs)
    assert {"A": "knight", "B": "knave"} in labeled
    assert {"A": "knave", "B": "knight"} in labeled
