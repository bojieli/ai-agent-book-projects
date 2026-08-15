from aworld.logs.util import logger
from aworld.trace.instrumentation.http_util import (
    collect_attributes_from_request,
    url_disabled,
    get_excluded_urls,
    parse_excluded_urls,
    HTTP_RESPONSE_STATUS_CODE,
    HTTP_FLAVOR
)
from aworld.metrics.context_manager import MetricContext
from aworld.metrics.template import MetricTemplate
from aworld.metrics.metric import MetricType
from aworld.trace.instrumentation import Instrumentor
from aworld.trace.propagator.carrier import DictCarrier
import functools
from timeit import default_timer
from requests import sessions
from requests.models import PreparedRequest, Response
from requests.structures import CaseInsensitiveDict
from typing import Collection, Any, Callable
from aworld.trace.base import TraceProvider, TraceContext, Tracer, SpanType, get_tracer_provider
from aworld.trace.propagator import get_global_trace_propagator


def _wrapped_send(
    tracer: Tracer = None,
    excluded_urls=None,
    request_hook: Callable = None,
    response_hook: Callable = None,
    duration_histogram: MetricTemplate = None
):

    oringinal_send = sessions.Session.send

    @functools.wraps(oringinal_send)
    def instrumented_send(
        self: sessions.Session, request: PreparedRequest, **kwargs: Any
    ):
        if excluded_urls and url_disabled(request.url, excluded_urls):
            return oringinal_send(self, request, **kwargs)

        def get_or_create_headers():
            request.headers = (
                request.headers
                if request.headers is not None
                else CaseInsensitiveDict()
            )
            return request.headers

        method = request.method
        if method is None:
            method = "HTTP"
        span_name = method.upper()

        span_attributes = collect_attributes_from_request(request)
        with tracer.start_as_current_span(
            span_name, span_type=SpanType.CLIENT, attributes=span_attributes
        ) as span:
            exception = None
            if callable(request_hook):
                request_hook(span, request)

            headers = get_or_create_headers()

            trace_context = TraceContext(
                trace_id=span.get_trace_id(),
                span_id=span.get_span_id(),
            )
            propagator = get_global_trace_propagator()
            if propagator:
                propagator.inject(trace_context, DictCarrier(headers))

            start_time = default_timer()
            try:
                logger.info("Sending headers: %s", request.headers)
                result = oringinal_send(
                    self, request, **kwargs
                )  # *** PROCEED
            except Exception as exc:  # pylint: disable=W0703
                exception = exc
                result = getattr(exc, "response", None)
            finally:
                elapsed_time = max(default_timer() - start_time, 0)

            if isinstance(result, Response):
                span_attributes = {}
                span_attributes[HTTP_RESPONSE_STATUS_CODE] = result.status_code

                if result.raw is not None:
                    version = getattr(result.raw, "version", None)
                    if version:
                        # Only HTTP/1 is supported by requests
                        version_text = "1.1" if version == 11 else "1.0"
                        span_attributes[HTTP_FLAVOR] = version_text
                span.set_attributes(span_attributes)

                if callable(response_hook):
                    response_hook(span, request, result)

            if exception is not None:
                span.record_exception(exception)

            if duration_histogram is not None and MetricContext.metric_initialized():
                MetricContext.histogram_record(
                    duration_histogram,
                    elapsed_time,
                    span_attributes
                )

            if exception is not None:
                raise exception.with_traceback(exception.__traceback__)

        return result

    return instrumented_send


class _InstrumentedSession(sessions.Session):
    """
    An instrumented requests.Session class.
    """
    _excluded_urls = None
    _tracer_provider: TraceProvider = None
    _request_hook = None
    _response_hook = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tracer = self._tracer_provider.get_tracer(
            "aworld.trace.instrumentation.requests")
        excluded_urls = kwargs.get("excluded_urls")

        duration_histogram = MetricTemplate(
            type=MetricType.HISTOGRAM,
            name="client_request_duration_histogram",
            unit="s",
            description="Duration of  HTTP client requests."
        )
        self.send = functools.partial(_wrapped_send(
            tracer=tracer,
            excluded_urls=excluded_urls,
            request_hook=self._request_hook,
            response_hook=self._response_hook,
            duration_histogram=duration_histogram
        ), self)


class RequestsInstrumentor(Instrumentor):
    """
    An instrumentor for the requests module.
    """

    def instrumentation_dependencies(self) -> Collection[str]:
        return ["requests"]

    def _instrument(self, **kwargs):
        """
        Instruments the requests module.
        """
        logger.info("requests _instrument entered.")
        self._original_session = sessions.Session
        request_hook = kwargs.get("request_hook")
        response_hook = kwargs.get("response_hook")
        if callable(request_hook):
            _InstrumentedSession._request_hook = request_hook
        if callable(response_hook):
            _InstrumentedSession._response_hook = response_hook
        tracer_provider = kwargs.get("tracer_provider")
        _InstrumentedSession._tracer_provider = tracer_provider
        excluded_urls = kwargs.get("excluded_urls")
        _InstrumentedSession._excluded_urls = (
            get_excluded_urls("FLASK")
            if excluded_urls is None
            else parse_excluded_urls(excluded_urls)
        )
        sessions.Session = _InstrumentedSession
        logger.info("requests _instrument exited.")

    def _uninstrument(self, **kwargs):
        """
        Uninstruments the requests module.
        """
        sessions.Session = self._original_session


def instrument_requests(excluded_urls: str = None,
                        request_hook: Callable = None,
                        response_hook: Callable = None,
                        tracer_provider: TraceProvider = None,
                        **kwargs: Any,
                        ):
    """
    Instruments the requests module.
    Args:
        excluded_urls: A comma separated list of URLs to exclude from tracing.
        request_hook: A function that will be called before a request is sent.  
            The function will be called with the span and the request.
        response_hook: A function that will be called after a response is received.
            The function will be called with the span and the response.
        tracer_provider: The tracer provider to use. If not provided, the global
            tracer provider will be used.
        kwargs: Additional keyword arguments.
    """
    all_kwargs = {
        "excluded_urls": excluded_urls,
        "request_hook": request_hook,
        "response_hook": response_hook,
        "tracer_provider": tracer_provider or get_tracer_provider(),
        **kwargs
    }
    RequestsInstrumentor().instrument(**all_kwargs)
    logger.info("Requests instrumented.")
