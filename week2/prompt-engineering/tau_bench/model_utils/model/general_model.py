import abc
from typing import Any, TypeVar

from pydantic import BaseModel

from tau_bench.model_utils.api.datapoint import (
    BinaryClassifyDatapoint,
    ClassifyDatapoint,
    GenerateDatapoint,
    ParseDatapoint,
    ParseForceDatapoint,
    ScoreDatapoint,
)
from tau_bench.model_utils.api.types import PartialObj
from tau_bench.model_utils.model.model import (
    BinaryClassifyModel,
    ClassifyModel,
    GenerateModel,
    ParseForceModel,
    ParseModel,
    Platform,
    ScoreModel,
)

T = TypeVar("T", bound=BaseModel)

LLM_SAMPLING_TEMPERATURE_EPS = 1e-5


def wrap_temperature(temperature: float) -> float:
    return max(temperature, LLM_SAMPLING_TEMPERATURE_EPS)


class GeneralModel(
    ClassifyModel,
    BinaryClassifyModel,
    ParseModel,
    GenerateModel,
    ParseForceModel,
    ScoreModel,
):
    @abc.abstractmethod
    def classify(
        self,
        instruction: str,
        text: str,
        options: list[str],
        examples: list[ClassifyDatapoint] | None = None,
        temperature: float | None = None,
    ) -> int:
        raise NotImplementedError

    def binary_classify(
        self,
        instruction: str,
        text: str,
        examples: list[BinaryClassifyDatapoint] | None = None,
        temperature: float | None = None,
    ) -> bool:
        return (
            self.classify(
                instruction,
                text,
                ["true", "false"],
                examples=(
                    None
                    if examples is None
                    else [
                        ClassifyDatapoint(
                            instruction=example.instruction,
                            text=example.text,
                            options=["true", "false"],
                            response=0 if example.response else 1,
                        )
                        for example in examples
                    ]
                ),
                temperature=temperature,
            )
            == 0
        )

    @abc.abstractmethod
    def parse(
        self,
        text: str,
        typ: type[T] | dict[str, Any],
        examples: list[ParseDatapoint] | None = None,
        temperature: float | None = None,
    ) -> T | PartialObj | dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def generate(
        self,
        instruction: str,
        text: str,
        examples: list[GenerateDatapoint] | None = None,
        temperature: float | None = None,
    ) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def parse_force(
        self,
        instruction: str,
        typ: type[T] | dict[str, Any],
        text: str | None = None,
        examples: list[ParseForceDatapoint] | None = None,
        temperature: float | None = None,
    ) -> T | dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def score(
        self,
        instruction: str,
        text: str,
        min: int,
        max: int,
        examples: list[ScoreDatapoint] | None = None,
        temperature: float | None = None,
    ) -> int:
        raise NotImplementedError


def default_model() -> GeneralModel:
    from tau_bench.model_utils.model.openai import OpenAIModel

    return OpenAIModel()


def default_quick_model() -> GeneralModel:
    from tau_bench.model_utils.model.openai import OpenAIModel

    return OpenAIModel(model="gpt-4o-mini")


def model_factory(
    model_id: str,
    platform: str | Platform,
    base_url: str | None = None,
    api_key: str | None = None,
    temperature: float = 0.0,
) -> GeneralModel:
    if isinstance(platform, str):
        platform = Platform(platform)
    if platform == Platform.OPENAI:
        from tau_bench.model_utils.model.openai import OpenAIModel

        return OpenAIModel(model=model_id, api_key=api_key, temperature=temperature)
    elif platform == Platform.MISTRAL:
        from tau_bench.model_utils.model.mistral import MistralModel

        return MistralModel(model=model_id, api_key=api_key, temperature=temperature)
    elif platform == Platform.ANTHROPIC:
        from tau_bench.model_utils.model.claude import ClaudeModel

        return ClaudeModel(model=model_id, api_key=api_key, temperature=temperature)

    elif platform == Platform.ANYSCALE:
        from tau_bench.model_utils.model.anyscale import AnyscaleModel

        return AnyscaleModel(model=model_id, api_key=api_key, temperature=temperature)
    elif platform == Platform.OUTLINES:
        if base_url is None:
            raise ValueError("base_url must be provided for custom models")
        from tau_bench.model_utils.model.outlines_completion import OutlinesCompletionModel

        return OutlinesCompletionModel(model=model_id, base_url=base_url, temperature=temperature)
    elif platform == Platform.VLLM_CHAT:
        if base_url is None:
            raise ValueError("base_url must be provided for custom models")
        from tau_bench.model_utils.model.vllm_chat import VLLMChatModel

        return VLLMChatModel(
            model=model_id,
            base_url=base_url,
            api_key="sk-no-api-key-required" if api_key is None else api_key,
            temperature=temperature,
        )
    else:
        if base_url is None:
            raise ValueError("base_url must be provided for custom models")
        from tau_bench.model_utils.model.vllm_completion import VLLMCompletionModel

        return VLLMCompletionModel(model=model_id, base_url=base_url, temperature=temperature)
