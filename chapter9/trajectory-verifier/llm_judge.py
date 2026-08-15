"""Real OpenAI Responses API judge for Experiment 8-1."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from verifier import DimensionResult, FAIL, PASS, UNCERTAIN


def _json_object(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


class OpenAIQualityJudge:
    """Evaluate open-ended quality while citing concrete dialogue turns."""

    def __init__(self, model: str | None = None, *, evidence_client=None):
        if evidence_client is None:
            from evidence_client import EvidenceChatClient
            evidence_client = EvidenceChatClient("openrouter", model)
        self.client = evidence_client
        self.model = evidence_client.model

    def evaluate(self, trajectory: Dict[str, Any]) -> Iterable[DimensionResult]:
        if not isinstance(trajectory, dict):
            trajectory = {}
        facts = trajectory.get("process_facts")
        if not isinstance(facts, dict):
            facts = {}
        messages = trajectory.get("messages")
        if not isinstance(messages, list):
            messages = []
        tool_calls = trajectory.get("tool_calls")
        if not isinstance(tool_calls, list):
            tool_calls = []
        checked_rules = facts.get("checked_rules")
        if not isinstance(checked_rules, list):
            checked_rules = []
        evidence = {
            "user_request": trajectory.get("user_request"),
            "messages": messages,
            "tool_calls": tool_calls,
            "checked_rules": checked_rules,
        }
        prompt = f"""You are calibrating a customer-service Agent trajectory.

Evaluate exactly two dimensions and keep their scopes separate from the code-checked layers:
1. expression_quality: ONLY whether wording is natural, concise and non-repetitive. Do not fail this dimension for factual, privacy, policy or action errors; those are checked elsewhere. Raw JSON presented to a customer is not natural expression.
2. compliant_flexibility: if the requested business path is blocked, find an allowed alternative without breaking policy. The user's explicit fallback request is evidence of an available alternative. If no business path is blocked, return pass (not uncertain), because no workaround was needed. Do not use this dimension to re-score privacy.

For each dimension return verdict (pass, fail, or uncertain), score from 0 to 1,
confidence from 0 to 1, and an evidence array citing concrete turn numbers. If
the transcript lacks enough evidence, use uncertain. Return JSON only:
{{"dimensions": [{{"dimension": "expression_quality", "verdict": "pass", "score": 1.0, "confidence": 0.8, "evidence": ["turn 2: ..."]}}, ...]}}

Trajectory evidence:
{json.dumps(evidence, ensure_ascii=False, indent=2)}
"""
        response = self.client.complete(
            kind="quality_judge",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        payload = _json_object(response.choices[0].message.content or "{}")
        if isinstance(payload, list):
            raw_dims = payload
        elif isinstance(payload, dict):
            raw_dims = payload.get("dimensions")
        else:
            raw_dims = []
        if not isinstance(raw_dims, list):
            raw_dims = []
        by_name = {
            item.get("dimension"): item
            for item in raw_dims
            if isinstance(item, dict) and item.get("dimension")
        }
        results = []
        for name in ("expression_quality", "compliant_flexibility"):
            item = by_name.get(name) or {}
            verdict = item.get("verdict", UNCERTAIN)
            if verdict not in {PASS, FAIL, UNCERTAIN}:
                verdict = UNCERTAIN
            # dict.get(key, default) returns the default only when the key is
            # ABSENT; a model that emits an explicit JSON null (common for a
            # dimension it marks "uncertain") returns None, and float(None) /
            # iterating None both raise. Coerce non-numeric / non-list values to
            # the neutral defaults instead of crashing the whole trajectory.
            score = item.get("score")
            confidence = item.get("confidence")
            evidence = item.get("evidence")
            clean_evidence = [str(v) for v in evidence if v is not None] if isinstance(evidence, list) else []
            results.append(DimensionResult(
                dimension=name,
                layer="llm_rubric",
                verdict=verdict,
                score=float(score) if isinstance(score, (int, float)) and not isinstance(score, bool) else 0.5,
                evidence=clean_evidence if clean_evidence else ["LLM returned no evidence"],
                confidence=float(confidence) if isinstance(confidence, (int, float)) and not isinstance(confidence, bool) else 0.5,
            ))
        return results
