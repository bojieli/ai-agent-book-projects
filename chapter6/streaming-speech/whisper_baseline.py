"""VAD + Whisper comparison baseline for Experiment 9-3."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    import librosa
    import soundfile as sf
except ImportError:
    librosa = None
    sf = None
import numpy as np


@dataclass
class BaselineResult:
    configured_silence_ms: int
    first_speech_start_seconds: float
    first_endpoint_audio_seconds: float
    first_decision_audio_seconds: float
    post_speech_vad_delay_seconds: float
    first_segment_asr_seconds: float
    all_segments_asr_seconds: float
    post_endpoint_response_seconds: float
    first_response_from_audio_start_seconds: float
    transcript: str
    segment_transcripts: list[str]
    segment_asr_seconds: list[float]
    segment_count: int
    endpoints: list[float]
    decisions: list[float]


@dataclass
class VadEvent:
    speech_start: int
    speech_endpoint: int
    decision: int


def energy_vad_events(audio: np.ndarray, sr: int, silence_ms: int = 600) -> list[VadEvent]:
    """Return start, acoustic endpoint, and later VAD decision sample.

    The decision occurs only after the full low-energy run. Keeping it separate
    from the acoustic endpoint prevents a 4-second utterance position from being
    mislabeled as a 600 ms VAD latency.
    """
    if len(audio) == 0:
        return []
    frame = max(1, int(sr * 0.02))
    energies = np.array([np.sqrt(np.mean(audio[i:i + frame] ** 2) + 1e-12) for i in range(0, len(audio), frame)])
    # A conservative fixed-relative threshold keeps a long silent gap distinct
    # even when speech occupies most of the clip (where p30 itself is speech).
    threshold = max(0.004, min(0.03, float(np.percentile(energies, 90) * 0.15)))
    silent_needed = max(1, silence_ms // 20)
    # A streaming endpoint detector observes silence after the physical file
    # ends too, so append an analysis-only silent tail. It is never transcribed.
    analysis_energies = np.concatenate([energies, np.zeros(silent_needed)])
    events, silent, speech_start = [], 0, None
    active = False
    for index, energy in enumerate(analysis_energies):
        if energy >= threshold:
            if not active:
                speech_start = index * frame
            active, silent = True, 0
        elif active:
            silent += 1
            if silent >= silent_needed:
                endpoint = min(len(audio), (index + 1 - silent_needed) * frame)
                decision = min(len(audio) + silent_needed * frame, (index + 1) * frame)
                events.append(VadEvent(int(speech_start or 0), endpoint, decision))
                active, silent, speech_start = False, 0, None
    return events


def energy_vad_endpoints(audio: np.ndarray, sr: int, silence_ms: int = 600) -> list[int]:
    """Compatibility helper returning only acoustic endpoint locations."""
    return [event.speech_endpoint for event in energy_vad_events(audio, sr, silence_ms)]


class LocalWhisper:
    """Actual open-source Whisper inference, loaded once for all VAD segments."""

    def __init__(self, model: str = "small") -> None:
        import whisper

        self.model_name = model
        self.model = whisper.load_model(model)

    def transcribe(self, path: Path) -> str:
        return str(self.model.transcribe(str(path), language="zh", fp16=False)["text"]).strip()


def run_whisper_baseline(audio_path: str | Path, transcriber) -> BaselineResult:
    audio, sr = librosa.load(str(audio_path), sr=None, mono=True)
    silence_ms = 600
    events = energy_vad_events(audio, sr, silence_ms)
    if not events:
        raise RuntimeError("VAD found no speech event")
    texts, asr_times, previous = [], [], 0
    temp_dir = Path(audio_path).parent / ".baseline_chunks"
    temp_dir.mkdir(exist_ok=True)
    try:
        for index, event in enumerate(events):
            chunk = temp_dir / f"chunk_{index}.wav"
            sf.write(chunk, audio[previous:event.speech_endpoint], sr)
            t0 = time.perf_counter()
            text = transcriber.transcribe(chunk)
            asr_times.append(time.perf_counter() - t0)
            texts.append(text)
            previous = event.speech_endpoint
    finally:
        for item in temp_dir.glob("*.wav"):
            item.unlink()
        temp_dir.rmdir()
    first = events[0]
    vad_delay = (first.decision - first.speech_endpoint) / sr
    return BaselineResult(
        configured_silence_ms=silence_ms,
        first_speech_start_seconds=first.speech_start / sr,
        first_endpoint_audio_seconds=first.speech_endpoint / sr,
        first_decision_audio_seconds=first.decision / sr,
        post_speech_vad_delay_seconds=vad_delay,
        first_segment_asr_seconds=asr_times[0],
        all_segments_asr_seconds=sum(asr_times),
        post_endpoint_response_seconds=vad_delay + asr_times[0],
        first_response_from_audio_start_seconds=first.decision / sr + asr_times[0],
        transcript=" ".join(t for t in texts if t),
        segment_transcripts=texts,
        segment_asr_seconds=asr_times,
        segment_count=len(events),
        endpoints=[round(event.speech_endpoint / sr, 3) for event in events],
        decisions=[round(event.decision / sr, 3) for event in events],
    )


def serialize(result: BaselineResult):
    return asdict(result)
