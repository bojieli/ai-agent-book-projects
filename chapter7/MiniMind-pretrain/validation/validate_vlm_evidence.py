#!/usr/bin/env python3
"""Fail-closed validator for the canonical Experiment 7-4 evidence package."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import run_vlm_training_report_audit as audit

HERE = Path(__file__).resolve().parent
EXPERIMENT_DIR = HERE.parent
REPO_ROOT = EXPERIMENT_DIR.parents[1]
EXPECTED_ARTIFACTS = {
    "retained_outputs.json",
    "reproduction_contract.json",
    "judge_receipts.json",
    "summary.json",
    "report.md",
}
FORBIDDEN_SECRET_PATTERNS = (
    re.compile(r"(?i)authorization\s*[:=]\s*bearer"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
)


class EvidenceError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise EvidenceError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON {path}: {exc}")


def resolve_repo_path(relative: str) -> Path:
    path = (REPO_ROOT / relative).resolve()
    if not path.is_relative_to(REPO_ROOT.resolve()):
        fail(f"input escapes repository: {relative}")
    return path


def verify_records(
    records: list[dict[str, Any]], *, base: Path, expected_names: set[str] | None = None
) -> None:
    names = []
    for record in records:
        if set(record) != {"path", "sha256", "bytes"}:
            fail(f"malformed hash record: {record}")
        relative = record["path"]
        if not isinstance(relative, str) or not relative:
            fail("hash record path is missing")
        path = (base / relative).resolve()
        if not path.is_relative_to(base.resolve()):
            fail(f"hash record escapes base: {relative}")
        if not path.is_file() or path.is_symlink():
            fail(f"hashed file missing or symlinked: {path}")
        if path.stat().st_size != record["bytes"]:
            fail(f"byte count mismatch: {path}")
        if sha256_file(path) != record["sha256"]:
            fail(f"SHA-256 mismatch: {path}")
        names.append(relative)
    if len(names) != len(set(names)):
        fail("duplicate hash records")
    if expected_names is not None and set(names) != expected_names:
        fail(f"artifact set mismatch: {set(names)} != {expected_names}")


def decode_image_url(url: str) -> bytes:
    match = re.fullmatch(r"data:image/[A-Za-z0-9.+-]+;base64,([A-Za-z0-9+/=]+)", url)
    if not match:
        fail("judge request does not contain an exact base64 image data URL")
    try:
        return base64.b64decode(match.group(1), validate=True)
    except ValueError as exc:
        fail(f"invalid image base64: {exc}")


def validate_receipts(
    retained: dict[str, Any], receipts_doc: dict[str, Any], summary: dict[str, Any]
) -> list[dict[str, Any]]:
    if (
        receipts_doc.get("schema_version") != "exp7-4-judge-receipts-v1"
        or receipts_doc.get("experiment") != "7-4"
    ):
        fail("wrong judge receipt schema or experiment")
    if receipts_doc.get("credential_headers_retained") is not False:
        fail("judge receipt must state that credential headers were not retained")
    receipts = receipts_doc.get("calls")
    if not isinstance(receipts, list) or [row.get("image") for row in receipts] != list(
        audit.IMAGE_FILES
    ):
        fail("judge calls must cover the eight images exactly in canonical order")
    response_ids: list[str] = []
    for receipt in receipts:
        image = receipt["image"]
        if receipt.get("image_source_filename") != audit.IMAGE_FILES[image]:
            fail(f"wrong source image filename for {image}")
        if receipt.get("image_sha256") != audit.IMAGE_SHA256[image]:
            fail(f"wrong image SHA-256 for {image}")
        if not isinstance(receipt.get("image_bytes"), int) or receipt["image_bytes"] <= 0:
            fail(f"missing image byte count for {image}")
        if receipt.get("provider") != "ark" or receipt.get("credential_env") != "ARK_API_KEY":
            fail(f"wrong provider metadata for {image}")
        if receipt.get("credential_headers_retained") is not False:
            fail(f"credential header retention is not false for {image}")
        if (
            receipt.get("http_status") != 200
            or not isinstance(receipt.get("latency_ms"), (int, float))
            or receipt["latency_ms"] <= 0
        ):
            fail(f"invalid transport evidence for {image}")
        if receipt.get("blind_seed") != audit.BLIND_SEED or receipt.get(
            "blind_map"
        ) != audit.blind_mapping(image):
            fail(f"blind mapping mismatch for {image}")
        if set(receipt["blind_map"]) != set(audit.LABELS) or set(
            receipt["blind_map"].values()
        ) != set(audit.CONFIGS):
            fail(f"blind map is not a bijection for {image}")

        request = receipt.get("request")
        if not isinstance(request, dict) or request.get("temperature") != 0:
            fail(f"malformed deterministic judge request for {image}")
        if request.get("response_format") != {"type": "json_object"}:
            fail(f"judge request is not fail-closed JSON mode for {image}")
        if request.get("model") != summary["judge"]["model"]:
            fail(f"judge model mismatch for {image}")
        messages = request.get("messages")
        if (
            not isinstance(messages, list)
            or len(messages) != 2
            or messages[0].get("role") != "system"
        ):
            fail(f"malformed judge messages for {image}")
        user_content = messages[1].get("content")
        if not isinstance(user_content, list) or len(user_content) != 2:
            fail(f"image-aware user content missing for {image}")
        image_part, text_part = user_content
        if (
            image_part.get("type") != "image_url"
            or image_part.get("image_url", {}).get("detail") != "high"
        ):
            fail(f"high-detail image input missing for {image}")
        raw_image = decode_image_url(image_part["image_url"].get("url", ""))
        if (
            hashlib.sha256(raw_image).hexdigest() != audit.IMAGE_SHA256[image]
            or len(raw_image) != receipt["image_bytes"]
        ):
            fail(f"request image bytes do not match pinned input for {image}")
        if text_part.get("type") != "text" or not isinstance(text_part.get("text"), str):
            fail(f"judge text input missing for {image}")
        try:
            prompt = json.loads(text_part["text"])
        except json.JSONDecodeError as exc:
            fail(f"judge text is not canonical JSON for {image}: {exc}")
        expected_outputs = audit.outputs_for_image(retained, image)
        expected_candidates = {
            label: expected_outputs[config] for label, config in receipt["blind_map"].items()
        }
        if prompt.get("image") != image or prompt.get("candidates") != expected_candidates:
            fail(f"anonymous candidate text does not match retained outputs for {image}")
        prompt_text = json.dumps(prompt, ensure_ascii=False)
        if any(config in prompt_text for config in audit.CONFIGS):
            fail(f"judge prompt leaks configuration identity for {image}")

        response = receipt.get("response")
        response_id = receipt.get("response_id")
        if (
            not isinstance(response, dict)
            or response.get("id") != response_id
            or not isinstance(response_id, str)
            or not response_id
        ):
            fail(f"raw response ID mismatch for {image}")
        if (
            response.get("usage") != receipt.get("usage")
            or not isinstance(receipt.get("usage", {}).get("total_tokens"), int)
            or receipt["usage"]["total_tokens"] <= 0
        ):
            fail(f"raw response usage mismatch for {image}")
        try:
            parsed = audit.extract_json_object(response["choices"][0]["message"]["content"])
            audit.validate_judgment(parsed, image)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            fail(f"invalid raw judgment for {image}: {exc}")
        if parsed != receipt.get("judgment"):
            fail(f"normalized judgment is not derived from raw response for {image}")
        response_ids.append(response_id)
    if len(set(response_ids)) != len(audit.IMAGE_FILES):
        fail("judge response IDs are not unique")
    return receipts


def scan_credentials(run_dir: Path) -> None:
    for path in run_dir.iterdir():
        if not path.is_file() or path.suffix not in {".json", ".md"}:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"possible credential material in {path.name}")


def validate_run(run_dir: Path, *, verify_latest: bool = True) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        fail(f"missing run directory: {run_dir}")
    if any(path.is_symlink() for path in run_dir.iterdir()):
        fail("run directory contains a symlink")
    manifest = load_json(run_dir / "manifest.json")
    if (
        manifest.get("schema_version") != "exp7-4-manifest-v1"
        or manifest.get("experiment") != "7-4"
    ):
        fail("wrong manifest schema or experiment")
    if (
        manifest.get("status") != "passed"
        or manifest.get("checkpoint_policy") != "not distributed; not an acceptance artifact"
    ):
        fail("manifest does not declare a passed checkpoint-free report")
    if not isinstance(manifest.get("inputs"), list) or not isinstance(
        manifest.get("artifacts"), list
    ):
        fail("manifest hash lists are missing")
    for record in manifest["inputs"]:
        path = resolve_repo_path(record.get("path", ""))
        if (
            not path.is_file()
            or path.is_symlink()
            or path.stat().st_size != record.get("bytes")
            or sha256_file(path) != record.get("sha256")
        ):
            fail(f"input hash mismatch: {record.get('path')}")
    if len({record["path"] for record in manifest["inputs"]}) != len(manifest["inputs"]):
        fail("duplicate manifest inputs")
    verify_records(manifest["artifacts"], base=run_dir, expected_names=EXPECTED_ARTIFACTS)

    retained = load_json(run_dir / "retained_outputs.json")
    current_retained = audit.parse_retained_outputs()
    if retained != current_retained:
        fail("retained outputs do not exactly match the content-hashed book report")
    if retained.get("cell_count") != 8 or retained.get("output_count") != 64:
        fail("retained output coverage is incomplete")
    if retained.get("configs") != list(audit.CONFIGS) or retained.get("images") != list(
        audit.IMAGE_FILES
    ):
        fail("retained configuration/image contract changed")

    contract = load_json(run_dir / "reproduction_contract.json")
    if contract != audit.reproduction_contract():
        fail("reproduction contract differs from frozen source/data/model pins")
    if contract["checkpoint_policy"]["acceptance_artifact"] is not False:
        fail("checkpoint policy was weakened")

    summary = load_json(run_dir / "summary.json")
    if summary.get("schema_version") != "exp7-4-summary-v1" or summary.get("status") != "passed":
        fail("summary is not a passed Experiment 7-4 report")
    receipts_doc = load_json(run_dir / "judge_receipts.json")
    receipts = validate_receipts(retained, receipts_doc, summary)
    recomputed = audit.summarize(retained, receipts, contract)
    if summary != recomputed:
        fail("summary metrics or acceptance gates do not recompute exactly")
    if manifest.get("acceptance") != summary.get("acceptance") or not all(
        summary["acceptance"].values()
    ):
        fail("manifest/summary acceptance mismatch")

    report = (run_dir / "report.md").read_text(encoding="utf-8")
    if (
        "Status: **passed**" not in report
        or summary["scientific_findings"]["top_configuration"] not in report
    ):
        fail("rendered report does not bind the recomputed result")
    scan_credentials(run_dir)

    if verify_latest:
        latest = load_json(audit.LATEST_PATH)
        if latest.get("schema_version") != "exp7-4-latest-v1" or latest.get("experiment") != "7-4":
            fail("latest pointer has wrong schema or experiment")
        if latest.get("run_id") != manifest.get("run_id") or latest.get("status") != "passed":
            fail("latest pointer does not identify this passed run")
        if latest.get("manifest_sha256") != sha256_file(run_dir / "manifest.json"):
            fail("latest pointer manifest SHA-256 mismatch")
        expected_run_dir = EXPERIMENT_DIR / latest.get("run_dir", "")
        if expected_run_dir.resolve() != run_dir:
            fail("latest pointer resolves to another run")

    return {
        "experiment": "7-4",
        "status": "passed",
        "run_id": manifest["run_id"],
        "cells": retained["cell_count"],
        "outputs": retained["output_count"],
        "images": len(audit.IMAGE_FILES),
        "judge_receipts": len(receipts),
        "artifacts": len(manifest["artifacts"]),
        "inputs": len(manifest["inputs"]),
        "manifest_sha256": sha256_file(run_dir / "manifest.json"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir", type=Path, help="Run directory; defaults to validation/latest_vlm.json"
    )
    parser.add_argument(
        "--no-latest",
        action="store_true",
        help="Skip latest-pointer binding (for deliberate tamper tests only)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.run_dir is None:
        latest = load_json(audit.LATEST_PATH)
        run_dir = EXPERIMENT_DIR / latest.get("run_dir", "")
    else:
        run_dir = args.run_dir
    try:
        result = validate_run(run_dir, verify_latest=not args.no_latest)
    except EvidenceError as exc:
        print(
            json.dumps(
                {"experiment": "7-4", "status": "failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
