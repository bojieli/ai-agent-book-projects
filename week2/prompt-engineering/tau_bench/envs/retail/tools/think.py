# Copyright Sierra

from typing import Any, Dict
from tau_bench.envs.tool import Tool


class Think(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], thought: str) -> str:
        # This method does not change the state of the data; it simply returns an empty string.
        return ""

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "think",
                "description": (
                    "Use the tool to think about something. It will not obtain new information or change the database, "
                    "but just append the thought to the log. Use it when complex reasoning or some cache memory is needed."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "thought": {
                            "type": "string",
                            "description": "A thought to think about.",
                        },
                    },
                    "required": ["thought"],
                },
            },
        }
