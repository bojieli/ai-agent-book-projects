"""Regression test: agent must tolerate providers that return usage=None.

The OpenAI SDK response object always HAS a `usage` attribute (pydantic
field), but it deserializes as None when the provider omits token accounting.
The old `hasattr(response, 'usage')` guard was therefore ineffective and
`response.usage.total_tokens` raised AttributeError, crashing execute_task.
"""
import os
import sys
from types import SimpleNamespace

os.environ.setdefault("OPENAI_API_KEY", "test-key")  # OpenAI() requires a key at construction
sys.path.insert(0, os.path.dirname(__file__))

from agent import ActiveToolAgent, RetrievalToolAgent, PassiveToolAgent
from tool_knowledge_base import ToolDefinition, ServerDefinition

AGENT_CLASSES = [ActiveToolAgent, RetrievalToolAgent, PassiveToolAgent]


def _catalog():
    tool = ToolDefinition(
        name="demo_tool",
        description="demo tool",
        parameters={"type": "object", "properties": {}},
        server="demo",
    )
    return [ServerDefinition(name="demo", description="demo server", tools=[tool])]


def _client_with_usage(usage):
    """Fake OpenAI client; response mimics the SDK object (usage attr always present)."""
    message = SimpleNamespace(content="final answer", tool_calls=None)
    response = SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)
    completions = SimpleNamespace(create=lambda **kwargs: response)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


def test_usage_none_does_not_crash():
    for cls in AGENT_CLASSES:
        agent = cls(servers=_catalog())
        agent.client = _client_with_usage(None)
        result = agent.execute_task("do something trivial")
        assert result["metrics"]["tokens_used"] == 0, cls.__name__


def test_usage_still_accumulated_when_present():
    for cls in AGENT_CLASSES:
        agent = cls(servers=_catalog())
        agent.client = _client_with_usage(SimpleNamespace(total_tokens=42))
        result = agent.execute_task("do something trivial")
        assert result["metrics"]["tokens_used"] == 42, cls.__name__
