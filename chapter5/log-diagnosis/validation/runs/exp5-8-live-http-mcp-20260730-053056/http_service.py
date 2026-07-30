"""Small real HTTP system used by the Experiment 5-8 campaign.

The service intentionally exposes ordinary order, refund, and inventory
endpoints.  The buggy/fixed distinction lives in the orchestrator under test:
the buggy orchestrator skips a required endpoint and mishandles an inventory
timeout, while the fixed orchestrator makes the required calls and degrades.
"""

from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class Handler(BaseHTTPRequestHandler):
    server_version = "Experiment58HTTP/1.0"

    def log_message(self, fmt: str, *args: object) -> None:
        print(
            json.dumps(
                {
                    "client": self.client_address[0],
                    "message": fmt % args,
                    "time": time.time(),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )

    def _json(self, status: int, value: object) -> None:
        raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except BrokenPipeError:
            # A timed-out client is an expected part of the observed buggy run.
            pass

    def _body(self) -> dict[str, object]:
        length = int(self.headers.get("content-length") or 0)
        if not length:
            return {}
        value = json.loads(self.rfile.read(length))
        return value if isinstance(value, dict) else {}

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._json(200, {"ok": True})
            return
        if parsed.path.startswith("/orders/"):
            order_id = parsed.path.rsplit("/", 1)[-1]
            self._json(200, {"order_id": order_id, "status": "paid", "sku": "SKU-42"})
            return
        if parsed.path.startswith("/inventory/"):
            sku = parsed.path.rsplit("/", 1)[-1]
            degraded = parse_qs(parsed.query).get("degraded", ["0"])[0] == "1"
            if degraded:
                self._json(200, {"sku": sku, "stock": 12, "source": "cache", "degraded": True})
            else:
                # Longer than the campaign's real client deadline.
                time.sleep(0.8)
                self._json(200, {"sku": sku, "stock": 12, "source": "origin", "degraded": False})
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        body = self._body()
        if self.path == "/refund/eligibility":
            self._json(200, {"order_id": body.get("order_id"), "eligible": True})
            return
        if self.path == "/refund/process":
            self._json(200, {"order_id": body.get("order_id"), "refund_id": "RF-LIVE-1"})
            return
        if self.path == "/notifications":
            self._json(200, {"sent": True, "status": body.get("status")})
            return
        self._json(404, {"error": "not_found"})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(json.dumps({"listening": args.port}), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
