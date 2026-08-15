import sys
import os
import traceback
import time
import datetime
import requests
from threading import Lock
from typing import Any, Iterator, Sequence, Optional, TYPE_CHECKING
from contextvars import Token
from urllib.parse import urljoin
import opentelemetry.context as otlp_context_api
from opentelemetry.trace import (
    SpanKind,
    set_span_in_context,
    get_current_span as get_current_otlp_span,
    NonRecordingSpan,
    SpanContext,
    TraceFlags
)
from opentelemetry.trace.status import StatusCode
from opentelemetry.sdk.trace import (
    ReadableSpan,
    SynchronousMultiSpanProcessor,
    Tracer as SDKTracer,
    Span as SDKSpan,
    TracerProvider as SDKTracerProvider
)
from opentelemetry.context import Context as OTLPContext
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

from aworld.trace.base import (
    AttributeValueType,
    NoOpTracer,
    SpanType,
    TraceProvider,
    Tracer,
    Span,
    TraceContext,
    set_tracer_provider
)
from aworld.trace.span_cosumer import SpanConsumer
from aworld.trace.propagator import get_global_trace_context
from aworld.trace.baggage.sofa_tracer import SofaSpanHelper
from aworld.logs.util import logger
from aworld.utils.common import get_local_ip
from .memory_storage import InMemorySpanExporter, InMemoryStorage
from ..constants import ATTRIBUTES_MESSAGE_KEY
from .export import FileSpanExporter, NoOpSpanExporter, SpanConsumerExporter
from ..server import set_trace_server


class OTLPTraceProvider(TraceProvider):
    """A TraceProvider that wraps an existing `SDKTracerProvider`.
    This class provides a way to use a `SDKTracerProvider` as a `TraceProvider`.
    When the context manager is entered, it returns the `SDKTracerProvider` itself.
    When the context manager is exited, it calls `shutdown` on the `SDKTracerProvider`.
    Args:
        provider: The internal provider to wrap.
    """

    def __init__(self, provider: SDKTracerProvider, suppressed_scopes: Optional[set[str]] = None):
        self._provider: SDKTracerProvider = provider
        self._suppressed_scopes = set()
        if suppressed_scopes:
            self._suppressed_scopes.update(suppressed_scopes)
        self._lock: Lock = Lock()

    def get_tracer(
            self,
            name: str,
            version: Optional[str] = None
    ):
        with self._lock:
            if name in self._suppressed_scopes:
                return NoOpTracer()
            else:
                tracer = self._provider.get_tracer(instrumenting_module_name=name,
                                                   instrumenting_library_version=version)
                return OTLPTracer(tracer)

    def shutdown(self) -> None:
        with self._lock:
            if isinstance(self._provider, SDKTracerProvider):
                self._provider.shutdown()

    def force_flush(self, timeout: Optional[float] = None) -> bool:
        with self._lock:
            if isinstance(self._provider, SDKTracerProvider):
                return self._provider.force_flush(timeout)
            else:
                return False

    def get_current_span(self) -> Optional["Span"]:
        otlp_span = get_current_otlp_span()
        return OTLPSpan(otlp_span, is_new_span=False)


class OTLPTracer(Tracer):
    """A Tracer represents a collection of Spans.
    Args:
        tracer: The internal tracer to wrap.
    """

    def __init__(self, tracer: SDKTracer):
        self._tracer = tracer

    def start_span(
            self,
            name: str,
            span_type: SpanType = SpanType.INTERNAL,
            attributes: dict[str, AttributeValueType] = None,
            start_time: Optional[int] = None,
            record_exception: bool = True,
            set_status_on_exception: bool = True,
            trace_context: Optional[TraceContext] = None
    ) -> "Span":
        otel_context = None
        trace_context = trace_context or get_global_trace_context().get_and_clear()
        if trace_context:
            otel_context = self._get_otel_context_from_trace_context(
                trace_context)
        start_time = start_time or time.time_ns()
        attributes = {**(attributes or {})}
        attributes.setdefault(ATTRIBUTES_MESSAGE_KEY, name)
        SofaSpanHelper.set_sofa_context_to_attr(attributes)
        attributes = {k: v for k, v in attributes.items(
        ) if is_valid_attribute_value(k, v)}

        span_kind = self._convert_to_span_kind(
            span_type) if span_type else SpanKind.INTERNAL
        span = self._tracer.start_span(name=name,
                                       kind=span_kind,
                                       context=otel_context,
                                       attributes=attributes,
                                       start_time=start_time,
                                       record_exception=record_exception,
                                       set_status_on_exception=set_status_on_exception)
        return OTLPSpan(span)

    def start_as_current_span(
            self,
            name: str,
            span_type: SpanType = SpanType.INTERNAL,
            attributes: dict[str, AttributeValueType] = None,
            start_time: Optional[int] = None,
            record_exception: bool = True,
            set_status_on_exception: bool = True,
            end_on_exit: bool = True,
            trace_context: Optional[TraceContext] = None
    ) -> Iterator["Span"]:

        start_time = start_time or time.time_ns()
        attributes = {**(attributes or {})}
        attributes.setdefault(ATTRIBUTES_MESSAGE_KEY, name)
        SofaSpanHelper.set_sofa_context_to_attr(attributes)
        attributes = {k: v for k, v in attributes.items(
        ) if is_valid_attribute_value(k, v)}

        span_kind = self._convert_to_span_kind(
            span_type) if span_type else SpanKind.INTERNAL
        otel_context = None
        trace_context = trace_context or get_global_trace_context().get_and_clear()
        if trace_context:
            otel_context = self._get_otel_context_from_trace_context(
                trace_context)

        class _OTLPSpanContextManager:
            def __init__(self, tracer: SDKTracer):
                self._span_cm = None
                self._tracer = tracer

            def __enter__(self):
                self._span_cm = self._tracer.start_as_current_span(
                    name=name,
                    kind=span_kind,
                    context=otel_context,
                    attributes=attributes,
                    start_time=start_time,
                    record_exception=record_exception,
                    set_status_on_exception=set_status_on_exception,
                    end_on_exit=end_on_exit
                )
                inner_span = self._span_cm.__enter__()
                return OTLPSpan(inner_span)

            def __exit__(self, exc_type, exc_val, exc_tb):
                return self._span_cm.__exit__(exc_type, exc_val, exc_tb)

        return _OTLPSpanContextManager(self._tracer)

    def _convert_to_span_kind(self, span_type: SpanType) -> str:
        if span_type == SpanType.INTERNAL:
            return SpanKind.INTERNAL
        elif span_type == SpanType.CLIENT:
            return SpanKind.CLIENT
        elif span_type == SpanType.SERVER:
            return SpanKind.SERVER
        elif span_type == SpanType.PRODUCER:
            return SpanKind.PRODUCER
        elif span_type == SpanType.CONSUMER:
            return SpanKind.CONSUMER
        else:
            return SpanKind.INTERNAL

    def _get_otel_context_from_trace_context(self, trace_context: TraceContext) -> OTLPContext:
        trace_flags = None
        if trace_context.trace_flags:
            trace_flags = TraceFlags(int(trace_context.trace_flags, 16))
        otel_context = otlp_context_api.Context()
        return set_span_in_context(
            NonRecordingSpan(
                SpanContext(
                    trace_id=int(trace_context.trace_id, 16),
                    span_id=int(trace_context.span_id, 16),
                    is_remote=True,
                    trace_flags=trace_flags
                )
            ),
            otel_context,
        )


class OTLPSpan(Span, ReadableSpan):
    """A Span represents a single operation within a trace.
    """

    def __init__(self, span: SDKSpan, is_new_span=True):
        self._span = span
        self._token: Optional[Token[OTLPContext]] = None
        if is_new_span:
            self._attach()
            self._add_to_open_spans()

    if not TYPE_CHECKING:  # pragma: no branch
        def __getattr__(self, name: str) -> Any:
            return getattr(self._span, name)

    def end(self, end_time: Optional[int] = None) -> None:
        self._remove_from_open_spans()
        end_time = end_time or time.time_ns()
        if not self._span._status or self._span._status.status_code == StatusCode.UNSET:
            self._span.set_status(
                status=StatusCode.OK,
                description="",
            )
        self._span.end(end_time=end_time)
        self._detach()

    def set_attribute(self, key: str, value: Any) -> None:
        if not is_valid_attribute_value(key, value):
            return
        self._span.set_attribute(key=key, value=value)

    def set_attributes(self, attributes: dict[str, Any]) -> None:
        attributes = {k: v for k, v in attributes.items(
        ) if is_valid_attribute_value(k, v)}
        self._span.set_attributes(attributes=attributes)

    def is_recording(self) -> bool:
        return self._span.is_recording()

    def record_exception(
            self,
            exception: BaseException,
            attributes: dict[str, Any] = None,
            timestamp: Optional[int] = None,
            escaped: bool = False,
    ) -> None:
        timestamp = timestamp or time.time_ns()
        attributes = {**(attributes or {})}

        stacktrace = ''.join(traceback.format_exception(
            type(exception), exception, exception.__traceback__))
        self._span.set_attributes({
            SpanAttributes.EXCEPTION_STACKTRACE: stacktrace,
            SpanAttributes.EXCEPTION_TYPE: type(exception).__name__,
            SpanAttributes.EXCEPTION_MESSAGE: str(exception),
            SpanAttributes.EXCEPTION_ESCAPED: escaped
        })
        if exception is not sys.exc_info()[1]:
            attributes[SpanAttributes.EXCEPTION_STACKTRACE] = stacktrace

        self._span.record_exception(exception=exception,
                                    attributes=attributes,
                                    timestamp=timestamp,
                                    escaped=escaped)
        self._span.set_status(
            status=StatusCode.ERROR,
            description=str(exception),
        )

    def get_trace_id(self) -> str:
        """Get the trace ID of the span.
        Returns:
            The trace ID of the span.
        """
        if not self._span or not self._span.get_span_context() or not self.is_recording():
            return None
        return f"{self._span.get_span_context().trace_id:032x}"

    def get_span_id(self) -> str:
        """Get the span ID of the span.
        Returns:
            The span ID of the span.
        """
        if not self._span or not self._span.get_span_context() or not self.is_recording():
            return None
        return f"{self._span.get_span_context().span_id:016x}"

    def _attach(self):
        if self._token is not None:
            return
        self._token = otlp_context_api.attach(set_span_in_context(self._span))

    def _detach(self):
        if self._token is None:
            return
        try:
            otlp_context_api.detach(self._token)
        except ValueError as e:
            logger.warning(f"Failed to detach context: {e}")
        finally:
            self._token = None


def configure_otlp_provider(
        backends: Sequence[str] = None,
        base_url: str = None,
        write_token: str = None,
        span_consumers: Optional[Sequence[SpanConsumer]] = None,
        **kwargs
) -> None:
    """Configure the OTLP provider.
    Args:
        backend: The backend to use.
        write_token: The write token to use.
        **kwargs: Additional keyword arguments to pass to the provider.
    """
    from aworld.metrics.opentelemetry.opentelemetry_adapter import build_otel_resource
    backends = backends or ["logfire"]
    processor = SynchronousMultiSpanProcessor()
    processor.add_span_processor(BatchSpanProcessor(
        SpanConsumerExporter(span_consumers)))
    for backend in backends:
        if backend == "logfire":
            span_exporter = _configure_logfire_exporter(
                write_token=write_token, base_url=base_url, **kwargs)
            processor.add_span_processor(BatchSpanProcessor(span_exporter))
        elif backend == "console":
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            processor.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter()))
        elif backend == "file":
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            file_path = kwargs.get("file_path", f"traces_{timestamp}.json")
            processor.add_span_processor(
                BatchSpanProcessor(FileSpanExporter(file_path)))
        elif backend == "memory":
            logger.info("Using in-memory storage for traces.")
            storage = kwargs.get(
                "storage", InMemoryStorage()) or InMemoryStorage()
            processor.add_span_processor(
                SimpleSpanProcessor(InMemorySpanExporter(storage=storage)))
            server_enabled = str(kwargs.get("server_enabled")) or os.getenv(
                "START_TRACE_SERVER") or "true"
            server_port = kwargs.get("server_port") or 7079
            if (server_enabled.lower() == "true"):
                logger.info(f"Starting trace server on port {server_port}.")
                set_trace_server(storage=storage, port=int(
                    server_port), start_server=True)
            else:
                logger.info("Trace server is not started.")
                set_trace_server(storage=storage, port=int(
                    server_port), start_server=False)
        else:
            span_exporter = _configure_otlp_exporter(
                base_url=base_url, **kwargs)
            processor.add_span_processor(BatchSpanProcessor(span_exporter))

    set_tracer_provider(OTLPTraceProvider(SDKTracerProvider(active_span_processor=processor,
                                                            resource=build_otel_resource())))


def _configure_logfire_exporter(write_token: str, base_url: str = None) -> None:
    """Configure the Logfire exporter.
    Args:
        write_token: The write token to use.
        base_url: The base URL to use.
        **kwargs: Additional keyword arguments to pass to the exporter.
    """
    from opentelemetry.exporter.otlp.proto.http import Compression
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    base_url = base_url or "https://logfire-us.pydantic.dev"
    headers = {'User-Agent': f'logfire/3.14.0', 'Authorization': write_token}
    session = requests.Session()
    session.headers.update(headers)
    return OTLPSpanExporter(
        endpoint=urljoin(base_url, '/v1/traces'),
        session=session,
        compression=Compression.Gzip,
    )


def _configure_otlp_exporter(base_url: str = None, **kwargs) -> None:
    """Configure the OTLP exporter.
    Args:
        write_token: The write token to use.
        base_url: The base URL to use.
        **kwargs: Additional keyword arguments to pass to the exporter.
    """
    import requests
    from opentelemetry.exporter.otlp.proto.http import Compression
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    otlp_traces_endpoint = os.getenv("OTLP_TRACES_ENDPOINT")
    base_url = base_url or otlp_traces_endpoint
    session = requests.Session()
    return OTLPSpanExporter(
        endpoint=base_url,
        session=session,
        compression=Compression.Gzip,
    )


def is_valid_attribute_value(k, v):
    valid = True
    if not v:
        valid = False
    valid = isinstance(v, (str, bool, int, float)) or \
        (isinstance(v, Sequence) and
            all(isinstance(i, (str, bool, int, float)) for i in v))
    if not valid:
        logger.debug(f"value of attribute[{k}] is invalid: {v}")
    return valid
