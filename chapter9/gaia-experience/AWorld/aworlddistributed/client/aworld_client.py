import asyncio
import logging
import os
import traceback
from datetime import datetime
from typing import AsyncGenerator

from aworld.models.llm import acall_llm_model, get_llm_model, acall_llm_model_stream
from aworld.models.model_response import ModelResponse, LLMResponseError
from pydantic import BaseModel, Field

from base import AworldTask, AworldTaskResult, AworldTaskForm


class TaskLogger:
    """Task submission logger"""

    def __init__(self, log_file: str = "aworld_task_submissions.log"):
        self.log_file = 'task_logs/' + log_file
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self):
        """ensure log file exists"""
        if not os.path.exists(self.log_file):
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("# Aworld Task Submission Log\n")
                f.write("# Format: [timestamp] task_id | agent_id | server | status | agent_answer | correct_answer | is_correct | details\n\n")

    def log_task_submission(self, task: AworldTask, server: str, status: str, details: str = "", task_result: AworldTaskResult = None):
        """log task submission"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {task.task_id} | {task.agent_id} | {task.node_id} | {status} | { task_result.data.get('agent_answer') if task_result and task_result.data else None } | {task_result.data.get('correct_answer') if task_result and task_result.data else None} | {task_result.data.get('gaia_correct') if task_result and task_result.data else None} |{details}\n"

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            logging.error(f"Failed to write task submission log: {e}")

    def log_task_result(self, task: AworldTask, result: ModelResponse):
        """log task result to markdown file"""
        try:
            # create result directory
            date_str = datetime.now().strftime("%Y%m%d")
            result_dir = f"task_logs/result/{date_str}"
            os.makedirs(result_dir, exist_ok=True)

            # create markdown file
            md_file = f"{result_dir}/{task.task_id}.md"

            # concat content
            content_parts = []
            if hasattr(result, 'content') and result.content:
                if isinstance(result.content, list):
                    content_parts.extend(result.content)
                else:
                    content_parts.append(str(result.content))

            # write to markdown file
            file_exists = os.path.exists(md_file)
            with open(md_file, 'a', encoding='utf-8') as f:
                # only write title info when file not exists
                if not file_exists:
                    f.write(f"# Task Result: {task.task_id}\n\n")
                    f.write(f"**Agent ID:** {task.agent_id}\n\n")
                    f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("## Content\n\n")

                # write content parts
                if content_parts:
                    for i, content in enumerate(content_parts, 1):
                        f.write(f"{content}\n\n")
                else:
                    f.write("No content available.\n\n")

        except Exception as e:
            logging.error(f"Failed to write task result log: {e}")

task_logger = TaskLogger(log_file=f"aworld_task_submissions_{datetime.now().strftime('%Y%m%d')}.log")

class AworldTaskClient(BaseModel):
    """
    AworldTaskClient
    """
    know_hosts: list[str] = Field(default_factory=list, description="aworldserver list")
    tasks: list[AworldTask] = Field(default_factory=list, description="submitted task list")
    task_states: dict[str, AworldTaskResult] = Field(default_factory=dict, description="task_states")

    async def submit_task(self, task: AworldTask, background: bool = True):
        if not self.know_hosts:
            raise ValueError("No aworld server hosts configured.")
        # 1. select aworld server from know_hosts using round-robin
        if not hasattr(self, '_current_server_index'):
            self._current_server_index = 0
        aworld_server = self.know_hosts[self._current_server_index]
        if not aworld_server.startswith("http"):
            aworld_server = "http://" + aworld_server
        self._current_server_index = (self._current_server_index + 1) % len(self.know_hosts)

        # 2. call _submit_task
        result = await self._submit_task(aworld_server, task, background)
        # 3. update task_states
        self.task_states[task.task_id] = result

        
    async def _submit_task(self, aworld_server, task: AworldTask, background: bool = True):
        try:
            logging.info(f"submit task#{task.task_id} to cluster#[{aworld_server}]")
            if not background:
                task_result = await self._submit_task_to_server(aworld_server, task)
            else:
                task_result = await self._async_submit_task_to_server(aworld_server, task)
            return task_result
        except Exception as e:
            if isinstance(e, LLMResponseError):
                if e.message and 'peer closed connection without sending complete message body (incomplete chunked read)' == e.message:
                    task_logger.log_task_submission(task, aworld_server, "server_close_connection", str(e))
                    logging.error(f"execute task to {task.node_id} server_close_connection: [{e}], please see replays wait a moment")
                    return
            traceback.print_exc()
            logging.error(f"execute task to {task.node_id} execute_failed: [{e}], please see logs from server ")
            task_logger.log_task_submission(task, aworld_server, "execute_failed", str(e))

    async def _async_submit_task_to_server(self, aworld_server, task: AworldTask):
        import httpx
        from base import AworldTaskForm, AworldTaskResult
        # 构建 AworldTaskForm
        form_data = AworldTaskForm(task=task)
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{aworld_server}/api/v1/tasks/submit_task", json=form_data.model_dump())
            resp.raise_for_status()
            data = resp.json()
            task_logger.log_task_submission(task, aworld_server, "submitted")
            return AworldTaskResult(**data)

    async def _submit_task_to_server(self, aworld_server, task: AworldTask):
        # build params
        llm_model = get_llm_model(
            llm_provider="openai",
            model_name=task.agent_id,
            base_url=f"{aworld_server}/v1",
            api_key="0p3n-w3bu!"
        )
        messages = [
            {"role": "user", "content": task.agent_input}
        ]
        #call_llm_model
        data = acall_llm_model_stream(llm_model, messages, stream=True, user={
            "user_id": task.user_id,
            "session_id": task.session_id,
            "task_id": task.task_id,
            "aworld_task": task.model_dump_json()
        })
        items = []
        task_result = {}
        if isinstance(data, AsyncGenerator):
            async for item in data:
                items.append(item)
                if item.raw_response and item.raw_response.model_extra and item.raw_response.model_extra.get('node_id'):
                    if not task.node_id:
                        logging.info(f"submit task#{task.task_id} success. execute pod ip is [{item.raw_response.model_extra.get('node_id')}]")
                        task.node_id = item.raw_response.model_extra.get('node_id')
                        task_logger.log_task_submission(task, aworld_server, "submitted")

                if item.content:
                    task_logger.log_task_result(task, item)
                    logging.info(f"task#{task.task_id} response data chunk is: {item}"[:500])

                if item.raw_response and item.raw_response.model_extra and item.raw_response.model_extra.get(
                        'task_output_meta'):
                    task_result = item.raw_response.model_extra.get('task_output_meta')


        elif isinstance(data, ModelResponse):
            if data.raw_response and data.raw_response.model_extra and data.raw_response.model_extra.get('node_id'):
                if not task.node_id:
                    logging.info(f"submit task#{task.task_id} success. execute pod ip is [{data.raw_response.model_extra.get('node_id')}]")
                task.node_id = data.raw_response.model_extra.get('node_id')

            logging.info(f"task#{task.task_id} response data is: {data}")
            task_logger.log_task_result(task, data)
            if data.raw_response and data.raw_response.model_extra and data.raw_response.model_extra.get('task_output_meta'):
                task_result = data.raw_response.model_extra.get('task_output_meta')

        result = AworldTaskResult(task=task, server_host=aworld_server, data=task_result)
        task_logger.log_task_submission(task, aworld_server, "execute_finished", task_result=result)
        return result

    async def get_task_state(self, task_id: str):
        if not isinstance(self.task_states, dict):
            self.task_states = dict(self.task_states)
        return self.task_states.get(task_id, None)

    async def download_task_results(
        self, 
        start_time: str = None, 
        end_time: str = None, 
        task_id: str = None, 
        page_size: int = 100,
        save_path: str = None
    ) -> str:
        """
        Download task results and generate a JSONL format file
        
        Args:
            start_time: Start time, format: YYYY-MM-DD HH:MM:SS
            end_time: End time, format: YYYY-MM-DD HH:MM:SS
            task_id: Task ID
            page_size: Page size
            save_path: Save path, if not specified, it will be generated automatically
            
        Returns:
            str: Save path
        """
        if not self.know_hosts:
            raise ValueError("No aworld server hosts configured.")
        
        # select server
        if not hasattr(self, '_current_server_index'):
            self._current_server_index = 0
        aworld_server = self.know_hosts[self._current_server_index]
        
        logging.info(f"🚀 downloading task results from server: {aworld_server}")
        
        try:
            import httpx
            
            # build query params
            params = {"page_size": page_size}
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
            if task_id:
                params["task_id"] = task_id
            
            # send download request
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5分钟超时
                response = await client.get(
                    f"{aworld_server}/api/v1/tasks/download_task_results",
                    params=params
                )
                response.raise_for_status()
                
                # if not specified save path, generate automatically
                if not save_path:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = f"task_results_{timestamp}.jsonl"
                
                # ensure directory exists
                save_dir = os.path.dirname(save_path) if os.path.dirname(save_path) else "."
                os.makedirs(save_dir, exist_ok=True)
                
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
                
                # calculate file size
                file_size = os.path.getsize(save_path)
                logging.info(f"✅ task results downloaded successfully, file: {save_path}, size: {file_size} bytes")
                
                return save_path
                
        except Exception as e:
            logging.error(f"❌ download task results failed: {e}")
            raise ValueError(f"❌ download task results failed: {str(e)}")

    async def download_task_results_to_memory(
        self, 
        start_time: str = None, 
        end_time: str = None, 
        task_id: str = None, 
        page_size: int = 100
    ) -> list:
        """
        Download task results to memory, return parsed data list
        
        Args:
            start_time: Start time, format: YYYY-MM-DD HH:MM:SS
            end_time: End time, format: YYYY-MM-DD HH:MM:SS
            task_id: Task ID
            page_size: Page size
            
        Returns:
            list: Task results data list
        """
        if not self.know_hosts:
            raise ValueError("No aworld server hosts configured.")
        
        # select server
        if not hasattr(self, '_current_server_index'):
            self._current_server_index = 0
        aworld_server = self.know_hosts[self._current_server_index]
        
        logging.info(f"🚀 downloading task results to memory from server: {aworld_server}")
        
        try:
            import httpx
            import json
            
            # build query params
            params = {"page_size": page_size}
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
            if task_id:
                params["task_id"] = task_id
            
            # send download request
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5分钟超时
                response = await client.get(
                    f"{aworld_server}/api/v1/tasks/download_task_results",
                    params=params
                )
                response.raise_for_status()
                
                # parse jsonl content
                results = []
                content = response.text
                if content.strip():  # check content is not empty
                    for line in content.strip().split('\n'):
                        if line.strip():  # skip empty line
                            try:
                                result_data = json.loads(line)
                                results.append(result_data)
                            except json.JSONDecodeError as e:
                                logging.warning(f"Failed to parse line: {line}, error: {e}")
                
                logging.info(f"✅ task results downloaded to memory successfully, total: {len(results)} records")
                
                return results
                
        except Exception as e:
            logging.error(f"❌ download task results to memory failed: {e}")
            raise ValueError(f"❌ download task results to memory failed: {str(e)}")

    def parse_task_results_file(self, file_path: str) -> list:
        """
        Parse local task results jsonl file

        Args:
            file_path: jsonl file path

        Returns:
            list: Parsed task results list
        """
        import json

        results = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:  # 跳过空行
                        try:
                            result_data = json.loads(line)
                            results.append(result_data)
                        except json.JSONDecodeError as e:
                            logging.warning(f"Failed to parse line {line_num} in {file_path}: {e}")

            logging.info(f"✅ parsed {len(results)} task results from {file_path}")
            return results

        except Exception as e:
            logging.error(f"❌ failed to parse task results file {file_path}: {e}")
            raise ValueError(f"❌ failed to parse task results file: {str(e)}")

