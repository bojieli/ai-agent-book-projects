"""Real LLM extraction of candidate experience fields from evaluated runs."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Iterable, List


def _parse(text: str) -> Dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


class OpenAIExperienceExtractor:
    def __init__(self, model: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError("Install requirements-lite.txt for the real LLM path") from error
        kwargs = {}
        if os.getenv("OPENAI_BASE_URL"):
            kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]
        self.client = OpenAI(**kwargs)
        self.model = model or os.getenv("LLM_MODEL", "gpt-5.6")

    def extract(self, record: Dict[str, Any]) -> Dict[str, Any]:
        evidence = {
            key: value for key, value in record.items()
            if key not in {"applies_when", "observed_strategies", "mistakes", "exceptions"}
        }
        prompt = f"""Analyze one externally evaluated GAIA-style Agent run.

The environment score is evidence; do not relabel a failed run as successful.
Extract candidate lessons without copying the full trajectory. Return JSON only
with four arrays of concise strings:
- applies_when: future conditions under which the lesson matters
- observed_strategies: actions that helped this run; keep empty when unsupported
- mistakes: actions or omissions linked to partial/failure outcomes
- exceptions: when the apparent lesson should not be applied

Evaluated run:
{json.dumps(evidence, ensure_ascii=False, indent=2)}
"""
        response = self.client.responses.create(model=self.model, input=prompt)
        fields = _parse(response.output_text)
        enriched = dict(record)
        for key in ("applies_when", "observed_strategies", "mistakes", "exceptions"):
            value = fields.get(key, [])
            enriched[key] = [str(item) for item in value] if isinstance(value, list) else []
        return enriched

    def extract_all(self, records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        records = list(records)
        evidence = [
            {key: value for key, value in record.items()
             if key not in {"applies_when", "observed_strategies", "mistakes", "exceptions"}}
            for record in records
        ]
        prompt = f"""Compare these externally evaluated GAIA-style Agent runs.

Return JSON only as {{"records": [...]}}. Each output record must contain id and
four string arrays: applies_when, observed_strategies, mistakes, exceptions.
Use success/partial/failure scores as evidence. Most importantly, normalize a
reusable strategy to exactly the same wording in every non-failed run that
supports it; do not give a failed path positive strategy credit. When the
evidence supports one of these experiment rubric anchors, use its exact text:
- verify the answer with a primary source
- inspect the file type before choosing a parser
- validate the computed total against row count
This lets a later deterministic stage require support from at least two
independent runs and score transfer without another LLM judge. Do not copy the
full trajectory.

Runs:
{json.dumps(evidence, ensure_ascii=False, indent=2)}
"""
        response = self.client.responses.create(model=self.model, input=prompt)
        payload = _parse(response.output_text)
        extracted = {item.get("id"): item for item in payload.get("records", [])}
        enriched_records = []
        for record in records:
            enriched = dict(record)
            fields = extracted.get(record["id"], {})
            for key in ("applies_when", "observed_strategies", "mistakes", "exceptions"):
                value = fields.get(key, [])
                enriched[key] = [str(item) for item in value] if isinstance(value, list) else []
            enriched_records.append(enriched)
        return enriched_records
