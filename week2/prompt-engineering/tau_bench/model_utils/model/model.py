import abc
import enum
from typing import Any, TypeVar

from pydantic import BaseModel

from tau_bench.model_utils.api.datapoint import (
    BinaryClassifyDatapoint,
    ClassifyDatapoint,
    Datapoint,
    GenerateDatapoint,
    ParseDatapoint,
    ParseForceDatapoint,
    ScoreDatapoint,
)
from tau_bench.model_utils.api.types import PartialObj

T = TypeVar("T", bound=BaseModel)


class Platform(enum.Enum):
    OPENAI = "openai"
    MISTRAL = "mistral"
    ANTHROPIC = "anthropic"
    ANYSCALE = "anyscale"
    OUTLINES = "outlines"
    VLLM_CHAT = "vllm-chat"
    VLLM_COMPLETION = "vllm-completion"


# @runtime_checkable
# class Model(Protocol):
class Model(abc.ABC):
    @abc.abstractmethod
    def get_capability(self) -> float:
        """Return the capability of the model, a float between 0.0 and 1.0."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_approx_cost(self, dp: Datapoint) -> float:
        raise NotImplementedError

    @abc.abstractmethod
    def get_latency(self, dp: Datapoint) -> float:
        raise NotImplementedError

    @abc.abstractmethod
    def supports_dp(self, dp: Datapoint) -> bool:
        raise NotImplementedError


class ClassifyModel(Model):
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


class BinaryClassifyModel(Model):
    @abc.abstractmethod
    def binary_classify(
        self,
        instruction: str,
        text: str,
        examples: list[BinaryClassifyDatapoint] | None = None,
        temperature: float | None = None,
    ) -> bool:
        raise NotImplementedError


class ParseModel(Model):
    @abc.abstractmethod
    def parse(
        self,
        text: str,
        typ: type[T] | dict[str, Any],
        examples: list[ParseDatapoint] | None = None,
        temperature: float | None = None,
    ) -> T | PartialObj | dict[str, Any]:
        raise NotImplementedError


class GenerateModel(Model):
    @abc.abstractmethod
    def generate(
        self,
        instruction: str,
        text: str,
        examples: list[GenerateDatapoint] | None = None,
        temperature: float | None = None,
    ) -> str:
        raise NotImplementedError


class ParseForceModel(Model):
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


class ScoreModel(Model):
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


AnyModel = (
    BinaryClassifyModel | ClassifyModel | ParseForceModel | GenerateModel | ParseModel | ScoreModel
)
