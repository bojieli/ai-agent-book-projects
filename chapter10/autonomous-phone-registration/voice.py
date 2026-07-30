"""Live microphone/ASR/TTS channel and a deterministic test channel."""

from __future__ import annotations

import asyncio
import os
import subprocess
import tempfile
import time
import wave
from pathlib import Path
from typing import Dict, List, Protocol


class PhoneChannel(Protocol):
    async def say(self, text: str) -> None: ...
    async def listen(self, *, timeout: float = 30.0) -> str: ...


class LiveMicrophoneChannel:
    """A real cascaded phone-audio loop: OpenAI TTS -> speaker -> mic -> OpenAI ASR.

    Local microphone/speaker are the call transport. The provider boundary is kept
    behind this class so a PSTN/WebRTC transport can implement the same two methods.
    """

    def __init__(self, *, language: str = "zh", voice: str = "coral"):
        from openai import OpenAI

        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("实时语音需要 OPENAI_API_KEY（OpenRouter 不提供 ASR/TTS）")
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=60, max_retries=1)
        self.language = language
        self.voice = voice
        self.sample_rate = int(os.getenv("VOICE_SAMPLE_RATE", "16000"))
        self.silence_seconds = float(os.getenv("VOICE_SILENCE_SECONDS", "0.9"))
        self.threshold = float(os.getenv("VOICE_RMS_THRESHOLD", "0.012"))
        self.latencies: List[Dict[str, float]] = []

    async def say(self, text: str) -> None:
        started = time.monotonic()
        path = Path(tempfile.mkstemp(suffix=".mp3")[1])

        def synthesize():
            result = self.client.audio.speech.create(
                model=os.getenv("OPENAI_TTS_MODEL", "tts-1"),
                voice=self.voice,
                input=text,
            )
            result.stream_to_file(path)

        try:
            await asyncio.to_thread(synthesize)
            synth_done = time.monotonic()
            player = os.getenv("AUDIO_PLAYER", "afplay")
            proc = await asyncio.create_subprocess_exec(
                player, str(path), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            await proc.wait()
            self.latencies.append({
                "tts_seconds": round(synth_done - started, 3),
                "playback_seconds": round(time.monotonic() - synth_done, 3),
            })
        finally:
            path.unlink(missing_ok=True)

    async def listen(self, *, timeout: float = 30.0) -> str:
        path = Path(tempfile.mkstemp(suffix=".wav")[1])
        started = time.monotonic()
        try:
            await asyncio.to_thread(self._record_vad, path, timeout)
            record_done = time.monotonic()

            def transcribe() -> str:
                with path.open("rb") as audio:
                    response = self.client.audio.transcriptions.create(
                        model=os.getenv("OPENAI_ASR_MODEL", "whisper-1"),
                        file=audio,
                        language=self.language,
                    )
                return response.text.strip()

            text = await asyncio.to_thread(transcribe)
            self.latencies.append({
                "capture_seconds": round(record_done - started, 3),
                "asr_seconds": round(time.monotonic() - record_done, 3),
            })
            print(f"  [ASR] 用户：{text}")
            return text
        finally:
            path.unlink(missing_ok=True)

    def _record_vad(self, path: Path, timeout: float) -> None:
        import numpy as np
        import sounddevice as sd

        block = 1024
        frames = []
        heard_speech = False
        silent_blocks = 0
        required_silence = max(1, int(self.silence_seconds * self.sample_rate / block))
        deadline = time.monotonic() + timeout
        print("  [麦克风] 请开始回答；检测到句末静音后自动提交……")
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32", blocksize=block) as stream:
            while time.monotonic() < deadline:
                data, overflowed = stream.read(block)
                if overflowed:
                    print("  [麦克风] 输入发生 overflow，继续采集")
                mono = data[:, 0].copy()
                frames.append(mono)
                rms = float(np.sqrt(np.mean(np.square(mono))))
                if rms >= self.threshold:
                    heard_speech = True
                    silent_blocks = 0
                elif heard_speech:
                    silent_blocks += 1
                    if silent_blocks >= required_silence:
                        break
        if not heard_speech:
            raise TimeoutError("未在规定时间内检测到语音")
        pcm = (np.concatenate(frames).clip(-1, 1) * 32767).astype("<i2")
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(pcm.tobytes())


class ScriptedPhoneChannel:
    """Non-audio supplement for tests and orchestration debugging only."""

    def __init__(self, answers: List[str]):
        self.answers = asyncio.Queue()
        for answer in answers:
            self.answers.put_nowait(answer)
        self.prompts: List[str] = []

    async def say(self, text: str) -> None:
        self.prompts.append(text)
        print(f"  [scripted-phone] {text}")
        await asyncio.sleep(0)

    async def listen(self, *, timeout: float = 30.0) -> str:
        return await asyncio.wait_for(self.answers.get(), timeout)
