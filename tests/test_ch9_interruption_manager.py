"""Unit tests for chapter9/streaming-speech/interruption_manager.py (DuplexInterruptionManager)."""

import importlib.util
import os
import sys
from pathlib import Path
import numpy as np
import pytest

# Dynamic import for hypenated module path
_module_path = (
    Path(__file__).resolve().parent.parent
    / "chapter9"
    / "streaming-speech"
    / "interruption_manager.py"
)
_spec = importlib.util.spec_from_file_location("interruption_manager", _module_path)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["interruption_manager"] = _mod
_spec.loader.exec_module(_mod)

DuplexInterruptionManager = _mod.DuplexInterruptionManager
InterruptionEvent = _mod.InterruptionEvent
DialogueTurn = _mod.DialogueTurn


def test_calculate_energy_silence_vs_speech():
    """Verify calculate_energy correctly distinguishes silence from speech across formats."""
    manager = DuplexInterruptionManager(vad_threshold=0.05)

    silence_array = np.zeros(1600, dtype=np.float32)
    assert manager.calculate_energy(silence_array) < 0.01

    speech_array = np.random.uniform(-0.5, 0.5, 1600).astype(np.float32)
    assert manager.calculate_energy(speech_array) > 0.05

    silence_bytes = (np.zeros(320, dtype=np.int16)).tobytes()
    assert manager.calculate_energy(silence_bytes) < 0.01

    speech_bytes = (np.random.randint(-10000, 10000, 320, dtype=np.int16)).tobytes()
    assert manager.calculate_energy(speech_bytes) > 0.05


def test_process_audio_chunk_inactive_playback():
    """Verify process_audio_chunk does not trigger barge-in when TTS playback is inactive."""
    manager = DuplexInterruptionManager(vad_threshold=0.02)
    manager.stop_playback()

    speech_data = np.random.uniform(-0.4, 0.4, 800).astype(np.float32)
    result = manager.process_audio_chunk(speech_data)

    assert result["barge_in"] is False
    assert result["is_playing"] is False
    assert manager.barge_in_count == 0


def test_process_audio_chunk_barge_in_active_playback():
    """Verify process_audio_chunk triggers instant barge-in during active TTS playback."""
    manager = DuplexInterruptionManager(vad_threshold=0.02)
    manager.start_playback(initial_audio_stream=[b"chunk1", b"chunk2", b"chunk3"])

    manager.add_dialogue_turn("user", "What is the weather today?")
    manager.add_dialogue_turn("assistant", "The weather in Seattle is sunny and 72 degrees.")

    assert manager.is_playing is True
    speech_data = np.random.uniform(-0.5, 0.5, 1600).astype(np.float32)

    result = manager.process_audio_chunk(speech_data)

    assert result["barge_in"] is True
    assert result["status"] == "interrupted"
    assert result["playback_cancelled"] is True
    assert manager.is_playing is False
    assert len(manager.pending_audio_stream) == 0
    assert manager.barge_in_count == 1

    # Verify context truncation
    context = manager.get_dialogue_context()
    assistant_turn = [t for t in context if t["role"] == "assistant"][0]
    assert assistant_turn["status"] == "interrupted"
    assert "[interrupted]" in assistant_turn["content"]

    # Verify re-planning trigger
    assert len(manager.replan_triggers) == 1
    assert manager.replan_triggers[0]["trigger"] == "barge_in"


def test_handle_barge_in_entrypoint():
    """Verify direct invocation of handle_barge_in entrypoint."""
    barge_in_events = []
    replan_events = []

    def on_barge_in(evt):
        barge_in_events.append(evt)

    def on_replan(payload):
        replan_events.append(payload)

    manager = DuplexInterruptionManager(
        vad_threshold=0.02,
        on_barge_in=on_barge_in,
        on_replan=on_replan,
    )
    manager.start_playback(initial_audio_stream=[b"stream1", b"stream2"])
    manager.add_dialogue_turn("assistant", "Playing long audio response...")

    res = manager.handle_barge_in(reason="manual_button_click")

    assert res["status"] == "interrupted"
    assert res["replan_triggered"] is True
    assert manager.is_playing is False
    assert len(barge_in_events) == 1
    assert len(replan_events) == 1
    assert barge_in_events[0].reason == "manual_button_click"


def test_manager_reset():
    """Verify reset restores initial clean state."""
    manager = DuplexInterruptionManager()
    manager.start_playback([b"test"])
    manager.add_dialogue_turn("user", "Hello")
    manager.handle_barge_in()

    assert manager.barge_in_count == 1
    assert len(manager.dialogue_context) == 1

    manager.reset()

    assert manager.is_playing is False
    assert manager.barge_in_count == 0
    assert len(manager.dialogue_context) == 0
    assert len(manager.replan_triggers) == 0
    assert manager.last_interruption_event is None
