"""Real speech synthesis and microphone-audio ASR for Experiment 9-2."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pcm16_wav(pcm: bytes, sample_rate: int) -> bytes:
    with tempfile.SpooledTemporaryFile() as handle:
        with wave.open(handle, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm)
        handle.seek(0)
        return handle.read()


def read_pcm16_wav(value: bytes) -> tuple[bytes, int]:
    with tempfile.SpooledTemporaryFile() as handle:
        handle.write(value)
        handle.seek(0)
        with wave.open(handle, "rb") as wav:
            if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getcomptype() != "NONE":
                raise RuntimeError("speech synthesizer output must be mono PCM16 WAV")
            return wav.readframes(wav.getnframes()), wav.getframerate()


def _command_receipt(path: str) -> dict[str, Any]:
    resolved = Path(path).resolve()
    return {
        "name": resolved.name,
        "sha256": sha256_file(resolved),
    }


@dataclass(frozen=True)
class SynthesizedSpeech:
    pcm: bytes
    wav: bytes
    receipt: dict[str, Any]


class SystemSpeechSynthesizer:
    """Synthesize actual speech with an explicitly selected local speech engine."""

    def __init__(self) -> None:
        requested = os.getenv("PHONE_TTS_ENGINE", "auto").casefold()
        say = shutil.which("say")
        espeak = shutil.which("espeak-ng") or shutil.which("espeak")
        if requested == "say" and not say:
            raise RuntimeError("PHONE_TTS_ENGINE=say but the say executable is unavailable")
        if requested == "espeak" and not espeak:
            raise RuntimeError("PHONE_TTS_ENGINE=espeak but espeak is unavailable")
        if requested not in {"auto", "say", "espeak"}:
            raise RuntimeError("PHONE_TTS_ENGINE must be auto, say, or espeak")
        self.engine = say if requested in {"auto", "say"} and say else espeak
        self.ffmpeg = shutil.which("ffmpeg")
        if not self.engine or not self.ffmpeg:
            raise RuntimeError("real local TTS requires say/espeak and ffmpeg")
        self.kind = "say" if Path(self.engine).name == "say" else "espeak"
        self.voice = os.getenv("PHONE_TTS_VOICE", "Samantha" if self.kind == "say" else "en-us")

    def synthesize(self, text: str, *, sample_rate: int = 8_000) -> SynthesizedSpeech:
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("TTS text must not be empty")
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="exp9-2-tts-") as directory:
            directory_path = Path(directory)
            source = directory_path / ("speech.aiff" if self.kind == "say" else "speech.wav")
            target = directory_path / "speech.wav"
            if self.kind == "say":
                command = [self.engine, "-v", self.voice, "-o", str(source), cleaned]
            else:
                command = [self.engine, "-v", self.voice, "-w", str(source), cleaned]
            subprocess.run(command, check=True, capture_output=True, timeout=90)
            subprocess.run(
                [
                    self.ffmpeg,
                    "-nostdin",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(source),
                    "-ac",
                    "1",
                    "-ar",
                    str(sample_rate),
                    "-acodec",
                    "pcm_s16le",
                    str(target),
                ],
                check=True,
                capture_output=True,
                timeout=90,
            )
            wav = target.read_bytes()
        pcm, actual_rate = read_pcm16_wav(wav)
        if actual_rate != sample_rate or not pcm:
            raise RuntimeError("TTS produced empty audio or the wrong sample rate")
        receipt = {
            "schema_version": 1,
            "operation": "tts",
            "execution": "real_speech_synthesis",
            "provider": "macOS say" if self.kind == "say" else "eSpeak",
            "model": "operating-system speech synthesizer",
            "voice": self.voice,
            "sample_rate_hz": sample_rate,
            "channels": 1,
            "sample_width_bytes": 2,
            "sample_count": len(pcm) // 2,
            "duration_seconds": round(len(pcm) / 2 / sample_rate, 6),
            "wav_bytes": len(wav),
            "wav_sha256": sha256_bytes(wav),
            "pcm_sha256": sha256_bytes(pcm),
            "latency_seconds": round(time.monotonic() - started, 6),
            "engine": _command_receipt(self.engine),
            "decoder": _command_receipt(self.ffmpeg),
            "network_used": False,
            "mock": False,
            "probe_only": False,
            "fallback_used": False,
        }
        return SynthesizedSpeech(pcm=pcm, wav=wav, receipt=receipt)


class WhisperASR:
    """Run a real cached OpenAI Whisper checkpoint over exact RTP-derived PCM."""

    def __init__(self) -> None:
        requested = os.getenv("WHISPER_PYTHON")
        candidates = [requested] if requested else [sys.executable, shutil.which("python3")]
        self.python = next(
            (candidate for candidate in candidates if candidate and self._available(candidate)),
            None,
        )
        if not self.python:
            raise RuntimeError(
                "local ASR requires torch and openai-whisper; set WHISPER_PYTHON to that Python executable"
            )
        self.model = os.getenv("WHISPER_MODEL", "tiny")

    @staticmethod
    def _available(python: str) -> bool:
        try:
            return (
                subprocess.run(
                    [python, "-c", "import torch, whisper"],
                    capture_output=True,
                    timeout=20,
                    check=False,
                ).returncode
                == 0
            )
        except (OSError, subprocess.SubprocessError):
            return False

    def transcribe(
        self, pcm: bytes, *, retained_wav_path: Path | None = None
    ) -> tuple[str, dict[str, Any]]:
        if len(pcm) < 16_000:
            raise RuntimeError("microphone RTP buffer is too short for ASR")
        wav = pcm16_wav(pcm, 16_000)
        if retained_wav_path is not None:
            retained_wav_path.parent.mkdir(parents=True, exist_ok=True)
            retained_wav_path.write_bytes(wav)
            source_path = retained_wav_path
        else:
            with tempfile.NamedTemporaryFile(
                prefix="exp9-2-asr-", suffix=".wav", delete=False
            ) as temporary:
                temporary.write(wav)
                source_path = Path(temporary.name)
        script = """import hashlib, json, pathlib, sys, time
import torch, whisper
model_name, audio = sys.argv[1:3]
checkpoint = pathlib.Path.home()/'.cache'/'whisper'/(model_name+'.pt')
started=time.perf_counter(); model=whisper.load_model(model_name); loaded=time.perf_counter()
result=model.transcribe(audio, language='en', fp16=False, temperature=0, verbose=False, condition_on_previous_text=False)
finished=time.perf_counter()
payload={'text':str(result.get('text') or '').strip(),'language':result.get('language'),
'checkpoint_name':checkpoint.name,'checkpoint_sha256':hashlib.sha256(checkpoint.read_bytes()).hexdigest() if checkpoint.exists() else None,
'python':sys.version.split()[0],'torch':torch.__version__,'whisper':getattr(whisper,'__version__','unknown'),
'model_load_seconds':loaded-started,'inference_seconds':finished-loaded}
print('EXPERIMENT_JSON='+json.dumps(payload,ensure_ascii=False))
"""
        started = time.monotonic()
        try:
            process = subprocess.run(
                [self.python, "-c", script, self.model, str(source_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=240,
            )
        finally:
            if retained_wav_path is None:
                source_path.unlink(missing_ok=True)
        marker = next(
            (line for line in process.stdout.splitlines() if line.startswith("EXPERIMENT_JSON=")),
            None,
        )
        if not marker:
            raise RuntimeError("Whisper returned no structured result")
        result = json.loads(marker.split("=", 1)[1])
        transcript = str(result.get("text") or "").strip()
        checkpoint_sha = str(result.get("checkpoint_sha256") or "")
        if not transcript or len(checkpoint_sha) != 64:
            raise RuntimeError("Whisper returned an empty transcript or missing checkpoint hash")
        receipt = {
            "schema_version": 1,
            "operation": "asr",
            "execution": "real_local_inference",
            "provider": "local OpenAI Whisper",
            "model": f"whisper-{self.model}",
            "checkpoint_name": result["checkpoint_name"],
            "checkpoint_sha256": checkpoint_sha,
            "runtime": {
                "python": result["python"],
                "torch": result["torch"],
                "openai_whisper": result["whisper"],
            },
            "input_source": "browser_microphone_rtp",
            "input_sample_rate_hz": 16_000,
            "input_channels": 1,
            "input_pcm_bytes": len(pcm),
            "input_wav_bytes": len(wav),
            "input_wav_sha256": sha256_bytes(wav),
            "input_duration_seconds": round(len(pcm) / 2 / 16_000, 6),
            "language": result.get("language") or "unknown",
            "transcript": transcript,
            "transcript_sha256": hashlib.sha256(transcript.encode("utf-8")).hexdigest(),
            "model_load_seconds": round(float(result["model_load_seconds"]), 6),
            "inference_seconds": round(float(result["inference_seconds"]), 6),
            "latency_seconds": round(time.monotonic() - started, 6),
            "retained_safe_fixture_path": (
                str(retained_wav_path.name) if retained_wav_path is not None else None
            ),
            "external_request": False,
            "mock": False,
            "probe_only": False,
            "fallback_used": False,
        }
        return transcript, receipt


def make_synthetic_speech_fixture(
    text: str,
    output_path: Path,
    *,
    leading_silence_seconds: float = 4.0,
    trailing_silence_seconds: float = 3.0,
) -> dict[str, Any]:
    """Generate a non-private browser microphone WAV for automated acceptance."""
    synthesizer = SystemSpeechSynthesizer()
    speech = synthesizer.synthesize(text, sample_rate=16_000)
    leading = b"\x00\x00" * int(16_000 * leading_silence_seconds)
    trailing = b"\x00\x00" * int(16_000 * trailing_silence_seconds)
    wav = pcm16_wav(leading + speech.pcm + trailing, 16_000)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(wav)
    return {
        "kind": "safe_synthetic_browser_microphone_fixture",
        "contains_private_data": False,
        "sample_rate_hz": 16_000,
        "duration_seconds": round((len(leading) + len(speech.pcm) + len(trailing)) / 2 / 16_000, 6),
        "wav_bytes": len(wav),
        "wav_sha256": sha256_bytes(wav),
        "leading_silence_seconds": leading_silence_seconds,
        "trailing_silence_seconds": trailing_silence_seconds,
        "synthesis": speech.receipt,
    }


__all__ = [
    "SystemSpeechSynthesizer",
    "WhisperASR",
    "make_synthetic_speech_fixture",
    "pcm16_wav",
    "sha256_bytes",
    "sha256_file",
]
