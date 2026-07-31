#!/usr/bin/env python3
"""Launch the fixed-parameter control arm of Experiment 9-2."""

from __future__ import annotations

import argparse
import threading
import urllib.parse
import webbrowser

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Name shown in the AI's opening line")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--context", required=True)
    parser.add_argument("--instructions", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--no-open", action="store_true", help="Do not open the browser automatically"
    )
    args = parser.parse_args()
    query = urllib.parse.urlencode(
        {
            "mode": "direct",
            "callee_name": args.name,
            "goal": args.goal,
            "context": args.context,
            "instructions": args.instructions,
        }
    )
    url = f"http://{args.host}:{args.port}/?{query}"
    print(f"Experiment 9-2 direct endpoint: {url}")
    if not args.no_open:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    uvicorn.run("webrtc_app:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
