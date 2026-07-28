"""A deterministic reference agent for the reporting evaluation environment."""

from __future__ import annotations

from typing import Any

from reporting_tools import ReportingEnvironment


class DeterministicReportingAgent:
    """Executes the task's explicit tool plan and returns a structured trace."""

    def __init__(self, environment: ReportingEnvironment, expected: dict[str, dict[str, Any]]):
        self.environment = environment
        self.expected = expected

    def run(self, task: dict[str, Any]) -> dict[str, Any]:
        result = self.environment.call(task["tool"], task["arguments"])
        expected = self.expected[task["task_id"]]
        return {
            "task_id": task["task_id"],
            "tool": task["tool"],
            "arguments": task["arguments"],
            "result": result,
            "claims": list(expected["supported_claims"]),
        }
