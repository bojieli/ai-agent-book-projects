"""BaxBench-derived adapter harness.

Two modes:
  --self-test    Run reference impls (raw_secure, raw_insecure, pedo) for
                 every adapted scenario through their oracles. No model calls.
  --models ...   Run model-generated handler code (stub).

Usage:
    python -m pedo.eval.baxbench_adapter.harness --self-test
    python -m pedo.eval.baxbench_adapter.harness --self-test --output results.json
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import Any, Callable

from pedo.core.store import ObjectStore

from .oracle import (
    OracleResult,
    run_secret_storage_oracle, run_user_creation_oracle,
    run_shopping_cart_oracle, run_image_transfer_oracle,
)
from .scenarios import (
    register_secret_storage_types, register_user_creation_types,
    register_shopping_cart_types, register_image_transfer_types,
)
from .reference_impls import (
    make_secret_storage_sqlite, make_user_creation_sqlite,
    make_shopping_cart_sqlite, make_image_transfer_sqlite,
    SS_RAW_SECURE, SS_RAW_INSECURE, SS_PEDO,
    UC_RAW_SECURE, UC_RAW_INSECURE, UC_PEDO,
    SC_RAW_SECURE, SC_RAW_INSECURE, SC_PEDO,
    IT_RAW_SECURE, IT_RAW_INSECURE, IT_PEDO,
)


DSN = os.environ.get("DATAGUARDBENCH_DSN", "dbname=pedo_test")


# Each scenario entry: (oracle, register_pedo_types, make_raw_backend,
#                       handler triples [(label, condition, handlers), ...]).
SCENARIOS = [
    {
        "id": "SecretStorage",
        "oracle": run_secret_storage_oracle,
        "register_pedo": register_secret_storage_types,
        "make_raw": make_secret_storage_sqlite,
        "impls": [
            ("raw_secure",   "raw",  SS_RAW_SECURE),
            ("raw_insecure", "raw",  SS_RAW_INSECURE),
            ("pedo",         "pedo", SS_PEDO),
        ],
    },
    {
        "id": "UserCreation",
        "oracle": run_user_creation_oracle,
        "register_pedo": register_user_creation_types,
        "make_raw": make_user_creation_sqlite,
        "impls": [
            ("raw_secure",   "raw",  UC_RAW_SECURE),
            ("raw_insecure", "raw",  UC_RAW_INSECURE),
            ("pedo",         "pedo", UC_PEDO),
        ],
    },
    {
        "id": "ShoppingCart",
        "oracle": run_shopping_cart_oracle,
        "register_pedo": register_shopping_cart_types,
        "make_raw": make_shopping_cart_sqlite,
        "impls": [
            ("raw_secure",   "raw",  SC_RAW_SECURE),
            ("raw_insecure", "raw",  SC_RAW_INSECURE),
            ("pedo",         "pedo", SC_PEDO),
        ],
    },
    {
        "id": "ImageTransfer",
        "oracle": run_image_transfer_oracle,
        "register_pedo": register_image_transfer_types,
        "make_raw": make_image_transfer_sqlite,
        "impls": [
            ("raw_secure",   "raw",  IT_RAW_SECURE),
            ("raw_insecure", "raw",  IT_RAW_INSECURE),
            ("pedo",         "pedo", IT_PEDO),
        ],
    },
]


def make_pedo_backend(register_fn) -> ObjectStore:
    store = ObjectStore(DSN)
    store.clear_all()
    register_fn(store)
    return store


def run_one(scenario: dict, label: str, condition: str, handlers) -> dict:
    if condition == "pedo":
        backend = make_pedo_backend(scenario["register_pedo"])
    else:
        backend = scenario["make_raw"]()
    try:
        r: OracleResult = scenario["oracle"](handlers, backend)
        return {
            "scenario": scenario["id"],
            "implementation": label,
            "condition": condition,
            "func_test_passed": r.func_test_passed,
            "cwes_fired": sorted(r.cwes_fired),
            "notes": r.notes,
        }
    except Exception as e:
        return {
            "scenario": scenario["id"],
            "implementation": label,
            "condition": condition,
            "error": f"{type(e).__name__}: {e}",
        }


def self_test() -> dict:
    results = []
    for scenario in SCENARIOS:
        print(f"\n── {scenario['id']} ──")
        for label, condition, handlers in scenario["impls"]:
            r = run_one(scenario, label, condition, handlers)
            results.append(r)
            if "error" in r:
                print(f"  {label:<14} ERROR: {r['error']}")
            else:
                print(f"  {label:<14} func={r['func_test_passed']!s:<5} "
                      f"cwes_fired={r['cwes_fired']}"
                      f"{'  notes=' + str(r['notes']) if r['notes'] else ''}")
    return {
        "benchmark": "BaxBench-Adapter",
        "version": "0.2",
        "ran_at": datetime.now().isoformat(),
        "scenarios": [s["id"] for s in SCENARIOS],
        "results": results,
    }


def summarize(out: dict) -> str:
    """Compact text summary suitable for paper inclusion."""
    by = {}
    for r in out["results"]:
        if "error" in r:
            continue
        key = (r["scenario"], r["implementation"])
        by[key] = r
    lines = []
    lines.append(f"{'Scenario':<16} {'Impl':<14} {'Func':<6} {'CWEs fired':<28}")
    lines.append("-" * 70)
    for s in out["scenarios"]:
        for impl in ("raw_secure", "raw_insecure", "pedo"):
            r = by.get((s, impl))
            if not r:
                continue
            cwes = ",".join(r["cwes_fired"]) or "(none)"
            func = "yes" if r["func_test_passed"] else "no"
            lines.append(f"{s:<16} {impl:<14} {func:<6} {cwes:<28}")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="BaxBench adapter harness")
    p.add_argument("--self-test", action="store_true",
                   help="Run reference implementations through the oracles.")
    p.add_argument("--output", default=None, help="Output JSON path")
    args = p.parse_args()

    if args.self_test:
        print("=" * 70)
        print("BaxBench-Adapter self-test (4 scenarios)")
        print("=" * 70)
        out = self_test()
        print()
        print(summarize(out))
        if args.output:
            with open(args.output, "w") as f:
                json.dump(out, f, indent=2)
            print(f"\nResults written to {args.output}")
    else:
        print("Model-driven mode not yet wired up. Use --self-test for now.")


if __name__ == "__main__":
    main()
