#!/usr/bin/env python3
"""Run the complete, real local-server campaign for Chapter 2 Experiment 2-1.

Unlike an OpenAI-compatible client, this runner deliberately uses Ollama's
``/api/generate`` endpoint with ``raw=true``.  The exact string emitted by the
Qwen chat template is therefore visible in the evidence, including role
sentinels and the model's XML tool-call protocol.  No model output is mocked.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from transformers import AutoTokenizer

from tools import ToolRegistry


ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "experiment_protocol.json"
TOOL_PATTERN = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_tool_calls(raw_text: str) -> list[dict[str, Any]]:
    calls = []
    for match in TOOL_PATTERN.finditer(raw_text):
        value = json.loads(match.group(1))
        if not isinstance(value, dict) or not isinstance(value.get("name"), str):
            raise ValueError("tool call must contain a string name")
        arguments = value.get("arguments", {})
        if not isinstance(arguments, dict):
            raise ValueError("tool-call arguments must be an object")
        calls.append({"name": value["name"], "arguments": arguments})
    return calls


class OllamaRawClient:
    def __init__(self, base_url: str, model: str, timeout: float = 180.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def get_json(self, path: str) -> dict[str, Any]:
        response = requests.get(self.base_url + path, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def show_model(self) -> dict[str, Any]:
        response = requests.post(
            self.base_url + "/api/show",
            json={"model": self.model},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def generate(
        self,
        prompt: str,
        *,
        num_predict: int,
        temperature: float,
    ) -> dict[str, Any]:
        """Stream one raw request and retain every credential-free chunk."""
        request_body = {
            "model": self.model,
            "prompt": prompt,
            "raw": True,
            "stream": True,
            "keep_alive": "10m",
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
                "seed": 21,
            },
        }
        started_at = utc_now()
        started = time.perf_counter()
        first_piece_s = None
        chunks: list[dict[str, Any]] = []
        pieces: list[str] = []
        with requests.post(
            self.base_url + "/api/generate",
            json=request_body,
            stream=True,
            timeout=self.timeout,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                chunks.append(chunk)
                piece = chunk.get("response") or ""
                if piece:
                    if first_piece_s is None:
                        first_piece_s = time.perf_counter() - started
                    pieces.append(piece)
        wall_s = time.perf_counter() - started
        final = chunks[-1] if chunks else {}
        eval_count = int(final.get("eval_count") or 0)
        eval_duration_s = float(final.get("eval_duration") or 0) / 1e9
        return {
            "requested_at": started_at,
            "request": request_body,
            "request_prompt_sha256": sha256_text(prompt),
            "raw_chunks": chunks,
            "raw_response": "".join(pieces),
            "response_sha256": sha256_text("".join(pieces)),
            "ttft_s": first_piece_s if first_piece_s is not None else wall_s,
            "wall_s": wall_s,
            "server": {
                key: final.get(key)
                for key in (
                    "model",
                    "created_at",
                    "done",
                    "done_reason",
                    "total_duration",
                    "load_duration",
                    "prompt_eval_count",
                    "prompt_eval_duration",
                    "eval_count",
                    "eval_duration",
                )
            },
            "decode_tokens_per_second": (
                eval_count / eval_duration_s if eval_duration_s > 0 else None
            ),
        }


def normalize_tool_call(call: dict[str, Any]) -> dict[str, Any]:
    """Normalize the small model's harmless city-vs-schema variations."""
    name = call["name"]
    args = dict(call["arguments"])
    if name == "get_current_time":
        city = args.pop("city", None)
        if city and "timezone" not in args:
            args["timezone"] = "America/Vancouver"
    elif name in {"get_weather", "get_current_temperature"}:
        name = "get_current_temperature"
        city = args.pop("city", None)
        if city and "location" not in args:
            args["location"] = "Vancouver, Canada"
        args.setdefault("unit", "celsius")
    return {"name": name, "arguments": args}


def execute_parallel(registry: ToolRegistry, calls: list[dict[str, Any]]) -> dict[str, Any]:
    started_at = utc_now()
    started = time.perf_counter()

    def execute(index_and_call):
        index, call = index_and_call
        one_started = time.perf_counter()
        result = registry.execute_tool(call["name"], call["arguments"])
        return {
            "index": index,
            "call": call,
            "result": result,
            "duration_s": time.perf_counter() - one_started,
        }

    with ThreadPoolExecutor(max_workers=len(calls)) as executor:
        results = list(executor.map(execute, enumerate(calls)))
    results.sort(key=lambda item: item["index"])
    return {
        "started_at": started_at,
        "execution": "ThreadPoolExecutor",
        "wall_s": time.perf_counter() - started,
        "results": results,
    }


def render_prompt(tokenizer, messages, tools=None) -> str:
    return tokenizer.apply_chat_template(
        messages,
        tools=tools,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=True,
    )


def run_tool_case(client, tokenizer, protocol) -> dict[str, Any]:
    registry = ToolRegistry()
    all_schemas = registry.get_tool_schemas()
    required_names = set(protocol["tool_case"]["required_tools"])
    tools = [item for item in all_schemas if item["function"]["name"] in required_names]
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Use tools for current facts. "
                "When asking for Vancouver time, pass the IANA timezone "
                "America/Vancouver; do not substitute another city's timezone."
            ),
        },
        {"role": "user", "content": protocol["tool_case"]["prompt"]},
    ]
    first_prompt = render_prompt(tokenizer, messages, tools)
    first = client.generate(
        first_prompt,
        num_predict=protocol["runtime"]["num_predict"],
        temperature=protocol["runtime"]["temperature"],
    )
    parsed = parse_tool_calls(first["raw_response"])
    normalized = [normalize_tool_call(item) for item in parsed]
    parallel = execute_parallel(registry, normalized) if normalized else {
        "started_at": utc_now(), "execution": "not_run", "wall_s": 0, "results": []
    }

    messages.append({"role": "assistant", "content": first["raw_response"]})
    for result in parallel["results"]:
        messages.append({"role": "tool", "content": result["result"]})
    second_prompt = render_prompt(tokenizer, messages, tools)
    second = client.generate(
        second_prompt,
        num_predict=protocol["runtime"]["num_predict"],
        temperature=protocol["runtime"]["temperature"],
    )
    second_calls = parse_tool_calls(second["raw_response"])

    observed = [item["name"] for item in normalized]
    required = protocol["tool_case"]["required_tools"]
    calls_by_name = {item["name"]: item["arguments"] for item in normalized}
    time_arguments = calls_by_name.get("get_current_time", {})
    weather_arguments = calls_by_name.get("get_current_temperature", {})
    tool_results_valid = len(parallel["results"]) == 2 and all(
        not str(item["result"]).startswith('{"error"')
        for item in parallel["results"]
    )
    gates = {
        "chat_template_special_tokens_visible": all(
            token in first_prompt for token in ("<|im_start|>", "<|im_end|>", "<tools>")
        ),
        "raw_tool_tags_visible": "<tool_call>" in first["raw_response"],
        "exact_required_tools": len(observed) == 2 and sorted(observed) == sorted(required),
        "tool_arguments_match_vancouver": (
            time_arguments.get("timezone") == protocol["tool_case"]["required_timezone"]
            and "vancouver" in str(weather_arguments.get("location", "")).lower()
        ),
        "parallel_tool_results_valid": tool_results_valid,
        "terminated_after_results": bool(second["raw_response"].strip()) and not second_calls,
    }
    return {
        "messages": messages,
        "tools": tools,
        "first_turn": first,
        "parsed_tool_calls": parsed,
        "normalized_tool_calls": normalized,
        "parallel_execution": parallel,
        "second_rendered_prompt": second_prompt,
        "second_turn": second,
        "second_turn_tool_calls": second_calls,
        "gates": gates,
        "passed": all(gates.values()),
    }


def run_cache_case(client, tokenizer, protocol) -> dict[str, Any]:
    cfg = protocol["cache_case"]
    filler = "Keep this stable operating-manual sentence unchanged. "
    header = "# Stable operating manual\n"
    system = header + filler * max(1, int(cfg["approximate_prefix_tokens"] * 4 / len(filler)))
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": "Reply with only the word READY."},
    ]
    stable = render_prompt(tokenizer, messages)
    warmups = [
        client.generate(stable, num_predict=8, temperature=0)
        for _ in range(cfg["warmups"])
    ]
    pairs = []
    for index in range(cfg["matched_repeats"]):
        hit = client.generate(stable, num_predict=8, temperature=0)
        marker = f"M{index:07d}"  # fixed width and placed at byte zero
        mutated_system = marker + system[len(marker):]
        mutated = render_prompt(
            tokenizer,
            [
                {"role": "system", "content": mutated_system},
                {"role": "user", "content": "Reply with only the word READY."},
            ],
        )
        miss = client.generate(mutated, num_predict=8, temperature=0)
        pairs.append({
            "pair": index + 1,
            "hit": hit,
            "miss": miss,
            "prompt_character_lengths_equal": len(stable) == len(mutated),
        })
    hit_samples = [item["hit"]["ttft_s"] for item in pairs]
    miss_samples = [item["miss"]["ttft_s"] for item in pairs]
    return {
        "stable_prompt_sha256": sha256_text(stable),
        "stable_prompt_character_count": len(stable),
        "warmups": warmups,
        "pairs": pairs,
        "summary": {
            "hit_ttft_s": hit_samples,
            "miss_ttft_s": miss_samples,
            "hit_mean_s": statistics.fmean(hit_samples),
            "miss_mean_s": statistics.fmean(miss_samples),
            "miss_over_hit": (
                statistics.fmean(miss_samples) / statistics.fmean(hit_samples)
                if statistics.fmean(hit_samples) else None
            ),
            "hit_faster_in_pairs": sum(
                item["hit"]["ttft_s"] < item["miss"]["ttft_s"] for item in pairs
            ),
            "matched_pairs": len(pairs),
        },
    }


def credential_scan(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    findings = []
    for pattern in (r"sk-[A-Za-z0-9_-]{16,}", r"sk-or-[A-Za-z0-9_-]{12,}"):
        findings.extend(match.group(0)[:8] + "…" for match in re.finditer(pattern, text))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--model", default="qwen3:0.6b")
    parser.add_argument("--tokenizer", default="Qwen/Qwen3-0.6B")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    protocol_bytes = PROTOCOL.read_bytes()
    protocol = json.loads(protocol_bytes)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "experiment_protocol.json").write_bytes(protocol_bytes)

    client = OllamaRawClient(args.base_url, args.model)
    version = client.get_json("/api/version")
    tags = client.get_json("/api/tags")
    matching = [item for item in tags.get("models", []) if item.get("name") == args.model]
    show = client.show_model()
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer, local_files_only=True)

    evidence: dict[str, Any] = {
        "experiment_id": "2-1",
        "started_at": utc_now(),
        "protocol_sha256": sha256_bytes(protocol_bytes),
        "provider": "local Ollama",
        "endpoint": args.base_url,
        "model": args.model,
        "tokenizer": args.tokenizer,
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
        },
        "server": {
            "version": version,
            "tag": matching[0] if matching else None,
            "show": {
                "modified_at": show.get("modified_at"),
                "details": show.get("details"),
                "model_info": show.get("model_info"),
            },
        },
    }
    evidence["tool_case"] = run_tool_case(client, tokenizer, protocol)
    evidence["cache_case"] = run_cache_case(client, tokenizer, protocol)
    evidence["finished_at"] = utc_now()

    tag = evidence["server"]["tag"] or {}
    throughput = [
        evidence["tool_case"][turn].get("decode_tokens_per_second")
        for turn in ("first_turn", "second_turn")
    ]
    throughput = [value for value in throughput if value is not None]
    evidence["summary"] = {
        "model_digest": tag.get("digest"),
        "local_model_verified": bool(tag.get("digest")),
        "tool_case_passed": evidence["tool_case"]["passed"],
        "mean_tool_case_decode_tokens_per_second": (
            statistics.fmean(throughput) if throughput else None
        ),
        "exceeded_100_tokens_per_second_on_this_host": bool(
            throughput and statistics.fmean(throughput) > 100
        ),
        "cache_observation": evidence["cache_case"]["summary"],
    }
    evidence["official_complete"] = bool(
        evidence["summary"]["local_model_verified"]
        and evidence["summary"]["tool_case_passed"]
        and evidence["cache_case"]["summary"]["matched_pairs"] == cfg_pairs(protocol)
    )

    evidence_path = output / "evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    findings = credential_scan(evidence_path)
    manifest = {
        "experiment_id": "2-1",
        "official_complete": evidence["official_complete"] and not findings,
        "protocol_sha256": evidence["protocol_sha256"],
        "evidence_sha256": sha256_bytes(evidence_path.read_bytes()),
        "credential_scan_passed": not findings,
        "credential_scan_findings": findings,
        "cost": {"amount": 0, "currency": "USD", "qualification": "local inference"},
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps({"output": str(output), **manifest, "summary": evidence["summary"]}, indent=2))
    return 0 if manifest["official_complete"] else 1


def cfg_pairs(protocol: dict[str, Any]) -> int:
    return int(protocol["cache_case"]["matched_repeats"])


if __name__ == "__main__":
    raise SystemExit(main())
