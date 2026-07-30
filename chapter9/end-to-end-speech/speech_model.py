"""Exact Step-Audio R1 vLLM client and ASR→LLM cascade baseline."""

from __future__ import annotations

import base64
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import requests


@dataclass
class InferenceResult:
    backend: str
    model: str
    response: str
    latency_seconds: float
    first_token_seconds: float | None
    audio_token_count: int = 0
    transcript: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _audio_content(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    raw = path.read_bytes()
    # The official Step-Audio-R1 helper converts every source to WAV first. The
    # companion requires WAV to keep the wire contract unambiguous.
    if path.suffix.lower() != ".wav":
        raise ValueError("Step-Audio R1 input must be WAV; convert with ffmpeg first")
    return {
        "type": "input_audio",
        "input_audio": {"data": base64.b64encode(raw).decode("ascii"), "format": "wav"},
    }


class StepAudioR1Client:
    """Client for the upstream customized-vLLM OpenAI-compatible endpoint."""

    def __init__(self, endpoint: str, model: str = "Step-Audio-R1", timeout: float = 1800) -> None:
        base = endpoint.rstrip("/")
        if base.endswith("/v1/chat/completions"):
            self.endpoint = base
        elif base.endswith("/v1"):
            self.endpoint = base + "/chat/completions"
        else:
            self.endpoint = base + "/v1/chat/completions"
        self.model = model
        self.timeout = timeout

    def healthcheck(self) -> dict[str, Any]:
        models_url = self.endpoint.rsplit("/chat/completions", 1)[0] + "/models"
        response = requests.get(models_url, timeout=30)
        response.raise_for_status()
        return response.json()

    def infer(
        self,
        audio_path: str | Path,
        instruction: str,
        *,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        repetition_penalty: float = 1.0,
    ) -> InferenceResult:
        # This is the exact message shape used by upstream stepaudior1vllm.py.
        messages = [
            {"role": "human", "content": [
                {"type": "text", "text": instruction},
                _audio_content(audio_path),
            ]},
            {"role": "assistant", "content": "<think>\n"},
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "skip_special_tokens": False,
            "continue_final_message": True,
            "add_generation_prompt": False,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "repetition_penalty": repetition_penalty,
            "stop_token_ids": [151665],
        }
        started, first_token, text_parts, audio_tokens = time.perf_counter(), None, [], 0
        with requests.post(
            self.endpoint,
            headers={"Content-Type": "application/json"},
            json=payload,
            stream=True,
            timeout=self.timeout,
        ) as response:
            response.raise_for_status()
            for raw_line in response.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                if line == "[DONE]":
                    break
                data = json.loads(line)
                delta = data["choices"][0].get("delta", {})
                tts = delta.get("tts_content") or {}
                piece = tts.get("tts_text") or delta.get("content") or ""
                if piece:
                    if first_token is None:
                        first_token = time.perf_counter() - started
                    text_parts.append(piece)
                token_string = tts.get("tts_audio") or ""
                audio_tokens += token_string.count("<audio_")
        return InferenceResult(
            backend="step-audio-r1",
            model=self.model,
            response="".join(text_parts),
            latency_seconds=time.perf_counter() - started,
            first_token_seconds=first_token,
            audio_token_count=audio_tokens,
        )


class CascadeClient:
    """ASR→text LLM control receiving the same WAV but losing acoustics at ASR."""

    def __init__(self, client, asr_model="whisper-1", llm_model="gpt-4o-mini") -> None:
        self.client = client
        self.asr_model = asr_model
        self.llm_model = llm_model

    def infer(self, audio_path: str | Path, instruction: str) -> InferenceResult:
        started = time.perf_counter()
        with Path(audio_path).open("rb") as handle:
            transcript = self.client.audio.transcriptions.create(
                model=self.asr_model, file=handle
            ).text.strip()
        response = self.client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": "Answer the task using only the supplied transcript."},
                {"role": "user", "content": f"{instruction}\nTranscript: {transcript}"},
            ],
        )
        text = response.choices[0].message.content or ""
        return InferenceResult(
            backend="whisper-llm-cascade",
            model=f"{self.asr_model} -> {self.llm_model}",
            response=text,
            latency_seconds=time.perf_counter() - started,
            first_token_seconds=None,
            transcript=transcript,
        )
