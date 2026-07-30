#!/usr/bin/env python3
"""Real local-model benchmark for Experiment 3-3.

Compares the existing regex engine, local Qwen3 through Ollama, and a hybrid
regex-first/LLM-second path on labeled logs.  Gold values are intentionally
fictional.  Metrics are exact-span precision/recall, residual leakage, utility,
and latency; the local model emits type/location/confidence JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import ollama

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from experiment_utils import jsonable, write_campaign_evidence

import regex_sanitizer


CASES = [
    {"id": "structured_cn", "text": "客户身份证号11010519491231002X，手机号13800138000。", "gold": [("cn_id_card", "11010519491231002X"), ("cn_phone", "13800138000")]},
    {"id": "structured_us", "text": "SSN 123-45-6789; Visa 4111 1111 1111 1111; ticket 123-45-6780 is not an SSN.", "gold": [("us_ssn", "123-45-6789"), ("credit_card", "4111 1111 1111 1111")]},
    {"id": "credentials", "text": "postgres://alice:S3cr3t-Pass@db.internal:5432/prod failed; retry token=not-a-real-token-but-secret", "gold": [("password", "S3cr3t-Pass"), ("secret", "not-a-real-token-but-secret")]},
    {"id": "natural_password", "text": "用户说：我网银的登录口令是‘Blue moon over river 77’，请帮我记住。", "gold": [("password", "Blue moon over river 77")]},
    {"id": "address", "text": "Please ship replacements to apartment 3B, 1847 Maple Street, Portland, Oregon 97205 after Tuesday.", "gold": [("address", "apartment 3B, 1847 Maple Street, Portland, Oregon 97205")]},
    {"id": "medical", "text": "Chart note: patient Maria Chen, MRN-789456, was diagnosed with stage II breast cancer and starts doxorubicin Friday.", "gold": [("medical_record", "MRN-789456"), ("medical_diagnosis", "stage II breast cancer"), ("treatment", "doxorubicin")]},
    {"id": "passport", "text": "Traveler passport P987654321 expires 2027-04-09; booking code P987654320 is unrelated.", "gold": [("passport", "P987654321")]},
    {"id": "financial", "text": "Wire account 4429853327 routing 123006800. Product SKU 4429853328 should remain visible.", "gold": [("bank_account", "4429853327"), ("routing_number", "123006800")]},
    {"id": "email_bearer", "text": "Authorization: Bearer fakeBearerToken1234567890; notify alice.wang@example.com.", "gold": [("bearer_token", "fakeBearerToken1234567890"), ("email", "alice.wang@example.com")]},
    {"id": "negative_numbers", "text": "Metrics: latency 13800138000 ns, build 4111111111111112 vectors, model XR-7003. None identify a person.", "gold": []},
    {"id": "negative_language", "text": "The password field must contain at least 12 characters. Never log a user's real password.", "gold": []},
    {"id": "mixed_context", "text": "Support transcript: 'call me at 13912345678'. Agent replied that order 13912345679 ships tomorrow and wrote password: hunter2xyz.", "gold": [("cn_phone", "13912345678"), ("password", "hunter2xyz")]},
]

SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "value": {"type": "string"},
                    "start": {"type": "integer"},
                    "end": {"type": "integer"},
                    "confidence": {"type": "number"},
                },
                "required": ["type", "value", "start", "end", "confidence"],
            },
        }
    },
    "required": ["findings"],
}

SYSTEM = """You detect sensitive information in logs. Return exact substrings only.
Types include cn_id_card, cn_phone, us_ssn, credit_card, password, secret,
address, medical_record, medical_diagnosis, treatment, passport, bank_account,
routing_number, bearer_token, email, private_key, and api_key. Distinguish a
real disclosed value from a field name, instruction, product code, metric, or
explicit decoy. start/end are zero-based Python slice offsets and confidence is
0..1. Return JSON matching the schema; never redact or paraphrase the value."""


ALIASES = {
    "url_credential": "password",
    "secret_assignment": "secret",
    "us_ssn": "us_ssn",
    "credit_card": "credit_card",
    "cn_id_card": "cn_id_card",
    "cn_phone": "cn_phone",
    "bearer_token": "bearer_token",
    "email": "email",
    "api_key": "api_key",
    "private_key": "private_key",
}


def normalize_findings(text: str, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    occupied = set()
    for finding in findings or []:
        value = str(finding.get("value") or "").strip(" \t\n\r'\"“”‘’")
        if not value:
            continue
        start = int(finding.get("start", -1))
        end = int(finding.get("end", -1))
        if start < 0 or end <= start or text[start:end] != value:
            start = text.find(value)
            end = start + len(value) if start >= 0 else -1
        key = (start, end, value)
        if start < 0 or key in occupied:
            continue
        occupied.add(key)
        out.append({
            "type": str(finding.get("type") or "unknown").lower(),
            "value": value,
            "start": start,
            "end": end,
            "confidence": float(finding.get("confidence", 0.5)),
        })
    return sorted(out, key=lambda x: (x["start"], x["end"]))


def regex_findings(text: str) -> Tuple[List[Dict[str, Any]], float]:
    start = time.perf_counter()
    _, raw = regex_sanitizer.sanitize(text)
    elapsed = (time.perf_counter() - start) * 1000
    findings = [{
        "type": ALIASES.get(x["category"], x["category"]),
        "value": x["value"], "start": x["start"], "end": x["end"], "confidence": 1.0,
    } for x in raw]
    return findings, elapsed


def llm_findings(client: ollama.Client, model: str, text: str, purpose: str, receipts: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float]:
    request = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}],
        "format": SCHEMA,
        "options": {"temperature": 0, "seed": 37, "num_predict": 1200},
        "stream": False,
    }
    started = time.perf_counter()
    response = client.chat(**request)
    latency = (time.perf_counter() - started) * 1000
    raw_text = response["message"]["content"]
    parsed = json.loads(raw_text)
    findings = normalize_findings(text, parsed.get("findings") or [])
    receipts.append({
        "purpose": purpose,
        "provider": "ollama-local",
        "endpoint": "http://127.0.0.1:11434",
        "model": model,
        "request": request,
        "response": jsonable(response),
        "latency_ms": round(latency, 3),
        "usage": {
            "prompt_tokens": response.get("prompt_eval_count"),
            "completion_tokens": response.get("eval_count"),
        },
    })
    return findings, latency


def redact(text: str, findings: List[Dict[str, Any]]) -> str:
    accepted = []
    for finding in sorted(findings, key=lambda x: (-float(x.get("confidence", 0)), x["start"])):
        if any(not (finding["end"] <= x["start"] or finding["start"] >= x["end"]) for x in accepted):
            continue
        accepted.append(finding)
    result = text
    for finding in sorted(accepted, key=lambda x: x["start"], reverse=True):
        result = result[:finding["start"]] + f"[REDACTED_{finding['type'].upper()}]" + result[finding["end"]:]
    return result


def evaluate_case(case: Dict[str, Any], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    gold = {(t, v) for t, v in case["gold"]}
    predicted = {(f["type"], f["value"]) for f in findings}
    # Value equality is decisive; type aliases are also audited separately.
    gold_values = {v for _, v in gold}
    pred_values = {v for _, v in predicted}
    tp_values = gold_values & pred_values
    redacted = redact(case["text"], findings)
    false_redacted_chars = sum(len(f["value"]) for f in findings if f["value"] not in gold_values)
    non_sensitive_chars = max(1, len(case["text"]) - sum(len(v) for v in gold_values))
    return {
        "findings": findings,
        "precision": len(tp_values) / len(pred_values) if pred_values else (1.0 if not gold_values else 0.0),
        "recall": len(tp_values) / len(gold_values) if gold_values else 1.0,
        "typed_exact": len(gold & predicted) / len(gold) if gold else (1.0 if not predicted else 0.0),
        "residual_leaks": [value for value in gold_values if value in redacted],
        "utility": max(0.0, 1.0 - false_redacted_chars / non_sensitive_chars),
        "sanitized_text": redacted,
    }


def aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(rows)
    return {
        "cases": n,
        "mean_precision": sum(r["precision"] for r in rows) / n,
        "mean_recall": sum(r["recall"] for r in rows) / n,
        "mean_typed_exact": sum(r["typed_exact"] for r in rows) / n,
        "residual_leaks": sum(len(r["residual_leaks"]) for r in rows),
        "mean_utility": sum(r["utility"] for r in rows) / n,
        "mean_latency_ms": sum(r["latency_ms"] for r in rows) / n,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Experiment 3-3 real Ollama sanitization benchmark")
    parser.add_argument("--model", default="qwen3:0.6b")
    parser.add_argument("--limit", type=int, default=len(CASES))
    args = parser.parse_args()
    cases = CASES[: args.limit]
    client = ollama.Client()
    model_info = jsonable(client.show(args.model))
    receipts: List[Dict[str, Any]] = []
    results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for index, case in enumerate(cases, start=1):
        regex_hits, regex_ms = regex_findings(case["text"])
        llm_hits, llm_ms = llm_findings(client, args.model, case["text"], f"llm:{case['id']}", receipts)

        regex_redacted = redact(case["text"], regex_hits)
        remaining_hits, hybrid_llm_ms = llm_findings(
            client, args.model, regex_redacted, f"hybrid-after-regex:{case['id']}", receipts
        )
        # Map LLM values from the regex-redacted text back into original text.
        mapped = []
        for finding in remaining_hits:
            start = case["text"].find(finding["value"])
            if start >= 0:
                mapped.append({**finding, "start": start, "end": start + len(finding["value"])})
        hybrid_hits = normalize_findings(case["text"], regex_hits + mapped)

        for strategy, hits, latency in (
            ("regex", regex_hits, regex_ms),
            ("llm", llm_hits, llm_ms),
            ("hybrid", hybrid_hits, regex_ms + hybrid_llm_ms),
        ):
            row = evaluate_case(case, hits)
            row.update({"case_id": case["id"], "strategy": strategy, "latency_ms": round(latency, 3)})
            results[strategy].append(row)
        print(f"[{index}/{len(cases)}] {case['id']} complete")

    summaries = {strategy: aggregate(rows) for strategy, rows in results.items()}
    full = len(cases) == len(CASES) and len(receipts) == len(CASES) * 2
    evidence = {
        "status": "passed" if full else "partial",
        "configuration": {
            "backend": "ollama-local",
            "endpoint": "http://127.0.0.1:11434",
            "model": args.model,
            "model_info": model_info,
            "seed": 37,
            "schema": SCHEMA,
        },
        "acceptance": {
            "local_model": True,
            "qwen3_model": args.model.startswith("qwen3:"),
            "structured_type_location_confidence": True,
            "structured_semistructured_natural_language_cases": len(cases) >= len(CASES),
            "regex_llm_hybrid_compared": set(results) == {"regex", "llm", "hybrid"},
            "leakage_utility_latency_measured": True,
            "passed": full,
        },
        "summary": summaries,
        "dataset": cases,
        "results": dict(results),
    }
    manifest = write_campaign_evidence(HERE, "3-3", evidence, receipts)
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
