import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "chapter9" / "streaming-speech"))

from whisper_baseline import energy_vad_events


def test_energy_vad_events_handles_empty_audio_array():
    """Empty or zero-length audio array must return an empty list of VAD events without crashing."""
    empty_audio = np.array([], dtype=np.float32)
    events = energy_vad_events(empty_audio, 16000)
    assert events == []
