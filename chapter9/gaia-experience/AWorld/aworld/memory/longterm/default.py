# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import asyncio
import json
import traceback
from datetime import datetime
from typing import Any, List, Literal, Optional, Tuple

from aworld.core.memory import MemoryItem, LongTermConfig, MemoryStore, MemoryBase
from aworld.models.llm import LLMModel, acall_llm_model
from .base import MemoryGungnir, MemoryOrchestrator, MemoryProcessingTask, MemoryProcessingResult
from ..models import AgentExperience, LongTermExtractParams, UserProfile
from ...logs.util import logger


class DefaultMemoryGungnir(MemoryGungnir):
    """
    Default implementation of MemoryGungnir.
    """

    def __init__(self, llm_instance: LLMModel):
        super().__init__(llm_instance)

    async def process_memory_task(self, task: MemoryProcessingTask) -> MemoryProcessingResult:
        try:
            return await self._process_memory_task(task)
        except Exception as e:
            logger.error(
                f"🧠 [MEMORY:long-term] Error processing memory task:{task.memory_task_id} failed: {e}" + traceback.format_exc())
            return MemoryProcessingResult(
                success=False,
                error_message=str(e)
            )

    async def _process_memory_task(self, task: MemoryProcessingTask) -> MemoryProcessingResult:

        logger.debug(
            f"🧠 [MEMORY:long-term] Processing memory task start:{task.memory_task_id} with task_type:{task.task_type}")
        # 1. extract long-term memories
        user_profiles = []
        agent_experiences = []
        if task.task_type == "agent_experience":
            agent_experiences = await self._extract_agent_experience(task)
        elif task.task_type == "user_profile":
            user_profiles = await self._extract_user_profile(task)
        else:
            raise ValueError(f"Invalid task type: {task.task_type}")

        # 2. return the result
        result = MemoryProcessingResult(
            success=True,
            user_profiles=user_profiles,
            agent_experiences=agent_experiences,
            finished_at=datetime.now().isoformat(),
        )
        logger.debug(
            f"🧠 [MEMORY:long-term] Processing memory task end:{task.memory_task_id} with task_type:{task.task_type}")
        return result

    async def _extract_data_from_llm(self, task: MemoryProcessingTask, prompt: str, parser: callable) -> Optional[List[Any]]:
        messages = [{"role": "user", "content": prompt}]
        try:
            llm_response = await acall_llm_model(self._llm_instance, messages=messages)
            logger.info(f"🧠 [MEMORY:long-term] Extracted data for task {task.memory_task_id}: {llm_response}")
            result = json.loads(llm_response.content.replace("```json", "").replace("```", ""))
            parsed_data = parser(result, task)
            logger.info(f"🧠 [MEMORY:long-term] Parsed data for task {task.memory_task_id}: {parsed_data}")
            return parsed_data
        except Exception as e:
            logger.error(f"🧠 [MEMORY:long-term] Error extracting data for task {task.memory_task_id}: {e}" + traceback.format_exc())
            return None

    async def _extract_agent_experience(self, task: MemoryProcessingTask) -> Optional[List[AgentExperience]]:
        to_be_extracted_messages = task.extract_params.to_openai_messages()
        agent_experiences_prompt = task.longterm_config.get_agent_experience_prompt(
            messages=str(to_be_extracted_messages))

        def parse_agent_experience(result, task):
            return [AgentExperience(
                agent_id=task.extract_params.agent_id,
                skill=result['skill'],
                actions=result['actions']
            )]

        return await self._extract_data_from_llm(task, agent_experiences_prompt, parse_agent_experience)

    async def _extract_user_profile(self, task: MemoryProcessingTask) -> Optional[List[UserProfile]]:
        to_be_extracted_messages = task.extract_params.to_openai_messages()
        user_profile_prompt = task.longterm_config.get_user_profile_prompt(
            messages=str(to_be_extracted_messages))

        def parse_user_profile(result, task):
            user_profiles = []
            profile_entries = result if isinstance(result, list) else [result]
            for profile_entry in profile_entries:
                if not isinstance(profile_entry, dict) or 'key' not in profile_entry or 'value' not in profile_entry:
                    logger.warning(f"🧠 [MEMORY:long-term] Invalid profile entry format: {profile_entry}")
                    continue
                user_profiles.append(UserProfile(
                    user_id=task.extract_params.user_id,
                    key=profile_entry['key'],
                    value=profile_entry['value']
                ))
            return user_profiles

        return await self._extract_data_from_llm(task, user_profile_prompt, parse_user_profile)


class DefaultMemoryOrchestrator(MemoryOrchestrator):
    """
    Simple implementation of MemoryOrchestrator that provides basic memory processing decisions.
    This orchestrator evaluates trigger conditions and creates processing tasks based on configuration.
    """

    def __init__(self,
                 llm_instance: LLMModel,
                 embedding_model: Optional[Any] = None,
                 memory: "MemoryBase" = None
                 ) -> None:
        """
        Initialize the simple memory orchestrator.
        
        Args:
            llm_instance: LLM model instance for processing
        """
        super().__init__(llm_instance, embedding_model)
        self.memory_gungnir = DefaultMemoryGungnir(llm_instance)
        self.memory_tasks: List[MemoryProcessingTask] = []
        self.memory = memory

    async def create_longterm_processing_tasks(self, task_params: list[LongTermExtractParams],
                                               longterm_config: LongTermConfig,
                                               force: bool = False) -> None:
        for task_param in task_params:
            await self._create_longterm_processing_task(task_param, longterm_config, force)

    async def _create_longterm_processing_task(self, extract_param: LongTermExtractParams,
                                               longterm_config: LongTermConfig
                                               , force: bool = False) -> None:
        """
        Check if long-term memory processing should be triggered and process if necessary.

        Args:
            extract_param: Long-term extract parameters
            longterm_config: Long-term memory configuration settings
        """
        try:
            # Get all current memory items
            memory_task = self._create_memory_task(
                extract_param,
                longterm_config=longterm_config,
                force=force
            )

            if memory_task:
                logger.info(f"🧠 [MEMORY:long-term] Created processing task {memory_task.memory_task_id} "
                            f"with trigger_reason: {memory_task.metadata.get('trigger_reason', 'unknown')}")
                await self._add_memory_task(memory_task)
                if longterm_config.processing.enable_background_processing:
                    asyncio.create_task(self._process_longterm_memory_task(memory_task))
                else:
                    asyncio.run(self._process_longterm_memory_task(memory_task))
        except Exception as e:
            logger.warning(
                f"🧠 [MEMORY:long-term] Error during long-term memory processing check: {e}" + traceback.format_exc())

    def _should_process_memory(
            self,
            extract_param: LongTermExtractParams,
            longterm_config: LongTermConfig
    ) -> Tuple[bool, str]:

        # 1.Check message count threshold
        if self._check_message_count_threshold(extract_param.memories, longterm_config):
            return True, "message_count"

        # 2.Check content importance if enabled
        if longterm_config.trigger.enable_importance_trigger:
            if self._check_content_importance(extract_param.memories, longterm_config):
                return True, "content_importance"

        return False, "not_trigger"

    def _create_memory_task(
            self,
            extract_param: LongTermExtractParams,
            longterm_config: LongTermConfig,
            force: bool = False
    ) -> Optional[MemoryProcessingTask]:
        """
        Create a memory processing task from the given memory items.
        
        Args:
            extract_param: Long-term extract parameters
            longterm_config: Long-term memory configuration settings
            
        Returns:
            Memory processing task
        """
        if not force:
            # Check if processing should be triggered
            should_process, reason = self._should_process_memory(
                extract_param,
                longterm_config=longterm_config
            )
            logger.debug(
                f"🧠 [MEMORY:long-term] [DefaultMemoryOrchestrator] flag of should_process: {should_process}, reason: {reason}")

            if not should_process:
                logger.debug(
                    f"🧠 [MEMORY:long-term] [DefaultMemoryOrchestrator] not trigger memory task#{extract_param.extract_type}[{extract_param.session_id}:{extract_param.task_id}]")
                return None
        else:
            reason = "force"

        # create long-term memory task
        memory_task = MemoryProcessingTask(
            task_type=extract_param.extract_type,
            extract_params=extract_param,
            longterm_config=longterm_config
        )

        # Add metadata based on configuration
        memory_task.metadata.update({
            "trigger_reason": reason,
            'config_snapshot': {
                'message_threshold': longterm_config.trigger.message_count_threshold,
                'user_profile_extraction': longterm_config.extraction.enable_user_profile_extraction,
                'agent_experience_extraction': longterm_config.extraction.enable_agent_experience_extraction
            }
        })

        logger.info(
            f"🧠 [MEMORY:long-term] [DefaultMemoryOrchestrator] created memory task#{extract_param.extract_type}[{extract_param.session_id}:{extract_param.task_id}]: {memory_task.memory_task_id}, reason: {reason}")
        return memory_task

    def _check_message_count_threshold(self, memory_items: List[MemoryItem], longterm_config: LongTermConfig) -> bool:
        """
        Check if the message count threshold is reached.
        
        Args:
            memory_items: List of memory items to check
            longterm_config: Long-term memory configuration settings
            
        Returns:
            True if threshold is reached, False otherwise
        """
        return len(memory_items) >= longterm_config.trigger.message_count_threshold

    def _check_content_importance(self, memory_items: List[MemoryItem], longterm_config: LongTermConfig) -> bool:
        """
        Check if the content importance threshold is reached.
        
        Args:
            memory_items: List of memory items to check
            longterm_config: Long-term memory configuration settings
            
        Returns:
            True if content is important enough, False otherwise
        """
        if not longterm_config.trigger.enable_importance_trigger:
            return False

        # Check for importance keywords in recent messages
        recent_items = memory_items[-1:] if len(memory_items) > 1 else memory_items
        importance_keywords = longterm_config.trigger.importance_keywords

        for item in recent_items:
            content = item.content.lower()
            for keyword in importance_keywords:
                if keyword.lower() in content:
                    return True

        return False

    async def _process_longterm_memory_task(self, task: MemoryProcessingTask) -> None:
        """
        Process a long-term memory task (placeholder implementation).

        Args:
            task: MemoryProcessingTask to process
        """
        try:
            logger.info(f"🧠 [MEMORY:long-term] Processing long-term task {task.memory_task_id} started")
            # 1. process memory task
            result = await self.memory_gungnir.process_memory_task(task)

            # 2. store the result
            await self._store_longterm_memories(result, task)

            logger.info(f"🧠 [MEMORY:long-term] Processing long-term task {task.memory_task_id} completed")

        except Exception as e:
            logger.error(
                f"🧠 [MEMORY:long-term] Error processing task#{task.memory_task_id}: {e}" + traceback.format_exc())
            task.status = "failed"
            await self._update_task_status(task)

    async def _store_longterm_memories(self, result: MemoryProcessingResult, task: MemoryProcessingTask) -> None:
        """
        Store the long-term memories.
        """
        try:
            if result.success:
                # 1. store user profiles
                await self._handle_store_longterm_memories(result.user_profiles, "user_profile")
                # 2. store agent experiences
                await self._handle_store_longterm_memories(result.agent_experiences, "agent_experience")
                # 3. update the task status
                task.status = "completed"
                await self._update_task_status(task)
            else:
                logger.error(f"🧠 [MEMORY:long-term] Error storing long-term memories: {result.error_message}")
                task.status = "failed"
                await self._update_task_status(task)
        except Exception as e:
            logger.error(f"🧠 [MEMORY:long-term] Error storing long-term memories: {e}" + traceback.format_exc())
            task.status = "failed"
            await self._update_task_status(task)

    async def _handle_store_longterm_memories(self, memory_items: List[MemoryItem],
                                              memory_type: Literal["user_profile", "agent_experience"]) -> None:
        """
        Store the long-term memory_items.

        1. retrieve the long-term memories from the long-term memory store
        2. compare the memories with the new memories
        3. if the memories are not in the long-term memory store, store the memories
        4. if the memories are in the long-term memory store, update the memories
        """
        if not memory_items:
            logger.debug(f"🧠 [MEMORY:long-term] Storing {memory_type} memories: {memory_items}")
            return

        for memory_item in memory_items:
            logger.info(f"🧠 [MEMORY:long-term] Storing {memory_type} memory: {memory_item.content}")
            await self.memory.add(memory_item)

    async def _add_memory_task(self, task: MemoryProcessingTask) -> None:
        """
        Add a memory task to the memory tasks list.
        """
        self.memory_tasks.append(task)

    async def _update_task_status(self, task: MemoryProcessingTask) -> None:
        """
        Update the task status.
        """
        try:
            self.memory_tasks = [t for t in self.memory_tasks if t.memory_task_id != task.memory_task_id]
            self.memory_tasks.append(task)
        except Exception as e:
            logger.error(f"🧠 [MEMORY:long-term] Error updating task status: {e}" + traceback.format_exc())

    async def retrieve_agent_experience(self, query: str, agent_id: Optional[str] = None,
                                        application_id: Optional[str] = "default") -> List[AgentExperience]:
        pass

    async def retrieve_user_profile(self, query: str, user_id: Optional[str] = None,
                                    application_id: Optional[str] = "default") -> List[UserProfile]:
        pass
