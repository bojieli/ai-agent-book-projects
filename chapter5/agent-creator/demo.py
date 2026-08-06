from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from creator import DEFAULT_PROTOCOL, load_protocol, run_experiment


DEFAULT_REQUIREMENTS = load_protocol()[0]["requirements"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Experiment 5-13: compare an Agent created from scratch with one adapted from a proven Agent"
    )
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--output", type=Path, default=Path("runs/latest"))
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument(
        "--live-task",
        default=None,
        help="Development-only single task override; it cannot complete the frozen book experiment",
    )
    parser.add_argument("--no-live", action="store_true", help="Skip real API execution of generated Agents")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse already generated arms in --output and repair/revalidate them",
    )
    args = parser.parse_args()
    result = run_experiment(
        args.requirements,
        args.output,
        live=not args.no_live,
        live_task=args.live_task,
        resume=args.resume,
        protocol_path=args.protocol,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["official_complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
