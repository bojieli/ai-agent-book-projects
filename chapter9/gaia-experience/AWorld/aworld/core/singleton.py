# coding: utf-8
# Copyright (c) 2025 inclusionAI.
from aworld.logs.util import logger

import threading


class SingletonMeta(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        """Create or get the class instance."""
        with cls._lock:
            if cls not in cls._instances:
                instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class InheritanceSingleton(object, metaclass=SingletonMeta):
    _local_instances = {}

    @staticmethod
    def __get_base_class(clazz):
        if clazz == object:
            return None

        bases = clazz.__bases__
        for base in bases:
            if base == InheritanceSingleton:
                return clazz
            else:
                base_class = InheritanceSingleton.__get_base_class(base)
                if base_class:
                    return base_class
        return None

    def __new__(cls, *args, **kwargs):
        base = InheritanceSingleton.__get_base_class(cls)
        if base is None:
            raise ValueError(f"{cls} singleton base not found")

        return super(InheritanceSingleton, cls).__new__(cls)

    @classmethod
    def instance(cls, *args, **kwargs):
        """Each thread has its own singleton instance."""

        if cls.__name__ not in cls._local_instances:
            cls._local_instances[cls.__name__] = threading.local()

        local_instance = cls._local_instances[cls.__name__]
        if not hasattr(local_instance, 'instance'):
            logger.info(f"{threading.current_thread().name} thread create {cls} instance.")
            local_instance.instance = cls(*args, **kwargs)

        return local_instance.instance

    @classmethod
    def clear_singleton(cls):
        base = InheritanceSingleton.__get_base_class(cls)
        cls._instances.pop(base, None)
