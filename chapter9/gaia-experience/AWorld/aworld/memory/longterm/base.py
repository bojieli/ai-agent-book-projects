# coding: utf-8
# Copyright (c) 2025 inclusionAI.

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Any, Optional, Literal

from pydantic import BaseModel, Field

from aworld.core.memory import MemoryStore, LongTermConfig
from aworld.models.llm import LLMModel
from aworld.memory.models import UserProfile, AgentExperience, LongTermExtractParams


class MemoryProcessingResult(BaseModel):
    """
    Represents the result of memory processing operation.
    """
    task_id: str = Field(default=None, description="Task identifier")
    success: bool = Field(default=False, description="Success flag")
    user_profiles: Optional[List[UserProfile]] = Field(default_factory=list, description="User profiles")
    agent_experiences: Optional[List[AgentExperience]] = Field(default_factory=list, description="Agent experiences")
    finished_at: Optional[str] = Field(default=str(datetime.now().isoformat()), description="Finished timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message")

class MemoryProcessingTask(BaseModel):
    """
    Represents a memory processing task containing information needed for long-term memory processing.
    
    Args:
        memory_task_id: Task identifier
        task_type: Task type
        extract_params: Long-term extract parameters
        created_at: Creation timestamp
        finished_at: Finished timestamp
    """
    memory_task_id: str = Field(default=str(uuid.uuid4()), description="Memory task identifier")
    task_type: Literal['user_profile', 'agent_experience'] = Field(..., description="Memory task type")
    extract_params: LongTermExtractParams = Field(description="Long-term extract parameters")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Creation timestamp")
    finished_at: str = Field(default=None, description="Finished timestamp")
    status: Literal['initial', 'processing', 'completed', 'failed'] = Field(default='initial', description="Task status")
    result: Optional[MemoryProcessingResult] = Field(default=None, description="Processing result")
    longterm_config: LongTermConfig = Field(description="Long-term memory configuration")

class MemoryOrchestrator(ABC):

    """
    Abstract base class for memory orchestrator that determines when and how to process memories.
    Responsible for evaluating trigger conditions and creating processing tasks.
    """
    
    def __init__(self, llm_instance: LLMModel,
                 longterm_config: LongTermConfig,
                 embedding_model: Optional[Any] = None,
                 long_term_memory_store: MemoryStore = None) -> None:
        """
        Initialize the memory orchestrator.
        
        Args:
            llm_instance: LLM model instance for processing
        """
        self._llm_instance = llm_instance
        self._longterm_config = longterm_config
        self._embedding_model = embedding_model
        self._long_term_memory_store: MemoryStore = long_term_memory_store


    @abstractmethod
    async def create_longterm_processing_tasks(self,
                                         extract_param_list: list[LongTermExtractParams],
                                         longterm_config: LongTermConfig
                                         ) -> None:
        """
        Create long-term memory processing tasks from the given memory items.

        Args:
            task_params: List of long-term extract parameters
            longterm_config: Long-term memory configuration settings
        """
        pass


    @abstractmethod
    async def retrieve_agent_experience(
        self, 
        query: str, 
        agent_id: Optional[str] = None,
        application_id: Optional[str] = "default",
    ) -> List[AgentExperience]:
        """
        Retrieve similar agent experiences from long-term storage for context.
        
        Args:
            query: Query string for similarity search
            agent_id: Agent identifier for filtering
            application_id: Application identifier for filtering
            
        Returns:
            List of similar memory items
        """
        pass

    @abstractmethod
    async def retrieve_user_profile(
        self, 
        query: str, 
        user_id: Optional[str] = None,
        application_id: Optional[str] = "default",
    ) -> List[UserProfile]:
        """
        Retrieve similar user profiles from long-term storage for context.

        Args:
            query: Query string for similarity search
            user_id: User identifier for filtering
            application_id: Application identifier for filtering
            
        Returns:
            List of similar memory items
        """
        pass


class MemoryGungnir(ABC):
    """
    Abstract base class for memory processing engine (Gungnir - the eternal spear of memory).
    Responsible for extracting and processing long-term memories from short-term memory items.
    """
    
    def __init__(self, llm_instance: LLMModel) -> None:
        """
        Initialize the memory processing engine.
        
        Args:
            llm_instance: LLM model instance for processing
        """
        self._llm_instance = llm_instance
    

    @abstractmethod
    async def process_memory_task(
        self, 
        task: MemoryProcessingTask
    ) -> MemoryProcessingResult:
        """
        Process a memory task and extract long-term memories.
        
        Args:
            task: Memory processing task to execute
            
        Returns:
            Processing result containing extracted memories
        """
        pass

 