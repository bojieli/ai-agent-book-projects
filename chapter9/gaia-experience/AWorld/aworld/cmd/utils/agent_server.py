from abc import abstractmethod
import asyncio
from pathlib import Path
from typing import Dict, List
import os

from dotenv import load_dotenv
from aworld import trace
from aworld.cmd.data_model import (
    AgentModel,
    ChatCompletionMessage,
    ChatCompletionRequest,
)
from aworld.session.base_session_service import BaseSessionService
from aworld.session.simple_session_service import SimpleSessionService
from . import agent_loader
from aworld.trace.config import ObservabilityConfig
from aworld.trace.opentelemetry.memory_storage import InMemoryWithPersistStorage


# bugfix for tracer exception
trace.configure(ObservabilityConfig(trace_storage=(InMemoryWithPersistStorage())))


class ChatCallBack:
    @abstractmethod
    async def on_chat_completion_request(
        self, server: "AgentServer", request: ChatCompletionRequest
    ):
        pass

    @abstractmethod
    async def on_chat_completion_end(
        self, server: "AgentServer", request: ChatCompletionRequest, final_response: str
    ):
        pass


class SessionChatCallBack(ChatCallBack):

    async def on_chat_completion_request(
        self, server: "AgentServer", request: ChatCompletionRequest
    ):
        await server.get_session_service().append_messages(
            request.user_id,
            request.session_id,
            request.messages[-1:],
        )

    async def on_chat_completion_end(
        self, server: "AgentServer", request: ChatCompletionRequest, final_response: str
    ):
        await server.get_session_service().append_messages(
            request.user_id,
            request.session_id,
            [
                ChatCompletionMessage(
                    role="assistant",
                    content=final_response,
                    trace_id=request.trace_id,
                ),
            ],
        )


class AgentServer:
    server_id: str
    server_name: str
    server_dir: str
    session_service: BaseSessionService = None
    agent_instances: Dict[str, AgentModel] = {}
    chat_call_backs: List[ChatCallBack] = [SessionChatCallBack()]

    def __init__(
        self,
        server_id: str,
        server_name: str,
        server_dir: str = os.getcwd(),
        session_service: BaseSessionService = SimpleSessionService(),
    ):
        """
        Initialize AgentServer
        """
        self.server_id = server_id
        self.server_name = server_name
        self.server_dir = server_dir
        self.session_service = session_service
        # Load server global env
        load_dotenv(Path(self.server_dir) / ".env", override=True, verbose=True)
        # Load agent instances
        self.agent_instances = agent_loader.list_agents(self.server_dir)

    def list_agents(self) -> Dict[str, AgentModel]:
        return self.agent_instances

    def get_agent(self, agent_id: str) -> AgentModel:
        return self.agent_instances.get(agent_id)

    def get_session_service(self) -> BaseSessionService:
        return self.session_service

    async def on_chat_completion_request(self, request: ChatCompletionRequest):
        tasks = []
        for chat_call_back in self.chat_call_backs:
            tasks.append(chat_call_back.on_chat_completion_request(self, request))
        await asyncio.gather(*tasks)

    async def on_chat_completion_end(
        self, request: ChatCompletionRequest, final_response: str
    ):
        tasks = []
        for chat_call_back in self.chat_call_backs:
            tasks.append(
                chat_call_back.on_chat_completion_end(self, request, final_response)
            )
        await asyncio.gather(*tasks)
