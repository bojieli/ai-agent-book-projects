from abc import ABC, abstractmethod
from typing import Optional, Any, Iterator, Union, Sequence, Protocol, Iterable
from enum import Enum
from weakref import WeakSet
from dataclasses import dataclass, field
from aworld.logs.util import trace_logger


class TraceProvider(ABC):

    @abstractmethod
    def get_tracer(
            self,
            name: str,
            version: Optional[str] = None
    ) -> "Tracer":
        """Returns a `Tracer` for use by the given name.

        This function may return different `Tracer` types (e.g. a no-op tracer
        vs.  a functional tracer).

        Args:
            name: The uniquely identifiable name for instrumentation
                scope, such as instrumentation library, package, module or class name.
                ``__name__`` may not be used as this can result in
                different tracer names if the tracers are in different files.
                It is better to use a fixed string that can be imported where
                needed and used consistently as the name of the tracer.

                This should *not* be the name of the module that is
                instrumented but the name of the module doing the instrumentation.
                E.g., instead of ``"requests"``, use
                ``"opentelemetry.instrumentation.requests"``.

            version: Optional. The version string of the
                instrumenting library.  Usually this should be the same as
                ``importlib.metadata.version(instrumenting_library_name)``
        """

    @abstractmethod
    def shutdown(self) -> None:
        """Shuts down the provider and all its resources.
        This method should be called when the application is shutting down.
        """

    @abstractmethod
    def force_flush(self, timeout: Optional[float] = None) -> bool:
        """Forces all the data to be sent to the backend.
        This method should be called when the application is shutting down.
        Args:
            timeout: The maximum time to wait for the data to be sent.
        Returns:
            True if the data was sent successfully, False otherwise.
        """

    @abstractmethod
    def get_current_span(self) -> Optional["Span"]:
        """Returns the current span from the current context.
        Returns:
            The current span from the current context.
        """


class SpanType(Enum):
    """Specifies additional details on how this span relates to its parent span.
    """

    #: Default value. Indicates that the span is used internally in the
    # application.
    INTERNAL = 0

    #: Indicates that the span describes an operation that handles a remote
    # request.
    SERVER = 1

    #: Indicates that the span describes a request to some remote service.
    CLIENT = 2

    #: Indicates that the span describes a producer sending a message to a
    #: broker. Unlike client and server, there is usually no direct critical
    #: path latency relationship between producer and consumer spans.
    PRODUCER = 3

    #: Indicates that the span describes a consumer receiving a message from a
    #: broker. Unlike client and server, there is usually no direct critical
    #: path latency relationship between producer and consumer spans.
    CONSUMER = 4


AttributeValueType = Union[
    str,
    bool,
    int,
    float,
    Sequence[str],
    Sequence[bool],
    Sequence[int],
    Sequence[float],
]


class Tracer(ABC):
    """Handles span creation and in-process context propagation.
    """

    @abstractmethod
    def start_span(
            self,
            name: str,
            span_type: SpanType = SpanType.INTERNAL,
            attributes: dict[str, AttributeValueType] = None,
            start_time: Optional[int] = None,
            record_exception: bool = True,
            set_status_on_exception: bool = True,
            trace_context: Optional["TraceContext"] = None,
    ) -> "Span":
        """Starts and returns a new Span.
        Args:
            name: The name of the span.
            kind: The span's kind (relationship to parent). Note that is
                meaningful even if there is no parent.
            attributes: The span's attributes.
            start_time: Sets the start time of a span
            record_exception: Whether to record any exceptions raised within the
                context as error event on the span.
            set_status_on_exception: Only relevant if the returned span is used
                in a with/context manager. Defines whether the span status will
                be automatically set to ERROR when an uncaught exception is
                raised in the span with block. The span status won't be set by
                this mechanism if it was previously set manually.
            trace_context: The trace context to use for the span. If not
                provided, the current trace context will be used.
        """

    @abstractmethod
    def start_as_current_span(
            self,
            name: str,
            span_type: SpanType = SpanType.INTERNAL,
            attributes: dict[str, AttributeValueType] = None,
            start_time: Optional[int] = None,
            record_exception: bool = True,
            set_status_on_exception: bool = True,
            end_on_exit: bool = True,
            trace_context: Optional['TraceContext'] = None
    ) -> Iterator["Span"]:
        """Context manager for creating a new span and set it
        as the current span in this tracer's context.

        Example::

            with tracer.start_as_current_span("one") as parent:
                parent.add_event("parent's event")
                with tracer.start_as_current_span("two") as child:
                    child.add_event("child's event")
                    trace.get_current_span()  # returns child
                trace.get_current_span()      # returns parent
            trace.get_current_span()          # returns previously active span

            This can also be used as a decorator::
            @tracer.start_as_current_span("name")
            def function():

        Args:
            name: The name of the span to be created.
            kind: The span's kind (relationship to parent). Note that is
                meaningful even if there is no parent.
            attributes: The span's attributes.
            start_time: Sets the start time of a span
            record_exception: Whether to record any exceptions raised within the
                context as error event on the span.
            set_status_on_exception: Only relevant if the returned span is used
                in a with/context manager. Defines whether the span status will
                be automatically set to ERROR when an uncaught exception is
                raised in the span with block. The span status won't be set by
                this mechanism if it was previously set manually.
            end_on_exit: Whether to end the span automatically when leaving the
                context manager.
            trace_context: The trace context to use for the span. If not
                provided, the current trace context will be used.
    """


class Span(ABC):
    """A Span represents a single operation within a trace.
    """

    @abstractmethod
    def end(self, end_time: Optional[int] = None) -> None:
        """Sets the current time as the span's end time.

        The span's end time is the wall time at which the operation finished.

        Only the first call to `end` should modify the span, and
        implementations are free to ignore or raise on further calls.
        """

    @abstractmethod
    def set_attribute(self, key: str, value: Any) -> None:
        """Sets an attribute on the Span.
        Args:
            key: The attribute key.
            value: The attribute value.
        """

    @abstractmethod
    def set_attributes(self, attributes: dict[str, Any]) -> None:
        """Sets multiple attributes on the Span.
        Args:
            attributes: A dictionary of attributes to set.
        """

    @abstractmethod
    def is_recording(self) -> bool:
        """Returns whether this span will be recorded.
        Returns true if this Span is active and recording information like attributes using set_attribute.
        """

    @abstractmethod
    def record_exception(
            self,
            exception: BaseException,
            attributes: dict[str, Any] = None,
            timestamp: Optional[int] = None,
            escaped: bool = False,
    ) -> None:
        """Records an exception in the span.
        Args:
            exception: The exception to record.
            attributes: A dictionary of attributes to set on the exception event.
            timestamp: The timestamp of the exception.
            escaped: Whether the exception was escaped.
        """

    @abstractmethod
    def get_trace_id(self) -> str:
        """Returns the trace ID of the span.
        Returns:
            The trace ID of the span.
        """

    @abstractmethod
    def get_span_id(self) -> str:
        """Returns the ID of the span.
        Returns:
            The ID of the span.
        """

    def _add_to_open_spans(self) -> None:
        """Add the current span to OPEN_SPANS."""
        _OPEN_SPANS.add(self)

    def _remove_from_open_spans(self) -> None:
        """Remove the current span from OPEN_SPANS."""
        _OPEN_SPANS.discard(self)


class NoOpSpan(Span):
    """No-op implementation of `Span`."""

    def end(self, end_time: Optional[int] = None) -> None:
        pass

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_attributes(self, attributes: dict[str, Any]) -> None:
        pass

    def is_recording(self) -> bool:
        return False

    def record_exception(
            self,
            exception: BaseException,
            attributes: dict[str, Any] = None,
            timestamp: Optional[int] = None,
            escaped: bool = False,
    ) -> None:
        pass

    def get_trace_id(self) -> str:
        return ""

    def get_span_id(self) -> str:
        return ""


class NoOpTracer(Tracer):
    """No-op implementation of `Tracer`."""

    def start_span(
            self,
            name: str,
            span_type: SpanType = SpanType.INTERNAL,
            attributes: dict[str, AttributeValueType] = None,
            start_time: Optional[int] = None,
            record_exception: bool = True,
            set_status_on_exception: bool = True,
            trace_context: Optional["TraceContext"] = None,
    ) -> Span:
        return NoOpSpan()

    def start_as_current_span(
            self,
            name: str,
            span_type: SpanType = SpanType.INTERNAL,
            attributes: dict[str, AttributeValueType] = None,
            start_time: Optional[int] = None,
            record_exception: bool = True,
            set_status_on_exception: bool = True,
            end_on_exit: bool = True,
            trace_context: Optional['TraceContext'] = None
    ) -> Iterator[Span]:
        yield NoOpSpan()


class Carrier(Protocol):
    """Carrier is a protocol that represents a carrier for trace context.
    """

    def get(self, key: str) -> Optional[str]:
        """Returns the value of the given key from the carrier.
        Args:
            key: The key to get the value for.
        Returns:
            The value of the given key from the carrier.
        """

    def set(self, key: str, value: str) -> None:
        """Sets the value of the given key in the carrier.
        Args:
            key: The key to set the value for.
            value: The value to set.
        """

    def keys(self) -> Iterable[str]:
        """Returns an iterable of keys in the carrier.
        Returns:
            An iterable of keys in the carrier.
        """


@dataclass(frozen=True)
class TraceContext:
    """TraceContext is a class that represents a trace context.
    """
    trace_id: str
    span_id: str
    version: str = "00"
    trace_flags: str = "01"
    attributes: dict[str, Any] = field(default_factory=dict)


class Propagator(ABC):
    """Propagator is a protocol that represents a propagator for trace context.
    """

    def _get_value(self, carrier: Carrier, name: str) -> str:
        """
        Get value from carrier.
        Args:
            carrier: The carrier to get value from.
            name: The name of the value.
        Returns:
            The value of the name.
        """
        return carrier.get(name) or carrier.get('HTTP_' + name.upper().replace('-', '_'))

    @abstractmethod
    def extract(self, carrier: Carrier) -> Optional[TraceContext]:
        """Extracts a trace context from the given carrier.
        Args:
            carrier: The carrier to extract the trace context from.
        Returns:
            The trace context extracted from the carrier.
        """
    @abstractmethod
    def inject(self, trace_context: TraceContext, carrier: Carrier) -> None:
        """Injects a trace context into the given carrier.
        Args:
            trace_context: The trace context to inject.
            carrier: The carrier to inject the trace context into.
        """


_GLOBAL_TRACER_PROVIDER: Optional[TraceProvider] = None
_OPEN_SPANS: WeakSet[Span] = WeakSet()


def set_tracer_provider(provider: TraceProvider):
    """
    Set the global tracer provider.
    """
    global _GLOBAL_TRACER_PROVIDER
    _GLOBAL_TRACER_PROVIDER = provider


def get_tracer_provider() -> TraceProvider:
    """
    Get the global tracer provider.
    """
    global _GLOBAL_TRACER_PROVIDER
    if _GLOBAL_TRACER_PROVIDER is None:
        raise Exception("No tracer provider has been set.")
    return _GLOBAL_TRACER_PROVIDER


def get_tracer_provider_silent():
    try:
        return get_tracer_provider()
    except Exception:
        return None


def log_trace_error():
    """
    Log an error with traceback information.
    """
    trace_logger.exception(
        'This is logging the trace internal error.',
    )
