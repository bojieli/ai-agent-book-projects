#!/usr/bin/env python3
"""Probe every backend required by a config without exposing credentials."""

import argparse
import json
import os
import time
from pathlib import Path

from experiment import (
    ChatBackend,
    Chunk,
    EmbeddingBackend,
    EndpointSpec,
    ExperimentRunner,
    execution_config_fingerprint,
    load_config,
    required_readiness_components,
)


def sanitized_error(exc: Exception, key_envs) -> str:
    message = f"{type(exc).__name__}: {exc}"
    for env_name in key_envs:
        secret = os.getenv(env_name, "")
        if secret:
            message = message.replace(secret, "<redacted>")
    return message[:1000]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("default_config.yaml"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    key_envs = {
        data["api_key_env"]
        for section in ("chat_models", "embeddings")
        for data in config[section].values()
    } | {
        data["api_key_env"] for data in config["rerankers"].values() if data.get("api_key_env")
    }
    results = []

    required_chat = {
        config["experiment_6_4"]["main_model"],
        config["experiment_6_11"]["retrieval_judge_model"],
        *config["experiment_6_11"]["main_models"],
        *[
            data["chat_model"]
            for name, data in config["rerankers"].items()
            if name in config["experiment_6_11"]["rerankers"] and data.get("type") == "llm"
        ],
    }
    for name in sorted(required_chat):
        raw = config["chat_models"][name]
        row = {"component": "chat", "name": name, "model": raw.get("model"), "key_env": raw.get("api_key_env")}
        try:
            spec = EndpointSpec.from_dict({"name": name, **raw})
            turn = ChatBackend(spec).complete([{"role": "user", "content": "Reply exactly OK"}])
            row.update(status="ok", latency_ms=turn.latency_ms, key_present=True)
        except Exception as exc:
            row.update(status="error", error=sanitized_error(exc, key_envs), key_present=bool(os.getenv(raw.get("api_key_env", ""))))
        results.append(row)

    required_embeddings = {
        config["experiment_6_4"]["embedding"], *config["experiment_6_11"]["embeddings"]
    }
    for name in sorted(required_embeddings):
        raw = config["embeddings"][name]
        row = {"component": "embedding", "name": name, "model": raw.get("model"), "key_env": raw.get("api_key_env")}
        try:
            spec = EndpointSpec.from_dict({"name": name, **raw})
            backend = EmbeddingBackend(spec)
            vector = backend.embed(["user memory retrieval backend probe"])[0]
            row.update(status="ok", dimensions=len(vector), latency_ms=backend.last_latency_ms, key_present=True)
        except Exception as exc:
            row.update(status="error", error=sanitized_error(exc, key_envs), key_present=bool(os.getenv(raw.get("api_key_env", ""))))
        results.append(row)

    # Reuse the production factory so this verifies the same reranker code path.
    runner = object.__new__(ExperimentRunner)
    runner.config = config
    runner.endpoint_specs = {
        name: EndpointSpec.from_dict({"name": name, **data}) for name, data in config["chat_models"].items()
    }
    chunks = [Chunk("a", "probe", "checking account number 123", 1, 1), Chunk("b", "probe", "weather", 2, 2)]
    required_rerankers = {
        config["experiment_6_4"]["reranker"], *config["experiment_6_11"]["rerankers"]
    }
    for name in sorted(required_rerankers):
        row = {"component": "reranker", "name": name}
        try:
            backend = runner._reranker(name)
            ranked = backend.rerank("checking account", chunks, 2)
            row.update(status="ok", returned=len(ranked), latency_ms=backend.last_latency_ms)
        except Exception as exc:
            row.update(status="error", error=sanitized_error(exc, key_envs))
        results.append(row)

    payload = {
        "schema_version": "2.0",
        "experiment": "6-4/6-11 provider readiness",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config_file": str(args.config),
        "execution_config_fingerprint": execution_config_fingerprint(config, "6-11"),
        "required_components": [
            {"component": component, "name": name}
            for component, name in sorted(required_readiness_components(config))
        ],
        "credentials_redacted": True,
        "probes": results,
        "summary": {
            "ok": sum(row["status"] == "ok" for row in results),
            "error": sum(row["status"] == "error" for row in results),
            "all_required_backends_ready": all(row["status"] == "ok" for row in results),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"]))
    print(f"Wrote sanitized backend readiness evidence to {args.output}")
    return 0 if payload["summary"]["all_required_backends_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
