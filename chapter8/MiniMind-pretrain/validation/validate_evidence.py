#!/usr/bin/env python3
"""Fail-closed validator for Experiment 7-3 retained training evidence."""

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

ARMS = {"original", "qk_norm_muon"}
STAGES = {"pretrain", "sft", "dpo"}
EXPECTED_COUNTS = {
    ("original", "pretrain"): 7,
    ("original", "sft"): 8,
    ("original", "dpo"): 9,
    ("qk_norm_muon", "pretrain"): 7,
    ("qk_norm_muon", "sft"): 9,
    ("qk_norm_muon", "dpo"): 9,
}
EXPECTED_SOURCE_REVISION = "8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795"
EXPECTED_DATASET_REVISION = "84983ed4dec7836d240577760c1d6be5d4cabcf9"
EXPECTED_DATASET_FILES = {
    "pretrain_hq.jsonl": (
        "9801b0d2210c61c2e4bc130f6dc4b3c870698a88d04af8f103c23dd5f0ce2440",
        1_669_750_047,
    ),
    "sft_512.jsonl": (
        "053b7d09574e48a86232e929211434ff9e5016c6ed13312e63687dd52edcbebf",
        7_531_517_862,
    ),
    "dpo.jsonl": (
        "ee934a8a455ccc99d1334d63e1254dd1d64f497fd067cfcbb71e3043f5b46768",
        53_653_322,
    ),
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


def parse_response_content(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    value = json.loads(stripped)
    if not isinstance(value, dict):
        raise AssertionError("judge response content must decode to an object")
    return value


def find_pair(
    retained: dict[str, Any], arm: str, stage: str, keyword: str
) -> dict[str, str]:
    cells = [
        cell
        for cell in retained["cells"]
        if cell.get("arm") == arm and cell.get("stage") == stage
    ]
    if len(cells) != 1:
        raise AssertionError(f"missing or duplicate retained cell: {arm}/{stage}")
    matches = [
        pair
        for pair in cells[0]["pairs"]
        if keyword.lower() in pair.get("prompt", "").lower()
    ]
    if len(matches) != 1:
        raise AssertionError(f"missing or duplicate selected prompt: {arm}/{stage}/{keyword}")
    return matches[0]


def validate(latest_path: Path = LATEST_PATH) -> dict[str, Any]:
    latest = load_json(latest_path)
    if latest.get("experiment") != "7-3" or latest.get("status") != "passed":
        raise AssertionError("latest pointer is not a passed Experiment 7-3 run")
    run_dir = resolve_relative(EXPERIMENT_DIR, latest["run_dir"])
    manifest_path = run_dir / "manifest.json"
    if sha256_file(manifest_path) != latest.get("manifest_sha256"):
        raise AssertionError("latest manifest hash mismatch")
    manifest = load_json(manifest_path)
    if manifest.get("run_id") != latest.get("run_id"):
        raise AssertionError("run ID mismatch between latest and manifest")
    if manifest.get("experiment") != "7-3" or manifest.get("status") != "passed":
        raise AssertionError("manifest is not a passed Experiment 7-3 run")
    if manifest.get("checkpoint_policy") != "not distributed; not an acceptance artifact":
        raise AssertionError("manifest checkpoint policy is incorrect")

    inputs = manifest.get("inputs")
    artifacts = manifest.get("artifacts")
    if not isinstance(inputs, list) or len(inputs) != 5:
        raise AssertionError("manifest must bind exactly five repository inputs")
    if not isinstance(artifacts, list) or len(artifacts) != 5:
        raise AssertionError("manifest must bind exactly five run artifacts")
    for record in inputs:
        check_record(resolve_relative(REPO_ROOT, record["path"]), record)
    for record in artifacts:
        check_record(resolve_relative(run_dir, record["path"]), record)

    retained = load_json(run_dir / "retained_outputs.json")
    report_record = next(
        (record for record in inputs if record.get("path") == retained.get("source_report")),
        None,
    )
    if report_record is None or retained.get("source_report_sha256") != report_record.get("sha256"):
        raise AssertionError("retained source-report hash does not match the manifest input")
    if retained.get("cell_count") != 6 or retained.get("output_count") != 49:
        raise AssertionError("retained report must contain six cells and 49 outputs")
    if set(retained.get("arms", [])) != ARMS or set(retained.get("stages", [])) != STAGES:
        raise AssertionError("retained report arm/stage coverage is incomplete")
    cells = retained.get("cells")
    if not isinstance(cells, list) or len(cells) != 6:
        raise AssertionError("retained cells are malformed")
    combos: set[tuple[str, str]] = set()
    for cell in cells:
        combo = (cell.get("arm"), cell.get("stage"))
        if combo in combos or combo not in EXPECTED_COUNTS:
            raise AssertionError(f"duplicate or unexpected cell: {combo}")
        combos.add(combo)
        pairs = cell.get("pairs")
        if not isinstance(pairs, list) or len(pairs) != EXPECTED_COUNTS[combo]:
            raise AssertionError(f"wrong retained pair count for {combo}")
        if any(not pair.get("prompt") or not pair.get("output") for pair in pairs):
            raise AssertionError(f"empty retained prompt/output in {combo}")
    if combos != set(EXPECTED_COUNTS):
        raise AssertionError("not all arm/stage cells are present")

    receipts_root = load_json(run_dir / "judge_receipts.json")
    if receipts_root.get("credential_headers_retained") is not False:
        raise AssertionError("credential header retention must be explicitly false")
    calls = receipts_root.get("calls")
    if not isinstance(calls, list) or len(calls) != 8:
        raise AssertionError("exactly eight raw judge calls are required")
    response_ids: set[str] = set()
    normalized_rows: dict[str, Any] = {}
    for expected_case_id, call in enumerate(calls, start=1):
        if call.get("case_id") != expected_case_id or call.get("http_status") != 200:
            raise AssertionError("judge calls must be successful and ordered by case ID")
        if call.get("credential_headers_retained") is not False:
            raise AssertionError("per-call credential retention boundary is missing")
        response_id = call.get("response_id")
        if not isinstance(response_id, str) or not response_id or response_id in response_ids:
            raise AssertionError("judge response IDs must be present and unique")
        response_ids.add(response_id)
        if call.get("latency_ms", 0) <= 0 or call.get("usage", {}).get("total_tokens", 0) <= 0:
            raise AssertionError("judge usage and positive latency must be retained")
        raw_response = call.get("response", {})
        if raw_response.get("id") != response_id or raw_response.get("usage") != call.get("usage"):
            raise AssertionError("copied response ID/usage does not match raw response")
        try:
            content = raw_response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AssertionError("raw judge response is missing message content") from exc
        judgment = parse_response_content(content)
        if judgment != call.get("judgment"):
            raise AssertionError("normalized judgment does not match raw response content")
        if str(judgment.get("case_id")) != str(expected_case_id):
            raise AssertionError("raw judgment has the wrong case ID")
        if set(judgment.get("candidates", {})) != {"A", "B"}:
            raise AssertionError("judge judgment must score A and B")
        if judgment.get("winner") not in {"A", "B", "tie"}:
            raise AssertionError("judge winner is invalid")

        mapping = call.get("blind_map")
        if not isinstance(mapping, dict) or set(mapping) != {"A", "B"} or set(mapping.values()) != ARMS:
            raise AssertionError("blind mapping must cover both arms")
        request = call.get("request")
        request_text = json.dumps(request, ensure_ascii=False).lower()
        if "qk_norm_muon" in request_text or '"original"' in request_text:
            raise AssertionError("judge request leaks an arm identity")
        try:
            user_payload = json.loads(request["messages"][1]["content"])
            request_candidates = user_payload["candidates"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise AssertionError("judge request is missing structured candidates") from exc
        if user_payload.get("case_id") != expected_case_id:
            raise AssertionError("judge request case ID mismatch")
        for label, arm in mapping.items():
            retained_pair = find_pair(retained, arm, call["stage"], call["keyword"])
            expected_candidate = {
                "historical_prompt": retained_pair["prompt"],
                "historical_output": retained_pair["output"],
            }
            if request_candidates.get(label) != expected_candidate:
                raise AssertionError("raw judge request is not bound to the retained output")
        normalized_rows[str(expected_case_id)] = {
            mapping[label]: score for label, score in judgment["candidates"].items()
        }

    contract = load_json(run_dir / "reproduction_contract.json")
    future = contract.get("future_reproduction", {})
    source = future.get("source", {})
    dataset = future.get("dataset", {})
    if source.get("revision") != EXPECTED_SOURCE_REVISION:
        raise AssertionError("frozen MiniMind source revision mismatch")
    source_hashes = source.get("file_sha256")
    if not isinstance(source_hashes, dict) or len(source_hashes) < 12:
        raise AssertionError("frozen source file hashes are incomplete")
    if any(not re.fullmatch(r"[0-9a-f]{64}", value) for value in source_hashes.values()):
        raise AssertionError("invalid frozen source SHA-256")
    if dataset.get("revision") != EXPECTED_DATASET_REVISION:
        raise AssertionError("frozen dataset revision mismatch")
    dataset_files = dataset.get("files", {})
    for name, (expected_hash, expected_bytes) in EXPECTED_DATASET_FILES.items():
        record = dataset_files.get(name, {})
        if record.get("lfs_sha256") != expected_hash or record.get("bytes") != expected_bytes:
            raise AssertionError(f"frozen dataset file mismatch: {name}")
    if len(future.get("commands", {})) != 6:
        raise AssertionError("all six reproduction commands are required")
    boundary = contract.get("historical_evidence_boundary", {})
    for key in (
        "historical_source_revision_retained",
        "historical_dataset_hashes_retained",
        "historical_checkpoint_hashes_retained",
        "historical_stepwise_training_logs_retained",
    ):
        if boundary.get(key) is not False:
            raise AssertionError(f"historical provenance boundary is not explicit: {key}")
    mechanisms = contract.get("model_and_training", {}).get("source_verified_mechanisms", {})
    if not mechanisms or not all(value is True for value in mechanisms.values()):
        raise AssertionError("source mechanism assertions are incomplete")
    policy = contract.get("checkpoint_policy", {})
    if policy.get("distributed_with_book") is not False or policy.get("acceptance_artifact") is not False:
        raise AssertionError("checkpoint policy does not match the book contract")

    summary = load_json(run_dir / "summary.json")
    if summary.get("status") != "passed" or summary.get("acceptance", {}).get("passed") is not True:
        raise AssertionError("summary acceptance did not pass")
    acceptance = summary["acceptance"]
    if not all(value is True for key, value in acceptance.items() if key != "passed"):
        failed = [key for key, value in acceptance.items() if key != "passed" and value is not True]
        raise AssertionError(f"required acceptance gates failed: {failed}")
    if summary.get("per_case_arm_scores") != normalized_rows:
        raise AssertionError("summary scores do not match raw judge responses")
    findings = summary.get("scientific_findings", {})
    if not isinstance(findings.get("blind_judge_prefers_qk_norm_muon_overall"), bool):
        raise AssertionError("comparative scientific finding is missing")
    if findings.get("reported_loss_comparison_retained_but_not_independently_recomputed") is not True:
        raise AssertionError("loss-evidence qualification is missing")

    for record in artifacts:
        path = resolve_relative(run_dir, record["path"])
        if path.suffix not in {".json", ".md"}:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                raise AssertionError(f"possible credential in retained artifact: {path.name}")

    return {
        "experiment": "7-3",
        "run_id": latest["run_id"],
        "status": "passed",
        "inputs_verified": len(inputs),
        "artifacts_verified": len(artifacts),
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
