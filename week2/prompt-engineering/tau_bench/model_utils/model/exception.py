from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


class ModelError(Exception):
    def __init__(
        self,
        short_message: str,
        prompt: str | list[dict[str, str]] | None = None,
        response: str | None = None,
    ) -> None:
        super().__init__(short_message)
        self.short_message = short_message
        self.prompt = prompt
        self.response = response


@dataclass
class Result(Generic[T]):
    value: T | None
    error: ModelError | None
