"""审计链写入锁：单进程 threading；可选 Postgres advisory lock 防双副本分叉。"""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Any, Iterator

# 固定锁键：llm-safety audit chain namespace
_ADVISORY_KEY = 0x53414645_41554449  # "SAFEAUDI" truncated hex-ish


_process_lock = threading.Lock()


@contextmanager
def audit_chain_lock(db_session: Any | None = None) -> Iterator[None]:
    """
    包裹审计链追加。

    - 始终持有进程内锁（HashChainLedger 已用；此处供 DB 路径复用）。
    - 当 SAFETY_AUDIT_ADVISORY_LOCK=1 且提供 SQLAlchemy session 时，
      额外获取 pg_advisory_lock，使双副本并发写可串行化；
      若仍出现分叉，verify_audit_rows 会报 error=fork。
    """
    use_pg = os.getenv("SAFETY_AUDIT_ADVISORY_LOCK", "").strip() in {"1", "true", "yes"}
    locked_pg = False
    with _process_lock:
        if use_pg and db_session is not None:
            try:
                db_session.execute(
                    __import__("sqlalchemy").text("SELECT pg_advisory_lock(:k)"),
                    {"k": _ADVISORY_KEY},
                )
                locked_pg = True
            except Exception:
                # 非 PG 或锁失败：继续进程锁，由链校验兜底检测分叉
                locked_pg = False
        try:
            yield
        finally:
            if locked_pg and db_session is not None:
                try:
                    db_session.execute(
                        __import__("sqlalchemy").text("SELECT pg_advisory_unlock(:k)"),
                        {"k": _ADVISORY_KEY},
                    )
                except Exception:
                    pass


def simulate_dual_writer_fork() -> dict[str, Any]:
    """
    演示双副本无锁并发写会产生可检测分叉（验收用，不写入真实 DB）。
    """
    from app.observability.chain_verify import compute_chain_hash, verify_audit_rows
    import json

    class _Row:
        def __init__(self, request_id: str, decision: dict) -> None:
            self.request_id = request_id
            payload = {k: v for k, v in decision.items() if k not in ("chain_hash", "prev_chain_hash")}
            self.body_json = json.dumps(payload, sort_keys=True, ensure_ascii=False)
            self.chain_hash = decision["chain_hash"]
            self.prev_chain_hash = decision["prev_chain_hash"]
            self.content_hash = ""

    genesis_prev = "GENESIS"
    base = {"request_id": "req_0", "decision": "allow", "n": 0}
    h0 = compute_chain_hash(genesis_prev, base)
    d0 = {**base, "prev_chain_hash": genesis_prev, "chain_hash": h0}

    # 两个副本同时基于 h0 写下一条 → fork
    d1a_body = {"request_id": "req_1a", "decision": "allow", "n": 1, "replica": "A"}
    d1b_body = {"request_id": "req_1b", "decision": "allow", "n": 1, "replica": "B"}
    h1a = compute_chain_hash(h0, d1a_body)
    h1b = compute_chain_hash(h0, d1b_body)
    d1a = {**d1a_body, "prev_chain_hash": h0, "chain_hash": h1a}
    d1b = {**d1b_body, "prev_chain_hash": h0, "chain_hash": h1b}

    rows = [_Row("req_0", d0), _Row("req_1a", d1a), _Row("req_1b", d1b)]
    result = verify_audit_rows(rows)
    return {
        "ok": result.get("ok") is False and result.get("error") == "fork",
        "verify": result,
        "recovery": "启用 SAFETY_AUDIT_ADVISORY_LOCK=1 或专用 single-writer；分叉必须人工仲裁后重放",
    }
