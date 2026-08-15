# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from enum import Enum

package = 'examples.common.tools'


class Tools(Enum):
    """Tool list supported in the framework, pre-defined to avoid spelling errors."""
    BROWSER = "browser"
    ANDROID = "android"
    GYM = "openai_gym"
    SEARCH_API = "search_api"
    SHELL = "shell"
    PYTHON_EXECUTE = "python_execute"
    CODE_EXECUTE = "code_execute"
    FILE = "file"
    IMAGE_ANALYSIS = "image_analysis"
    DOCUMENT_ANALYSIS = "document_analysis"
    HTML = "html"
    MCP = "mcp"


class Agents(Enum):
    """Agent supported in the framework, pre-defined to avoid spelling errors."""
    BROWSER = "browser_agent"
    ANDROID = "android_agent"
    SEARCH = "search_agent"
    CODE_EXECUTE = "code_execute_agent"
    FILE = "file_agent"
    IMAGE_ANALYSIS = "image_analysis_agent"
    SHELL = "shell_agent"
    DOCUMENT = "document_agent"
    GYM = "gym_agent"
    PLAN = "plan_agent"
    EXECUTE = "execute_agent"
    SUMMARY = "summary_agent"
