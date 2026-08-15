import os
import pickle
import threading

from typing import List, Optional
from typing_extensions import override
from datetime import datetime
from aworld.cmd.data_model import SessionModel, ChatCompletionMessage
from aworld.logs.util import logger
from .base_session_service import BaseSessionService


class SimpleSessionService(BaseSessionService):
    def __init__(self):
        self.data_file = os.path.join(os.curdir, "data", "session.bin")
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        self._lock = threading.Lock()

    def _load_sessions(self) -> dict:
        if not os.path.exists(self.data_file):
            return {}
        try:
            with open(self.data_file, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            return {}

    def _save_sessions(self, sessions: dict):
        try:
            temp_file = self.data_file + ".tmp"
            with open(temp_file, "wb") as f:
                pickle.dump(sessions, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_file, self.data_file)
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise

    @override
    async def get_session(
        self, user_id: str, session_id: str
    ) -> Optional[SessionModel]:
        session_key = f"{user_id}:{session_id}"
        with self._lock:
            sessions = self._load_sessions()
            return sessions.get(session_key)

    @override
    async def list_sessions(self, user_id: str) -> List[SessionModel]:
        with self._lock:
            sessions = self._load_sessions()
            user_sessions = [
                session for key, session in sessions.items() if key.startswith(user_id)
            ]
            # Sort by created_at in descending order (newest first)
            return sorted(user_sessions, key=lambda x: x.created_at, reverse=True)

    @override
    async def delete_session(self, user_id: str, session_id: str) -> None:
        session_key = f"{user_id}:{session_id}"
        with self._lock:
            sessions = self._load_sessions()
            if session_key not in sessions:
                logger.warning(f"Session {session_key} not found")
                return
            del sessions[session_key]
            self._save_sessions(sessions)

    @override
    async def append_messages(
        self, user_id: str, session_id: str, messages: List[ChatCompletionMessage]
    ) -> None:
        session_key = f"{user_id}:{session_id}"
        with self._lock:
            sessions = self._load_sessions()

            if session_key not in sessions:
                logger.info(f"Session {session_key} not found, creating new session")
                sessions[session_key] = SessionModel(
                    user_id=user_id,
                    session_id=session_id,
                    name=messages[0].content,
                    description=messages[0].content,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    messages=[],
                )

            sessions[session_key].messages.extend(messages)
            sessions[session_key].updated_at = datetime.now()
            self._save_sessions(sessions)
