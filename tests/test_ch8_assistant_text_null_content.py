import pytest
import sys
import os

sys.path.insert(0, os.path.abspath("chapter8/trajectory-verifier"))

from verifier import _assistant_text, ProcessVerifier, PASS


def test_assistant_text_handles_null_content():
    """Contract: _assistant_text does not output literal 'None' for assistant tool-call messages with content: None."""
    trajectory = {
        "messages": [
            {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1"}]}
        ]
    }
    assert _assistant_text(trajectory) == ""


def test_process_verifier_privacy_tolerates_null_content_assistant_messages():
    """Contract: ProcessVerifier._privacy does not flag false positive privacy leak on content: None assistant messages."""
    trajectory = {
        "messages": [
            {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1"}]}
        ],
        "sensitive_values": [
            {"label": "auth token", "value": "None"}
        ]
    }
    pv = ProcessVerifier()
    res = pv._privacy(trajectory)
    assert res.verdict == PASS
