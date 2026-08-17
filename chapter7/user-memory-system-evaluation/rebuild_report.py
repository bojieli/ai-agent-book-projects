#!/usr/bin/env python3
"""Rebuild aggregate/report metadata from saved live trajectory records.

This performs no model calls and never invents records. It is useful when report
logic changes (for example, the stricter core-dimension success gate) while the
underlying expensive API answers and judge dimension scores remain valid.
"""

import argparse
import hashlib
import json
import time
from pathlib import Path

from experiment import RunRecord, load_config, reprice_legacy_64_records, save_report


CORE_SUCCESS_DIMENSIONS = ("precision", "recall", "reasoning")
ACCOUNTING_FIELDS = {
    "cost_usd",
    "cost_by_currency",
    "unpriced_tokens",
    "cached_input_tokens",
    "unpriced_requests",
    "cost_accounting",
}


def canonical_non_accounting_hash(records: list[RunRecord]) -> str:
    payload = [
        {
            key: value
            for key, value in vars(record).items()
            if key not in ACCOUNTING_FIELDS
        }
        for record in records
    ]
    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("live_config.yaml"))
    parser.add_argument(
        "--reprice-legacy-7-4",
        action="store_true",
        help=(
            "Cover legacy Kimi usage with dated native-CNY list prices. Legacy cached-token counts "
            "were not saved, so all unpriced Kimi input uses the uncached rate."
        ),
    )
    args = parser.parse_args()

    source = json.loads(args.source.read_text(encoding="utf-8"))
    records = [RunRecord(**row) for row in source.get("records", [])]
    non_accounting_hash_before = canonical_non_accounting_hash(records)
    config = load_config(args.config)
    repricing = None
    if args.reprice_legacy_7_4:
        if source.get("experiment") != "7-4":
            parser.error("--reprice-legacy-7-4 requires an Experiment 7-4 source")
        repricing = reprice_legacy_64_records(
            records,
            config,
            source_generated_at_utc=source.get("generated_at_utc"),
        )
    for record in records:
        if record.status != "ok":
            record.success = False
            continue
        record.success = (
            not record.hallucination_veto
            and all(record.rubric_dimensions.get(name, 0) >= 3 for name in CORE_SUCCESS_DIMENSIONS)
        )
    non_accounting_hash_after = canonical_non_accounting_hash(records)
    if non_accounting_hash_before != non_accounting_hash_after:
        raise RuntimeError(
            "canonical non-accounting record hash changed; refusing to write a derived report"
        )
    save_report(args.output, source["experiment"], records, config)
    rebuilt = json.loads(args.output.read_text(encoding="utf-8"))
    rebuilt["evidence_lineage"] = {
        "source_file": str(args.source),
        "source_api_generated_at_utc": source.get("generated_at_utc"),
        "report_rebuilt_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "transformation": (
            "No API records were added or removed. Aggregates/run-scope metadata were rebuilt and "
            "success was recomputed from saved rubric dimensions using the documented >=3 core gate. "
            + (
                "Legacy unpriced Kimi usage was covered using dated native-CNY list prices; all legacy "
                "input was conservatively treated as uncached because cached-token counts were not saved."
                if repricing else "No cost repricing was requested."
            )
        ),
        "repricing": repricing,
        "trajectory_record_count_preserved": len(records),
        "canonical_non_accounting_sha256_before": non_accounting_hash_before,
        "canonical_non_accounting_sha256_after": non_accounting_hash_after,
        "canonical_non_accounting_records_preserved": True,
        "canonical_hash_excluded_fields": sorted(ACCOUNTING_FIELDS),
    }
    args.output.write_text(json.dumps(rebuilt, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Rebuilt {len(records)} saved trajectories into {args.output}; no model calls made")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
