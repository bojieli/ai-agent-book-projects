"""Duplex Interruption Manager for Real-Time Streaming Speech Systems.

Monitors real-time Voice Activity Detection (VAD) energy signals during active TTS audio playback,
enabling instant audio stream cancellation upon user barge-in, dialogue context truncation,
and re-planning trigger generation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
import numpy as np


@dataclass
class InterruptionEvent:
    """Event payload generated when a user barge-in interrupts active TTS playback."""
    timestamp: float
    barge_in_id: int
    energy_level: float
    vad_threshold: float
    truncated_turns: int
    reason: str
    replan_triggered: bool
    cancelled_audio_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert interruption event to dictionary representation."""
        return {
            "timestamp": self.timestamp,
            "barge_in_id": self.barge_in_id,
            "energy_level": self.energy_level,
            "vad_threshold": self.vad_threshold,
            "truncated_turns": self.truncated_turns,
            "reason": self.reason,
            "replan_triggered": self.replan_triggered,
            "cancelled_audio_bytes": self.cancelled_audio_bytes,
        }


@dataclass
class DialogueTurn:
    """Represents a turn in the dialogue context."""
    role: str
    content: str
    status: str = "completed"  # "completed", "interrupted", "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)


class DuplexInterruptionManager:
    """Manages real-time interruption (barge-in) detection and handling for duplex speech systems.
    
    Monitors user audio input streams via VAD energy analysis while TTS audio is actively playing.
    If speech is detected during active TTS output, it instantly cancels playback, truncates
    the dialogue context to match what was actually delivered, and emits a re-planning trigger.
    """

    def __init__(
        self,
        vad_threshold: float = 0.02,
        consecutive_frames_required: int = 1,
        on_barge_in: Optional[Callable[[InterruptionEvent], None]] = None,
        on_replan: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        """Initialize the DuplexInterruptionManager.

        Args:
            vad_threshold: RMS energy threshold above which audio frame is treated as voice active.
            consecutive_frames_required: Number of consecutive active frames required to trigger barge-in.
            on_barge_in: Optional callback invoked when a barge-in event occurs.
            on_replan: Optional callback invoked when re-planning is triggered.
        """
        self.vad_threshold = float(vad_threshold)
        self.consecutive_frames_required = max(1, int(consecutive_frames_required))
        self.on_barge_in = on_barge_in
        self.on_replan = on_replan

        # Playback & state management
        self.is_playing: bool = False
        self._consecutive_active_frames: int = 0
        self.barge_in_count: int = 0
        self.dialogue_context: List[DialogueTurn] = []
        self.pending_audio_stream: List[bytes] = []
        self.last_interruption_event: Optional[InterruptionEvent] = None
        self.replan_triggers: List[Dict[str, Any]] = []

    def start_playback(self, initial_audio_stream: Optional[List[bytes]] = None) -> None:
        """Mark TTS playback as active and optionally register pending audio stream chunks."""
        self.is_playing = True
        self._consecutive_active_frames = 0
        if initial_audio_stream is not None:
            self.pending_audio_stream = list(initial_audio_stream)

    def stop_playback(self) -> None:
        """Mark TTS playback as inactive and clear pending audio stream."""
        self.is_playing = False
        self._consecutive_active_frames = 0
        self.pending_audio_stream.clear()

    def calculate_energy(
        self,
        audio_data: Union[np.ndarray, bytes, bytearray, memoryview, List[float], List[int]],
        sample_format: Optional[str] = None,
    ) -> float:
        """Calculate Root Mean Square (RMS) energy level of an audio chunk.

        Supports numpy arrays, raw bytes/bytearray/memoryview (16-bit PCM, uint8, or float32), or float/int lists.
        sample_format can be 'int16', 'uint8', 'float32', or None for auto detection.
        """
        if audio_data is None:
            return 0.0

        fmt = (sample_format or "").lower()
        if isinstance(audio_data, (bytes, bytearray, memoryview)):
            if len(audio_data) == 0:
                return 0.0
            if fmt in ("float32", "float"):
                arr = np.frombuffer(audio_data, dtype=np.float32)
            elif fmt in ("uint8", "u8"):
                arr = (np.frombuffer(audio_data, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
            elif fmt in ("int8", "i8"):
                arr = np.frombuffer(audio_data, dtype=np.int8).astype(np.float32) / 128.0
            elif fmt in ("int16", "i16"):
                arr = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                if len(audio_data) % 2 != 0:
                    arr = (np.frombuffer(audio_data, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
                else:
                    arr = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        elif isinstance(audio_data, (list, tuple)):
            if len(audio_data) == 0:
                return 0.0
            raw_arr = np.array(audio_data)
            if np.issubdtype(raw_arr.dtype, np.integer):
                if raw_arr.dtype == np.uint8 or fmt in ("uint8", "u8"):
                    arr = (raw_arr.astype(np.float32) - 128.0) / 128.0
                elif raw_arr.dtype == np.int8 or fmt in ("int8", "i8"):
                    arr = raw_arr.astype(np.float32) / 128.0
                elif raw_arr.dtype == np.int16 or fmt in ("int16", "i16"):
                    arr = raw_arr.astype(np.float32) / 32768.0
                else:
                    max_abs = float(np.max(np.abs(raw_arr))) if raw_arr.size > 0 else 0.0
                    if max_abs <= 128.0:
                        scale = 128.0
                    elif max_abs <= 32768.0:
                        scale = 32768.0
                    elif max_abs <= 2147483648.0:
                        scale = 2147483648.0
                    else:
                        scale = float(np.iinfo(raw_arr.dtype).max)
                    arr = raw_arr.astype(np.float32) / scale
            else:
                arr = raw_arr.astype(np.float32)
                # If values are in integer PCM range (>1.0), normalize to [-1, 1].
                # Use a fixed int16 scale rather than per-chunk max to preserve
                # relative volume across chunks.
                max_abs = float(np.max(np.abs(arr))) if arr.size > 0 else 0.0
                if max_abs > 1.0:
                    if max_abs <= 128.0:
                        arr = arr / 128.0
                    elif max_abs <= 32768.0:
                        arr = arr / 32768.0
                    else:
                        arr = arr / 2147483648.0
        elif isinstance(audio_data, np.ndarray):
            if audio_data.size == 0:
                return 0.0
            if np.issubdtype(audio_data.dtype, np.integer):
                if audio_data.dtype == np.uint8 or fmt in ("uint8", "u8"):
                    arr = (audio_data.astype(np.float32) - 128.0) / 128.0
                elif audio_data.dtype == np.int8 or fmt in ("int8", "i8"):
                    arr = audio_data.astype(np.float32) / 128.0
                elif audio_data.dtype == np.int16 or fmt in ("int16", "i16"):
                    arr = audio_data.astype(np.float32) / 32768.0
                else:
                    max_abs = float(np.max(np.abs(audio_data))) if audio_data.size > 0 else 0.0
                    if max_abs <= 128.0:
                        scale = 128.0
                    elif max_abs <= 32768.0:
                        scale = 32768.0
                    elif max_abs <= 2147483648.0:
                        scale = 2147483648.0
                    else:
                        scale = float(np.iinfo(audio_data.dtype).max)
                    arr = audio_data.astype(np.float32) / scale
            else:
                arr = audio_data.astype(np.float32)
                max_abs = float(np.max(np.abs(arr))) if arr.size > 0 else 0.0
                if max_abs > 1.0:
                    if max_abs <= 128.0:
                        arr = arr / 128.0
                    elif max_abs <= 32768.0:
                        arr = arr / 32768.0
                    else:
                        arr = arr / 2147483648.0
        else:
            return 0.0

        if arr.size == 0:
            return 0.0

        rms = float(np.sqrt(np.mean(arr ** 2) + 1e-12))
        return rms

    def is_voice_active(
        self,
        audio_data: Union[np.ndarray, bytes, bytearray, memoryview, List[float], List[int]],
        sample_format: Optional[str] = None,
    ) -> bool:
        """Check if incoming audio chunk exceeds the VAD energy threshold."""
        energy = self.calculate_energy(audio_data, sample_format=sample_format)
        return energy >= self.vad_threshold

    def process_audio_chunk(
        self,
        audio_data: Union[np.ndarray, bytes, bytearray, memoryview, List[float], List[int]],
        sample_rate: int = 16000,
        sample_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process real-time incoming audio chunk from user.

        Monitors VAD energy signal during active TTS audio playback.
        If VAD energy surpasses threshold while playing, triggers barge-in.

        Returns:
            Dict containing VAD analysis results, playback status, and interruption info.
        """
        energy = self.calculate_energy(audio_data, sample_format=sample_format)
        is_speech = energy >= self.vad_threshold

        if not self.is_playing:
            self._consecutive_active_frames = 0
            return {
                "barge_in": False,
                "is_speech": is_speech,
                "consecutive_frames": 0,
                "energy": energy,
                "vad_threshold": self.vad_threshold,
                "is_playing": False,
                "message": "TTS playback inactive; audio processed normally.",
            }

        if is_speech:
            self._consecutive_active_frames += 1
            if self._consecutive_active_frames >= self.consecutive_frames_required:
                current_consecutive = self._consecutive_active_frames
                # Trigger instant barge-in
                barge_in_result = self.handle_barge_in(
                    reason="user_barge_in_detected",
                    energy_level=energy,
                )
                barge_in_result["energy"] = energy
                barge_in_result["is_speech"] = True
                barge_in_result["consecutive_frames"] = current_consecutive
                barge_in_result["vad_threshold"] = self.vad_threshold
                barge_in_result["is_playing"] = False
                return barge_in_result
        else:
            self._consecutive_active_frames = 0

        return {
            "barge_in": False,
            "is_speech": is_speech,
            "consecutive_frames": self._consecutive_active_frames,
            "energy": energy,
            "vad_threshold": self.vad_threshold,
            "is_playing": True,
            "message": (
                "Voice activity detected; awaiting consecutive frames."
                if is_speech
                else "No voice activity detected during TTS playback."
            ),
        }

    def handle_barge_in(
        self,
        truncated_length: Optional[int] = None,
        reason: str = "user_barge_in",
        energy_level: float = 0.0,
    ) -> Dict[str, Any]:
        """Handle instant audio stream cancellation, dialogue context truncation, and re-planning.

        Entrypoint called upon barge-in detection or manual invocation.

        Returns:
            Dict containing complete interruption event outcome details.
        """
        # 1. Instant audio stream cancellation
        was_playing = self.is_playing
        cancelled_bytes = sum(len(b) for b in self.pending_audio_stream) if was_playing else 0

        if not was_playing:
            return {
                "status": "ignored",
                "barge_in": False,
                "playback_cancelled": False,
                "cancelled_audio_bytes": 0,
                "context_truncated": False,
                "truncated_turns_count": 0,
                "replan_triggered": False,
                "replan_payload": None,
                "barge_in_count": self.barge_in_count,
                "event": None,
            }

        self.stop_playback()
        self.barge_in_count += 1
        truncated_turns_count = 0
        if self.dialogue_context:
            last_turn = self.dialogue_context[-1]
            if last_turn.role in ("assistant", "system", "agent") and last_turn.status != "interrupted":
                last_turn.status = "interrupted"
                truncated_turns_count += 1
                if truncated_length is not None and truncated_length < len(last_turn.content):
                    last_turn.content = last_turn.content[:truncated_length] + " [interrupted...]"
                else:
                    last_turn.content = last_turn.content + " [interrupted]"

        # 3. Re-planning trigger generation
        replan_payload = {
            "trigger": "barge_in",
            "barge_in_id": self.barge_in_count,
            "timestamp": time.time(),
            "reason": reason,
            "dialogue_state": [
                {"role": t.role, "content": t.content, "status": t.status}
                for t in self.dialogue_context
            ],
        }
        self.replan_triggers.append(replan_payload)

        # Build interruption event
        event = InterruptionEvent(
            timestamp=time.time(),
            barge_in_id=self.barge_in_count,
            energy_level=energy_level,
            vad_threshold=self.vad_threshold,
            truncated_turns=truncated_turns_count,
            reason=reason,
            replan_triggered=True,
            cancelled_audio_bytes=cancelled_bytes,
        )
        self.last_interruption_event = event

        # Callbacks
        if self.on_barge_in is not None:
            self.on_barge_in(event)
        if self.on_replan is not None:
            self.on_replan(replan_payload)

        return {
            "status": "interrupted",
            "barge_in": True,
            "playback_cancelled": was_playing,
            "cancelled_audio_bytes": cancelled_bytes,
            "context_truncated": truncated_turns_count > 0,
            "truncated_turns_count": truncated_turns_count,
            "replan_triggered": True,
            "replan_payload": replan_payload,
            "barge_in_count": self.barge_in_count,
            "event": event.to_dict(),
        }

    def add_dialogue_turn(self, role: str, content: str, status: str = "completed") -> DialogueTurn:
        """Add a dialogue turn to the current context."""
        turn = DialogueTurn(role=role, content=content, status=status)
        self.dialogue_context.append(turn)
        return turn

    def get_dialogue_context(self) -> List[Dict[str, Any]]:
        """Return formatted dialogue context."""
        return [
            {"role": t.role, "content": t.content, "status": t.status, "metadata": t.metadata}
            for t in self.dialogue_context
        ]

    def reset(self) -> None:
        """Reset internal state, counters, and buffers."""
        self.stop_playback()
        self.barge_in_count = 0
        self.dialogue_context.clear()
        self.replan_triggers.clear()
        self.last_interruption_event = None
        self._consecutive_active_frames = 0
