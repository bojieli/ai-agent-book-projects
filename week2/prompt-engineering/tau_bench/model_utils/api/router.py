import abc

from pydantic import BaseModel

from tau_bench.model_utils.api.datapoint import Datapoint, ScoreDatapoint
from tau_bench.model_utils.model.model import Model


class RequestRouter(abc.ABC):
    @abc.abstractmethod
    def route(self, dp: Datapoint, available_models: list[Model]) -> Model:
        raise NotImplementedError


class FirstModelRequestRouter(RequestRouter):
    def route(self, dp: Datapoint, available_models: list[Model]) -> Model:
        supporting_models = [model for model in available_models if model.supports_dp(dp)]
        if len(supporting_models) == 0:
            raise ValueError(f"No supporting models found from {available_models}")
        return supporting_models[0]


class CapabilityScoreModel(abc.ABC):
    @abc.abstractmethod
    def score_dp(self, dp: Datapoint) -> float:
        raise NotImplementedError


class PromptedLLMCapabilityScoreModel:
    def __init__(self, model: Model | None = None) -> None:
        if model is None:
            from tau_bench.model_utils.model.claude import ClaudeModel

            # claude is used as the default model as it is better at meta-level tasks
            model = ClaudeModel()
        self.model = model

    def score_dp(self, dp: Datapoint, examples: list[ScoreDatapoint] | None = None) -> float:
        return (
            self.model.score(
                instruction="Score the task in the datapoint on a scale of 1 (least complex) to 10 (most complex).",
                text=f"----- start task -----\n{dp.model_dump_json()}\n----- end task -----",
                min=1,
                max=10,
                examples=examples,
            )
            / 10.0
        )


class MinimumCapabilityRequestRouter(RequestRouter):
    def __init__(self, capability_score_model: CapabilityScoreModel) -> None:
        self.capability_score_model = capability_score_model

    def route(self, dp: Datapoint, available_models: list[Model]) -> Model:
        supporting_models = [model for model in available_models if model.supports_dp(dp)]
        if len(supporting_models) == 0:
            raise ValueError(f"No supporting models found from {available_models}")
        required_capability = self.capability_score_model.score_dp(dp)
        minimum_model: Model | None = None
        minimum_model_capability: float | None = None
        for model in supporting_models:
            capability = model.get_capability()
            if capability >= required_capability and (
                minimum_model_capability is None or capability < minimum_model_capability
            ):
                minimum_model = model
                minimum_model_capability = capability
        if minimum_model is None:
            raise ValueError(f"No model found with capability >= {required_capability}")
        return minimum_model


def request_router_factory(
    router_id: str, capability_score_model: CapabilityScoreModel | None = None
) -> RequestRouter:
    if router_id == "first-model":
        return FirstModelRequestRouter()
    elif router_id == "minimum-capability":
        if capability_score_model is None:
            raise ValueError("CapabilityScoreModel is required for minimum-capability router")
        return MinimumCapabilityRequestRouter(capability_score_model=capability_score_model)
    raise ValueError(f"Unknown router_id: {router_id}")


def default_request_router() -> RequestRouter:
    return FirstModelRequestRouter()


class RequestRouteDatapoint(BaseModel):
    dp: Datapoint
    capability_score: float
