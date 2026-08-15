# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import json

import numpy as np


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def to_serializable(obj, _memo=None):
    if _memo is None:
        _memo = set()
    obj_id = id(obj)
    if obj_id in _memo:
        return str(obj)
    _memo.add(obj_id)

    if isinstance(obj, dict):
        return {k: to_serializable(v, _memo) for k, v in obj.items()}
    elif isinstance(obj, (list, set)):
        return [to_serializable(i, _memo) for i in obj]
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    elif hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        return obj.dict()
    elif hasattr(obj, "__dataclass_fields__"):
        return {field.name: to_serializable(getattr(obj, field.name), _memo)
                for field in obj.__dataclass_fields__.values()}
    elif hasattr(obj, "__dict__"):
        return {k: to_serializable(v, _memo) for k, v in obj.__dict__.items()
                if not k.startswith('_') and not callable(v)}
    else:
        try:
            json.dumps(obj)
            return obj
        except TypeError as e:
            raise RuntimeError(f"{e}")
