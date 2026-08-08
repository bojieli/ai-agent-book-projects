import sys, os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath("chapter10/multi-role-transfer"))
from orchestrator import MultiRoleOrchestrator


def test_orchestrator_non_dict_tool_call_arguments_handled():
    mock_client = MagicMock()

    # Mock tool call with arguments parsing to a list [1, 2] instead of a dict
    tool_call = MagicMock()
    tool_call.id = "call_non_dict"
    tool_call.function.name = "transfer_to_agent"
    tool_call.function.arguments = "[1, 2]"

    msg = MagicMock()
    msg.content = None
    msg.tool_calls = [tool_call]

    choice = MagicMock()
    choice.message = msg

    response = MagicMock()
    response.choices = [choice]

    mock_client.chat.completions.create.return_value = response

    orchestrator = MultiRoleOrchestrator(client=mock_client, verbose=False)
    # _run_one_llm_turn should handle non-dict arguments gracefully without raising AttributeError
    res = orchestrator._run_one_llm_turn()
    assert res is None
    assert len(orchestrator.history) >= 2
    # The tool response message should record the invalid transfer attempt cleanly
    tool_msg = orchestrator.history[-1]
    assert tool_msg["role"] == "tool"
    assert "移交失败" in tool_msg["content"]
