import json
import os

from tau_bench.model_utils.api.datapoint import Datapoint
from tau_bench.model_utils.model.chat import ChatModel, Message
from tau_bench.model_utils.model.completion import approx_cost_for_datapoint, approx_prompt_str
from tau_bench.model_utils.model.general_model import wrap_temperature
from tau_bench.model_utils.model.utils import approx_num_tokens

DEFAULT_CLAUDE_MODEL = "claude-3-5-sonnet-20240620"
DEFAULT_MAX_TOKENS = 8192
ENV_VAR_API_KEY = "ANTHROPIC_API_KEY"

PRICE_PER_INPUT_TOKEN_MAP = {
    "claude-3-5-sonnet-20240620": 3 / 1000000,
}
INPUT_PRICE_PER_TOKEN_FALLBACK = 15 / 1000000

CAPABILITY_SCORE_MAP = {
    "claude-3-5-sonnet-20240620": 1.0,
}
CAPABILITY_SCORE_FALLBACK = 0.5

# TODO: implement
LATENCY_MS_PER_OUTPUT_TOKEN_MAP = {}
# TODO: implement
LATENCY_MS_PER_OUTPUT_TOKEN_FALLBACK = 0.0

MAX_CONTEXT_LENGTH_MAP = {
    "claude-3-5-sonnet-20240620": 8192,
}
MAX_CONTEXT_LENGTH_FALLBACK = 8192


class ClaudeModel(ChatModel):
    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.0,
    ) -> None:
        from anthropic import Anthropic, AsyncAnthropic

        if model is None:
            self.model = DEFAULT_CLAUDE_MODEL
        else:
            self.model = model

        api_key = None
        if api_key is None:
            api_key = os.getenv(ENV_VAR_API_KEY)
            if api_key is None:
                raise ValueError(f"{ENV_VAR_API_KEY} environment variable is not set")
        # `anthropic-beta` header is needed for the 8192 context length (https://docs.anthropic.com/en/docs/about-claude/models)
        self.client = Anthropic(
            api_key=api_key, default_headers={"anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"}
        )
        self.async_client = AsyncAnthropic(api_key=api_key)
        self.temperature = temperature

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

    def _remap_messages(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        remapped: list[dict[str, str]] = []
        is_user = True
        for i, message in enumerate(messages):
            role = message["role"]
            if role == "assistant":
                if i == 0:
                    raise ValueError(
                        f"First message must be a system or user message, got {[m['role'] for m in messages]}"
                    )
                elif is_user:
                    raise ValueError(
                        f"Must alternate between user and assistant, got {[m['role'] for m in messages]}"
                    )
                remapped.append(message)
                is_user = True
            else:
                if is_user:
                    remapped.append({"role": "user", "content": message["content"]})
                    is_user = False
                else:
                    if remapped[-1]["role"] != "user":
                        raise ValueError(
                            f"Invalid sequence, expected user message but got {[m['role'] for m in messages]}"
                        )
                    remapped[-1]["content"] += "\n\n" + message["content"]
        return remapped

    def build_generate_message_state(
        self,
        messages: list[Message],
    ) -> list[dict[str, str]]:
        msgs: list[dict[str, str]] = []
        for msg in messages:
            if msg.obj is not None:
                content = json.dumps(msg.obj)
            else:
                content = msg.content
            msgs.append({"role": msg.role.value, "content": content})
        return self._remap_messages(msgs)

    def generate_message(
        self,
        messages: list[Message],
        force_json: bool,
        temperature: float | None = None,
    ) -> Message:
        if temperature is None:
            temperature = self.temperature
        msgs = self.build_generate_message_state(messages)
        res = self.client.messages.create(
            model=self.model,
            messages=msgs,
            temperature=wrap_temperature(temperature),
            max_tokens=DEFAULT_MAX_TOKENS,
        )
        return self.handle_generate_message_response(
            prompt=msgs, content=res.content[0].text, force_json=force_json
        )
