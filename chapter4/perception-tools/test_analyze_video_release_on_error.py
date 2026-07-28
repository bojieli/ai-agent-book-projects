"""Regression test: analyze_video_ai must release the VideoCapture even when a
per-frame Vision API call raises mid-loop.

The capture was previously released only on the success path, so a failing
Vision call (network / rate-limit / auth) leaked the native decoder/file handle
until GC. Release now happens in a finally.
"""
import asyncio
import json
import os
import sys
import types
from pathlib import Path

import cv2
import numpy as np
import pytest

SRC = os.path.join(os.path.dirname(__file__), "src")


class _TextContent:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def media_processing_tools(monkeypatch):
    """Import the chapter module with its optional runtime deps stubbed only for
    the duration of the test. monkeypatch restores sys.modules / sys.path
    afterwards, so we never permanently overwrite a real `mcp` / `dotenv` (or
    leave a partial stub in the global cache for other tests to pick up)."""
    monkeypatch.syspath_prepend(SRC)
    monkeypatch.setitem(
        sys.modules, "dotenv", types.SimpleNamespace(load_dotenv=lambda: None)
    )
    mcp = types.ModuleType("mcp")
    mcp_types = types.ModuleType("mcp.types")
    mcp_types.TextContent = _TextContent
    monkeypatch.setitem(sys.modules, "mcp", mcp)
    monkeypatch.setitem(sys.modules, "mcp.types", mcp_types)
    # Force a fresh import under the stubs even if another test already imported
    # the module; monkeypatch restores the original entry on teardown.
    monkeypatch.delitem(sys.modules, "media_processing_tools", raising=False)
    import media_processing_tools

    return media_processing_tools


class _FakeCapture:
    """Minimal VideoCapture stand-in that yields a few frames and records
    whether release() was called."""

    def __init__(self):
        self.released = False
        self._frames = 3
        self._i = 0

    def get(self, prop):
        if prop == cv2.CAP_PROP_FPS:
            return 10.0
        if prop == cv2.CAP_PROP_FRAME_COUNT:
            return float(self._frames)
        return 0.0

    def isOpened(self):
        return True

    def read(self):
        if self._i < self._frames:
            self._i += 1
            return True, np.zeros((48, 64, 3), dtype=np.uint8)
        return False, None

    def release(self):
        self.released = True


def test_analyze_video_ai_releases_capture_when_vision_call_raises(
    media_processing_tools, monkeypatch
):
    mpt = media_processing_tools
    fake = _FakeCapture()
    monkeypatch.setattr(mpt.cv2, "VideoCapture", lambda _path: fake)

    def _boom(**kwargs):
        raise RuntimeError("vision backend unavailable")

    client = types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=_boom))
    )
    monkeypatch.setattr(mpt, "_make_vision_client", lambda: (client, "fake-model"))
    # validate_file_path would reject a non-existent path before we reach the
    # capture; stub it to pass the path through unchanged.
    monkeypatch.setattr(mpt, "validate_file_path", lambda p: Path(p))

    result = asyncio.run(mpt.analyze_video_ai("some_clip.mp4", num_frames=2))
    payload = json.loads(result.text)

    assert payload["success"] is False
    assert fake.released is True
