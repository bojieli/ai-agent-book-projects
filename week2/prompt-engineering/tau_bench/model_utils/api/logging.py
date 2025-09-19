import functools
import inspect
import json
from multiprocessing import Lock
from typing import Any

from pydantic import BaseModel

from tau_bench.model_utils.api.sample import SamplingStrategy
from tau_bench.model_utils.model.utils import optionalize_type

log_files = {}


def prep_for_json_serialization(obj: Any, from_parse_method: bool = False):
    # TODO: refine type annotations
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, dict):
        return {k: prep_for_json_serialization(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [prep_for_json_serialization(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(prep_for_json_serialization(v) for v in obj)
    elif isinstance(obj, set):
        return {prep_for_json_serialization(v) for v in obj}
    elif isinstance(obj, frozenset):
        return frozenset(prep_for_json_serialization(v) for v in obj)
    elif isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    elif isinstance(obj, type) and issubclass(obj, BaseModel):
        if from_parse_method:
            optionalized_type = optionalize_type(obj)
            return optionalized_type.model_json_schema()
        else:
            return obj.model_json_schema()
    elif isinstance(obj, SamplingStrategy):
        return obj.__class__.__name__
    else:
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def log_call(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        response = func(self, *args, **kwargs)
        log_file = getattr(self, "_log_file", None)
        if log_file is not None:
            if log_file not in log_files:
                log_files[log_file] = Lock()
            sig = inspect.signature(func)
            bound_args = sig.bind(self, *args, **kwargs)
            bound_args.apply_defaults()
            all_args = bound_args.arguments
            all_args.pop("self", None)

            cls_name = self.__class__.__name__
            log_entry = {
                "cls_name": cls_name,
                "method_name": func.__name__,
                "kwargs": {
                    k: prep_for_json_serialization(
                        v, from_parse_method=func.__name__ in ["parse", "async_parse"]
                    )
                    for k, v in all_args.items()
                },
                "response": prep_for_json_serialization(response),
            }
            with log_files[log_file]:
                with open(log_file, "a") as f:
                    f.write(f"{json.dumps(log_entry)}\n")
        return response

    return wrapper
