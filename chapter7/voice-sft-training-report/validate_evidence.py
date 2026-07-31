#!/usr/bin/env python3
"""Fail-closed validator for Experiment 7-6 retained training evidence."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import run_training_report_audit as audit

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
EXPECTED_ARTIFACTS = {
    "upstream_orpheus.ipynb",
    "upstream_sesame.ipynb",
    "orpheus_output_1.wav",
    "sesame_output_1.wav",
    "sesame_output_2.wav",
    "sesame_output_3.wav",
    "source_audit.json",
    "judge_receipts.json",
    "summary.json",
    "report.md",
}
FORBIDDEN_SECRET_PATTERNS = (
    re.compile(r"(?i)authorization\s*[:=]\s*bearer"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_-]{16,}"),
    re.compile(r"\b(?:sk|ak)-[A-Za-z0-9_-]{16,}\b"),
)


class EvidenceError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise EvidenceError(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON {path}: {exc}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def verify_manifest_inputs(records: list[dict[str, Any]]) -> None:
    expected = set(audit.LOCAL_SOURCE_PATHS)
    if {record.get("path") for record in records} != expected:
        fail("manifest input set differs from the frozen local-source contract")
    verify_records(records, base=REPO_ROOT, expected_names=expected)


def verify_failed_attempts(records: list[dict[str, Any]]) -> None:
    expected = set(audit.FAILED_ATTEMPT_PATHS)
    if {record.get("path") for record in records} != expected:
        fail("failed-attempt set differs from the retained failure contract")
    verify_records(records, base=REPO_ROOT, expected_names=expected)


def verify_notebooks_and_audio(run_dir: Path, source_audit: dict[str, Any]) -> None:
    expected_audio = []
    for name, spec in audit.NOTEBOOKS.items():
        path = run_dir / f"upstream_{name}.ipynb"
        raw = path.read_bytes()
        if audit.git_blob_sha1(raw) != spec["blob_sha1"]:
            fail(f"{name}: immutable notebook Git blob mismatch")
        try:
            notebook = audit.load_notebook_bytes(raw, name)
            training = audit.training_record(notebook, name)
            environment = audit.environment_record(notebook, name)
            audio_rows = audit.extracted_audio(notebook, name)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            fail(f"{name}: invalid retained notebook: {exc}")
        recorded = source_audit["upstream_executed_notebooks"].get(name, {})
        if recorded.get("training") != training or recorded.get("environment") != environment:
            fail(f"{name}: notebook-derived training evidence mismatch")
        for row in audio_rows:
            path = run_dir / row["filename"]
            if not path.is_file() or path.read_bytes() != row["audio_bytes"]:
                fail(f"{name}: extracted WAV does not match notebook bytes")
            expected_audio.append(
                {key: value for key, value in row.items() if key != "audio_bytes"}
            )
    if source_audit.get("extracted_audio") != expected_audio:
        fail("source audit audio records do not derive from the immutable notebooks")


def decode_audio_url(value: str) -> bytes:
    match = re.fullmatch(r"data:audio/wav;base64,([A-Za-z0-9+/=]+)", value)
    if not match:
        fail("judge request contains a malformed audio data URL")
    try:
        return base64.b64decode(match.group(1), validate=True)
    except ValueError as exc:
        fail(f"judge audio base64 is invalid: {exc}")


def validate_receipts(
    run_dir: Path, receipts_doc: dict[str, Any], summary: dict[str, Any]
) -> list[dict[str, Any]]:
    if (
        receipts_doc.get("schema_version") != "exp7-6-judge-receipts-v1"
        or receipts_doc.get("experiment") != "7-6"
        or receipts_doc.get("credential_headers_retained") is not False
    ):
        fail("wrong judge receipt schema or credential boundary")
    receipts = receipts_doc.get("calls")
    if not isinstance(receipts, list) or [row.get("track") for row in receipts] != [
        "orpheus",
        "sesame",
    ]:
        fail("judge receipts must cover Orpheus and Sesame in canonical order")
    response_ids = []
    for receipt in receipts:
        track = receipt["track"]
        if (
            receipt.get("provider") != "mistral"
            or receipt.get("credential_env") != "MISTRAL_API_KEY"
            or receipt.get("credential_headers_retained") is not False
        ):
            fail(f"{track}: wrong judge provider or credential metadata")
        if (
            receipt.get("http_status") != 200
            or not isinstance(receipt.get("latency_ms"), (int, float))
            or receipt["latency_ms"] <= 0
        ):
            fail(f"{track}: invalid transport evidence")
        request = receipt.get("request")
        if (
            not isinstance(request, dict)
            or request.get("model") != summary["judge"]["model"]
            or request.get("temperature") != 0
            or request.get("response_format") != {"type": "json_object"}
        ):
            fail(f"{track}: malformed deterministic judge request")
        messages = request.get("messages")
        if not isinstance(messages, list) or len(messages) != 1:
            fail(f"{track}: malformed judge messages")
        content = messages[0].get("content")
        if not isinstance(content, list):
            fail(f"{track}: judge content is missing")
        request_audio = [
            decode_audio_url(part.get("input_audio", ""))
            for part in content
            if isinstance(part, dict) and part.get("type") == "input_audio"
        ]
        audio_map = receipt.get("audio_map")
        if not isinstance(audio_map, dict):
            fail(f"{track}: audio map is missing")
        expected_audio = [(run_dir / filename).read_bytes() for filename in audio_map.values()]
        if request_audio != expected_audio:
            fail(f"{track}: raw request audio differs from retained WAVs")
        response = receipt.get("response")
        response_id = receipt.get("response_id")
        if (
            not isinstance(response, dict)
            or response.get("id") != response_id
            or not isinstance(response_id, str)
            or not response_id
        ):
            fail(f"{track}: raw response ID mismatch")
        usage = receipt.get("usage")
        if (
            response.get("usage") != usage
            or not isinstance(usage, dict)
            or not isinstance(usage.get("total_tokens"), int)
            or usage["total_tokens"] <= 0
        ):
            fail(f"{track}: raw response usage mismatch")
        try:
            raw_content = response["choices"][0]["message"]["content"]
            if isinstance(raw_content, list):
                raw_content = "".join(
                    str(item.get("text", "")) for item in raw_content if isinstance(item, dict)
                )
            parsed = audit.extract_json_object(str(raw_content))
            audit.validate_judgment(track, parsed)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            fail(f"{track}: invalid raw judge response: {exc}")
        if parsed != receipt.get("judgment"):
            fail(f"{track}: normalized judgment is not derived from the raw response")
        response_ids.append(response_id)
    if len(set(response_ids)) != 2:
        fail("judge response IDs are not unique")
    return receipts


def scan_credentials(run_dir: Path) -> None:
    for path in run_dir.iterdir():
        if not path.is_file() or path.suffix not in {".json", ".md", ".ipynb"}:
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
        manifest.get("schema_version") != "exp7-6-manifest-v1"
        or manifest.get("experiment") != "7-6"
        or manifest.get("status") != "passed"
    ):
        fail("wrong or non-passing Experiment 7-6 manifest")
    if manifest.get("checkpoint_policy") != "not distributed; not an acceptance artifact":
        fail("checkpoint policy was weakened")
    if (
        not isinstance(manifest.get("inputs"), list)
        or not isinstance(manifest.get("failed_attempts"), list)
        or not isinstance(manifest.get("artifacts"), list)
    ):
        fail("manifest hash records are missing")
    verify_manifest_inputs(manifest["inputs"])
    verify_failed_attempts(manifest["failed_attempts"])
    verify_records(manifest["artifacts"], base=run_dir, expected_names=EXPECTED_ARTIFACTS)

    source_audit = load_json(run_dir / "source_audit.json")
    if (
        source_audit.get("schema_version") != "exp7-6-source-audit-v1"
        or source_audit.get("experiment") != "7-6"
    ):
        fail("wrong source-audit schema")
    verify_notebooks_and_audio(run_dir, source_audit)
    try:
        recomputed_source_audit = audit.build_source_audit(run_dir)
    except (KeyError, TypeError, ValueError, OSError) as exc:
        fail(f"source audit does not recompute: {exc}")
    if source_audit != recomputed_source_audit:
        fail("source audit differs from frozen local/upstream evidence")

    summary = load_json(run_dir / "summary.json")
    if summary.get("schema_version") != "exp7-6-summary-v1" or summary.get("status") != "passed":
        fail("summary is not a passing Experiment 7-6 report")
    receipts_doc = load_json(run_dir / "judge_receipts.json")
    receipts = validate_receipts(run_dir, receipts_doc, summary)
    recomputed_summary = audit.summarize(source_audit, receipts)
    if summary != recomputed_summary:
        fail("summary metrics or acceptance gates do not recompute")
    if manifest.get("acceptance") != summary.get("acceptance") or not all(
        summary["acceptance"].values()
    ):
        fail("manifest and summary acceptance gates differ")

    report = (run_dir / "report.md").read_text(encoding="utf-8")
    if (
        report != audit.render_report(summary)
        or "Status: **passed**" not in report
        or "mechanism labels are reversed" not in report
    ):
        fail("rendered report is stale or omits the negative result")
    scan_credentials(run_dir)

    if verify_latest:
        latest = load_json(audit.LATEST_PATH)
        if (
            latest.get("schema_version") != "exp7-6-latest-v1"
            or latest.get("experiment") != "7-6"
            or latest.get("run_id") != manifest.get("run_id")
            or latest.get("status") != "passed"
        ):
            fail("latest pointer does not identify this passing run")
        if latest.get("manifest_sha256") != sha256_file(run_dir / "manifest.json"):
            fail("latest pointer manifest SHA-256 mismatch")
        if (HERE / latest.get("run_dir", "")).resolve() != run_dir:
            fail("latest pointer resolves to another run")

    return {
        "experiment": "7-6",
        "status": "passed",
        "run_id": manifest["run_id"],
        "notebooks": 2,
        "loss_rows": 358,
        "audio_files": 4,
        "judge_receipts": len(receipts),
        "inputs": len(manifest["inputs"]),
        "failed_attempts": len(manifest["failed_attempts"]),
        "artifacts": len(manifest["artifacts"]),
        "manifest_sha256": sha256_file(run_dir / "manifest.json"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--no-latest", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.run_dir is None:
        latest = load_json(audit.LATEST_PATH)
        run_dir = HERE / latest.get("run_dir", "")
    else:
        run_dir = args.run_dir
    try:
        result = validate_run(run_dir, verify_latest=not args.no_latest)
    except EvidenceError as exc:
        print(
            json.dumps(
                {"experiment": "7-6", "status": "failed", "error": str(exc)},
                indent=2,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
