"""回归测试：只含控制标记、没有任何语音正文的输入不应让 ffmpeg 空 concat 崩溃。

此前 `demo.py --text '[EMO:happy]'` 这类输入经 parse() 得到 0 个片段，
synthesize_segments 会拿空文件列表去跑 ffmpeg concat，
抛出晦涩的 CalledProcessError；现在应直接给出清晰的 SystemExit。
"""

import sys
from types import ModuleType

import pytest

try:
    import openai  # noqa: F401
except ImportError:
    sys.modules["openai"] = ModuleType("openai")
    sys.modules["openai"].OpenAI = object

from markup import parse
from tts import synthesize_segments


def test_marker_only_text_parses_to_zero_segments():
    assert parse("[EMO:happy]") == []


def test_empty_segments_raise_clear_system_exit(tmp_path):
    with pytest.raises(SystemExit) as excinfo:
        synthesize_segments([], str(tmp_path / "out.mp3"), str(tmp_path / "work"))
    assert "没有可合成的语音片段" in str(excinfo.value)


def test_normal_text_still_parses_to_speech_segment():
    segs = parse("[EMO:happy]太好了！")
    assert len(segs) == 1
    assert segs[0]["type"] == "speech"
    assert segs[0]["text"] == "太好了！"
    assert segs[0]["emotion"] == "happy"
