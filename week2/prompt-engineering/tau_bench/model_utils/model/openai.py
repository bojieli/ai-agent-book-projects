import os

from tau_bench.model_utils.api.datapoint import Datapoint
from tau_bench.model_utils.model.chat import ChatModel, Message
from tau_bench.model_utils.model.completion import approx_cost_for_datapoint, approx_prompt_str
from tau_bench.model_utils.model.general_model import wrap_temperature
from tau_bench.model_utils.model.utils import approx_num_tokens

DEFAULT_OPENAI_MODEL = "gpt-4o-2024-08-06"
API_KEY_ENV_VAR = "OPENAI_API_KEY"

PRICE_PER_INPUT_TOKEN_MAP = {
    "gpt-4o-2024-08-06": 2.5 / 1000000,
    "gpt-4o": 5 / 1000000,
    "gpt-4o-2024-08-06": 2.5 / 1000000,
    "gpt-4o-2024-05-13": 5 / 1000000,
    "gpt-4-turbo": 10 / 1000000,
    "gpt-4-turbo-2024-04-09": 10 / 1000000,
    "gpt-4": 30 / 1000000,
    "gpt-4o-mini": 0.15 / 1000000,
    "gpt-4o-mini-2024-07-18": 0.15 / 1000000,
    "gpt-3.5-turbo": 0.5 / 1000000,
    "gpt-3.5-turbo-0125": 0.5 / 1000000,
    "gpt-3.5-turbo-instruct": 1.5 / 1000000,
}
INPUT_PRICE_PER_TOKEN_FALLBACK = 10 / 1000000

CAPABILITY_SCORE_MAP = {
    "gpt-4o-2024-08-06": 0.8,
    "gpt-4o": 0.8,
    "gpt-4o-2024-08-06": 0.8,
    "gpt-4o-2024-05-13": 0.8,
    "gpt-4-turbo": 0.9,
    "gpt-4-turbo-2024-04-09": 0.9,
    "gpt-4": 0.8,
    "gpt-4o-mini": 0.5,
    "gpt-4o-mini-2024-07-18": 0.5,
    "gpt-3.5-turbo": 0.3,
    "gpt-3.5-turbo-0125": 0.3,
}
CAPABILITY_SCORE_FALLBACK = 0.3

# TODO: implement
LATENCY_MS_PER_OUTPUT_TOKEN_MAP = {}
# TODO: implement
LATENCY_MS_PER_OUTPUT_TOKEN_FALLBACK = 0.0

MAX_CONTEXT_LENGTH_MAP = {
    "gpt-4o-2024-08-06": 128000,
    "gpt-4o": 128000,
    "gpt-4o-2024-08-06": 128000,
    "gpt-4o-2024-05-13": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4-turbo-2024-04-09": 128000,
    "gpt-4": 8192,
    "gpt-4o-mini": 128000,
    "gpt-4o-mini-2024-07-18": 128000,
    "gpt-3.5-turbo": 16385,
    "gpt-3.5-turbo-0125": 16385,
}
MAX_CONTEXT_LENGTH_FALLBACK = 128000


class OpenAIModel(ChatModel):
    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.0,
    ) -> None:
        from openai import AsyncOpenAI, OpenAI

        if model is None:
            self.model = DEFAULT_OPENAI_MODEL
        else:
            self.model = model

        api_key = None
        if api_key is None:
            api_key = os.getenv(API_KEY_ENV_VAR)
            if api_key is None:
                raise ValueError(f"{API_KEY_ENV_VAR} environment variable is not set")
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
        self.temperature = temperature

    def generate_message(
        self,
        messages: list[Message],
        force_json: bool,
        temperature: float | None = None,
    ) -> Message:
        if temperature is None:
            temperature = self.temperature
        msgs = self.build_generate_message_state(messages)
        res = self.client.chat.completions.create(
            model=self.model,
            messages=msgs,
            temperature=wrap_temperature(temperature),
            response_format={"type": "json_object" if force_json else "text"},
        )
        return self.handle_generate_message_response(
            prompt=msgs, content=res.choices[0].message.content, force_json=force_json
        )

    def get_approx_cost(self, dp: Datapoint) -> float:
        cost_per_token = PRICE_PER_INPUT_TOKEN_MAP.get(self.model, INPUT_PRICE_PER_TOKEN_FALLBACK)
        return approx_cost_for_datapoint(dp=dp, price_per_input_token=cost_per_token)

    def get_latency(self, dp: Datapoint) -> float:
        latency_per_output_token = LATENCY_MS_PER_OUTPUT_TOKEN_MAP.get(
            self.model, LATENCY_MS_PER_OUTPUT_TOKEN_FALLBACK
        )
        return approx_cost_for_datapoint(dp=dp, price_per_input_token=latency_per_output_token)

    def get_capability(self) -> float:
        return CAPABILITY_SCORE_MAP.get(self.model, CAPABILITY_SCORE_FALLBACK)

    def supports_dp(self, dp: Datapoint) -> bool:
        prompt = approx_prompt_str(dp)
        return approx_num_tokens(prompt) <= MAX_CONTEXT_LENGTH_MAP.get(
            self.model, MAX_CONTEXT_LENGTH_FALLBACK
        )
