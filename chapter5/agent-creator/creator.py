"""Experiment 5-13: an Agent that creates and validates another Agent."""

from __future__ import annotations

import json
import hashlib
import os
import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from openai import OpenAI

from validator import validate_agent


ROOT = Path(__file__).resolve().parent
REFERENCE = ROOT / "reference_agent"
DEFAULT_PROTOCOL = ROOT / "experiment_protocol.json"
ALLOWED_TEMPLATE_FILES = {"domain_spec.json"}
REQUIRED_SCRATCH_FILES = {
    "agent.py", "domain_tools.py", "main.py", "system_prompt.md", "tools.json",
    "requirements.txt", "tests/test_contract.py", "tests/test_domain_tools.py", "README.md",
}
SCRATCH_FILE_GROUPS = (
    ("domain_tools.py",),
    ("tools.json",),
    ("agent.py",),
    ("main.py",),
    ("tests/test_contract.py",),
    ("tests/test_domain_tools.py",),
    ("system_prompt.md", "requirements.txt", "README.md"),
)
SCRATCH_CHECKPOINT = "scratch_generation_checkpoint.json"
SCRATCH_CHECKPOINT_CALLS = "creator_calls.checkpoint.json"


@dataclass(frozen=True)
class ResolvedBackend:
    """A real OpenAI-compatible endpoint used by creator and generated Agents."""

    provider: str
    client: OpenAI
    model: str
    api_key: str
    base_url: str | None

    def generated_agent_env(self) -> dict[str, str]:
        """Expose this endpoint through the standard environment contract.

        Scratch-mode output is model-generated and may only understand the
        conventional OPENAI_* variables.  Aliasing a resolved compatible
        endpoint here lets both comparison arms use the *same* real model.
        Clearing OpenRouter prevents generated code from selecting a stale
        router key merely because one exists in the parent shell.
        """

        return {
            "OPENAI_API_KEY": self.api_key,
            "OPENAI_BASE_URL": self.base_url or "https://api.openai.com/v1",
            "OPENAI_MODEL": self.model,
            "OPENROUTER_API_KEY": "",
            "OPENROUTER_MODEL": "",
            "AGENT_PROVIDER": "openai",
        }


def resolve_client() -> ResolvedBackend:
    requested = os.getenv("AGENT_CREATOR_PROVIDER", "auto").strip().casefold()
    aliases = {"kimi": "moonshot", "volcengine": "ark", "doubao": "ark"}
    requested = aliases.get(requested, requested)
    if requested not in {"auto", "moonshot", "ark", "openai", "openrouter"}:
        raise RuntimeError(
            "AGENT_CREATOR_PROVIDER must be auto, moonshot/kimi, ark, openai, or openrouter"
        )

    candidates: list[tuple[str, str | None, str | None, str | None]] = [
        (
            "moonshot",
            os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY"),
            os.getenv("MOONSHOT_BASE_URL") or os.getenv("KIMI_BASE_URL") or "https://api.moonshot.cn/v1",
            os.getenv("AGENT_CREATOR_MODEL") or os.getenv("KIMI_MODEL") or "kimi-k3",
        ),
        (
            "ark",
            os.getenv("ARK_API_KEY"),
            os.getenv("ARK_BASE_URL") or "https://ark.cn-beijing.volces.com/api/v3",
            os.getenv("AGENT_CREATOR_MODEL") or os.getenv("ARK_MODEL") or os.getenv("ARK_ENDPOINT"),
        ),
        (
            "openai",
            os.getenv("OPENAI_API_KEY"),
            os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
            os.getenv("AGENT_CREATOR_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-5.6-luna",
        ),
        (
            "openrouter",
            os.getenv("OPENROUTER_API_KEY"),
            "https://openrouter.ai/api/v1",
            os.getenv("AGENT_CREATOR_MODEL") or os.getenv("OPENROUTER_MODEL") or "openai/gpt-5.6-luna",
        ),
    ]
    for provider, api_key, base_url, model in candidates:
        if requested not in {"auto", provider}:
            continue
        if api_key and model:
            request_timeout = float(os.getenv("AGENT_CREATOR_REQUEST_TIMEOUT", "600"))
            if request_timeout < 60:
                raise RuntimeError("AGENT_CREATOR_REQUEST_TIMEOUT must be at least 60 seconds")
            return ResolvedBackend(
                provider=provider,
                client=OpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    timeout=request_timeout,
                    # The creator records and controls retries itself.  Hidden SDK
                    # retries would make raw request accounting and checkpoints
                    # incomplete.
                    max_retries=0,
                ),
                model=model,
                api_key=api_key,
                base_url=base_url,
            )
    wanted = "a usable real endpoint" if requested == "auto" else requested
    raise RuntimeError(f"No credentials/model configured for {wanted}")


def _json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("model response must be a JSON object")
    return value


@dataclass
class GenerationStats:
    strategy: str
    model: str
    prompt_tokens: int | None
    completion_tokens: int | None
    generation_s: float
    model_calls: int = 1
    repair_attempts: int = 0
    cached_prompt_tokens: int | None = 0
    transport_failures: int = 0
    usage_complete: bool = True


def load_protocol(path: Path = DEFAULT_PROTOCOL) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get("experiment") != "5-13":
        raise ValueError("experiment protocol must be an Experiment 5-13 object")
    return value, hashlib.sha256(raw).hexdigest()


def _usage_cost(usage: dict[str, Any], pricing: dict[str, Any]) -> dict[str, Any]:
    prompt = int(usage.get("prompt_tokens") or 0)
    cached = int(usage.get("cached_prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    cached = min(max(cached, 0), prompt)
    uncached = prompt - cached
    cost = (
        uncached * float(pricing["uncached_input_per_million"])
        + cached * float(pricing["cached_input_per_million"])
        + completion * float(pricing["output_per_million"])
    ) / 1_000_000
    usage_complete = usage.get("usage_complete") is not False
    return {
        "prompt_tokens": prompt,
        "cached_prompt_tokens": cached,
        "uncached_prompt_tokens": uncached,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
        "requests": int(usage.get("requests") or 0),
        "cost": round(cost, 9),
        "currency": pricing["currency"],
        "pricing_as_of": pricing["as_of"],
        "pricing_source_url": pricing["source_url"],
        "all_usage_priced": usage_complete,
        "cost_qualification": (
            "complete observed provider usage priced in native currency"
            if usage_complete
            else "observed-usage lower bound; at least one failed request had unknown usage"
        ),
    }


class AgentCreator:
    def __init__(self, client: Any, model: str):
        self.client = client
        self.model = model
        self.call_records: list[dict[str, Any]] = []

    def _ask(
        self,
        prompt: str,
        *,
        purpose: str = "creator_generation",
        max_tokens: int = 12000,
    ) -> tuple[dict[str, Any], GenerationStats]:
        started = time.perf_counter()
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior Agent engineer. Return one JSON object only. "
                    "Never include credentials. Generated code must be complete, typed, tested, "
                    "use standard role/tool-call messages, preserve tool results, cap iterations, "
                    "and read model/API configuration from environment variables."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        kwargs: dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=1 if any(tag in self.model.casefold() for tag in ("kimi-", "gpt-5")) else 0,
            max_tokens=max_tokens,
        )
        prompt_tokens = 0
        completion_tokens = 0
        cached_prompt_tokens = 0
        usage_seen = False
        model_calls = 0
        parse_errors: list[str] = []
        response_format_enabled = True
        transport_failures = 0
        for attempt in range(1, 4):
            response = None
            for transport_attempt in range(1, 4):
                request_started = time.perf_counter()
                try:
                    response = self.client.chat.completions.create(**kwargs)
                    break
                except Exception as exc:
                    message = str(exc).casefold()
                    unsupported_format = response_format_enabled and any(
                        tag in message
                        for tag in ("response_format", "json_object", "unsupported", "not support")
                    )
                    retryable = type(exc).__name__ in {
                        "APITimeoutError",
                        "APIConnectionError",
                        "InternalServerError",
                        "RateLimitError",
                    }
                    self.call_records.append(
                        {
                            "call_index": len(self.call_records) + 1,
                            "purpose": purpose,
                            "logical_attempt": attempt,
                            "transport_attempt": transport_attempt,
                            "request": {
                                "model": self.model,
                                "messages": json.loads(json.dumps(messages, ensure_ascii=False)),
                                "response_format": kwargs.get("response_format"),
                                "temperature": kwargs.get("temperature"),
                                "max_tokens": kwargs.get("max_tokens"),
                            },
                            "response": None,
                            "usage": None,
                            "error": {
                                "type": type(exc).__name__,
                                "message": str(exc)[:2000],
                                "retryable": retryable,
                                "usage_known": False,
                            },
                            "duration_s": round(time.perf_counter() - request_started, 3),
                            "duration_from_operation_start_s": round(
                                time.perf_counter() - started, 3
                            ),
                        }
                    )
                    if unsupported_format:
                        kwargs.pop("response_format", None)
                        response_format_enabled = False
                        continue
                    if not retryable or transport_attempt == 3:
                        raise
                    transport_failures += 1
            if response is None:  # pragma: no cover - defensive; exceptions raise above
                raise RuntimeError("creator request ended without a response")
            model_calls += 1
            usage = getattr(response, "usage", None)
            prompt_details = getattr(usage, "prompt_tokens_details", None)
            if usage is not None:
                usage_seen = True
                prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
                completion_tokens += getattr(usage, "completion_tokens", 0) or 0
                cached_prompt_tokens += getattr(prompt_details, "cached_tokens", 0) or 0
            content = response.choices[0].message.content or "{}"
            self.call_records.append(
                {
                    "call_index": len(self.call_records) + 1,
                    "purpose": purpose,
                    "logical_attempt": attempt,
                    "transport_attempt": transport_attempt,
                    "request": {
                        "model": self.model,
                        "messages": json.loads(json.dumps(messages, ensure_ascii=False)),
                        "response_format": kwargs.get("response_format"),
                        "temperature": kwargs.get("temperature"),
                        "max_tokens": kwargs.get("max_tokens"),
                    },
                    "response": {
                        "id": getattr(response, "id", None),
                        "model": getattr(response, "model", self.model),
                        "finish_reason": getattr(response.choices[0], "finish_reason", None),
                        "content": content,
                    },
                    "usage": {
                        "prompt_tokens": getattr(usage, "prompt_tokens", None),
                        "cached_prompt_tokens": getattr(prompt_details, "cached_tokens", None),
                        "completion_tokens": getattr(usage, "completion_tokens", None),
                    },
                    "error": None,
                    "duration_s": round(time.perf_counter() - request_started, 3),
                    "duration_from_operation_start_s": round(time.perf_counter() - started, 3),
                }
            )
            try:
                payload = _json_object(content)
                return payload, GenerationStats(
                    strategy="",
                    model=self.model,
                    prompt_tokens=prompt_tokens if usage_seen else None,
                    completion_tokens=completion_tokens if usage_seen else None,
                    generation_s=round(time.perf_counter() - started, 3),
                    model_calls=model_calls,
                    cached_prompt_tokens=cached_prompt_tokens if usage_seen else None,
                    transport_failures=transport_failures,
                    usage_complete=transport_failures == 0,
                )
            except (json.JSONDecodeError, ValueError) as exc:
                parse_errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
                if attempt == 3:
                    break
                # Do not echo a potentially huge/truncated response back into the
                # context. Ask for a fresh compact envelope and account for both
                # calls in the efficiency comparison.
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "The prior response was not a complete parseable JSON object "
                            f"({type(exc).__name__}). Start over; do not continue it. Return the "
                            "same complete requested object, but keep the whole response below "
                            "6,000 tokens by using concise code and no duplicated explanation."
                        ),
                    }
                )
        raise ValueError(
            "model returned no parseable JSON object after 3 real calls: "
            + " | ".join(parse_errors)
        )

    @staticmethod
    def _safe_files(payload: dict[str, Any], allowed: set[str]) -> dict[str, str]:
        files = payload.get("files")
        if not isinstance(files, dict):
            # Code models use a few semantically equivalent envelope labels.
            # Accept one explicit mapping wrapper, but never relax the path
            # allowlist applied below.
            wrappers = [
                payload.get(key)
                for key in ("artifacts", "outputs", "generated_files")
                if isinstance(payload.get(key), dict)
            ]
            if len(wrappers) == 1:
                files = wrappers[0]
            # Code-oriented models sometimes honor the requested file mapping but
            # omit the redundant outer ``files`` key.  Accept that wire-shape only
            # when every top-level key is itself an allowed path; the same path
            # traversal and allowlist checks below still apply.
            elif payload and set(payload).issubset(allowed):
                files = payload
            else:
                raise ValueError("model response must contain a files object")
        clean: dict[str, str] = {}
        for raw_path, content in files.items():
            path = PurePosixPath(raw_path)
            if path.is_absolute() or ".." in path.parts or str(path) not in allowed:
                raise ValueError(f"model attempted disallowed file: {raw_path}")
            # A JSON file is occasionally returned as a nested JSON value instead
            # of a JSON-encoded string.  Serializing that value is lossless and
            # does not weaken the executable-file content checks.
            if path.suffix == ".json" and isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False, indent=2)
            if not isinstance(content, str):
                raise ValueError(f"file content must be text: {raw_path}")
            clean[str(path)] = content
        return clean

    @staticmethod
    def _write_files(output: Path, files: dict[str, str]) -> None:
        for relative, content in files.items():
            path = output / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    @staticmethod
    def _normalize_files(files: dict[str, str]) -> dict[str, str]:
        """Normalize harmless wire-shape variation without altering behavior."""

        result = dict(files)
        if "tools.json" in result:
            value = json.loads(result["tools.json"])
            if isinstance(value, list):
                value = {"tools": value}
            if not isinstance(value, dict) or not isinstance(value.get("tools"), list):
                raise ValueError("tools.json must be an object with a tools array")
            result["tools.json"] = json.dumps(value, ensure_ascii=False, indent=2)
        return result

    @staticmethod
    def _validate_template_spec(
        payload: dict[str, Any], requirements: str
    ) -> dict[str, Any]:
        """Validate the compact specialization consumed by the proven template.

        Template mode intentionally asks the model for domain decisions only.  The
        standard Agent loop, tool dispatcher, CLI, and tests remain deterministic
        reference code, so their token cost and correctness do not depend on the
        model regenerating boilerplate.
        """

        raw = payload.get("specialization")
        if not isinstance(raw, dict):
            raise ValueError("template response must contain a specialization object")
        required_strings = (
            "name",
            "role",
            "sample_task",
            "tool_name",
            "tool_description",
            "record_noun",
            "records_argument",
            "identifier_field",
            "required_field",
            "status_field",
            "evidence_field",
            "approved_label",
            "rejected_label",
        )
        spec: dict[str, Any] = {}
        for key in required_strings:
            value = raw.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"specialization.{key} must be a non-empty string")
            spec[key] = value.strip()
        identifier = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
        for key in (
            "tool_name",
            "records_argument",
            "identifier_field",
            "required_field",
            "status_field",
            "evidence_field",
        ):
            if not identifier.fullmatch(spec[key]):
                raise ValueError(f"specialization.{key} must be a Python/JSON identifier")
        if len(spec["tool_name"]) > 64:
            raise ValueError("specialization.tool_name must be at most 64 characters")

        passing_values = raw.get("passing_values")
        if not isinstance(passing_values, list) or not passing_values or not all(
            isinstance(value, str) and value.strip() for value in passing_values
        ):
            raise ValueError("specialization.passing_values must be a non-empty string list")
        spec["passing_values"] = [value.strip() for value in passing_values]

        remediation = raw.get("remediation_by_status")
        if not isinstance(remediation, dict) or not remediation or not all(
            isinstance(key, str)
            and key.strip()
            and isinstance(value, str)
            and value.strip()
            for key, value in remediation.items()
        ):
            raise ValueError(
                "specialization.remediation_by_status must map statuses to actions"
            )
        spec["remediation_by_status"] = {
            key.strip(): value.strip() for key, value in remediation.items()
        }
        default_remediation = raw.get("default_remediation")
        if not isinstance(default_remediation, str) or not default_remediation.strip():
            raise ValueError("specialization.default_remediation must be non-empty")
        spec["default_remediation"] = default_remediation.strip()
        # The authoritative user requirement is copied verbatim; the model cannot
        # silently narrow it while producing the compact domain overlay.
        spec["requirements"] = requirements
        spec["schema_version"] = "1.0"
        return spec

    @staticmethod
    def _materialize_template(output: Path) -> None:
        spec = json.loads((output / "domain_spec.json").read_text(encoding="utf-8"))
        records_argument = spec["records_argument"]
        identifier_field = spec["identifier_field"]
        required_field = spec["required_field"]
        status_field = spec["status_field"]
        evidence_field = spec["evidence_field"]
        record_noun = spec["record_noun"]
        system_prompt = f"""{spec['role']}

Your complete requirement is:
{spec['requirements']}

Mandatory workflow:
1. Read the structured records supplied by the user.
2. Call `{spec['tool_name']}` exactly once with the complete `{records_argument}` array; do not omit records.
3. Treat a required {record_noun} as passing only when the tool says it passes.
4. Base the final decision, evidence, and remediation only on the tool result and the user's supplied facts.

Never invent a registration ID, facts ID, database prerequisite, hidden tool, or missing-information
request when the user already supplied the records. Never approve when any required record is not in
the configured passing state. In the final answer, state `{spec['approved_label']}` or
`{spec['rejected_label']}`, list every non-passing required record with its exact evidence, and give a
specific remediation action for each one.
"""
        tool = {
            "type": "function",
            "function": {
                "name": spec["tool_name"],
                "description": spec["tool_description"],
                "parameters": {
                    "type": "object",
                    "properties": {
                        records_argument: {
                            "type": "array",
                            "description": (
                                f"The complete list of {record_noun} records supplied by the user."
                            ),
                            "items": {
                                "type": "object",
                                "properties": {
                                    identifier_field: {"type": "string"},
                                    required_field: {"type": "boolean"},
                                    status_field: {"type": "string"},
                                    evidence_field: {"type": "string"},
                                },
                                "required": [
                                    identifier_field,
                                    required_field,
                                    status_field,
                                    evidence_field,
                                ],
                                "additionalProperties": True,
                            },
                        }
                    },
                    "required": [records_argument],
                    "additionalProperties": False,
                },
            },
        }
        readme = f"""# {spec['name']}

This Agent was produced by adapting the proven Experiment 5-13 reference Agent.
Its model-generated artifact is the compact `domain_spec.json`; the bounded Agent
loop, standard tool protocol, dispatcher, CLI, and contract tests are inherited.

## Purpose

{spec['requirements']}

## Run

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=...
export OPENAI_MODEL=...
python main.py --task '{spec['sample_task']}'
```

The tool accepts the complete `{records_argument}` array directly. It does not
require facts to be pre-registered and never stores credentials.
"""
        (output / "system_prompt.md").write_text(system_prompt, encoding="utf-8")
        (output / "tools.json").write_text(
            json.dumps({"tools": [tool]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (output / "README.md").write_text(readme, encoding="utf-8")

    def _generate_template_spec(
        self, requirements: str, prompt: str
    ) -> tuple[dict[str, Any], GenerationStats]:
        total: GenerationStats | None = None
        feedback = ""
        for _attempt in range(1, 4):
            payload, stats = self._ask(
                prompt + feedback,
                purpose="template_specialization",
                max_tokens=2500,
            )
            total = self._add_stats(total, stats)
            try:
                return self._validate_template_spec(payload, requirements), total
            except ValueError as exc:
                feedback = (
                    "\n\nThe previous compact specialization was invalid: "
                    f"{exc}. Return a corrected complete object only."
                )
        raise ValueError("model failed to return a valid template specialization")

    @staticmethod
    def _add_stats(total: GenerationStats | None, current: GenerationStats) -> GenerationStats:
        if total is None:
            return current
        total.prompt_tokens = (
            (total.prompt_tokens or 0) + (current.prompt_tokens or 0)
            if total.prompt_tokens is not None or current.prompt_tokens is not None else None
        )
        total.completion_tokens = (
            (total.completion_tokens or 0) + (current.completion_tokens or 0)
            if total.completion_tokens is not None or current.completion_tokens is not None else None
        )
        total.cached_prompt_tokens = (
            (total.cached_prompt_tokens or 0) + (current.cached_prompt_tokens or 0)
            if total.cached_prompt_tokens is not None or current.cached_prompt_tokens is not None else None
        )
        total.generation_s = round(total.generation_s + current.generation_s, 3)
        total.model_calls += current.model_calls
        total.transport_failures += current.transport_failures
        total.usage_complete = total.usage_complete and current.usage_complete
        return total

    def _generate_valid_envelope(
        self,
        prompt: str,
        allowed: set[str],
        required: set[str],
        *,
        purpose: str = "creator_generation",
        max_tokens: int = 12000,
    ) -> tuple[dict[str, Any], dict[str, str], GenerationStats]:
        total: GenerationStats | None = None
        feedback = ""
        envelope_errors: list[str] = []
        for attempt in range(1, 4):
            payload, stats = self._ask(
                prompt + feedback,
                purpose=purpose,
                max_tokens=max_tokens,
            )
            total = self._add_stats(total, stats)
            try:
                files = self._normalize_files(self._safe_files(payload, allowed))
                missing = required - set(files)
                if missing:
                    raise ValueError(f"response omitted required files: {sorted(missing)}")
                return payload, files, total
            except (ValueError, json.JSONDecodeError) as exc:
                if "disallowed file" in str(exc):
                    raise
                envelope_errors.append(
                    f"attempt {attempt}: {type(exc).__name__}: {exc}; "
                    f"top-level keys={sorted(payload)}"
                )
                feedback = (
                    "\n\nYOUR PREVIOUS RESPONSE FAILED THE ENVELOPE CHECK. "
                    f"Error: {exc}. Top-level keys were {sorted(payload)}. "
                    "Return a fresh complete JSON object with exactly one top-level "
                    "`files` object. "
                    "Do not discuss the error and do not omit any required file. Keep code concise."
                )
        raise ValueError(
            "model failed to return a complete safe file envelope after 3 calls: "
            + " | ".join(envelope_errors)
        )

    @staticmethod
    def _validate_scratch_blueprint(payload: dict[str, Any]) -> dict[str, Any]:
        """Validate the model-authored contract used across staged scratch calls.

        Generating every source file in one JSON response is unnecessarily brittle:
        JSON escaping expands code and some otherwise capable models truncate the
        envelope.  The blueprint is not a reference implementation.  It is the
        scratch model's own architecture decision, carried across smaller real
        generation calls so independently generated files agree on interfaces.
        """

        name = payload.get("name")
        sample_task = payload.get("sample_task")
        design = payload.get("design")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("scratch blueprint name must be non-empty")
        if not isinstance(sample_task, str) or not sample_task.strip():
            raise ValueError("scratch blueprint sample_task must be non-empty")
        if not isinstance(design, dict):
            raise ValueError("scratch blueprint design must be an object")
        required = (
            "tool_name",
            "records_argument",
            "identifier_field",
            "required_field",
            "status_field",
            "evidence_field",
            "passing_value",
            "agent_contract",
            "dispatcher_contract",
            "cli_contract",
            "test_contract",
        )
        for key in required:
            value = design.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"scratch blueprint design.{key} must be non-empty")
        identifier = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
        for key in (
            "tool_name",
            "records_argument",
            "identifier_field",
            "required_field",
            "status_field",
            "evidence_field",
        ):
            if not identifier.fullmatch(str(design[key])):
                raise ValueError(
                    f"scratch blueprint design.{key} must be a Python/JSON identifier"
                )
        return {
            "name": name.strip(),
            "sample_task": sample_task.strip(),
            "design": {key: str(design[key]).strip() for key in required},
        }

    @staticmethod
    def _renumber_calls(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = json.loads(json.dumps(calls, ensure_ascii=False))
        for index, record in enumerate(result, start=1):
            record["call_index"] = index
        return result

    @staticmethod
    def _stats_from_calls(
        calls: list[dict[str, Any]], *, strategy: str, repair_attempts: int = 0
    ) -> GenerationStats:
        prompt_tokens = 0
        cached_prompt_tokens = 0
        completion_tokens = 0
        successful = 0
        failures = 0
        usage_complete = True
        duration_s = 0.0
        model = ""
        for record in calls:
            duration_s += float(record.get("duration_s") or 0)
            request = record.get("request") or {}
            model = str(request.get("model") or model)
            error = record.get("error")
            if error:
                failures += 1
                message = str(error.get("message") or "").casefold()
                # A request rejected before inference solely because the endpoint
                # does not implement response_format has known zero token usage.
                if not any(
                    marker in message
                    for marker in (
                        "response_format",
                        "json_object",
                        "unsupported",
                        "not support",
                    )
                ):
                    usage_complete = False
                continue
            usage = record.get("usage")
            if not isinstance(usage, dict):
                usage_complete = False
                continue
            observed_prompt = usage.get("prompt_tokens")
            observed_completion = usage.get("completion_tokens")
            if not isinstance(observed_prompt, int) or not isinstance(
                observed_completion, int
            ):
                usage_complete = False
                continue
            successful += 1
            prompt_tokens += observed_prompt
            completion_tokens += observed_completion
            observed_cached = usage.get("cached_prompt_tokens")
            if isinstance(observed_cached, int):
                cached_prompt_tokens += observed_cached
        return GenerationStats(
            strategy=strategy,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            generation_s=round(duration_s, 3),
            model_calls=successful,
            repair_attempts=repair_attempts,
            cached_prompt_tokens=cached_prompt_tokens,
            transport_failures=failures,
            usage_complete=usage_complete,
        )

    def _generate_scratch_files(
        self,
        requirements: str,
        checkpoint_dir: Path,
        *,
        resume: bool = False,
    ) -> tuple[dict[str, Any], dict[str, str], GenerationStats]:
        """Generate a standalone Agent from scratch through resumable real calls."""

        blueprint_prompt = f"""Design a standalone tool-using Agent from scratch for:

{requirements}

Do not use or assume any reference implementation. Return exactly one compact JSON object:
{{
  "name": "short Agent name",
  "sample_task": "one executable sample task",
  "design": {{
    "tool_name": "snake_case tool name",
    "records_argument": "array argument in the supplied task",
    "identifier_field": "record identifier field",
    "required_field": "boolean required field",
    "status_field": "status field",
    "evidence_field": "evidence field",
    "passing_value": "the only passing status",
    "agent_contract": "precise bounded ReAct loop and standard message protocol",
    "dispatcher_contract": "precise validation and result contract",
    "cli_contract": "--task/--model input and one-JSON stdout/exit behavior",
    "test_contract": "dependency-injected protocol and domain cases to test"
  }}
}}
For this release-readiness task, map the real gates/id/required/outcome/evidence fields,
accept only `passed`, and require REFUSED when any required gate is non-passing. Keep the
entire blueprint below 900 tokens.
"""
        checkpoint_path = checkpoint_dir / SCRATCH_CHECKPOINT
        calls_path = checkpoint_dir / SCRATCH_CHECKPOINT_CALLS
        requirements_sha256 = hashlib.sha256(requirements.encode("utf-8")).hexdigest()
        call_start = len(self.call_records)
        existing_calls: list[dict[str, Any]] = []
        if resume:
            if not checkpoint_path.is_file() or not calls_path.is_file():
                raise ValueError("scratch resume requires both generation checkpoint files")
            state = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            calls_payload = json.loads(calls_path.read_text(encoding="utf-8"))
            existing_calls = list(calls_payload.get("calls") or [])
            if state.get("requirements_sha256") != requirements_sha256:
                raise ValueError("scratch resume rejected: requirements changed")
            if state.get("model") != self.model:
                raise ValueError("scratch resume rejected: creator model changed")
        else:
            state = {
                "schema_version": "1.0",
                "experiment": "5-13",
                "strategy": "scratch",
                "requirements_sha256": requirements_sha256,
                "model": self.model,
                "status": "in_progress",
                "blueprint": None,
                "blueprint_receipts": [],
                "completed_groups": [],
                "group_receipts": {},
                "file_sha256": {},
                "stats": None,
                "error": None,
            }

        def combined_calls() -> list[dict[str, Any]]:
            return self._renumber_calls(
                [*existing_calls, *self.call_records[call_start:]]
            )

        def persist(status: str, error: str | None = None) -> GenerationStats:
            calls = combined_calls()
            stats = self._stats_from_calls(calls, strategy="scratch")
            state["status"] = status
            state["stats"] = stats.__dict__
            state["error"] = error
            state["updated_at_utc"] = time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
            )
            _write_evidence(checkpoint_path, state, forbidden_secret="")
            _write_evidence(
                calls_path,
                {
                    "schema_version": "1.0",
                    "experiment": "5-13",
                    "strategy": "scratch",
                    "model": self.model,
                    "checkpoint_status": status,
                    "calls": calls,
                },
                forbidden_secret="",
            )
            return stats

        expected_file_sha = dict(state.get("file_sha256", {}))
        mismatched_files: list[str] = []
        for relative, expected_sha in expected_file_sha.items():
            path = checkpoint_dir / relative
            if not path.is_file():
                raise ValueError(f"scratch checkpoint file missing: {relative}")
            observed = hashlib.sha256(path.read_bytes()).hexdigest()
            if observed != expected_sha:
                mismatched_files.append(relative)

        if mismatched_files:
            # A failed enclosing run may still have completed and materialized a
            # model-authored deterministic/live repair.  Those calls are durably
            # retained next to the scratch directory.  Replay only successful,
            # safe repair envelopes over the generation hashes and accept the
            # current files iff every byte is explained by those receipts.  An
            # invalid/truncated repair response changes no expected hash.
            failed_calls_path = checkpoint_dir.parent / "scratch_failed_creator_calls.json"
            if failed_calls_path.is_file() and state.get("status") == "generated":
                failed_payload = json.loads(failed_calls_path.read_text(encoding="utf-8"))
                for record in failed_payload.get("calls") or []:
                    purpose = str(record.get("purpose") or "")
                    response = record.get("response") or {}
                    if not purpose.startswith(
                        ("scratch_deterministic_repair", "scratch_live_repair")
                    ):
                        continue
                    try:
                        repair_payload = _json_object(str(response.get("content") or ""))
                        repaired = self._normalize_files(
                            self._safe_files(repair_payload, REQUIRED_SCRATCH_FILES)
                        )
                    except (json.JSONDecodeError, ValueError):
                        continue
                    for relative, content in repaired.items():
                        expected_file_sha[relative] = hashlib.sha256(
                            content.encode("utf-8")
                        ).hexdigest()
            unexplained = []
            for relative in mismatched_files:
                observed = hashlib.sha256((checkpoint_dir / relative).read_bytes()).hexdigest()
                if observed != expected_file_sha.get(relative):
                    unexplained.append(relative)
            if unexplained:
                raise ValueError(
                    "scratch checkpoint has file changes not explained by retained model repair "
                    f"receipts: {', '.join(sorted(unexplained))}"
                )

        blueprint = state.get("blueprint")
        if blueprint is None:
            feedback = ""
            try:
                for _attempt in range(1, 4):
                    before = len(self.call_records)
                    payload, _stats = self._ask(
                        blueprint_prompt + feedback,
                        purpose="scratch_blueprint",
                        max_tokens=2500,
                    )
                    state["blueprint_receipts"].extend(
                        {
                            "response_id": (record.get("response") or {}).get("id"),
                            "response_model": (record.get("response") or {}).get("model"),
                        }
                        for record in self.call_records[before:]
                        if record.get("response")
                    )
                    try:
                        blueprint = self._validate_scratch_blueprint(payload)
                        state["blueprint"] = blueprint
                        persist("in_progress")
                        break
                    except ValueError as exc:
                        persist("in_progress", f"invalid blueprint: {exc}")
                        feedback = (
                            "\nThe prior blueprint was invalid: "
                            f"{exc}. Return a corrected complete blueprint only."
                        )
            except Exception as exc:
                persist("failed", f"{type(exc).__name__}: {exc}")
                raise
        else:
            blueprint = self._validate_scratch_blueprint(blueprint)
        if blueprint is None:
            persist("failed", "model failed to return a valid scratch blueprint")
            raise ValueError("model failed to return a valid scratch blueprint")

        context_by_group: dict[tuple[str, ...], tuple[str, ...]] = {
            ("domain_tools.py",): (),
            ("tools.json",): (),
            ("agent.py",): ("domain_tools.py", "tools.json"),
            ("main.py",): ("agent.py",),
            ("tests/test_contract.py",): ("agent.py", "main.py"),
            ("tests/test_domain_tools.py",): ("domain_tools.py", "tools.json"),
            ("system_prompt.md", "requirements.txt", "README.md"): ("tools.json",),
        }
        for paths in SCRATCH_FILE_GROUPS:
            group_id = "|".join(paths)
            if group_id in state.get("completed_groups", []):
                continue
            context_paths = context_by_group[paths]
            context_files = {
                path: (checkpoint_dir / path).read_text(encoding="utf-8")
                for path in context_paths
            }
            group_specific = ""
            if paths == ("main.py",):
                group_specific = """
This group is deliberately tiny. `agent.py` already owns the complete CLI and
exports `main`. Make `main.py` a thin executable wrapper that imports and calls
that function; do not duplicate the Agent, tool, parsing, or CLI implementation.
Keep it below 15 physical lines.
"""
            elif paths == ("tests/test_contract.py",):
                group_specific = """
Use dependency-injected fake chat-completion objects. Test the exact standard
assistant.tool_calls -> role=tool protocol, matching tool_call_id, bounded loop,
history order, provider usage aggregation, and CLI result contract.
"""
            elif paths == ("tests/test_domain_tools.py",):
                group_specific = """
Test all-passed approval, required failed/skipped refusal, optional failure,
evidence preservation, malformed records, and unknown tool rejection.
"""
            group_prompt = f"""Implement one file group of a standalone Agent built from scratch.

Authoritative requirement:
{requirements}

The same model already authored this architecture contract:
{json.dumps(blueprint, ensure_ascii=False)}

Previously generated interface context (read-only; keep compatible):
{json.dumps(context_files, ensure_ascii=False)}

Return exactly one JSON object of the form {{"files": {{"path": "complete content"}}}}.
Return exactly these files and no others: {', '.join(paths)}.

The final Agent must define `GeneratedAgent(model=None, client=None)` and
`run(task, history=None, max_iterations=...)`. It must use the current OpenAI client and
`client.chat.completions.create`, standard assistant tool_calls followed by role=tool results with
matching tool_call_id, a bounded for/range loop, argument validation, dependency injection in
deterministic tests, and API/model configuration only from environment or `--model`.
`python main.py --task "..." --model "..." --history-json '[]'` must perform a real model run,
print exactly one JSON object, and exit zero only when `ok` is true. The JSON must preserve the full
credential-free `messages` list and aggregate provider `usage` with prompt_tokens,
cached_prompt_tokens, completion_tokens, and requests. Prior history must remain in exact order.
Never hard-code temperature. Tests must assert protocol, history preservation, usage, and domain
behavior, not placeholders or mocks of the complete experiment. Keep each Python file below 170
lines and this response below 4,500 tokens.
{group_specific}
"""
            before = len(self.call_records)
            try:
                _payload, group_files, _group_stats = self._generate_valid_envelope(
                    group_prompt,
                    set(paths),
                    set(paths),
                    purpose=f"scratch_group:{group_id}",
                    max_tokens=12000,
                )
                self._write_files(checkpoint_dir, group_files)
                for relative in paths:
                    state["file_sha256"][relative] = hashlib.sha256(
                        (checkpoint_dir / relative).read_bytes()
                    ).hexdigest()
                state["completed_groups"].append(group_id)
                state["group_receipts"][group_id] = [
                    {
                        "response_id": (record.get("response") or {}).get("id"),
                        "response_model": (record.get("response") or {}).get("model"),
                        "purpose": record.get("purpose"),
                    }
                    for record in self.call_records[before:]
                    if record.get("response")
                ]
                persist("in_progress")
            except Exception as exc:
                persist(
                    "failed",
                    f"scratch file group {list(paths)} failed: {type(exc).__name__}: {exc}",
                )
                raise ValueError(
                    f"scratch file group {list(paths)} failed: {exc}"
                ) from exc

        files = {
            relative: (checkpoint_dir / relative).read_text(encoding="utf-8")
            for relative in REQUIRED_SCRATCH_FILES
            if (checkpoint_dir / relative).is_file()
        }
        missing = REQUIRED_SCRATCH_FILES - set(files)
        if missing:
            persist("failed", f"staged scratch generation omitted files: {sorted(missing)}")
            raise ValueError(f"staged scratch generation omitted files: {sorted(missing)}")
        stats = persist("generated")
        return blueprint, files, stats

    def _repair_until_deterministic(
        self,
        *,
        strategy: str,
        requirements: str,
        output: Path,
        allowed: set[str],
        stats: GenerationStats,
    ) -> GenerationStats:
        """Use actual compiler/pytest feedback to repair the created Agent."""

        for repair in range(1, 4):
            report = validate_agent(output, timeout=120)
            if report.ok:
                return stats
            current_files = {
                relative: (output / relative).read_text(encoding="utf-8")
                for relative in sorted(allowed)
                if (output / relative).is_file() and relative != "README.md"
            }
            repair_prompt = f"""Repair a generated Agent for this requirement:

{requirements}

Generation strategy: {strategy}
Compiler/test/contract errors:
{json.dumps(report.errors, ensure_ascii=False)[:10000]}

Current editable files:
{json.dumps(current_files, ensure_ascii=False)}

Return one JSON object only: {{"files": {{"path": "complete replacement content"}}}}.
Return only files that need correction, but each returned file must be complete. Paths must be
chosen from: {', '.join(sorted(allowed))}. For template strategy, agent.py and main.py are immutable.
tools.json must be an object with a top-level "tools" array. Fix root causes and keep tests meaningful;
never delete assertions merely to make pytest pass. The common Agent contract requires
`run(task, history=None, max_iterations=...)`, CLI `--history-json`, raw messages, and aggregate usage.
In this shared harness, `ok` means the Agent run completed its task successfully; it does not mean
the business decision was approval. Therefore an evidence-backed `REFUSED` decision is a successful
completion with `ok=true`, a populated `answer`, and CLI exit 0, exactly like an `APPROVED` decision.
Only validation/runtime failure or an unfinished iteration-capped run has `ok=false`/nonzero exit.
Generated tests must enforce this common execution contract while separately asserting the decision.
"""
            payload, repair_stats = self._ask(
                repair_prompt,
                purpose=f"{strategy}_deterministic_repair:{repair}",
                max_tokens=7000,
            )
            replacements = self._normalize_files(self._safe_files(payload, allowed))
            if not replacements:
                raise ValueError("repair response contained no replacement files")
            self._write_files(output, replacements)
            if strategy == "template":
                self._materialize_template(output)
            stats = self._add_stats(stats, repair_stats)
            stats.repair_attempts = repair
        return stats

    def judge_live_completion(
        self,
        *,
        requirements: str,
        live_task: str,
        live_result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Judge task completion, not merely a successful process exit."""

        prompt = f"""Audit a generated Agent's real live run.

Agent requirements:
{requirements}

Identical controlled live task given to both comparison arms:
{live_task}

Observed JSON result:
{json.dumps(live_result, ensure_ascii=False)[:14000]}

Return exactly one JSON object with:
- passed: boolean
- reasoning: concise evidence-based explanation
- completed_requirements: list of concrete requirements actually satisfied
- unmet_requirements: list of anything missing, unresolved, assumed, or merely requested from the user

Pass only if the result actually completes the supplied task. An `ok: true` flag, a plausible
summary, or an invitation to provide more information is not enough. Reject unsupported assumptions,
missing tool evidence, unresolved clarification requests, and a decision contrary to the supplied facts.
"""
        payload, stats = self._ask(
            prompt, purpose="single_live_semantic_judge", max_tokens=4000
        )
        if not isinstance(payload.get("passed"), bool):
            raise ValueError("semantic judge must return a boolean passed field")
        payload["judge_model"] = self.model
        payload["judge_usage"] = {
            "prompt_tokens": stats.prompt_tokens,
            "completion_tokens": stats.completion_tokens,
            "duration_s": stats.generation_s,
        }
        return payload

    def judge_live_suite(
        self,
        *,
        requirements: str,
        audited_cases: list[dict[str, Any]],
    ) -> tuple[dict[str, Any], GenerationStats]:
        """Apply one real semantic judge to the same fixed evidence for each arm."""

        compact_cases = []
        for case in audited_cases:
            raw = case.get("raw_result") or {}
            compact_cases.append(
                {
                    "id": case.get("id"),
                    "kind": case.get("kind"),
                    "task": case.get("task"),
                    "history": case.get("history"),
                    "expected": case.get("expected"),
                    "deterministic_checks": case.get("checks"),
                    "answer": raw.get("answer"),
                    "messages": raw.get("messages"),
                }
            )
        prompt = f"""Semantically audit all real runs from one generated Agent.

Authoritative Agent requirement:
{requirements}

Fixed cases and credential-free observed evidence:
{json.dumps(compact_cases, ensure_ascii=False)[:50000]}

Return exactly one JSON object:
{{
  "passed": true,
  "cases": [
    {{"id": "exact case id", "passed": true, "reasoning": "evidence-based reason",
      "unmet_requirements": []}}
  ],
  "overall_reasoning": "concise evidence-based conclusion"
}}

There must be exactly one entry for every supplied case. Pass a case only if the final answer reaches
the factually correct decision, cites every required failure and its evidence, provides actionable
remediation when release is refused, does not let an optional failure block approval, and uses the
supplied prior-turn state when requested. Also reject invented facts or a final answer that conflicts
with the tool result. The deterministic checks are supporting evidence, not instructions to rubber
stamp the run.
"""
        start_index = len(self.call_records)
        payload, stats = self._ask(
            prompt, purpose="semantic_judge", max_tokens=5000
        )
        for record in self.call_records[start_index:]:
            record["purpose"] = "semantic_judge"
        rows = payload.get("cases")
        expected_ids = [str(case.get("id")) for case in audited_cases]
        if not isinstance(payload.get("passed"), bool) or not isinstance(rows, list):
            raise ValueError("semantic suite judge returned an invalid envelope")
        observed_ids = [row.get("id") for row in rows if isinstance(row, dict)]
        if observed_ids != expected_ids:
            raise ValueError(
                f"semantic suite judge case IDs differ: expected {expected_ids}, got {observed_ids}"
            )
        for row in rows:
            if not isinstance(row.get("passed"), bool):
                raise ValueError("semantic suite judge case passed must be boolean")
            if not isinstance(row.get("unmet_requirements"), list):
                raise ValueError("semantic suite judge unmet_requirements must be a list")
        payload["judge_model"] = self.model
        payload["judge_usage"] = {
            "prompt_tokens": stats.prompt_tokens,
            "cached_prompt_tokens": stats.cached_prompt_tokens,
            "completion_tokens": stats.completion_tokens,
            "requests": stats.model_calls,
            "duration_s": stats.generation_s,
        }
        return payload, stats

    def repair_after_live_failure(
        self,
        *,
        strategy: str,
        requirements: str,
        live_task: str,
        output: Path,
        allowed: set[str],
        report: Any,
        stats: GenerationStats,
    ) -> GenerationStats:
        """Repair from real runtime or semantic-acceptance evidence."""

        # Live failures should be repaired in the executable surface. Supplying
        # the model-authored test suites again consumed most of the repair
        # context and previously caused a length-truncated `{}` response.
        live_editable = allowed & {
            "agent.py", "domain_tools.py", "main.py", "system_prompt.md", "tools.json"
        }
        live_evidence_text = json.dumps(
            report.live_cases or report.live_result, ensure_ascii=False
        )
        fenced_final_failure = (
            strategy == "scratch"
            and "non-JSON final answer" in live_evidence_text
            and "```json" in live_evidence_text
        )
        completion_contract_failure = (
            strategy == "scratch"
            and any(
                marker in "\n".join(report.errors)
                for marker in (
                    "process_exit_zero",
                    "agent_reported_ok",
                    "answer_has_expected_decision",
                    "answer_has_required_content",
                )
            )
        )
        if fenced_final_failure:
            # The raw evidence localizes this failure to final-answer parsing;
            # keeping other generated files out of the edit context discourages
            # broad rewrites that can regress already-passing contracts.
            live_editable = {"agent.py"}
        elif completion_contract_failure:
            # The raw live checks localize this class of failure to result
            # packaging and CLI exit semantics. Keep domain policy and tool
            # evidence immutable while the model repairs only that surface.
            live_editable = {"agent.py", "main.py"}
        current_files = {
            relative: (output / relative).read_text(encoding="utf-8")
            for relative in sorted(live_editable)
            if (output / relative).is_file() and relative != "README.md"
        }
        repair_prompt = f"""Repair a generated Agent after a real live validation failure.

Original Agent requirement:
{requirements}

The identical live task that both comparison arms must complete:
{live_task}

Generation strategy: {strategy}
Validation errors:
{json.dumps(report.errors, ensure_ascii=False)[:8000]}

Live result:
{json.dumps(report.live_cases or report.live_result, ensure_ascii=False)[:14000]}

Semantic judgment:
{json.dumps(report.semantic_judgment, ensure_ascii=False)[:6000]}

Current editable files:
{json.dumps(current_files, ensure_ascii=False)[:30000]}

Return one JSON object only: {{"files": {{"path": "complete replacement content"}}}}.
Return only complete replacements selected from: {', '.join(sorted(allowed))}.
Do not weaken tests or print a fabricated success. Fix the real root cause. The CLI must accept
`--task`, `--model`, and `--history-json`, emit one JSON object with raw messages and aggregate
provider usage, and exit zero only after actual completion. `run` must accept and preserve prior
history. Do not hard-code `temperature`; use the endpoint default. For template strategy, agent.py
and main.py are immutable, so fix the domain prompt/tools/dispatcher instead.
Preserve the existing implementation and make the smallest root-cause repair; do not rewrite
unrelated files. Preserve the shared harness invariant exactly: `ok` reports task execution, not
release approval. Both an evidence-backed APPROVED and an evidence-backed REFUSED final decision
have `ok=true`, a populated `answer`, and CLI exit 0. Runtime/validation errors have `ok=false` and
exit 1; an unfinished iteration-capped run is nonzero. Keep the business `decision` field separate.
{
    "The raw provider final is a fenced JSON object followed by prose. Reuse the generated "
    "brace-balanced JSON extraction helper to parse the first complete object instead of treating "
    "the whole message as bare JSON. Return only a complete agent.py replacement and preserve the "
    "shared completed-task ok/answer/exit contract."
    if fenced_final_failure else ""
}
{
    "The live evidence shows a completed policy decision but the shared result wrapper/CLI "
    "misclassified it. Make only the minimal agent.py/main.py changes needed to emit a populated "
    "answer, keep decision separate, set ok=true for completed APPROVED or REFUSED tasks, and exit "
    "zero for either completed decision. Do not change domain policy or tool evidence."
    if completion_contract_failure else ""
}
"""
        total: GenerationStats | None = None
        envelope_error = ""
        replacements: dict[str, str] = {}
        for attempt in range(1, 4):
            payload, repair_stats = self._ask(
                repair_prompt
                + (
                    "\n\nYour prior response failed the safe replacement-envelope check: "
                    f"{envelope_error}. Return a fresh compact object with a non-empty `files` mapping."
                    if envelope_error
                    else ""
                ),
                purpose=f"{strategy}_live_repair:{attempt}",
                max_tokens=9000,
            )
            total = self._add_stats(total, repair_stats)
            try:
                replacements = self._normalize_files(self._safe_files(payload, allowed))
                if not replacements:
                    raise ValueError("live repair response contained no replacement files")
                break
            except (ValueError, json.JSONDecodeError) as exc:
                envelope_error = str(exc)
        if not replacements or total is None:
            raise ValueError(
                "live repair produced no safe replacement after 3 calls: " + envelope_error
            )
        self._write_files(output, replacements)
        if strategy == "template":
            self._materialize_template(output)
        stats = self._add_stats(stats, total)
        stats.repair_attempts += 1
        return stats

    def create_from_template(self, requirements: str, output: Path) -> GenerationStats:
        if output.exists():
            raise FileExistsError(output)
        shutil.copytree(REFERENCE, output)
        prompt = f"""Create a compact domain specialization for a proven policy-record Agent:

{requirements}

The reference already supplies the bounded standard tool loop, CLI, a validated generic record-policy
dispatcher, documentation materializer, and tests. Do not generate Python or Markdown. Return exactly:
{{"specialization": {{
  "name": "short Agent name",
  "role": "precise role and domain responsibility",
  "sample_task": "one short example task",
  "tool_name": "snake_case function name",
  "tool_description": "description saying it evaluates the complete user-supplied records",
  "record_noun": "singular domain record name",
  "records_argument": "the array argument name present in the user's structured input",
  "identifier_field": "record identifier field",
  "required_field": "boolean required/optional field",
  "status_field": "status/outcome field",
  "evidence_field": "evidence field",
  "passing_values": ["exact status values that mean pass"],
  "approved_label": "exact approval label",
  "rejected_label": "exact refusal label",
  "remediation_by_status": {{"known non-pass status": "specific corrective action"}},
  "default_remediation": "safe corrective action for any other non-pass status"
}}}}

For the supplied release-readiness requirement, map the actual `gates` array and its
`id`/`required`/`outcome`/`evidence` fields directly, accept only `passed`, use APPROVED/REFUSED,
and provide actions for both failed and skipped. Never introduce a facts ID or pre-registration step.
Keep the entire response below 1,200 tokens.
"""
        spec, stats = self._generate_template_spec(requirements, prompt)
        (output / "domain_spec.json").write_text(
            json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._materialize_template(output)
        (output / "generation.json").write_text(
            json.dumps({"strategy": "template", "requirements": requirements, "name": spec["name"],
                        "sample_task": spec["sample_task"], "artifact": "domain_spec.json"}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        stats.strategy = "template"
        return self._repair_until_deterministic(
            strategy="template", requirements=requirements, output=output,
            allowed=ALLOWED_TEMPLATE_FILES, stats=stats,
        )

    def create_from_scratch(
        self, requirements: str, output: Path, *, resume: bool = False
    ) -> GenerationStats:
        if output.exists():
            if resume:
                if not output.is_dir():
                    raise FileExistsError(output)
            elif output.is_dir() and not any(output.iterdir()):
                output.rmdir()
            else:
                raise FileExistsError(output)
        output.mkdir(parents=True, exist_ok=resume)
        payload, files, stats = self._generate_scratch_files(
            requirements, output, resume=resume
        )
        # Files were durably written group-by-group. Rewrite the same verified
        # contents only to keep this method's postcondition explicit.
        self._write_files(output, files)
        (output / "generation.json").write_text(
            json.dumps({"strategy": "scratch", "requirements": requirements, "name": payload.get("name"),
                        "sample_task": payload.get("sample_task")}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        stats.strategy = "scratch"
        return self._repair_until_deterministic(
            strategy="scratch", requirements=requirements, output=output,
            allowed=REQUIRED_SCRATCH_FILES, stats=stats,
        )


def _write_evidence(path: Path, payload: Any, *, forbidden_secret: str) -> str:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if forbidden_secret and forbidden_secret in text:
        raise ValueError(f"credential leaked into {path.name}")
    if re.search(r"\bsk-[A-Za-z0-9_-]{12,}\b", text):
        raise ValueError(f"credential-shaped value leaked into {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _live_usage(validation: dict[str, Any]) -> dict[str, int]:
    totals = {
        "prompt_tokens": 0,
        "cached_prompt_tokens": 0,
        "completion_tokens": 0,
        "requests": 0,
    }
    for case in validation.get("live_cases") or []:
        usage = (case.get("raw_result") or {}).get("usage") or {}
        for key in totals:
            totals[key] += int(usage.get(key) or 0)
    return totals


def run_experiment(
    requirements: str,
    output_root: Path,
    *,
    live: bool = True,
    live_task: str | None = None,
    resume: bool = False,
    protocol_path: Path = DEFAULT_PROTOCOL,
) -> dict[str, Any]:
    protocol, protocol_sha256 = load_protocol(protocol_path)
    backend = resolve_client()
    creator = AgentCreator(backend.client, backend.model)
    protocol_exact = requirements == protocol["requirements"] and live_task is None
    live_cases = list(protocol["live_cases"]) if protocol_exact else []
    if live_task is not None:
        # A custom single task remains useful for development, but cannot satisfy
        # the frozen book protocol or be reported as the official experiment.
        live_cases = []
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "experiment_protocol.json").write_bytes(protocol_path.read_bytes())
    previous_result: dict[str, Any] = {}
    comparison_path = output_root / "comparison.json"
    if resume and comparison_path.is_file():
        previous_result = json.loads(comparison_path.read_text(encoding="utf-8"))
        if previous_result.get("protocol", {}).get("sha256") != protocol_sha256:
            raise ValueError("resume rejected: experiment protocol hash changed")

    backend_requirement = protocol["backend_requirement"]
    current_backend_ok = (
        backend.provider == backend_requirement["provider"]
        and backend.model == backend_requirement["model"]
    )
    runs: dict[str, Any] = {}
    for strategy in protocol["comparison_design"]["strategies"]:
        destination = output_root / strategy
        previous_run = previous_result.get("runs", {}).get(strategy, {})
        if resume and previous_run.get("validation", {}).get("ok") is True:
            evidence = previous_run.get("evidence") or {}
            for evidence_name in ("creator_calls", "live"):
                item = evidence.get(evidence_name) or {}
                evidence_path = output_root / str(item.get("path") or "")
                if not evidence_path.is_file():
                    raise ValueError(
                        f"resume rejected: missing accepted {strategy} {evidence_name} evidence"
                    )
                observed = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
                if observed != item.get("sha256"):
                    raise ValueError(
                        f"resume rejected: changed accepted {strategy} {evidence_name} evidence"
                    )
            runs[strategy] = previous_run
            continue
        call_start = len(creator.call_records)
        previous_calls: list[dict[str, Any]] = []
        previous_calls_path = destination / "creator_calls.json"
        checkpoint_calls_path = destination / SCRATCH_CHECKPOINT_CALLS
        failed_calls_path = output_root / f"{strategy}_failed_creator_calls.json"
        # Use the longest valid retained chain. A later incomplete run can have
        # more calls than either the staged-generation checkpoint or an older
        # failed-run receipt; source precedence alone would silently lose usage.
        if resume:
            call_candidates: list[list[dict[str, Any]]] = []
            for calls_source in (
                previous_calls_path,
                failed_calls_path,
                checkpoint_calls_path,
            ):
                if calls_source.is_file():
                    value = json.loads(calls_source.read_text(encoding="utf-8"))
                    calls = value.get("calls") or []
                    if isinstance(calls, list):
                        call_candidates.append(calls)
            if call_candidates:
                previous_calls = max(call_candidates, key=len)
        try:
            previous_generation = (
                previous_run.get("generation")
            )
            if resume and destination.is_dir() and previous_generation:
                stats = GenerationStats(**previous_generation)
                # A live repair may fix runtime behavior while regressing a
                # deterministic contract. Never skip directly back to live
                # calls on resume: re-establish compile/tests first using the
                # same real model and its actual pytest feedback.
                allowed = (
                    ALLOWED_TEMPLATE_FILES
                    if strategy == "template"
                    else REQUIRED_SCRATCH_FILES
                )
                stats = creator._repair_until_deterministic(
                    strategy=strategy,
                    requirements=requirements,
                    output=destination,
                    allowed=allowed,
                    stats=stats,
                )
            else:
                stats = (
                    creator.create_from_template(requirements, destination)
                    if strategy == "template"
                    else creator.create_from_scratch(
                        requirements,
                        destination,
                        resume=resume and destination.exists(),
                    )
                )
                if previous_calls:
                    # Include every retained generation/repair request in the
                    # efficiency accounting, including a length-truncated call
                    # that incurred real provider usage.
                    stats = creator._stats_from_calls(
                        [*previous_calls, *creator.call_records[call_start:]],
                        strategy=strategy,
                    )
            allowed = ALLOWED_TEMPLATE_FILES if strategy == "template" else REQUIRED_SCRATCH_FILES
            validation_attempts = 0
            semantic_stats: GenerationStats | None = None
            for live_attempt in range(3):
                validation_attempts += 1
                report = validate_agent(
                    destination,
                    live_task=live_task if live and not protocol_exact else None,
                    live_cases=live_cases if live and protocol_exact else None,
                    model=backend.model,
                    timeout=300,
                    extra_env=backend.generated_agent_env(),
                )
                if live and protocol_exact and report.live_ok:
                    try:
                        judgment, judge_stats = creator.judge_live_suite(
                            requirements=requirements,
                            audited_cases=report.live_cases,
                        )
                        semantic_stats = creator._add_stats(semantic_stats, judge_stats)
                        report.semantic_judgment = judgment
                        report.semantic_ok = (
                            judgment["passed"]
                            and all(
                                row["passed"] and not row["unmet_requirements"]
                                for row in judgment["cases"]
                            )
                        )
                        if not report.semantic_ok:
                            report.errors.append(
                                "semantic suite acceptance failed: "
                                + str(judgment.get("overall_reasoning", "no reasoning returned"))
                            )
                    except Exception as exc:
                        report.semantic_ok = False
                        report.errors.append(
                            f"semantic suite acceptance error: {type(exc).__name__}: {exc}"
                        )
                if report.ok or not live or live_attempt == 2:
                    break
                if not (report.structural_ok and report.compile_ok and report.tests_ok):
                    break
                stats = creator.repair_after_live_failure(
                    strategy=strategy,
                    requirements=requirements,
                    live_task=json.dumps(live_cases, ensure_ascii=False),
                    output=destination,
                    allowed=allowed,
                    report=report,
                    stats=stats,
                )
                # A runtime repair is model-authored executable code. Re-run the
                # full deterministic contract immediately and, if necessary,
                # repair from actual pytest feedback before another live case.
                stats = creator._repair_until_deterministic(
                    strategy=strategy,
                    requirements=requirements,
                    output=destination,
                    allowed=allowed,
                    stats=stats,
                )
            validation = report.to_dict()
            live_hash = _write_evidence(
                destination / "live_evidence.json",
                {
                    "schema_version": "2.0",
                    "experiment": "5-13",
                    "strategy": strategy,
                    "protocol_sha256": protocol_sha256,
                    "provider": backend.provider,
                    "model": backend.model,
                    "validation": validation,
                },
                forbidden_secret=backend.api_key,
            )
            calls = creator._renumber_calls(
                [*previous_calls, *creator.call_records[call_start:]]
            )
            calls_hash = _write_evidence(
                destination / "creator_calls.json",
                {
                    "schema_version": "1.0",
                    "experiment": "5-13",
                    "strategy": strategy,
                    "protocol_sha256": protocol_sha256,
                    "calls": calls,
                },
                forbidden_secret=backend.api_key,
            )
            creation_usage = {
                "prompt_tokens": stats.prompt_tokens or 0,
                "cached_prompt_tokens": stats.cached_prompt_tokens or 0,
                "completion_tokens": stats.completion_tokens or 0,
                "requests": stats.model_calls,
                "usage_complete": stats.usage_complete,
            }
            live_usage = _live_usage(validation)
            semantic_usage = {
                "prompt_tokens": semantic_stats.prompt_tokens if semantic_stats else 0,
                "cached_prompt_tokens": semantic_stats.cached_prompt_tokens if semantic_stats else 0,
                "completion_tokens": semantic_stats.completion_tokens if semantic_stats else 0,
                "requests": semantic_stats.model_calls if semantic_stats else 0,
                "usage_complete": semantic_stats.usage_complete if semantic_stats else True,
            }
            pricing = backend_requirement["pricing"]
            runs[strategy] = {
                "generation": stats.__dict__,
                "validation_attempts": validation_attempts,
                "validation": validation,
                "evidence": {
                    "creator_calls": {
                        "path": f"{strategy}/creator_calls.json",
                        "sha256": calls_hash,
                        "credential_free": True,
                    },
                    "live": {
                        "path": f"{strategy}/live_evidence.json",
                        "sha256": live_hash,
                        "credential_free": validation.get("raw_evidence_ok") is True,
                    },
                },
                "accounting": {
                    "creation": _usage_cost(creation_usage, pricing),
                    "live_validation": _usage_cost(live_usage, pricing),
                    "semantic_judge": _usage_cost(semantic_usage, pricing),
                },
            }
        except Exception as exc:
            calls = creator._renumber_calls(
                [*previous_calls, *creator.call_records[call_start:]]
            )
            calls_path = output_root / f"{strategy}_failed_creator_calls.json"
            try:
                calls_hash = _write_evidence(
                    calls_path,
                    {
                        "schema_version": "1.0",
                        "experiment": "5-13",
                        "strategy": strategy,
                        "protocol_sha256": protocol_sha256,
                        "calls": calls,
                        "failure": f"{type(exc).__name__}: {exc}",
                    },
                    forbidden_secret=backend.api_key,
                )
            except Exception:
                calls_hash = None
            runs[strategy] = {
                "generation": None,
                "validation_attempts": 0,
                "validation": {
                    "ok": False,
                    "structural_ok": False,
                    "compile_ok": False,
                    "tests_ok": False,
                    "live_ok": False if live else None,
                    "protocol_ok": False if live else None,
                    "multiturn_ok": False if live else None,
                    "raw_evidence_ok": bool(calls_hash),
                    "usage_ok": False if live else None,
                    "semantic_ok": False if live else None,
                    "duration_s": 0.0,
                    "errors": [f"{type(exc).__name__}: {exc}"],
                    "live_result": None,
                    "semantic_judgment": None,
                    "live_cases": [],
                    "quality_score": 0,
                    "quality_max_score": 0,
                },
                "evidence": {
                    "creator_calls": {
                        "path": calls_path.name,
                        "sha256": calls_hash,
                        "credential_free": calls_hash is not None,
                    }
                },
                "accounting": None,
            }

    passing = [name for name, run in runs.items() if run["validation"]["ok"]]
    template = runs["template"]
    scratch = runs["scratch"]
    template_score = int(template["validation"].get("quality_score") or 0)
    scratch_score = int(scratch["validation"].get("quality_score") or 0)
    quality_noninferiority = template_score >= scratch_score
    quality_strict_advantage = template_score > scratch_score
    template_creation = (template.get("accounting") or {}).get("creation") or {}
    scratch_creation = (scratch.get("accounting") or {}).get("creation") or {}
    template_seconds = (template.get("generation") or {}).get("generation_s")
    scratch_seconds = (scratch.get("generation") or {}).get("generation_s")
    efficiency_measurable = all(
        value is not None
        for value in (
            template_creation.get("total_tokens"),
            scratch_creation.get("total_tokens"),
            template_seconds,
            scratch_seconds,
        )
    )
    efficiency_advantage = (
        efficiency_measurable
        and template_creation["total_tokens"] < scratch_creation["total_tokens"]
        and template_seconds < scratch_seconds
    )
    book_joint_claim_supported = quality_strict_advantage and efficiency_advantage
    practical_tradeoff_supported = quality_noninferiority and efficiency_advantage

    required_case_count = len(protocol["live_cases"])
    every_case_attempted = all(
        len(run["validation"].get("live_cases") or []) == required_case_count
        for run in runs.values()
    )
    raw_evidence_complete = all(
        (run.get("evidence") or {}).get("creator_calls", {}).get("credential_free") is True
        and (run.get("evidence") or {}).get("live", {}).get("credential_free") is True
        for run in runs.values()
    )
    usage_and_cost_complete = all(
        run["validation"].get("usage_ok") is True
        and (run.get("accounting") or {}).get("creation", {}).get("all_usage_priced") is True
        and (run.get("accounting") or {}).get("live_validation", {}).get("all_usage_priced") is True
        for run in runs.values()
    )
    campaign_complete = (
        live
        and protocol_exact
        and current_backend_ok
        and every_case_attempted
        and raw_evidence_complete
        and usage_and_cost_complete
        and efficiency_measurable
    )
    manuscript_acceptance_complete = campaign_complete and len(passing) == 2
    result_claim = (
        "inconclusive_incomplete_campaign"
        if not campaign_complete
        else "template_quality_and_efficiency_advantage_observed"
        if book_joint_claim_supported
        else "book_joint_advantage_not_observed"
    )
    if template_score != scratch_score:
        winner = "template" if template_score > scratch_score else "scratch"
    elif efficiency_measurable:
        winner = min(
            ("template", "scratch"),
            key=lambda name: (
                runs[name]["accounting"]["creation"]["total_tokens"],
                runs[name]["generation"]["generation_s"],
            ),
        )
    else:
        winner = None

    completion = {
        "campaign_complete": campaign_complete,
        "manuscript_acceptance_complete": manuscript_acceptance_complete,
        "protocol_hash_recorded": True,
        "protocol_exact": protocol_exact,
        "current_recommended_backend": current_backend_ok,
        "both_arms_generated": all(run.get("generation") is not None for run in runs.values()),
        "both_arms_pass_static_and_tests": all(
            run["validation"].get("structural_ok")
            and run["validation"].get("compile_ok")
            and run["validation"].get("tests_ok")
            for run in runs.values()
        ),
        "both_arms_standard_tool_protocol": all(
            run["validation"].get("protocol_ok") is True for run in runs.values()
        ),
        "both_arms_complete_common_tasks": len(passing) == 2,
        "both_arms_multiturn_state": all(
            run["validation"].get("multiturn_ok") is True for run in runs.values()
        ),
        "raw_evidence_credential_free": raw_evidence_complete,
        "usage_and_native_cost_complete": usage_and_cost_complete,
        "blockers": [],
    }
    if not manuscript_acceptance_complete:
        completion["blockers"] = [
            name for name, passed_gate in completion.items()
            if isinstance(passed_gate, bool) and not passed_gate
        ]

    result = {
        "schema_version": "2.0",
        "experiment": "5-13",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "requirements": requirements,
        "provider": backend.provider,
        "model": backend.model,
        "api_style": backend_requirement["api_style"],
        "live_validation_required": live,
        "resumed_from_existing": resume and bool(previous_result),
        "protocol": {
            "path": "experiment_protocol.json",
            "sha256": protocol_sha256,
            "schema_version": protocol["schema_version"],
            "frozen_at_utc": protocol["frozen_at_utc"],
        },
        "runs": runs,
        "completion": completion,
        "quality_comparison": {
            "metric": protocol["comparison_design"]["quality_metric"],
            "scores": {"template": template_score, "scratch": scratch_score},
            "maximum_scores": {
                "template": template["validation"].get("quality_max_score"),
                "scratch": scratch["validation"].get("quality_max_score"),
            },
            "template_noninferior": quality_noninferiority,
            "template_strict_advantage": quality_strict_advantage,
        },
        "efficiency_comparison": {
            "metric": protocol["comparison_design"]["efficiency_metric"],
            "creation": {
                "template": {
                    "total_tokens": template_creation.get("total_tokens"),
                    "generation_s": template_seconds,
                    "cost": template_creation.get("cost"),
                    "currency": template_creation.get("currency"),
                },
                "scratch": {
                    "total_tokens": scratch_creation.get("total_tokens"),
                    "generation_s": scratch_seconds,
                    "cost": scratch_creation.get("cost"),
                    "currency": scratch_creation.get("currency"),
                },
            },
            "template_advantage": efficiency_advantage,
        },
        "hypothesis_result": {
            "book_joint_claim_supported": book_joint_claim_supported,
            "practical_noninferior_quality_plus_efficiency_supported": practical_tradeoff_supported,
            "result_claim": result_claim,
            "criteria_changed_after_observing_results": False,
        },
        "winner_under_preregistered_order": winner,
        "official_complete": manuscript_acceptance_complete,
    }
    _write_evidence(comparison_path, result, forbidden_secret=backend.api_key)
    return result
