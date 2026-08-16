"""Static regression check: no bare ``except:`` in book-owned Python code.

Closes the class where bare ``except:`` clauses swallowed
``KeyboardInterrupt`` / ``SystemExit`` and masked real errors. Vendored
third-party trees and test fixtures are excluded; the invariant applies
only to code the book authors own.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Directories that contain vendored third-party code or test scaffolding
# where the book's coding standards do not apply.
_EXCLUDED_DIRS = {
    "chapter9/gaia-experience/AWorld",
    "chapter9/browser-use-rpa",
    ".venv",
    "__pycache__",
    ".git",
    "node_modules",
}


def _is_excluded(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT).as_posix()
    return any(rel.startswith(ex) or rel.startswith(ex + "/") for ex in _EXCLUDED_DIRS)


def _find_bare_excepts(path: Path) -> list[int]:
    """Return line numbers of bare ``except:`` handlers in *path*."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return []

    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            lines.append(node.lineno)
    return lines


def test_no_bare_except_in_book_owned_code():
    """No book-owned Python file may contain a bare ``except:`` clause.

    A bare except catches ``BaseException``, swallowing
    ``KeyboardInterrupt`` and ``SystemExit`` and masking real defects.
    Use a specific exception type (or ``except Exception:`` for
    last-resort cleanup handlers) instead.
    """
    offenders: list[str] = []
    for py in REPO_ROOT.rglob("*.py"):
        if _is_excluded(py):
            continue
        bare_lines = _find_bare_excepts(py)
        for lineno in bare_lines:
            offenders.append(f"{py.relative_to(REPO_ROOT)}:{lineno}")
    assert not offenders, (
        "Bare 'except:' clauses found in book-owned code (use specific "
        f"exception types):\n  {chr(10).join(offenders)}"
    )
