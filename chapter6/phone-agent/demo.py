#!/usr/bin/env python3
"""Launch the ReAct arm of the local Experiment 9-2 browser call."""

from __future__ import annotations

import argparse
import threading
import urllib.parse
import webbrowser

import uvicorn

DEFAULT_TASK = (
    "Call me to arrange a dental checkup. I did not include the exact time or confirmation code, "
    "so ask me for both by voice, repeat the details, and save only what I explicitly confirm."
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default=DEFAULT_TASK)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--no-open", action="store_true", help="Do not open the browser automatically"
    )
    args = parser.parse_args()
    query = urllib.parse.urlencode({"mode": "react", "task": args.task})
    url = f"http://{args.host}:{args.port}/?{query}"
    print(f"Experiment 9-2 ReAct endpoint: {url}")
    if not args.no_open:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    uvicorn.run("webrtc_app:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
