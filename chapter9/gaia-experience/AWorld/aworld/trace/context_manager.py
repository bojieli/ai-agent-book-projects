import types
import inspect
from typing import Union, Optional, Any, Type, Sequence, Callable, Iterable
from aworld.trace.base import (
    AttributeValueType,
    NoOpSpan,
    Span, Tracer,
    NoOpTracer,
    get_tracer_provider,
    get_tracer_provider_silent,
    log_trace_error
)
from aworld.trace.span_cosumer import SpanConsumer
from aworld.version_gen import __version__
from aworld.trace.auto_trace import AutoTraceModule, install_auto_tracing
from aworld.trace.stack_info import get_user_stack_info
from aworld.trace.constants import (
    ATTRIBUTES_MESSAGE_KEY,
    ATTRIBUTES_MESSAGE_RUN_TYPE_KEY,
    ATTRIBUTES_MESSAGE_TEMPLATE_KEY,
    RunType
)
from aworld.trace.msg_format import (
    chunks_formatter,
    warn_formatting,
    FStringAwaitError,
    KnownFormattingError,
    warn_fstring_await
)
from aworld.trace.function_trace import trace_func
from .opentelemetry.opentelemetry_adapter import configure_otlp_provider
from aworld.logs.util import logger


def trace_configure(provider: str = "otlp",
                    backends: Sequence[str] = None,
                    base_url: str = None,
                    write_token: str = None,
                    span_consumers: Optional[Sequence[SpanConsumer]] = None,
                    **kwargs
                    ) -> None:
    """
    Configure the trace provider.
    Args:
        provider: The trace provider to use.
        backends: The trace backends to use.
        base_url: The base URL of the trace backend.
        write_token: The write token of the trace backend.
        span_consumers: The span consumers to use.
        **kwargs: Additional arguments to pass to the trace provider.
    Returns:
        None
    """
    exist_provider = get_tracer_provider_silent()
    if exist_provider:
        logger.info("Trace provider already configured, shutting down...")
        exist_provider.shutdown()
    if provider == "otlp":
        configure_otlp_provider(
            backends=backends, base_url=base_url, write_token=write_token, span_consumers=span_consumers, **kwargs)
    else:
        raise ValueError(f"Unknown trace provider: {provider}")


class TraceManager:
    """
    TraceManager is a class that provides a way to trace the execution of a function.
    """

    def __init__(self, tracer_name: str = None) -> None:
        self._tracer_name = tracer_name or "aworld"
        self._version = __version__

    def _create_auto_span(self,
                          name: str,
                          attributes: dict[str, AttributeValueType] = None
                          ) -> Span:
        """
        Create a auto trace span with the given name and attributes.
        """
        return self._create_context_span(name, attributes)

    def _create_context_span(self,
                             name: str,
                             attributes: dict[str, AttributeValueType] = None) -> Span:
        try:
            tracer = get_tracer_provider().get_tracer(
                name=self._tracer_name, version=self._version)
            return ContextSpan(span_name=name, tracer=tracer, attributes=attributes)
        except Exception:
            return ContextSpan(span_name=name, tracer=NoOpTracer(), attributes=attributes)

    def get_current_span(self) -> Span:
        """
        Get the current span.
        """
        try:
            return get_tracer_provider().get_current_span()
        except Exception:
            return NoOpSpan()

    def new_manager(self, tracer_name_suffix: str = None) -> "TraceManager":
        """
        Create a new TraceManager with the given tracer name suffix.
        """
        tracer_name = self._tracer_name if not tracer_name_suffix else f"{self._tracer_name}.{tracer_name_suffix}"
        return TraceManager(tracer_name=tracer_name)

    def auto_tracing(self,
                     modules: Union[Sequence[str], Callable[[AutoTraceModule], bool]],
                     min_duration: float) -> None:
        """
        Automatically trace the execution of a function.
        Args:
            modules: A list of module names or a callable that takes a `AutoTraceModule` and returns a boolean.
            min_duration: The minimum duration of a function to be traced.
        Returns:
            None
        """
        install_auto_tracing(self, modules, min_duration)

    def span(self,
             msg_template: str = "",
             attributes: dict[str, AttributeValueType] = None,
             *,
             span_name: str = None,
             run_type: RunType = RunType.OTHER) -> "ContextSpan":

        try:
            attributes = attributes or {}
            stack_info = get_user_stack_info()
            merged_attributes = {**stack_info, **attributes}
            # Retrieve stack information of user code and add it to the attributes

            if any(c in msg_template for c in ('{', '}')):
                fstring_frame = inspect.currentframe().f_back
            else:
                fstring_frame = None
            log_message, extra_attrs, msg_template = format_span_msg(
                msg_template,
                merged_attributes,
                fstring_frame=fstring_frame,
            )
            merged_attributes[ATTRIBUTES_MESSAGE_KEY] = log_message
            merged_attributes.update(extra_attrs)
            merged_attributes[ATTRIBUTES_MESSAGE_TEMPLATE_KEY] = msg_template
            merged_attributes[ATTRIBUTES_MESSAGE_RUN_TYPE_KEY] = run_type.value
            span_name = span_name or msg_template

            return self._create_context_span(span_name, merged_attributes)

        except Exception:
            log_trace_error()
            return ContextSpan(span_name=span_name, tracer=NoOpTracer(), attributes=attributes)

    def func_span(self,
                  msg_template: Union[str, Callable] = None,
                  *,
                  attributes: dict[str, AttributeValueType] = None,
                  span_name: str = None,
                  extract_args: Union[bool, Iterable[str]] = False,
                  **kwargs) -> Callable:
        """
        A decorator that traces the execution of a function.
        Args:
            msg_template: The message template to use.
            attributes: The attributes to add to the span.
            span_name: The name of the span.
            extract_args: Whether to extract arguments from the function call.
            **kwargs: Additional attributes to add to the span.
        Returns:
            A decorator that traces the execution of a function.
        """
        if callable(msg_template):
            #  @trace_func
            #  def foo():
            return self.func_span()(msg_template)

        attributes = attributes or {}
        attributes.update(kwargs)
        return trace_func(self, msg_template, attributes, span_name, extract_args)


class ContextSpan(Span):
    """A context manager that wraps an existing `Span` object.
    This class provides a way to use a `Span` object as a context manager.
    When the context manager is entered, it returns the `Span` itself.
    When the context manager is exited, it calls `end` on the `Span`.
    Args:
        span: The `Span` object to wrap.
    """

    def __init__(self,
                 span_name: str,
                 tracer: Tracer,
                 attributes: dict[str, AttributeValueType] = None) -> None:
        self._span_name = span_name
        self._tracer = tracer
        self._attributes = attributes
        self._span: Span = None
        self._coro_context = None

    def _start(self):
        if self._span is not None:
            return

        self._span = self._tracer.start_span(
            name=self._span_name,
            attributes=self._attributes,
        )

    def __enter__(self) -> "Span":
        self._start()
        return self

    def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            traceback: Optional[Any],
    ) -> None:
        """Ends context manager and calls `end` on the `Span`."""
        self._handle_exit(exc_type, exc_val, traceback)

    async def __aenter__(self) -> "Span":
        self._start()

        return self

    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            traceback: Optional[Any],
    ) -> None:
        self._handle_exit(exc_type, exc_val, traceback)

    def _handle_exit(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            traceback: Optional[Any],
    ) -> None:
        try:
            if self._span and self._span.is_recording() and isinstance(exc_val, BaseException):
                self._span.record_exception(exc_val, escaped=True)
        except ValueError as e:
            logger.warning(f"Failed to record_exception: {e}")
        finally:
            if self._span:
                self._span.end()

    def end(self, end_time: Optional[int] = None) -> None:
        if self._span:
            self._span.end(end_time)

    def set_attribute(self, key: str, value: AttributeValueType) -> None:
        if self._span:
            self._span.set_attribute(key, value)

    def set_attributes(self, attributes: dict[str, AttributeValueType]) -> None:
        if self._span:
            self._span.set_attributes(attributes)

    def is_recording(self) -> bool:
        if self._span:
            return self._span.is_recording()
        return False

    def record_exception(
            self,
            exception: BaseException,
            attributes: dict[str, Any] = None,
            timestamp: Optional[int] = None,
            escaped: bool = False,
    ) -> None:
        if self._span:
            self._span.record_exception(
                exception, attributes, timestamp, escaped)

    def get_trace_id(self) -> str:
        if self._span:
            return self._span.get_trace_id()

    def get_span_id(self) -> str:
        if self._span:
            return self._span.get_span_id()


def format_span_msg(
        format_string: str,
        kwargs: dict[str, Any],
        fstring_frame: types.FrameType = None,
) -> tuple[str, dict[str, Any], str]:
    """ Returns
    1. The formatted message.
    2. A dictionary of extra attributes to add to the span/log.
         These can come from evaluating values in f-strings.
    3. The final message template, which may differ from `format_string` if it was an f-string.
    """
    try:
        chunks, extra_attrs, new_template = chunks_formatter.chunks(
            format_string,
            kwargs,
            fstring_frame=fstring_frame
        )
        return ''.join(chunk['v'] for chunk in chunks), extra_attrs, new_template
    except KnownFormattingError as e:
        warn_formatting(str(e) or str(e.__cause__))
    except FStringAwaitError as e:
        warn_fstring_await(str(e))
    except Exception:
        log_trace_error()

    # Formatting failed, so just use the original format string as the message.
    return format_string, {}, format_string
