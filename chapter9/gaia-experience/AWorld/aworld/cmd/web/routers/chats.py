import logging
import json
from typing import Dict
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from aworld.cmd.data_model import AgentModel, ChatCompletionRequest
from aworld.cmd.utils import agent_executor
from aworld.cmd.utils.trace_summarize import summarize_trace
from aworld.cmd.web.utils.users import get_user_id_from_jwt
import aworld.trace as trace

logger = logging.getLogger(__name__)

router = APIRouter()

prefix = "/api/agent"


@router.get("/list")
@router.get("/models")
async def list_agents(request: Request) -> Dict[str, AgentModel]:
    return request.app.state.agent_server.list_agents()


@router.post("/chat/completions")
async def chat_completion(
    form_data: ChatCompletionRequest,
    request: Request,
    user_id: str = Depends(get_user_id_from_jwt),
) -> StreamingResponse:
    # Set user_id from JWT to form_data
    form_data.user_id = user_id

    async def generate_stream():
        async with trace.span(
            "/chat/chat_completion", attributes={"model": form_data.model}
        ) as span:
            form_data.trace_id = span.get_trace_id()
            async for chunk in agent_executor.stream_run(
                form_data, request.app.state.agent_server
            ):
                yield f"data: {json.dumps(chunk.model_dump(), ensure_ascii=False)}\n\n"
        summarize_trace(form_data.trace_id)

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
