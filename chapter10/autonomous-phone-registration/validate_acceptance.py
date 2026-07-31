#!/usr/bin/env python3
"""Fail-closed validator for retained Experiment 10-5 evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

TOOL_NAME = "initiate_phone_call_agent"
ARK_PROVIDER = "Volcengine ARK"
ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3"
INPUT_NAMES = {"experiment_input.json"}
ARTIFACT_NAMES = {
    "acceptance_report.json",
    "decision.json",
    "form_submission_receipt.json",
    "message_timeline.json",
    "raw_decision_request.json",
    "raw_decision_response.json",
    "validation_report.json",
}
SOURCE_NAMES = {
    "browser.py",
    "bus.py",
    "decision.py",
    "demo.py",
    "models.py",
    "orchestration.py",
    "run_acceptance.py",
    "validate_acceptance.py",
    "voice.py",
    "webrtc_channel.py",
}
CREDENTIAL_PATTERN = re.compile(
    r"(?i)(?:sk-[A-Za-z0-9_-]{12,}|gho_[A-Za-z0-9_-]{12,}|"
    r"github_pat_[A-Za-z0-9_-]{12,}|authorization.{0,16}bearer\s+[A-Za-z0-9._-]{12,})"
)


class ValidationFailure(RuntimeError):
    """Raised when retained evidence does not prove its claims."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationFailure(message)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"cannot read JSON evidence {path.name}: {exc}") from exc
    _require(isinstance(value, dict), f"{path.name} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise ValidationFailure(f"cannot hash {path}: {exc}") from exc


def _validate_hash_map(
    *,
    expected_names: set[str],
    hashes: Any,
    base: Path,
    label: str,
) -> None:
    _require(isinstance(hashes, dict), f"manifest {label} must be an object")
    names = set(hashes)
    _require(names == expected_names, f"manifest {label} names differ: {sorted(names)}")
    for name, expected in hashes.items():
        _require(
            isinstance(expected, str) and len(expected) == 64, f"invalid {label} hash for {name}"
        )
        _require(_sha256(base / name) == expected, f"{label} hash mismatch for {name}")


def _tool_call(response: dict[str, Any]) -> dict[str, Any]:
    choices = response.get("choices")
    _require(isinstance(choices, list) and len(choices) == 1, "raw response must have one choice")
    choice = choices[0]
    _require(
        choice.get("finish_reason") == "tool_calls", "raw response did not finish with tool_calls"
    )
    message = choice.get("message", {})
    calls = message.get("tool_calls")
    _require(isinstance(calls, list) and len(calls) == 1, "raw response must have one tool call")
    call = calls[0]
    _require(call.get("type") == "function", "raw response tool call must be a function")
    function = call.get("function", {})
    _require(function.get("name") == TOOL_NAME, "raw response selected the wrong tool")
    return function


def _normalized_required_info(
    raw_arguments: dict[str, Any], decision: dict[str, Any]
) -> list[dict[str, Any]]:
    discovered = decision.get("discovered_fields")
    _require(isinstance(discovered, list), "normalized decision lacks discovered_fields")
    by_name = {str(field.get("name", "")): field for field in discovered}
    by_label = {str(field.get("label", "")).casefold(): field for field in discovered}
    known = set(decision.get("known_fields", []))
    normalized = []
    for item in raw_arguments.get("required_info", []):
        _require(isinstance(item, dict), "raw required_info entries must be objects")
        candidate = by_name.get(str(item.get("name", ""))) or by_label.get(
            str(item.get("label", "")).casefold()
        )
        _require(candidate is not None, "raw tool arguments reference an unknown field")
        if candidate["name"] not in known and candidate not in normalized:
            normalized.append(candidate)
    return normalized


def validate_run(
    run_dir: Path,
    *,
    source_root: Path | None = None,
    require_validation_report: bool = True,
) -> dict[str, Any]:
    """Validate one retained run and return a deterministic validation report."""
    run_dir = run_dir.resolve()
    source_root = (source_root or Path(__file__).parent).resolve()
    manifest = _load_json(run_dir / "manifest.json")
    _require(manifest.get("schema_version") == 2, "manifest schema_version must be 2")
    _require(manifest.get("experiment") == "10-5", "manifest experiment must be 10-5")

    artifact_names = (
        ARTIFACT_NAMES if require_validation_report else ARTIFACT_NAMES - {"validation_report.json"}
    )
    expected_run_names = {"manifest.json"} | INPUT_NAMES | artifact_names
    actual_run_names = {path.name for path in run_dir.iterdir()}
    _require(
        actual_run_names == expected_run_names,
        f"retained run files differ: {sorted(actual_run_names)}",
    )
    input_hashes = manifest.get("input_sha256")
    _validate_hash_map(
        expected_names=INPUT_NAMES,
        hashes=input_hashes,
        base=run_dir,
        label="input_sha256",
    )
    _validate_hash_map(
        expected_names=artifact_names,
        hashes=manifest.get("artifact_sha256"),
        base=run_dir,
        label="artifact_sha256",
    )
    source_hashes = manifest.get("source_sha256")
    _require(isinstance(source_hashes, dict), "manifest source_sha256 must be an object")
    _require(set(source_hashes) == SOURCE_NAMES, "manifest source_sha256 names differ")
    for name, expected in source_hashes.items():
        _require(_sha256(source_root / name) == expected, f"source_sha256 hash mismatch for {name}")
    _require(
        re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("git_head_at_run", ""))) is not None,
        "manifest git_head_at_run is invalid",
    )

    experiment_input = _load_json(run_dir / "experiment_input.json")
    raw_request = _load_json(run_dir / "raw_decision_request.json")
    raw_response = _load_json(run_dir / "raw_decision_response.json")
    decision = _load_json(run_dir / "decision.json")
    acceptance = _load_json(run_dir / "acceptance_report.json")
    form_receipt = _load_json(run_dir / "form_submission_receipt.json")
    timeline = json.loads((run_dir / "message_timeline.json").read_text(encoding="utf-8"))

    _require(raw_request.get("provider") == ARK_PROVIDER, "raw request is not an ARK request")
    _require(raw_request.get("endpoint") == ARK_ENDPOINT, "raw request uses an unexpected endpoint")
    _require(
        raw_request.get("credential_fields_retained") == [],
        "raw request retained credential fields",
    )
    request = raw_request.get("request", {})
    _require(request.get("tool_choice") == "auto", "raw request did not use tool_choice=auto")
    tools = request.get("tools")
    _require(
        isinstance(tools, list) and len(tools) == 1, "raw request must expose one optional tool"
    )
    _require(
        tools[0].get("function", {}).get("name") == TOOL_NAME, "raw request tool schema differs"
    )

    _require(raw_response.get("provider") == ARK_PROVIDER, "raw response is not from ARK")
    _require(decision.get("provider") == ARK_PROVIDER, "normalized decision is not from ARK")
    latency = raw_response.get("latency_seconds")
    _require(
        isinstance(latency, (int, float)) and latency > 0, "raw response lacks positive latency"
    )
    response = raw_response.get("response", {})
    _require(
        response.get("id") == decision.get("provider_response_id"),
        "response ID differs from decision",
    )
    _require(request.get("model") == decision.get("model"), "request model differs from decision")
    _require(response.get("model") == decision.get("model"), "response model differs from decision")
    usage = response.get("usage", {})
    normalized_usage = {
        key: usage[key]
        for key in ("prompt_tokens", "completion_tokens", "total_tokens")
        if key in usage
    }
    _require(
        normalized_usage == decision.get("provider_usage"), "response usage differs from decision"
    )

    function = _tool_call(response)
    try:
        raw_arguments = json.loads(function["arguments"])
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValidationFailure("raw tool-call arguments are not valid JSON") from exc
    _require(isinstance(raw_arguments, dict), "raw tool-call arguments must be an object")
    _require(
        set(raw_arguments) == {"purpose", "required_info"},
        "raw tool-call arguments contain unexpected fields",
    )
    _require(isinstance(raw_arguments["required_info"], list), "raw required_info must be a list")
    _require(decision.get("tool_called") == TOOL_NAME, "normalized decision records the wrong tool")
    _require(
        raw_arguments.get("purpose") == decision.get("purpose"), "raw purpose differs from decision"
    )
    _require(
        _normalized_required_info(raw_arguments, decision) == decision.get("required_info"),
        "raw tool-call arguments do not normalize exactly to decision.json",
    )

    messages = request.get("messages")
    _require(
        isinstance(messages, list) and len(messages) == 2, "raw request messages are incomplete"
    )
    try:
        user_observation = json.loads(messages[1]["content"])
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValidationFailure("raw request user observation is invalid") from exc
    _require(
        user_observation.get("page_url") == experiment_input.get("page_url"),
        "input page URL differs",
    )
    visible_decision_fields = [
        {
            "name": field["name"],
            "label": field["label"],
            "type": field["input_type"],
            "required": field["required"],
            "format_hint": field["format_hint"],
            "options": field["options"],
        }
        for field in decision["discovered_fields"]
    ]
    _require(
        user_observation.get("form_fields") == visible_decision_fields,
        "raw page observation differs",
    )
    _require(
        experiment_input.get("form_html_sha256")
        == hashlib.sha256(experiment_input.get("form_html", "").encode("utf-8")).hexdigest(),
        "input form HTML hash differs",
    )

    _require(acceptance.get("overall_status") == "pass", "acceptance status is not pass")
    gates = acceptance.get("gates", {})
    _require(
        gates and all(item.get("status") == "pass" for item in gates.values()),
        "an acceptance gate failed",
    )
    _require(
        manifest.get("acceptance")
        == {
            "overall_status": "pass",
            "gate_count": len(gates),
            "passed_gate_count": len(gates),
        },
        "manifest acceptance summary differs",
    )
    if require_validation_report:
        _require(
            manifest.get("retained_evidence_validation") == "pass",
            "manifest retained-evidence status is not pass",
        )
    _require(isinstance(timeline, list), "message timeline must be a list")
    collected = [row for row in timeline if row.get("type") == "info_collected"]
    _require(collected, "message timeline has no collected fields")
    _require(
        all(row.get("payload", {}).get("value") == "<redacted>" for row in collected),
        "participant values are not redacted",
    )
    _require(
        acceptance.get("webrtc_receipt", {}).get("raw_audio_retained") is False,
        "raw audio retained",
    )
    _require(
        acceptance.get("webrtc_receipt", {}).get("transcripts_retained") is False,
        "transcripts retained",
    )
    _require(
        experiment_input.get("participant_values_retained") is False, "input claims values retained"
    )
    _require(form_receipt.get("raw_values_retained") is False, "form receipt retained raw values")
    retained_text = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(run_dir.iterdir()) if path.is_file()
    )
    _require(
        not CREDENTIAL_PATTERN.search(retained_text), "retained evidence contains a credential"
    )

    result = {
        "schema_version": 1,
        "experiment": "10-5",
        "status": "pass",
        "checks": {
            "source_hashes": "pass",
            "artifact_hashes": "pass",
            "input_hashes": "pass",
            "raw_ark_request_tool_choice_auto": "pass",
            "raw_ark_response_metadata": "pass",
            "raw_arguments_normalize_to_decision": "pass",
            "participant_privacy": "pass",
            "acceptance_gates": "pass",
        },
    }
    if require_validation_report:
        _require(
            _load_json(run_dir / "validation_report.json") == result,
            "retained validation report differs from recomputed result",
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    report = validate_run(args.run_dir, source_root=args.source_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
