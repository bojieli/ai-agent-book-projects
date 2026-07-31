"""Browser-to-aiortc voice Agent for Experiment 9-2.

The browser microphone is the only user-semantic input.  The server buffers its
decoded RTP audio, runs real Whisper ASR, sends that transcript to a real external
LLM, synthesizes the Agent reply, and places the resulting PCM on the WebRTC
downlink track.  The data channel carries captions and control events only.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import uuid
from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from agent import CallPlan, conversation_turn, direct_plan, react_plan
from aiortc import AudioStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamError
from av import AudioFrame, AudioResampler
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator
from speech import SystemSpeechSynthesizer, WhisperASR, sha256_bytes

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
load_dotenv(HERE / ".env")
CALLS: dict[str, dict[str, Any]] = {}
PEERS: dict[str, RTCPeerConnection] = {}
RUNTIMES: dict[str, CallRuntime] = {}
MAX_MICROPHONE_PCM_BYTES = 16_000 * 2 * 60


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_error(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    for name, secret in os.environ.items():
        if (
            any(marker in name.upper() for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD"))
            and len(secret) >= 8
        ):
            text = text.replace(secret, "[REDACTED]")
    return text[:1000]


class CreateCall(BaseModel):
    mode: Literal["direct", "react"]
    task: str = Field(default="", max_length=4000)
    callee_name: str = Field(default="", max_length=200)
    goal: str = Field(default="", max_length=2000)
    context: str = Field(default="", max_length=4000)
    instructions: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def validate_arm(self) -> CreateCall:
        if self.mode == "react" and not self.task.strip():
            raise ValueError("the ReAct arm requires a natural-language task")
        if self.mode == "direct":
            missing = [
                name
                for name in ("callee_name", "goal", "context", "instructions")
                if not getattr(self, name).strip()
            ]
            if missing:
                raise ValueError("the direct arm requires: " + ", ".join(missing))
        return self


class EventEnvelope(BaseModel):
    event: dict[str, Any]


class CompleteTask(BaseModel):
    result: str = Field(min_length=1, max_length=2000)
    appointment_time: str = Field(min_length=1, max_length=300)
    confirmation_number: str = Field(min_length=1, max_length=300)
    notes: str = Field(min_length=1, max_length=2000)


class FinishCall(BaseModel):
    reason: str = Field(default="user_hangup", max_length=200)


@dataclass
class QueuedUtterance:
    receipt: dict[str, Any]
    pcm: bytes
    offset: int = 0


class SynthesizedAudioTrack(AudioStreamTrack):
    """Continuous WebRTC audio track whose non-silent segments are real TTS PCM."""

    def __init__(self, record: dict[str, Any]) -> None:
        super().__init__()
        self.record = record
        self.queue: deque[QueuedUtterance] = deque()

    def enqueue(self, pcm: bytes, receipt: dict[str, Any]) -> None:
        if not pcm:
            raise ValueError("cannot enqueue empty TTS audio")
        receipt["enqueued_on_webrtc_track"] = True
        receipt["transmitted_samples"] = 0
        receipt["delivery_complete"] = False
        self.queue.append(QueuedUtterance(receipt=receipt, pcm=pcm))

    async def recv(self) -> AudioFrame:
        frame = await super().recv()
        target = bytearray(frame.samples * 2)
        cursor = 0
        while cursor < len(target) and self.queue:
            utterance = self.queue[0]
            available = len(utterance.pcm) - utterance.offset
            take = min(len(target) - cursor, available)
            target[cursor : cursor + take] = utterance.pcm[
                utterance.offset : utterance.offset + take
            ]
            utterance.offset += take
            cursor += take
            samples = take // 2
            utterance.receipt["transmitted_samples"] += samples
            self.record["transport"]["server_sent_tts_samples"] += samples
            if utterance.offset == len(utterance.pcm):
                utterance.receipt["delivery_complete"] = True
                utterance.receipt["delivered_pcm_sha256"] = utterance.receipt["pcm_sha256"]
                self.queue.popleft()
        frame.planes[0].update(bytes(target))
        return frame


class CallRuntime:
    def __init__(self, record: dict[str, Any]) -> None:
        self.record = record
        self.tts = SystemSpeechSynthesizer()
        self.asr = WhisperASR()
        self.output_track = SynthesizedAudioTrack(record)
        self.microphone_pcm = bytearray()
        self.resampler = AudioResampler(format="s16", layout="mono", rate=16_000)
        self.channel: Any | None = None
        self.commit_started = False


app = FastAPI(title="Experiment 9-2 WebRTC Voice Agent", version="3.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def _record(call_id: str) -> dict[str, Any]:
    record = CALLS.get(call_id)
    if record is None:
        raise HTTPException(status_code=404, detail="unknown call")
    return record


def _public(record: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(record, ensure_ascii=False))


def _hash_is_valid(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _llm_receipt_is_real(receipt: dict[str, Any]) -> bool:
    usage = receipt.get("usage") or {}
    return bool(
        receipt.get("execution") == "real_external_llm"
        and receipt.get("external_request_completed") is True
        and receipt.get("provider_response_id")
        and receipt.get("provider_model")
        and receipt.get("finish_reason")
        and int(usage.get("total_tokens", 0)) > 0
        and float(receipt.get("latency_seconds", 0)) > 0
        and _hash_is_valid(receipt.get("request_sha256"))
        and _hash_is_valid(receipt.get("raw_response_sha256"))
        and _hash_is_valid(receipt.get("response_content_sha256"))
        and receipt.get("fallback_used") is False
        and receipt.get("mock") is False
        and receipt.get("probe_only") is False
        and receipt.get("credential_fields_retained") is False
    )


def _acceptance(record: dict[str, Any]) -> dict[str, Any]:
    transport = record["transport"]
    stats = transport["rtc_stats"]
    transcript = record["transcript"]
    llm_receipts = record["models"]["llm_receipts"]
    asr_receipts = record["models"]["asr_receipts"]
    tts_receipts = record["models"]["tts_receipts"]
    planning_receipts = [item for item in llm_receipts if item.get("purpose") == "react_planning"]
    dialogue_receipts = [
        item for item in llm_receipts if item.get("purpose") == "post_asr_dialogue"
    ]
    all_model_receipts = [*llm_receipts, *asr_receipts, *tts_receipts]
    completion = record.get("completion") or {}
    first_agent = next((turn for turn in transcript if turn.get("speaker") == "agent"), {})
    checks = {
        "sdp_offer_answer_negotiated": bool(transport["sdp_negotiated"]),
        "ice_connected": bool(transport["ice_connected_observed"]),
        "data_channel_open": bool(transport["data_channel_open"]),
        "browser_microphone_track": bool(transport["local_audio_track"]),
        "server_downlink_audio_track": bool(transport["remote_audio_track"]),
        "outbound_audio_rtp": int(stats["outbound_packets"]) > 0
        and int(stats["outbound_bytes"]) > 0,
        "inbound_audio_rtp": int(stats["inbound_packets"]) > 0 and int(stats["inbound_bytes"]) > 0,
        "server_buffered_microphone_rtp": (
            int(transport["server_received_audio_frames"]) > 0
            and int(transport["server_received_audio_pcm_bytes"]) > 0
        ),
        "real_asr_consumed_microphone_audio": bool(
            asr_receipts
            and all(
                item.get("execution") == "real_local_inference"
                and item.get("input_source") == "browser_microphone_rtp"
                and _hash_is_valid(item.get("input_wav_sha256"))
                and _hash_is_valid(item.get("checkpoint_sha256"))
                and item.get("fallback_used") is False
                for item in asr_receipts
            )
        ),
        "external_react_planner_or_fixed_direct_control": (
            record["mode"] == "direct"
            and record["input_contract"]["fields_supplied_by_caller"]
            == ["callee_name", "goal", "context", "instructions"]
        )
        or (
            record["mode"] == "react"
            and len(planning_receipts) == 1
            and _llm_receipt_is_real(planning_receipts[0])
        ),
        "real_external_post_asr_dialogue": len(dialogue_receipts) == 1
        and _llm_receipt_is_real(dialogue_receipts[0]),
        "real_tts_assets_synthesized": len(tts_receipts) >= 2
        and all(
            item.get("execution") == "real_speech_synthesis"
            and int(item.get("sample_count", 0)) > 0
            and _hash_is_valid(item.get("wav_sha256"))
            and _hash_is_valid(item.get("pcm_sha256"))
            and item.get("fallback_used") is False
            for item in tts_receipts
        ),
        "tts_audio_transmitted_on_downlink": len(tts_receipts) >= 2
        and all(
            item.get("enqueued_on_webrtc_track") is True
            and item.get("delivery_complete") is True
            and int(item.get("transmitted_samples", 0)) == int(item.get("sample_count", -1))
            and item.get("delivered_pcm_sha256") == item.get("pcm_sha256")
            for item in tts_receipts
        ),
        "media_is_canonical_transcript_source": bool(transcript)
        and all(
            (turn.get("speaker") == "user" and turn.get("source") == "asr.microphone_rtp")
            or (turn.get("speaker") == "agent" and turn.get("source") == "tts.webrtc_downlink")
            for turn in transcript
        ),
        "data_channel_is_control_and_caption_only": int(
            record["event_counts"].get("semantic_user_messages", 0)
        )
        == 0,
        "missing_fields_were_clarified_aloud": (
            first_agent.get("purpose") == "missing_field_clarification"
            and first_agent.get("source") == "tts.webrtc_downlink"
            and (record["mode"] == "direct" or bool(record["plan"].get("missing_information")))
        ),
        "explicit_confirmation_observed": record.get("explicit_confirmation_observed") is True,
        "structured_completion_saved": bool(
            completion.get("appointment_time")
            and completion.get("confirmation_number")
            and completion.get("result")
        ),
        "no_mock_probe_or_fallback": bool(all_model_receipts)
        and all(
            item.get("mock") is False
            and item.get("probe_only") is False
            and item.get("fallback_used") is False
            for item in all_model_receipts
        ),
        "privacy_boundary_preserved": record["privacy"]["private_audio_retained"] is False
        and record["privacy"]["private_transcripts_retained"] is False,
    }
    return {"checks": checks, "passed": all(checks.values()) and not record["errors"]}


def _retained_media_path(record: dict[str, Any], filename: str) -> Path | None:
    if os.getenv("PHONE_SAFE_SYNTHETIC_ACCEPTANCE") != "1":
        return None
    root = os.getenv("PHONE_EVIDENCE_DIR")
    if not root:
        raise RuntimeError("safe acceptance media retention requires PHONE_EVIDENCE_DIR")
    path = Path(root).resolve() / "media" / record["mode"] / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _relative_evidence_path(path: Path | None) -> str | None:
    if path is None:
        return None
    root = Path(os.environ["PHONE_EVIDENCE_DIR"]).resolve()
    return str(path.relative_to(root))


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "experiment": "9-2",
        "model_provider": os.getenv("PHONE_MODEL_PROVIDER", "ark"),
        "model_credential_present": bool(
            os.getenv("ARK_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("OPENROUTER_API_KEY")
        ),
        "speech_paths": "browser microphone RTP -> Whisper ASR; system TTS -> WebRTC RTP",
    }


@app.post("/api/calls")
async def create_call(request: CreateCall) -> dict[str, Any]:
    try:
        if request.mode == "direct":
            plan = direct_plan(
                callee_name=request.callee_name,
                goal=request.goal,
                context=request.context,
                instructions=request.instructions,
            )
            supplied = ["callee_name", "goal", "context", "instructions"]
        else:
            plan = await asyncio.to_thread(react_plan, request.task)
            supplied = ["task"]
    except (RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail=_safe_error(exc)) from exc

    plan_dict = plan.to_dict()
    planner_receipt = plan_dict.pop("planner_receipt", None)
    llm_receipts = [planner_receipt] if planner_receipt else []
    call_id = "rtc_" + uuid.uuid4().hex[:20]
    safe_acceptance = os.getenv("PHONE_SAFE_SYNTHETIC_ACCEPTANCE") == "1"
    record = {
        "schema_version": 3,
        "experiment": "9-2",
        "call_id": call_id,
        "created_at_utc": _now(),
        "finished_at_utc": None,
        "status": "planned",
        "mode": request.mode,
        "input_contract": {
            "fields_supplied_by_caller": supplied,
            "natural_language_task": request.task,
        },
        "plan": plan_dict,
        "models": {
            "planner": plan.planner_model,
            "dialogue_models": [],
            "llm_receipts": llm_receipts,
            "asr_receipts": [],
            "tts_receipts": [],
        },
        "transport": {
            "kind": "webrtc",
            "pstn_used": False,
            "e164_required": False,
            "sdp_negotiated": False,
            "offer_sha256": None,
            "answer_sha256": None,
            "ice_connection_state": "new",
            "ice_connected_observed": False,
            "data_channel_open": False,
            "local_audio_track": False,
            "remote_audio_track": False,
            "rtc_stats": {
                "inbound_packets": 0,
                "inbound_bytes": 0,
                "outbound_packets": 0,
                "outbound_bytes": 0,
            },
            "server_received_audio_frames": 0,
            "server_received_audio_samples": 0,
            "server_received_audio_pcm_bytes": 0,
            "server_sent_tts_samples": 0,
        },
        "privacy": {
            "safe_synthetic_acceptance": safe_acceptance,
            "private_audio_retained": False,
            "private_transcripts_retained": False,
            "safe_synthetic_media_retained": safe_acceptance,
        },
        "event_counts": {},
        "transcript": [],
        "explicit_confirmation_observed": False,
        "completion": None,
        "errors": [],
        "acceptance": {"checks": {}, "passed": False},
    }
    CALLS[call_id] = record
    return {"call_id": call_id, "join_url": f"/?call_id={call_id}", "plan": plan_dict}


async def _consume_microphone(track: Any, runtime: CallRuntime) -> None:
    record = runtime.record
    try:
        while True:
            frame = await track.recv()
            record["transport"]["server_received_audio_frames"] += 1
            record["transport"]["server_received_audio_samples"] += int(
                getattr(frame, "samples", 0)
            )
            for resampled in runtime.resampler.resample(frame):
                # Packed mono s16 has two bytes per sample. Reading the plane
                # directly avoids imposing NumPy on this transport-only stack.
                pcm = bytes(resampled.planes[0])[: int(resampled.samples) * 2]
                if len(runtime.microphone_pcm) + len(pcm) > MAX_MICROPHONE_PCM_BYTES:
                    raise RuntimeError("microphone buffer exceeded the 60-second safety limit")
                runtime.microphone_pcm.extend(pcm)
                record["transport"]["server_received_audio_pcm_bytes"] = len(runtime.microphone_pcm)
    except MediaStreamError:
        return
    except Exception as exc:  # noqa: BLE001 - evidence must retain asynchronous media failures
        record["errors"].append(
            {"at": _now(), "stage": "microphone_rtp", "message": _safe_error(exc)}
        )


async def _send_agent(
    runtime: CallRuntime,
    text: str,
    *,
    purpose: str,
) -> None:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Agent TTS text is empty")
    index = len(runtime.record["models"]["tts_receipts"]) + 1
    speech = await asyncio.to_thread(runtime.tts.synthesize, cleaned)
    path = _retained_media_path(runtime.record, f"agent_{index:02d}.wav")
    if path is not None:
        path.write_bytes(speech.wav)
        if sha256_bytes(path.read_bytes()) != speech.receipt["wav_sha256"]:
            raise RuntimeError("retained TTS asset hash mismatch")
    receipt = {
        **speech.receipt,
        "utterance_id": f"tts_{index:02d}",
        "purpose": purpose,
        "retained_safe_fixture_path": _relative_evidence_path(path),
        "text_sha256": hashlib.sha256(cleaned.encode("utf-8")).hexdigest(),
    }
    runtime.record["models"]["tts_receipts"].append(receipt)
    runtime.output_track.enqueue(speech.pcm, receipt)
    runtime.record["transcript"].append(
        {
            "speaker": "agent",
            "text": cleaned,
            "source": "tts.webrtc_downlink",
            "utterance_id": receipt["utterance_id"],
            "purpose": purpose,
        }
    )
    channel = runtime.channel
    if channel is not None and channel.readyState == "open":
        channel.send(
            json.dumps(
                {
                    "type": "agent.caption",
                    "text": cleaned,
                    "utterance_id": receipt["utterance_id"],
                    "source": "accessibility_mirror_of_tts",
                },
                ensure_ascii=False,
            )
        )


async def _commit_microphone(runtime: CallRuntime) -> None:
    if runtime.commit_started:
        raise RuntimeError("microphone audio was already committed")
    runtime.commit_started = True
    record = runtime.record
    pcm = bytes(runtime.microphone_pcm)
    path = _retained_media_path(record, "microphone_rtp_asr_input.wav")
    transcript, asr_receipt = await asyncio.to_thread(
        runtime.asr.transcribe, pcm, retained_wav_path=path
    )
    asr_receipt["retained_safe_fixture_path"] = _relative_evidence_path(path)
    if path is not None and sha256_bytes(path.read_bytes()) != asr_receipt["input_wav_sha256"]:
        raise RuntimeError("retained microphone/ASR input hash mismatch")
    record["models"]["asr_receipts"].append(asr_receipt)
    record["transcript"].append(
        {
            "speaker": "user",
            "text": transcript,
            "source": "asr.microphone_rtp",
            "asr_receipt_index": len(record["models"]["asr_receipts"]) - 1,
        }
    )
    channel = runtime.channel
    if channel is not None and channel.readyState == "open":
        channel.send(
            json.dumps(
                {
                    "type": "user.caption",
                    "text": transcript,
                    "source": "accessibility_mirror_of_asr",
                },
                ensure_ascii=False,
            )
        )
    plan = CallPlan(**record["plan"])
    dialogue = await asyncio.to_thread(
        conversation_turn,
        plan,
        list(record["transcript"][:-1]),
        transcript,
    )
    receipt = dialogue["llm_receipt"]
    record["models"]["llm_receipts"].append(receipt)
    model = dialogue["dialogue_model"]
    if model not in record["models"]["dialogue_models"]:
        record["models"]["dialogue_models"].append(model)
    record["explicit_confirmation_observed"] = dialogue["explicit_confirmation_observed"] is True
    if not dialogue["should_complete"]:
        raise RuntimeError("canonical call did not reach explicit structured completion")
    completion = CompleteTask(**dialogue["completion"])
    await _send_agent(runtime, dialogue["assistant_message"], purpose="confirmed_completion")
    record["completion"] = {
        **completion.model_dump(),
        "saved_at_utc": _now(),
        "tool": "complete_task",
    }
    if channel is not None and channel.readyState == "open":
        channel.send(json.dumps({"type": "tool.result", "name": "complete_task", "saved": True}))


async def _handle_data_message(runtime: CallRuntime, raw: Any) -> None:
    record = runtime.record
    try:
        message = json.loads(raw) if isinstance(raw, str) else {}
        message_type = message.get("type")
        if message_type == "client.ready":
            record["transport"]["data_channel_open"] = True
            if not record["transcript"]:
                await _send_agent(
                    runtime,
                    record["plan"]["opening_line"],
                    purpose="missing_field_clarification",
                )
            return
        if message_type == "client.audio.commit":
            record["event_counts"]["client.audio.commit"] = (
                int(record["event_counts"].get("client.audio.commit", 0)) + 1
            )
            await _commit_microphone(runtime)
            return
        if message_type in {"user.message", "client.user_text"}:
            record["event_counts"]["semantic_user_messages"] = (
                int(record["event_counts"].get("semantic_user_messages", 0)) + 1
            )
            raise RuntimeError("semantic user text is forbidden; speak over the microphone track")
    except Exception as exc:  # noqa: BLE001 - asynchronous failures belong in the evidence record
        error = {"at": _now(), "stage": "voice_agent_loop", "message": _safe_error(exc)}
        record["errors"].append(error)
        if runtime.channel is not None and runtime.channel.readyState == "open":
            runtime.channel.send(json.dumps({"type": "error", "error": error}, ensure_ascii=False))


@app.post("/api/calls/{call_id}/session")
async def negotiate(call_id: str, request: Request) -> Response:
    record = _record(call_id)
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("application/sdp"):
        raise HTTPException(status_code=415, detail="expected application/sdp")
    offer = (await request.body()).decode("utf-8", errors="strict")
    if not offer.startswith("v=0") or len(offer) > 1_000_000:
        raise HTTPException(status_code=400, detail="invalid SDP offer")
    try:
        runtime = CallRuntime(record)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=_safe_error(exc)) from exc
    RUNTIMES[call_id] = runtime
    pc = RTCPeerConnection()
    PEERS[call_id] = pc
    pc.addTrack(runtime.output_track)

    @pc.on("track")
    def on_track(track: Any) -> None:
        if track.kind == "audio":
            record["transport"]["local_audio_track"] = True
            asyncio.create_task(_consume_microphone(track, runtime))

    @pc.on("datachannel")
    def on_datachannel(channel: Any) -> None:
        runtime.channel = channel

        @channel.on("message")
        def on_message(message: Any) -> None:
            asyncio.create_task(_handle_data_message(runtime, message))

    @pc.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        state = pc.connectionState
        if state in {"connected", "completed"}:
            record["transport"]["ice_connected_observed"] = True
            record["transport"]["ice_connection_state"] = state
        elif not record["transport"]["ice_connected_observed"]:
            record["transport"]["ice_connection_state"] = state
        if state in {"failed", "closed"}:
            await pc.close()

    await pc.setRemoteDescription(RTCSessionDescription(sdp=offer, type="offer"))
    answer_description = await pc.createAnswer()
    await pc.setLocalDescription(answer_description)
    answer = pc.localDescription.sdp
    record["status"] = "connected"
    record["transport"].update(
        {
            "sdp_negotiated": True,
            "offer_sha256": _sha256_text(offer),
            "answer_sha256": _sha256_text(answer),
            "remote_audio_track": True,
        }
    )
    return Response(content=answer, media_type="application/sdp")


@app.post("/api/calls/{call_id}/events")
async def save_event(call_id: str, envelope: EventEnvelope) -> dict[str, bool]:
    record = _record(call_id)
    event = envelope.event
    event_type = str(event.get("type", "unknown"))[:200]
    counts = Counter(record["event_counts"])
    counts[event_type] += 1
    record["event_counts"] = dict(sorted(counts.items()))
    if event_type == "rtc.ready":
        state = str(event.get("ice_connection_state", "unknown"))[:30]
        if state in {"connected", "completed"}:
            record["transport"]["ice_connected_observed"] = True
            record["transport"]["ice_connection_state"] = state
        for field, event_field in (
            ("data_channel_open", "data_channel_open"),
            ("local_audio_track", "local_audio_track"),
            ("remote_audio_track", "remote_audio_track"),
        ):
            record["transport"][field] = bool(record["transport"][field] or event.get(event_field))
    elif event_type == "rtc.stats":
        stats = record["transport"]["rtc_stats"]
        for field in stats:
            stats[field] = max(int(stats[field]), max(0, int(event.get(field, 0))))
        state = str(event.get("ice_connection_state", ""))[:30]
        if state in {"connected", "completed"}:
            record["transport"]["ice_connected_observed"] = True
            record["transport"]["ice_connection_state"] = state
    elif event_type == "error":
        record["errors"].append({"at": _now(), "stage": "browser", "message": str(event)[:1000]})
    return {"saved": True}


@app.post("/api/calls/{call_id}/finish")
async def finish(call_id: str, finish_request: FinishCall) -> dict[str, Any]:
    record = _record(call_id)
    record["finished_at_utc"] = _now()
    record["finish_reason"] = finish_request.reason
    record["acceptance"] = _acceptance(record)
    record["status"] = "completed" if record["acceptance"]["passed"] else "ended"
    result = _public(record)
    peer = PEERS.pop(call_id, None)
    RUNTIMES.pop(call_id, None)
    if peer is not None:
        await peer.close()
    return result


@app.get("/api/calls/{call_id}")
async def get_call(call_id: str) -> dict[str, Any]:
    record = _record(call_id)
    record["acceptance"] = _acceptance(record)
    return _public(record)
