"""Live HTTP regressions for the findings reported in issue #502."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from http.server import ThreadingHTTPServer

import pytest

from campaign import INVENTORY_DEADLINE_SECONDS, _trajectory
from http_service import Handler


@pytest.fixture
def order_service() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


def test_refund_verifies_eligibility_before_processing(order_service: str) -> None:
    trajectory = _trajectory(
        order_service,
        {"intent": "refund", "order_id": "ORD-58-A"},
        "HTTP-RF-001",
    )

    tools = [turn.get("tool") for turn in trajectory["turns"]]
    assert tools.count("verify_refund_eligibility") == 1
    assert tools.index("verify_refund_eligibility") < tools.index("process_refund")
    assert trajectory["final_status"] == "success"


def test_inventory_timeout_uses_cache_within_deadline(order_service: str) -> None:
    trajectory = _trajectory(
        order_service,
        {
            "intent": "order_status",
            "order_id": "ORD-58-B",
            "sku": "SKU-42",
        },
        "HTTP-INV-001",
    )

    stock_calls = [
        turn for turn in trajectory["turns"] if turn.get("tool") == "check_stock"
    ]
    assert len(stock_calls) == 2
    assert stock_calls[0]["status"] == "error"
    assert stock_calls[1]["status"] == "success"
    assert stock_calls[1]["response"]["source"] == "cache"
    assert sum(float(turn["latency_ms"]) for turn in stock_calls) < (
        INVENTORY_DEADLINE_SECONDS * 1000
    )
    assert trajectory["final_status"] == "success"
