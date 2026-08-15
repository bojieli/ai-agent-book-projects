# coding: utf-8
# Copyright (c) 2025 inclusionAI.
import traceback
from contextvars import ContextVar, Token
from aworld.trace.base import TraceContext, Propagator
from aworld.trace.propagator.w3c import W3CTraceContextPropagator
from aworld.trace.baggage.sofa_tracer import SofaTracerBaggagePropagator
from aworld.trace.baggage.w3c import W3CBaggagePropagator
from aworld.logs.util import logger


class CompositePropagator(Propagator):
    """
    Composite propagator.
    """

    def __init__(self, propagators: list[Propagator]):
        self._propagators = propagators

    def extract(self, carrier: dict) -> TraceContext:
        trace_context = None
        for propagator in self._propagators:
            try:
                context = propagator.extract(carrier)
                if context and not trace_context:
                    trace_context = context
            except Exception:
                stack_trace = traceback.format_exc()
                logger.error(
                    f"Failed to extract trace context: {stack_trace}, propagator: {propagator.__class__.__name__}")
        return trace_context

    def inject(self, trace_context: TraceContext, carrier: dict) -> None:
        for propagator in self._propagators:
            propagator.inject(trace_context, carrier)


_GLOBAL_TRACE_PROPAGATOR = CompositePropagator(
    [W3CTraceContextPropagator(), SofaTracerBaggagePropagator(), W3CBaggagePropagator()])


def get_global_trace_propagator():
    return _GLOBAL_TRACE_PROPAGATOR


class TraceContextHolder:
    def __init__(self):
        self._var = ContextVar("current_trace_context", default=None)

    def set(self, trace_context: TraceContext) -> Token:
        if not trace_context or not trace_context.trace_id or not trace_context.span_id:
            return None
        token = self._var.set(trace_context)
        return token

    def get_and_clear(self) -> TraceContext:
        try:
            value = self._var.get()
        except LookupError:
            return self._var.get(None)
        finally:
            self._var.set(None)
        return value

    def get(self) -> TraceContext:
        return self._var.get()

    def reset(self, token: Token):
        self._var.reset(token)


_GLOBAL_TRACE_CONTEXT = TraceContextHolder()


def get_global_trace_context():
    return _GLOBAL_TRACE_CONTEXT
