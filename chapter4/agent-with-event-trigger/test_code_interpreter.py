"""Regression tests for the code interpreter's execution namespace."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


def _load_agent_module():
    openai = types.ModuleType("openai")
    openai.OpenAI = type("OpenAI", (), {})

    mcp = types.ModuleType("mcp")
    mcp.__path__ = []
    mcp.ClientSession = type("ClientSession", (), {})
    mcp.StdioServerParameters = type("StdioServerParameters", (), {})

    mcp_client = types.ModuleType("mcp.client")
    mcp_client.__path__ = []
    mcp_stdio = types.ModuleType("mcp.client.stdio")
    mcp_stdio.stdio_client = lambda *args, **kwargs: None
    mcp_types = types.ModuleType("mcp.types")
    mcp_types.TextContent = type("TextContent", (), {})

    stubs = {
        "openai": openai,
        "mcp": mcp,
        "mcp.client": mcp_client,
        "mcp.client.stdio": mcp_stdio,
        "mcp.types": mcp_types,
    }
    module_path = Path(__file__).with_name("agent.py")
    module_name = "_event_trigger_agent_under_test"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)

    with patch.dict(sys.modules, stubs):
        sys.modules[module_name] = module
        sys.path.insert(0, str(module_path.parent))
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)

    return module


class CodeInterpreterNamespaceTests(unittest.TestCase):
    def test_code_interpreter_shares_names_with_defined_functions(self):
        agent_module = _load_agent_module()
        agent = agent_module.EventTriggeredAgent.__new__(agent_module.EventTriggeredAgent)

        result = agent._tool_code_interpreter(
            "value = 5\n"
            "def double():\n"
            "    return value * 2\n"
            "print(double())"
        )

        self.assertEqual(
            result,
            {
                "success": True,
                "stdout": "10\n",
                "stderr": "",
            },
        )


if __name__ == "__main__":
    unittest.main()
