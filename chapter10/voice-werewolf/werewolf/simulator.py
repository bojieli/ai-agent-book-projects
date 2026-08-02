# -*- coding: utf-8 -*-
"""LLM-driven user simulator with a real speech round trip.

The simulator is deliberately not an ordinary all-AI player.  It occupies the same
protected user seat as ``HumanPlayerAgent`` and receives only that seat's memory.  For
each turn a real LLM must call the one legal user tool.  The selected utterance is then
synthesized to audio and the game consumes only the ASR transcript, never the original
text.  This makes ASR mistakes observable instead of silently bypassing the voice
boundary.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import List, Optional

from . import agent as agent_module
from .agent import PlayerAgent
from .human import HumanPlayerAgent
from .roles import Role


def _usage_dict(value):
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return None


class SimulatedVoiceSession:
    """Headless speech transport for a synthetic user.

    ``openai`` uses the hosted OpenAI TTS and ASR APIs. ``gemini-system`` uses a
    real local OS synthesizer to create the waveform and the hosted Gemini API for
    ASR. ``openrouter-system`` uses the same local synthesis plus a multimodal model
    through OpenRouter. ``auto`` chooses OpenAI, then OpenRouter, then Gemini. In all
    cases the LLM user's text must cross an actual audio file and ASR before the game
    sees it.
    """

    def __init__(self, out_dir: str, *, provider: str = "auto"):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.events = []
        self._sequence = 0
        requested = provider.casefold()
        if requested == "auto":
            requested = (
                "openai" if os.getenv("OPENAI_API_KEY")
                else "openrouter-system" if os.getenv("OPENROUTER_API_KEY")
                else "gemini-system"
            )
        if requested not in {"openai", "openrouter-system", "gemini-system"}:
            raise ValueError(
                "simulator speech provider must be auto, openai, openrouter-system, "
                "or gemini-system"
            )
        self.provider = requested
        self.client = None
        self.espeak = None
        self.system_say = None
        self.ffmpeg = None
        if requested == "openai":
            from openai import OpenAI

            if not os.getenv("OPENAI_API_KEY"):
                raise RuntimeError("OpenAI simulator speech requires OPENAI_API_KEY")
            self.client = OpenAI(
                api_key=os.environ["OPENAI_API_KEY"], timeout=90, max_retries=1
            )
        else:
            if requested == "gemini-system" and not os.getenv("GEMINI_API_KEY"):
                raise RuntimeError("gemini-system simulator speech requires GEMINI_API_KEY")
            if requested == "openrouter-system":
                from openai import OpenAI

                if not os.getenv("OPENROUTER_API_KEY"):
                    raise RuntimeError(
                        "openrouter-system simulator speech requires OPENROUTER_API_KEY"
                    )
                self.client = OpenAI(
                    api_key=os.environ["OPENROUTER_API_KEY"],
                    base_url="https://openrouter.ai/api/v1",
                    timeout=90,
                    max_retries=1,
                )
            self.espeak = shutil.which("espeak-ng") or shutil.which("espeak")
            self.system_say = shutil.which("say")
            self.ffmpeg = shutil.which("ffmpeg")
            if not (self.espeak or self.system_say) or not self.ffmpeg:
                raise RuntimeError(
                    "system speech requires espeak (Linux) or say (macOS), plus ffmpeg"
                )

    def _event(self, type_: str, **data):
        self._sequence += 1
        event = {
            "sequence": self._sequence,
            "monotonic": time.monotonic(),
            "wall_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "type": type_,
            **data,
        }
        self.events.append(event)
        (self.out_dir / "simulator_voice_trace.json").write_text(
            json.dumps(self.events, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return event

    def record_llm_decision(self, **data):
        self._event("simulator_llm_tool", **data)

    def _synthesize(self, speaker: str, text: str, round_no: int) -> Path:
        if not text.strip():
            raise ValueError("refusing to synthesize an empty utterance")
        started = time.monotonic()
        stem = f"r{round_no}_{speaker}_{self._sequence + 1}"
        request_id = None
        model = None
        if self.provider == "openai":
            path = self.out_dir / f"{stem}.mp3"
            model = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
            response = self.client.audio.speech.create(
                model=model,
                voice=os.getenv("OPENAI_TTS_VOICE", "coral"),
                input=text,
                response_format="mp3",
            )
            path.write_bytes(response.content)
            request_id = getattr(response, "_request_id", None)
            provider = "OpenAI Audio API"
        else:
            path = self.out_dir / f"{stem}.wav"
            with tempfile.TemporaryDirectory(prefix="werewolf-simulator-tts-") as directory:
                if self.espeak:
                    voice = os.getenv("SIMULATOR_ESPEAK_VOICE", "en-us")
                    model = f"espeak-{voice}"
                    source = Path(directory) / "speech.wav"
                    command = [
                        self.espeak,
                        "-v", voice,
                        "-s", os.getenv("SIMULATOR_ESPEAK_SPEED", "145"),
                        "-w", str(source),
                        text,
                    ]
                else:
                    voice = os.getenv("SIMULATOR_SAY_VOICE", "Samantha")
                    model = f"macos-say-{voice}"
                    source = Path(directory) / "speech.aiff"
                    command = [self.system_say, "-v", voice, "-o", str(source), text]
                subprocess.run(command, check=True, capture_output=True)
                subprocess.run(
                    [self.ffmpeg, "-nostdin", "-loglevel", "error", "-y", "-i",
                     str(source), "-ac", "1", "-ar", "24000", str(path)],
                    check=True,
                    capture_output=True,
                )
            provider = "local espeak"
        content = path.read_bytes()
        if not content:
            raise RuntimeError("speech synthesizer returned empty audio")
        self._event(
            "tts_ready",
            speaker=speaker,
            provider=provider,
            model=model,
            request_id=request_id,
            latency_seconds=round(time.monotonic() - started, 3),
            file=str(path),
            audio_bytes=len(content),
            audio_sha256=hashlib.sha256(content).hexdigest(),
        )
        return path

    def _transcribe(self, path: Path) -> str:
        started = time.monotonic()
        request_id = None
        usage = None
        if self.provider == "openai":
            model = os.getenv("OPENAI_ASR_MODEL", "gpt-4o-mini-transcribe")
            with path.open("rb") as audio:
                response = self.client.audio.transcriptions.create(
                    model=model,
                    file=audio,
                    language=os.getenv("VOICE_LANGUAGE", "zh"),
                )
            transcript = response.text.strip()
            request_id = getattr(response, "_request_id", None)
            provider = "OpenAI Audio API"
        elif self.provider == "openrouter-system":
            model = os.getenv("SIMULATOR_ASR_MODEL", "google/gemini-2.5-flash")
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": (
                        "Transcribe this short Werewolf game utterance exactly. Return only the "
                        "transcript with no label, quotes, explanation, or Markdown. Preserve "
                        "player-number phrases and seat labels such as P1."
                    )},
                    {"type": "input_audio", "input_audio": {
                        "data": base64.b64encode(path.read_bytes()).decode("ascii"),
                        "format": "wav",
                    }},
                ]}],
                temperature=0,
                max_tokens=512,
            )
            transcript = (response.choices[0].message.content or "").strip()
            request_id = getattr(response, "id", None)
            usage = _usage_dict(getattr(response, "usage", None))
            provider = "OpenRouter multimodal audio API"
        else:
            model = os.getenv("GEMINI_ASR_MODEL", "gemini-2.5-flash")
            audio = path.read_bytes()
            payload = json.dumps(
                {
                    "contents": [{"parts": [
                        {"text": (
                            "Transcribe this Mandarin Werewolf game utterance exactly. Return only "
                            "the transcript with no label, quotes, explanation, or Markdown. Preserve "
                            "seat labels such as P1 and Chinese player-number phrases."
                        )},
                        {"inline_data": {
                            "mime_type": "audio/wav",
                            "data": base64.b64encode(audio).decode("ascii"),
                        }},
                    ]}],
                    "generationConfig": {"temperature": 0, "maxOutputTokens": 512},
                },
                ensure_ascii=False,
            ).encode("utf-8")
            key = os.environ["GEMINI_API_KEY"]
            request = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
                request_id = response.headers.get("x-request-id")
            transcript = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            usage = data.get("usageMetadata")
            provider = "Google Gemini API"
        if not transcript:
            raise RuntimeError("ASR returned an empty transcript")
        self._event(
            "simulator_asr",
            provider=provider,
            model=model,
            request_id=request_id,
            usage=usage,
            latency_seconds=round(time.monotonic() - started, 3),
            source_audio_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            transcript=transcript,
        )
        return transcript

    def roundtrip_user(self, speaker: str, text: str, round_no: int) -> str:
        path = self._synthesize(speaker, text, round_no)
        return self._transcribe(path)

    def say(self, speaker: str, text: str, round_no: int, *, allow_barge_in: bool = False):
        self._synthesize(speaker, text, round_no)
        return None

    def synth(self, speaker: str, text: str, round_no: int):
        return self.say(speaker, text, round_no)


class SimulatedUserPlayerAgent(PlayerAgent):
    """An independent, tool-using LLM behind the user seat's speech boundary."""

    _CHINESE_NUMBERS = {
        1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
        6: "六", 7: "七", 8: "八", 9: "九", 10: "十",
    }

    def __init__(self, name: str, role: Role, voice: SimulatedVoiceSession, *, model=None):
        super().__init__(name, role, offline=False)
        self.voice = voice
        self.simulator_model = model
        self.is_simulated_user = True
        self.is_user = True

    def _tool_call(self, *, tool_name: str, description: str, properties: dict,
                   required: List[str], instruction: str, players: List[str]):
        messages = [
            {"role": "system", "content": (
                self._system_prompt(players)
                + "\n你是独立的用户模拟器。请像有策略的真人玩家一样推理，并且必须调用给定工具完成当前回合。"
                + "\n证据纪律：把公开身份声明与自己确定知道的事实逐项比较。正确说出你的阵营是支持该声明的证据，"
                  "但不是绝对证明；矛盾声明则是反证。不要仅因某人公开了神职身份就投他，尤其不要在没有对跳或矛盾时"
                  "仅凭‘过早跳身份’放逐唯一的预言家声明者。怀疑与投票必须引用具体发言、查验声明或既有投票记录。"
            )},
            {"role": "user", "content": (
                f"【你目前掌握的信息（仅你可见）】\n{self._context_block()}\n\n"
                f"【当前任务】\n{instruction}"
            )},
        ]
        tool = {
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False,
                },
            },
        }
        client = agent_module.get_client()
        model = self.simulator_model or agent_module._MODEL
        response = agent_module._safe_create(
            client,
            model=model,
            messages=messages,
            tools=[tool],
            tool_choice={"type": "function", "function": {"name": tool_name}},
            temperature=0.8,
            max_tokens=512,
        )
        message = response.choices[0].message
        calls = message.tool_calls or []
        if len(calls) != 1 or calls[0].function.name != tool_name:
            raise RuntimeError(f"user simulator did not call required tool {tool_name}")
        try:
            arguments = json.loads(calls[0].function.arguments)
        except (TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("user simulator returned invalid tool arguments") from exc
        self.voice.record_llm_decision(
            seat=self.name,
            tool=tool_name,
            arguments=arguments,
            response_id=getattr(response, "id", None),
            requested_model=model,
            provider_reported_model=getattr(response, "model", None),
            usage=_usage_dict(getattr(response, "usage", None)),
        )
        return arguments

    def speak(self, players: List[str]) -> str:
        arguments = self._tool_call(
            tool_name="speak_publicly",
            description="Submit the simulated user's public Werewolf speech.",
            properties={
                "utterance": {
                    "type": "string",
                    "description": "Natural concise English public speech, 2-4 short sentences.",
                }
            },
            required=["utterance"],
            instruction=(
                "现在轮到你公开发言。结合私有记忆和公开历史进行真实的社交推理。"
                "狼人应隐藏身份；好人应引用证据。为保证本机 TTS 清晰，请用简洁英文发言，"
                "然后调用 speak_publicly。"
            ),
            players=players,
        )
        utterance = str(arguments.get("utterance", "")).strip()
        if not utterance:
            raise RuntimeError("user simulator submitted empty public speech")
        return self.voice.roundtrip_user(self.name, utterance, self._round_no())

    def _round_no(self) -> int:
        if hasattr(self, "current_round"):
            return int(self.current_round)
        rounds = []
        for item in self.memory:
            import re
            rounds.extend(int(value) for value in re.findall(r"第(\d+)回合", item))
        return max(rounds, default=0)

    def _choose(self, *, prompt: str, candidates: List[str], players: List[str],
                allow_none: bool, action: str) -> Optional[str]:
        choices = list(candidates) + (["none"] if allow_none else [])
        arguments = self._tool_call(
            tool_name="choose_player",
            description="Select exactly one legal player target or explicitly abstain when allowed.",
            properties={
                "target": {"type": "string", "enum": choices},
                "reason": {"type": "string", "description": "A concise strategic reason."},
            },
            required=["target", "reason"],
            instruction=(
                f"{prompt}\n合法目标：{'、'.join(choices)}。这是 {action} 行动。"
                "只依据你的私有记忆和公开信息推理，然后调用 choose_player。"
            ),
            players=players,
        )
        target = str(arguments.get("target", "")).strip()
        if target not in choices:
            raise RuntimeError(f"user simulator selected illegal target {target!r}")
        self.last_decision_reason = str(arguments.get("reason", "")).strip() or None
        expected = None if target == "none" else target
        if expected is None:
            spoken = "I choose to abstain."
        else:
            number = int(expected[1:])
            english = {
                1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
                6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
            }
            spoken = f"I choose player {english.get(number, number)}."
        transcript = self.voice.roundtrip_user(self.name, spoken, self._round_no())
        parsed = HumanPlayerAgent._spoken_target(transcript, candidates, allow_none)
        explicit_abstention = expected is not None or HumanPlayerAgent._explicit_none(transcript)
        if parsed != expected or not explicit_abstention:
            self.voice._event(
                "simulator_action_mismatch",
                action=action,
                tool_target=target,
                asr_transcript=transcript,
                parsed_target=parsed,
            )
            raise RuntimeError(
                f"speech boundary changed simulator action: tool={target}, transcript={transcript!r}, parsed={parsed}"
            )
        return expected

    def choose_target(self, prompt: str, candidates: List[str], players: List[str],
                      allow_none: bool = False) -> Optional[str]:
        return self._choose(
            prompt=prompt,
            candidates=candidates,
            players=players,
            allow_none=allow_none,
            action="night_target",
        )

    def vote(self, candidates: List[str], players: List[str]) -> Optional[str]:
        return self._choose(
            prompt=(
                "现在是白天投票放逐环节，选出你认为最可能是狼人的玩家。好人阵营必须"
                "按证据强度决策：没有对跳且已报告自洽查验结果的预言家声明是当前最强"
                "公开证据；除非有具体矛盾或另一名预言家对跳，不得投该声明者。若其报告"
                "某玩家是狼人，应优先投被查杀者；被查杀者仅仅否认不构成矛盾或对跳。"
                "理由必须引用具体发言、查验或既有票型。"
            ),
            candidates=candidates,
            players=players,
            allow_none=True,
            action="vote",
        )
