import json
import os
import time
from datetime import datetime
from typing import AsyncGenerator, Optional, List

from aworld.utils.common import get_local_ip
from fastapi import APIRouter, Query, Response
from fastapi.responses import StreamingResponse

import logging
import traceback
from asyncio import Queue
import asyncio

from aworld.models.model_response import ModelResponse
from pydantic import BaseModel, Field, PrivateAttr

from aworldspace.db.db import AworldTaskDB, SqliteTaskDB, PostgresTaskDB
from aworldspace.utils.job import generate_openai_chat_completion, call_pipeline
from aworldspace.utils.log import task_logger
from base import AworldTask, AworldTaskResult, OpenAIChatCompletionForm, OpenAIChatMessage, AworldTaskForm


from config import ROOT_DIR

__STOP_TASK__ = object()




class AworldTaskExecutor(BaseModel):
    """
    task executor
    - load task from db and execute task in a loop
    - use semaphore to limit concurrent tasks
    """
    _task_db: AworldTaskDB = PrivateAttr()
    _tasks: Queue = PrivateAttr()
    max_concurrent: int = Field(default=os.environ.get("AWORLD_MAX_CONCURRENT_TASKS", 2), description="max concurrent tasks")

    def __init__(self, task_db: AworldTaskDB):
        super().__init__()
        self._task_db = task_db
        self._tasks = Queue()
        self._semaphore = asyncio.BoundedSemaphore(self.max_concurrent)

    async def start(self):
        """
        execute task in a loop
        """
        await asyncio.sleep(5)
        logging.info(f"🚀[task executor] start, max concurrent is {self.max_concurrent}")
        while True:
            # load task if queue is empty and semaphore is not full
            if self._tasks.empty():
                await self.load_task()
            task = await self._tasks.get()
            if not task:
                logging.info("task is none")
                continue
            if task == __STOP_TASK__:
                logging.info("✅[task executor] stop, all tasks finished")
                break
            # acquire semaphore
            await self._semaphore.acquire()
            asyncio.create_task(self._run_task_and_release_semaphore(task))


    async def stop(self):
        logging.info("🛑 task executor stop, wait for all tasks to finish")
        await self._tasks.put(__STOP_TASK__)

    async def _run_task_and_release_semaphore(self, task: AworldTask):
        """
        execute task and release semaphore when done
        """
        start_time = time.time()
        logging.info(f"🚀[task executor] execute task#{task.task_id} start, lock acquired")
        try:
            await self.execute_task(task)
        finally:
            # release semaphore
            self._semaphore.release()
        logging.info(f"✅[task executor] execute task#{task.task_id} success, use time {time.time() - start_time:.2f}s")

    async def load_task(self):
        interval = os.environ.get("AWORLD_TASK_LOAD_INTERVAL", 10)
        # calculate the number of tasks to load
        need_load = self._semaphore._value
        if need_load <= 0:
            logging.info(f"🔍[task executor] runner is busy, wait {interval}s and retry")
            await asyncio.sleep(interval)
            return await self.load_task()
        tasks = await self._task_db.query_tasks_by_status(status="INIT", nums=need_load)
        logging.info(f"🔍[task executor] load {len(tasks)} tasks from db (need {need_load})")


        if not tasks or len(tasks) == 0:
            logging.info(f"🔍[task executor] no task to load, wait {interval}s and retry")
            await asyncio.sleep(interval)
            return await self.load_task()
        for task in tasks:
            task.mark_running()
            await self._task_db.update_task(task)
            await self._tasks.put(task)
        return True

    async def execute_task(self, task: AworldTask):
        """
        execute task
        """
        try:
            result = await self._execute_task(task)
            task.mark_success()
            await self._task_db.update_task(task)
            await self._task_db.save_task_result(result)
            task_logger.log_task_submission(task, "execute_finished", task_result=result)
        except Exception as err:
            task.mark_failed()
            await self._task_db.update_task(task)
            traceback.print_exc()
            task_logger.log_task_submission(task, "execute_failed", details=f"err is {err}")

    async def _execute_task(self, task: AworldTask):

        # build params
        messages = [
            OpenAIChatMessage(role="user", content=task.agent_input)
        ]
        # call_llm_model
        form_data = OpenAIChatCompletionForm(
            model=task.agent_id,
            messages=messages,
            stream=True,
            user={
                "user_id": task.user_id,
                "session_id": task.session_id,
                "task_id": task.task_id,
                "aworld_task": task.model_dump_json()
            }
        )
        data = await generate_openai_chat_completion(form_data)
        task_result = {}
        task.node_id = get_local_ip()
        items = []
        md_file = ""
        if data.body_iterator:
            if isinstance(data.body_iterator, AsyncGenerator):

                async for item_content in data.body_iterator:
                    async def parse_item(_item_content) -> Optional[ModelResponse]:
                        if item_content == "data: [DONE]":
                            return None
                        return ModelResponse.from_openai_stream_chunk(json.loads(item_content.replace("data:", "")))

                    # if isinstance(item, ModelResponse)
                    item = await parse_item(item_content)
                    items.append(item)
                    if not item:
                        continue

                    if item.content:
                        md_file = task_logger.log_task_result(task, item)
                        logging.info(f"task#{task.task_id} response data chunk is: {item}"[:500])

                    if item.raw_response and item.raw_response and isinstance(item.raw_response, dict) and item.raw_response.get('task_output_meta'):
                        task_result = item.raw_response.get('task_output_meta')

        data = {
            "task_result": task_result,
            "md_file": md_file,
            "replays_file": f"trace_data/{datetime.now().strftime('%Y%m%d')}/{get_local_ip()}/replays/task_replay_{task.task_id}.json"
        }
        result = AworldTaskResult(task=task, server_host=get_local_ip(), data=data)
        return result


class AworldTaskManager(BaseModel):
    _task_db: AworldTaskDB = PrivateAttr()
    _task_executor: AworldTaskExecutor = PrivateAttr()

    def __init__(self, task_db: AworldTaskDB):
        super().__init__()
        self._task_db = task_db
        self._task_executor = AworldTaskExecutor(task_db=self._task_db)
    
    async def start_task_executor(self):
        asyncio.create_task(self._task_executor.start())

    async def stop_task_executor(self):
        self._task_executor.tasks.put_nowait(None)

    async def submit_task(self, task: AworldTask):
        # save to db
        await self._task_db.insert_task(task)
        # log it
        task_logger.log_task_submission(task, status="init")

        return AworldTaskResult(task = task)

    async def load_one_unfinished_task(self) -> Optional[AworldTask]:
        tasks = await self._task_db.query_tasks_by_status(status="INIT", nums=1)
        if not tasks or len(tasks) == 0:
            return None

        cur_task = tasks[0]
        cur_task.mark_running()
        await self._task_db.update_task(cur_task)
        # from db load one task by locked and mark task running
        return cur_task

    async def get_task_result(self, task_id: str) -> Optional[AworldTaskResult]:
        task = await self._task_db.query_task_by_id(task_id)
        if task:
            task_result = await self._task_db.query_latest_task_result_by_id(task_id)
            if task_result:
                return task_result
            return AworldTaskResult(task=task)

    async def get_batch_task_results(self, task_ids: List[str]) -> List[dict]:
        """
        Batch retrieve task results, returns dictionary format
        Each dict contains: task (required) and task_result (may be None)
        """
        results = []
        for task_id in task_ids:
            task = await self._task_db.query_task_by_id(task_id)

            if task:
                task_result = await self._task_db.query_latest_task_result_by_id(task_id)
                
                result_dict = {
                    "task": task,
                    "task_result": task_result  # May be None
                }
                results.append(result_dict)
        return results

    async def query_and_download_task_results(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        task_id: Optional[str] = None,
        page_size: int = 100
    ) -> List[dict]:
        """
        Query tasks and get results, support time range and task_id filtering
        """
        all_results = []
        page_num = 1
        
        while True:
            # Build query filter conditions
            filter_dict = {}
            if start_time:
                filter_dict['start_time'] = start_time
            if end_time:
                filter_dict['end_time'] = end_time
            if task_id:
                filter_dict['task_id'] = task_id
            
            # Page query tasks
            page_result = await self._task_db.page_query_tasks(
                filter=filter_dict, 
                page_size=page_size, 
                page_num=page_num
            )
            
            if not page_result['items']:
                break
                
            tasks = page_result['items']
            
            for task in tasks:
                # Only query task_result (may not exist)
                task_result = await self._task_db.query_latest_task_result_by_id(task.task_id)
                
                # Use task information to build results
                result_data = {
                    "task_id": task.task_id,
                    "agent_id": task.agent_id,
                    "status": task.status,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                    "user_id": task.user_id,
                    "session_id": task.session_id,
                    "node_id": task.node_id,
                    "client_id": task.client_id,
                    "task_data": task.model_dump(mode='json'),
                    "has_result": task_result is not None,
                    "server_host": task_result.server_host if task_result else None,
                    "result_data": task_result.data if task_result else None,
                }
                all_results.append(result_data)
            
            if len(page_result['items']) < page_size:
                break
                
            page_num += 1
        
        return all_results


########################################################################################
###########################   API
########################################################################################

router = APIRouter()

task_db_path = os.environ.get("AWORLD_TASK_DB_PATH", f"sqlite:///{ROOT_DIR}/db/aworld.db")

if task_db_path.startswith("sqlite://"):
    task_db = SqliteTaskDB(db_path = task_db_path)
elif task_db_path.startswith("mysql://"):
    task_db = None  # todo: add mysql task db
elif task_db_path.startswith("postgresql://") or task_db_path.startswith("postgresql+"):
    task_db = PostgresTaskDB(db_url=task_db_path)
else:
    raise ValueError("❌ task_db_path is not a valid sqlite, mysql or postgresql path")

task_manager = AworldTaskManager(task_db)

@router.post("/submit_task")
async def submit_task(form_data: AworldTaskForm) -> Optional[AworldTaskResult]:

    logging.info(f"🚀 submit task#{form_data.task.task_id} start")
    if not form_data.task:
        raise ValueError("task is empty")

    try:
        task_result = await task_manager.submit_task(form_data.task)
        logging.info(f"✅ submit task#{form_data.task.task_id} success")
        return task_result
    except Exception as err:
        traceback.print_exc()
        logging.error(f"❌ submit task#{form_data.task.task_id} failed, err is {err}")
        raise ValueError("❌ submit task failed, please see logs for details")


@router.get("/task_result")
async def get_task_result(task_id) -> Optional[AworldTaskResult]:
    if not task_id:
        raise ValueError("❌ task_id is empty")

    logging.info(f"🚀 get task result#{task_id} start")
    try:
        task_result = await task_manager.get_task_result(task_id)
        logging.info(f"✅ get task result#{task_id} success, task result is {task_result}")
        return task_result
    except Exception as err:
        traceback.print_exc()
        logging.error(f"❌ get task result#{task_id} failed, err is {err}")
        raise ValueError("❌ get task result failed, please see logs for details")

@router.post("/get_batch_task_results")
async def get_batch_task_results(task_ids: List[str]) -> List[dict]:
    if not task_ids or len(task_ids) == 0:
        raise ValueError("❌ task_ids is empty")

    logging.info(f"🚀 get batch task results start, task_ids: {task_ids}")
    try:
        batch_results = await task_manager.get_batch_task_results(task_ids)
        logging.info(f"✅ get batch task results success, found {len(batch_results)} results")
        return batch_results
    except Exception as err:
        traceback.print_exc()
        logging.error(f"❌ get batch task results failed, err is {err}")
        raise ValueError("❌ get batch task results failed, please see logs for details")

@router.get("/download_task_results")
async def download_task_results(
    start_time: Optional[str] = Query(None, description="Start time, format: YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="End time, format: YYYY-MM-DD HH:MM:SS"),
    task_id: Optional[str] = Query(None, description="Task ID"),
    page_size: int = Query(100, description="Page size, ge=1, le=1000")
) -> StreamingResponse:
    """
    Download task results, generate jsonl format file
    Query parameters support: time range (based on creation time), task_id
    """
    logging.info(f"🚀 download task results start, start_time: {start_time}, end_time: {end_time}, task_id: {task_id}")
    
    try:
        start_datetime = None
        end_datetime = None
        
        if start_time:
            try:
                start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError("❌ start_time格式错误，请使用 YYYY-MM-DD HH:MM:SS 格式")
                
        if end_time:
            try:
                end_datetime = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError("❌ end_time格式错误，请使用 YYYY-MM-DD HH:MM:SS 格式")
        
        results = await task_manager.query_and_download_task_results(
            start_time=start_datetime,
            end_time=end_datetime,
            task_id=task_id,
            page_size=page_size
        )
        
        if not results:
            logging.info("📄 no task results found")

            def generate_empty():
                yield ""
            
            return StreamingResponse(
                generate_empty(),
                media_type="application/jsonl",
                headers={"Content-Disposition": "attachment; filename=task_results_empty.jsonl"}
            )
        
        # Generate jsonl content
        def generate_jsonl():
            for result in results:
                yield json.dumps(result, ensure_ascii=False) + "\n"
        
        # Generate file name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"task_results_{timestamp}.jsonl"
        
        logging.info(f"✅ download task results success, total: {len(results)} results")
        
        return StreamingResponse(
            generate_jsonl(),
            media_type="application/jsonl",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as err:
        traceback.print_exc()
        logging.error(f"❌ download task results failed, err is {err}")
        raise ValueError(f"❌ download task results failed: {str(err)}")