"""Qwen2-Audio growing-prefix inference for Experiment 9-3."""

from __future__ import annotations

import json
import ast
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

import librosa


EVENT_ALIASES = {
    "noise": "<|noise|>",
    "background noise": "<|noise|>",
    "laughter": "<|laughter|>",
    "laugh": "<|laughter|>",
    "silence": "<|silence|>",
    "pause": "<|silence|>",
    "cough": "<|cough|>",
}


@dataclass
class PrefixResult:
    prefix_seconds: float
    inference_seconds: float
    transcript: str
    acoustic_events: list[str]
    raw_response: str


def parse_response(raw: str) -> tuple[str, list[str]]:
    """Parse the model's requested JSON while retaining raw output for audit."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip()).strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        payload = None
        if match:
            try:
                payload = json.loads(match.group(0))
            except json.JSONDecodeError:
                try:
                    payload = ast.literal_eval(match.group(0))
                except (ValueError, SyntaxError):
                    pass
        if not isinstance(payload, dict):
            payload = {"transcript": cleaned, "acoustic_events": []}
    transcript = str(payload.get("transcript") or "")
    events: list[str] = []
    raw_events = payload.get("acoustic_events")
    if isinstance(raw_events, str):
        event_list = [raw_events]
    elif isinstance(raw_events, (list, tuple, set)):
        event_list = list(raw_events)
    else:
        event_list = []
    for event in event_list:
        if event is None:
            continue
        text = str(event).strip()
        if not text:
            continue
        normalized = EVENT_ALIASES.get(text.lower(), text)
        if normalized and normalized not in events:
            events.append(normalized)
    # Qwen may place an event token next to the transcription rather than in JSON.
    for token in re.findall(r"<\|[^|]+\|>", raw):
        if token not in events:
            events.append(token)
    return transcript, events


class Qwen2AudioRecognizer:
    """Actual ``Qwen/Qwen2-Audio-7B-Instruct`` inference backend."""

    def __init__(
        self,
        model_id: str = "Qwen/Qwen2-Audio-7B-Instruct",
        device: str = "auto",
        max_new_tokens: int = 128,
    ) -> None:
        self._mlx = device == "mlx" or model_id.startswith("mlx-community/")
        if self._mlx:
            from mlx_audio.stt.utils import load_model

            self.device = "mlx"
            self.model_id = model_id
            self.max_new_tokens = max_new_tokens
            self.model = load_model(model_id)
            self.processor = None
            return
        import torch
        from transformers import AutoProcessor, Qwen2AudioForConditionalGeneration

        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        self.device = device
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        dtype = torch.float16 if device in ("cuda", "mps") else torch.float32
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = Qwen2AudioForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=dtype,
            low_cpu_mem_usage=True,
        ).to(device)
        self.model.eval()

    def transcribe_array(self, audio: Any, sample_rate: int) -> tuple[str, list[str], str]:
        instruction = (
            "Transcribe all speech heard so far. Also detect non-verbal acoustic events. "
            "Return JSON only with keys transcript (string) and acoustic_events (array). "
            "The acoustic_events array must contain only events actually audible in this clip; "
            "return an empty array when none are audible. Valid event names are noise, laughter, silence, cough. "
            "Never copy the list of valid names into the answer. "
            "Do not treat a pause or background noise as the end of the utterance."
        )
        if self._mlx:
            if sample_rate != 16000:
                audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=16000)
            result = self.model.generate(
                audio,
                prompt=instruction,
                max_tokens=self.max_new_tokens,
                temperature=0.0,
            )
            raw = result.text.strip()
            transcript, events = parse_response(raw)
            return transcript, events, raw

        import torch
        conversation = [{"role": "user", "content": [
            {"type": "audio", "audio_url": "prefix.wav"},
            {"type": "text", "text": instruction},
        ]}]
        text = self.processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
        target_sr = self.processor.feature_extractor.sampling_rate
        if sample_rate != target_sr:
            audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=target_sr)
        inputs = self.processor(text=text, audios=[audio], return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) if hasattr(v, "to") else v for k, v in inputs.items()}
        with torch.inference_mode():
            generated = self.model.generate(**inputs, max_new_tokens=self.max_new_tokens, do_sample=False)
        generated = generated[:, inputs["input_ids"].shape[1]:]
        raw = self.processor.batch_decode(
            generated, skip_special_tokens=False, clean_up_tokenization_spaces=False
        )[0].strip()
        transcript, events = parse_response(raw)
        return transcript, events, raw


def growing_prefix(
    recognizer: Qwen2AudioRecognizer,
    audio_path: str | Path,
    chunk_seconds: float,
    *,
    on_result: Callable[[PrefixResult], None] | None = None,
) -> list[PrefixResult]:
    """Re-encode [0:t] for every chunk; this is intentionally not incremental."""
    audio, sr = librosa.load(str(audio_path), sr=None, mono=True)
    duration = len(audio) / sr
    endpoints = []
    endpoint = chunk_seconds
    while endpoint < duration:
        endpoints.append(endpoint)
        endpoint += chunk_seconds
    endpoints.append(duration)
    results = []
    for endpoint in endpoints:
        prefix = audio[: max(1, round(endpoint * sr))]
        started = time.perf_counter()
        transcript, events, raw = recognizer.transcribe_array(prefix, sr)
        result = PrefixResult(endpoint, time.perf_counter() - started, transcript, events, raw)
        results.append(result)
        if on_result:
            on_result(result)
    return results


def serialize(results: list[PrefixResult]) -> list[dict[str, Any]]:
    return [asdict(result) for result in results]
