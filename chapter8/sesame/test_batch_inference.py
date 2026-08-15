#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regression tests for batch_inference.py JSON input handling:

- Items missing the required "text" field must raise a clear ValueError
  (previously a bare KeyError: 'text' aborted the whole batch).
- An explicit JSON null "output" must fall back to the default filename
  (previously `output_path / None` raised TypeError mid-batch).

Heavy dependencies (torch, unsloth, transformers, peft, datasets, soundfile,
tqdm) are stubbed via sys.modules so the real module can be imported and
generate_speech_batch driven directly with a mock model/processor -- the bugs
lived in the per-item parsing, before any real model work.
"""

import contextlib
import os
import sys
import types
from unittest.mock import MagicMock

import pytest


def _stub(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module


_stub("torch",
      cuda=types.SimpleNamespace(is_available=lambda: False),
      no_grad=lambda: contextlib.nullcontext(),
      float32="float32")
_stub("soundfile", write=lambda *a, **k: None)
_stub("datasets", load_dataset=lambda *a, **k: None, Audio=lambda *a, **k: None)
_stub("unsloth", FastModel=object)
_stub("transformers", CsmForConditionalGeneration=object)
_stub("peft", PeftModel=object)
_stub("tqdm", tqdm=lambda it, desc=None: it)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import batch_inference  # noqa: E402


def _run_batch(texts, tmp_path):
    """Run generate_speech_batch over texts, returning the sf.write call paths."""
    written = []
    sys.modules["soundfile"].write = lambda path, *a, **k: written.append(str(path))
    batch_inference.generate_speech_batch(
        model=MagicMock(),
        processor=MagicMock(),
        texts=texts,
        output_dir=str(tmp_path),
    )
    return written


def test_missing_text_raises_clear_error(tmp_path):
    """Item without a 'text' key must fail loudly with a clear message."""
    with pytest.raises(ValueError, match="text"):
        _run_batch([{"speaker_id": 0, "output": "hello.wav"}], tmp_path)


def test_empty_text_raises_clear_error(tmp_path):
    """Item with empty 'text' must also fail loudly."""
    with pytest.raises(ValueError, match="text"):
        _run_batch([{"text": ""}], tmp_path)


def test_null_output_falls_back_to_default_filename(tmp_path):
    """Explicit JSON null 'output' must use the generated default filename."""
    written = _run_batch([{"text": "Hello world", "output": None}], tmp_path)
    assert len(written) == 1
    assert os.path.basename(written[0]).startswith("output_")
    assert written[0].endswith(".wav")


def test_valid_item_still_works(tmp_path):
    """A well-formed item still generates to its explicit output path."""
    written = _run_batch([{"text": "Hi", "speaker_id": 0, "output": "hi.wav"}], tmp_path)
    assert len(written) == 1
    assert written[0].endswith("hi.wav")
