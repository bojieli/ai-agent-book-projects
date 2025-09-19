from __future__ import annotations

import abc
import json
from typing import Any, Callable, TypeVar

from pydantic import BaseModel

import tau_bench.model_utils
from tau_bench.model_utils.api._model_methods import MODEL_METHODS
from tau_bench.model_utils.api.exception import APIError
from tau_bench.model_utils.api.types import PartialObj
from tau_bench.model_utils.model.exception import ModelError

T = TypeVar("T", bound=BaseModel)


def _is_trace(obj: dict[str, Any]) -> bool:
    return (
        "method_name" in obj
        and obj["method_name"] in MODEL_METHODS
        and "kwargs" in obj
        and "response" in obj
        and isinstance(obj["kwargs"], dict)
    )


def dict_equal(d1: dict, d2: dict) -> bool:
    d1_keys_sorted = sorted(d1.keys())
    d2_keys_sorted = sorted(d2.keys())
    if d1_keys_sorted != d2_keys_sorted:
        return False
    for k in d1_keys_sorted:
        if isinstance(d1[k], dict) and isinstance(d2[k], dict):
            if not dict_equal(d1[k], d2[k]):
                return False
        elif isinstance(d1[k], list) and isinstance(d2[k], list):
            if not list_equal(d1[k], d2[k]):
                return False
        elif isinstance(d1[k], set) and isinstance(d2[k], set):
            if d1[k] != d2[k]:
                return False
        elif isinstance(d1[k], str) and isinstance(d2[k], str):
            if not str_equal(d1[k], d2[k]):
                return False
        elif d1[k] != d2[k]:
            return False
    return True


def list_equal(l1: list, l2: list) -> bool:
    if len(l1) != len(l2):
        return False
    for i1, i2 in zip(l1, l2):
        if isinstance(i1, dict) and isinstance(i2, dict):
            if not dict_equal(i1, i2):
                return False
        elif isinstance(i1, list) and isinstance(i2, list):
            if not list_equal(i1, i2):
                return False
        elif isinstance(i1, set) and isinstance(i2, set):
            if i1 != i2:
                return False
        elif isinstance(i1, str) and isinstance(i2, str):
            if not str_equal(i1, i2):
                return False
        elif i1 != i2:
            return False
    return True


def set_equal(s1: set, s2: set) -> bool:
    if len(s1) != len(s2):
        return False
    for i1, i2 in zip(s1, s2):
        if isinstance(i1, dict) and isinstance(i2, dict):
            if not dict_equal(i1, i2):
                return False
        elif isinstance(i1, list) and isinstance(i2, list):
            if not list_equal(i1, i2):
                return False
        elif isinstance(i1, set) and isinstance(i2, set):
            if i1 != i2:
                return False
        elif isinstance(i1, str) and isinstance(i2, str):
            if not str_equal(i1, i2):
                return False
        elif i1 != i2:
            return False
    return True


def str_equal(s1: str, s2: str) -> bool:
    def remove_special_chars(s: str) -> str:
        return "".join(filter(str.isalnum, s))

    def strip_and_lower(s: str) -> str:
        return s.lower().strip()

    return strip_and_lower(remove_special_chars(s1)) == strip_and_lower(remove_special_chars(s2))


class EvaluationResult(BaseModel):
    is_error: bool
    is_correct: bool
    datapoint: dict[str, Any] | None
    response: Any | None
    error: str | None


class Datapoint(BaseModel, abc.ABC):
    @classmethod
    def from_trace(cls, d: dict[str, Any]) -> "Datapoint":
        if not _is_trace(d):
            raise ValueError(f"This is not a trace: {d}")
        response = d["response"]
        kwargs = d["kwargs"]
        return cls(response=response, **kwargs)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Datapoint":
        if _is_trace(d):
            return cls.from_trace(d)
        return cls(**d)

    @abc.abstractmethod
    def evaluate(self, api: tau_bench.model_utils.API) -> EvaluationResult:
        raise NotImplementedError


class ClassifyDatapoint(Datapoint):
    instruction: str
    text: str
    options: list[str]
    response: int | None = None
    examples: list["ClassifyDatapoint"] | None = None

    def evaluate(self, api: tau_bench.model_utils.API) -> EvaluationResult:
        return run_and_catch_api_error(
            lambda: api.classify(
                instruction=self.instruction,
                text=self.text,
                options=self.options,
                examples=self.examples,
            ),
            self.response,
            self.model_dump(),
        )


class BinaryClassifyDatapoint(Datapoint):
    instruction: str
    text: str
    response: bool | None = None
    examples: list["BinaryClassifyDatapoint"] | None = None

    def evaluate(self, api: tau_bench.model_utils.API) -> EvaluationResult:
        return run_and_catch_api_error(
            lambda: api.binary_classify(
                instruction=self.instruction, text=self.text, examples=self.examples
            ),
            self.response,
            self.model_dump(),
        )


class ScoreDatapoint(Datapoint):
    instruction: str
    text: str
    min: int
    max: int
    response: int | None = None
    examples: list["ScoreDatapoint"] | None = None

    def evaluate(self, api: tau_bench.model_utils.API) -> EvaluationResult:
        raise NotImplementedError


class ParseDatapoint(Datapoint):
    text: str
    typ: type[T] | dict[str, Any]
    response: dict[str, Any] | T | PartialObj | None = None
    examples: list["ParseDatapoint"] | None = None

    def evaluate(self, api: tau_bench.model_utils.API) -> EvaluationResult:
        return run_and_catch_api_error(
            lambda: api.parse(text=self.text, typ=self.typ),
            self.response,
            self.model_dump(),
        )


class GenerateDatapoint(Datapoint):
    instruction: str
    text: str
    response: str | None = None
    examples: list["GenerateDatapoint"] | None = None

    def evaluate(self, api: tau_bench.model_utils.API) -> tau_bench.model_utils.EvaluationResult:
        raise NotImplementedError


class ParseForceDatapoint(Datapoint):
    instruction: str
    typ: type[T] | dict[str, Any]
    text: str | None = None
    response: dict[str, Any] | T | None = None
    examples: list["ParseForceDatapoint"] | None = None

    def evaluate(self, api: tau_bench.model_utils.API) -> EvaluationResult:
        return run_and_catch_api_error(
            lambda: api.parse_force(
                instruction=self.instruction,
                text=self.text,
                typ=self.typ,
                examples=self.examples,
            ),
            self.response,
            self.model_dump(),
        )


def datapoint_factory(d: dict[str, Any]) -> Datapoint:
    if _is_trace(d):
        method_name = d["method_name"]
        kwargs = d["kwargs"]
        data = {"response": d["response"], **kwargs}
        if method_name == "classify":
            return ClassifyDatapoint(**data)
        elif method_name == "binary_classify":
            return BinaryClassifyDatapoint(**data)
        elif method_name == "parse":
            return ParseDatapoint(**data)
        elif method_name == "parse_force":
            return ParseForceDatapoint(**data)
        elif method_name == "generate":
            return GenerateDatapoint(**data)
        elif method_name == "score":
            return ScoreDatapoint(**data)
        else:
            raise ValueError(f"Unknown method name: {method_name}")
    else:
        if all(k in d for k in ["instruction", "text", "options"]) and isinstance(
            d["response"], int
        ):
            return ClassifyDatapoint(**d)
        elif all(k in d for k in ["instruction", "text"]) and isinstance(d["response"], bool):
            return BinaryClassifyDatapoint(**d)
        elif all(k in d for k in ["instruction", "text", "min", "max"]) and isinstance(
            d["response"], int
        ):
            return ScoreDatapoint(**d)
        elif all(k in d for k in ["instruction", "text", "typ"]) and isinstance(
            d["response"], dict
        ):
            return ParseForceDatapoint(**d)
        elif all(k in d for k in ["text", "typ"]) and isinstance(d["response"], dict):
            return ParseDatapoint(**d)
        elif all(k in d for k in ["instruction", "text"]) and isinstance(d["response"], str):
            return GenerateDatapoint(**d)
        else:
            raise ValueError(f"Unknown datapoint: {d}")


def run_and_catch_api_error(
    callable: Callable[..., Any], response: Any, datapoint: dict[str, Any]
) -> EvaluationResult:
    try:
        res = callable()
        if isinstance(response, dict):
            is_correct = dict_equal(res, response)
        else:
            is_correct = res == response
        return EvaluationResult(
            is_error=False,
            is_correct=is_correct,
            response=res,
            error=None,
            datapoint=datapoint,
        )
    except (APIError, ModelError) as e:
        return EvaluationResult(
            is_error=True,
            is_correct=False,
            response=None,
            error=str(e),
            datapoint=datapoint,
        )


def load_from_disk(path: str) -> list[Datapoint]:
    with open(path, "r") as f:
        if path.endswith(".jsonl"):
            data = [json.loads(line) for line in f]
        elif path.endswith(".json"):
            data = json.load(f)
        else:
            raise ValueError(f"Unknown file format: {path}")
    return [datapoint_factory(d) for d in data]
