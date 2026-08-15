import threading
from typing import Protocol, TypeVar, Any, Callable
from wrapt import wrap_function_wrapper
from concurrent import futures
import aworld.trace as trace
from aworld.trace.base import TraceContext, Span
from aworld.trace.propagator import get_global_trace_context
from aworld.trace.instrumentation import Instrumentor
from aworld.trace.instrumentation.utils import unwrap
from aworld.logs.util import logger


R = TypeVar("R")


class HasTraceContext(Protocol):
    _trace_context: TraceContext


class ThreadingInstrumentor(Instrumentor):
    '''
    Trace instrumentor for threading
    '''

    def instrumentation_dependencies(self) -> str:
        return ()

    def _instrument(self, **kwargs: Any):
        self._instrument_thread()
        self._instrument_timer()
        self._instrument_thread_pool()

    def _uninstrument(self, **kwargs: Any):
        self._uninstrument_thread()
        self._uninstrument_timer()
        self._uninstrument_thread_pool()

    @staticmethod
    def _instrument_thread():
        wrap_function_wrapper(
            threading.Thread,
            "start",
            ThreadingInstrumentor.__wrap_threading_start,
        )
        wrap_function_wrapper(
            threading.Thread,
            "run",
            ThreadingInstrumentor.__wrap_threading_run,
        )

    @staticmethod
    def _instrument_timer():
        wrap_function_wrapper(
            threading.Timer,
            "start",
            ThreadingInstrumentor.__wrap_threading_start,
        )
        wrap_function_wrapper(
            threading.Timer,
            "run",
            ThreadingInstrumentor.__wrap_threading_run,
        )

    @staticmethod
    def _instrument_thread_pool():
        wrap_function_wrapper(
            futures.ThreadPoolExecutor,
            "submit",
            ThreadingInstrumentor.__wrap_thread_pool_submit,
        )

    @staticmethod
    def _uninstrument_thread():
        unwrap(threading.Thread, "start")
        unwrap(threading.Thread, "run")

    @staticmethod
    def _uninstrument_timer():
        unwrap(threading.Timer, "start")
        unwrap(threading.Timer, "run")

    @staticmethod
    def _uninstrument_thread_pool():
        unwrap(futures.ThreadPoolExecutor, "submit")

    @staticmethod
    def __wrap_threading_start(
        call_wrapped: Callable[[], None],
        instance: HasTraceContext,
        args: tuple[()],
        kwargs: dict[str, Any],
    ) -> None:
        span: Span = trace.get_current_span()
        if span:
            instance._trace_context = TraceContext(
                trace_id=span.get_trace_id(), span_id=span.get_span_id())
        return call_wrapped(*args, **kwargs)

    @staticmethod
    def __wrap_threading_run(
        call_wrapped: Callable[..., R],
        instance: HasTraceContext,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> R:

        token = None
        try:
            if hasattr(instance, "_trace_context"):
                if instance._trace_context:
                    token = get_global_trace_context().set(instance._trace_context)
            return call_wrapped(*args, **kwargs)
        finally:
            if token:
                get_global_trace_context().reset(token)

    @staticmethod
    def __wrap_thread_pool_submit(
        call_wrapped: Callable[..., R],
        instance: futures.ThreadPoolExecutor,
        args: tuple[Callable[..., Any], ...],
        kwargs: dict[str, Any],
    ) -> R:
        # obtain the original function and wrapped kwargs
        original_func = args[0]
        trace_context = None
        span: Span = trace.get_current_span()
        if span and span.get_trace_id() != "":
            trace_context = TraceContext(
                trace_id=span.get_trace_id(), span_id=span.get_span_id())

        def wrapped_func(*func_args: Any, **func_kwargs: Any) -> R:
            token = None
            try:
                if trace_context:
                    token = get_global_trace_context().set(trace_context)
                return original_func(*func_args, **func_kwargs)
            finally:
                if token:
                    get_global_trace_context().reset(token)

        # replace the original function with the wrapped function
        new_args: tuple[Callable[..., Any], ...] = (wrapped_func,) + args[1:]
        return call_wrapped(*new_args, **kwargs)


def instrument_theading(**kwargs: Any) -> None:
    ThreadingInstrumentor().instrument(**kwargs)
    logger.info("Threading instrumented")
