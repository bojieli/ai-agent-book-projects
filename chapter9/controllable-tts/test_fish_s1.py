import json

import pytest

from markup import parse
from voice_library import EMOTIONS, SPEEDS, STYLES, load_voice_library


def test_native_s1_nonverbal_events_not_onomatopoeia():
    segments = parse("[THINKING]好吧，[SIGH][LAUGH:small][BREATH]继续。")
    texts = [s["text"] for s in segments if s["type"] == "speech"]
    assert "(uncertain)嗯……" in texts
    assert "(sighing)" in texts
    assert "(chuckling)" in texts
    assert "(gasping)" in texts
    assert "哈哈，" not in texts and "唉——" not in texts


def test_library_requires_exact_cartesian_product(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"profiles": {}}))
    with pytest.raises(ValueError, match="24"):
        load_voice_library(manifest)


def test_dimensions_are_4_by_3_by_2():
    assert len(EMOTIONS) * len(SPEEDS) * len(STYLES) == 24
