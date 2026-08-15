from typing import AsyncGenerator
import traceback
import logging
import os
import json
import sys
import uuid
import time

logger = logging.getLogger(__name__)


class GaiaAgentServer:
    def __init__(self):
        pass

    def _get_model_config(self):
        try:
            llm_provider = os.getenv("LLM_PROVIDER", "openai")
            llm_model_name = os.getenv("LLM_MODEL_NAME")
            llm_api_key = os.getenv("LLM_API_KEY")
            llm_base_url = os.getenv("LLM_BASE_URL")
            llm_temperature = float(os.getenv("LLM_TEMPERATURE", 0.0))
            return {
                "provider": llm_provider,
                "model": llm_model_name,
                "api_key": llm_api_key,
                "base_url": llm_base_url,
                "temperature": llm_temperature,
            }
        except Exception as e:
            logger.warning(
                f">>> Gaia Agent: GAIA_MODEL_CONFIG is not configured, using LLM"
            )
            raise e

    def models(self):
        model = self._get_model_config()

        return [
            {
                "id": f"{model['provider']}/{model['model']}",
                "name": f"gaia_agent@{model['provider']}/{model['model']}",
            }
        ]

    async def chat_completions(self, body: dict) -> AsyncGenerator[str, None]:
        def response_line(line: str, model: str):
            return {
                "object": "chat.completion.chunk",
                "id": str(uuid.uuid4()).replace("-", ""),
                "choices": [
                    {"index": 0, "delta": {"content": line, "role": "assistant"}}
                ],
                "created": int(time.time()),
                "model": model,
            }

        try:
            logger.info(f">>> Gaia Agent: body={body}")

            prompt = body["messages"][-1]["content"]
            model = body["model"].replace("gaia_agent.", "")

            logger.info(f">>> Gaia Agent: prompt={prompt}, model={model}")

            selected_model = self._get_model_config()

            logger.info(f">>> Gaia Agent: Using model configuration: {selected_model}")

            logger.info(f">>> Gaia Agent Python Path: sys.path={sys.path}")

            llm_provider = selected_model.get("provider")
            llm_model_name = selected_model.get("model")
            llm_api_key = selected_model.get("api_key")
            llm_base_url = selected_model.get("base_url")
            llm_temperature = selected_model.get("temperature", 0.0)

            from examples.gaia.gaia_agent_runner import GaiaAgentRunner

            runner = GaiaAgentRunner(
                llm_provider=llm_provider,
                llm_model_name=llm_model_name,
                llm_base_url=llm_base_url,
                llm_api_key=llm_api_key,
                llm_temperature=llm_temperature,
            )

            logger.info(f">>> Gaia Agent: prompt={prompt}, runner={runner}")

            async for i in runner.run(prompt):
                line = response_line(i, model)
                logger.info(f">>> Gaia Agent Line: {line}")
                yield line

        except Exception as e:
            emsg = traceback.format_exc()
            logger.error(f">>> Gaia Agent Error: exception {emsg}")
            yield response_line(f"Gaia Agent Error: {emsg}", model)

        finally:
            logger.info(f">>> Gaia Agent Done")


import fastapi
from fastapi.responses import StreamingResponse

app = fastapi.FastAPI()

from examples.gaia.gaia_agent_server import GaiaAgentServer

agent_server = GaiaAgentServer()


@app.get("/v1/models")
async def models():
    return agent_server.models()


@app.post("/v1/chat/completions")
async def chat_completions(request: fastapi.Request):
    form_data = await request.json()
    logger.info(f">>> Gaia Agent Server: form_data={form_data}")

    async def event_generator():
        async for chunk in agent_server.chat_completions(form_data):
            # Format as SSE: each line needs to start with "data: " and end with two newlines
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("gaia_agent_server:app", host="0.0.0.0", port=8888)
