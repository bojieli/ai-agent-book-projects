"""Null issues on request_revision must behave like empty list."""
from unittest.mock import MagicMock

from agent import StagedAgent
import tools as T


def test_null_issues_like_empty():
    agent = StagedAgent.__new__(StagedAgent)
    agent.workspace = T.Workspace()
    agent.revision_count = 0
    agent.logs = []
    agent._log = lambda *a, **k: None
    msg, desc = agent._transition_result(T.REQUEST_REVISION, {"issues": None})
    assert agent.workspace.review_issues == []
    assert desc["issues"] == []
    assert "退回" in msg or "问题" in msg
