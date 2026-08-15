from abc import ABC, abstractmethod
from typing import Sequence
from aworld.trace.base import Span


class SpanConsumer(ABC):
    """SpanConsumer is a protocol that represents a consumer for spans.
    """
    @abstractmethod
    def consume(self, spans: Sequence[Span]) -> None:
        """Consumes a span.
        Args:
            spans: The span to consume.
        """


_SPAN_CONSUMER_REGISTRY = {}


def register_span_consumer(default_kwargs=None) -> None:
    """Registers a span consumer.
    Args:
        default_kwargs: A dictionary of default keyword arguments to pass to the span consumer.
    """

    default_kwargs = default_kwargs or {}

    def decorator(cls):
        _SPAN_CONSUMER_REGISTRY[cls.__name__] = (cls, default_kwargs)
        return cls

    return decorator


def get_span_consumers() -> Sequence[SpanConsumer]:
    """Returns a list of span consumers.
    Returns:
        A list of span consumers.
    """
    return [
        cls(**kwargs)
        for cls, kwargs in _SPAN_CONSUMER_REGISTRY.values()
    ]
