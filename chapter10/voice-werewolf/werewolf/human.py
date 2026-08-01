# -*- coding: utf-8 -*-
"""Real human player and low-latency microphone/ASR/TTS voice session."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
import wave
from pathlib import Path
from typing import List, Optional

from .agent import PlayerAgent
from .roles import Role


class LiveVoiceSession:
    """Cascaded real-time voice transport with VAD and optional barge-in.

    AI speech is synthesized with the configured OpenAI TTS endpoint and played
    immediately. Human speech is captured from the microphone until end-of-speech
    silence and sent to the configured ASR endpoint. During public AI speech the
    microphone can terminate playback and turn the interruption into a public utterance.
    Headphones are recommended so speaker echo is not mistaken for barge-in.
    """

    def __init__(self, out_dir: str, *, allow_interruptions: bool = True):
        from openai import OpenAI

        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("真人实时语音需要可用的 OPENAI_API_KEY（ASR/TTS 不走 OpenRouter）")
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=60, max_retries=1)
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.allow_interruptions = allow_interruptions
        self.sample_rate = int(os.getenv("VOICE_SAMPLE_RATE", "16000"))
        self.threshold = float(os.getenv("VOICE_RMS_THRESHOLD", "0.025"))
        self.silence_seconds = float(os.getenv("VOICE_SILENCE_SECONDS", "0.8"))
        self.max_utterance = float(os.getenv("VOICE_MAX_UTTERANCE_SECONDS", "25"))
        self.player = os.getenv("AUDIO_PLAYER", "afplay")
        self.events = []
        self._sequence = 0

    def _event(self, type_: str, **data):
        self._sequence += 1
        self.events.append({
            "sequence": self._sequence,
            "monotonic": time.monotonic(),
            "wall_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "type": type_,
            **data,
        })
        (self.out_dir / "voice_trace.json").write_text(
            json.dumps(self.events, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _tts(self, speaker: str, text: str, round_no: int) -> Path:
        self._sequence += 1
        path = self.out_dir / f"r{round_no}_{speaker}_{self._sequence}.mp3"
        started = time.monotonic()
        response = self.client.audio.speech.create(
            model=os.getenv("OPENAI_TTS_MODEL", "tts-1"),
            voice=os.getenv("OPENAI_TTS_VOICE", "coral"),
            input=text,
        )
        response.stream_to_file(path)
        self._event("tts_ready", speaker=speaker, latency_seconds=round(time.monotonic() - started, 3), file=str(path))
        return path

    def _transcribe(self, wav_path: Path, *, kind: str) -> str:
        started = time.monotonic()
        with wav_path.open("rb") as audio:
            response = self.client.audio.transcriptions.create(
                model=os.getenv("OPENAI_ASR_MODEL", "whisper-1"),
                file=audio,
                language=os.getenv("VOICE_LANGUAGE", "zh"),
            )
        text = response.text.strip()
        self._event(kind, latency_seconds=round(time.monotonic() - started, 3), transcript=text)
        return text

    def _write_wav(self, frames, path: Path):
        import numpy as np
        pcm = (np.concatenate(frames).clip(-1, 1) * 32767).astype("<i2")
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(pcm.tobytes())

    def listen(self, prompt: str = "") -> str:
        import numpy as np
        import sounddevice as sd

        if prompt:
            self.say("judge", prompt, 0, allow_barge_in=False)
        print("  [真人麦克风] 请发言；句末静音后自动识别……")
        block = 1024
        frames, heard, silent = [], False, 0
        silence_blocks = max(1, int(self.silence_seconds * self.sample_rate / block))
        deadline = time.monotonic() + self.max_utterance
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32", blocksize=block) as stream:
            while time.monotonic() < deadline:
                data, _ = stream.read(block)
                mono = data[:, 0].copy()
                frames.append(mono)
                rms = float(np.sqrt(np.mean(np.square(mono))))
                if rms >= self.threshold:
                    heard, silent = True, 0
                elif heard:
                    silent += 1
                    if silent >= silence_blocks:
                        break
        if not heard:
            raise TimeoutError("规定时间内没有检测到真人语音")
        path = Path(tempfile.mkstemp(suffix=".wav")[1])
        try:
            self._write_wav(frames, path)
            text = self._transcribe(path, kind="human_asr")
            print(f"  [ASR] 真人：{text}")
            return text
        finally:
            path.unlink(missing_ok=True)

    def say(self, speaker: str, text: str, round_no: int, *, allow_barge_in: bool = False) -> Optional[str]:
        path = self._tts(speaker, text, round_no)
        if not (allow_barge_in and self.allow_interruptions):
            subprocess.run([self.player, str(path)], check=False)
            return None

        # Real barge-in: monitor microphone during playback, cancel output on speech,
        # then hand the captured utterance to ASR as an interruption turn.
        import numpy as np
        import sounddevice as sd
        block = 1024
        proc = subprocess.Popen([self.player, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        frames = []
        consecutive = 0
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32", blocksize=block) as stream:
            while proc.poll() is None:
                data, _ = stream.read(block)
                mono = data[:, 0].copy()
                rms = float(np.sqrt(np.mean(np.square(mono))))
                consecutive = consecutive + 1 if rms >= self.threshold else 0
                if consecutive >= 2:
                    frames.extend([mono])
                    proc.terminate()
                    self._event("barge_in", interrupted_speaker=speaker)
                    break
            if not frames:
                return None
            silent = 0
            silence_blocks = max(1, int(self.silence_seconds * self.sample_rate / block))
            deadline = time.monotonic() + self.max_utterance
            while time.monotonic() < deadline:
                data, _ = stream.read(block)
                mono = data[:, 0].copy()
                frames.append(mono)
                rms = float(np.sqrt(np.mean(np.square(mono))))
                silent = silent + 1 if rms < self.threshold else 0
                if silent >= silence_blocks:
                    break
        wav_path = Path(tempfile.mkstemp(suffix=".wav")[1])
        try:
            self._write_wav(frames, wav_path)
            return self._transcribe(wav_path, kind="interruption_asr")
        finally:
            wav_path.unlink(missing_ok=True)

    # Judge expects a TTS-like object with synth().
    def synth(self, speaker: str, text: str, round_no: int):
        return self.say(speaker, text, round_no, allow_barge_in=True)


class HumanPlayerAgent(PlayerAgent):
    """A real human seat that obeys the same private-memory boundary as AI seats."""

    def __init__(self, name: str, role: Role, voice: LiveVoiceSession):
        super().__init__(name, role, offline=True)
        self.voice = voice
        self.is_human = True
        self.is_user = True

    @staticmethod
    def _explicit_none(text: str) -> bool:
        folded = text.casefold()
        return bool(
            any(word in folded for word in ("放弃", "不用", "弃票"))
            or re.search(r"\b(?:none|abstain|skip)\b", folded)
        )

    @staticmethod
    def _spoken_target(text: str, candidates: List[str], allow_none: bool) -> Optional[str]:
        if allow_none and HumanPlayerAgent._explicit_none(text):
            return None
        match = re.search(r"(?:P|player\s*|玩家\s*|[投查验救毒刀]\s*)(\d+)", text, re.I)
        if match and f"P{int(match.group(1))}" in candidates:
            return f"P{int(match.group(1))}"
        chinese = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8}
        match = re.search(r"([一二三四五六七八])号", text)
        if match and f"P{chinese[match.group(1)]}" in candidates:
            return f"P{chinese[match.group(1)]}"
        english = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        }
        match = re.search(
            r"(?:player|seat)\s+(one|two|three|four|five|six|seven|eight|nine|ten)\b",
            text,
            re.I,
        )
        if match and f"P{english[match.group(1).casefold()]}" in candidates:
            return f"P{english[match.group(1).casefold()]}"
        return PlayerAgent._parse_target(text, candidates, allow_none)

    def speak(self, players: List[str]) -> str:
        return self.voice.listen("现在轮到您公开发言。请结合已知信息说出您的分析。")

    def choose_target(self, prompt: str, candidates: List[str], players: List[str], allow_none: bool = False):
        answer = self.voice.listen(f"{prompt} 候选：{'、'.join(candidates)}。请说出玩家编号。")
        return self._spoken_target(answer, candidates, allow_none)

    def vote(self, candidates: List[str], players: List[str]):
        answer = self.voice.listen(f"现在投票放逐。候选：{'、'.join(candidates)}。请说出玩家编号或弃票。")
        return self._spoken_target(answer, candidates, True)
