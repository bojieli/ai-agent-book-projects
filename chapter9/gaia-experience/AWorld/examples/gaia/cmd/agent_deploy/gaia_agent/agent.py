import logging
import os
from aworld.cmd.data_model import BaseAWorldAgent, ChatCompletionRequest
from examples.gaia.gaia_agent_runner import GaiaAgentRunner

logger = logging.getLogger(__name__)


class AWorldAgent(BaseAWorldAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        os.makedirs(os.path.join(os.getcwd(), "static"), exist_ok=True)

    async def run(self, prompt: str = None, request: ChatCompletionRequest = None):
        llm_provider = os.getenv("LLM_PROVIDER", "openai")
        llm_model_name = os.getenv("LLM_MODEL_NAME")
        llm_api_key = os.getenv("LLM_API_KEY")
        llm_base_url = os.getenv("LLM_BASE_URL")
        llm_temperature = float(os.getenv("LLM_TEMPERATURE", 0.0))

        if not llm_model_name or not llm_api_key or not llm_base_url:
            raise ValueError(
                "LLM_MODEL_NAME, LLM_API_KEY, LLM_BASE_URL must be set in your envrionment variables"
            )

        runner = GaiaAgentRunner(
            llm_provider=llm_provider,
            llm_model_name=llm_model_name,
            llm_base_url=llm_base_url,
            llm_api_key=llm_api_key,
            llm_temperature=llm_temperature,
            session_id=request.session_id,
        )

        if prompt is None and request is not None:
            prompt = request.messages[-1].content

        logger.info(f">>> Gaia Agent: prompt={prompt}, runner={runner}")

        async for line in runner.run(prompt):
            logger.info(f">>> Gaia Agent Line: {line}")
            yield line
