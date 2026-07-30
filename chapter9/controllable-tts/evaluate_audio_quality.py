#!/usr/bin/env python3
"""Run a blinded, position-balanced audio study for Experiment 9-5.

The three clips already come from real Fish Audio S1 calls.  This program asks a
real audio-capable Gemini model to listen to them in three different orders,
validates every returned score/evidence field, and writes a receipt without
persisting the API key.  It evaluates the manuscript claim; it does not label an
LLM judgement as a human MOS study.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

HERE = Path(__file__).parent
OUTPUTS = {
    "A_no_control_markers": HERE / "output" / "A_no_control_markers.mp3",
    "B_single_reference": HERE / "output" / "B_single_reference.mp3",
    "C_24_reference_library": HERE / "output" / "C_24_reference_library.mp3",
}
DIMENSIONS = (
    "naturalness",
    "expressive_fit",
    "thinking_behavior",
    "speaker_consistency",
    "human_customer_service",
)
PREFERRED_MODELS = (
    "gemini-3.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-flash-latest",
)
PREFERRED_OPENROUTER_MODELS = (
    "google/gemini-3.5-flash",
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
)
PERMUTATIONS = (
    ("A_no_control_markers", "B_single_reference", "C_24_reference_library"),
    ("B_single_reference", "C_24_reference_library", "A_no_control_markers"),
    ("C_24_reference_library", "A_no_control_markers", "B_single_reference"),
)
ALIASES = ("X", "Y", "Z")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _http_json(
    url: str,
    *,
    body: dict[str, Any] | None = None,
    timeout: int = 120,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=None if body is None else json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="GET" if body is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        # The provider response does not contain the key.  Never include the
        # request URL because the key is deliberately carried in its query.
        detail = exc.read().decode("utf-8", "replace")[:2000]
        raise RuntimeError(f"Provider HTTP {exc.code}: {detail}") from None


def resolve_model(api_key: str, requested: str | None) -> str:
    if requested:
        return requested.removeprefix("models/")
    payload = _http_json(
        "https://generativelanguage.googleapis.com/v1beta/models?key=" + api_key,
        timeout=30,
    )
    available = {
        str(item.get("name", "")).removeprefix("models/")
        for item in payload.get("models", [])
        if "generateContent" in (item.get("supportedGenerationMethods") or [])
    }
    for model in PREFERRED_MODELS:
        if model in available:
            return model
    candidates = sorted(
        model for model in available
        if model and not any(term in model for term in ("image", "embedding", "tts"))
    )
    if not candidates:
        raise RuntimeError("Gemini did not report an audio-judge-capable generateContent model")
    return candidates[-1]


def resolve_openrouter_model(requested: str | None) -> str:
    if requested:
        return requested
    payload = _http_json("https://openrouter.ai/api/v1/models", timeout=30)
    models = payload.get("data") or []
    available = {str(item.get("id", "")): item for item in models if isinstance(item, dict)}
    for model in PREFERRED_OPENROUTER_MODELS:
        item = available.get(model)
        modalities = (item or {}).get("architecture", {}).get("input_modalities") or []
        if item and (not modalities or "audio" in modalities):
            return model
    audio_google = sorted(
        model for model, item in available.items()
        if model.startswith("google/")
        and "audio" in ((item.get("architecture") or {}).get("input_modalities") or [])
    )
    if not audio_google:
        raise RuntimeError("OpenRouter did not report an audio-capable Google model")
    return audio_google[-1]


def _prompt() -> str:
    return (
        "You are a strict bilingual speech-quality evaluator. Listen directly to the three "
        "Chinese customer-service clips supplied after this instruction. Their anonymous labels "
        "and order are X, Y, Z. All aim to express: 太好了！您的订单已确认。让我查一下发货时间。"
        "预计明天下午送达。 Some versions may add a natural thinking filler or pause. Do not infer "
        "which synthesis configuration produced a clip. Score each clip independently from 1 "
        "(poor) to 5 (excellent) on exactly these dimensions: naturalness; expressive_fit "
        "(happy confirmation followed by thoughtful lookup and neutral delivery); "
        "thinking_behavior (whether any pause/filler is natural and useful, not merely whether it "
        "exists); speaker_consistency; human_customer_service. Every dimension must include one "
        "specific audible observation. Then rank X/Y/Z best to worst, with no ties. Return only JSON "
        "with this shape: {\"clips\":{\"X\":{\"naturalness\":{\"score\":1,\"reason\":\"...\"},"
        "\"expressive_fit\":{...},\"thinking_behavior\":{...},\"speaker_consistency\":{...},"
        "\"human_customer_service\":{...}},\"Y\":{...},\"Z\":{...}},"
        "\"ranking\":[\"X\",\"Y\",\"Z\"],\"ranking_reason\":\"audible comparative evidence\"}."
    )


def validate_response(payload: dict[str, Any]) -> dict[str, Any]:
    clips = payload.get("clips")
    if not isinstance(clips, dict) or set(clips) != set(ALIASES):
        raise ValueError("judge response must contain exactly clips X, Y, and Z")
    normalized: dict[str, Any] = {"clips": {}}
    for alias in ALIASES:
        clip = clips[alias]
        if not isinstance(clip, dict) or set(clip) != set(DIMENSIONS):
            raise ValueError(f"clip {alias} must contain exactly the five rubric dimensions")
        normalized["clips"][alias] = {}
        for dimension in DIMENSIONS:
            item = clip[dimension]
            if not isinstance(item, dict):
                raise ValueError(f"{alias}.{dimension} must be an object")
            score = item.get("score")
            reason = item.get("reason")
            if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
                raise ValueError(f"{alias}.{dimension}.score must be an integer from 1 to 5")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError(f"{alias}.{dimension}.reason must contain audible evidence")
            normalized["clips"][alias][dimension] = {"score": score, "reason": reason.strip()}
    ranking = payload.get("ranking")
    if not isinstance(ranking, list) or len(ranking) != 3 or set(ranking) != set(ALIASES):
        raise ValueError("ranking must contain X, Y, Z exactly once")
    ranking_reason = payload.get("ranking_reason")
    if not isinstance(ranking_reason, str) or not ranking_reason.strip():
        raise ValueError("ranking_reason must contain audible comparative evidence")
    normalized["ranking"] = ranking
    normalized["ranking_reason"] = ranking_reason.strip()
    return normalized


def _parse_judge_text(text: str) -> dict[str, Any]:
    if not text:
        raise RuntimeError("Audio judge returned no text")
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip() in ("```", "```json"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return validate_response(json.loads(text))
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            f"Audio judge returned an invalid quality-study response: {exc}; "
            f"response excerpt={text[:3000]!r}"
        ) from None


def judge_once(
    api_key: str,
    model: str,
    permutation: tuple[str, str, str],
    *,
    provider: str = "gemini",
) -> dict[str, Any]:
    parts: list[dict[str, Any]] = [{"text": _prompt()}]
    for alias, name in zip(ALIASES, permutation):
        parts.append({"text": f"Anonymous clip {alias}:"})
        parts.append({
            "inline_data": {
                "mime_type": "audio/mpeg",
                "data": base64.b64encode(OUTPUTS[name].read_bytes()).decode("ascii"),
            }
        })
    if provider == "gemini":
        body = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"},
        }
        response = _http_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
            body=body,
        )
        candidates = response.get("candidates") or []
        response_parts = ((candidates[0].get("content") or {}).get("parts") or []) if candidates else []
        text = "".join(str(part.get("text", "")) for part in response_parts).strip()
        if not text:
            raise RuntimeError(f"Gemini returned no judge text: {response.get('promptFeedback') or response}")
        return _parse_judge_text(text)
    if provider == "dashscope":
        native_parts: list[dict[str, Any]] = [{"text": _prompt()}]
        for alias, name in zip(ALIASES, permutation):
            native_parts.append({"text": f"Anonymous clip {alias}:"})
            native_parts.append({
                "audio": "data:audio/mpeg;base64," + base64.b64encode(OUTPUTS[name].read_bytes()).decode("ascii")
            })
        response = _http_json(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
            body={
                "model": model,
                "input": {"messages": [{"role": "user", "content": native_parts}]},
                "parameters": {"result_format": "message", "temperature": 0.0, "text_only": True},
            },
            headers={"Authorization": "Bearer " + api_key},
        )
        choices = (response.get("output") or {}).get("choices") or []
        message_content = ((choices[0].get("message") or {}).get("content")) if choices else None
        if isinstance(message_content, list):
            text = "".join(str(item.get("text", "")) for item in message_content if isinstance(item, dict))
        else:
            text = str(message_content or "")
        return _parse_judge_text(text.strip())
    if provider == "mistral":
        mistral_content: list[dict[str, Any]] = [{"type": "text", "text": _prompt()}]
        for alias, name in zip(ALIASES, permutation):
            mistral_content.append({"type": "text", "text": f"Anonymous clip {alias}:"})
            mistral_content.append({
                "type": "input_audio",
                "input_audio": "data:audio/mpeg;base64," + base64.b64encode(
                    OUTPUTS[name].read_bytes()
                ).decode("ascii"),
            })
        response = _http_json(
            "https://api.mistral.ai/v1/chat/completions",
            body={
                "model": model,
                "temperature": 0.0,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": mistral_content}],
            },
            headers={"Authorization": "Bearer " + api_key},
        )
        choices = response.get("choices") or []
        message_content = ((choices[0].get("message") or {}).get("content")) if choices else None
        if isinstance(message_content, list):
            text = "".join(str(item.get("text", "")) for item in message_content if isinstance(item, dict))
        else:
            text = str(message_content or "")
        return _parse_judge_text(text.strip())
    if provider != "openrouter":
        raise ValueError(f"unsupported audio judge provider: {provider}")
    content: list[dict[str, Any]] = [{"type": "text", "text": _prompt()}]
    for alias, name in zip(ALIASES, permutation):
        content.append({"type": "text", "text": f"Anonymous clip {alias}:"})
        content.append({
            "type": "input_audio",
            "input_audio": {
                "data": base64.b64encode(OUTPUTS[name].read_bytes()).decode("ascii"),
                "format": "mp3",
            },
        })
    response = _http_json(
        "https://openrouter.ai/api/v1/chat/completions",
        body={
            "model": model,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": content}],
        },
        headers={"Authorization": "Bearer " + api_key},
    )
    choices = response.get("choices") or []
    message_content = ((choices[0].get("message") or {}).get("content")) if choices else None
    if isinstance(message_content, list):
        text = "".join(str(item.get("text", "")) for item in message_content if isinstance(item, dict))
    else:
        text = str(message_content or "")
    return _parse_judge_text(text.strip())


def aggregate(passes: list[dict[str, Any]]) -> dict[str, Any]:
    scores = {name: {dimension: [] for dimension in DIMENSIONS} for name in OUTPUTS}
    rank_points = {name: 0 for name in OUTPUTS}
    for run in passes:
        alias_to_name = run["alias_to_configuration"]
        response = run["response"]
        for alias, clip in response["clips"].items():
            name = alias_to_name[alias]
            for dimension, item in clip.items():
                scores[name][dimension].append(item["score"])
        for points, alias in zip((3, 2, 1), response["ranking"]):
            rank_points[alias_to_name[alias]] += points
    configurations: dict[str, Any] = {}
    for name, dimensions in scores.items():
        means = {dimension: sum(values) / len(values) for dimension, values in dimensions.items()}
        configurations[name] = {
            "dimension_means": means,
            "overall_mean": sum(means.values()) / len(means),
            "rank_points": rank_points[name],
        }
    ordered = sorted(
        configurations,
        key=lambda name: (configurations[name]["rank_points"], configurations[name]["overall_mean"]),
        reverse=True,
    )
    a, b, c = (configurations[name] for name in OUTPUTS)
    ordering_reproduced = ordered == [
        "C_24_reference_library", "B_single_reference", "A_no_control_markers"
    ] and c["overall_mean"] > b["overall_mean"] > a["overall_mean"]
    near_human_supported = c["dimension_means"]["human_customer_service"] >= 4.0
    return {
        "configurations": configurations,
        "aggregate_ranking": ordered,
        "expected_manuscript_ranking": [
            "C_24_reference_library", "B_single_reference", "A_no_control_markers"
        ],
        "manuscript_quality_ordering_reproduced": ordering_reproduced,
        "near_human_customer_service_supported": near_human_supported,
        "manuscript_quality_claim_reproduced": ordering_reproduced and near_human_supported,
    }


def validate_study(study: dict[str, Any]) -> None:
    if study.get("schema_version") != 1 or study.get("experiment") != "9-5":
        raise ValueError("unexpected quality-study schema or experiment")
    if study.get("study_design", {}).get("judge_type") != "multimodal_llm_not_human_mos":
        raise ValueError("study must identify its judge type honestly")
    passes = study.get("passes")
    if not isinstance(passes, list) or len(passes) != 3:
        raise ValueError("quality study requires three position-balanced passes")
    seen = []
    for run in passes:
        mapping = run.get("alias_to_configuration")
        if not isinstance(mapping, dict) or set(mapping) != set(ALIASES) or set(mapping.values()) != set(OUTPUTS):
            raise ValueError("each pass must map X/Y/Z to all three configurations")
        seen.append(tuple(mapping[alias] for alias in ALIASES))
        validate_response(run.get("response") or {})
    if tuple(seen) != PERMUTATIONS:
        raise ValueError("quality-study passes are not the required balanced permutations")
    hashes = study.get("audio_sha256") or {}
    if hashes != {name: sha256(path) for name, path in OUTPUTS.items()}:
        raise ValueError("quality-study audio hashes do not match current comparison clips")
    if study.get("aggregate") != aggregate(passes):
        raise ValueError("quality-study aggregate does not recompute from raw judge passes")


def main() -> int:
    parser = argparse.ArgumentParser(description="Blinded real-API audio study for Experiment 9-5")
    parser.add_argument("--model", help="Gemini generateContent model; default probes available models")
    parser.add_argument(
        "--provider", choices=("auto", "gemini", "openrouter", "dashscope", "mistral"), default="auto",
        help="audio judge transport; auto tries all configured audio-capable providers",
    )
    parser.add_argument("--output", default=str(HERE / "validation" / "audio_quality_study.json"))
    args = parser.parse_args()
    load_dotenv(HERE / ".env")
    gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    openrouter_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    dashscope_key = (os.getenv("DASHSCOPE_API_KEY") or "").strip()
    mistral_key = (os.getenv("MISTRAL_API_KEY") or "").strip()
    for path in OUTPUTS.values():
        if not path.is_file() or path.stat().st_size <= 1000:
            parser.error(f"Missing real comparison audio: {path}")
    provider_attempts: list[dict[str, Any]] = []
    candidates: list[tuple[str, str, str]] = []
    if args.provider in ("auto", "gemini") and gemini_key:
        try:
            candidates.append(("gemini", gemini_key, resolve_model(gemini_key, args.model)))
        except RuntimeError as exc:
            provider_attempts.append({"provider": "Google Gemini API", "status": "unavailable", "error": str(exc)})
            if args.provider == "gemini":
                raise
    if args.provider in ("auto", "openrouter") and openrouter_key:
        candidates.append(("openrouter", openrouter_key, resolve_openrouter_model(args.model)))
    if args.provider in ("auto", "dashscope") and dashscope_key:
        candidates.append(("dashscope", dashscope_key, args.model or "qwen3-omni-flash"))
    if args.provider in ("auto", "mistral") and mistral_key:
        candidates.append(("mistral", mistral_key, args.model or "voxtral-small-latest"))
    if not candidates:
        parser.error("No configured Gemini, OpenRouter, DashScope, or Mistral audio credential is available")
    def run_passes(selected_provider: str, selected_key: str, selected_model: str):
        completed = []
        for permutation in PERMUTATIONS:
            mapping = dict(zip(ALIASES, permutation))
            completed.append({
                "alias_to_configuration": mapping,
                "response": judge_once(
                    selected_key, selected_model, permutation, provider=selected_provider
                ),
            })
        return completed

    passes = None
    provider = model = ""
    provider_names = {
        "gemini": "Google Gemini API",
        "openrouter": "OpenRouter audio route",
        "dashscope": "Alibaba DashScope multimodal API",
        "mistral": "Mistral Voxtral API",
    }
    last_error = None
    for candidate_provider, candidate_key, candidate_model in candidates:
        try:
            passes = run_passes(candidate_provider, candidate_key, candidate_model)
            provider, model = candidate_provider, candidate_model
            break
        except RuntimeError as exc:
            last_error = exc
            provider_attempts.append({
                "provider": provider_names[candidate_provider],
                "model": candidate_model,
                "status": "unavailable",
                "error": str(exc),
            })
            if args.provider != "auto":
                raise
    if passes is None:
        raise RuntimeError(f"All configured audio judges failed; last error: {last_error}")
    study = {
        "schema_version": 1,
        "experiment": "9-5",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "provider": provider_names[provider],
        "model": model,
        "provider_attempts": provider_attempts,
        "study_design": {
            "judge_type": "multimodal_llm_not_human_mos",
            "blinded_configuration_labels": True,
            "position_balanced": True,
            "passes": 3,
            "temperature": 0.0,
            "dimensions": list(DIMENSIONS),
        },
        "audio_sha256": {name: sha256(path) for name, path in OUTPUTS.items()},
        "passes": passes,
        "aggregate": aggregate(passes),
        "limitations": [
            "This is a real multimodal-model listening study, not a human MOS panel.",
            "Three position-balanced passes reduce order bias but share one judge model.",
        ],
    }
    validate_study(study)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(study, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "model": model, **study["aggregate"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
