"""
Test suite locking out TypeError in _resolve_gemini_model
when API returns data with models: None or non-dict items.
"""

import json
from unittest.mock import MagicMock

from pipeline import _resolve_gemini_model, config


def test_resolve_gemini_model_handles_null_models():
    """
    Ensure _resolve_gemini_model returns default model without TypeError when models key is None.
    """
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"models": None}).encode("utf-8")
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=None)

    import urllib.request
    urllib.request.urlopen = MagicMock(return_value=mock_resp)

    res = _resolve_gemini_model("dummy_key")
    assert res == config.GEMINI_MODEL_DEFAULT
