import functools
import hashlib
import inspect
import threading
from collections import defaultdict
from multiprocessing import Lock
from typing import Any, Callable, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

USE_CACHE = True
_USE_CACHE_LOCK = Lock()
cache: dict[str, tuple[T, threading.Event]] = {}
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


def hash_item(item: Any) -> int:
    if isinstance(item, dict):
        return hash(tuple({k: hash_item(v) for k, v in sorted(item.items())}))
    elif isinstance(item, list):
        return hash(tuple([hash_item(x) for x in item]))
    elif isinstance(item, set):
        return hash(frozenset([hash_item(x) for x in item]))
    elif isinstance(item, tuple):
        return hash(tuple([hash_item(x) for x in item]))
    elif isinstance(item, BaseModel):
        return hash_item(item.model_json_schema())
    return hash(item)


def hash_func_call(func: Callable[..., Any], args: tuple[Any], kwargs: dict[str, Any]) -> str:
    bound_args = inspect.signature(func).bind(*args, **kwargs)
    bound_args.apply_defaults()
    standardized_args = sorted(bound_args.arguments.items())
    arg_hash = hash_item(standardized_args)
    hashed_func = id(func)
    call = (hashed_func, arg_hash)
    return hashlib.md5(str(call).encode()).hexdigest()


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
