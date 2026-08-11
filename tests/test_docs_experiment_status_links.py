"""Regression tests for docs/EXPERIMENT_STATUS.md ledger links.

Closes the class where ledger bullet-list entries used literal ``+- `` prefixes
that render as text instead of Markdown list items, and where linked ledger
files could drift out of existence.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STATUS_FILE = REPO_ROOT / "docs" / "EXPERIMENT_STATUS.md"

_BULLET_RE = re.compile(r"^\+- \[", re.MULTILINE)
_LEDGER_LINK_RE = re.compile(r"^- \[.+?\]\((\.\./.+?\.md)\)$", re.MULTILINE)


def test_no_literal_plus_prefix_bullets():
    """No ledger bullet may start with ``+- `` — it renders as text, not a list item."""
    assert not _BULLET_RE.search(STATUS_FILE.read_text(encoding="utf-8")), (
        "Found literal '+- ' bullet prefix in EXPERIMENT_STATUS.md"
    )


def test_ledger_links_resolve_to_existing_files():
    """Every ledger link in the detailed-ledgers section must point to a real file."""
    missing: list[str] = []
    for match in _LEDGER_LINK_RE.finditer(STATUS_FILE.read_text(encoding="utf-8")):
        target = (STATUS_FILE.parent / match.group(1)).resolve()
        if not target.exists():
            missing.append(str(match.group(1)))
    assert not missing, f"Broken ledger links: {missing}"
