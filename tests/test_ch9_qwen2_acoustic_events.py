import pytest
pytest.importorskip("librosa")
import importlib
import sys
from pathlib import Path

ch9_streaming = Path(__file__).resolve().parent.parent / "chapter9" / "streaming-speech"
if str(ch9_streaming) not in sys.path:
    sys.path.insert(0, str(ch9_streaming))

import qwen2_streaming  # noqa: E402
importlib.reload(qwen2_streaming)
from qwen2_streaming import parse_response  # noqa: E402


def test_parse_response_handles_string_acoustic_event():
    raw_json = '{"transcript": "Hello world", "acoustic_events": "laughter"}'
    transcript, events = parse_response(raw_json)
    assert transcript == "Hello world"
    assert events == ["<|laughter|>"]


def test_parse_response_handles_list_acoustic_events():
    raw_json = '{"transcript": "Hello", "acoustic_events": ["cough", "laughter", "laughter"]}'
    transcript, events = parse_response(raw_json)
    assert transcript == "Hello"
    assert events == ["<|cough|>", "<|laughter|>"]


def test_parse_response_handles_none_acoustic_events():
    raw_json = '{"transcript": "Silence", "acoustic_events": null}'
    transcript, events = parse_response(raw_json)
    assert transcript == "Silence"
    assert events == []


def test_parse_response_handles_non_iterable_acoustic_events():
    raw_json = '{"transcript": "Number event", "acoustic_events": 12345}'
    transcript, events = parse_response(raw_json)
    assert transcript == "Number event"
    assert events == []


def test_parse_response_handles_dict_acoustic_events():
    raw_json = '{"transcript": "Dict event", "acoustic_events": {"event": "cough"}}'
    transcript, events = parse_response(raw_json)
    assert transcript == "Dict event"
    assert events == []


def test_parse_response_combines_json_and_inline_tokens():
    raw_text = '{"transcript": "Hello <|noise|>", "acoustic_events": "laughter"}'
    transcript, events = parse_response(raw_text)
    assert transcript == "Hello <|noise|>"
    assert events == ["<|laughter|>", "<|noise|>"]
