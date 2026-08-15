# coding: utf-8

from typing import Optional
from aworld.config.conf import AgentConfig
from typing import Literal

ToolCallingMethod = Literal['function_calling', 'json_mode', 'raw', 'auto']


class BrowserAgentConfig(AgentConfig):
    use_vision: bool = True
    use_vision_for_planner: bool = False
    save_conversation_path: Optional[str] = None
    save_conversation_path_encoding: Optional[str] = 'utf-8'
    max_failures: int = 3
    retry_delay: int = 10
    validate_output: bool = False
    message_context: Optional[str] = None
    generate_gif: bool | str = False
    available_file_paths: Optional[list[str]] = None
    override_system_message: Optional[str] = None
    extend_system_message: Optional[str] = None
    tool_calling_method: Optional[ToolCallingMethod] = 'auto'
    max_llm_json_retries: int = 3
    save_file_path: str = "browser_agent_history.json"