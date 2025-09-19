from typing import Any

from pydantic import BaseModel

from tau_bench.model_utils.api.datapoint import Datapoint
from tau_bench.model_utils.model.vllm_completion import VLLMCompletionModel
from tau_bench.model_utils.model.vllm_utils import generate_request


class OutlinesCompletionModel(VLLMCompletionModel):
    def parse_force_from_prompt(
        self, prompt: str, typ: BaseModel, temperature: float | None = None
    ) -> dict[str, Any]:
        if temperature is None:
            temperature = self.temperature
        schema = typ.model_json_schema()
        res = generate_request(
            url=self.url,
            prompt=prompt,
            force_json=True,
            schema=schema,
            temperature=temperature,
        )
        return self.handle_parse_force_response(prompt=prompt, content=res)

    def get_approx_cost(self, dp: Datapoint) -> float:
        return super().get_approx_cost(dp)

    def get_latency(self, dp: Datapoint) -> float:
        return super().get_latency(dp)

    def get_capability(self) -> float:
        return super().get_capability()

    def supports_dp(self, dp: Datapoint) -> bool:
        return super().supports_dp(dp)
