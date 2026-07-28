"""Reference agents for a longitudinal continual-evolution evaluation."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import re
import time
from typing import Any, Dict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


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
    """A controllable agent used to verify the evaluation harness.

    Profiles:
    - evolving: learns and replaces an older rule with a newer version;
    - append_only: learns an initial rule but cannot revise it;
    - static: never persists feedback.
    """

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
            "memory_version": entry.version if used_memory else None,
            "tokens": tokens,
            "time_ms": elapsed,
        }

    def observe(self, task: Dict[str, Any]) -> Dict[str, Any]:
        signal = task.get("learning_signal")
        if not signal or self.profile == "static":
            return {"updated": False, "tokens": 0, "time_ms": 0}

        rule_id = task["rule_id"]
        current = self.memory.get(rule_id)
        can_write = current is None or (
            self.profile in {"evolving", "llm_evolving"} and int(signal["version"]) > current.version
        )
        if can_write:
            self.memory[rule_id] = MemoryEntry(signal["value"], int(signal["version"]))
            self.token_cost += 25
            self.time_ms += 50
            return {"updated": True, "tokens": 25, "time_ms": 50}
        return {"updated": False, "tokens": 0, "time_ms": 0}

    @property
    def storage_bytes(self) -> int:
        return sum(len(key) + len(entry.value) + 8 for key, entry in self.memory.items())


class OpenAILongitudinalAgent(ReferenceAgent):
    """A real LLM policy with the same external-memory update protocol."""

    ACTIONS = tuple(sorted(set(BASELINE_ACTIONS.values()) | {
        "offer_tax_only_refund", "verify_identity_first",
        "answer_20kg", "answer_23kg", "ask_for_clarification",
    }))

    def __init__(self, model: str | None = None):
        super().__init__("evolving")
        self.profile = "llm_evolving"
        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from error
        kwargs = {}
        if os.getenv("OPENAI_BASE_URL"):
            kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]
        self.client = OpenAI(**kwargs)
        self.model = model or os.getenv("LLM_MODEL", "gpt-5.6")

    @staticmethod
    def _parse(text: str) -> Dict[str, Any]:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            return json.loads(match.group(0)) if match else {}

    def act(self, task: Dict[str, Any]) -> Dict[str, Any]:
        memory = [
            {"rule_id": key, "version": entry.version, "required_action": entry.value}
            for key, entry in sorted(self.memory.items())
        ]
        prompt = f"""Act as an airline-service policy Agent in a longitudinal evaluation.

Choose exactly one action from this vocabulary:
{json.dumps(self.ACTIONS, ensure_ascii=False)}

Use a stored rule only when its rule_id applies. Return JSON only:
{{"action": "one exact vocabulary value", "used_rule_id": "rule id or null"}}

Current external memory:
{json.dumps(memory, ensure_ascii=False, indent=2)}

Task family: {task['family']}
Task rule id: {task['rule_id']}
User request: {task['input']}
"""
        started = time.perf_counter()
        response = self.client.responses.create(model=self.model, input=prompt)
        elapsed = max(1, round((time.perf_counter() - started) * 1000))
        payload = self._parse(response.output_text)
        action = payload.get("action", "invalid_output")
        if action not in self.ACTIONS:
            action = "invalid_output"
        usage = getattr(response, "usage", None)
        tokens = int(getattr(usage, "total_tokens", 0) or 0)
        self.token_cost += tokens
        self.time_ms += elapsed
        used_rule_id = payload.get("used_rule_id")
        entry = self.memory.get(task["rule_id"])
        used_memory = used_rule_id == task["rule_id"] and entry is not None
        return {
            "action": action,
            "used_memory": used_memory,
            "memory_version": entry.version if used_memory else None,
            "tokens": tokens,
            "time_ms": elapsed,
        }
