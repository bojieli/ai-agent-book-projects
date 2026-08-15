from typing import Any, Dict, Optional, List
import copy
import uuid
from datetime import datetime, timezone
from abc import ABC, abstractmethod
import asyncio
from pydantic import BaseModel, Field, ConfigDict


class CheckpointMetadata(BaseModel):
    """
    Metadata for a checkpoint, including session and task identifiers.

    Attributes:
        session_id (str): The session identifier (required).
        task_id (Optional[str]): The task identifier (optional).
        artifact_id (Optional[str]): The artifact identifier (optional).
    """
    session_id: str = Field(..., description="The session identifier.")
    task_id: Optional[str] = Field(None, description="The task identifier.")
    artifact_id: Optional[str] = Field(None, description="The artifact identifier.")

    model_config = ConfigDict(extra="allow")

class Checkpoint(BaseModel):
    """
    Core structure for a state checkpoint.
    
    Attributes:
        id (str): Unique identifier for the checkpoint.
        ts (str): Timestamp of the checkpoint.
        metadata (CheckpointMetadata): Metadata associated with the checkpoint.
        values (dict[str, Any]): State values stored in the checkpoint.
        version (str): Version of the checkpoint format.
        parent_id (Optional[str]): Parent checkpoint identifier, if any.
        namespace (str): Namespace for the checkpoint, default is 'aworld'.
    """
    id: str = Field(..., description="Unique identifier for the checkpoint.")
    ts: str = Field(..., description="Timestamp of the checkpoint.")
    metadata: CheckpointMetadata = Field(..., description="Metadata associated with the checkpoint.")
    values: Dict[str, Any] = Field(..., description="State values stored in the checkpoint.")
    version: int = Field(..., description="Version of the checkpoint format.")
    parent_id: Optional[str] = Field(default=None, description="Parent checkpoint identifier, if any.")
    namespace: str = Field(default="aworld", description="Namespace for the checkpoint, default is 'aworld'.")

def empty_checkpoint() -> Checkpoint:
    """
    Create an empty checkpoint with default values.
    
    Returns:
        Checkpoint: An empty checkpoint structure.
    """
    return Checkpoint(
        id=str(uuid.uuid4()),
        ts=datetime.now(timezone.utc).isoformat(),
        metadata=CheckpointMetadata(session_id="", task_id=None),
        values={},
        version=1,
        parent_id=None,
        namespace="aworld",
    )

def copy_checkpoint(checkpoint: Checkpoint) -> Checkpoint:
    """
    Create a deep copy of a checkpoint.
    
    Args:
        checkpoint (Checkpoint): The checkpoint to copy.
    Returns:
        Checkpoint: A deep copy of the provided checkpoint.
    """
    return copy.deepcopy(checkpoint)

def create_checkpoint(
    values: Dict[str, Any],
    metadata: CheckpointMetadata,
    parent_id: Optional[str] = None,
    version: int = 1,
    namespace: str = 'aworld',
) -> Checkpoint:
    """
    Create a new checkpoint from provided state values and metadata.
    
    Args:
        values (dict[str, Any]): State values to store in the checkpoint.
        metadata (CheckpointMetadata): Metadata for the checkpoint.
        parent_id (Optional[str]): Parent checkpoint identifier, if any.
        version (str): Version of the checkpoint format.
        namespace (str): Namespace for the checkpoint.
    Returns:
        Checkpoint: The newly created checkpoint.
    """
    return Checkpoint(
        id=str(uuid.uuid4()),
        ts=datetime.now(timezone.utc).isoformat(),
        metadata=metadata,
        values=values,
        version=version,
        parent_id=parent_id,
        namespace=namespace,
    )

class BaseCheckpointRepository(ABC):
    """
    Abstract base class for a checkpoint repository.
    Provides synchronous and asynchronous methods for checkpoint management.
    """

    @abstractmethod
    def get(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        Retrieve a checkpoint by its unique identifier.
        
        Args:
            checkpoint_id (str): The unique identifier of the checkpoint.
        Returns:
            Optional[Checkpoint]: The checkpoint if found, otherwise None.
        """
        pass

    @abstractmethod
    def list(self, params: Dict[str, Any]) -> List[Checkpoint]:
        """
        List checkpoints matching the given parameters.
        
        Args:
            params (dict): Parameters to filter checkpoints.
        Returns:
            List[Checkpoint]: List of matching checkpoints.
        """
        pass

    @abstractmethod
    def put(self, checkpoint: Checkpoint) -> None:
        """
        Store a checkpoint.
        
        Args:
            checkpoint (Checkpoint): The checkpoint to store.
        """
        pass

    @abstractmethod
    def get_by_session(self, session_id: str) -> Optional[Checkpoint]:
        """
        Get the latest checkpoint for a session.
        
        Args:
            session_id (str): The session identifier.
        Returns:
            Optional[Checkpoint]: The latest checkpoint if found, otherwise None.
        """
        pass

    @abstractmethod
    def delete_by_session(self, session_id: str) -> None:
        """
        Delete all checkpoints related to a session.
        
        Args:
            session_id (str): The session identifier.
        """
        pass

    # Async methods
    async def aget(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        Asynchronously retrieve a checkpoint by its unique identifier.
        
        Args:
            checkpoint_id (str): The unique identifier of the checkpoint.
        Returns:
            Optional[Checkpoint]: The checkpoint if found, otherwise None.
        """
        return await asyncio.to_thread(self.get, checkpoint_id)

    async def alist(self, params: Dict[str, Any]) -> List[Checkpoint]:
        """
        Asynchronously list checkpoints matching the given parameters.
        
        Args:
            params (dict): Parameters to filter checkpoints.
        Returns:
            List[Checkpoint]: List of matching checkpoints.
        """
        return await asyncio.to_thread(self.list, params)

    async def aput(self, checkpoint: Checkpoint) -> None:
        """
        Asynchronously store a checkpoint.
        
        Args:
            checkpoint (Checkpoint): The checkpoint to store.
        """
        await asyncio.to_thread(self.put, checkpoint)

    async def aget_by_session(self, session_id: str) -> Optional[Checkpoint]:
        """
        Asynchronously get the latest checkpoint for a session.
        
        Args:
            session_id (str): The session identifier.
        Returns:
            Optional[Checkpoint]: The latest checkpoint if found, otherwise None.
        """
        return await asyncio.to_thread(self.get_by_session, session_id)

    async def adelete_by_session(self, session_id: str) -> None:
        """
        Asynchronously delete all checkpoints related to a session.
        
        Args:
            session_id (str): The session identifier.
        """
        await asyncio.to_thread(self.delete_by_session, session_id)

class VersionUtils:

    @staticmethod
    def get_next_version(version: int) -> int:
        """
        Get the next version of the checkpoint.
        """
        return version + 1
    
    @staticmethod
    def get_previous_version(version: int)  -> int:
        """
        Get the previous version of the checkpoint.
        """
        return version - 1
        
    @staticmethod
    def is_version_greater(checkpoint: Checkpoint, version: int) -> bool:
        """
        Check if the checkpoint version is greater than the given version.
        """
        return checkpoint.version > version
    
    @staticmethod
    def is_version_less(checkpoint: Checkpoint, version: int) -> bool:
        """
        Check if the checkpoint version is less than the given version.
        """
        return checkpoint.version < version