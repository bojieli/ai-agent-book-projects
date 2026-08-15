import flask
import weakref
from typing import Any, Callable, Collection
from time import time_ns
from timeit import default_timer
from importlib_metadata import version
from packaging import version as package_version
from aworld.trace.instrumentation import Instrumentor
from aworld.trace.base import Span, TraceProvider, TraceContext, Tracer, SpanType, get_tracer_provider
from aworld.metrics.metric import MetricType
from aworld.metrics.template import MetricTemplate
from aworld.logs.util import logger
from aworld.trace.instrumentation.http_util import (
    collect_request_attributes,
    url_disabled,
    get_excluded_urls,
    parse_excluded_urls,
    HTTP_ROUTE
)
from aworld.trace.propagator import get_global_trace_propagator
from aworld.metrics.context_manager import MetricContext
from aworld.trace.propagator.carrier import ListTupleCarrier, DictCarrier

_ENVIRON_STARTTIME_KEY = "aworld-flask.starttime_key"
_ENVIRON_SPAN_KEY = "aworld-flask.span_key"
_ENVIRON_REQCTX_REF_KEY = "aworld-flask.reqctx_ref_key"

flask_version = version("flask")
if package_version.parse(flask_version) >= package_version.parse("2.2.0"):

    def _request_ctx_ref() -> weakref.ReferenceType:
        return weakref.ref(flask.globals.request_ctx._get_current_object())

else:

    def _request_ctx_ref() -> weakref.ReferenceType:
        return weakref.ref(flask._request_ctx_stack.top)


def _rewrapped_app(
    wsgi_app,
    active_requests_counter,
    duration_histogram,
    response_hook=None,
    excluded_urls=None,
):
    def _wrapped_app(wrapped_app_environ, start_response):
        # We want to measure the time for route matching, etc.
        # In theory, we could start the span here and use
        # update_name later but that API is "highly discouraged" so
        # we better avoid it.
        wrapped_app_environ[_ENVIRON_STARTTIME_KEY] = time_ns()
        start = default_timer()
        attributes = collect_request_attributes(wrapped_app_environ)

        if MetricContext.metric_initialized():
            MetricContext.inc(active_requests_counter, 1, attributes)

        request_route = None

        def _start_response(status, response_headers, *args, **kwargs):
            if flask.request and (
                excluded_urls is None
                or not url_disabled(flask.request.url, excluded_urls)
            ):
                nonlocal request_route
                request_route = flask.request.url_rule

                span: Span = flask.request.environ.get(_ENVIRON_SPAN_KEY)

                propagator = get_global_trace_propagator()
                if propagator and span:
                    trace_context = TraceContext(
                        trace_id=span.get_trace_id(),
                        span_id=span.get_span_id()
                    )
                    propagator.inject(
                        trace_context, ListTupleCarrier(response_headers))

                if span and span.is_recording():
                    status_code_str, _ = status.split(" ", 1)
                    try:
                        status_code = int(status_code_str)
                    except ValueError:
                        status_code = -1

                    span.set_attribute(
                        "http.response.status_code", status_code)
                    span.set_attributes(attributes)

                if response_hook is not None:
                    response_hook(span, status, response_headers)
            return start_response(status, response_headers, *args, **kwargs)

        result = wsgi_app(wrapped_app_environ, _start_response)
        duration_s = default_timer() - start

        if MetricContext.metric_initialized():
            MetricContext.histogram_record(
                duration_histogram,
                duration_s,
                attributes
            )
            MetricContext.dec(active_requests_counter, 1, attributes)
        return result

    return _wrapped_app


def _wrapped_before_request(
    request_hook=None,
    tracer: Tracer = None,
    excluded_urls=None
):
    def _before_request():
        if excluded_urls and url_disabled(flask.request.url, excluded_urls):
            return
        flask_request_environ = flask.request.environ
        logger.info(
            f"_wrapped_before_request flask_request_environ={flask_request_environ}")

        attributes = collect_request_attributes(flask_request_environ)

        if flask.request.url_rule:
            # For 404 that result from no route found, etc, we
            # don't have a url_rule.
            attributes[HTTP_ROUTE] = flask.request.url_rule.rule
            span_name = f"HTTP {flask.request.url_rule.rule}"
        else:
            span_name = f"HTTP {flask.request.url}"

        propagator = get_global_trace_propagator()
        trace_context = None
        if propagator:
            trace_context = propagator.extract(
                DictCarrier(flask_request_environ))

        logger.info(f"_wrapped_before_request trace_context={trace_context}")

        span = tracer.start_span(
            span_name,
            SpanType.SERVER,
            attributes=attributes,
            start_time=flask_request_environ.get(_ENVIRON_STARTTIME_KEY),
            trace_context=trace_context
        )

        if request_hook:
            request_hook(span, flask_request_environ)

        flask_request_environ[_ENVIRON_SPAN_KEY] = span
        flask_request_environ[_ENVIRON_REQCTX_REF_KEY] = _request_ctx_ref()

    return _before_request


def _wrapped_teardown_request(
    excluded_urls=None,
):
    def _teardown_request(exc):
        if excluded_urls and url_disabled(flask.request.url, excluded_urls):
            return

        span: Span = flask.request.environ.get(_ENVIRON_SPAN_KEY)

        original_reqctx_ref = flask.request.environ.get(
            _ENVIRON_REQCTX_REF_KEY
        )
        current_reqctx_ref = _request_ctx_ref()
        if not span or original_reqctx_ref != current_reqctx_ref:
            return
        if exc is None:
            span.end()
        else:
            span.record_exception(exc)
            span.end()

    return _teardown_request


class _InstrumentedFlask(flask.Flask):
    _excluded_urls = None
    _tracer_provider: TraceProvider = None
    _request_hook = None
    _response_hook = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tracer = self._tracer_provider.get_tracer(
            "aworld.trace.instrumentation.flask")

        duration_histogram = MetricTemplate(
            type=MetricType.HISTOGRAM,
            name="flask_request_duration_histogram",
            description="Duration of flask HTTP server requests."
        )

        active_requests_counter = MetricTemplate(
            type=MetricType.UPDOWNCOUNTER,
            name="flask_active_request_counter",
            unit="1",
            description="Number of active HTTP server requests.",
        )

        self.wsgi_app = _rewrapped_app(
            self.wsgi_app,
            active_requests_counter,
            duration_histogram,
            _InstrumentedFlask._response_hook,
            excluded_urls=_InstrumentedFlask._excluded_urls
        )

        _before_request = _wrapped_before_request(
            _InstrumentedFlask._request_hook,
            tracer,
            excluded_urls=_InstrumentedFlask._excluded_urls
        )
        self._before_request = _before_request
        self.before_request(_before_request)

        _teardown_request = _wrapped_teardown_request(
            excluded_urls=_InstrumentedFlask._excluded_urls,
        )
        self.teardown_request(_teardown_request)


class FlaskInstrumentor(Instrumentor):

    def instrumentation_dependencies(self) -> Collection[str]:
        return ("flask >= 1.0",)

    def _instrument(self, **kwargs: Any):
        logger.info("Flask _instrument entered.")
        self._original_flask = flask.Flask
        request_hook = kwargs.get("request_hook")
        response_hook = kwargs.get("response_hook")
        if callable(request_hook):
            _InstrumentedFlask._request_hook = request_hook
        if callable(response_hook):
            _InstrumentedFlask._response_hook = response_hook
        tracer_provider = kwargs.get("tracer_provider")
        _InstrumentedFlask._tracer_provider = tracer_provider
        excluded_urls = kwargs.get("excluded_urls")
        _InstrumentedFlask._excluded_urls = (
            get_excluded_urls("FLASK")
            if excluded_urls is None
            else parse_excluded_urls(excluded_urls)
        )
        flask.Flask = _InstrumentedFlask
        logger.info("Flask _instrument exited.")

    def _uninstrument(self, **kwargs):
        flask.Flask = self._original_flask


def instrument_flask(excluded_urls: str = None,
                     request_hook: Callable = None,
                     response_hook: Callable = None,
                     tracer_provider: TraceProvider = None,
                     **kwargs: Any,
                     ):
    """
    Instrument the Flask application.
    Args:
        excluded_urls (str): A comma separated list of URLs to be excluded from instrumentation.
        request_hook (Callable): A function to be called before a request is processed.
        response_hook (Callable): A function to be called after a request is processed.
        tracer_provider (TraceProvider): The trace provider to use.
    """
    all_kwargs = {
        "excluded_urls": excluded_urls,
        "request_hook": request_hook,
        "response_hook": response_hook,
        "tracer_provider": tracer_provider or get_tracer_provider(),
        **kwargs
    }
    FlaskInstrumentor().instrument(**all_kwargs)
    logger.info("Flask instrumented.")
