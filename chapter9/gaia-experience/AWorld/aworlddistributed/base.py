import uuid
from typing import Any
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic import Field


class AworldTask(BaseModel):
    task_id: str = Field(default=None, description="task id")
    agent_id: str = Field(default=None, description="agent id")
    agent_input: str = Field(default=None, description="agent input")
    session_id: Optional[str] = Field(default=None, description="session id")
    user_id: Optional[str] = Field(default=None, description="user id")
    llm_provider: Optional[str] = Field(default=None, description="llm provider")
    llm_model_name: Optional[str] = Field(default=None, description="llm model name")
    llm_api_key: Optional[str] = Field(default=None, description="llm api key")
    llm_base_url: Optional[str] = Field(default=None, description="llm base url")
    llm_custom_input: Optional[str] = Field(default=None, description="custom_input")
    task_system_prompt: Optional[str] = Field(default=None, description="task_system_prompt")
    mcp_servers: Optional[list[str]] = Field(default=None, description="mcp_servers")
    node_id: Optional[str] = Field(default=None, description="execute task node_id")
    client_id: Optional[str] = Field(default=None, description="submit client ip")
    status: Optional[str] = Field(default="INIT", description="submitted/running/execute_failed/execute_success")
    history_messages: Optional[int] = Field(default=100, description="history_message")
    max_steps: Optional[int] = Field(default=100, description="max_steps")
    max_retries: Optional[int] = Field(default=5, description="max_retries use Exponential backoff with jitter")
    ext_info: Optional[dict] = Field(default_factory=dict, description="custom")
    created_at: Optional[datetime] = Field(default=None, description="created time")
    updated_at: Optional[datetime] = Field(default=None, description="updated time")

    def mark_running(self):
        self.status = 'RUNNING'

    def mark_failed(self):
        self.status = 'FAILED'

    def mark_success(self):
        self.status = 'SUCCESS'

class AworldTaskResult(BaseModel):
    task: AworldTask = Field(default=None, description="task")
    server_host: Optional[str] = Field(default=None, description="aworld server id")
    data: Any = Field(default=None, description="result data")

class AworldTaskForm(BaseModel):
    batch_id: str = Field(default=str(uuid.uuid4()), description="batch_id")
    task: Optional[AworldTask] = Field(default=None, description="task")
    user_id: Optional[str] = Field(default=None, description="user id")
    client_id: Optional[str] = Field(default=None, description="submit client ip")


class OpenAIChatMessage(BaseModel):
    role: str
    content: str | List

    model_config = ConfigDict(extra="allow")


class OpenAIChatCompletionForm(BaseModel):
    stream: bool = True
    model: str
    messages: List[OpenAIChatMessage]

    model_config = ConfigDict(extra="allow")


class FilterForm(BaseModel):
    body: dict
    user: Optional[dict] = None
    model_config = ConfigDict(extra="allow")