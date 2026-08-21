"""外部调用留证：每次 API/模型调用的参数、响应摘要、时间戳、耗时落盘为 JSON。

密钥绝不写入 receipt——只记录端点、模型、请求参数与响应内容。
"""
from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class ReceiptBook:
    """一次正式运行内全部外部调用的留证簿。"""

    def __init__(self, directory):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.calls = []

    def record(self, name: str, *, provider: str, endpoint: str, model: str | None,
               request: dict, response: dict, started_utc: str, ended_utc: str,
               latency_ms: int, status: str = "ok") -> dict:
        idx = len(self.calls) + 1
        rec = {
            "name": name,
            "provider": provider,
            "endpoint": endpoint,
            "model": model,
            "status": status,
            "started_utc": started_utc,
            "ended_utc": ended_utc,
            "latency_ms": latency_ms,
            "request": request,
            "response": response,
        }
        path = self.dir / f"{idx:02d}-{name}.json"
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=2))
        entry = {"name": name, "path": str(path), "sha256": sha256_file(path),
                 "status": status, "latency_ms": latency_ms}
        self.calls.append(entry)
        return entry
