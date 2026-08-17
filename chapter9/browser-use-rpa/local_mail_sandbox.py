"""Resettable localhost mail UI used by the real Playwright Experiment 9-5.

The server is deliberately small, but it is not a mocked browser: Chromium
loads the page, JavaScript sends HTTP requests, and the final sent-list is
rendered from server-side state.  All side effects remain inside this process.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Lock, Thread
from typing import Any, Iterator
from urllib.parse import urlparse


@dataclass
class MailState:
    messages: list[dict[str, str]] = field(default_factory=list)
    version: int = 1
    fault: str = "normal"
    reset_count: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)
    lock: Lock = field(default_factory=Lock, repr=False)

    def reset(self, *, version: int = 1, fault: str = "normal") -> None:
        with self.lock:
            self.messages.clear()
            self.version = version
            self.fault = fault
            self.reset_count += 1
            self.events.append({
                "event": "validation_reset",
                "version": version,
                "fault": fault,
                "reset_index": self.reset_count,
            })

    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        message = {key: str(payload.get(key, "")) for key in ("recipient", "subject", "content")}
        with self.lock:
            self.events.append({"event": "send_request", "message": message, "version": self.version})
            if not all(value.strip() for value in message.values()):
                self.events.append({"event": "validation_rejected", "reason": "blank_field"})
                return {"ok": False, "persisted": False, "reason": "blank_field"}
            if self.fault == "drop_persistence":
                self.events.append({"event": "persistence_dropped"})
                return {"ok": True, "persisted": False, "reason": "storage_write_dropped"}
            self.messages.append(message)
            self.events.append({"event": "message_persisted", "message": message})
            return {"ok": True, "persisted": True, "reason": None}

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "messages": list(self.messages),
                "version": self.version,
                "fault": self.fault,
                "reset_count": self.reset_count,
                "events": list(self.events),
            }


def _html(version: int) -> str:
    button_id = "send" if version == 1 else "deliver-v2"
    button_text = "Send message" if version == 1 else "Deliver message"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Local mail sandbox</title>
<style>body{{font:16px sans-serif;max-width:700px;margin:2rem auto}}label{{display:block;margin:.7rem 0}}input,textarea{{display:block;width:100%}}#status{{min-height:1.5rem}}</style>
</head><body>
<main><h1>Compose sandbox message</h1>
<label>Recipient <input id="recipient" name="recipient" type="email" data-testid="recipient"></label>
<label>Subject <input id="subject" name="subject" data-testid="subject"></label>
<label>Content <textarea id="content" name="content" data-testid="content"></textarea></label>
<button id="{button_id}" data-testid="{button_id}" type="button">{button_text}</button>
<p id="status" role="status">Draft</p>
<h2>Sent messages</h2><div id="sent-list"></div></main>
<script>
window.__agentState = {{sent:false, persistedCount:0}};
async function refresh() {{
  const state = await (await fetch('/api/state')).json();
  window.__agentState.persistedCount = state.messages.length;
  document.querySelector('#sent-list').innerHTML = state.messages.map((m) =>
    `<article data-message><strong>${{m.recipient}}</strong><b>${{m.subject}}</b><span>${{m.content}}</span></article>`).join('');
}}
document.querySelector('#{button_id}').addEventListener('click', async () => {{
  const payload = {{
    recipient:document.querySelector('#recipient').value,
    subject:document.querySelector('#subject').value,
    content:document.querySelector('#content').value
  }};
  const result = await (await fetch('/api/send', {{method:'POST',headers:{{'content-type':'application/json'}},body:JSON.stringify(payload)}})).json();
  window.__agentState.sent = !!result.persisted;
  document.querySelector('#status').textContent = result.persisted ? 'Message sent' : (result.ok ? 'Accepted but not persisted' : 'Message not sent');
  await refresh();
}});
refresh();
</script></body></html>"""


def make_handler(state: MailState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: Any) -> None:
            return

        def _json(self, payload: Any, status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "application/json; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            path = urlparse(self.path).path
            if path == "/app":
                body = _html(state.snapshot()["version"]).encode("utf-8")
                self.send_response(200)
                self.send_header("content-type", "text/html; charset=utf-8")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif path == "/api/state":
                self._json(state.snapshot())
            else:
                self._json({"error": "not_found"}, 404)

        def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            length = int(self.headers.get("content-length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            path = urlparse(self.path).path
            if path == "/api/send":
                self._json(state.send(payload))
            elif path == "/api/reset":
                state.reset(version=int(payload.get("version", 1)), fault=str(payload.get("fault", "normal")))
                self._json({"ok": True, "reset_count": state.reset_count})
            else:
                self._json({"error": "not_found"}, 404)

    return Handler


@contextmanager
def mail_sandbox() -> Iterator[tuple[str, MailState]]:
    state = MailState()
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(state))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
