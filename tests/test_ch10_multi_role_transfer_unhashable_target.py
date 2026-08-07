import json
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest

ch10_mrt = Path(__file__).resolve().parent.parent / "chapter10" / "multi-role-transfer"
if str(ch10_mrt) not in sys.path:
    sys.path.insert(0, str(ch10_mrt))

tools_backup = sys.modules.pop("tools", None)
from orchestrator import MultiRoleOrchestrator
sys.modules.pop("tools", None)
if tools_backup is not None:
    sys.modules["tools"] = tools_backup

FINAL_TEXT = "处理完毕。"


def _tool_call_msg(name, arguments):
    tc = SimpleNamespace(
        id="call_1",
        type="function",
        function=SimpleNamespace(name=name, arguments=arguments),
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[tc]))]
    )


def _final_msg():
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=FINAL_TEXT, tool_calls=None))]
    )


def _fake_client(responses):
    queue = list(responses)
    return SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: queue.pop(0)))
    )


def test_unhashable_target_role_in_transfer_to_agent_returns_error_string_not_crash():
    """Regression test: when transfer_to_agent receives an unhashable target_role (e.g. list or dict),
    the orchestrator must not crash with TypeError: unhashable type, but return a failure message."""
    bad_args = json.dumps({"target_role": ["research"], "reason": "test"})
    orch = MultiRoleOrchestrator(
        client=_fake_client([_tool_call_msg("transfer_to_agent", bad_args), _final_msg()]),
        verbose=False,
        start_role="triage",
    )
    final = orch.run("处理任务")
    assert final == FINAL_TEXT
    tool_results = [m["content"] for m in orch.history if m["role"] == "tool"]
    assert any("移交失败" in r for r in tool_results)
