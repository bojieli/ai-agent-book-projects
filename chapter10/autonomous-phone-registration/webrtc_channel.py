"""Local WebRTC transport for the Experiment 10-5 Phone Agent.

The participant page contains the two ends of a standards-based WebRTC call.  The
agent sends synthesized speech on one RTP audio track; the participant sends a
microphone track in the other direction.  Only the peer-side recording is handed to
ASR, and it is kept in memory.  A safe acceptance mode substitutes generated speech
for the microphone without bypassing WebRTC, MediaRecorder, or ASR.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Tuple


CALL_PAGE = r"""<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Experiment 10-5 · Private WebRTC call</title>
<style>
  :root { color-scheme: light dark; font: 16px/1.5 system-ui, sans-serif; }
  body { max-width: 760px; margin: 4rem auto; padding: 0 1.25rem; }
  .card { border: 1px solid #8886; border-radius: 16px; padding: 1.4rem; }
  #status { font-weight: 700; }
  #prompt { min-height: 4.5rem; font-size: 1.15rem; padding: 1rem; background: #8881; }
  button { font: inherit; padding: .7rem 1rem; margin-right: .5rem; }
  .privacy { color: #666; font-size: .9rem; }
</style>
<body>
  <main class="card">
    <h1>Registration assistant call</h1>
    <p id="status">Connecting a private local WebRTC session…</p>
    <p id="prompt" aria-live="polite">The assistant's question will appear here.</p>
    <button id="start" disabled>Start answer</button>
    <button id="stop" disabled>Finish answer</button>
    <p class="privacy">Audio stays in this process: the received answer is transcribed
      ephemerally and raw media is discarded. No phone number or PSTN provider is used.</p>
    <audio id="remoteAudio" autoplay></audio>
  </main>
<script>
(() => {
  const q = new URLSearchParams(location.search);
  const automated = q.get('automation') === '1';
  const status = document.querySelector('#status');
  const prompt = document.querySelector('#prompt');
  const start = document.querySelector('#start');
  const stop = document.querySelector('#stop');
  const remoteAudio = document.querySelector('#remoteAudio');
  let context, agentPeer, userPeer, agentOutput, userOutput;
  let control, agentInput, currentRecorder, answerResolve, answerReject, answerTimer;
  const call = { offers: 0, answers: 0, iceCandidates: 0, mediaRecordings: 0 };

  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  const asBytes = value => Uint8Array.from(atob(value), c => c.charCodeAt(0));
  const asBase64 = blob => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = reject;
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.readAsDataURL(blob);
  });
  async function playInto(base64Audio, destination) {
    const decoded = await context.decodeAudioData(asBytes(base64Audio).buffer);
    const source = context.createBufferSource();
    source.buffer = decoded;
    source.connect(destination);
    source.start();
    await new Promise(resolve => source.onended = resolve);
    return decoded.duration;
  }
  async function rtpStats() {
    const rows = [];
    for (const [side, peer] of [['agent', agentPeer], ['participant', userPeer]]) {
      for (const item of (await peer.getStats()).values()) {
        if (item.kind === 'audio' && (item.type === 'inbound-rtp' || item.type === 'outbound-rtp')) {
          rows.push({
            side, type: item.type,
            packets: item.packetsReceived ?? item.packetsSent ?? 0,
            bytes: item.bytesReceived ?? item.bytesSent ?? 0
          });
        }
      }
    }
    return rows;
  }
  async function finishRecording(error) {
    clearTimeout(answerTimer);
    const recorder = currentRecorder;
    if (!recorder) return;
    const done = new Promise(resolve => recorder.onstop = resolve);
    recorder.stop();
    await done;
    currentRecorder = null;
    start.disabled = automated;
    stop.disabled = true;
    if (error) {
      answerReject?.(error);
    } else {
      const blob = new Blob(recorder.__chunks || [], { type: recorder.mimeType });
      answerResolve?.({ audio: await asBase64(blob), mime: blob.type, stats: await rtpStats() });
    }
  }
  // Keep chunks on the recorder so finishRecording does not retain answer media globally.
  function prepareRecording(timeoutMs) {
    return new Promise((resolve, reject) => {
      answerResolve = resolve; answerReject = reject;
      if (!agentInput) return reject(new Error('participant audio track is unavailable'));
      const chunks = [];
      const type = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus' : 'audio/webm';
      currentRecorder = new MediaRecorder(agentInput, { mimeType: type });
      currentRecorder.__chunks = chunks;
      currentRecorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
      currentRecorder.start(100);
      call.mediaRecordings += 1;
      start.disabled = true; stop.disabled = false;
      status.textContent = 'Listening over the WebRTC audio track…';
      answerTimer = setTimeout(() => finishRecording(new Error('answer timed out')), timeoutMs);
    });
  }

  window.agentSay = async ({audio, text}) => {
    prompt.textContent = text;
    if (control?.readyState === 'open') control.send(JSON.stringify({type: 'prompt', text}));
    const duration = await playInto(audio, agentOutput);
    return { duration, stats: await rtpStats() };
  };
  window.waitForHumanAnswer = timeoutMs => new Promise((resolve, reject) => {
    status.textContent = 'Click Start answer, speak, then click Finish answer.';
    start.disabled = false;
    stop.disabled = true;
    const startTimer = setTimeout(() => {
      start.disabled = true;
      reject(new Error('answer was not started before timeout'));
    }, timeoutMs);
    start.onclick = () => {
      clearTimeout(startTimer);
      prepareRecording(timeoutMs).then(resolve, reject);
    };
  });
  window.acceptanceAnswer = async ({audio, timeoutMs}) => {
    const result = prepareRecording(timeoutMs);
    await wait(250);
    await playInto(audio, userOutput);
    await wait(300);
    await finishRecording();
    return result;
  };
  window.callReceipt = async () => ({
    ...call,
    agentConnectionState: agentPeer?.connectionState,
    participantConnectionState: userPeer?.connectionState,
    rtp: await rtpStats()
  });
  window.closeCall = async () => {
    clearTimeout(answerTimer);
    for (const peer of [agentPeer, userPeer]) {
      peer?.getSenders().forEach(sender => sender.track?.stop());
      peer?.close();
    }
    context?.close();
  };
  stop.onclick = () => finishRecording();

  window.callReady = (async () => {
    context = new AudioContext();
    await context.resume();
    agentPeer = new RTCPeerConnection({iceServers: []});
    userPeer = new RTCPeerConnection({iceServers: []});
    agentPeer.onicecandidate = event => {
      if (event.candidate) { call.iceCandidates++; userPeer.addIceCandidate(event.candidate); }
    };
    userPeer.onicecandidate = event => {
      if (event.candidate) { call.iceCandidates++; agentPeer.addIceCandidate(event.candidate); }
    };
    agentOutput = context.createMediaStreamDestination();
    agentPeer.addTrack(agentOutput.stream.getAudioTracks()[0], agentOutput.stream);
    if (automated) {
      userOutput = context.createMediaStreamDestination();
      userPeer.addTrack(userOutput.stream.getAudioTracks()[0], userOutput.stream);
    } else {
      const mic = await navigator.mediaDevices.getUserMedia({audio: true, video: false});
      userPeer.addTrack(mic.getAudioTracks()[0], mic);
    }
    agentPeer.ontrack = event => { agentInput = event.streams[0]; };
    userPeer.ontrack = event => { remoteAudio.srcObject = event.streams[0]; remoteAudio.play().catch(() => {}); };
    control = agentPeer.createDataChannel('non-sensitive-control');
    userPeer.ondatachannel = event => event.channel.onmessage = message => {
      const payload = JSON.parse(message.data);
      if (payload.type === 'prompt') prompt.textContent = payload.text;
    };
    const offer = await agentPeer.createOffer(); call.offers++;
    await agentPeer.setLocalDescription(offer);
    await userPeer.setRemoteDescription(offer);
    const answer = await userPeer.createAnswer(); call.answers++;
    await userPeer.setLocalDescription(answer);
    await agentPeer.setRemoteDescription(answer);
    for (let i = 0; i < 100 && (agentPeer.connectionState !== 'connected' || userPeer.connectionState !== 'connected'); i++) await wait(50);
    if (agentPeer.connectionState !== 'connected' || userPeer.connectionState !== 'connected') throw new Error('WebRTC connection did not reach connected state');
    status.textContent = automated ? 'Safe synthesized participant connected.' : 'Private WebRTC call connected.';
    start.disabled = true;
    return window.callReceipt();
  })();
})();
</script>
</body>
</html>"""


class SpeechBackend(Protocol):
    provider: str

    async def synthesize(self, text: str) -> Tuple[bytes, str, Dict[str, object]]: ...
    async def transcribe(self, audio: bytes, mime: str) -> Tuple[str, Dict[str, object]]: ...


class OpenAISpeechBackend:
    """OpenAI speech provider with value-free receipts."""

    provider = "OpenAI Audio API"

    def __init__(self, *, language: str = "zh", voice: str = "coral"):
        from openai import OpenAI

        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("WebRTC 实时语音需要 OPENAI_API_KEY")
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=90, max_retries=1)
        self.language = language
        self.voice = voice

    async def synthesize(self, text: str) -> Tuple[bytes, str, Dict[str, object]]:
        started = time.monotonic()

        def call():
            response = self.client.audio.speech.create(
                model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
                voice=self.voice,
                input=text,
                response_format="mp3",
            )
            return response.content, getattr(response, "_request_id", None)

        content, request_id = await asyncio.to_thread(call)
        return content, "audio/mpeg", {
            "operation": "tts",
            "provider": self.provider,
            "model": os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
            "request_id": request_id,
            "response_bytes": len(content),
            "latency_seconds": round(time.monotonic() - started, 3),
        }

    async def transcribe(self, audio: bytes, mime: str) -> Tuple[str, Dict[str, object]]:
        started = time.monotonic()

        def call():
            extension = ".webm" if "webm" in mime else ".wav"
            stream = io.BytesIO(audio)
            stream.name = f"ephemeral-answer{extension}"
            response = self.client.audio.transcriptions.create(
                model=os.getenv("OPENAI_ASR_MODEL", "gpt-4o-mini-transcribe"),
                file=stream,
                language=self.language,
            )
            return response.text.strip(), getattr(response, "_request_id", None)

        text, request_id = await asyncio.to_thread(call)
        return text, {
            "operation": "asr",
            "provider": self.provider,
            "model": os.getenv("OPENAI_ASR_MODEL", "gpt-4o-mini-transcribe"),
            "request_id": request_id,
            "request_bytes": len(audio),
            "latency_seconds": round(time.monotonic() - started, 3),
            "raw_audio_retained": False,
            "transcript_retained": False,
        }


class SystemGeminiSpeechBackend:
    """Local OS speech synthesis plus Gemini audio transcription.

    This backend keeps generated prompt audio local and uses the already-authorized
    Gemini endpoint only for ASR.  It is useful when an OpenAI text key is available
    but its separate Audio API quota is not.
    """

    provider = "local system TTS + Google Gemini ASR"

    def __init__(self):
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("Gemini ASR requires GEMINI_API_KEY")
        self.say = shutil.which("say")
        self.espeak = shutil.which("espeak-ng") or shutil.which("espeak")
        self.ffmpeg = shutil.which("ffmpeg")
        if not (self.say or self.espeak) or not self.ffmpeg:
            raise RuntimeError("local TTS requires say/espeak and ffmpeg")

    async def synthesize(self, text: str) -> Tuple[bytes, str, Dict[str, object]]:
        started = time.monotonic()

        def call() -> bytes:
            with tempfile.TemporaryDirectory(prefix="exp10-5-tts-") as directory:
                source = Path(directory) / ("speech.aiff" if self.say else "speech.wav")
                target = Path(directory) / "speech.wav"
                if self.say:
                    subprocess.run([self.say, "-o", str(source), text], check=True, capture_output=True)
                else:
                    subprocess.run([self.espeak, "-w", str(source), text], check=True, capture_output=True)
                converted = Path(directory) / "speech-24k.wav"
                subprocess.run(
                    [self.ffmpeg, "-nostdin", "-loglevel", "error", "-y", "-i", str(source),
                     "-ac", "1", "-ar", "24000", str(converted)],
                    check=True, capture_output=True,
                )
                return converted.read_bytes()

        content = await asyncio.to_thread(call)
        return content, "audio/wav", {
            "operation": "tts",
            "provider": "macOS say" if self.say else "espeak",
            "model": "operating-system speech synthesizer",
            "request_id": None,
            "response_bytes": len(content),
            "latency_seconds": round(time.monotonic() - started, 3),
            "network_used": False,
        }

    async def transcribe(self, audio: bytes, mime: str) -> Tuple[str, Dict[str, object]]:
        started = time.monotonic()
        model = os.getenv("GEMINI_ASR_MODEL", "gemini-2.5-flash")

        def call():
            payload = json.dumps({
                "contents": [{"parts": [
                    {"text": (
                        "Transcribe this single short form-field answer exactly. Return only the "
                        "transcript, with no quotes, label, explanation, or Markdown. Preserve email "
                        "addresses, digits, punctuation, and capitalization when audible."
                    )},
                    {"inline_data": {
                        "mime_type": mime.split(";", 1)[0],
                        "data": base64.b64encode(audio).decode("ascii"),
                    }},
                ]}],
                "generationConfig": {"temperature": 0, "maxOutputTokens": 256},
            }).encode("utf-8")
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
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return text, request_id, data.get("usageMetadata", {})

        text, request_id, usage = await asyncio.to_thread(call)
        return text, {
            "operation": "asr",
            "provider": "Google Gemini",
            "model": model,
            "request_id": request_id,
            "usage": usage,
            "request_bytes": len(audio),
            "latency_seconds": round(time.monotonic() - started, 3),
            "raw_audio_retained": False,
            "transcript_retained": False,
        }


class SystemWhisperSpeechBackend(SystemGeminiSpeechBackend):
    """Local OS speech synthesis and a local OpenAI Whisper checkpoint."""

    provider = "local system TTS + local OpenAI Whisper"

    def __init__(self):
        self.say = shutil.which("say")
        self.espeak = shutil.which("espeak-ng") or shutil.which("espeak")
        self.ffmpeg = shutil.which("ffmpeg")
        if not (self.say or self.espeak) or not self.ffmpeg:
            raise RuntimeError("local speech requires say/espeak and ffmpeg")
        requested = os.getenv("WHISPER_PYTHON")
        candidates = [requested] if requested else [sys.executable, shutil.which("python3")]
        self.whisper_python = next(
            (candidate for candidate in candidates if candidate and self._has_whisper(candidate)), None
        )
        if not self.whisper_python:
            raise RuntimeError(
                "local ASR requires openai-whisper; set WHISPER_PYTHON to an environment containing whisper and torch"
            )

    @staticmethod
    def _has_whisper(python: str) -> bool:
        try:
            return subprocess.run(
                [python, "-c", "import torch, whisper"],
                capture_output=True, timeout=20,
            ).returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    async def transcribe(self, audio: bytes, mime: str) -> Tuple[str, Dict[str, object]]:
        started = time.monotonic()
        model = os.getenv("WHISPER_MODEL", "tiny")

        def call():
            with tempfile.TemporaryDirectory(prefix="exp10-5-asr-") as directory:
                source = Path(directory) / ("answer.webm" if "webm" in mime else "answer.wav")
                target = Path(directory) / "answer-16k.wav"
                source.write_bytes(audio)
                subprocess.run(
                    [self.ffmpeg, "-nostdin", "-loglevel", "error", "-y", "-i", str(source),
                     "-ac", "1", "-ar", "16000", str(target)],
                    check=True, capture_output=True,
                )
                script = "\n".join([
                    "import hashlib, json, pathlib, sys, torch, whisper",
                    "model_name, path = sys.argv[1:3]",
                    "cache = pathlib.Path.home()/'.cache'/'whisper'/(model_name+'.pt')",
                    "loaded = whisper.load_model(model_name)",
                    "result = loaded.transcribe(path, language='en', fp16=False, verbose=False)",
                    "print('EXPERIMENT_JSON='+json.dumps({",
                    " 'text': str(result.get('text') or '').strip(),",
                    " 'model_sha256': hashlib.sha256(cache.read_bytes()).hexdigest() if cache.exists() else None,",
                    " 'torch': torch.__version__, 'whisper': getattr(whisper, '__version__', 'unknown')}, ensure_ascii=False))",
                ])
                process = subprocess.run(
                    [self.whisper_python, "-c", script, model, str(target)],
                    check=True, capture_output=True, text=True, timeout=180,
                )
            marker = next(
                line for line in process.stdout.splitlines() if line.startswith("EXPERIMENT_JSON=")
            )
            return json.loads(marker.split("=", 1)[1])

        result = await asyncio.to_thread(call)
        return result["text"], {
            "operation": "asr",
            "provider": "local OpenAI Whisper",
            "model": f"whisper-{model}",
            "model_sha256": result["model_sha256"],
            "runtime": {"torch": result["torch"], "openai_whisper": result["whisper"]},
            "request_bytes": len(audio),
            "latency_seconds": round(time.monotonic() - started, 3),
            "network_used": False,
            "raw_audio_retained": False,
            "transcript_retained": False,
        }

def default_speech_backend() -> SpeechBackend:
    requested = os.getenv("WEBRTC_SPEECH_PROVIDER", "auto").casefold()
    if requested not in {"auto", "openai", "gemini-system", "local-whisper"}:
        raise RuntimeError(
            "WEBRTC_SPEECH_PROVIDER must be auto, openai, gemini-system, or local-whisper"
        )
    if requested == "local-whisper":
        return SystemWhisperSpeechBackend()
    if requested == "gemini-system" or (
        requested == "auto" and os.getenv("GEMINI_API_KEY")
        and (shutil.which("say") or shutil.which("espeak-ng") or shutil.which("espeak"))
        and shutil.which("ffmpeg")
    ):
        return SystemGeminiSpeechBackend()
    return OpenAISpeechBackend()


class _CallPageHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path.split("?", 1)[0] not in {"/", "/call"}:
            self.send_error(404)
            return
        body = CALL_PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        return


class WebRTCPhoneChannel:
    """A browser-based, bidirectional WebRTC PhoneChannel."""

    def __init__(
        self,
        *,
        headless: bool = False,
        port: int = 0,
        synthetic_answers: Optional[List[str]] = None,
        speech_backend: Optional[SpeechBackend] = None,
    ):
        self.headless = headless
        self.port = port
        self.synthetic_answers: asyncio.Queue[str] = asyncio.Queue()
        for answer in synthetic_answers or []:
            self.synthetic_answers.put_nowait(answer)
        self.synthetic_participant = synthetic_answers is not None
        self.speech = speech_backend or default_speech_backend()
        self.provider_receipts: List[Dict[str, object]] = []
        self.latencies: List[Dict[str, float]] = []
        self.tts_prompt_count = 0
        self.asr_count = 0
        self.closed = False
        self.call_status = "created"
        self.call_url = ""
        self.receipt: Dict[str, object] = {}
        self._server = None
        self._server_thread = None
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def start(self) -> None:
        from playwright.async_api import async_playwright

        self._server = ThreadingHTTPServer(("127.0.0.1", self.port), _CallPageHandler)
        self._server_thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._server_thread.start()
        self.call_url = f"http://127.0.0.1:{self._server.server_port}/call"
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=["--autoplay-policy=no-user-gesture-required"],
        )
        self._context = await self._browser.new_context(permissions=["microphone"])
        self._page = await self._context.new_page()
        url = self.call_url + ("?automation=1" if self.synthetic_participant else "")
        print(f"  [WebRTC] participant page: {self.call_url}")
        await self._page.goto(url, wait_until="domcontentloaded")
        self.receipt = await self._page.evaluate("() => window.callReady")
        self.call_status = "connected"

    async def say(self, text: str) -> None:
        if self.call_status != "connected":
            raise RuntimeError("WebRTC call is not connected")
        audio, _mime, provider_receipt = await self.speech.synthesize(text)
        self.provider_receipts.append(provider_receipt)
        started = time.monotonic()
        result = await self._page.evaluate(
            "payload => window.agentSay(payload)",
            {"audio": base64.b64encode(audio).decode("ascii"), "text": text},
        )
        self.tts_prompt_count += 1
        self.latencies.append({
            "tts_seconds": float(provider_receipt.get("latency_seconds", 0)),
            "webrtc_playback_seconds": round(time.monotonic() - started, 3),
        })
        self.receipt["rtp"] = result["stats"]

    async def listen(self, *, timeout: float = 120.0) -> str:
        if self.call_status != "connected":
            raise RuntimeError("WebRTC call is not connected")
        if self.synthetic_participant:
            answer = await asyncio.wait_for(self.synthetic_answers.get(), timeout)
            audio, _mime, tts_receipt = await self.speech.synthesize(answer)
            tts_receipt = {**tts_receipt, "operation": "synthetic_participant_tts"}
            self.provider_receipts.append(tts_receipt)
            result = await self._page.evaluate(
                "payload => window.acceptanceAnswer(payload)",
                {
                    "audio": base64.b64encode(audio).decode("ascii"),
                    "timeoutMs": int(timeout * 1000),
                },
            )
        else:
            result = await self._page.evaluate(
                "timeoutMs => window.waitForHumanAnswer(timeoutMs)", int(timeout * 1000)
            )
        captured = base64.b64decode(result["audio"])
        if len(captured) < 256:
            raise RuntimeError("WebRTC answer audio was empty")
        text, asr_receipt = await self.speech.transcribe(captured, result["mime"])
        # Delete the only Python reference before returning the transcript.  Raw
        # audio and transcripts never enter call receipts or message traces.
        captured = b""
        self.provider_receipts.append(asr_receipt)
        self.asr_count += 1
        self.latencies.append({"asr_seconds": float(asr_receipt.get("latency_seconds", 0))})
        self.receipt["rtp"] = result["stats"]
        return text

    async def close(self) -> None:
        if self.closed:
            return
        try:
            if self._page and not self._page.is_closed():
                try:
                    self.receipt = await self._page.evaluate("() => window.callReceipt()")
                    await self._page.evaluate("() => window.closeCall()")
                except Exception:
                    pass
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        finally:
            if self._server:
                await asyncio.to_thread(self._server.shutdown)
                self._server.server_close()
            if self._server_thread:
                self._server_thread.join(timeout=2)
            self.call_status = "completed"
            self.closed = True

    def acceptance_receipt(self) -> Dict[str, object]:
        """Return only transport metadata; no prompt, answer, audio, or transcript."""
        rtp = self.receipt.get("rtp", [])
        return {
            "transport": "webrtc",
            "signaling_scope": "in-page localhost offer/answer; no external relay",
            "offers": self.receipt.get("offers", 0),
            "answers": self.receipt.get("answers", 0),
            "ice_candidates": self.receipt.get("iceCandidates", 0),
            "media_recordings": self.receipt.get("mediaRecordings", 0),
            "agent_connection_state": self.receipt.get("agentConnectionState"),
            "participant_connection_state": self.receipt.get("participantConnectionState"),
            "audio_rtp": rtp,
            "tts_prompt_count": self.tts_prompt_count,
            "asr_count": self.asr_count,
            "speech_provider": self.speech.provider,
            "synthetic_participant": self.synthetic_participant,
            "raw_audio_retained": False,
            "transcripts_retained": False,
            "status": self.call_status,
        }
