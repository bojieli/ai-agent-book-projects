import pytest
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
TTS_DIR = HERE / "chapter6" / "tts-quality-eval"
if str(TTS_DIR) not in sys.path:
    sys.path.insert(0, str(TTS_DIR))

sys.modules.pop("config", None)

import pipeline  # noqa: E402


def test_char_error_rate_empty_reference_with_hypothesis():
    res = pipeline.char_error_rate("!!!", "hello")
    assert res.accuracy == 0.0
    assert res.edits == 5
    assert res.cer == 5.0
    assert res.ref_len == 0

    res_empty = pipeline.char_error_rate("", "abc")
    assert res_empty.accuracy == 0.0
    assert res_empty.edits == 3
    assert res_empty.cer == 3.0
    assert res_empty.ref_len == 0


def test_char_error_rate_both_empty():
    res = pipeline.char_error_rate("!!!", "???")
    assert res.accuracy == 1.0
    assert res.edits == 0
    assert res.cer == 0.0
    assert res.ref_len == 0

    res_empty = pipeline.char_error_rate("", "")
    assert res_empty.accuracy == 1.0
    assert res_empty.edits == 0
    assert res_empty.cer == 0.0
    assert res_empty.ref_len == 0


def test_char_error_rate_normal_and_partial_match():
    res_exact = pipeline.char_error_rate("hello", "hello")
    assert res_exact.accuracy == 1.0
    assert res_exact.edits == 0
    assert res_exact.cer == 0.0
    assert res_exact.ref_len == 5

    res_deleted = pipeline.char_error_rate("hello", "")
    assert res_deleted.accuracy == 0.0
    assert res_deleted.edits == 5
    assert res_deleted.cer == 1.0
    assert res_deleted.ref_len == 5
