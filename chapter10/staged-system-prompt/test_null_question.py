"""Null ask_clarifying_question.question must coerce to empty string."""

import sys
from pathlib import Path
from types import ModuleType

sys.path.insert(0, str(Path(__file__).parent))

try:
    import openai  # noqa: F401
except ImportError:
    sys.modules["openai"] = ModuleType("openai")
    sys.modules["openai"].OpenAI = object

import tools as T
from agent import StagedAgent
from simulated_user import SimulatedUser


def _bare_agent():
    ag = object.__new__(StagedAgent)
    ag.workspace = T.Workspace()
    ag.logs = []
    ag.verbose = False
    ag.stage = "requirements"
    ag.interactive = False
    ag.sim_user = SimulatedUser()
    return ag


def test_ask_clarifying_null_question_does_not_crash():
    ag = _bare_agent()
    res = ag._dispatch_tool("ask_clarifying_question", {"question": None})
    assert isinstance(res, str)
    assert len(res) > 0


def test_ask_clarifying_normal_question_still_answers():
    ag = _bare_agent()
    res = ag._dispatch_tool(
        "ask_clarifying_question", {"question": "需要递归处理子目录吗？"})
    assert "递归" in res or "子" in res
