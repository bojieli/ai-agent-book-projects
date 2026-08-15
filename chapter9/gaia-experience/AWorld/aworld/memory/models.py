import uuid
from abc import abstractmethod
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, List, Optional, Literal

from aworld.models.model_response import ToolCall

class MemoryItem(BaseModel):
    id: str = Field(description="id")
    content: Any = Field(description="content")
    created_at: Optional[str] = Field(None, description="created at")
    updated_at: Optional[str] = Field(None, description="updated at")
    metadata: dict = Field(
        description="metadata, use to store additional information, such as user_id, agent_id, run_id, task_id, etc.")
    tags: list[str] = Field(description="tags")
    histories: list["MemoryItem"] = Field(default_factory=list)
    deleted: bool = Field(default=False)
    memory_type: Literal["init", "message", "summary", "agent_experience", "user_profile", "fact", "conversation_summary"] = Field(default="message")
    version: int = Field(description="version")

    def __init__(self, **data):
        # Set default values for optional fields
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        if "created_at" not in data:
            data["created_at"] = datetime.now().isoformat()
        if "updated_at" not in data:
            data["updated_at"] = data["created_at"]
        if "metadata" not in data:
            data["metadata"] = {}
        if "tags" not in data:
            data["tags"] = []
        if "version" not in data:
            data["version"] = 1

        super().__init__(**data)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryItem":
        """Create a MemoryItem instance from a dictionary.

        Args:
            data (dict): A dictionary containing the memory item data.

        Returns:
            MemoryItem: An instance of MemoryItem.
        """
        return cls(**data)

    @property
    def user_id(self) -> str:
        return self.metadata.get('user_id')

    @property
    def session_id(self) -> str:
        return self.metadata.get('session_id')

    @property
    def task_id(self) -> str:
        return self.metadata.get('task_id')

    @property
    def agent_id(self) -> str:
        return self.metadata.get('agent_id')

    @property
    def agent_name(self) -> str:
        return self.metadata.get('agent_name')

    @property
    def application_id(self) -> str:
        return self.metadata.get('application_id', 'default')

    @property
    def embedding_text(self) -> Optional[str]:
        return self.content

    def mark_has_summary(self):
        self.metadata['summary'] = True

    @property
    def has_summary(self) -> bool:
        return self.metadata.get('summary', False)
    
    @property
    def content_length(self) -> int:
        return len(self.content)

    @property
    def status(self) -> str:
        return self.metadata.get('status', 'ACCEPTED')

    @status.setter
    def status(self, value: Literal["DRAFT", "ACCEPTED", "DISCARD"]) -> None:
        self.metadata['status'] = value

    @abstractmethod
    def to_openai_message(self) -> dict:
        pass


class MessageMetadata(BaseModel):
    """
    Metadata for memory messages, including user, session, task, and agent information.
    Args:
        user_id (str): The ID of the user.
        session_id (str): The ID of the session.
        task_id (str): The ID of the task.
        agent_id (str): The ID of the agent.
    """
    agent_id: str = Field(description="The ID of the agent")
    agent_name: Optional[str] = Field(description="The name of the agent")
    session_id: Optional[str] = Field(default=None,description="The ID of the session")
    task_id: Optional[str] = Field(default=None,description="The ID of the task")
    user_id: Optional[str] = Field(default=None, description="The ID of the user")
    summary_content: Optional[str] = Field(default=None, description="The summary of the memory item")

    model_config = ConfigDict(extra="allow")

    @property
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

class AgentExperienceItem(BaseModel):
    skill: str = Field(description="The skill demonstrated in the experience")
    actions: List[str] = Field(description="The actions taken by the agent")


class AgentExperience(MemoryItem):
    """
    Represents an agent's experience, including skills and actions.
    All custom attributes are stored in content and metadata.
    Args:
        agent_id (str): The ID of the agent.
        skill (str): The skill demonstrated in the experience.
        actions (List[str]): The actions taken by the agent.
        metadata (Optional[Dict[str, Any]]): Additional metadata.
    """
    def __init__(self, agent_id: str, skill: str, actions: List[str], metadata: Optional[Dict[str, Any]] = None) -> None:
        meta = metadata.copy() if metadata else {}
        meta['agent_id'] = agent_id
        agent_experience = AgentExperienceItem(skill=skill, actions=actions)
        super().__init__(content=agent_experience, metadata=meta, memory_type="agent_experience")

    @property
    def agent_id(self) -> str:
        return self.metadata['agent_id']

    @property
    def skill(self) -> str:
        return self.content.skill

    @property
    def actions(self) -> List[str]:
        return self.content.actions

    @property
    def embedding_text(self):
        return f"skill:{self.skill}, actions:{self.actions}"

    def to_openai_message(self) -> dict:
        return {
            "role": "system",
            "content": self.content
        }


class UserProfileItem(BaseModel):
    key: str = Field(description="The key of the profile")
    value: Any = Field(description="The value of the profile")

class UserProfile(MemoryItem):
    """
    Represents a user profile key-value pair.
    All custom attributes are stored in content and metadata.
    Args:
        user_id (str): The ID of the user.
        key (str): The profile key.
        value (Any): The profile value.
        metadata (Optional[Dict[str, Any]]): Additional metadata.
    """
    def __init__(self, user_id: str, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        meta = metadata.copy() if metadata else {}
        meta['user_id'] = user_id
        user_profile = UserProfileItem(key=key, value=value)
        super().__init__(content=user_profile, metadata=meta, memory_type="user_profile", **kwargs)

    @property
    def user_id(self) -> str:
        return self.metadata['user_id']

    @property
    def key(self) -> str:
        return self.content.key

    @property
    def value(self) -> Any:
        return self.content.value

    @property
    def item(self) -> UserProfileItem:
        return self.content

    @property
    def embedding_text(self):
        return f"key:{self.key} value:{self.value}"
    
    def to_openai_message(self) -> dict:
        return {
            "role": "system",
            "content": self.content
        }

class Fact(MemoryItem):
    """
    Represents Fact from conversation.
    Args:
        user_id (str): The ID of the user.
        content (str): fact.
        metadata (Optional[Dict[str, Any]]): Additional metadata.
    """
    def __init__(self, user_id: str = None, agent_id: str = None, content: str = None, metadata: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        meta = metadata.copy() if metadata else {}
        if user_id:
            meta['user_id'] = user_id
        elif metadata.get('user_id'):
            meta['user_id'] = metadata.get('user_id')

        if 'memory_type' in kwargs:
            kwargs.pop("memory_type")
        super().__init__(content=content, metadata=meta, memory_type="fact", **kwargs)

    @property
    def key(self) -> str:
        return self.content.key

    @property
    def value(self) -> Any:
        return self.content.value

    @property
    def embedding_text(self):
        return self.content

    def to_openai_message(self) -> dict:
        return {
            "role": "user",
            "content": self.content
        }

class MemorySummary(MemoryItem):
    """
    Represents a memory summary.
    All custom attributes are stored in content and metadata.
    Args:
        item_ids (str): The IDS of the agent.
        summary (str): The summary text.
        metadata (Optional[Dict[str, Any]]): Additional metadata.
    """
    def __init__(self, item_ids: list[str], summary: str, metadata: MessageMetadata, **kwargs) -> None:
        meta = metadata.to_dict
        meta['item_ids'] = item_ids
        meta['role'] = "user"
        super().__init__(content=summary, metadata=meta, memory_type="summary", **kwargs)

    @property
    def summary_item_ids(self):
        return self.metadata['item_ids']

    def to_openai_message(self) -> dict:
        return {
            "role": "user",
            "content": self.content
        }


class ConversationSummary(MemoryItem):
    """
    Represents a conversation summary.
    All custom attributes are stored in content and metadata.
    Args:
        user_id (str): The ID of the user.
        session_id (str): The ID of the session.
        summary (str): The summary text of the conversation.
        metadata (MessageMetadata): Metadata object containing additional information.
    """

    def __init__(self, user_id: str, session_id: str, summary: str, metadata: MessageMetadata, **kwargs) -> None:
        meta = metadata.to_dict
        meta['user_id'] = user_id
        meta['session_id'] = session_id
        super().__init__(content=summary, metadata=meta, memory_type="conversation_summary", **kwargs)

    def to_openai_message(self) -> dict:
        return {
            "role": "assistant",
            "content": self.content
        }


class MemoryMessage(MemoryItem):
    """
    Represents a memory message with role, user, session, task, and agent information.
    Args:
        role (str): The role of the message sender.
        metadata (MessageMetadata): Metadata object containing user, session, task, and agent IDs.
        content (Optional[Any]): Content of the message.
    """
    def __init__(self, role: str, metadata: MessageMetadata, content: Optional[Any] = None, memory_type="message", **kwargs) -> None:
        meta = metadata.to_dict
        meta['role'] = role
        super().__init__(content=content, metadata=meta, memory_type=memory_type, **kwargs)

    @property
    def role(self) -> str:
        return self.metadata['role']

    @property
    def user_id(self) -> str:
        return self.metadata['user_id']

    @property
    def session_id(self) -> str:
        return self.metadata['session_id']

    @property
    def task_id(self) -> str:
        return self.metadata['task_id']

    def set_task_id(self, task_id):
        self.metadata['task_id'] = task_id

    @property
    def agent_id(self) -> str:
        return self.metadata['agent_id']
    
    @abstractmethod
    def to_openai_message(self) -> dict:
        pass

class MemorySystemMessage(MemoryMessage):
    """
    Represents a system message with role and content.
    Args:
        metadata (MessageMetadata): Metadata object containing user, session, task, and agent IDs.
        content (str): The content of the message.
    """
    def __init__(self, content: str, metadata: MessageMetadata, **kwargs) -> None:
        super().__init__(role="system", metadata=metadata, content=content, memory_type="init", **kwargs)

    def to_openai_message(self) -> dict:
        return {
            "role": self.role,
            "content": self.content
        }

    @property
    def embedding_text(self) -> Optional[str]:
        return None


class MemoryHumanMessage(MemoryMessage):
    """
    Represents a human message with role and content.
    Args:
        metadata (MessageMetadata): Metadata object containing user, session, task, and agent IDs.
        content (str): The content of the message.
    """
    def __init__(self, metadata: MessageMetadata, content: Any, memory_type = "init", **kwargs) -> None:
        super().__init__(role="user", metadata=metadata, content=content, memory_type=memory_type, **kwargs)
    
    def to_openai_message(self) -> dict:
        return {
            "role": self.role,
            "content": self.content
        }

class MemoryAIMessage(MemoryMessage):
    """
    Represents an AI message with role and content.
    Args:
        metadata (MessageMetadata): Metadata object containing user, session, task, and agent IDs.
        content (str): The content of the message.
    """
    def __init__(self, content: str, tool_calls: Optional[List[ToolCall]] = [], metadata: MessageMetadata = None, **kwargs) -> None:
        meta = metadata.to_dict
        if tool_calls:
            meta['tool_calls'] = [tool_call.to_dict() for tool_call in tool_calls]
        super().__init__(role="assistant", metadata=MessageMetadata(**meta), content=content, **kwargs)

    @property
    def tool_calls(self) -> List[ToolCall]:
        if "tool_calls" not in self.metadata or not self.metadata['tool_calls']:
            return None
        tc = [ToolCall(**tool_call) for tool_call in self.metadata['tool_calls']]
        return tc if len(tc) > 0 else None
      
    def to_openai_message(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "tool_calls": [tool_call.to_dict() for tool_call in self.tool_calls or []] or None
        }

class MemoryToolMessage(MemoryMessage):
    """
    Represents a tool message with role, content, tool_call_id, and status.
    Args:
        metadata (MessageMetadata): Metadata object containing user, session, task, and agent IDs.
        tool_call_id (str): The ID of the tool call.
        status (Literal["success", "error"]): The status of the tool call.
        content (str): The content of the message.
    """
    def __init__(self, tool_call_id: str, content: Any, status: Literal["success", "error"] = "success", metadata: MessageMetadata = None, **kwargs) -> None:
        metadata.tool_call_id = tool_call_id
        metadata.status = status
        super().__init__(role="tool", metadata=metadata, content=content, **kwargs)

    @property
    def tool_call_id(self) -> str:
        return self.metadata['tool_call_id']

    @property
    def status(self) -> str:
        return self.metadata['status']

    @property
    def embedding_text(self) -> Optional[str]:
        return None

    def to_openai_message(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "tool_call_id": self.tool_call_id,
        }


class LongTermExtractParams(BaseModel):
    session_id: str = Field(description="The ID of the session")
    task_id: Optional[str] = Field(description="The ID of the task")
    memories: List[MemoryItem] = Field(default_factory=list, description="The list of memories to process")

    application_id: Optional[str] = Field(default=None, description="The ID of the application")
    extract_type: Literal["user_profile", "agent_experience"] = Field(description="The type of long-term extract")

    def to_openai_messages(self) -> List[dict]:
        return [memory.to_openai_message() for memory in self.memories]

class UserProfileExtractParams(LongTermExtractParams):
    user_id: Optional[str] = Field(description="The ID of the user")

    def __init__(self, user_id: str, session_id: str, task_id: str, memories: List[MemoryItem] = None, application_id: str = None, **kwargs) -> None:
        kwargs = {
            "user_id": user_id,
            "session_id": session_id,
            "task_id": task_id,
            "memories": memories or [],
            "application_id": application_id,
            "extract_type": "user_profile",
            **kwargs
        }
        super().__init__(**kwargs)

    model_config = ConfigDict(extra="allow")

class AgentExperienceExtractParams(LongTermExtractParams):
    agent_id: str = Field(default=None, description="The ID of the agent")

    def __init__(self, agent_id: str, session_id: str, task_id: str, memories: List[MemoryItem] = None,
                 application_id: str = None,**kwargs) -> None:
        super().__init__(session_id=session_id,
                         task_id=task_id,
                         memories=memories,
                         application_id=application_id,
                         extract_type="agent_experience", **kwargs)
        self.agent_id = agent_id

    model_config = ConfigDict(extra="allow")

class LongTermMemoryTriggerParams(BaseModel):
    """
    Metadata for memory messages, including user, session, task, and agent information.
    Args:
        user_id (str): The ID of the user.
        session_id (str): The ID of the session.
        task_id (str): The ID of the task.
        agent_id (str): The ID of the agent.
    """
    agent_id: str = Field(default=None, description="The ID of the agent")
    session_id: str = Field(default=None, description="The ID of the session")
    task_id: str = Field(default=None, description="The ID of the task")
    user_id: Optional[str] = Field(default=None, description="The ID of the user")
    application_id: Optional[str] = Field(default="default", description="The ID of the application, namespace for memory")
    force: Optional[bool] = Field(default=False, description="Whether to force trigger long-term memory")

    model_config = ConfigDict(extra="allow")