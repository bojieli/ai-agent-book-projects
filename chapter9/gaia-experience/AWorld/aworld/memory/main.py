# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import abc
import json
import traceback
from typing import Optional, Tuple

from aworld.core.memory import MemoryBase, MemoryItem, MemoryStore, MemoryConfig, AgentMemoryConfig
from aworld.logs.util import logger
from aworld.memory.embeddings.base import EmbeddingsResult, EmbeddingsMetadata
from aworld.memory.embeddings.factory import EmbedderFactory
from aworld.memory.longterm import DefaultMemoryOrchestrator
from aworld.memory.models import AgentExperience, LongTermMemoryTriggerParams, MemoryToolMessage, MessageMetadata, \
    UserProfileExtractParams, \
    AgentExperienceExtractParams, UserProfile, MemorySummary, MemoryAIMessage, Fact
from aworld.memory.vector.factory import VectorDBFactory
from aworld.models.llm import acall_llm_model
from aworld.models.utils import num_tokens_from_messages

AWORLD_MEMORY_EXTRACT_NEW_SUMMARY = """
You are presented with a user task, a conversion that may contain the answer, and a previous conversation summary. 
Please read the conversation carefully and extract new information from the conversation that helps to solve user task
<guide>
1. if current conversion contain answer of task or related information, must include it in the summary.
2. record key step of current conversion. such visited web page, use tools information, etc. example:
    - step_info:
       - step_content: the description of step, must be a complete sentence and keep information params of step.
        - use tools information:
         - tool_name: search
         - tool_input: {{
            "query": "python"
          }}
       - step_result: the result of step and evidence information, such link of visited web page for slove task

3. In your summary, aim to reduce unnecessary information, but make sure your summarized content still provides enough details for the task and does not lose any important information.
<guide>


<user_task> {user_task} </user_task>
<existed_summary> {existed_summary} </existed_summary>
<conversation> {to_be_summary} </conversation>

## output new summary: 
"""
AWORLD_MEMORY_UPDATE_SUMMARY = """
You are presented with a user task, a conversion that may contain the answer, and a previous conversation summary. 
Please read the conversation carefully and extract new information from the conversation that helps to solve user task, while retaining all relevant details from the previous memory.
<user_task> {user_task} </user_task>
<existed_summary> {existed_summary} </existed_summary>
<conversation> {to_be_summary} </conversation>

## result summary: 
"""

class InMemoryMemoryStore(MemoryStore):
    def __init__(self):
        self.memory_items = []

    def add(self, memory_item: MemoryItem):
        self.memory_items.append(memory_item)

    def get(self, memory_id) -> Optional[MemoryItem]:
        return next((item for item in self.memory_items if item.id == memory_id), None)

    def get_first(self, filters: dict = None) -> Optional[MemoryItem]:
        """Get the first memory item."""
        filtered_items = self.get_all(filters)
        if len(filtered_items) == 0:
            return None
        return filtered_items[0]

    def total_rounds(self, filters: dict = None) -> int:
        """Get the total number of rounds."""
        return len(self.get_all(filters))

    def get_all(self, filters: dict = None) -> list[MemoryItem]:
        """Filter memory items based on filters."""
        filtered_items = [item for item in self.memory_items if self._filter_memory_item(item, filters)]
        return filtered_items

    def _filter_memory_item(self, memory_item: MemoryItem, filters: dict = None) -> bool:
        if memory_item.deleted:
            return False
        if filters is None:
            return True
        if filters.get('application_id') is not None:
            if memory_item.application_id is None:
                return False
            if memory_item.application_id != filters['application_id']:
                return False
        if filters.get('user_id') is not None:
            if memory_item.user_id is None:
                return False
            if memory_item.user_id != filters['user_id']:
                return False
        if filters.get('agent_id') is not None:
            if memory_item.agent_id is None:
                return False
            if memory_item.agent_id != filters['agent_id']:
                return False
        if filters.get('agent_name') is not None:
            if memory_item.agent_id is None:
                return False
            if memory_item.agent_id != filters['agent_id']:
                return False
        if filters.get('task_id') is not None:
            if memory_item.task_id is None:
                return False
            if memory_item.task_id != filters['task_id']:
                return False
        if filters.get('session_id') is not None:
            if memory_item.session_id is None:
                return False
            if memory_item.session_id != filters['session_id']:
                return False
        if filters.get('tool_call_id') is not None:
            if memory_item.metadata.get("tool_call_id") is None:
                return False
            if memory_item.metadata.get("tool_call_id") != filters['tool_call_id']:
                return False
        if filters.get('memory_type') is not None:
            if memory_item.memory_type is None:
                return False
            elif isinstance(filters['memory_type'], list) and memory_item.memory_type not in filters['memory_type']:
                    return False
            elif isinstance(filters['memory_type'], str) and memory_item.memory_type != filters['memory_type']:
                return False
        return True

    def get_last_n(self, last_rounds, filters: dict = None) -> list[MemoryItem]:
        return self.get_all(filters=filters)[-last_rounds:]

    def update(self, memory_item: MemoryItem):
        for index, item in enumerate(self.memory_items):
            if item.id == memory_item.id:
                self.memory_items[index] = memory_item
                break

    def delete(self, memory_id):
        exists = self.get(memory_id)
        if exists:
            exists.deleted = True

    def delete_items(self, message_types: list[str], session_id: str, task_id: str, filters: dict = None):
        for item in self.memory_items:
            if item.memory_type in message_types and item.session_id == session_id and item.task_id == task_id:
                item.deleted = True

    def history(self, memory_id) -> list[MemoryItem] | None:
        exists = self.get(memory_id)
        if exists:
            return exists.histories
        return None

MEMORY_HOLDER = {}
class MemoryFactory:

    @classmethod
    def init(cls, custom_memory_store: MemoryStore = None, config: MemoryConfig = MemoryConfig(provider="aworld")):
        if custom_memory_store:
            MEMORY_HOLDER["instance"] = AworldMemory(
                memory_store=custom_memory_store,
                config=config
            )
        else:
            MEMORY_HOLDER["instance"] = AworldMemory(
                memory_store=InMemoryMemoryStore(),
                config=config
            )
        logger.info(f"Memory init success")


    @classmethod
    def instance(cls) -> "MemoryBase":
        """
        Get the in-memory memory instance.
        Returns:
            MemoryBase: In-memory memory instance.
        """
        if MEMORY_HOLDER.get("instance"):
            logger.info(f"instance use cached memory instance")
            return MEMORY_HOLDER["instance"]
        MEMORY_HOLDER["instance"] =  MemoryFactory.from_config(
            config=MemoryConfig(provider="aworld"),
            memory_store=InMemoryMemoryStore()
        )
        logger.info(f"instance use new memory instance")
        return MEMORY_HOLDER["instance"]

    @classmethod
    def from_config(cls, config: MemoryConfig, memory_store: MemoryStore = None) -> "MemoryBase":
        """
        Initialize a Memory instance from a configuration dictionary.

        Args:
            config (dict): Configuration dictionary.

        Returns:
            MemoryBase: Memory instance.
        """
        if config.provider == "aworld":
            logger.info("🧠 [MEMORY]setup memory store: aworld")
            return AworldMemory(
                memory_store=memory_store or InMemoryMemoryStore(),
                config=config
            )
        elif config.provider == "mem0":
            from aworld.memory.mem0.mem0_memory import Mem0Memory
            logger.info("🧠 [MEMORY]setup memory store: mem0")
            return Mem0Memory(
                memory_store=memory_store or InMemoryMemoryStore(),
                config=config
            )
        else:
            raise ValueError(f"Invalid memory store type: {config.get('memory_store')}")


class Memory(MemoryBase):
    __metaclass__ = abc.ABCMeta

    def __init__(self, memory_store: MemoryStore, config: MemoryConfig, **kwargs):
        self.memory_store = memory_store
        self.config = config

        # Initialize llm_model components
        self._llm_instance = config.get_llm_instance()

        # Initialize embedding and vector database components
        self._embedder = EmbedderFactory.get_embedder(config.embedding_config)
        self._vector_db = VectorDBFactory.get_vector_db(config.vector_store_config)

        # Initialize long-term memory components
        self.memory_orchestrator = DefaultMemoryOrchestrator(
            self._llm_instance,
            embedding_model=self._embedder,
            memory=self
        )

    @property
    def default_llm_instance(self):
        if not self._llm_instance:
            raise ValueError("LLM instance is not initialized")
        return self._llm_instance


    def _build_history_context(self, messages) -> str:
        """Build the history context string from a list of messages.

        Args:
            messages: List of message objects with 'role', 'content', and optional 'tool_calls'.
        Returns:
            Concatenated context string.
        """
        history_context = ""
        for item in messages:
            history_context += (f"\n\n{item['role']}: {item['content']}, "
                                f"{'tool_calls:' + json.dumps(item['tool_calls']) if 'tool_calls' in item and item['tool_calls'] else ''}")
        return history_context

    async def _call_llm_summary(self, summary_messages: list, agent_memory_config: AgentMemoryConfig) -> str:
        """Call LLM to generate summary and log the process.

        Args:
            summary_messages: List of messages to send to LLM.
        Returns:
            Summary content string.
        """
        llm_response = await acall_llm_model(
            self.default_llm_instance,
            messages=summary_messages,
            # model_name=agent_memory_config.summary_model,
            stream=False,
        )
        logger.debug(f"🧠 [MEMORY:short-term] [Summary] Creating summary memory, history messages: {summary_messages}")
        return llm_response.content

    def _get_parsed_history_messages(self, history_items: list[MemoryItem]) -> list[dict]:
        """Get and format history messages for summary.

        Args:
            history_items: list[MemoryItem]
        Returns:
            List of parsed message dicts
        """
        parsed_messages = [
            {
                'role': message.metadata['role'],
                'content': message.content,
                'tool_calls': message.metadata.get('tool_calls') if message.metadata.get('tool_calls') else None
            }
            for message in history_items]
        return parsed_messages

    async def async_gen_multi_rounds_summary(self, to_be_summary: list[MemoryItem], agent_memory_config: AgentMemoryConfig) -> str:
        logger.info(
            f"🧠 [MEMORY:short-term] [Summary] Creating summary memory, history messages")
        if len(to_be_summary) == 0:
            return ""
        parsed_messages = self._get_parsed_history_messages(to_be_summary)
        history_context = self._build_history_context(parsed_messages)

        summary_messages = [
            {"role": "user", "content": agent_memory_config.summary_prompt.format(context=history_context)}
        ]

        return await self._call_llm_summary(summary_messages)

    async def async_gen_summary(self, filters: dict, last_rounds: int, agent_memory_config: AgentMemoryConfig) -> str:
        """A tool for summarizing the conversation history."""

        logger.info(f"🧠 [MEMORY:short-term] [Summary] Creating summary memory, history messages [filters -> {filters}, "
                    f"last_rounds -> {last_rounds}]")
        history_items = self.memory_store.get_last_n(last_rounds, filters=filters)
        if len(history_items) == 0:
            return ""
        parsed_messages = self._get_parsed_history_messages(history_items)
        history_context = self._build_history_context(parsed_messages)

        summary_messages = [
            {"role": "user", "content": agent_memory_config.summary_prompt.format(context=history_context)}
        ]

        return await self._call_llm_summary(summary_messages)

    async def async_gen_cur_round_summary(self, to_be_summary: MemoryItem, filters: dict, last_rounds: int, agent_memory_config: AgentMemoryConfig) -> str:
        if not agent_memory_config.enable_summary or len(to_be_summary.content) < agent_memory_config.summary_single_context_length:
            return to_be_summary.content

        logger.info(f"🧠 [MEMORY:short-term] [Summary] Creating summary memory, history messages [filters -> {filters}, "
                    f"last_rounds -> {last_rounds}]: to be summary content is {to_be_summary.content}")
        history_items = self.memory_store.get_last_n(last_rounds, filters=filters)
        if len(history_items) == 0:
            return ""
        parsed_messages = self._get_parsed_history_messages(history_items)

        # Append the to_be_summary
        parsed_messages.append({
            "role": to_be_summary.metadata['role'],
            "content": f"{to_be_summary.content}",
            'tool_call_id': to_be_summary.metadata['tool_call_id'],
        })
        history_context = self._build_history_context(parsed_messages)

        summary_messages = [
            {"role": "user", "content": agent_memory_config.summary_prompt.format(context=history_context)}
        ]

        return await self._call_llm_summary(summary_messages)

    def search(self, query, limit=100, memory_type="message", threshold=0.8, filters=None) -> Optional[list[MemoryItem]]:
        pass

    async def add(self, memory_item: MemoryItem, filters: dict = None, agent_memory_config: AgentMemoryConfig = None):
        await self._add(memory_item, filters, agent_memory_config)
        # self.post_add(memory_item, filters, memory_config)

    @abc.abstractmethod
    async def _add(self, memory_item: MemoryItem, filters: dict = None, agent_memory_config: AgentMemoryConfig = None):
        pass

    async def post_add(self, memory_item: MemoryItem, filters: dict = None, agent_memory_config: AgentMemoryConfig = None):
        try:
            await self.post_process_long_terms(memory_item, filters, agent_memory_config)
        except Exception as err:
            logger.warning(f"🧠 [MEMORY:long-term] Error during long-term memory processing: {err}, traceback is {traceback.format_exc()}")

    async def post_process_long_terms(self, memory_item: MemoryItem, filters: dict = None, agent_memory_config: AgentMemoryConfig = None):
        """Post process long-term memory."""
        # check if memory_item is "message"
        if memory_item.memory_type != 'message':
            return

        if not agent_memory_config:
            return

        # check if long-term memory is enabled
        if not agent_memory_config.enable_long_term:
            return

        # check if long-term memory config is valid
        long_term_config = agent_memory_config.long_term_config
        if not long_term_config:
            return

        await self.trigger_short_term_memory_to_long_term(LongTermMemoryTriggerParams(
            agent_id=memory_item.agent_id,
            session_id=memory_item.session_id,
            task_id=memory_item.task_id,
            user_id=memory_item.user_id,
            application_id=memory_item.application_id
        ), agent_memory_config)

    async def trigger_short_term_memory_to_long_term(self, params: LongTermMemoryTriggerParams, agent_memory_config: AgentMemoryConfig = None):
        logger.info(f"🧠 [MEMORY:long-term] Trigger short-term memory to long-term memory, params is {params}")
        if not agent_memory_config:
            return

        # check if long-term memory is enabled
        if not agent_memory_config.enable_long_term:
            return

        # check if long-term memory config is valid
        long_term_config = agent_memory_config.long_term_config
        if not long_term_config:
            return

        # get all memories of current task
        task_memory_items = self.memory_store.get_all({
            'memory_type': 'message',
            'agent_id': params.agent_id,
            'application_id': params.application_id,
            'session_id': params.session_id,
            'task_id': params.task_id
        })

        task_params = []

        # Check if user profile extraction is enabled
        if long_term_config.extraction.enable_user_profile_extraction:
            if params.user_id:
                user_profile_task_params = UserProfileExtractParams(
                    user_id=params.user_id,
                    session_id=params.session_id,
                    task_id=params.task_id,
                    application_id=params.application_id,
                    memories=task_memory_items
                )
                task_params.append(user_profile_task_params)
                logger.info(f"🧠 [MEMORY:long-term] add user profile extraction task params is {user_profile_task_params}")
            else:
                logger.warning(f"🧠 [MEMORY:long-term] memory_item.user_id is None, skip user profile extraction")

        # Check if agent experience extraction is enabled
        if long_term_config.extraction.enable_agent_experience_extraction:
            if params.agent_id:
                agent_experience_task_params = AgentExperienceExtractParams(
                    agent_id=params.agent_id,
                    session_id=params.session_id,
                    task_id=params.task_id,
                    application_id=params.application_id,
                    memories=task_memory_items
                )
                task_params.append(agent_experience_task_params)
                logger.debug(f"🧠 [MEMORY:long-term] add agent experience extraction task params is {agent_experience_task_params}")
            else:
                logger.warning(
                    f"🧠 [MEMORY:long-term] memory_item.agent_id is None, skip agent experience extraction")

        await self.memory_orchestrator.create_longterm_processing_tasks(task_params, agent_memory_config.long_term_config, params.force)

    async def retrival_user_profile(self, user_id: str, user_input: str, threshold: float = 0.5, limit: int = 3, filters: dict = None) -> Optional[list[UserProfile]]:
        if not filters:
            filters = {}

        return self.search(user_input, limit=limit,memory_type='user_profile',threshold=threshold, filters={
            'user_id': user_id,
            **filters
        })

    async def retrival_facts(self, user_id: str, user_input: str, threshold: float = 0.5, limit: int = 3, filters: dict = None) -> Optional[list[Fact]]:
        if not filters:
            filters = {}

        return self.search(user_input, limit=limit,memory_type='fact',threshold=threshold, filters={
            'user_id': user_id,
            **filters
        })
        

    async def retrival_agent_experience(self, agent_id: str, user_input: str, threshold: float = 0.5, limit: int = 3, filters: dict = None) -> Optional[list[AgentExperience]]:
        if not filters:
            filters = {}
        return self.search(user_input, limit=limit, memory_type='agent_experience',threshold=threshold, filters={
            'agent_id': agent_id,
            **filters
        })

    async def retrival_similar_user_messages_history(self, user_id: str, user_input: str, threshold: float = 0.5, limit: int = 10, filters: dict = None) -> Optional[list[MemoryItem]]:
        if not filters:
            filters = {}
        return self.search(user_input, limit=limit, memory_type='message', threshold=threshold, filters={
            'role': 'user',
            'user_id': user_id,
            **filters
        })
    

    def delete(self, memory_id):
        pass

    def update(self, memory_item: MemoryItem):
        pass

class AworldMemory(Memory):
    def __init__(self, memory_store: MemoryStore, config: MemoryConfig,  **kwargs):
        super().__init__(memory_store=memory_store, config=config, **kwargs)
        self.summary = {}

    def _filter_incomplete_message_pairs(self, message_items: list[MemoryItem]) -> list[MemoryItem]:
        """
        Filter out incomplete message pairs to ensure only complete [ai, tool] message pair sequences are retained.
        
        For sequence [ai,tool,ai,tool,ai,tool,ai,tool,tool,ai,tool,tool,tool],
        identify the complete subsequence [ai,tool,ai,tool,ai,tool,ai,tool,tool],
        i.e., remove the incomplete part in the last group [ai,tool,tool,tool].

        Args:
            message_items: List of message items

        Returns:
            Filtered message items list, retaining only complete [ai, tool] pairs
        """
        if len(message_items) < 2:
            return message_items

        # Find the last AI message in the sequence
        last_ai_index = -1
        for i in range(len(message_items) - 1, -1, -1):
            if isinstance(message_items[i], MemoryAIMessage):
                last_ai_index = i
                break
        
        # If no AI message found, return empty list
        if last_ai_index == -1:
            return []
        
        # Remove everything from the last AI message onwards
        # This removes the last incomplete [ai, tool, tool, ...] group
        return message_items[:last_ai_index]

    async def _add(self, memory_item: MemoryItem, filters: dict = None, agent_memory_config: AgentMemoryConfig = None):
        self.memory_store.add(memory_item)

        # save to vector store
        self._save_to_vector_db(memory_item)

        # Check if we need to create or update summary
        if agent_memory_config and agent_memory_config.enable_summary:
            if memory_item.memory_type == "message":
                await self._summary_agent_task_memory(memory_item, agent_memory_config)

    async def _summary_agent_task_memory(self, memory_item: MemoryItem, agent_memory_config: AgentMemoryConfig):
        # obtain assistant un summary messages

        # get init messages
        agent_task_total_message = self.get_all(
            filters={
                "agent_id": memory_item.agent_id,
                "session_id": memory_item.session_id,
                "task_id": memory_item.task_id,
                "memory_type": ["init","message","summary"]
            }
        )
        to_be_summary_items = [item for item in agent_task_total_message if item.memory_type == "message" and not item.has_summary]

        # 序列中删除最后一组完整的 [ai,tool] 组合
        to_be_summary_items = self._filter_incomplete_message_pairs(to_be_summary_items)

        check_need_summary,trigger_reason = self._check_need_summary(to_be_summary_items, agent_memory_config)
        logger.info(f"🧠 [MEMORY:short-term] [Summary] check_need_summary: {check_need_summary}, trigger_reason: {trigger_reason}")

        if not check_need_summary:
            return

        existed_summary_items = [item for item in agent_task_total_message if item.memory_type == "summary"]
        user_task_items = [item for item in agent_task_total_message if item.memory_type == "init"]
        # generate summary
        summary_content = await self._gen_multi_rounds_summary(user_task_items, existed_summary_items, to_be_summary_items, agent_memory_config)
        logger.debug(f"🧠 [MEMORY:short-term] [Summary] summary_content: {summary_content}")

        summary_metadata = MessageMetadata(
            agent_id=memory_item.agent_id,
            agent_name=memory_item.agent_name,
            session_id=memory_item.session_id,
            task_id=memory_item.task_id,
            user_id=memory_item.user_id
        )
        summary_memory = MemorySummary(
            item_ids=[item.id for item in to_be_summary_items],
            summary=summary_content,
            metadata=summary_metadata,
            created_at=to_be_summary_items[0].created_at
        )

        # add summary to memory
        self.memory_store.add(summary_memory)

        # mark memory item summary flag
        for summary_item in to_be_summary_items:
            summary_item.mark_has_summary()
            self.memory_store.update(summary_item)
        logger.info(f"🧠 [MEMORY:short-term] [Summary] [{trigger_reason}]Creating summary memory finished: content is {summary_content[:100]}")


    def _check_need_summary(self, to_be_summary_items: list[MemoryItem], agent_memory_config: AgentMemoryConfig) -> Tuple[bool,str]:
        if len(to_be_summary_items) <= 0:
            return False, "EMPTY"
        if isinstance(to_be_summary_items[-1], MemoryAIMessage):
            if to_be_summary_items[-1].tool_calls and len(to_be_summary_items[-1].tool_calls) > 0:
                return False,"last message has tool_calls"
        if len(to_be_summary_items) == 0:
            return False, "items is empty"
        if len(to_be_summary_items) >= agent_memory_config.summary_rounds:
            return True, "summary_rounds"
        if num_tokens_from_messages([item.to_openai_message() for item in to_be_summary_items]) > agent_memory_config.summary_context_length:
            return True, "summary_context_length"
        return False, "unknown"

    async def _gen_multi_rounds_summary(self, user_task_items: list[MemoryItem], existed_summary_items: list[MemorySummary],
                                        to_be_summary_items: list[MemoryItem], agent_memory_config: AgentMemoryConfig) -> str:
        
        if len(to_be_summary_items) == 0:
            return ""

        # get user task, existed summary, to be summary
        user_task = [{"role": item.metadata['role'], "content": item.content} for item in user_task_items]
        existed_summary = [{"summary_item_ids": item.summary_item_ids, "content": item.content} for item in existed_summary_items]
        to_be_summary = [{"role": item.metadata['role'], "content": item.content} for item in to_be_summary_items]

        # generate summary
        summary_messages = [
            {
                "role": "user", 
                "content": AWORLD_MEMORY_EXTRACT_NEW_SUMMARY.format(
                    user_task=user_task,
                    existed_summary=existed_summary,
                    to_be_summary=to_be_summary
                )
            }
        ]
        llm_summary = await self._call_llm_summary(summary_messages, agent_memory_config)
        tool_use_content = "\n\n the following is the tool use history:\n"
        for item in to_be_summary_items:
            if item.metadata.get('summary_content'):
                tool_use_content += f"{item.metadata.get('summary_content', '')}\n"

        return f"{llm_summary}{tool_use_content}"




    def _save_to_vector_db(self, memory_item: MemoryItem):
        try:
            if not memory_item.embedding_text:
                logger.debug(f"memory_item.embedding_text is None, skip save to vector store")
                return
            if self._vector_db and self._embedder:
                embedding = self._embedder.embed_query(memory_item.embedding_text)
                # save to vector store
                embedding_meta = EmbeddingsMetadata(
                    memory_id=memory_item.id,
                    agent_id = memory_item.agent_id,
                    session_id = memory_item.session_id,
                    task_id = memory_item.task_id,
                    user_id = memory_item.user_id,
                    application_id = memory_item.application_id,
                    memory_type=memory_item.memory_type,
                    created_at=memory_item.created_at,
                    updated_at=memory_item.updated_at,
                    embedding_model=self.config.embedding_config.model_name,
                )
                embedding_item= EmbeddingsResult(embedding = embedding, content=memory_item.embedding_text, metadata=embedding_meta)

                self._vector_db.insert(self.config.vector_store_config.config['collection_name'], [embedding_item])
            else:
                logger.warning(f"memory_store or embedder is None, skip save to vector store")
        except Exception as err:
            logger.warning(f"save_to_vector, failed is {err}")

    def update(self, memory_item: MemoryItem):
        self.memory_store.update(memory_item)

    def delete(self, memory_id):
        self.memory_store.delete(memory_id)

    def delete_items(self, message_types: list[str], session_id: str, task_id: str, filters: dict = None):
        self.memory_store.delete_items(message_types, session_id, task_id, filters)

    def get(self, memory_id) -> Optional[MemoryItem]:
        return self.memory_store.get(memory_id)

    def get_all(self, filters: dict = None) -> list[MemoryItem]:
        return self.memory_store.get_all(filters=filters)

    def get_last_n(self, last_rounds, filters: dict = None, agent_memory_config: AgentMemoryConfig = None) -> list[MemoryItem]:
        """
        Retrieve the last N rounds of conversation memory, including initialization messages, unsummarized messages, and summary messages.

        Workflow:
        1. Fetch all relevant messages (init, message, summary types)
        2. Extract initialization messages (init type)
        3. Get unsummarized messages (message type not summarized) and summary messages (summary type)
        4. If total messages <= requested rounds, return all messages
        5. Otherwise, return the last N rounds while ensuring tool message integrity

        Args:
            last_rounds (int): Number of recent message rounds to retrieve
            filters (dict): Filter conditions, must contain agent_id, session_id, task_id
            agent_memory_config (AgentMemoryConfig): Agent memory configuration

        Returns:
            list[MemoryItem]: Returns a combined list of memories in the following order:
                1. Initialization messages (if any)
                2. Last N rounds of unsummarized messages and summary messages

        Note:
            - When the most recent message is a tool message, may return more than last_rounds 
              messages to ensure tool call integrity
            - Returns empty list if filters is empty
        """
        if last_rounds < 0:
            return []
        
        if not filters:
            return []
        
        # get all messages
        agent_task_total_message = self.get_all(
            filters={
                "agent_id": filters.get('agent_id'),
                "session_id": filters.get('session_id'),
                "task_id": filters.get('task_id'),
                "memory_type": ["init", "message", "summary"]
            }
        )

        init_items = [item for item in agent_task_total_message if item.memory_type == "init"]

        # if last_rounds is 0, return init_items
        if last_rounds == 0:
            return init_items
        
        # get unsummarized messages and summary messages
        result_items = [item for item in agent_task_total_message if (item.memory_type == "message" and not item.has_summary) or (item.memory_type == 'summary')]

        # if total messages <= requested rounds, return all messages
        if len(result_items) <= last_rounds:
            result_items =  init_items + result_items
        else:
            # Ensure tool message completeness: LLM API requires the preceding tool_calls message 
            # to be included when processing a tool message. If the first message in our window 
            # is a tool message, we need to expand the window to include its associated tool_calls.
            while isinstance(result_items[-last_rounds], MemoryToolMessage):
                last_rounds = last_rounds + 1
            result_items = init_items + result_items[-last_rounds:]

        result_items.sort(key=lambda x: x.created_at, reverse=False)
        return result_items



    def search(self, query, limit=100, memory_type="message", threshold=0.8, filters=None) -> Optional[list[MemoryItem]]:
        if self._vector_db:
            if not filters:
                filters = {}
            filters['memory_type'] = memory_type
            embedding = self._embedder.embed_query(query)
            results = self._vector_db.search(self.config.vector_store_config.config['collection_name'], [embedding], filters, threshold, limit)
            memory_items = []
            if results and results.docs:
                for result in results.docs:
                    memory_item = self.memory_store.get(result.metadata.memory_id)
                    if memory_item:
                        memory_item.metadata['score'] = result.score
                        memory_items.append(memory_item)
                return memory_items
        else:
            logger.warning(f"vector_db is None, skip search")
        return []


