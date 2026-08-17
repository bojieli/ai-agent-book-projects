"""Unit tests for chapter6/streaming-speech/interruption_manager.py (DuplexInterruptionManager)."""

import importlib.util
import os
import sys
from pathlib import Path
import pytest

pytest.importorskip("numpy")
import numpy as np

# Dynamic import for hypenated module path
_module_path = (
    Path(__file__).resolve().parent.parent
    / "chapter6"
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

def test_calculate_energy_low_amplitude_int_list():
    """Verify low-amplitude integer lists do not produce false high energy values."""
    manager = DuplexInterruptionManager(vad_threshold=0.02)
    quiet_int_list = [0, 1, -1, 0, 1, 0]
    energy = manager.calculate_energy(quiet_int_list)
    assert energy < 0.01

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
def test_calculate_energy_integer_normalization():
    """Verify integer arrays and lists are properly normalized to avoid false barge-in."""
    manager = DuplexInterruptionManager(vad_threshold=0.05)

    # int16 numpy array
    int16_speech = np.random.randint(-15000, 15000, 1600, dtype=np.int16)
    energy_int16 = manager.calculate_energy(int16_speech)
    assert energy_int16 < 1.0
    assert energy_int16 > 0.05

    # int list
    int_list_speech = int16_speech.tolist()
    energy_list = manager.calculate_energy(int_list_speech)
    assert energy_list < 1.0
    assert energy_list > 0.05


def test_process_audio_chunk_consecutive_frames_speech_flag():
    """Verify is_speech remains True when consecutive frames condition is pending."""
    manager = DuplexInterruptionManager(vad_threshold=0.02, consecutive_frames_required=2)
    manager.start_playback()

    speech_data = np.random.uniform(-0.4, 0.4, 800).astype(np.float32)
    result = manager.process_audio_chunk(speech_data)

    assert result["barge_in"] is False
    assert result["is_speech"] is True
    assert result["is_playing"] is True
    assert "awaiting consecutive frames" in result["message"]
def test_uint8_energy_normalization():
    """Verify uint8 PCM energy is normalized to [-1, 1)."""
    manager = DuplexInterruptionManager(vad_threshold=0.05)
    uint8_speech = np.random.randint(0, 255, 1600, dtype=np.uint8)
    energy = manager.calculate_energy(uint8_speech)
    assert energy > 0.05
    assert energy < 1.0


def test_float32_bytes_energy_calculation():
    """Verify float32 raw bytes energy calculation."""
    manager = DuplexInterruptionManager(vad_threshold=0.05)
    float32_speech = np.random.uniform(-0.5, 0.5, 400).astype(np.float32).tobytes()
    energy = manager.calculate_energy(float32_speech, sample_format="float32")
    assert energy > 0.05
    assert energy < 1.0


def test_repeated_barge_in_does_not_truncate_historical_turns():
    """Verify repeated barge-in does not pollute earlier completed turns."""
    manager = DuplexInterruptionManager()
    manager.add_dialogue_turn("assistant", "First turn completed", status="completed")
    manager.add_dialogue_turn("assistant", "Second turn playing", status="completed")

    manager.start_playback([b"audio"])
    manager.handle_barge_in()

    ctx = manager.get_dialogue_context()
    assert ctx[0]["status"] == "completed"
    assert "[interrupted]" not in ctx[0]["content"]
    assert ctx[1]["status"] == "interrupted"

    # Second barge-in without new turn should not affect turn 0
    manager.handle_barge_in()
    ctx = manager.get_dialogue_context()
    assert ctx[0]["status"] == "completed"
    assert "[interrupted]" not in ctx[0]["content"]
def test_bytearray_and_memoryview_energy():
    """Verify bytearray and memoryview inputs are handled cleanly in energy calculation."""
    manager = DuplexInterruptionManager()
    pcm_bytes = (np.sin(np.linspace(0, 440 * 2 * np.pi, 320)) * 16000).astype(np.int16).tobytes()

    energy_bytearray = manager.calculate_energy(bytearray(pcm_bytes))
    energy_memoryview = manager.calculate_energy(memoryview(pcm_bytes))

    assert energy_bytearray > 0.05
    assert energy_memoryview > 0.05


def test_consecutive_frames_and_is_speech_in_process_chunk():
    """Verify is_speech=True and consecutive_frames=N are returned prior to reaching barge-in threshold."""
    manager = DuplexInterruptionManager(vad_threshold=0.02, consecutive_frames_required=3)
    manager.start_playback([b"audio"])

    speech_pcm = (np.sin(np.linspace(0, 440 * 2 * np.pi, 320)) * 16000).astype(np.int16).tobytes()

    res1 = manager.process_audio_chunk(speech_pcm)
    assert res1["barge_in"] is False
    assert res1["is_speech"] is True
    assert res1["consecutive_frames"] == 1

    res2 = manager.process_audio_chunk(speech_pcm)
    assert res2["barge_in"] is False
    assert res2["is_speech"] is True
    assert res2["consecutive_frames"] == 2

    res3 = manager.process_audio_chunk(speech_pcm)
    assert res3["barge_in"] is True
    assert res3["is_speech"] is True
    assert res3["consecutive_frames"] == 3


def test_uint8_normalization_around_128():
    """Verify 8-bit unsigned audio is normalized around 128 correctly."""
    manager = DuplexInterruptionManager()
    # 128 is silence in uint8
    silence_uint8 = bytes([128] * 320)
    energy_silence = manager.calculate_energy(silence_uint8, sample_format="uint8")
    assert energy_silence < 0.01

    # Tone between 0 and 255
    tone_uint8 = bytes([128 + int(100 * np.sin(i / 10.0)) for i in range(320)])
    energy_tone = manager.calculate_energy(tone_uint8, sample_format="uint8")
    assert energy_tone > 0.1


def test_unknown_int_dtype_uses_value_range_scale():
    """Regression: unknown integer dtypes must use a standard scale based on value range, not chunk max, so relative volume is preserved."""
    manager = DuplexInterruptionManager()
    # Same int16-range values in different containers must produce same energy
    vals = [15000, -15000, 10000, -10000] * 80
    energy_int16 = manager.calculate_energy(np.array(vals, dtype=np.int16))
    energy_int32 = manager.calculate_energy(np.array(vals, dtype=np.int32))
    energy_list = manager.calculate_energy(vals)
    assert abs(energy_int16 - energy_int32) < 0.01, "int16 and int32 should match"
    assert abs(energy_int16 - energy_list) < 0.01, "int16 and list should match"

    # Quiet audio (small values) must have lower energy than loud audio (large values)
    # at the same scale tier
    quiet = np.array([100, -100, 50, -50] * 80, dtype=np.int32)
    loud = np.array([30000, -30000, 25000, -25000] * 80, dtype=np.int32)
    energy_quiet = manager.calculate_energy(quiet)
    energy_loud = manager.calculate_energy(loud)
    assert energy_quiet < energy_loud, f"Quiet ({energy_quiet}) should be < loud ({energy_loud})"


def test_float_audio_above_unity_uses_fixed_scale():
    """Regression: float arrays with values > 1.0 must use a fixed scale (32768), not chunk max, preserving relative volume."""
    manager = DuplexInterruptionManager()
    # Quiet float in int16 range (well below int16 max)
    quiet = [100.0, -100.0, 50.0, -50.0] * 80
    energy_quiet = manager.calculate_energy(quiet)

    # Loud float in int16 range (near int16 max)
    loud = [30000.0, -30000.0, 25000.0, -25000.0] * 80
    energy_loud = manager.calculate_energy(loud)

    # Both are in the same scale tier (<=32768), so relative volume is preserved
    assert energy_quiet < energy_loud, f"Quiet ({energy_quiet}) should be < loud ({energy_loud})"


def test_barge_in_when_not_playing_preserves_queued_audio():
    """Regression: barge-in while not playing must not drop queued pending audio."""
    manager = DuplexInterruptionManager()
    # Queue some audio but don't start playing
    manager.pending_audio_stream.append(b"\x00" * 1024)
    manager.is_playing = False

    result = manager.handle_barge_in(reason="test")
    assert result["status"] == "ignored"
    # Queued audio must still be present
    assert len(manager.pending_audio_stream) == 1
