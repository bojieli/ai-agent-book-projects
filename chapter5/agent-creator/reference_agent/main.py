from __future__ import annotations

import argparse
import json

from agent import GeneratedAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the generated Agent")
    parser.add_argument("--task", required=True)
    parser.add_argument("--model")
    parser.add_argument("--history-json", default="[]")
    args = parser.parse_args()
    history = json.loads(args.history_json)
    if not isinstance(history, list):
        raise SystemExit("--history-json must decode to a list")
    result = GeneratedAgent(model=args.model).run(args.task, history=history)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
