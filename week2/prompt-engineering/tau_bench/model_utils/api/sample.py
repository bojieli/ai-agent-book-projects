import abc
import functools
from multiprocessing import Lock
from typing import Any, Callable, TypeVar

from pydantic import BaseModel

from tau_bench.model_utils.api.exception import APIError, execute_and_filter_model_errors
from tau_bench.model_utils.model.exception import ModelError
from tau_bench.model_utils import func_tools

T = TypeVar("T")


class SamplingStrategy(abc.ABC):
    @abc.abstractmethod
    def execute(self, invocable_or_invokables: Callable[..., T] | list[Callable[..., T]]) -> T:
        raise NotImplementedError


def catch_model_errors(func: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except ModelError as e:
            raise APIError(
                short_message=str(e),
                report={
                    "prompt": e.prompt,
                    "response": e.response,
                    "error_message": str(e),
                },
            )

    return wrapper


class SingleSamplingStrategy(SamplingStrategy):
    @catch_model_errors
    def execute(self, invocable_or_invokables: Callable[..., T]) -> T:
        assert isinstance(invocable_or_invokables, Callable)
        return invocable_or_invokables()


class RedundantSamplingStrategy(SamplingStrategy):
    def __init__(self, n: int = 2) -> None:
        assert n > 0
        self.n = n

    @catch_model_errors
    def execute(self, invocable_or_invokables: Callable[..., T] | list[Callable[..., T]]) -> T:
        results = execute_and_filter_model_errors(
            [lambda: invocable_or_invokables() for _ in range(self.n)]
            if isinstance(invocable_or_invokables, Callable)
            else invocable_or_invokables
        )
        assert len(results) > 0
        return results[0]


class RetrySamplingStrategy(SamplingStrategy):
    def __init__(self, max_retries: int = 5) -> None:
        assert max_retries > 0
        self.max_retries = max_retries

    @catch_model_errors
    def execute(self, invocable_or_invokables: Callable[..., T]) -> T:
        assert isinstance(invocable_or_invokables, Callable)
        first_error = None
        for _ in range(self.max_retries):
            try:
                return invocable_or_invokables()
            except ModelError as e:
                if first_error is None:
                    first_error = e
        assert first_error is not None
        raise first_error


class MajoritySamplingStrategy(SamplingStrategy):
    def __init__(
        self,
        n: int = 5,
        max_concurrency: int | None = None,
        panic_on_first_model_error: bool = False,
    ) -> None:
        self.n = n
        self.max_concurrency = max_concurrency if max_concurrency is not None else n
        self.panic_on_first_model_error = panic_on_first_model_error

    @catch_model_errors
    def execute(self, invocable_or_invokables: Callable[..., T] | list[Callable[..., T]]) -> T:
        if self.panic_on_first_model_error:
            if isinstance(invocable_or_invokables, Callable):
                results = list(
                    func_tools.map(
                        lambda _: invocable_or_invokables(),
                        range(self.n),
                        max_concurrency=self.max_concurrency,
                    )
                )
            else:
                results = list(
                    func_tools.map(
                        lambda invocable: invocable(),
                        invocable_or_invokables,
                        max_concurrency=self.max_concurrency,
                    )
                )
        else:
            results = execute_and_filter_model_errors(
                (
                    [lambda: invocable_or_invokables() for _ in range(self.n)]
                    if isinstance(invocable_or_invokables, Callable)
                    else invocable_or_invokables
                ),
                max_concurrency=self.max_concurrency,
            )
        if not self.panic_on_first_model_error and len(results) == 0:
            raise SamplingError(
                "No results from majority sampling (all calls resulted in LLM errors)"
            )
        return get_majority(results)


def get_majority(results: list[T]) -> T:
    grouped: dict[str, Any] = {}
    for result in results:
        if isinstance(result, BaseModel):
            key = result.model_dump_json()
        else:
            key = str(result)
        if key not in grouped:
            # for now, just store duplicate results for the count
            grouped[key] = [result]
        else:
            grouped[key].append(result)
    majority = max(grouped, key=lambda key: len(grouped[key]))
    return grouped[majority][0]


class EnsembleSamplingStrategy(SamplingStrategy):
    def __init__(
        self, max_concurrency: int | None = None, panic_on_first_model_error: bool = False
    ) -> None:
        self.max_concurrency = max_concurrency
        self.panic_on_first_model_error = panic_on_first_model_error

    @catch_model_errors
    def execute(self, invocable_or_invokables: Callable[..., T] | list[Callable[..., T]]) -> T:
        if not isinstance(invocable_or_invokables, list) or len(invocable_or_invokables) < 2:
            raise ValueError("Ensemble sampling requires at least 2 invocables")
        if self.panic_on_first_model_error:
            results = list(
                func_tools.map(
                    lambda invocable: invocable(),
                    invocable_or_invokables,
                    max_concurrency=self.max_concurrency,
                )
            )
        else:
            results = execute_and_filter_model_errors(
                invocable_or_invokables, max_concurrency=self.max_concurrency
            )
        if not self.panic_on_first_model_error and len(results) == 0:
            raise SamplingError(
                "No results from ensemble sampling (all calls resulted in LLM errors)"
            )
        return get_majority(results)


class UnanimousSamplingStrategy(SamplingStrategy):
    def __init__(
        self,
        n: int = 5,
        max_concurrency: int | None = None,
        panic_on_first_model_error: bool = False,
    ) -> None:
        self.n = n
        self.max_concurrency = max_concurrency if max_concurrency is not None else n
        self.panic_on_first_model_error = panic_on_first_model_error

    @catch_model_errors
    def execute(self, invocable_or_invokables: Callable[..., T] | list[Callable[..., T]]) -> T:
        if self.panic_on_first_model_error:
            if isinstance(invocable_or_invokables, Callable):
                results = list(
                    func_tools.map(
                        lambda _: invocable_or_invokables(),
                        range(self.n),
                        max_concurrency=self.max_concurrency,
                    )
                )
            else:
                results = list(
                    func_tools.map(
                        lambda invocable: invocable(),
                        invocable_or_invokables,
                        max_concurrency=self.max_concurrency,
                    )
                )
        else:
            results = execute_and_filter_model_errors(
                (
                    [lambda: invocable_or_invokables() for _ in range(self.n)]
                    if isinstance(invocable_or_invokables, Callable)
                    else invocable_or_invokables
                ),
                max_concurrency=self.max_concurrency,
            )
        if len(set(results)) > 1:
            raise SamplingError("Results are not unanimous")
        return results[0]


class SamplingError(Exception):
    pass


DEFAULT_SAMPLING_STRATEGY = SingleSamplingStrategy()
_DEFAULT_SAMPLING_STRATEGY_LOCK = Lock()


def set_default_sampling_strategy(strategy: SamplingStrategy) -> None:
    with _DEFAULT_SAMPLING_STRATEGY_LOCK:
        global DEFAULT_SAMPLING_STRATEGY
        DEFAULT_SAMPLING_STRATEGY = strategy


def get_default_sampling_strategy() -> SamplingStrategy:
    with _DEFAULT_SAMPLING_STRATEGY_LOCK:
        return DEFAULT_SAMPLING_STRATEGY
