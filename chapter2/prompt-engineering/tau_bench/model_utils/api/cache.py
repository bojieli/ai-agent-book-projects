import functools
import inspect
import threading
from collections import defaultdict
from multiprocessing import Lock
from typing import Any, Callable, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class _CallableIdentity:
    __slots__ = ("func",)

    def __init__(self, func: Callable[..., Any]):
        self.func = func

    def __hash__(self) -> int:
        return id(self.func)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _CallableIdentity) and self.func is other.func


CacheKey = tuple[_CallableIdentity, Any]

USE_CACHE = True
_USE_CACHE_LOCK = Lock()
cache: dict[CacheKey, tuple[T, threading.Event]] = {}
lock = threading.Lock()
conditions = defaultdict(threading.Condition)


def disable_cache():
    global USE_CACHE
    with _USE_CACHE_LOCK:
        USE_CACHE = False


def enable_cache():
    global USE_CACHE
    with _USE_CACHE_LOCK:
        USE_CACHE = True


def hash_item(item: Any) -> Any:
    if isinstance(item, dict):
        return (
            "dict",
            frozenset(
                (hash_item(key), hash_item(value)) for key, value in item.items()
            ),
        )
    elif isinstance(item, list):
        return ("list", tuple(hash_item(x) for x in item))
    elif isinstance(item, set):
        return (
            "set",
            frozenset(hash_item(x) for x in item),
        )
    elif isinstance(item, tuple):
        return ("tuple", tuple(hash_item(x) for x in item))
    elif isinstance(item, BaseModel):
        values = item.model_dump() if hasattr(item, "model_dump") else item.dict()
        return (
            "model",
            type(item).__module__,
            type(item).__qualname__,
            hash_item(values),
        )
    return item


def hash_func_call(
    func: Callable[..., Any], args: tuple[Any], kwargs: dict[str, Any]
) -> CacheKey:
    bound_args = inspect.signature(func).bind(*args, **kwargs)
    bound_args.apply_defaults()
    standardized_args = sorted(bound_args.arguments.items())
    return _CallableIdentity(func), hash_item(standardized_args)


def cache_call_w_dedup(func: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        if not USE_CACHE:
            return func(*args, **kwargs)
        key = hash_func_call(func=func, args=args, kwargs=kwargs)
        if key in cache:
            result, event = cache[key]
            if event.is_set():
                return result
        else:
            with lock:
                cache[key] = (None, threading.Event())

        condition = conditions[key]
        with condition:
            if cache[key][1].is_set():
                return cache[key][0]
            if not cache[key][0]:
                try:
                    result = func(*args, **kwargs)
                    with lock:
                        cache[key] = (result, threading.Event())
                        cache[key][1].set()
                except Exception as e:
                    with lock:
                        cache[key] = (e, threading.Event())
                        cache[key][1].set()
                    raise e
            return cache[key][0]

    return wrapper
