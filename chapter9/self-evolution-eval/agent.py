"""Reference and real-model agents for the Experiment 8-7 task stream."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import re
import time
from typing import Any, Dict


BASELINE_ACTIONS = {
    "refund": "issue_full_refund",
    "identity": "change_without_verification",
    "baggage": "answer_unknown",
}


@dataclass
class MemoryEntry:
    value: str
    version: int


class ReferenceAgent:
    """Controllable arms used only to unit-test the model-external harness."""

    def __init__(self, profile: str = "evolving"):
        if profile not in {"evolving", "append_only", "static"}:
            raise ValueError(f"unknown profile: {profile}")
        self.profile = profile
        self.memory: Dict[str, MemoryEntry] = {}
        self.token_cost = 0
        self.time_ms = 0

    def act(self, task: Dict[str, Any]) -> Dict[str, Any]:
        entry = self.memory.get(task["rule_id"])
        used_memory = entry is not None and self.profile != "static"
        action = entry.value if used_memory else BASELINE_ACTIONS[task["family"]]
        tokens = 70 if used_memory else 120
        elapsed = 450 if used_memory else 900
        self.token_cost += tokens
        self.time_ms += elapsed
        return {
            "action": action,
            "used_memory": used_memory,
            "memory_available": entry is not None,
            "active_memory_value": entry.value if entry else None,
            "memory_version": entry.version if used_memory else None,
            "tokens": tokens,
            "prompt_tokens": tokens,
            "completion_tokens": 0,
            "provider_reported_cost_usd": None,
            "time_ms": elapsed,
            "response_id": None,
        }

    def observe(self, task: Dict[str, Any]) -> Dict[str, Any]:
        signal = task.get("learning_signal")
        if not signal or self.profile == "static":
            return {
                "updated": False, "candidate_proposed": False, "candidate_valid": None,
                "tokens": 0, "time_ms": 0, "event_order_valid": True,
            }
        rule_id = task["rule_id"]
        current = self.memory.get(rule_id)
        can_write = current is None or (
            self.profile == "evolving" and int(signal["version"]) > current.version
        )
        if can_write:
            self.memory[rule_id] = MemoryEntry(signal["value"], int(signal["version"]))
            self.token_cost += 25
            self.time_ms += 50
        return {
            "updated": can_write,
            "candidate_proposed": True,
            "candidate_valid": signal["value"] == task["expected_action"],
            "tokens": 25 if can_write else 0,
            "time_ms": 50 if can_write else 0,
            "event_order_valid": True,
        }

    @property
    def storage_bytes(self) -> int:
        return sum(len(key) + len(entry.value) + 8 for key, entry in self.memory.items())


class OpenAILongitudinalAgent:
    """A real LLM policy running one of the three external-memory arms.

    The model makes every task decision. The arm-specific update operation is
    deliberately model-external, is invoked only after ``act``, and never sees
    a task's expected action before that action has been recorded.
    """

    ACTIONS = tuple(sorted(set(BASELINE_ACTIONS.values()) | {
        "offer_tax_only_refund", "verify_identity_first",
        "answer_20kg", "answer_23kg", "ask_for_clarification",
    }))

    def __init__(
        self,
        model: str | None = None,
        *,
        arm: str = "evolving",
        provider: str = "ark",
        seed: int = 0,
        run_id: str = "run",
    ):
        if arm not in {"static", "append_only", "evolving"}:
            raise ValueError(f"unknown arm: {arm}")
        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from error
        if provider == "ark":
            key, base, key_env = os.getenv("ARK_API_KEY"), "https://ark.cn-beijing.volces.com/api/v3", "ARK_API_KEY"
            default_model = os.getenv("ARK_MODEL", "doubao-seed-1-6-250615")
        elif provider == "openrouter":
            key, base, key_env = os.getenv("OPENROUTER_API_KEY"), "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"
            default_model = "openai/gpt-4o-mini"
        else:
            key, base, key_env = os.getenv("OPENAI_API_KEY"), None, "OPENAI_API_KEY"
            default_model = "gpt-4o-mini"
        if not key:
            raise RuntimeError(f"{key_env} is required for provider {provider}")
        self.client = OpenAI(api_key=key, base_url=base) if base else OpenAI(api_key=key)
        self.arm = arm
        self.profile = f"llm_{arm}"
        self.provider = provider
        self.model = model or default_model
        self.seed = seed
        self.run_id = run_id
        self.key_env = key_env
        self.endpoint = (base or "https://api.openai.com/v1") + "/chat/completions"
        self.memory: Dict[str, MemoryEntry] = {}
        self.history: list[dict[str, Any]] = []
        self.receipts: list[dict[str, Any]] = []
        self.token_cost = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.time_ms = 0
        self.provider_reported_cost_usd = 0.0
        self.provider_cost_observations = 0
        self._call_index = 0
        self._last_action_finished_ns = 0

    @staticmethod
    def _parse(text: str) -> Dict[str, Any]:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            return json.loads(match.group(0)) if match else {}

    def _memory_view(self) -> list[dict[str, Any]]:
        return [
            {"rule_id": key, "version": entry.version, "required_action": entry.value, "active": True}
            for key, entry in sorted(self.memory.items())
        ]

    def act(self, task: Dict[str, Any]) -> Dict[str, Any]:
        memory = self._memory_view()
        # Only the input-side task fields are serialized. In particular,
        # expected_action and learning_signal stay in the evaluator.
        task_view = {key: task[key] for key in ("id", "phase", "family", "rule_id", "input")}
        prompt = f"""Act as an airline policy executor in a longitudinal experiment.

Company rules in this experiment are arbitrary. Never infer an unstored rule
from general knowledge. If ACTIVE_MEMORY has the exact task rule_id, return its
required_action exactly. Otherwise use the family baseline exactly:
{json.dumps(BASELINE_ACTIONS, sort_keys=True)}

Choose exactly one action from:
{json.dumps(self.ACTIONS)}

Return JSON only:
{{"action":"one vocabulary value","used_rule_id":"exact rule id or null","used_version":"integer or null"}}

ACTIVE_MEMORY:
{json.dumps(memory, ensure_ascii=False, sort_keys=True)}

TASK_INPUT:
{json.dumps(task_view, ensure_ascii=False, sort_keys=True)}
"""
        call_seed = self.seed + self._call_index
        request = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "seed": call_seed,
            "max_tokens": 160,
            "response_format": {"type": "json_object"},
        }
        started_ns = time.time_ns()
        started = time.perf_counter()
        response = self.client.chat.completions.create(**request)
        elapsed = max(1, round((time.perf_counter() - started) * 1000))
        finished_ns = time.time_ns()
        raw = response.model_dump(mode="json", exclude_none=True)
        payload = self._parse(response.choices[0].message.content or "")
        action = payload.get("action", "invalid_output")
        if action not in self.ACTIONS:
            action = "invalid_output"
        usage = raw.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
        native_cost = usage.get("cost")
        self.token_cost += tokens
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.time_ms += elapsed
        if native_cost is not None:
            self.provider_reported_cost_usd += float(native_cost)
            self.provider_cost_observations += 1
        entry = self.memory.get(task["rule_id"])
        used_memory = (
            entry is not None
            and payload.get("used_rule_id") == task["rule_id"]
            and int(payload.get("used_version") or -1) == entry.version
        )
        receipt = {
            "run_id": self.run_id,
            "arm": self.arm,
            "task_id": task["id"],
            "call_index": self._call_index,
            "seed": call_seed,
            "backend": {
                "provider": self.provider,
                "model": self.model,
                "endpoint": self.endpoint,
                "credential_env": self.key_env,
                "credential_value_recorded": False,
            },
            "request": request,
            "response": raw,
            "request_sha256": hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest(),
            "response_sha256": hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest(),
            "started_ns": started_ns,
            "finished_ns": finished_ns,
            "elapsed_ms": elapsed,
        }
        self.receipts.append(receipt)
        self._call_index += 1
        self._last_action_finished_ns = finished_ns
        return {
            "action": action,
            "used_memory": used_memory,
            "memory_available": entry is not None,
            "active_memory_value": entry.value if entry else None,
            "memory_version": entry.version if used_memory else None,
            "tokens": tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "provider_reported_cost_usd": float(native_cost) if native_cost is not None else None,
            "time_ms": elapsed,
            "response_id": raw.get("id"),
        }

    def observe(self, task: Dict[str, Any]) -> Dict[str, Any]:
        observed_ns = time.time_ns()
        signal = task.get("learning_signal")
        if not signal or self.arm == "static":
            return {
                "updated": False,
                "candidate_proposed": False,
                "candidate_valid": None,
                "tokens": 0,
                "time_ms": 0,
                "event_order_valid": observed_ns >= self._last_action_finished_ns,
            }
        entry = MemoryEntry(str(signal["value"]), int(signal["version"]))
        current = self.memory.get(task["rule_id"])
        if self.arm == "append_only":
            # Keep every observation, including a conflicting v2, but never
            # resolve or replace the first active version.
            updated = current is None
        else:
            updated = current is None or entry.version > current.version
        if updated:
            if current is not None:
                for item in self.history:
                    if item["rule_id"] == task["rule_id"] and item.get("active"):
                        item["active"] = False
                        item["status"] = "superseded"
            self.memory[task["rule_id"]] = entry
        self.history.append({
            "rule_id": task["rule_id"],
            "version": entry.version,
            "value": entry.value,
            "active": updated,
            "status": "active" if updated else ("unresolved_conflict" if current and entry.version > current.version else "duplicate"),
            "observed_after_task": task["id"],
            "observed_ns": observed_ns,
        })
        return {
            "updated": updated,
            "candidate_proposed": True,
            "candidate_valid": entry.value == task["expected_action"],
            "tokens": 0,
            "time_ms": 0,
            "event_order_valid": observed_ns >= self._last_action_finished_ns,
        }

    @property
    def storage_bytes(self) -> int:
        if self.arm == "static":
            return 0
        return len(json.dumps(self.history, ensure_ascii=False, sort_keys=True).encode("utf-8"))
