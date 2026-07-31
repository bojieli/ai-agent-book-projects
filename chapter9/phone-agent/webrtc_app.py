"""Local browser and aiortc media peer for Experiment 9-2."""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import os
import uuid
from array import array
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from agent import CallPlan, conversation_turn, direct_plan, react_plan
from aiortc import AudioStreamTrack, RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamError
from av import AudioFrame
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
load_dotenv(HERE / ".env")
CALLS: dict[str, dict[str, Any]] = {}
PEERS: dict[str, RTCPeerConnection] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


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
    appointment_time: str = Field(default="", max_length=300)
    confirmation_number: str = Field(default="", max_length=300)
    notes: str = Field(default="", max_length=2000)


class FinishCall(BaseModel):
    reason: str = Field(default="user_hangup", max_length=200)


app = FastAPI(title="Experiment 9-2 WebRTC Call Agent", version="2.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def _record(call_id: str) -> dict[str, Any]:
    record = CALLS.get(call_id)
    if record is None:
        raise HTTPException(status_code=404, detail="unknown call")
    return record


def _public(record: dict[str, Any]) -> dict[str, Any]:
    # Round-trip through JSON so API clients cannot mutate the in-memory state.
    return json.loads(json.dumps(record, ensure_ascii=False))


def _acceptance(record: dict[str, Any]) -> dict[str, Any]:
    transport = record["transport"]
    stats = transport["rtc_stats"]
    transcript = record["transcript"]
    checks = {
        "sdp_offer_answer_negotiated": bool(transport["sdp_negotiated"]),
        "ice_connected": bool(transport["ice_connected_observed"]),
        "data_channel_open": bool(transport["data_channel_open"]),
        "local_microphone_track": bool(transport["local_audio_track"]),
        "remote_audio_track": bool(transport["remote_audio_track"]),
        "outbound_audio_rtp": int(stats["outbound_packets"]) > 0 and int(stats["outbound_bytes"]) > 0,
        "inbound_audio_rtp": int(stats["inbound_packets"]) > 0 and int(stats["inbound_bytes"]) > 0,
        "server_consumed_microphone_audio": int(transport["server_received_audio_frames"]) > 0,
        "user_turn_recorded": any(turn["speaker"] == "user" and turn["text"] for turn in transcript),
        "agent_turn_recorded": any(turn["speaker"] == "agent" and turn["text"] for turn in transcript),
        "critical_fields_extracted": bool(record["completion"]),
    }
    return {"checks": checks, "passed": all(checks.values()) and not record["errors"]}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "experiment": "9-2",
        "model_provider_present": bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")),
    }


@app.post("/api/calls")
async def create_call(request: CreateCall) -> dict[str, Any]:
    try:
        plan: CallPlan
        if request.mode == "direct":
            plan = direct_plan(
                callee_name=request.callee_name,
                goal=request.goal,
                context=request.context,
                instructions=request.instructions,
            )
            supplied = ["callee_name", "goal", "context", "instructions"]
        else:
            plan = react_plan(request.task)
            supplied = ["task"]
    except (RuntimeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    call_id = "rtc_" + uuid.uuid4().hex[:20]
    record = {
        "schema_version": 2,
        "experiment": "9-2",
        "call_id": call_id,
        "created_at_utc": _now(),
        "finished_at_utc": None,
        "status": "planned",
        "mode": request.mode,
        "input_contract": {"fields_supplied_by_caller": supplied, "natural_language_task": request.task},
        "plan": plan.to_dict(),
        "models": {
            "planner": plan.planner_model,
            "dialogue_models": [],
            "speech_renderer": "browser-speechSynthesis",
        },
        "transport": {
            "kind": "webrtc",
            "pstn_used": False,
            "e164_required": False,
            "sdp_negotiated": False,
            "offer_sha256": None,
            "answer_sha256": None,
            "provider_session_id": None,
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
        },
        "event_counts": {},
        "transcript": [],
        "completion": None,
        "errors": [],
        "acceptance": {"checks": {}, "passed": False},
    }
    CALLS[call_id] = record
    return {"call_id": call_id, "join_url": f"/?call_id={call_id}", "plan": plan.to_dict()}


class ConnectionAudioTrack(AudioStreamTrack):
    """A real outbound RTP audio track with a short, quiet connection tone."""

    async def recv(self) -> AudioFrame:
        frame = await super().recv()
        # AudioStreamTrack produces 20 ms, 8 kHz mono silence. Add a 440 Hz cue
        # for the first 160 ms of each four-second interval; the remaining RTP
        # stays silent so browser-rendered speech is easy to hear.
        samples = frame.samples
        start = int(frame.pts or 0)
        values = array("h")
        for offset in range(samples):
            position = (start + offset) % (frame.sample_rate * 4)
            amplitude = 700 if position < int(frame.sample_rate * 0.16) else 0
            values.append(int(amplitude * math.sin(2 * math.pi * 440 * (start + offset) / frame.sample_rate)))
        frame.planes[0].update(values.tobytes())
        return frame


async def _consume_microphone(track: Any, record: dict[str, Any]) -> None:
    try:
        while True:
            frame = await track.recv()
            record["transport"]["server_received_audio_frames"] += 1
            record["transport"]["server_received_audio_samples"] += int(getattr(frame, "samples", 0))
    except MediaStreamError:
        # Track closure is the normal hang-up path. Browser/server RTP counters
        # remain the authoritative acceptance evidence.
        return


def _send_agent(channel: Any, record: dict[str, Any], text: str) -> None:
    text = text.strip()
    if not text or channel.readyState != "open":
        return
    record["transcript"].append({"speaker": "agent", "text": text, "source": "webrtc.data_channel"})
    channel.send(json.dumps({"type": "agent.message", "text": text}, ensure_ascii=False))


async def _handle_data_message(channel: Any, record: dict[str, Any], raw: Any) -> None:
    try:
        message = json.loads(raw) if isinstance(raw, str) else {}
    except json.JSONDecodeError:
        return
    if message.get("type") == "client.ready":
        record["transport"]["data_channel_open"] = True
        if not any(turn["speaker"] == "agent" for turn in record["transcript"]):
            plan = CallPlan(**record["plan"])
            _send_agent(channel, record, plan.opening_line)
        return
    if message.get("type") != "user.message":
        return
    text = str(message.get("text", "")).strip()[:4000]
    if not text:
        return
    record["event_counts"]["data_channel.user.message"] = (
        int(record["event_counts"].get("data_channel.user.message", 0)) + 1
    )
    record["transcript"].append({"speaker": "user", "text": text, "source": "webrtc.data_channel"})
    plan = CallPlan(**record["plan"])
    result = await asyncio.to_thread(conversation_turn, plan, list(record["transcript"][:-1]), text)
    model = str(result.get("dialogue_model", "unknown"))
    if model not in record["models"]["dialogue_models"]:
        record["models"]["dialogue_models"].append(model)
    if result.get("should_complete") and record["completion"] is None:
        try:
            completion = CompleteTask(**(result.get("completion") or {}))
            record["completion"] = {**completion.model_dump(), "saved_at_utc": _now()}
            channel.send(
                json.dumps({"type": "tool.result", "name": "complete_task", "value": record["completion"]})
            )
        except ValueError:
            pass
    _send_agent(channel, record, str(result.get("assistant_message", "")))


@app.post("/api/calls/{call_id}/session")
async def negotiate(call_id: str, request: Request) -> Response:
    record = _record(call_id)
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("application/sdp"):
        raise HTTPException(status_code=415, detail="expected application/sdp")
    offer = (await request.body()).decode("utf-8", errors="strict")
    if not offer.startswith("v=0") or len(offer) > 1_000_000:
        raise HTTPException(status_code=400, detail="invalid SDP offer")

    pc = RTCPeerConnection()
    PEERS[call_id] = pc
    pc.addTrack(ConnectionAudioTrack())

    @pc.on("track")
    def on_track(track: Any) -> None:
        if track.kind == "audio":
            record["transport"]["local_audio_track"] = True
            asyncio.create_task(_consume_microphone(track, record))

    @pc.on("datachannel")
    def on_datachannel(channel: Any) -> None:
        @channel.on("message")
        def on_message(message: Any) -> None:
            asyncio.create_task(_handle_data_message(channel, record, message))

    @pc.on("connectionstatechange")
    async def on_connectionstatechange() -> None:
        if pc.connectionState in {"connected", "completed"}:
            record["transport"]["ice_connected_observed"] = True
            record["transport"]["ice_connection_state"] = pc.connectionState
        elif not record["transport"]["ice_connected_observed"]:
            record["transport"]["ice_connection_state"] = pc.connectionState
        if pc.connectionState in {"failed", "closed"}:
            await pc.close()

    await pc.setRemoteDescription(RTCSessionDescription(sdp=offer, type="offer"))
    answer_description = await pc.createAnswer()
    await pc.setLocalDescription(answer_description)
    answer = pc.localDescription.sdp
    record["status"] = "connected"
    record["transport"].update(
        {
            "sdp_negotiated": True,
            "offer_sha256": _sha256(offer),
            "answer_sha256": _sha256(answer),
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
        elif not record["transport"]["ice_connected_observed"]:
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
    elif event_type == "session.created":
        session = event.get("session") or {}
        record["transport"]["provider_session_id"] = str(session.get("id", ""))[:200] or None
    elif event_type in {
        "response.output_audio_transcript.done",
        "response.audio_transcript.done",
    }:
        text = str(event.get("transcript", "")).strip()
        if text:
            record["transcript"].append({"speaker": "agent", "text": text, "source": event_type})
    elif event_type == "conversation.item.input_audio_transcription.completed":
        text = str(event.get("transcript", "")).strip()
        if text:
            record["transcript"].append({"speaker": "user", "text": text, "source": event_type})
    elif event_type == "client.user_text":
        text = str(event.get("text", "")).strip()[:4000]
        if text:
            record["transcript"].append({"speaker": "user", "text": text, "source": event_type})
    elif event_type == "error":
        detail = event.get("error") or {}
        record["errors"].append(
            {
                "at": _now(),
                "type": str(detail.get("type", "realtime_error"))[:100],
                "code": str(detail.get("code", ""))[:100],
                "message": str(detail.get("message", ""))[:1000],
            }
        )
    return {"saved": True}


@app.post("/api/calls/{call_id}/complete")
async def complete(call_id: str, completion: CompleteTask) -> dict[str, Any]:
    record = _record(call_id)
    if record["completion"] is None:
        record["completion"] = {**completion.model_dump(), "saved_at_utc": _now()}
    return {"saved": True, "completion": record["completion"]}


@app.post("/api/calls/{call_id}/finish")
async def finish(call_id: str, finish_request: FinishCall) -> dict[str, Any]:
    record = _record(call_id)
    record["finished_at_utc"] = _now()
    record["finish_reason"] = finish_request.reason
    record["acceptance"] = _acceptance(record)
    record["status"] = "completed" if record["acceptance"]["passed"] else "ended"
    result = _public(record)
    peer = PEERS.pop(call_id, None)
    if peer is not None:
        await peer.close()
    return result


@app.get("/api/calls/{call_id}")
async def get_call(call_id: str) -> dict[str, Any]:
    record = _record(call_id)
    record["acceptance"] = _acceptance(record)
    return _public(record)
