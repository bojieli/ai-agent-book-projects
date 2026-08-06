"""Hash-chain verification — graph rebuild from prev→hash links (not DB id order)."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any, Sequence


GENESIS = "GENESIS"


class ChainIntegrityError(Exception):
    """Raised when persisted audit chain cannot be verified (fail-closed)."""

    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        super().__init__(result.get("error", "chain_integrity_failed"))


def chain_payload(decision: dict[str, Any]) -> str:
    """Canonical JSON payload for hash-chain link (excludes chain fields)."""
    base = {k: v for k, v in decision.items() if k not in ("chain_hash", "prev_chain_hash")}
    return json.dumps(base, sort_keys=True, ensure_ascii=False)


def compute_chain_hash(prev: str, decision: dict[str, Any]) -> str:
    return hashlib.sha256((prev + chain_payload(decision)).encode("utf-8")).hexdigest()


def _row_chain_hash(row: Any) -> str:
    return (getattr(row, "chain_hash", "") or "").strip()


def _row_prev_hash(row: Any) -> str:
    prev = (getattr(row, "prev_chain_hash", "") or "").strip()
    return prev or GENESIS


def rebuild_chain_from_rows(rows: Sequence[Any]) -> tuple[list[Any], dict[str, Any]]:
    """Rebuild unique chain order from ``prev_chain_hash → chain_hash`` graph.

    Detects fork, missing link, cycle, duplicate hash, orphan, and payload tamper.
    DB insert/commit order is irrelevant — only link topology matters.
    """
    chained = [r for r in rows if _row_chain_hash(r)]
    if not chained:
        return [], {"ok": True, "length": 0, "source": "database", "note": "no_chained_rows"}

    by_hash: dict[str, Any] = {}
    by_prev: dict[str, list[Any]] = defaultdict(list)
    for row in chained:
        h = _row_chain_hash(row)
        if h in by_hash:
            return [], {
                "ok": False,
                "source": "database",
                "error": "duplicate_chain_hash",
                "chain_hash": h,
                "request_id": row.request_id,
            }
        by_hash[h] = row
        by_prev[_row_prev_hash(row)].append(row)

    for prev, children in by_prev.items():
        if len(children) > 1:
            return [], {
                "ok": False,
                "source": "database",
                "error": "fork",
                "prev_chain_hash": prev,
                "request_ids": [c.request_id for c in children],
            }

    ordered: list[Any] = []
    current_prev = GENESIS
    visited: set[str] = set()
    while True:
        children = by_prev.get(current_prev, [])
        if not children:
            break
        row = children[0]
        h = _row_chain_hash(row)
        if h in visited:
            return [], {
                "ok": False,
                "source": "database",
                "error": "cycle",
                "chain_hash": h,
                "request_id": row.request_id,
            }
        visited.add(h)

        if _row_prev_hash(row) != current_prev:
            return [], {
                "ok": False,
                "source": "database",
                "error": "broken_link",
                "request_id": row.request_id,
                "expected_prev": current_prev,
                "stored_prev": _row_prev_hash(row),
            }

        try:
            sd = json.loads(row.body_json)
        except (json.JSONDecodeError, TypeError):
            return [], {
                "ok": False,
                "source": "database",
                "error": "invalid_body_json",
                "request_id": row.request_id,
            }

        expect = compute_chain_hash(current_prev, sd)
        stored_hash = _row_chain_hash(row)
        if stored_hash != expect:
            return [], {
                "ok": False,
                "source": "database",
                "error": "hash_mismatch",
                "request_id": row.request_id,
                "chain_hash": stored_hash,
            }

        ordered.append(row)
        current_prev = stored_hash

    orphans = [r for r in chained if _row_chain_hash(r) not in visited]
    if orphans:
        missing_prevs = [
            r.request_id
            for r in orphans
            if _row_prev_hash(r) != GENESIS and _row_prev_hash(r) not in by_hash
        ]
        err = "orphan" if not missing_prevs else "missing_link"
        return [], {
            "ok": False,
            "source": "database",
            "error": err,
            "orphan_count": len(orphans),
            "request_ids": [r.request_id for r in orphans[:10]],
        }

    return ordered, {
        "ok": True,
        "length": len(ordered),
        "source": "database",
        "skipped_legacy": len(rows) - len(chained),
    }


def verify_chain_list(chain: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Verify in-memory ledger.chain entries (sequential append order)."""

    class _MemRow:
        def __init__(self, d: dict[str, Any]) -> None:
            self.body_json = json.dumps(
                {k: v for k, v in d.items() if k not in ("chain_hash", "prev_chain_hash")},
                ensure_ascii=False,
            )
            self.chain_hash = d.get("chain_hash", "")
            self.prev_chain_hash = d.get("prev_chain_hash", GENESIS)
            self.request_id = d.get("request_id", "")

    rows = [_MemRow(item) for item in chain if item.get("chain_hash")]
    _, result = rebuild_chain_from_rows(rows)
    if result.get("ok"):
        result["source"] = "memory"
    return result


def verify_audit_rows(rows: Sequence[Any]) -> dict[str, Any]:
    """Verify persisted audit rows via graph rebuild (not id order)."""
    _, result = rebuild_chain_from_rows(rows)
    return result


def hydrate_ledger_from_rows(ledger: Any, rows: Sequence[Any]) -> int:
    """Verify then hydrate in-process ledger — fail-closed on any integrity error."""
    ordered, result = rebuild_chain_from_rows(rows)
    if not result.get("ok"):
        raise ChainIntegrityError(result)

    ledger.chain.clear()
    ledger._prev = GENESIS  # noqa: SLF001
    for row in ordered:
        sd = json.loads(row.body_json)
        sd["chain_hash"] = _row_chain_hash(row)
        sd["prev_chain_hash"] = _row_prev_hash(row)
        ledger.chain.append(sd)
        ledger._prev = sd["chain_hash"]  # noqa: SLF001
    return len(ordered)
