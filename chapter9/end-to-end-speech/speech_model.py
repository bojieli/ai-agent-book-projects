"""Native local MiniCPM-o 4.5 inference for Experiment 9-4."""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


MODEL_ID = "openbmb/MiniCPM-o-4_5"
MODEL_REVISION = "1f761131fa83f5ed3cd6f2f22b225c4501d154fa"


@dataclass
class InferenceResult:
    mode: str
    response: str
    latency_seconds: float
    transcript: str | None = None
    stage_latencies: dict[str, float] | None = None
    output_audio: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audio_metadata(path: str | Path) -> dict[str, Any]:
    import soundfile as sf

    path = Path(path)
    info = sf.info(path)
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "sample_rate_hz": info.samplerate,
        "frames": info.frames,
        "duration_seconds": round(info.duration, 6),
        "channels": info.channels,
        "format": info.format,
    }


class MiniCPMOClient:
    """One-GPU Transformers client for the official MiniCPM-o 4.5 checkpoint."""

    def __init__(
        self,
        model_id: str = MODEL_ID,
        revision: str = MODEL_REVISION,
        *,
        device: str = "cuda",
        enable_tts: bool = True,
        local_files_only: bool = False,
    ) -> None:
        self.model_id = model_id
        self.revision = revision
        self.device = device
        self.enable_tts = enable_tts
        self.local_files_only = local_files_only
        self.model = None
        self.load_seconds: float | None = None

    def load(self) -> None:
        import torch
        from transformers import AutoModel

        if self.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("MiniCPM-o 4.5 local precision run requires an NVIDIA CUDA GPU")
        started = time.perf_counter()
        self.model = AutoModel.from_pretrained(
            self.model_id,
            revision=self.revision,
            trust_remote_code=True,
            attn_implementation="sdpa",
            torch_dtype=torch.bfloat16,
            init_vision=False,
            init_audio=True,
            init_tts=self.enable_tts,
            local_files_only=self.local_files_only,
        )
        self.model.eval().to(self.device)
        if self.enable_tts:
            self.model.init_tts()
        self.load_seconds = time.perf_counter() - started

    def _require_model(self):
        if self.model is None:
            raise RuntimeError("Call load() before inference")
        return self.model

    @staticmethod
    def load_audio(path: str | Path):
        import librosa

        audio, _ = librosa.load(path, sr=16000, mono=True)
        return audio

    def infer_audio(
        self,
        audio_path: str | Path,
        instruction: str,
        *,
        max_new_tokens: int = 256,
        output_audio_path: str | Path | None = None,
    ) -> InferenceResult:
        model = self._require_model()
        audio = self.load_audio(audio_path)
        generate_audio = output_audio_path is not None
        if generate_audio and not self.enable_tts:
            raise RuntimeError("The client was loaded with enable_tts=False")
        if output_audio_path is not None:
            output_audio_path = Path(output_audio_path)
            output_audio_path.parent.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        response = model.chat(
            msgs=[{"role": "user", "content": [instruction, audio]}],
            do_sample=False,
            max_new_tokens=max_new_tokens,
            use_tts_template=generate_audio,
            enable_thinking=False,
            generate_audio=generate_audio,
            output_audio_path=str(output_audio_path) if output_audio_path else None,
        )
        latency = time.perf_counter() - started
        return InferenceResult(
            mode="direct-audio-to-speech" if generate_audio else "direct-audio-to-text",
            response=response,
            latency_seconds=latency,
            output_audio=audio_metadata(output_audio_path) if output_audio_path else None,
        )

    def infer_text(
        self, prompt: str, *, max_new_tokens: int = 256
    ) -> InferenceResult:
        model = self._require_model()
        started = time.perf_counter()
        response = model.chat(
            msgs=[{"role": "user", "content": [prompt]}],
            do_sample=False,
            max_new_tokens=max_new_tokens,
            use_tts_template=False,
            enable_thinking=False,
            generate_audio=False,
        )
        return InferenceResult(
            mode="text-only",
            response=response,
            latency_seconds=time.perf_counter() - started,
        )

    def transcribe(self, audio_path: str | Path) -> InferenceResult:
        return self.infer_audio(
            audio_path,
            "Please transcribe only the words spoken in this audio. Do not describe tone, pace, or background sound.",
            max_new_tokens=256,
        )

    def self_cascade(
        self, audio_path: str | Path, instruction: str, *, max_new_tokens: int = 256
    ) -> InferenceResult:
        transcription = self.transcribe(audio_path)
        reasoning = self.infer_text(
            f"{instruction}\n\nUse only this transcript as evidence:\n{transcription.response}",
            max_new_tokens=max_new_tokens,
        )
        return InferenceResult(
            mode="self-cascade-audio-to-transcript-to-text",
            response=reasoning.response,
            latency_seconds=transcription.latency_seconds + reasoning.latency_seconds,
            transcript=transcription.response,
            stage_latencies={
                "transcription_seconds": transcription.latency_seconds,
                "reasoning_seconds": reasoning.latency_seconds,
            },
        )

    def runtime_metadata(self) -> dict[str, Any]:
        import torch
        import transformers

        gpu = None
        if torch.cuda.is_available():
            properties = torch.cuda.get_device_properties(0)
            gpu = {
                "name": properties.name,
                "total_memory_gib": round(properties.total_memory / 2**30, 3),
                "peak_allocated_gib": round(torch.cuda.max_memory_allocated() / 2**30, 3),
            }
        return {
            "model_id": self.model_id,
            "model_revision": self.revision,
            "device": self.device,
            "torch_version": torch.__version__,
            "transformers_version": transformers.__version__,
            "cuda_version": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
            "gpu": gpu,
            "load_seconds": self.load_seconds,
            "precision": "bfloat16",
            "attention": "sdpa",
            "init_vision": False,
            "init_audio": True,
            "init_tts": self.enable_tts,
        }
