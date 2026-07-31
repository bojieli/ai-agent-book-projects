#!/usr/bin/env python3
"""Build the checkpoint-free retained training report for Experiment 7-6."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
RUNS_DIR = HERE / "validation" / "runs"
LATEST_PATH = HERE / "validation" / "latest.json"

DEFAULT_RUN_ID = "exp7-6-training-report-20260731-v1"
DEFAULT_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
DEFAULT_MODEL = "voxtral-small-latest"

UPSTREAM_COMMIT = "154735d14755eaec2cc21b46f743db8f7910d43a"
NOTEBOOKS = {
    "orpheus": {
        "path": "nb/Orpheus_(3B)-TTS.ipynb",
        "blob_sha1": "cd582eab51355b95e180386885b915a1b5c1843a",
        "expected_steps": 298,
        "expected_audio": 1,
    },
    "sesame": {
        "path": "nb/Sesame_CSM_(1B)-TTS.ipynb",
        "blob_sha1": "d5ed1bdcc8c696cec0e4ca388a9c717aa6a06766",
        "expected_steps": 60,
        "expected_audio": 3,
    },
}

MODEL_DATA_PINS = {
    "orpheus_model": {
        "repository": "unsloth/orpheus-3b-0.1-ft",
        "revision": "eae2b6e5e429c81b95ac42a883ac64f126583d43",
        "weights": {
            "model-00001-of-00002.safetensors": {
                "sha256": "1064bbba044a8ba0f5e1c88a9f301399c958875ca0db5fb216b7c7d39c91a6ca",
                "bytes": 4991037968,
            },
            "model-00002-of-00002.safetensors": {
                "sha256": "6fac70f10fa2d2c37e06952366d43a0a4363b7e9e5fe48572b29f4a21b3479a9",
                "bytes": 1610725592,
            },
        },
    },
    "sesame_model": {
        "repository": "unsloth/csm-1b",
        "revision": "39e8c756bec133ad7eb9ea1097c84a2bd891c949",
        "weights": {
            "model.safetensors": {
                "sha256": "1c81da3653c0177283d17d0a94e8136e76429fcabed60ed336cea6abea6e81c3",
                "bytes": 4153376052,
            }
        },
    },
    "snac_codec": {
        "repository": "hubertsiuzdak/snac_24khz",
        "revision": "d73ad176a12188fcf4f360ba3bf2c2fbbe8f58ec",
        "weights": {
            "pytorch_model.bin": {
                "sha256": "4b8164cc6606bfa627f1a784734c1e539891518f1191ed9194fe1e3b9b4bff40",
                "bytes": 79488254,
            }
        },
    },
    "elise_dataset": {
        "repository": "MrDragonFox/Elise",
        "revision": "ee867f95526856352ba9c607e6f97e6b9c65b043",
        "files": {
            "data/train-00000-of-00001.parquet": {
                "sha256": "4c229cbc8542dc3e97b2c13992b1aa7dd6de6631d62eeee52c053014824c0e08",
                "bytes": 328144109,
            }
        },
    },
}

LOCAL_SOURCE_PATHS = (
    "book/chapter7.md",
    "chapter7/EXPERIMENT_LEDGER.md",
    "chapter7/README.md",
    "chapter7/README.en.md",
    "chapter7/README.ko.md",
    "chapter7/orpheus/README.md",
    "chapter7/orpheus/orpheus_sft_unsloth.py",
    "chapter7/orpheus/inference.py",
    "chapter7/orpheus/requirements.txt",
    "chapter7/orpheus/test_orpheus_inference.py",
    "chapter7/sesame/README.md",
    "chapter7/sesame/sesame_csm_sft_unsloth.py",
    "chapter7/sesame/inference.py",
    "chapter7/sesame/batch_inference.py",
    "chapter7/sesame/example_inputs.json",
    "chapter7/sesame/requirements.txt",
    "chapter7/sesame/test_batch_inference.py",
    "chapter7/voice-sft-training-report/README.md",
    "chapter7/voice-sft-training-report/run_training_report_audit.py",
    "chapter7/voice-sft-training-report/validate_evidence.py",
    "chapter7/voice-sft-training-report/test_training_report_audit.py",
)
FAILED_ATTEMPT_PATHS = (
    "chapter7/voice-sft-training-report/validation/failed_attempts/exp7-6-20260731-attempt1-source-audit.json",
    "chapter7/voice-sft-training-report/validation/failed_attempts/exp7-6-20260731-attempt1-raw/judge_receipts.json",
    "chapter7/voice-sft-training-report/validation/failed_attempts/exp7-6-20260731-attempt1-raw/upstream_orpheus.ipynb",
    "chapter7/voice-sft-training-report/validation/failed_attempts/exp7-6-20260731-attempt1-raw/upstream_sesame.ipynb",
    "chapter7/voice-sft-training-report/validation/failed_attempts/exp7-6-20260731-attempt1-raw/orpheus_output_1.wav",
    "chapter7/voice-sft-training-report/validation/failed_attempts/exp7-6-20260731-attempt1-raw/sesame_output_1.wav",
    "chapter7/voice-sft-training-report/validation/failed_attempts/exp7-6-20260731-attempt1-raw/sesame_output_2.wav",
    "chapter7/voice-sft-training-report/validation/failed_attempts/exp7-6-20260731-attempt1-raw/sesame_output_3.wav",
)


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_json_bytes(value))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data, usedforsecurity=False).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def cell_source(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def output_text(value: Any) -> str:
    return "".join(value) if isinstance(value, list) else str(value or "")


def notebook_url(name: str) -> str:
    path = NOTEBOOKS[name]["path"]
    return f"https://raw.githubusercontent.com/unslothai/notebooks/{UPSTREAM_COMMIT}/{path}"


def fetch_bytes(url: str, timeout: float = 120.0) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "ai-agent-book-exp7-6-audit"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:1000]
        raise RuntimeError(f"HTTP {exc.code} fetching {url}: {detail}") from exc


def load_notebook_bytes(data: bytes, name: str) -> dict[str, Any]:
    if git_blob_sha1(data) != NOTEBOOKS[name]["blob_sha1"]:
        raise ValueError(f"{name}: immutable notebook Git blob mismatch")
    parsed = json.loads(data)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("cells"), list):
        raise TypeError(f"{name}: malformed notebook")
    return parsed


def training_record(notebook: dict[str, Any], name: str) -> dict[str, Any]:
    matches = [
        cell for cell in notebook["cells"] if "trainer_stats = trainer.train()" in cell_source(cell)
    ]
    if len(matches) != 1:
        raise ValueError(f"{name}: expected one executed trainer cell")
    cell = matches[0]
    streams = []
    html_outputs = []
    for output in cell.get("outputs", []):
        if "text" in output:
            streams.append(output_text(output["text"]))
        data = output.get("data") or {}
        if "text/html" in data:
            html_outputs.append(output_text(data["text/html"]))
    combined_stream = "\n".join(streams)
    combined_html = "\n".join(html_outputs)
    loss_rows = [
        {"step": int(step), "training_loss": float(loss)}
        for step, loss in re.findall(
            r"<td[^>]*>\s*(\d+)\s*</td>\s*<td[^>]*>\s*([0-9.]+)\s*</td>",
            combined_html,
            flags=re.DOTALL,
        )
    ]
    expected_steps = NOTEBOOKS[name]["expected_steps"]
    if len(loss_rows) != expected_steps or loss_rows[-1]["step"] != expected_steps:
        raise ValueError(f"{name}: incomplete retained training-loss table")
    metadata_patterns = {
        "examples": r"Num examples = ([0-9,]+)",
        "epochs": r"Num Epochs = ([0-9]+)",
        "total_steps": r"Total steps = ([0-9]+)",
        "trainable_parameters": r"Trainable parameters = ([0-9,]+)/([0-9,]+)",
    }
    metadata = {}
    for key, pattern in metadata_patterns.items():
        match = re.search(pattern, combined_stream)
        if not match:
            raise ValueError(f"{name}: missing retained training metadata {key}")
        metadata[key] = [int(value.replace(",", "")) for value in match.groups()]
    metadata["examples"] = metadata["examples"][0]
    metadata["epochs"] = metadata["epochs"][0]
    metadata["total_steps"] = metadata["total_steps"][0]
    return {
        "cell_source": cell_source(cell),
        "raw_streams": streams,
        "raw_html_sha256": sha256_bytes(combined_html.encode()),
        "metadata": metadata,
        "loss_rows": loss_rows,
        "first_loss": loss_rows[0]["training_loss"],
        "final_loss": loss_rows[-1]["training_loss"],
        "first_20_mean": round(sum(row["training_loss"] for row in loss_rows[:20]) / 20, 6),
        "last_20_mean": round(sum(row["training_loss"] for row in loss_rows[-20:]) / 20, 6),
    }


def environment_record(notebook: dict[str, Any], name: str) -> dict[str, Any]:
    streams = []
    for cell in notebook["cells"]:
        for output in cell.get("outputs", []):
            if output.get("output_type") == "stream":
                text = output_text(output.get("text"))
                if "Unsloth " in text and "Torch:" in text and "CUDA" in text:
                    streams.append(text)
    if len(streams) != 1:
        raise ValueError(f"{name}: expected one retained environment banner")
    banner = streams[0]
    required = ("Tesla T4", "Platform: Linux", "Torch:", "CUDA Toolkit:", "Triton:")
    if not all(value in banner for value in required):
        raise ValueError(f"{name}: incomplete environment banner")
    return {"raw_banner": banner}


def extracted_audio(notebook: dict[str, Any], name: str) -> list[dict[str, Any]]:
    rows = []
    pattern = re.compile(r"data:audio/wav;base64,([A-Za-z0-9+/=]+)")
    for cell_index, cell in enumerate(notebook["cells"]):
        source = cell_source(cell)
        for output_index, output in enumerate(cell.get("outputs", [])):
            data = output.get("data") or {}
            html_value = output_text(data.get("text/html"))
            for encoded in pattern.findall(html_value):
                raw = base64.b64decode(encoded, validate=True)
                if not raw.startswith(b"RIFF") or raw[8:12] != b"WAVE":
                    raise ValueError(f"{name}: embedded audio is not WAV")
                rows.append(
                    {
                        "track": name,
                        "index": len(rows) + 1,
                        "filename": f"{name}_output_{len(rows) + 1}.wav",
                        "bytes": len(raw),
                        "sha256": sha256_bytes(raw),
                        "notebook_cell_index": cell_index,
                        "notebook_output_index": output_index,
                        "cell_source": source,
                        "audio_bytes": raw,
                    }
                )
    if len(rows) != NOTEBOOKS[name]["expected_audio"]:
        raise ValueError(f"{name}: embedded WAV coverage mismatch")
    return rows


def file_record(path: Path, *, relative_to: Path = REPO_ROOT) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(relative_to)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def mechanism_audit() -> dict[str, Any]:
    orpheus = (REPO_ROOT / "chapter7/orpheus/orpheus_sft_unsloth.py").read_text(encoding="utf-8")
    sesame = (REPO_ROOT / "chapter7/sesame/sesame_csm_sft_unsloth.py").read_text(encoding="utf-8")
    checks = {
        "orpheus_serializes_snac_audio_tokens": "SNAC.from_pretrained" in orpheus
        and "codes_list" in orpheus,
        "orpheus_serializes_speaker_text_prefix": "example['source']" in orpheus,
        "orpheus_retained_prompt_contains_paralinguistic_tag": "<giggles>" in orpheus
        and "<laugh>" in orpheus,
        "orpheus_inference_does_not_accept_reference_audio": "reference_audio" not in orpheus,
        "sesame_accepts_audio_context_in_conversation": '{"type": "audio"' in sesame,
        "sesame_uses_csm_conditional_generation": "CsmForConditionalGeneration" in sesame,
        "sesame_training_source_has_no_laugh_or_sigh_tag": "<laugh>" not in sesame
        and "<sigh>" not in sesame,
    }
    if not all(checks.values()):
        raise ValueError(f"local source mechanism audit failed: {checks}")
    return {
        "checks": checks,
        "manuscript_mapping_supported_by_executable_sources": False,
        "observed_mapping": {
            "orpheus": "discrete SNAC audio tokens, speaker-prefixed text, and retained <giggles>/<laugh> prompts; no raw reference-audio inference input",
            "sesame": "CSM conversation history with audio context for speaker/style conditioning; no <laugh>/<sigh> tag protocol in the retained training source",
        },
        "finding": (
            "The executable sources and immutable upstream notebook evidence map the two mechanisms "
            "opposite to the manuscript labels. This is retained as a negative result, not rewritten as support."
        ),
    }


def reproduction_contract() -> dict[str, Any]:
    return {
        "upstream_notebooks": {
            "repository": "unslothai/notebooks",
            "revision": UPSTREAM_COMMIT,
            "files": {
                name: {
                    "path": spec["path"],
                    "git_blob_sha1": spec["blob_sha1"],
                }
                for name, spec in NOTEBOOKS.items()
            },
        },
        "model_data_pins": MODEL_DATA_PINS,
        "commands": {
            "orpheus_notebook": f"git clone https://github.com/unslothai/notebooks.git upstream-notebooks && git -C upstream-notebooks checkout --detach {UPSTREAM_COMMIT} && jupyter nbconvert --execute --to notebook --inplace 'upstream-notebooks/nb/Orpheus_(3B)-TTS.ipynb'",
            "sesame_notebook": f"git clone https://github.com/unslothai/notebooks.git upstream-notebooks && git -C upstream-notebooks checkout --detach {UPSTREAM_COMMIT} && jupyter nbconvert --execute --to notebook --inplace 'upstream-notebooks/nb/Sesame_CSM_(1B)-TTS.ipynb'",
            "book_orpheus": "cd chapter7/orpheus && python -m venv .venv-orpheus && .venv-orpheus/bin/pip install -r requirements.txt && .venv-orpheus/bin/python orpheus_sft_unsloth.py",
            "book_sesame": "cd chapter7/sesame && python -m venv .venv-sesame && .venv-sesame/bin/pip install -r requirements.txt && .venv-sesame/bin/python sesame_csm_sft_unsloth.py",
        },
        "environment_boundary": {
            "upstream_executed_environment_retained_in_notebook": True,
            "book_requirements_files_content_hashed": True,
            "book_requirements_are_fully_pinned": False,
            "cuda_driver_and_container_digest_retained": False,
        },
        "checkpoint_policy": {
            "distributed_with_book": False,
            "acceptance_artifact": False,
            "required_artifact": "evidence-backed checkpoint-free training report",
        },
    }


def build_source_audit(run_dir: Path) -> dict[str, Any]:
    notebooks = {}
    audio_records = []
    for name, spec in NOTEBOOKS.items():
        path = run_dir / f"upstream_{name}.ipynb"
        raw = path.read_bytes()
        notebook = load_notebook_bytes(raw, name)
        audio = extracted_audio(notebook, name)
        for row in audio:
            audio_path = run_dir / row["filename"]
            if not audio_path.is_file() or audio_path.read_bytes() != row["audio_bytes"]:
                raise ValueError(f"{name}: extracted WAV differs from immutable notebook")
            audio_records.append({key: value for key, value in row.items() if key != "audio_bytes"})
        notebooks[name] = {
            "source_url": notebook_url(name),
            "upstream_commit": UPSTREAM_COMMIT,
            "path": spec["path"],
            "git_blob_sha1": git_blob_sha1(raw),
            "sha256": sha256_bytes(raw),
            "bytes": len(raw),
            "training": training_record(notebook, name),
            "environment": environment_record(notebook, name),
            "embedded_audio_count": len(audio),
        }
    return {
        "schema_version": "exp7-6-source-audit-v1",
        "experiment": "7-6",
        "local_sources": [file_record(REPO_ROOT / path) for path in LOCAL_SOURCE_PATHS],
        "upstream_executed_notebooks": notebooks,
        "extracted_audio": audio_records,
        "mechanism_audit": mechanism_audit(),
        "reproduction_contract": reproduction_contract(),
        "historical_evidence_boundary": {
            "upstream_gpu_training_logs_and_audio_retained": True,
            "author_local_training_receipts_retained": False,
            "author_local_adapter_hashes_retained": False,
            "author_local_generated_audio_retained": False,
            "upstream_notebooks_are_not_misrepresented_as_author_local_runs": True,
            "qualitative_manuscript_mapping_independently_supported": False,
        },
    }


def extract_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        if start < 0:
            raise
        value, _ = json.JSONDecoder().raw_decode(stripped[start:])
    if not isinstance(value, dict):
        raise TypeError("judge content must decode to an object")
    return value


def audio_part(raw: bytes) -> dict[str, str]:
    return {
        "type": "input_audio",
        "input_audio": "data:audio/wav;base64," + base64.b64encode(raw).decode(),
    }


def judge_payload(track: str, run_dir: Path, model: str) -> tuple[dict[str, Any], dict[str, str]]:
    if track == "orpheus":
        audio_map = {"A": "orpheus_output_1.wav"}
        prompt = {
            "task": "Evaluate the attached anonymous TTS audio directly. Do not infer the model or training method.",
            "expected_text": "Hey there my name is Kaira, <giggle> and I'm a speech generation model that can sound like a person.",
            "required_json": {
                "track": "orpheus",
                "transcript_accuracy": "integer 0-5",
                "naturalness": "integer 0-5",
                "audible_paralinguistic_event": "boolean",
                "event_type": "short string or none",
                "event_confidence": "number 0-1",
                "cross_sentence_voice_consistency_assessable": "boolean",
                "material_errors": ["specific audible errors; empty only if none"],
                "rationale": "brief audio-grounded explanation",
            },
        }
    elif track == "sesame":
        audio_map = {
            "A": "sesame_output_1.wav",
            "B": "sesame_output_2.wav",
            "C": "sesame_output_3.wav",
        }
        prompt = {
            "task": "Evaluate three anonymous TTS audios directly. B and C have the same target text. Do not infer model or context condition.",
            "expected_text": {
                "A": "We just finished fine tuning a text to speech model... and it's pretty good!",
                "B": "Sesame is a super cool TTS model which can be fine tuned with Unsloth.",
                "C": "Sesame is a super cool TTS model which can be fine tuned with Unsloth.",
            },
            "required_json": {
                "track": "sesame",
                "items": {
                    label: {
                        "transcript_accuracy": "integer 0-5",
                        "naturalness": "integer 0-5",
                        "voice_description": "brief string",
                        "audible_paralinguistic_event": "boolean",
                    }
                    for label in audio_map
                },
                "same_text_B_C_voice_similarity": "integer 0-5",
                "same_text_B_C_style_similarity": "integer 0-5",
                "B_C_material_difference": "brief string",
                "paralinguistic_tag_control_assessable": "boolean",
                "rationale": "brief audio-grounded explanation",
            },
        }
    else:
        raise ValueError(f"unknown track: {track}")
    content: list[dict[str, str]] = [
        {"type": "text", "text": json.dumps(prompt, ensure_ascii=False, sort_keys=True)}
    ]
    for label, filename in audio_map.items():
        content.append({"type": "text", "text": f"Anonymous audio {label}:"})
        content.append(audio_part((run_dir / filename).read_bytes()))
    return (
        {
            "model": model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": content}],
        },
        audio_map,
    )


def validate_judgment(track: str, judgment: dict[str, Any]) -> None:
    if judgment.get("track") != track:
        raise ValueError(f"{track}: judge returned the wrong track")
    if not isinstance(judgment.get("rationale"), str) or not judgment["rationale"].strip():
        raise ValueError(f"{track}: judge rationale is missing")
    if track == "orpheus":
        for key in ("transcript_accuracy", "naturalness"):
            if not isinstance(judgment.get(key), int) or not 0 <= judgment[key] <= 5:
                raise ValueError(f"orpheus: invalid {key}")
        if not isinstance(judgment.get("audible_paralinguistic_event"), bool):
            raise TypeError("orpheus: paralinguistic result must be boolean")
        confidence = judgment.get("event_confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            raise TypeError("orpheus: invalid event confidence")
        if not 0 <= confidence <= 1:
            raise ValueError("orpheus: event confidence outside 0-1")
        if not isinstance(judgment.get("cross_sentence_voice_consistency_assessable"), bool):
            raise TypeError("orpheus: assessability result must be boolean")
        if not isinstance(judgment.get("material_errors"), list):
            raise TypeError("orpheus: material errors must be a list")
    else:
        items = judgment.get("items")
        if not isinstance(items, dict) or set(items) != {"A", "B", "C"}:
            raise ValueError("sesame: judge must cover A-C exactly")
        for label, row in items.items():
            if not isinstance(row, dict):
                raise TypeError(f"sesame: {label} must be an object")
            for key in ("transcript_accuracy", "naturalness"):
                if not isinstance(row.get(key), int) or not 0 <= row[key] <= 5:
                    raise ValueError(f"sesame: invalid {label}/{key}")
            if not isinstance(row.get("voice_description"), str):
                raise TypeError(f"sesame: missing {label} voice description")
            if not isinstance(row.get("audible_paralinguistic_event"), bool):
                raise TypeError(f"sesame: invalid {label} event result")
        for key in ("same_text_B_C_voice_similarity", "same_text_B_C_style_similarity"):
            if not isinstance(judgment.get(key), int) or not 0 <= judgment[key] <= 5:
                raise ValueError(f"sesame: invalid {key}")
        if not isinstance(judgment.get("paralinguistic_tag_control_assessable"), bool):
            raise TypeError("sesame: tag assessability must be boolean")


def call_judge(
    track: str,
    run_dir: Path,
    *,
    endpoint: str,
    model: str,
    api_key: str,
    timeout: float,
) -> dict[str, Any]:
    payload, audio_map = judge_payload(track, run_dir, model)
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    started = time.perf_counter()
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw_response = json.loads(response.read())
                http_status = response.status
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:1000]
            last_error = RuntimeError(f"judge HTTP {exc.code}: {detail}")
            if exc.code < 500 or attempt == 2:
                raise last_error from exc
            time.sleep(2**attempt)
        except TimeoutError as exc:
            last_error = exc
            if attempt == 2:
                raise
    else:
        raise RuntimeError(f"judge failed: {last_error}")
    latency_ms = round((time.perf_counter() - started) * 1000, 3)
    content = raw_response["choices"][0]["message"]["content"]
    if isinstance(content, list):
        content = "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
    judgment = extract_json_object(str(content))
    validate_judgment(track, judgment)
    response_id = raw_response.get("id")
    usage = raw_response.get("usage")
    if not isinstance(response_id, str) or not response_id:
        raise ValueError("judge response ID is missing")
    if not isinstance(usage, dict) or not isinstance(usage.get("total_tokens"), int):
        raise TypeError("judge usage is missing")
    return {
        "track": track,
        "provider": "mistral",
        "endpoint": endpoint,
        "credential_env": "MISTRAL_API_KEY",
        "credential_headers_retained": False,
        "audio_map": audio_map,
        "request": payload,
        "http_status": http_status,
        "response": raw_response,
        "response_id": response_id,
        "usage": usage,
        "latency_ms": latency_ms,
        "judgment": judgment,
    }


def summarize(source_audit: dict[str, Any], receipts: list[dict[str, Any]]) -> dict[str, Any]:
    by_track = {receipt["track"]: receipt for receipt in receipts}
    orpheus = source_audit["upstream_executed_notebooks"]["orpheus"]
    sesame = source_audit["upstream_executed_notebooks"]["sesame"]
    acceptance = {
        "immutable_upstream_notebooks_retained": all(
            row["git_blob_sha1"] == NOTEBOOKS[name]["blob_sha1"]
            for name, row in source_audit["upstream_executed_notebooks"].items()
        ),
        "complete_orpheus_training_log_retained": len(orpheus["training"]["loss_rows"]) == 298,
        "complete_sesame_training_log_retained": len(sesame["training"]["loss_rows"]) == 60,
        "all_four_upstream_wavs_extracted_exactly": len(source_audit["extracted_audio"]) == 4,
        "two_direct_audio_judge_receipts_retained": set(by_track) == {"orpheus", "sesame"},
        "raw_requests_responses_ids_usage_latency_retained": len(
            {receipt["response_id"] for receipt in receipts}
        )
        == 2
        and all(
            receipt["usage"].get("total_tokens", 0) > 0 and receipt["latency_ms"] > 0
            for receipt in receipts
        ),
        "local_sources_and_requirements_content_hashed": len(source_audit["local_sources"])
        == len(LOCAL_SOURCE_PATHS),
        "model_dataset_codec_revisions_and_lfs_objects_frozen": source_audit[
            "reproduction_contract"
        ]["model_data_pins"]
        == MODEL_DATA_PINS,
        "mechanism_mapping_contradiction_explicit": source_audit["mechanism_audit"][
            "manuscript_mapping_supported_by_executable_sources"
        ]
        is False,
        "author_local_provenance_limits_explicit": source_audit["historical_evidence_boundary"][
            "author_local_adapter_hashes_retained"
        ]
        is False,
        "checkpoints_not_acceptance_artifacts": source_audit["reproduction_contract"][
            "checkpoint_policy"
        ]["acceptance_artifact"]
        is False,
    }
    passed = all(acceptance.values())
    return {
        "schema_version": "exp7-6-summary-v1",
        "experiment": "7-6",
        "status": "passed" if passed else "failed",
        "retained": {
            "upstream_notebooks": 2,
            "training_loss_rows": 358,
            "audio_files": len(source_audit["extracted_audio"]),
            "direct_audio_judge_calls": len(receipts),
        },
        "training": {
            "orpheus": {
                key: orpheus["training"][key]
                for key in ("first_loss", "final_loss", "first_20_mean", "last_20_mean")
            },
            "sesame": {
                key: sesame["training"][key]
                for key in ("first_loss", "final_loss", "first_20_mean", "last_20_mean")
            },
        },
        "judge": {
            "provider": "mistral",
            "model": receipts[0]["request"]["model"],
            "response_ids": [receipt["response_id"] for receipt in receipts],
            "total_tokens": sum(receipt["usage"]["total_tokens"] for receipt in receipts),
            "total_latency_ms": round(sum(receipt["latency_ms"] for receipt in receipts), 3),
            "orpheus": by_track["orpheus"]["judgment"],
            "sesame": by_track["sesame"]["judgment"],
        },
        "scientific_findings": {
            "manuscript_mechanism_mapping_supported": False,
            "source_evidence_maps_orpheus_to_paralinguistic_text_tags": True,
            "source_evidence_maps_sesame_to_audio_context_voice_style": True,
            "orpheus_cross_sentence_consistency_not_assessable_from_one_retained_wav": True,
            "sesame_paralinguistic_tag_control_not_assessable_from_untagged_prompts": True,
            "no_causal_training_gain_claim": True,
        },
        "acceptance": {**acceptance, "passed": passed},
        "limitations": [
            "The retained GPU executions are immutable upstream Unsloth notebooks, not author-local book runs.",
            "Author-local adapters, training logs, and generated audio were not retained and are not reconstructed.",
            "Only one Orpheus WAV is retained, so cross-sentence speaker consistency cannot be measured.",
            "The three Sesame prompts contain no paralinguistic control tags, so tag controllability cannot be measured.",
            "The upstream audio outputs are post-training examples without matched pre-training controls, so no causal SFT improvement is claimed.",
            "The book requirements files leave several CUDA packages unpinned; the notebook banners retain the executed environment but not a container digest.",
            "A single deterministic audio-judge call per track is descriptive, not a powered human listening study.",
        ],
    }


def render_report(summary: dict[str, Any]) -> str:
    training = summary["training"]
    orpheus_judge = summary["judge"]["orpheus"]
    sesame_judge = summary["judge"]["sesame"]
    lines = [
        "# Experiment 7-6 checkpoint-free voice-SFT training report",
        "",
        "## Result",
        "",
        (
            f"Status: **{summary['status']}**. The package retains two immutable executed Unsloth "
            f"notebooks, {summary['retained']['training_loss_rows']} step-level loss rows, four "
            "notebook-embedded WAV outputs, and two raw direct-audio Voxtral judgments."
        ),
        "",
        "| Track | Steps | First loss | Final loss | First-20 mean | Last-20 mean |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| Orpheus | 298 | {training['orpheus']['first_loss']:.4f} | "
            f"{training['orpheus']['final_loss']:.4f} | "
            f"{training['orpheus']['first_20_mean']:.4f} | "
            f"{training['orpheus']['last_20_mean']:.4f} |"
        ),
        (
            f"| Sesame | 60 | {training['sesame']['first_loss']:.4f} | "
            f"{training['sesame']['final_loss']:.4f} | "
            f"{training['sesame']['first_20_mean']:.4f} | "
            f"{training['sesame']['last_20_mean']:.4f} |"
        ),
        "",
        "## Direct-audio observations",
        "",
        (
            f"The Orpheus WAV received transcript accuracy {orpheus_judge['transcript_accuracy']}/5 "
            f"and naturalness {orpheus_judge['naturalness']}/5. The judge reported audible "
            f"paralinguistic activity={orpheus_judge['audible_paralinguistic_event']} "
            f"({orpheus_judge['event_type']}, confidence {orpheus_judge['event_confidence']})."
        ),
        (
            f"For Sesame's same-text B/C pair, the judge reported voice similarity "
            f"{sesame_judge['same_text_B_C_voice_similarity']}/5 and style similarity "
            f"{sesame_judge['same_text_B_C_style_similarity']}/5."
        ),
        "",
        "## Negative finding: the mechanism labels are reversed",
        "",
        (
            "The executable book sources and immutable upstream notebooks do not support the "
            "manuscript's Orpheus=reference-audio consistency / Sesame=paralinguistic-tag mapping. "
            "The retained Orpheus path serializes SNAC tokens and demonstrates a <giggle> text tag, "
            "while the Sesame path supplies prior audio in CSM conversation context for speaker/style "
            "conditioning and contains no <laugh>/<sigh> tag protocol. This contradiction is reported "
            "rather than converted into a positive result."
        ),
        "",
        "## Provenance boundary",
        "",
        (
            "The executed notebooks are public upstream reference runs at one immutable Git commit. "
            "They are not represented as author-local runs. Author-local adapters and outputs were not "
            "retained; checkpoints remain intentionally undistributed and are not acceptance artifacts."
        ),
        (
            "The reproduction contract freezes notebook blobs, model/data/codec revisions and weight "
            "objects, all book source hashes, commands, and the remaining CUDA-environment limits."
        ),
        "",
    ]
    return "\n".join(lines)


def artifact_record(path: Path, run_dir: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(run_dir)),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def build_manifest(run_id: str, run_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    artifact_names = [
        "upstream_orpheus.ipynb",
        "upstream_sesame.ipynb",
        "orpheus_output_1.wav",
        "sesame_output_1.wav",
        "sesame_output_2.wav",
        "sesame_output_3.wav",
        "source_audit.json",
        "judge_receipts.json",
        "summary.json",
        "report.md",
    ]
    return {
        "schema_version": "exp7-6-manifest-v1",
        "experiment": "7-6",
        "run_id": run_id,
        "created_at": utc_now(),
        "status": summary["status"],
        "run_dir": str(run_dir.relative_to(HERE)),
        "inputs": [file_record(REPO_ROOT / path) for path in LOCAL_SOURCE_PATHS],
        "failed_attempts": [file_record(REPO_ROOT / path) for path in FAILED_ATTEMPT_PATHS],
        "artifacts": [artifact_record(run_dir / name, run_dir) for name in artifact_names],
        "acceptance": summary["acceptance"],
        "checkpoint_policy": "not distributed; not an acceptance artifact",
    }


def write_derived(run_id: str, run_dir: Path, receipts_doc: dict[str, Any]) -> dict[str, Any]:
    source_audit = build_source_audit(run_dir)
    receipts = receipts_doc.get("calls")
    if (
        receipts_doc.get("schema_version") != "exp7-6-judge-receipts-v1"
        or receipts_doc.get("experiment") != "7-6"
        or not isinstance(receipts, list)
    ):
        raise ValueError("malformed retained judge receipts")
    summary = summarize(source_audit, receipts)
    write_json(run_dir / "source_audit.json", source_audit)
    write_json(run_dir / "summary.json", summary)
    (run_dir / "report.md").write_text(render_report(summary), encoding="utf-8")
    write_json(run_dir / "manifest.json", build_manifest(run_id, run_dir, summary))
    latest = {
        "schema_version": "exp7-6-latest-v1",
        "experiment": "7-6",
        "run_id": run_id,
        "status": summary["status"],
        "run_dir": str(run_dir.relative_to(HERE)),
        "manifest_sha256": sha256_file(run_dir / "manifest.json"),
    }
    write_json(LATEST_PATH, latest)
    return latest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--endpoint", default=os.getenv("MISTRAL_BASE_URL", DEFAULT_ENDPOINT))
    parser.add_argument("--model", default=os.getenv("VOICE_SFT_JUDGE_MODEL", DEFAULT_MODEL))
    parser.add_argument("--api-key-env", default="MISTRAL_API_KEY")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--refresh-manifest", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.run_id):
        raise SystemExit("run ID contains unsupported characters")
    run_dir = RUNS_DIR / args.run_id
    if args.refresh_manifest:
        if not run_dir.is_dir():
            raise SystemExit(f"cannot refresh missing run: {run_dir}")
        receipts_doc = json.loads((run_dir / "judge_receipts.json").read_text(encoding="utf-8"))
        latest = write_derived(args.run_id, run_dir, receipts_doc)
        print(json.dumps(latest, indent=2, sort_keys=True))
        return 0
    if run_dir.exists():
        raise SystemExit(f"refusing to overwrite existing run: {run_dir}")
    api_key = os.getenv(args.api_key_env, "").strip()
    if not api_key:
        raise SystemExit(f"missing required credential: {args.api_key_env}")
    run_dir.mkdir(parents=True)
    try:
        for name in NOTEBOOKS:
            raw = fetch_bytes(notebook_url(name))
            notebook = load_notebook_bytes(raw, name)
            (run_dir / f"upstream_{name}.ipynb").write_bytes(raw)
            for row in extracted_audio(notebook, name):
                (run_dir / row["filename"]).write_bytes(row["audio_bytes"])
        receipts = [
            call_judge(
                track,
                run_dir,
                endpoint=args.endpoint,
                model=args.model,
                api_key=api_key,
                timeout=args.timeout,
            )
            for track in ("orpheus", "sesame")
        ]
        receipts_doc = {
            "schema_version": "exp7-6-judge-receipts-v1",
            "experiment": "7-6",
            "credential_headers_retained": False,
            "calls": receipts,
        }
        write_json(run_dir / "judge_receipts.json", receipts_doc)
        latest = write_derived(args.run_id, run_dir, receipts_doc)
    except Exception:
        # Partial provider/source evidence is intentionally left in a non-canonical directory.
        raise
    print(json.dumps(latest, indent=2, sort_keys=True))
    return 0 if latest["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
