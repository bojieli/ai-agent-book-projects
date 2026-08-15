# coding: utf-8
# Copyright (c) 2025 inclusionAI.

from typing import TypeVar, Generic, Dict, Any

from aworld.logs.util import logger

T = TypeVar("T")


class Factory(Generic[T]):
    """The base generic class that is used to define a factory(local) for various objects, with a parameterized types: T."""

    def __init__(self, type_name: str = None):
        self._type = type_name
        self._cls: Dict[str, T] = {}
        self._desc: Dict[str, str] = {}
        self._asyn: Dict[str, bool] = {}
        self._ext_info: Dict[str, Dict[Any, Any]] = {}
        self._prio: Dict[str, int] = {}

    def __call__(self, name: str, asyn: bool = False, **kwargs):
        """Create the special type object instance by name. If not found, raise ValueError or construct object instance.

        Returns:
            Object instance.
        """
        exception = kwargs.pop('except', False)
        if not name in self._cls:
            if not exception:
                return None

            if self._type is None:
                raise ValueError(f"Unknown factory object type: '{self._type}'")
            raise ValueError(f"Unknown {self._type}: '{name}'")
        name = "async_" + name if asyn else name
        return self._cls[name](**kwargs)

    def __iter__(self):
        for name in self._cls:
            yield name

    def __contains__(self, name: str) -> bool:
        """Whether the name in the factory."""
        return name in self._cls

    def get_class(self, name: str, asyn: bool = False) -> T | None:
        """Get the object instance by name."""
        return self._cls.get(name, None)

    def count(self) -> int:
        """Total number in the special type object factory."""
        return len(self._cls)

    def desc(self, name: str, asyn: bool = False) -> str:
        """Obtain the description by name."""
        name = "async_" + name if asyn else name
        return self._desc.get(name, "")

    def get_ext_info(self, name: str, asyn: bool = False) -> Dict[Any, Any]:
        """Obtain the extent info by name."""
        name = "async_" + name if asyn else name
        return self._ext_info.get(name, {})

    def register(self, name: str, desc: str = '', prio: int = 0, **kwargs):
        def func(cls):
            asyn = kwargs.pop("asyn", False)
            prefix = "async_" if asyn else ""
            if len(prefix) > 0:
                logger.debug(f"{name} has an async type, will add `async_` prefix.")

            if prefix + name in self._cls:
                equal = True
                if asyn:
                    equal = self._asyn[name] == asyn
                existing_prio = self._prio.get(prefix + name, 0)
                if equal and prio > existing_prio:
                    logger.warning(f"{name} already in {self._type} factory, will override it.")
                else:
                    logger.warning(f"{name} already in {self._type} factory, skip register it.")
                    return self._cls[prefix + name]
            # Add REGISTERED_NAME attribute to the class to save the registered name
            setattr(cls, "REGISTERED_NAME", name)

            self._asyn[name] = asyn
            self._cls[prefix + name] = cls
            self._desc[prefix + name] = desc
            self._ext_info[prefix + name] = kwargs
            self._prio[prefix + name] = prio
            return cls

        return func

    def unregister(self, name: str):
        if name in self._cls:
            logger.warning(f"unregister {name} in the {self._type} factory.")
            del self._cls[name]
            del self._desc[name]
            del self._asyn[name]
