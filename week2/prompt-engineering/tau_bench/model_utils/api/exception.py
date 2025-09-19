import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, TypeVar

from tau_bench.model_utils.model.exception import ModelError, Result

T = TypeVar("T")

_REPORT_DIR = os.path.expanduser("~/.llm-primitives/log")


def set_report_dir(path: str) -> None:
    global _REPORT_DIR
    _REPORT_DIR = path


def get_report_dir() -> str:
    return _REPORT_DIR


def log_report_to_disk(report: dict[str, Any], path: str) -> None:
    with open(path, "w") as f:
        json.dump(report, f, indent=4)


def generate_report_location() -> str:
    if not os.path.exists(_REPORT_DIR):
        os.makedirs(_REPORT_DIR)
    return os.path.join(_REPORT_DIR, f"report-{time.time_ns()}.json")


class APIError(Exception):
    def __init__(self, short_message: str, report: dict[str, Any] | None = None) -> None:
        self.report_path = generate_report_location()
        self.short_message = short_message
        self.report = report
        if self.report is not None:
            log_report_to_disk(
                report={"error_type": "APIError", "report": report}, path=self.report_path
            )
        super().__init__(f"{short_message}\n\nSee the full report at {self.report_path}")


def execute_and_filter_model_errors(
    funcs: list[Callable[[], T]],
    max_concurrency: int | None = None,
) -> list[T] | list[ModelError]:
    def _invoke_w_o_llm_error(invocable: Callable[[], T]) -> Result:
        try:
            return Result(value=invocable(), error=None)
        except ModelError as e:
            return Result(value=None, error=e)

    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        results = list(executor.map(_invoke_w_o_llm_error, funcs))

    errors: list[ModelError] = []
    values = []
    for res in results:
        if res.error is not None:
            errors.append(res.error)
        else:
            values.append(res.value)
    if len(values) == 0:
        assert len(errors) > 0
        raise errors[0]
    return values
