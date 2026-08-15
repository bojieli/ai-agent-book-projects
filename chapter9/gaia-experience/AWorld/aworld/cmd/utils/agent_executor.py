from typing import AsyncGenerator
from aworld.cmd.utils.agent_server import AgentServer
from aworld.output.ui.base import AworldUI
from aworld.output.workspace import WorkSpace
from aworld.cmd.data_model import (
    BaseAWorldAgent,
    ChatCompletionChoice,
    ChatCompletionMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from .agent_ui_parser import AWorldWebAgentUI
import logging
import os
import uuid
from dotenv import load_dotenv
import traceback

logger = logging.getLogger(__name__)


async def stream_run(request: ChatCompletionRequest, agent_server: AgentServer):
    if not request.session_id:
        request.session_id = str(uuid.uuid4())
    if not request.query_id:
        request.query_id = str(uuid.uuid4())
    if request.messages and request.messages[-1].trace_id is None:
        request.messages[-1].trace_id = request.trace_id

    logger.info(f"Stream run agent: request={request.model_dump_json()}")
    agent = agent_server.get_agent(request.model)
    instance: BaseAWorldAgent = agent.instance
    env_file = os.path.join(agent.path, ".env")
    if os.path.exists(env_file):
        logger.info(f"Loading environment variables from {env_file}")
        load_dotenv(env_file, override=True, verbose=True)

    final_response: str = ""

    def build_response(delta_content: str):
        nonlocal final_response
        final_response += delta_content
        logger.info(f"Agent {agent.name} response: {delta_content}")
        return ChatCompletionResponse(
            choices=[
                ChatCompletionChoice(
                    index=0,
                    delta=ChatCompletionMessage(
                        role="assistant",
                        content=delta_content,
                        trace_id=request.trace_id,
                    ),
                )
            ]
        )

    rich_ui = AWorldWebAgentUI(
        session_id=request.session_id,
        workspace=WorkSpace.from_local_storages(
            workspace_id=request.session_id,
        ),
    )

    await agent_server.on_chat_completion_request(request)
    try:
        async for output in instance.run(request=request):
            try:
                logger.info(f"Agent {agent.name} output: {output}")

                if isinstance(output, str):
                    yield build_response(output)
                else:
                    res = await AworldUI.parse_output(output, rich_ui)
                    for item in res if isinstance(res, list) else [res]:
                        if isinstance(item, AsyncGenerator):
                            async for sub_item in item:
                                yield build_response(sub_item)
                        else:
                            yield build_response(item)
            except:
                logger.error(
                    f"Agent {agent.name} output error! output={output}, error={traceback.format_exc()}"
                )
    except:
        logger.error(f"Agent {agent.name} error: {traceback.format_exc()}")
    finally:
        await agent_server.on_chat_completion_end(request, final_response)
