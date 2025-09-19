from tau_bench.model_utils.api.datapoint import Datapoint
from tau_bench.model_utils.model.chat import ChatModel, Message
from tau_bench.model_utils.model.completion import approx_cost_for_datapoint, approx_prompt_str
from tau_bench.model_utils.model.general_model import wrap_temperature
from tau_bench.model_utils.model.utils import approx_num_tokens

PRICE_PER_INPUT_TOKEN_MAP = {
    "Qwen/Qwen2-0.5B-Instruct": 0.0,
    "Qwen/Qwen2-1.5B-Instruct": 0.0,
    "Qwen/Qwen2-7B-Instruct": 0.0,
    "Qwen/Qwen2-72B-Instruct": 0.0,
    "meta-llama/Meta-Llama-3.1-8B-Instruct": 0.0,
    "sierra-research/Meta-Llama-3.1-8B-Instruct": 0.0,
    "meta-llama/Meta-Llama-3.1-70B-Instruct": 0.0,
    "mistralai/Mistral-Nemo-Instruct-2407": 0.0,
}
INPUT_PRICE_PER_TOKEN_FALLBACK = 0.0

# TODO: refine this
CAPABILITY_SCORE_MAP = {
    "Qwen/Qwen2-0.5B-Instruct": 0.05,
    "Qwen/Qwen2-1.5B-Instruct": 0.07,
    "Qwen/Qwen2-7B-Instruct": 0.2,
    "Qwen/Qwen2-72B-Instruct": 0.4,
    "meta-llama/Meta-Llama-3.1-8B-Instruct": 0.3,
    "sierra-research/Meta-Llama-3.1-8B-Instruct": 0.3,
    "meta-llama/Meta-Llama-3.1-70B-Instruct": 0.4,
    "mistralai/Mistral-Nemo-Instruct-2407": 0.3,
}
CAPABILITY_SCORE_FALLBACK = 0.3

# TODO: implement
LATENCY_MS_PER_OUTPUT_TOKEN_MAP = {}
# TODO: implement
LATENCY_MS_PER_OUTPUT_TOKEN_FALLBACK = 0.0

MAX_CONTEXT_LENGTH_MAP = {
    "Qwen/Qwen2-0.5B-Instruct": 32768,
    "Qwen/Qwen2-1.5B-Instruct": 32768,
    "Qwen/Qwen2-7B-Instruct": 131072,
    "Qwen/Qwen2-72B-Instruct": 131072,
    "meta-llama/Meta-Llama-3.1-8B-Instruct": 128000,
    "sierra-research/Meta-Llama-3.1-8B-Instruct": 128000,
    "meta-llama/Meta-Llama-3.1-70B-Instruct": 128000,
    "mistralai/Mistral-Nemo-Instruct-2407": 128000,
}
MAX_CONTEXT_LENGTH_FALLBACK = 128000


class VLLMChatModel(ChatModel):
    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str,
        temperature: float = 0.0,
        price_per_input_token: float | None = None,
        capability: float | None = None,
        latency_ms_per_output_token: float | None = None,
        max_context_length: int | None = None,
    ) -> None:
        from openai import AsyncOpenAI, OpenAI

        self.model = model
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.async_client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        self.temperature = temperature
        self.price_per_input_token = (
            price_per_input_token
            if price_per_input_token is not None
            else PRICE_PER_INPUT_TOKEN_MAP.get(model, INPUT_PRICE_PER_TOKEN_FALLBACK)
        )
        self.capability = (
            capability
            if capability is not None
            else CAPABILITY_SCORE_MAP.get(model, CAPABILITY_SCORE_FALLBACK)
        )
        self.latency_ms_per_output_token = (
            latency_ms_per_output_token
            if latency_ms_per_output_token is not None
            else LATENCY_MS_PER_OUTPUT_TOKEN_MAP.get(model, LATENCY_MS_PER_OUTPUT_TOKEN_FALLBACK)
        )
        self.max_context_length = (
            max_context_length
            if max_context_length is not None
            else MAX_CONTEXT_LENGTH_MAP.get(model, MAX_CONTEXT_LENGTH_FALLBACK)
        )

    def get_approx_cost(self, dp: Datapoint) -> float:
        cost_per_token = self.price_per_input_token
        return approx_cost_for_datapoint(dp=dp, price_per_input_token=cost_per_token)

    def get_latency(self, dp: Datapoint) -> float:
        latency_per_output_token = self.latency_ms_per_output_token
        return approx_cost_for_datapoint(dp=dp, price_per_input_token=latency_per_output_token)

    def get_capability(self) -> float:
        return CAPABILITY_SCORE_MAP.get(self.model, CAPABILITY_SCORE_FALLBACK)

    def supports_dp(self, dp: Datapoint) -> bool:
        prompt = approx_prompt_str(dp)
        return approx_num_tokens(prompt) <= self.max_context_length

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
            temperature=wrap_temperature(temperature=temperature),
        )
        return self.handle_generate_message_response(
            prompt=msgs, content=res.choices[0].message.content, force_json=force_json
        )

    def force_json_prompt(self, text: str, _: bool = False) -> str:
        return super().force_json_prompt(text, with_prefix=True)
