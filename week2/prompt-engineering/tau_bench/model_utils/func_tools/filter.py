from typing import Callable, Iterable, TypeVar

from tau_bench.model_utils.func_tools.map import map

T = TypeVar("T")

builtin_filter = filter


def filter(
    func: Callable[[T], bool],
    iterable: Iterable[T],
    max_concurrency: int | None = None,
) -> Iterable[T]:
    assert max_concurrency is None or max_concurrency > 0
    bits = map(func, iterable=iterable, max_concurrency=max_concurrency)
    return [x for x, y in zip(iterable, bits) if y]
