"""Real LLM Coding Agent for generating the Experiment 8-5 candidate."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from evolution import candidate_from_source


def _code(text: str) -> str:
    value = text.strip()
    match = re.match(r"^```(?:python)?\s*(.*?)\s*```$", value, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() + "\n" if match else value + ("" if value.endswith("\n") else "\n")


def generate_with_openai(
    stable_source: str, diagnosis: Dict[str, Any], model: str | None = None
) -> Dict[str, Any]:
    try:
        from openai import OpenAI
    except ImportError as error:
        raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from error
    kwargs = {}
    if os.getenv("OPENAI_BASE_URL"):
        kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]
    client = OpenAI(**kwargs)
    selected_model = model or os.getenv("LLM_MODEL", "gpt-5.6")
    prompt = f"""You are the Coding Agent in a controlled self-modification pipeline.

Modify only the supplied retry-policy module. Preserve both public function
signatures and retry behavior for temporary failures. Permanent failures
(retryable=false or a listed permanent code) must not be retried and must open
the circuit on the first occurrence. Update VERSION to a candidate version.
Return the complete Python module only, with no markdown fence or explanation.

Failure diagnosis:
{json.dumps(diagnosis, ensure_ascii=False, indent=2)}

Stable module:
{stable_source}
"""
    response = client.responses.create(model=selected_model, input=prompt)
    return candidate_from_source(stable_source, _code(response.output_text))
