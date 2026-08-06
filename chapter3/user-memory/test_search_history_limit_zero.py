"""Regression test for ConversationHistory.search_history limit=0 handling.

Proves contract: Requesting limit<=0 from search_history returns an empty list
without executing text or vector search.
Locks out bug where limit=0 appended the first match before breaking, returning 1 result instead of 0.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from conversation_history import ConversationHistory  # noqa: E402
from config import Config  # noqa: E402


def make_history(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "CONVERSATION_HISTORY_DIR", str(tmp_path))
    monkeypatch.setattr(Config, "ENABLE_HISTORY_SEARCH", False)
    return ConversationHistory("user1")


def test_search_history_limit_zero_returns_empty_list(tmp_path, monkeypatch):
    history = make_history(tmp_path, monkeypatch)
    history.add_turn("session-1", "Hello assistant", "Hello user")
    history.add_turn("session-1", "Search for something", "Here is your result")

    results = history.search_history("hello", limit=0)
    assert results == []


def test_search_history_limit_negative_returns_empty_list(tmp_path, monkeypatch):
    history = make_history(tmp_path, monkeypatch)
    history.add_turn("session-1", "Hello assistant", "Hello user")

    results = history.search_history("hello", limit=-1)
    assert results == []
