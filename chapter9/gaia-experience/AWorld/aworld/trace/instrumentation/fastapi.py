from typing import Any, Callable
from .asgi import TraceMiddleware
from aworld.trace.instrumentation import Instrumentor
from aworld.trace.base import TraceProvider, get_tracer_provider
from aworld.trace.instrumentation.http_util import (
    get_excluded_urls,
    parse_excluded_urls,
)
from aworld.utils.import_package import import_packages
from aworld.logs.util import logger

import_packages(['fastapi'])  # noqa
import fastapi  # noqa


class _InstrumentedFastAPI(fastapi.FastAPI):
    """Instrumented FastAPI class."""
    _tracer_provider: TraceProvider = None
    _excluded_urls: list[str] = None
    _server_request_hook: Callable = None
    _client_request_hook: Callable = None
    _client_response_hook: Callable = None
    _instrumented_fastapi_apps = set()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        tracer = self._tracer_provider.get_tracer(
            "aworld.trace.instrumentation.fastapi")

        self.add_middleware(
            TraceMiddleware,
            tracer=tracer,
            excluded_urls=self._excluded_urls,
            server_request_hook=self._server_request_hook,
            client_request_hook=self._client_request_hook,
            client_response_hook=self._client_response_hook
        )

        self._is_instrumented_by_trace = True
        self._instrumented_fastapi_apps.add(self)

    def __del__(self):
        if self in self._instrumented_fastapi_apps:
            self._instrumented_fastapi_apps.remove(self)


class FastAPIInstrumentor(Instrumentor):
    """FastAPI Instrumentor."""
    _original_fastapi = None

    @staticmethod
    def uninstrument_app(app: fastapi.FastAPI):
        app.user_middleware = [
            x
            for x in app.user_middleware
            if x.cls is not TraceMiddleware
        ]
        app.middleware_stack = app.build_middleware_stack()
        app._is_instrumented_by_trace = False

    def instrumentation_dependencies(self) -> dict[str, Any]:
        return {"fastapi": fastapi}

    def _instrument(self, **kwargs):
        self._original_fastapi = fastapi.FastAPI
        _InstrumentedFastAPI._tracer_provider = kwargs.get("tracer_provider")
        _InstrumentedFastAPI._server_request_hook = kwargs.get(
            "server_request_hook"
        )
        _InstrumentedFastAPI._client_request_hook = kwargs.get(
            "client_request_hook"
        )
        _InstrumentedFastAPI._client_response_hook = kwargs.get(
            "client_response_hook"
        )
        excluded_urls = kwargs.get("excluded_urls")
        _InstrumentedFastAPI._excluded_urls = (
            get_excluded_urls("FASTAPI")
            if excluded_urls is None
            else parse_excluded_urls(excluded_urls)
        )
        fastapi.FastAPI = _InstrumentedFastAPI

    def _uninstrument(self, **kwargs):
        for app in _InstrumentedFastAPI._instrumented_fastapi_apps:
            self.uninstrument_app(app)
        _InstrumentedFastAPI._instrumented_fastapi_apps.clear()
        fastapi.FastAPI = self._original_fastapi


def instrument_fastapi(excluded_urls: str = None,
                       server_request_hook: Callable = None,
                       client_request_hook: Callable = None,
                       client_response_hook: Callable = None,
                       tracer_provider: TraceProvider = None,
                       **kwargs: Any,
                       ):
    kwargs.update({
        "excluded_urls": excluded_urls,
        "server_request_hook": server_request_hook,
        "client_request_hook": client_request_hook,
        "client_response_hook": client_response_hook,
        "tracer_provider": tracer_provider or get_tracer_provider(),
    })
    FastAPIInstrumentor().instrument(**kwargs)
    logger.info("FastAPI instrumented.")
