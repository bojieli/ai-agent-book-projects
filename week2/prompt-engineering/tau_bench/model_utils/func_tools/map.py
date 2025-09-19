from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
U = TypeVar("U")


def map(
    func: Callable[[T], U],
    iterable: Iterable[T],
    max_concurrency: int | None = None,
    use_tqdm: bool = False,
) -> Iterable[U]:
    assert max_concurrency is None or max_concurrency > 0
    with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
        if use_tqdm:
            from tqdm import tqdm

            return list(tqdm(executor.map(func, iterable), total=len(iterable)))
        return executor.map(func, iterable)
