"""get_recent_turns(limit=0) must return [], not the full history."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from conversation_history import ConversationHistory, ConversationTurn


def test_limit_zero_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "CONVERSATION_HISTORY_DIR", str(tmp_path))
    monkeypatch.setattr(Config, "ENABLE_HISTORY_SEARCH", False)
    hist = ConversationHistory("u1")
    hist.conversations = [
        ConversationTurn("s", "u0", "a0", "t0", 1),
        ConversationTurn("s", "u1", "a1", "t1", 2),
        ConversationTurn("s", "u2", "a2", "t2", 3),
    ]
    assert hist.get_recent_turns(0) == []


def test_positive_limit_still_returns_recent(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "CONVERSATION_HISTORY_DIR", str(tmp_path))
    monkeypatch.setattr(Config, "ENABLE_HISTORY_SEARCH", False)
    hist = ConversationHistory("u1")
    t1 = ConversationTurn("s", "u1", "a1", "t1", 1)
    t2 = ConversationTurn("s", "u2", "a2", "t2", 2)
    t3 = ConversationTurn("s", "u3", "a3", "t3", 3)
    hist.conversations = [t1, t2, t3]
    assert hist.get_recent_turns(2) == [t2, t3]
