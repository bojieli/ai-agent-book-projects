#!/usr/bin/env python3
"""Fail-closed validator for the canonical Experiment 7-5 report evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
EXPERIMENT_DIR = HERE.parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
LATEST_PATH = HERE / "latest.json"
STAGES = {"baseline", "pretrained", "finetuned"}
EXPECTED_REVISIONS = {
    "base_model": "9ea1b83f5ced5663c5fa89c300fe59f9bdcd2b10",
    "continued_pretraining_dataset": "b04c8d1ceb2f5cd4588862100d08de323dccfbaa",
    "instruction_dataset": "f38ae19cf673363d74fab6217de46c1b9c3150d4",
}
SECRET_PATTERNS = (
    re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+\S+"),
    re.compile(r"(?i)(?:api[_-]?key|secret)\s*[:=]\s*[A-Za-z0-9._-]{16,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return value


def parse_response_content(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    value = json.loads(stripped)
    if not isinstance(value, dict):
        raise AssertionError("judge response content must decode to an object")
    return value


def resolve_relative(base: Path, relative: str) -> Path:
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()):
        raise AssertionError(f"path escapes evidence root: {relative}")
    return path


def check_record(path: Path, record: dict[str, Any]) -> None:
    if not path.is_file():
        raise AssertionError(f"missing declared file: {path}")
    if path.stat().st_size != record.get("bytes"):
        raise AssertionError(f"byte count mismatch: {path}")
    if sha256_file(path) != record.get("sha256"):
        raise AssertionError(f"SHA-256 mismatch: {path}")


def validate(latest_path: Path = LATEST_PATH) -> dict[str, Any]:
    latest = load_json(latest_path)
    if latest.get("experiment") != "7-5" or latest.get("status") != "passed":
        raise AssertionError("latest pointer is not a passed Experiment 7-5 run")
    run_dir = resolve_relative(EXPERIMENT_DIR, latest["run_dir"])
    manifest_path = run_dir / "manifest.json"
    if sha256_file(manifest_path) != latest.get("manifest_sha256"):
        raise AssertionError("latest manifest hash mismatch")
    manifest = load_json(manifest_path)
    if manifest.get("run_id") != latest.get("run_id"):
        raise AssertionError("run ID mismatch between latest and manifest")
    if manifest.get("experiment") != "7-5" or manifest.get("status") != "passed":
        raise AssertionError("manifest is not a passed Experiment 7-5 run")

    for record in manifest.get("inputs", []):
        check_record(resolve_relative(REPO_ROOT, record["path"]), record)
    for record in manifest.get("artifacts", []):
        check_record(resolve_relative(run_dir, record["path"]), record)

    retained = load_json(run_dir / "retained_outputs.json")
    if retained.get("test_count") != 5 or retained.get("output_count") != 15:
        raise AssertionError("retained report must contain exactly five tests and fifteen outputs")
    tests = retained.get("tests")
    if not isinstance(tests, list) or [test.get("test_id") for test in tests] != [1, 2, 3, 4, 5]:
        raise AssertionError("retained tests must be ordered 1 through 5")
    if any(set(test.get("outputs", {})) != STAGES for test in tests):
        raise AssertionError("every retained test must have all three stages")

    receipts = load_json(run_dir / "judge_receipts.json")
    calls = receipts.get("calls")
    if receipts.get("credential_headers_retained") is not False:
        raise AssertionError("credential header retention must be explicitly false")
    if not isinstance(calls, list) or len(calls) != 5:
        raise AssertionError("exactly five independent judge receipts are required")
    response_ids: set[str] = set()
    for expected_test_id, call in enumerate(calls, start=1):
        if call.get("test_id") != expected_test_id or call.get("http_status") != 200:
            raise AssertionError("judge calls must be successful and ordered by test ID")
        response_id = call.get("response_id")
        if not isinstance(response_id, str) or not response_id or response_id in response_ids:
            raise AssertionError("judge response IDs must be present and unique")
        response_ids.add(response_id)
        if call.get("latency_ms", 0) <= 0 or call.get("usage", {}).get("total_tokens", 0) <= 0:
            raise AssertionError("judge usage and positive latency must be retained")
        response = call.get("response", {})
        if response.get("id") != response_id or response.get("usage") != call.get("usage"):
            raise AssertionError("copied judge response ID/usage does not match the raw response")
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AssertionError("raw judge response is missing message content") from exc
        if parse_response_content(content) != call.get("judgment"):
            raise AssertionError("normalized judgment does not match raw response content")
        mapping = call.get("blind_map")
        if not isinstance(mapping, dict) or set(mapping) != {"A", "B", "C"}:
            raise AssertionError("judge call is missing the blind label map")
        if set(mapping.values()) != STAGES:
            raise AssertionError("blind map must contain all three model stages")
        request_text = json.dumps(call.get("request"), ensure_ascii=False)
        if any(stage in request_text.lower() for stage in STAGES):
            raise AssertionError("judge request leaks a model-stage name")
        judgment = call.get("judgment", {})
        if set(judgment.get("candidates", {})) != {"A", "B", "C"}:
            raise AssertionError("judge judgment must score A, B, and C")

    contract = load_json(run_dir / "reproduction_contract.json")
    revisions = contract.get("upstream_revisions", {})
    for name, expected in EXPECTED_REVISIONS.items():
        if revisions.get(name, {}).get("revision") != expected:
            raise AssertionError(f"reproduction revision mismatch for {name}")
    boundary = contract.get("historical_evidence_boundary", {})
    if boundary.get("historical_upstream_revisions_retained") is not False:
        raise AssertionError("historical upstream-revision boundary is not explicit")
    policy = contract.get("checkpoint_policy", {})
    if policy.get("distributed_with_book") is not False or policy.get("acceptance_artifact") is not False:
        raise AssertionError("checkpoint policy does not match the book distribution contract")

    summary = load_json(run_dir / "summary.json")
    acceptance = summary.get("acceptance", {})
    if summary.get("status") != "passed" or acceptance.get("passed") is not True:
        raise AssertionError("summary acceptance did not pass")
    required_true = (
        "raw_report_hashed",
        "exactly_five_tests",
        "exactly_fifteen_outputs",
        "all_three_stages_retained",
        "five_independent_blind_judgments",
        "judge_response_ids_usage_and_latency_retained",
        "training_and_evaluation_sources_declared",
        "immutable_future_reproduction_revisions_frozen",
        "historical_revision_boundary_explicit",
        "checkpoints_not_an_acceptance_artifact",
        "korean_gain_comparison_completed",
        "english_retention_comparison_completed",
        "kimchi_failure_explicitly_reported",
    )
    if not all(acceptance.get(name) is True for name in required_true):
        missing = [name for name in required_true if acceptance.get(name) is not True]
        raise AssertionError(f"required acceptance gates failed: {missing}")

    findings = summary.get("scientific_findings", {})
    if not isinstance(findings.get("korean_gain_observed"), bool):
        raise AssertionError("Korean-gain finding is missing")
    if not isinstance(findings.get("english_retention_within_tolerance"), bool):
        raise AssertionError("English-retention finding is missing")
    if findings.get("kimchi_factual_failure_observed") is not True:
        raise AssertionError("material kimchi factual failure is not reported")

    for record in manifest["artifacts"]:
        path = resolve_relative(run_dir, record["path"])
        if path.suffix not in {".json", ".md"}:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                raise AssertionError(f"possible credential in retained artifact: {path.name}")

    return {
        "experiment": "7-5",
        "run_id": latest["run_id"],
        "status": "passed",
        "inputs_verified": len(manifest["inputs"]),
        "artifacts_verified": len(manifest["artifacts"]),
        "judge_receipts_verified": len(calls),
        "outputs_verified": retained["output_count"],
        "manifest_sha256": latest["manifest_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latest", type=Path, default=LATEST_PATH)
    args = parser.parse_args()
    result = validate(args.latest.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
