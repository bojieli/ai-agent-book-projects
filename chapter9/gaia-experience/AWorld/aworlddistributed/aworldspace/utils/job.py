import inspect
import json
import inspect
import json
import logging
import time
import uuid
from typing import Generator, Iterator, AsyncGenerator, Optional

from aworld.core.task import Task
from aworld.utils.common import get_local_ip
from fastapi import status, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from aworldspace.base import AGENT_SPACE
from aworldspace.utils.utils import get_last_user_message
from base import OpenAIChatCompletionForm

async def generate_openai_chat_completion(form_data: OpenAIChatCompletionForm):
    messages = [message.model_dump() for message in form_data.messages]
    user_message = get_last_user_message(messages)
    PIPELINES = await AGENT_SPACE.get_agents_meta()
    PIPELINE_MODULES = await AGENT_SPACE.get_agent_modules()
    if (
        form_data.model not in PIPELINES
        or PIPELINES[form_data.model]["type"] == "filter"
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline {form_data.model} not found",
        )

    def job():
        pipeline = PIPELINES[form_data.model]
        pipeline_id = form_data.model

        if pipeline["type"] == "manifold":
            manifold_id, pipeline_id = pipeline_id.split(".", 1)
            pipe = PIPELINE_MODULES[manifold_id].pipe
        else:
            pipe = PIPELINE_MODULES[pipeline_id].pipe

        def process_line(model, line):
            if isinstance(line, Task):
                task_output_meta = line.outputs._metadata
                line = openai_chat_chunk_message_template(model, "", task_output_meta=task_output_meta)
                return f"data: {json.dumps(line)}\n\n"
            if isinstance(line, BaseModel):
                line = line.model_dump_json()
                line = f"data: {line}"
            if isinstance(line, dict):
                line = f"data: {json.dumps(line)}"

            try:
                line = line.decode("utf-8")
            except Exception:
                pass

            if line.startswith("data:"):
                return f"{line}\n\n"
            else:
                line = openai_chat_chunk_message_template(model, line)
                return f"data: {json.dumps(line)}\n\n"

        if form_data.stream:
            async def stream_content():
                async def execute_pipe(_pipe):
                    if inspect.iscoroutinefunction(_pipe):
                        return await _pipe(user_message=user_message,
                                          model_id=pipeline_id,
                                          messages=messages,
                                          body=form_data.model_dump())
                    else:
                        return _pipe(user_message=user_message,
                                    model_id=pipeline_id,
                                    messages=messages,
                                    body=form_data.model_dump())

                try:
                    res = await execute_pipe(pipe)

                    # Directly return if the response is a StreamingResponse
                    if isinstance(res, StreamingResponse):
                        async for data in res.body_iterator:
                            yield data
                        return
                    if isinstance(res, dict):
                        yield f"data: {json.dumps(res)}\n\n"
                        return

                except Exception as e:
                    logging.error(f"Error: {e}")
                    import traceback
                    traceback.print_exc()
                    yield f"data: {json.dumps({'error': {'detail': str(e)}})}\n\n"
                    return

                if isinstance(res, str):
                    message = openai_chat_chunk_message_template(form_data.model, res)
                    yield f"data: {json.dumps(message)}\n\n"

                if isinstance(res, Iterator):
                    for line in res:
                        yield process_line(form_data.model, line)

                if isinstance(res, AsyncGenerator):
                    async for line in res:
                        yield process_line(form_data.model, line)
                    logging.info(f"AsyncGenerator end...")

                if isinstance(res, str) or isinstance(res, Generator) or isinstance(res, AsyncGenerator):
                    finish_message = openai_chat_chunk_message_template(
                        form_data.model, ""
                    )
                    finish_message["choices"][0]["finish_reason"] = "stop"
                    print(f"Pipe-Dataline:::: DONE")
                    yield f"data: {json.dumps(finish_message)}\n\n"
                    yield "data: [DONE]"

            return StreamingResponse(stream_content(), media_type="text/event-stream")
        else:
            res = pipe(
                user_message=user_message,
                model_id=pipeline_id,
                messages=messages,
                body=form_data.model_dump(),
            )
            logging.info(f"stream:false:{res}")

            if isinstance(res, dict):
                return res
            elif isinstance(res, BaseModel):
                return res.model_dump()
            else:

                message = ""

                if isinstance(res, str):
                    message = res

                if isinstance(res, Generator):
                    for stream in res:
                        message = f"{message}{stream}"

                logging.info(f"stream:false:{message}")
                return {
                    "id": f"{form_data.model}-{str(uuid.uuid4())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": form_data.model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": message,
                            },
                            "logprobs": None,
                            "finish_reason": "stop",
                        }
                    ],
                }


    return await run_in_threadpool(job)


async def call_pipeline(form_data: OpenAIChatCompletionForm):
    messages = [message.model_dump() for message in form_data.messages]
    user_message = get_last_user_message(messages)
    PIPELINES = await AGENT_SPACE.get_agents_meta()
    PIPELINE_MODULES = await AGENT_SPACE.get_agent_modules()
    if (
        form_data.model not in PIPELINES
        or PIPELINES[form_data.model]["type"] == "filter"
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline {form_data.model} not found",
        )

    pipeline = PIPELINES[form_data.model]
    pipeline_id = form_data.model

    if pipeline["type"] == "manifold":
        manifold_id, pipeline_id = pipeline_id.split(".", 1)
        pipe = PIPELINE_MODULES[manifold_id].pipe
    else:
        pipe = PIPELINE_MODULES[pipeline_id].pipe

    if form_data.stream:
        async def execute_pipe(_pipe):
            if inspect.iscoroutinefunction(_pipe):
                return await _pipe(user_message=user_message,
                                   model_id=pipeline_id,
                                   messages=messages,
                                   body=form_data.model_dump())
            else:
                return _pipe(user_message=user_message,
                             model_id=pipeline_id,
                             messages=messages,
                             body=form_data.model_dump())

        res = await execute_pipe(pipe)
        return res
    else:
        if not inspect.iscoroutinefunction(pipe):
            return await run_in_threadpool(
                pipe,
                user_message=user_message,
                model_id=pipeline_id,
                messages=messages,
                body=form_data.model_dump()
            )
        else:
            return await pipe(
                user_message=user_message,
                model_id=pipeline_id,
                messages=messages,
                body=form_data.model_dump()
            )

def openai_chat_chunk_message_template(
    model: str,
    content: Optional[str] = None,
    tool_calls: Optional[list[dict]] = None,
    usage: Optional[dict] = None,
    **kwargs
) -> dict:
    template = openai_chat_message_template(model, **kwargs)
    template["object"] = "chat.completion.chunk"

    template["choices"][0]["index"] = 0
    template["choices"][0]["delta"] = {}

    if content:
        template["choices"][0]["delta"]["content"] = content

    if tool_calls:
        template["choices"][0]["delta"]["tool_calls"] = tool_calls

    if not content and not tool_calls:
        template["choices"][0]["finish_reason"] = "stop"

    if usage:
        template["usage"] = usage
    return template

def openai_chat_message_template(model: str, **kwargs):
    return {
        "id": f"{model}-{str(uuid.uuid4())}",
        "created": int(time.time()),
        "model": model,
        "node_id": get_local_ip(),
        "task_output_meta": kwargs.get("task_output_meta"),
        "choices": [{"index": 0, "logprobs": None, "finish_reason": None}],
    }