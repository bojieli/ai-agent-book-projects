"""Real OpenAI Responses API judge for Experiment 8-1."""

from __future__ import annotations

import json
import os
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

    def __init__(self, model: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from error
        kwargs = {}
        if os.getenv("OPENAI_BASE_URL"):
            kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]
        self.client = OpenAI(**kwargs)
        self.model = model or os.getenv("LLM_MODEL", "gpt-5.6")

    def evaluate(self, trajectory: Dict[str, Any]) -> Iterable[DimensionResult]:
        evidence = {
            "user_request": trajectory.get("user_request"),
            "messages": trajectory.get("messages", []),
            "tool_calls": trajectory.get("tool_calls", []),
            "checked_rules": trajectory.get("process_facts", {}).get("checked_rules", []),
        }
        prompt = f"""You are calibrating a customer-service Agent trajectory.

Evaluate exactly two dimensions:
1. expression_quality: natural, concise, non-repetitive, and directly useful.
2. compliant_flexibility: if the requested path is blocked, find an allowed alternative without breaking policy; do not reward arbitrary rule-breaking.

For each dimension return verdict (pass, fail, or uncertain), score from 0 to 1,
confidence from 0 to 1, and an evidence array citing concrete turn numbers. If
the transcript lacks enough evidence, use uncertain. Return JSON only:
{{"dimensions": [{{"dimension": "expression_quality", "verdict": "pass", "score": 1.0, "confidence": 0.8, "evidence": ["turn 2: ..."]}}, ...]}}

Trajectory evidence:
{json.dumps(evidence, ensure_ascii=False, indent=2)}
"""
        response = self.client.responses.create(model=self.model, input=prompt)
        payload = _json_object(response.output_text)
        by_name = {item.get("dimension"): item for item in payload.get("dimensions", [])}
        results = []
        for name in ("expression_quality", "compliant_flexibility"):
            item = by_name.get(name, {})
            verdict = item.get("verdict", UNCERTAIN)
            if verdict not in {PASS, FAIL, UNCERTAIN}:
                verdict = UNCERTAIN
            results.append(DimensionResult(
                dimension=name,
                layer="llm_rubric",
                verdict=verdict,
                score=float(item.get("score", 0.5)),
                evidence=[str(value) for value in item.get("evidence", ["LLM returned no evidence"])],
                confidence=float(item.get("confidence", 0.5)),
            ))
        return results
