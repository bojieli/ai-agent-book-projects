import numpy as np

from qwen2_streaming import parse_response
from whisper_baseline import energy_vad_endpoints, energy_vad_events


def test_qwen_json_and_native_event_token_parsing():
    transcript, events = parse_response('{"transcript":"你好","acoustic_events":["noise", "<|laughter|>"]}')
    assert transcript == "你好"
    assert events == ["<|noise|>", "<|laughter|>"]


def test_600ms_vad_splits_a_long_pause():
    sr = 1000
    audio = np.concatenate([np.ones(sr), np.zeros(700), np.ones(sr)]) * 0.1
    endpoints = energy_vad_endpoints(audio, sr, silence_ms=600)
    assert len(endpoints) == 2
    assert 900 <= endpoints[0] <= 1100


def test_vad_separates_acoustic_endpoint_from_600ms_decision():
    sr = 1000
    audio = np.concatenate([np.ones(sr), np.zeros(700), np.ones(sr)]) * 0.1
    event = energy_vad_events(audio, sr, silence_ms=600)[0]
    assert 900 <= event.speech_endpoint <= 1100
    assert 590 <= event.decision - event.speech_endpoint <= 610
