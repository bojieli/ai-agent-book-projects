from timeit import default_timer
from typing import Any, Awaitable, Callable
from functools import wraps
from aworld.metrics.context_manager import MetricContext
from aworld.trace.instrumentation.http_util import (
    collect_request_attributes_asgi,
    url_disabled,
    parser_host_port_url_from_asgi
)
from aworld.trace.base import Span, TraceProvider, TraceContext, Tracer, SpanType
from aworld.trace.propagator import get_global_trace_propagator
from aworld.trace.propagator.carrier import DictCarrier, ListTupleCarrier
from aworld.metrics.metric import MetricType
from aworld.metrics.template import MetricTemplate
from aworld.logs.util import logger


def _wrapped_receive(
    server_span: Span,
    server_span_name: str,
    scope: dict[str, Any],
    receive: Callable[[], Awaitable[dict[str, Any]]],
    attributes: dict[str],
    client_request_hook: Callable = None
):

    @wraps(receive)
    async def otel_receive():
        message = await receive()
        if client_request_hook and callable(client_request_hook):
            client_request_hook(scope, message)

        server_span.set_attribute("asgi.event.type", message.get("type", ""))
        return message

    return otel_receive


def _wrapped_send(
    server_span: Span,
    server_span_name: str,
    scope: dict[str, Any],
    send: Callable[[dict[str, Any]], Awaitable[None]],
    attributes: dict[str],
    client_response_hook: Callable = None
):
    expecting_trailers = False

    @wraps(send)
    async def otel_send(message: dict[str, Any]):
        nonlocal expecting_trailers

        status_code = None
        if message["type"] == "http.response.start":
            status_code = message["status"]
        elif message["type"] == "websocket.send":
            status_code = 200

        # raw_headers = message.get("headers")
        # if raw_headers:
        if status_code:
            server_span.set_attribute(
                "http.response.status_code", status_code)

        if callable(client_response_hook):
            client_response_hook(scope, message)

        if message["type"] == "http.response.start":
            expecting_trailers = message.get("trailers", False)

        propagator = get_global_trace_propagator()
        if propagator:
            trace_context = TraceContext(
                trace_id=server_span.get_trace_id(),
                span_id=server_span.get_span_id()
            )
            propagator.inject(
                trace_context, DictCarrier(message))

        await send(message)

        if (
            not expecting_trailers
            and message["type"] == "http.response.body"
            and not message.get("more_body", False)
        ) or (
            expecting_trailers
            and message["type"] == "http.response.trailers"
            and not message.get("more_trailers", False)
        ):
            server_span.end()

    return otel_send


class TraceMiddleware:
    """
    A ASGI Middleware for tracing requests and responses.
    """

    def __init__(
            self,
            app,
            excluded_urls=None,
            tracer_provider: TraceProvider = None,
            tracer: Tracer = None,
            server_request_hook: Callable = None,
            client_request_hook: Callable = None,
            client_response_hook: Callable = None,):
        self.app = app
        self.excluded_urls = excluded_urls
        self.tracer_provider = tracer_provider
        self.server_request_hook = server_request_hook
        self.client_request_hook = client_request_hook
        self.client_response_hook = client_response_hook

        self.tracer: Tracer = (self.tracer_provider.get_tracer(
            "aworld.trace.instrumentation.asgi"
        ) if tracer is None else tracer)

        self.duration_histogram = MetricTemplate(
            type=MetricType.HISTOGRAM,
            name="asgi_request_duration_histogram",
            description="Duration of flask HTTP server requests."
        )

        self.active_requests_counter = MetricTemplate(
            type=MetricType.UPDOWNCOUNTER,
            name="asgi_active_request_counter",
            unit="1",
            description="Number of active HTTP server requests.",
        )

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ):
        start = default_timer()
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        _, _, url = parser_host_port_url_from_asgi(scope)
        if self.excluded_urls and url_disabled(url, self.excluded_urls):
            return await self.app(scope, receive, send)

        span_name = scope.get("method", "HTTP").strip(
        ).upper() + "_" + scope.get("path", "").strip()

        attributes = collect_request_attributes_asgi(scope)

        if scope["type"] == "http" and MetricContext.metric_initialized():
            MetricContext.inc(self.active_requests_counter, 1, attributes)

        trace_context = None
        propagator = get_global_trace_propagator()
        if propagator:
            trace_context = propagator.extract(
                ListTupleCarrier(scope.get("headers", [])))
            logger.info(
                f"asgi extract trace_context: {trace_context}, scope: {scope}")
        try:
            with self.tracer.start_as_current_span(
                span_name, span_type=SpanType.SERVER, trace_context=trace_context, attributes=attributes
            ) as span:

                if callable(self.server_request_hook):
                    self.server_request_hook(scope)

                wrappered_receive = _wrapped_receive(
                    span,
                    span_name,
                    scope,
                    receive,
                    attributes,
                    self.client_request_hook
                )
                wrappered_send = _wrapped_send(
                    span,
                    span_name,
                    scope,
                    send,
                    attributes,
                    self.client_response_hook
                )

                await self.app(scope, wrappered_receive, wrappered_send)
        finally:
            if scope["type"] == "http":
                duration_s = default_timer() - start

                if MetricContext.metric_initialized():
                    MetricContext.histogram_record(
                        self.duration_histogram,
                        duration_s,
                        attributes
                    )
                    MetricContext.inc(
                        self.active_requests_counter, -1, attributes)

            if span.is_recording():
                span.end()
