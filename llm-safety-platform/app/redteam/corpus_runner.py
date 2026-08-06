"""Run Gateway or /v1/classify against public attack corpora.

Usage:
  .venv/bin/python -m app.redteam.corpus_runner \\
    --source configs/evals/attack_corpora/seed_zh_en.yaml
  .venv/bin/python -m app.redteam.corpus_runner \\
    --source configs/evals/attack_corpora/jbb_harmful.csv --mode gateway
  # Faster model eval (one classify call per case):
  SAFETY_CLASSIFIER_URL=http://127.0.0.1:8091/v1/classify \\
  .venv/bin/python -m app.redteam.corpus_runner \\
    --source configs/evals/attack_corpora/jbb_harmful.csv --mode classify
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import urllib.request
from pathlib import Path

import yaml

from app.gateway import SafetyGateway

ROOT = Path(__file__).resolve().parents[2]


def load_cases(path: Path, limit: int | None) -> list[dict]:
    if path.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        cases = list(data.get("cases") or [])
        return cases[:limit] if limit else cases
    if path.suffix == ".csv":
        rows = []
        with path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit is not None and i >= limit:
                    break
                goal = (
                    row.get("goal")
                    or row.get("Goal")
                    or row.get("prompt")
                    or row.get("Prompt")
                    or row.get("text")
                    or ""
                ).strip()
                if not goal:
                    continue
                cat = (
                    row.get("Category")
                    or row.get("category")
                    or row.get("Behavior")
                    or "harmful"
                )
                prefix = "jbb" if "Category" in (reader.fieldnames or []) else "advbench"
                rows.append(
                    {
                        "id": f"{prefix}_{i}",
                        "category": cat,
                        "expect": "block",
                        "text": goal,
                    }
                )
        return rows
    raise SystemExit(f"unsupported source: {path}")


def classify_http(text: str, url: str, timeout: float) -> tuple[str, str | None]:
    body = json.dumps(
        {
            "text": text,
            "categories": [
                "sexual",
                "violence",
                "political",
                "self_harm",
                "harassment",
                "fraud",
                "privacy",
                "disinformation",
                "expert_advice",
                "jailbreak",
            ],
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    decision = str(data.get("decision", "allow"))
    reasons = ";".join(data.get("reasons") or [])
    return decision, reasons or None


def run_gateway(
    cases: list[dict],
    *,
    tenant: str = "t_demo",
    app: str = "customer_bot",
) -> dict:
    """Evaluate cases via SafetyGateway (shim-friendly)."""
    gw = SafetyGateway()
    results = []
    leaks = 0
    for c in cases:
        text = c["text"]
        expect = c.get("expect", "block")
        r = gw.chat(tenant_id=tenant, app_id=app, user_content=text)
        decision, reasons = r.decision, r.blocked_reason
        ok = decision == expect
        if not ok:
            leaks += 1
        results.append(
            {
                "id": c.get("id"),
                "category": c.get("category"),
                "expect": expect,
                "got": decision,
                "ok": ok,
                "reasons": reasons,
                "text": text,
            }
        )
    return {
        "mode": "gateway",
        "case_count": len(cases),
        "leak_rate": leaks / max(1, len(cases)),
        "passed": leaks == 0,
        "blocked": sum(1 for r in results if r["got"] == "block"),
        "results": results,
    }


def main() -> int:
    from app.scanners.content_safety import reset_classifier
    from app.scanners.engine import clear_rules_cache

    clear_rules_cache()
    reset_classifier()

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--source",
        type=Path,
        default=ROOT / "configs/evals/attack_corpora/seed_zh_en.yaml",
    )
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--tenant", default="t_demo")
    ap.add_argument("--app", default="customer_bot")
    ap.add_argument(
        "--expect",
        default=None,
        help="override expected decision for all cases (e.g. allow for benign set)",
    )
    ap.add_argument(
        "--mode",
        choices=("gateway", "classify"),
        default="gateway",
        help="gateway=full SafetyGateway; classify=one POST to SAFETY_CLASSIFIER_URL",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="optional path to write JSON report",
    )
    args = ap.parse_args()
    src = args.source if args.source.is_absolute() else ROOT / args.source
    cases = load_cases(src, args.limit)
    classify_url = os.getenv("SAFETY_CLASSIFIER_URL", "")
    timeout = float(os.getenv("SAFETY_REMOTE_TIMEOUT", "45"))
    gw = SafetyGateway() if args.mode == "gateway" else None
    results = []
    leaks = 0
    for c in cases:
        text = c["text"]
        expect = args.expect or c.get("expect", "block")
        if args.mode == "classify":
            if not classify_url:
                raise SystemExit("SAFETY_CLASSIFIER_URL required for --mode classify")
            decision, reasons = classify_http(text, classify_url, timeout)
        else:
            assert gw is not None
            r = gw.chat(tenant_id=args.tenant, app_id=args.app, user_content=text)
            decision, reasons = r.decision, r.blocked_reason
        ok = decision == expect
        if not ok:
            leaks += 1
        results.append(
            {
                "id": c.get("id"),
                "category": c.get("category"),
                "expect": expect,
                "got": decision,
                "ok": ok,
                "reasons": reasons,
                "text": text,
            }
        )
    report = {
        "source": str(src),
        "mode": args.mode,
        "case_count": len(cases),
        "leak_rate": leaks / max(1, len(cases)),
        "passed": leaks == 0,
        "blocked": sum(1 for r in results if r["ok"] and expect == "block"),
        "results": results,
    }
    # fix blocked count for expect=block corpus
    report["blocked"] = sum(1 for r in results if r["got"] == "block")
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        out = args.out if args.out.is_absolute() else ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        leaks_path = out.with_name(out.stem + "_leaks.json")
        leak_rows = [r for r in results if not r["ok"]]
        leaks_path.write_text(
            json.dumps(leak_rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
