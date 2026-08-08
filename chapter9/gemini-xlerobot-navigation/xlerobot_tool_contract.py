"""Book-local semantic tool contract for the optional RoboCrew/XLeRobot run.

The pinned navigation checkout exposes base-motion helpers, not a stable
semantic arm API.  This module is therefore an explicit adapter boundary: the
local GPU experiment validates the contract, while a hardware integrator must
map each primitive to calibrated XLeRobot arm motions before enabling torque.
"""

from __future__ import annotations

TOOL_CONTRACT = (
    {
        "name": "observe_scene",
        "description": "Capture a new RGB observation and return object/target state.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "pick",
        "description": "Execute one bounded calibrated pick primitive.",
        "parameters": {"type": "object", "properties": {"object_id": {"type": "string", "enum": ["red_cup", "yellow_paper"]}}, "required": ["object_id"], "additionalProperties": False},
    },
    {
        "name": "place",
        "description": "Execute one bounded calibrated place primitive.",
        "parameters": {"type": "object", "properties": {"object_id": {"type": "string", "enum": ["red_cup", "yellow_paper"]}, "target_id": {"type": "string", "enum": ["tray", "bin"]}}, "required": ["object_id", "target_id"], "additionalProperties": False},
    },
    {
        "name": "verify_state",
        "description": "Check the postcondition using a fresh observation.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "stop",
        "description": "Stop all motion and enter a safe state.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
)


def robocrew_function_declarations() -> list[dict[str, object]]:
    """Return JSON-compatible declarations for a RoboCrew/Gemini bridge."""

    return [
        {"name": item["name"], "description": item["description"], "parameters": item["parameters"]}
        for item in TOOL_CONTRACT
    ]
