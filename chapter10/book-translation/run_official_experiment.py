#!/usr/bin/env python3
"""Run Experiment 10-3 on a real illustrated, code-heavy technical book.

The tiny four-file fixture remains useful for a cheap tutorial.  This is the
acceptance campaign: it translates Chapters 1 and 2 of the English edition of
this book (more than 240 KB, with real figures and fenced code), compares the
four-role Manager workflow with one accumulating Agent conversation, and saves
quality, wall-clock, context, token, and provenance evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

HERE = Path(__file__).parent
REPO = HERE.parents[1]
DEFAULT_SOURCES = (REPO / "book-en" / "chapter1.md", REPO / "book-en" / "chapter2.md")
DIMENSIONS = ("accuracy", "fluency", "terminology", "markdown_code_fidelity")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def load_source_book(paths: list[Path]) -> tuple[dict[str, str], dict[str, str]]:
    chapters: dict[str, str] = {}
    title_to_path: dict[str, str] = {}
    for path in paths:
        text = path.read_text(encoding="utf-8")
        title = extract_title(text, path.stem)
        if title in chapters:
            raise ValueError(f"duplicate source title: {title}")
        chapters[title] = text
        title_to_path[title] = str(path.relative_to(REPO))
    return chapters, title_to_path


def markdown_blocks(text: str) -> list[str]:
    """Split at blank lines without ever cutting through a fenced code block."""
    blocks: list[str] = []
    current: list[str] = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        current.append(line)
        if not in_fence and not line.strip():
            blocks.append("".join(current))
            current = []
    if current:
        blocks.append("".join(current))
    return blocks


def split_translation_units(
    chapters: dict[str, str], max_characters: int = 36_000
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Create bounded chapter parts while retaining an exact reassembly map."""
    units: dict[str, str] = {}
    chapter_units: dict[str, list[str]] = {}
    for title, text in chapters.items():
        parts: list[str] = []
        current = ""
        for block in markdown_blocks(text):
            if current and len(current) + len(block) > max_characters:
                parts.append(current)
                current = ""
            if len(block) > max_characters:
                # A pathological prose block may be larger than the target.
                # Split at line boundaries; fenced code is one block and is
                # deliberately allowed to exceed the target rather than cut.
                if block.lstrip().startswith("```"):
                    if current:
                        parts.append(current)
                        current = ""
                    parts.append(block)
                    continue
                for line in block.splitlines(keepends=True):
                    if current and len(current) + len(line) > max_characters:
                        parts.append(current)
                        current = ""
                    current += line
            else:
                current += block
        if current:
            parts.append(current)
        names = []
        for index, part in enumerate(parts, start=1):
            name = f"{title} [Part {index}/{len(parts)}]"
            units[name] = part
            names.append(name)
        chapter_units[title] = names
        if "".join(parts) != text:
            raise AssertionError(f"translation-unit split changed source bytes for {title}")
    return units, chapter_units


def reassemble_translations(
    translations: dict[str, str], chapter_units: dict[str, list[str]]
) -> dict[str, str]:
    return {
        chapter: "\n\n".join(translations[unit].rstrip() for unit in units).rstrip() + "\n"
        for chapter, units in chapter_units.items()
    }


def fenced_code_payloads(text: str) -> list[str]:
    return re.findall(r"^```[^\n]*\n(.*?)^```[ \t]*$", text, flags=re.MULTILINE | re.DOTALL)


def image_targets(text: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", text)


def link_targets(text: str) -> list[str]:
    return re.findall(r"(?<!!)\[[^\]]+\]\(([^\s)]+)(?:\s+[^)]*)?\)", text)


def markdown_fidelity(source: str, translation: str) -> dict[str, Any]:
    source_code = fenced_code_payloads(source)
    translated_code = fenced_code_payloads(translation)
    source_images = image_targets(source)
    translated_images = image_targets(translation)
    source_links = link_targets(source)
    translated_links = link_targets(translation)
    source_headings = len(re.findall(r"^#{1,6}\s+", source, flags=re.MULTILINE))
    translated_headings = len(re.findall(r"^#{1,6}\s+", translation, flags=re.MULTILINE))
    return {
        "source_sha256": sha256_text(source),
        "translation_sha256": sha256_text(translation),
        "nonempty_translation": bool(translation.strip()),
        "character_ratio": len(translation) / len(source) if source else 0.0,
        "fenced_code": {
            "source_count": len(source_code),
            "translation_count": len(translated_code),
            "exact_payload_sequence_preserved": source_code == translated_code,
        },
        "images": {
            "source_count": len(source_images),
            "translation_count": len(translated_images),
            "exact_target_sequence_preserved": source_images == translated_images,
        },
        "links": {
            "source_count": len(source_links),
            "translation_count": len(translated_links),
            "exact_target_sequence_preserved": source_links == translated_links,
        },
        "headings": {
            "source_count": source_headings,
            "translation_count": translated_headings,
            "count_preserved": source_headings == translated_headings,
        },
    }


def validate_judge_response(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload)
    variants = payload.get("variants")
    repairs: list[str] = []
    if isinstance(variants, dict) and {"X", "Y"}.issubset(variants):
        extras = set(variants) - {"X", "Y"}
        # ARK occasionally duplicates the two preference fields one level too
        # deep while still returning complete X/Y rubrics.  This is a purely
        # structural, lossless repair; arbitrary extra keys and incomplete
        # rubrics remain hard failures.
        if extras and extras.issubset({"preferred", "preference_evidence"}):
            for key in extras:
                if key not in payload:
                    payload[key] = variants[key]
            variants = {alias: variants[alias] for alias in ("X", "Y")}
            repairs.append("lifted duplicated preference fields out of variants")
    if not isinstance(variants, dict) or set(variants) != {"X", "Y"}:
        raise ValueError("judge variants must contain exactly X and Y")
    normalized: dict[str, Any] = {"variants": {}}
    for alias in ("X", "Y"):
        variant = variants[alias]
        if not isinstance(variant, dict) or set(variant) != set(DIMENSIONS):
            raise ValueError(f"judge variant {alias} must contain all rubric dimensions")
        normalized["variants"][alias] = {}
        for dimension in DIMENSIONS:
            item = variant[dimension]
            if not isinstance(item, dict):
                raise ValueError(f"{alias}.{dimension} must be an object")
            score, evidence = item.get("score"), item.get("evidence")
            if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
                raise ValueError(f"{alias}.{dimension}.score must be an integer from 1 to 5")
            if not isinstance(evidence, str) or not evidence.strip():
                raise ValueError(f"{alias}.{dimension}.evidence must be non-empty")
            normalized["variants"][alias][dimension] = {
                "score": score, "evidence": evidence.strip(),
            }
    preferred = payload.get("preferred")
    if preferred not in ("X", "Y", "tie"):
        raise ValueError("judge preferred must be X, Y, or tie")
    reason = payload.get("preference_evidence")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("judge preference_evidence must be non-empty")
    normalized.update(preferred=preferred, preference_evidence=reason.strip())
    if repairs:
        normalized["schema_repairs"] = repairs
    return normalized


def _parse_json(text: str) -> dict[str, Any]:
    value = (text or "").strip()
    if value.startswith("```"):
        lines = value.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines.pop()
        value = "\n".join(lines)
    payload = json.loads(value)
    if not isinstance(payload, dict):
        raise ValueError("judge returned non-object JSON")
    return payload


def make_judge() -> tuple[OpenAI, str, str]:
    if os.getenv("ARK_API_KEY"):
        return (
            OpenAI(api_key=os.environ["ARK_API_KEY"], base_url="https://ark.cn-beijing.volces.com/api/v3"),
            os.getenv("ARK_MODEL", "doubao-seed-1-6-250615"),
            "Volcengine ARK",
        )
    if os.getenv("MISTRAL_API_KEY"):
        return (
            OpenAI(api_key=os.environ["MISTRAL_API_KEY"], base_url="https://api.mistral.ai/v1"),
            "mistral-medium-latest",
            "Mistral API",
        )
    raise RuntimeError("Official translation quality judging requires ARK_API_KEY or MISTRAL_API_KEY")


def judge_chapter(
    client: OpenAI,
    model: str,
    source: str,
    x_translation: str,
    y_translation: str,
    disable_thinking: bool = False,
    receipt_path: Path | None = None,
    max_attempts: int = 4,
) -> tuple[dict[str, Any], dict[str, int]]:
    prompt = (
        "You are an exacting bilingual technical-book translation evaluator. Compare two anonymous "
        "Chinese translations against the complete English Markdown source. Score both X and Y from "
        "1 to 5 on exactly: accuracy (no omissions, inventions, or changed claims); fluency; "
        "terminology (consistent and technically correct); markdown_code_fidelity (figures, links, "
        "headings, equations, and fenced code preserved). Each score needs concrete quoted or located "
        "evidence. Prefer one only when evidence supports it. Return JSON only: "
        '{"variants":{"X":{"accuracy":{"score":1,"evidence":"..."},"fluency":'
        '{"score":1,"evidence":"..."},"terminology":{"score":1,"evidence":"..."},'
        '"markdown_code_fidelity":{"score":1,"evidence":"..."}},"Y":{"accuracy":'
        '{"score":1,"evidence":"..."},"fluency":{"score":1,"evidence":"..."},'
        '"terminology":{"score":1,"evidence":"..."},"markdown_code_fidelity":'
        '{"score":1,"evidence":"..."}}},"preferred":"X|Y|tie",'
        '"preference_evidence":"..."}.\n\n'
        f"COMPLETE ENGLISH SOURCE:\n{source}\n\nANONYMOUS CHINESE X:\n{x_translation}"
        f"\n\nANONYMOUS CHINESE Y:\n{y_translation}"
    )
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    if disable_thinking:
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    def repair_prompt(content: str, error: Exception) -> str:
        return (
            "This is a formatting repair, not a new evaluation. Reshape the JSON below into the "
            "exact requested schema while preserving every substantive score, evidence statement, "
            "preference, and preference explanation. The top level must contain variants, preferred, "
            "and preference_evidence. variants must contain exactly X and Y. Each of X and Y must "
            "contain exactly accuracy, fluency, terminology, and markdown_code_fidelity, and every "
            "dimension must contain score and evidence. Do not re-evaluate, rename fields, nest Y "
            f"inside X, or add keys. Previous validation error: {error}. Return JSON only.\n\n"
            f"JSON TO REPAIR:\n{content}"
        )

    attempts: list[dict[str, Any]] = []
    repair_message: str | None = None
    if receipt_path is not None and receipt_path.exists():
        saved = json.loads(receipt_path.read_text(encoding="utf-8"))
        attempts = saved.get("attempts", [])
        if attempts:
            previous = attempts[-1]
            previous_content = previous.get("response", {}).get("content", "")
            try:
                recovered = validate_judge_response(_parse_json(previous_content))
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                repair_message = repair_prompt(previous_content, exc)
            else:
                previous["resume_validation"] = {
                    "valid": True,
                    "schema_repairs": recovered.get("schema_repairs", []),
                }
                write_json_atomic(receipt_path, {
                    "schema_version": 1,
                    "credential_free": True,
                    "attempts": attempts,
                })
                return recovered, {
                    "prompt_tokens": sum(
                        row["response"]["usage"]["prompt_tokens"] for row in attempts
                    ),
                    "completion_tokens": sum(
                        row["response"]["usage"]["completion_tokens"] for row in attempts
                    ),
                    "latency_milliseconds": sum(
                        row["latency_milliseconds"] for row in attempts
                    ),
                    "attempt_count": len(attempts),
                }
    prior_attempt_count = len(attempts)
    for retry_number in range(1, max_attempts + 1):
        attempt_number = prior_attempt_count + retry_number
        request = dict(kwargs)
        request["messages"] = (
            [{"role": "user", "content": repair_message}]
            if repair_message is not None else kwargs["messages"]
        )
        started = time.perf_counter()
        try:
            response = client.chat.completions.create(**request)
        except Exception as exc:
            if "temperature" not in str(exc).lower() or "temperature" not in kwargs:
                raise
            kwargs.pop("temperature")
            request.pop("temperature", None)
            response = client.chat.completions.create(**request)
        latency = time.perf_counter() - started
        content = response.choices[0].message.content or ""
        usage = response.usage
        attempt = {
            "attempt": attempt_number,
            "request_kind": "schema_repair" if repair_message is not None else "quality_judgment",
            "request": request,
            "response": {
                "id": getattr(response, "id", None),
                "model": getattr(response, "model", None),
                "created": getattr(response, "created", None),
                "content": content,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": getattr(
                        usage, "total_tokens", usage.prompt_tokens + usage.completion_tokens
                    ),
                },
            },
            "latency_milliseconds": round(latency * 1000),
        }
        try:
            result = validate_judge_response(_parse_json(content))
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            attempt["validation"] = {
                "valid": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            attempts.append(attempt)
            if receipt_path is not None:
                write_json_atomic(receipt_path, {
                    "schema_version": 1,
                    "credential_free": True,
                    "attempts": attempts,
                })
            if retry_number == max_attempts:
                raise RuntimeError(
                    f"judge response failed schema validation after {attempt_number} total attempts: {exc}"
                ) from exc
            repair_message = repair_prompt(content, exc)
            continue
        attempt["validation"] = {"valid": True}
        attempts.append(attempt)
        if receipt_path is not None:
            write_json_atomic(receipt_path, {
                "schema_version": 1,
                "credential_free": True,
                "attempts": attempts,
            })
        return result, {
            "prompt_tokens": sum(row["response"]["usage"]["prompt_tokens"] for row in attempts),
            "completion_tokens": sum(
                row["response"]["usage"]["completion_tokens"] for row in attempts
            ),
            "latency_milliseconds": sum(row["latency_milliseconds"] for row in attempts),
            "attempt_count": len(attempts),
        }
    raise AssertionError("unreachable judge retry loop")


def aggregate_judges(chapter_judges: list[dict[str, Any]]) -> dict[str, Any]:
    scores = {
        mode: {dimension: [] for dimension in DIMENSIONS}
        for mode in ("orchestration", "single_agent")
    }
    preferences = {"orchestration": 0, "single_agent": 0, "tie": 0}
    for row in chapter_judges:
        mapping = row["alias_to_mode"]
        result = row["result"]
        for alias, dimensions in result["variants"].items():
            mode = mapping[alias]
            for dimension, item in dimensions.items():
                scores[mode][dimension].append(item["score"])
        preferred = result["preferred"]
        preferences["tie" if preferred == "tie" else mapping[preferred]] += 1
    modes = {}
    for mode, dimensions in scores.items():
        means = {key: sum(values) / len(values) for key, values in dimensions.items()}
        modes[mode] = {"dimension_means": means, "overall_mean": sum(means.values()) / len(means)}
    return {"modes": modes, "chapter_preferences": preferences}


def source_statistics(chapters: dict[str, str]) -> dict[str, Any]:
    return {
        "chapter_count": len(chapters),
        "bytes": sum(len(text.encode("utf-8")) for text in chapters.values()),
        "lines": sum(len(text.splitlines()) for text in chapters.values()),
        "image_references": sum(len(image_targets(text)) for text in chapters.values()),
        "fenced_code_blocks": sum(len(fenced_code_payloads(text)) for text in chapters.values()),
        "link_references": sum(len(link_targets(text)) for text in chapters.values()),
    }


def tracker_receipt(tracker) -> dict[str, Any]:
    return {
        "calls": tracker.calls,
        "by_agent": tracker.by_agent(),
        "total_tokens": tracker.total_tokens(),
    }


def write_json_atomic(path: Path, value: Any) -> None:
    """Persist a restart checkpoint without exposing half-written JSON."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def serialize_arm(result: dict[str, Any]) -> dict[str, Any]:
    """Convert an agents.py arm result into credential-free checkpoint JSON."""
    return {
        **{key: value for key, value in result.items() if key != "tracker"},
        "tracker_calls": result["tracker"].calls,
    }


def restore_arm(payload: dict[str, Any], agents_module: Any) -> dict[str, Any]:
    value = dict(payload)
    calls = value.pop("tracker_calls")
    tracker = agents_module.TokenTracker()
    tracker.calls = calls
    value["tracker"] = tracker
    return value


def campaign_fingerprint(
    chapters: dict[str, str], translation_units: dict[str, str], provider: str, model: str
) -> str:
    contract = {
        "chapters": {title: sha256_text(text) for title, text in chapters.items()},
        "translation_units": {
            title: sha256_text(text) for title, text in translation_units.items()
        },
        "provider": provider,
        "model": model,
        "thinking": "disabled" if provider in ("ark", "Volcengine ARK") else "provider_default",
    }
    return sha256_text(json.dumps(contract, ensure_ascii=False, sort_keys=True))


def load_checkpoint(path: Path, fingerprint: str) -> Any | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("campaign_fingerprint") != fingerprint:
        raise RuntimeError(f"checkpoint does not match this campaign: {path}")
    return payload["value"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Official full-scope Experiment 10-3 campaign")
    parser.add_argument("--source", action="append", help="Markdown chapter; repeat (default: book-en ch1/ch2)")
    parser.add_argument("--provider", choices=("mistral", "ark", "openai", "openrouter"), default="mistral")
    parser.add_argument("--model", help="translation model (default chosen for provider)")
    parser.add_argument(
        "--max-unit-characters", type=int, default=20_000,
        help="Markdown-safe translation unit size (default: 20000)",
    )
    parser.add_argument("--output-dir", help="validation directory (default timestamped)")
    args = parser.parse_args()
    load_dotenv(HERE / ".env")
    os.environ["LLM_PROVIDER"] = args.provider
    if args.model:
        os.environ["OPENAI_MODEL"] = args.model

    # Import only after provider/model selection because agents reads its configuration at import time.
    import agents
    import consistency

    paths = [Path(item).resolve() for item in args.source] if args.source else list(DEFAULT_SOURCES)
    chapters, source_paths = load_source_book(paths)
    translation_units, chapter_units = split_translation_units(
        chapters, max_characters=args.max_unit_characters
    )
    stats = source_statistics(chapters)
    stats["translation_unit_count"] = len(translation_units)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = Path(args.output_dir).resolve() if args.output_dir else HERE / "validation" / f"real_{timestamp}"
    output.mkdir(parents=True, exist_ok=True)
    fingerprint = campaign_fingerprint(
        chapters, translation_units, agents.ACTIVE_PROVIDER or args.provider, agents.MODEL
    )

    started = time.perf_counter()
    orch_started = time.perf_counter()
    orchestration_checkpoint = output / "orchestration_checkpoint.json"
    saved_orchestration = load_checkpoint(orchestration_checkpoint, fingerprint)
    if saved_orchestration is None:
        orchestration = agents.run_orchestration(
            translation_units, str(output / "orchestration_parts"),
            source_lang="英文", target_lang="中文"
        )
        orchestration_elapsed = time.perf_counter() - orch_started
        write_json_atomic(orchestration_checkpoint, {
            "campaign_fingerprint": fingerprint,
            "value": {
                "result": serialize_arm(orchestration),
                "elapsed_seconds": orchestration_elapsed,
            },
        })
    else:
        orchestration = restore_arm(saved_orchestration["result"], agents)
        orchestration_elapsed = saved_orchestration["elapsed_seconds"]
    single_started = time.perf_counter()
    single_checkpoint = output / "single_agent_checkpoint.json"
    saved_single = load_checkpoint(single_checkpoint, fingerprint)
    if saved_single is None:
        single = agents.run_single_agent(
            translation_units, str(output / "single_agent_parts"),
            source_lang="英文", target_lang="中文"
        )
        single_elapsed = time.perf_counter() - single_started
        write_json_atomic(single_checkpoint, {
            "campaign_fingerprint": fingerprint,
            "value": {
                "result": serialize_arm(single),
                "elapsed_seconds": single_elapsed,
            },
        })
    else:
        single = restore_arm(saved_single["result"], agents)
        single_elapsed = saved_single["elapsed_seconds"]

    orchestration_complete = reassemble_translations(orchestration["translations"], chapter_units)
    single_complete = reassemble_translations(single["translations"], chapter_units)
    for mode, complete in (
        ("orchestration", orchestration_complete), ("single_agent", single_complete)
    ):
        destination = output / mode
        destination.mkdir(parents=True, exist_ok=True)
        for index, (title, text) in enumerate(complete.items(), start=1):
            (destination / f"chapter{index}_zh.md").write_text(text, encoding="utf-8")

    fidelity = {"orchestration": {}, "single_agent": {}}
    for title, source in chapters.items():
        fidelity["orchestration"][title] = markdown_fidelity(source, orchestration_complete[title])
        fidelity["single_agent"][title] = markdown_fidelity(source, single_complete[title])

    judge_client, judge_model, judge_provider = make_judge()
    judge_checkpoint = output / "judge_checkpoint.json"
    judge_receipt_dir = output / "judge_receipts"
    judge_receipt_dir.mkdir(parents=True, exist_ok=True)
    judge_rows = load_checkpoint(judge_checkpoint, fingerprint) or []
    expected_titles = list(translation_units)
    if [row.get("chapter") for row in judge_rows] != expected_titles[:len(judge_rows)]:
        raise RuntimeError("judge checkpoint order does not match translation units")
    for index, (title, source) in enumerate(translation_units.items()):
        if index < len(judge_rows):
            continue
        alias_to_mode = (
            {"X": "orchestration", "Y": "single_agent"}
            if index % 2 == 0 else {"X": "single_agent", "Y": "orchestration"}
        )
        translations = {
            "orchestration": orchestration["translations"][title],
            "single_agent": single["translations"][title],
        }
        result, usage = judge_chapter(
            judge_client, judge_model, source,
            translations[alias_to_mode["X"]], translations[alias_to_mode["Y"]],
            disable_thinking=judge_provider == "Volcengine ARK",
            receipt_path=judge_receipt_dir / f"unit-{index + 1:02d}.json",
        )
        receipt = judge_receipt_dir / f"unit-{index + 1:02d}.json"
        judge_rows.append({
            "chapter": title,
            "alias_to_mode": alias_to_mode,
            "result": result,
            "usage": usage,
            "receipt": str(receipt.relative_to(output)),
            "receipt_sha256": sha256(receipt),
        })
        write_json_atomic(judge_checkpoint, {
            "campaign_fingerprint": fingerprint,
            "value": judge_rows,
        })

    orch_consistency = consistency.analyze(orchestration_complete)
    single_consistency = consistency.analyze(single_complete)
    orch_adherence = consistency.check_adherence(orchestration_complete)
    single_adherence = consistency.check_adherence(single_complete)
    all_agent_types = set(orchestration["tracker"].by_agent())
    translation_calls = orchestration["tracker"].calls + single["tracker"].calls
    translation_fingerprints = {
        (call.get("provider"), call.get("model"), call.get("thinking"))
        for call in translation_calls
    }
    translation_provider, translation_model, translation_thinking = (
        next(iter(translation_fingerprints))
        if len(translation_fingerprints) == 1 else (None, None, None)
    )

    current_source_paths = [HERE / "run_official_experiment.py", HERE / "agents.py", HERE / "consistency.py"]
    checkpoint_paths = [orchestration_checkpoint, single_checkpoint, judge_checkpoint]
    translation_output_paths = [
        output / mode / f"chapter{index}_zh.md"
        for mode in ("orchestration", "single_agent")
        for index in range(1, len(chapters) + 1)
    ]
    prior_failure = output / "prior_judge_failure.json"

    def repo_hash_map(files: list[Path]) -> dict[str, str]:
        return {
            str(path.resolve().relative_to(REPO)): sha256(path)
            for path in files if path.is_file()
        }

    provenance = {
        "campaign_fingerprint": fingerprint,
        "current_acceptance_sources_sha256": repo_hash_map(current_source_paths),
        "arm_and_judge_checkpoints_sha256": repo_hash_map(checkpoint_paths),
        "reassembled_translation_outputs_sha256": repo_hash_map(translation_output_paths),
        "raw_judge_receipts_sha256": {
            str((output / row["receipt"]).resolve().relative_to(REPO)): row["receipt_sha256"]
            for row in judge_rows
        },
        "negative_provenance_sha256": repo_hash_map([prior_failure]),
        "resume_note": (
            "The long campaign resumed from fingerprint-bound arm and judge checkpoints. "
            "Current acceptance-source hashes bind the final validator/evidence builder; immutable "
            "raw judge receipts retain every schema failure and repair call."
        ),
    }
    declared_provenance_hashes = {
        key: digest
        for field in (
            "current_acceptance_sources_sha256",
            "arm_and_judge_checkpoints_sha256",
            "reassembled_translation_outputs_sha256",
            "raw_judge_receipts_sha256",
            "negative_provenance_sha256",
        )
        for key, digest in provenance[field].items()
    }
    receipt_payloads = [
        json.loads((output / row["receipt"]).read_text(encoding="utf-8"))
        for row in judge_rows
    ]
    judge_attempt_count = sum(len(item.get("attempts", [])) for item in receipt_payloads)
    rejected_judge_attempt_count = sum(
        not attempt.get("validation", {}).get("valid", False)
        for item in receipt_payloads for attempt in item.get("attempts", [])
    )
    gates = {
        "real_illustrated_code_heavy_technical_book": (
            stats["chapter_count"] >= 2 and stats["bytes"] >= 200_000
            and stats["image_references"] >= 10 and stats["fenced_code_blocks"] >= 5
        ),
        "four_agent_roles_executed": {"Glossary", "Translation", "Proofreading", "Manager"}.issubset(all_agent_types),
        "both_modes_translated_every_chapter": all(
            orchestration_complete.get(title, "").strip()
            and single_complete.get(title, "").strip()
            for title in chapters
        ),
        "real_usage_recorded_for_every_call": all(
            call.get("prompt_tokens", 0) > 0 and call.get("provider") and call.get("model")
            for call in translation_calls
        ),
        "uniform_translation_api_fingerprint": (
            len(translation_fingerprints) == 1
            and all((translation_provider, translation_model, translation_thinking))
        ),
        "manager_context_excludes_translation_bodies": all(
            text not in json.dumps(orchestration["manager_context_final"], ensure_ascii=False)
            for text in orchestration["translations"].values()
        ),
        "quality_compared_for_every_translation_unit": len(judge_rows) == len(translation_units),
        "raw_judge_receipts_hashed": len(judge_rows) == len(translation_units) and all(
            (output / row.get("receipt", "missing")).is_file()
            and sha256(output / row["receipt"]) == row.get("receipt_sha256")
            for row in judge_rows
        ),
        "raw_judge_response_ids_and_usage_recorded": all(
            item.get("attempts") and all(
                attempt.get("response", {}).get("id")
                and attempt.get("response", {}).get("usage", {}).get("prompt_tokens", 0) > 0
                and attempt.get("response", {}).get("usage", {}).get("completion_tokens", 0) > 0
                for attempt in item["attempts"]
            )
            for item in receipt_payloads
        ),
        "checkpoint_fingerprints_match": all(
            json.loads(path.read_text(encoding="utf-8")).get("campaign_fingerprint") == fingerprint
            for path in checkpoint_paths
        ),
        "all_declared_provenance_hashes_match": all(
            (REPO / relative).is_file() and sha256(REPO / relative) == digest
            for relative, digest in declared_provenance_hashes.items()
        ),
        "efficiency_and_resources_compared": (
            orchestration_elapsed > 0 and single_elapsed > 0
            and orchestration["tracker"].total_tokens() > 0 and single["tracker"].total_tokens() > 0
        ),
    }
    artifact = {
        "schema_version": 1,
        "experiment": "10-3",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_book": {
            "identity": "AI Agents in Depth, English edition, Chapters 1-2",
            "paths": source_paths,
            "sha256": {title: sha256(paths[index]) for index, title in enumerate(chapters)},
            "statistics": stats,
            "max_translation_unit_characters_requested": args.max_unit_characters,
            "translation_unit_sha256": {
                title: sha256_text(text) for title, text in translation_units.items()
            },
            "chapter_translation_units": chapter_units,
        },
        "translation_api": {
            "provider": translation_provider,
            "model": translation_model,
            "thinking": translation_thinking,
        },
        "quality_judge_api": {
            "provider": judge_provider,
            "model": judge_model,
            "thinking": "disabled" if judge_provider == "Volcengine ARK" else "provider_default",
            "raw_receipted_calls": judge_attempt_count,
            "known_pre_receipt_failures": 1 if prior_failure.is_file() else 0,
            "known_total_calls": judge_attempt_count + (1 if prior_failure.is_file() else 0),
            "rejected_receipted_schema_attempts": rejected_judge_attempt_count,
            "lossless_local_schema_normalizations": sum(
                bool(row["result"].get("schema_repairs")) for row in judge_rows
            ),
            "schema_formatting_repair_api_calls": sum(
                attempt.get("request_kind") == "schema_repair"
                for item in receipt_payloads for attempt in item.get("attempts", [])
            ),
            "prompt_tokens": sum(row["usage"]["prompt_tokens"] for row in judge_rows),
            "completion_tokens": sum(row["usage"]["completion_tokens"] for row in judge_rows),
            "latency_milliseconds": sum(
                row["usage"]["latency_milliseconds"] for row in judge_rows
            ),
        },
        "modes": {
            "orchestration": {
                "elapsed_seconds": orchestration_elapsed,
                "manager_context_peak": orchestration["manager_context_peak"],
                "tracker": tracker_receipt(orchestration["tracker"]),
                "terminology_consistency": orch_consistency,
                "mandated_terminology_adherence": orch_adherence,
            },
            "single_agent": {
                "elapsed_seconds": single_elapsed,
                "main_context_peak": single["main_context_peak"],
                "tracker": tracker_receipt(single["tracker"]),
                "terminology_consistency": single_consistency,
                "mandated_terminology_adherence": single_adherence,
            },
        },
        "markdown_fidelity": fidelity,
        "blinded_quality_judges": judge_rows,
        "quality_aggregate": aggregate_judges(judge_rows),
        "comparison": {
            "context_peak": {
                "orchestration_manager": orchestration["manager_context_peak"],
                "single_agent": single["main_context_peak"],
            },
            "wall_clock_seconds": {
                "orchestration": orchestration_elapsed,
                "single_agent": single_elapsed,
            },
            "total_tokens": {
                "orchestration": orchestration["tracker"].total_tokens(),
                "single_agent": single["tracker"].total_tokens(),
            },
        },
        "provenance": provenance,
        "acceptance_gates": gates,
        "experiment_execution_complete": all(gates.values()),
        "total_campaign_active_seconds": (
            orchestration_elapsed + single_elapsed
            + sum(row["usage"]["latency_milliseconds"] for row in judge_rows) / 1000
        ),
        "finalization_session_seconds": time.perf_counter() - started,
        "interpretation_rule": (
            "Completion means the full comparison ran with real APIs and all required metrics; "
            "it does not require the Manager workflow to win every metric."
        ),
    }
    evidence = output / "evidence.json"
    evidence.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    latest = HERE / "validation" / "latest.json"
    latest.write_text(json.dumps({
        "experiment": "10-3",
        "status": "complete" if artifact["experiment_execution_complete"] else "incomplete",
        "evidence": str(evidence.relative_to(HERE)),
        "evidence_sha256": sha256(evidence),
        "acceptance_gates": gates,
        "comparison": artifact["comparison"],
        "quality_aggregate": artifact["quality_aggregate"],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "evidence": str(evidence),
        "complete": artifact["experiment_execution_complete"],
        "source_statistics": stats,
        "comparison": artifact["comparison"],
        "quality": artifact["quality_aggregate"],
    }, ensure_ascii=False, indent=2))
    return 0 if artifact["experiment_execution_complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
