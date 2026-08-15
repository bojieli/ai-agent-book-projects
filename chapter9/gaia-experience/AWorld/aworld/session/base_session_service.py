import abc
from typing import List, Optional

from aworld.cmd.data_model import SessionModel, ChatCompletionMessage


class BaseSessionService(abc.ABC):
    @abc.abstractmethod
    async def get_session(
        self, user_id: str, session_id: str
    ) -> Optional[SessionModel]:
        pass

    @abc.abstractmethod
    async def list_sessions(self, user_id: str) -> List[SessionModel]:
        pass

    @abc.abstractmethod
    async def delete_session(self, user_id: str, session_id: str) -> None:
        pass

    @abc.abstractmethod
    async def append_messages(
        self, user_id: str, session_id: str, messages: List[ChatCompletionMessage]
    ) -> None:
        pass
