from enum import Enum

ATTRIBUTES_NAMESPACE = 'aworld'
"""Namespace within OTEL attributes used by aworld."""

ATTRIBUTES_MESSAGE_KEY = f'{ATTRIBUTES_NAMESPACE}.msg'
"""The formatted message for a log."""

ATTRIBUTES_MESSAGE_TEMPLATE_KEY = f'{ATTRIBUTES_NAMESPACE}.msg_template'
"""The template for a log message."""

ATTRIBUTES_MESSAGE_RUN_TYPE_KEY = f'{ATTRIBUTES_NAMESPACE}.run_type'
"""The template for a log message."""

MESSAGE_FORMATTED_VALUE_LENGTH_LIMIT = 128
"""Maximum number of characters for formatted values in a trace message."""

SPAN_NAME_PREFIX_EVENT = "event."
"""Prefix for event span name."""

SPAN_NAME_PREFIX_EVENT_AGENT = SPAN_NAME_PREFIX_EVENT + "agent."
"""Prefix for event span name of agent."""

SPAN_NAME_PREFIX_EVENT_TOOL = SPAN_NAME_PREFIX_EVENT + "tool."
"""Prefix for event span name of tool."""

SPAN_NAME_PREFIX_EVENT_TASK = SPAN_NAME_PREFIX_EVENT + "task."
"""Prefix for event span name of task."""

SPAN_NAME_PREFIX_EVENT_OUTPUT = SPAN_NAME_PREFIX_EVENT + "output."
"""Prefix for event span name of output."""

SPAN_NAME_PREFIX_EVENT_OTHER = SPAN_NAME_PREFIX_EVENT + "other."
"""Prefix for event span name of error."""

SPAN_NAME_PREFIX_TASK = "task."
"""Prefix for task span name."""

SPAN_NAME_PREFIX_AGENT = "agent."
"""Prefix for agent span name."""

SPAN_NAME_PREFIX_TOOL = "tool."
"""Prefix for tool span name."""

SPAN_NAME_PREFIX_LLM = "llm."
"""Prefix for llm span name."""


class RunType(Enum):
    '''Span run type supported in the framework
    '''
    AGNET = "AGENT"
    TOOL = "TOOL"
    MCP = "MCP"
    LLM = "LLM"
    TASK = "TASK"
    OTHER = "OTHER"
