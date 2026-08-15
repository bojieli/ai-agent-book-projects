from typing import Any, Dict, List, Optional
from . import Checkpoint, BaseCheckpointRepository, VersionUtils

class InMemoryCheckpointRepository(BaseCheckpointRepository):
    """
    In-memory implementation of BaseCheckpointRepository.
    Stores checkpoints in a simple in-memory dictionary.
    Thread safety is not guaranteed.
    """
    def __init__(self) -> None:
        """
        Initialize the in-memory checkpoint repository.
        """
        self._checkpoints: Dict[str, Checkpoint] = {}
        self._session_index: Dict[str, List[str]] = {}

    def get(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        Retrieve a checkpoint by its unique identifier.
        Args:
            checkpoint_id (str): The unique identifier of the checkpoint.
        Returns:
            Optional[Checkpoint]: The checkpoint if found, otherwise None.
        """
        return self._checkpoints.get(checkpoint_id)

    def list(self, params: Dict[str, Any]) -> List[Checkpoint]:
        """
        List checkpoints matching the given parameters.
        Args:
            params (dict): Parameters to filter checkpoints.
        Returns:
            List[Checkpoint]: List of matching checkpoints.
        """
        result = []
        for cp in self._checkpoints.values():
            match = True
            for k, v in params.items():
                if k == 'session_id':
                    if cp.metadata.session_id != v:
                        match = False
                        break
                elif k == 'task_id':
                    if cp.metadata.task_id != v:
                        match = False
                        break
                elif cp.get(k) != v:
                    match = False
                    break
            if match:
                result.append(cp)
        return result

    def put(self, checkpoint: Checkpoint) -> None:
        """
        Store a checkpoint.
        Args:
            checkpoint (Checkpoint): The checkpoint to store.
        """
        # Find last version checkpoint by session_id
        last_checkpoint = self.get_by_session(checkpoint.metadata.session_id)
        
        if last_checkpoint:
            # Compare versions to ensure optimistic locking
            if VersionUtils.is_version_less(checkpoint, last_checkpoint.version):
                raise ValueError(f"New checkpoint version {checkpoint.version} must be greater than last version {last_checkpoint.version}")
            
        # Store the new checkpoint
        self._checkpoints[checkpoint.id] = checkpoint
            
        # Update session index
        session_id = checkpoint.metadata.session_id
        if session_id:
            if session_id not in self._session_index:
                self._session_index[session_id] = []
            self._session_index[session_id].append(checkpoint.id)

    def get_by_session(self, session_id: str) -> Optional[Checkpoint]:
        """
        Get the latest checkpoint for a session.
        Args:
            session_id (str): The session identifier.
        Returns:
            Optional[Checkpoint]: The latest checkpoint if found, otherwise None.
        """
        ids = self._session_index.get(session_id, [])
        if not ids:
            return None
        # Assume the last one is the latest
        last_id = ids[-1]
        return self._checkpoints.get(last_id)

    def delete_by_session(self, session_id: str) -> None:
        """
        Delete all checkpoints related to a session.
        Args:
            session_id (str): The session identifier.
        """
        ids = self._session_index.pop(session_id, [])
        for cid in ids:
            self._checkpoints.pop(cid, None)

    async def alist(self, params: Dict[str, Any]) -> List[Checkpoint]:
        return self.list(params)

    async def aget(self, checkpoint_id: str) -> Optional[Checkpoint]:
        return self.get(checkpoint_id)

    async def aput(self, checkpoint: Checkpoint) -> None:
        self.put(checkpoint)

    async def aget_by_session(self, session_id: str) -> Optional[Checkpoint]:
        return self.get_by_session(session_id)

    async def adelete_by_session(self, session_id: str) -> None:
        self.delete_by_session(session_id)