#!/usr/bin/env python3
"""Deterministically validate retained Experiment 9-6 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


EXPECTED_MODEL = "claude-sonnet-4-5-20250929"
EXPECTED_SOURCE = "9bcc95e316e5ef6542b4c9d0469f4078829eead5"
EXPECTED_DOCKERFILE = (
    "3aa1f36a491f8f88d81a04c6a89b4cc9f9acd20ad946304c13419736da7c0ead"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    trajectory = json.loads((run_dir / "trajectory.json").read_text())

    calls = trajectory["api_calls"]
    actions = trajectory["actions"]
    final = trajectory["final_answer"]
    receipts = sorted((run_dir / "api_receipts").glob("response-*.json"))
    referenced_screenshots = [
        run_dir / action["result"]["screenshot"]
        for action in actions
        if action.get("result") and action["result"].get("screenshot")
    ]

    message_ids = [call["response"].get("message_id") for call in calls]
    request_ids = [call["response"].get("request_id") for call in calls]
    tool_ids = [action.get("tool_use_id") for action in actions]
    temperature = bool(
        re.search(r"\b-?\d{1,3}\s*(?:°\s*[CF]|degrees?\s*[CF])\b", final, re.I)
    )
    condition = bool(
        re.search(
            r"\b(?:sunny|clear|cloudy|overcast|fog(?:gy)?|rain(?:y)?|"
            r"showers?|storm(?:y)?|drizzle|snow(?:y)?|mist(?:y)?|haze|"
            r"partly\s+cloudy|mostly\s+cloudy)\b",
            final,
            re.I,
        )
    )

    gates = {
        "source_commit": trajectory["runtime"].get("source_commit")
        == EXPECTED_SOURCE,
        "dockerfile_sha256": trajectory["runtime"].get("dockerfile_sha256")
        == EXPECTED_DOCKERFILE,
        "immutable_image_id": str(trajectory["runtime"].get("image_id", "")).startswith(
            "sha256:"
        ),
        "base_image_digest": str(
            trajectory["runtime"].get("base_image_digest", "")
        ).startswith("sha256:"),
        "model_finished": trajectory.get("termination") == "model_finished"
        and trajectory.get("provider_stop_reason") == "end_turn",
        "action_ceiling": 0 < len(actions) <= trajectory.get("action_limit", 0) <= 25,
        "sequential_action_indexes": [a.get("index") for a in actions]
        == list(range(1, len(actions) + 1)),
        "unique_tool_use_ids": None not in tool_ids and len(tool_ids) == len(set(tool_ids)),
        "native_tools_retained": "computer"
        in {action.get("tool") for action in actions}
        and {action.get("tool") for action in actions}.issubset(
            {"computer", "bash", "str_replace_based_edit_tool"}
        ),
        "all_actions_executed": all(
            action.get("executed") and action.get("result") is not None
            for action in actions
        ),
        "all_provider_calls_succeeded": bool(calls)
        and all(call["response"].get("http_status") == 200 for call in calls),
        "provider_model_match": trajectory.get("observed_models") == [EXPECTED_MODEL]
        and all(call["response"].get("model") == EXPECTED_MODEL for call in calls),
        "unique_message_ids": None not in message_ids
        and len(message_ids) == len(set(message_ids)),
        "unique_request_ids": None not in request_ids
        and len(request_ids) == len(set(request_ids)),
        "receipt_count": len(receipts) == len(calls),
        "screenshots_exist_and_match": bool(referenced_screenshots)
        and all(
            path.is_file()
            and sha256(path)
            == next(
                action["result"]["screenshot_sha256"]
                for action in actions
                if action.get("result")
                and action["result"].get("screenshot")
                and run_dir / action["result"]["screenshot"] == path
            )
            for path in referenced_screenshots
        ),
        "grounded_weather_answer": temperature and condition,
        "no_captcha_interaction": not any(
            "captcha" in json.dumps(action.get("input", {})).lower()
            or "i'm not a robot" in json.dumps(action.get("input", {})).lower()
            for action in actions
        ),
        "no_credential_material": not any(
            b"sk-ant-" in path.read_bytes()
            for path in run_dir.rglob("*")
            if path.is_file()
        ),
    }

    files = []
    for path in sorted(p for p in run_dir.rglob("*") if p.is_file()):
        if path.name in {"acceptance.json", "manifest.json"}:
            continue
        files.append(
            {
                "path": str(path.relative_to(run_dir)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    acceptance = {
        "schema_version": 1,
        "experiment": "9-6",
        "run_dir": run_dir.name,
        "passed": all(gates.values()),
        "gates": gates,
        "counts": {
            "api_calls": len(calls),
            "actions": len(actions),
            "screenshots": len(referenced_screenshots),
            "files_hashed": len(files),
        },
    }
    manifest = {
        "schema_version": 1,
        "experiment": "9-6",
        "run_dir": run_dir.name,
        "files": files,
    }
    (run_dir / "acceptance.json").write_text(json.dumps(acceptance, indent=2) + "\n")
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(acceptance, indent=2))
    return 0 if acceptance["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
