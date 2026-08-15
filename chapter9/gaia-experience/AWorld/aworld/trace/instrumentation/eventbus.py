import wrapt
from typing import Any, Collection
from aworld.trace.instrumentation import Instrumentor
from aworld.trace.base import Tracer, get_tracer_provider_silent, TraceContext
from aworld.trace.propagator import get_global_trace_propagator, get_global_trace_context
from aworld.trace.propagator.carrier import DictCarrier
from aworld.logs.util import logger


def _emit_message_class_wrapper(tracer: Tracer):
    async def awrapper(wrapped, instance, args, kwargs):
        from aworld.core.event.base import Message
        try:
            event = args[0] if len(args) > 0 else kwargs.get("event")
            propagator = get_global_trace_propagator()
            trace_provider = get_tracer_provider_silent()
            if trace_provider and propagator and event and isinstance(event, Message):
                if not event.headers:
                    event.headers = {}
                current_span = trace_provider.get_current_span()
                if current_span:
                    trace_context = TraceContext(
                        trace_id=current_span.get_trace_id(), span_id=current_span.get_span_id())
                    propagator.inject(trace_context=trace_context,
                                      carrier=DictCarrier(event.headers))
                logger.info(
                    f"EventManager emit_message trace propagate, event.headers={event.headers}")
        except Exception as e:
            logger.error(
                f"EventManager emit_message trace propagate exception: {e}")
        return await wrapped(*args, **kwargs)
    return awrapper


def _emit_message_instance_wrapper(tracer: Tracer):

    @wrapt.decorator
    async def awrapper(wrapped, instance, args, kwargs):
        wrapper = _emit_message_class_wrapper(tracer)
        return await wrapper(wrapped, instance, args, kwargs)

    return awrapper


def _consume_class_wrapper(tracer: Tracer):
    async def awrapper(wrapped, instance, args, kwargs):
        from aworld.core.event.base import Message
        event = await wrapped(*args, **kwargs)
        try:
            propagator = get_global_trace_propagator()
            if propagator and event and isinstance(event, Message) and event.headers:
                trace_context = propagator.extract(DictCarrier(event.headers))
                # logger.info(
                #     f"extract trace_context from event: {trace_context}")
                if trace_context:
                    get_global_trace_context().set(trace_context)
        except Exception as e:
            logger.error(
                f"EventManager consume trace propagate exception: {e}")
        return event
    return awrapper


def _consume_instance_wrapper(tracer: Tracer):

    @wrapt.decorator
    async def awrapper(wrapped, instance, args, kwargs):
        wrapper = _consume_class_wrapper(tracer)
        return await wrapper(wrapped, instance, args, kwargs)

    return awrapper


class EventBusInstrumentor(Instrumentor):

    def instrumentation_dependencies(self) -> Collection[str]:
        return ()

    def _uninstrument(self, **kwargs: Any):
        pass

    def _instrument(self, **kwargs: Any):
        tracer_provider = get_tracer_provider_silent()
        if not tracer_provider:
            return
        tracer = tracer_provider.get_tracer(
            "aworld.trace.instrumentation.eventbus")

        wrapt.wrap_function_wrapper(
            "aworld.events.manager",
            "EventManager.emit_message",
            _emit_message_class_wrapper(tracer=tracer)
        )

        wrapt.wrap_function_wrapper(
            "aworld.events.manager",
            "EventManager.consume",
            _consume_class_wrapper(tracer=tracer)
        )


def wrap_event_manager(manager: 'aworld.events.manager.EventManager'):
    tracer_provider = get_tracer_provider_silent()
    if not tracer_provider:
        return manager
    tracer = tracer_provider.get_tracer(
        "aworld.trace.instrumentation.eventbus")

    emit_wrapper = _emit_message_instance_wrapper(tracer)
    consume_wrapper = _consume_instance_wrapper(tracer)

    manager.emit_message = emit_wrapper(manager.emit_message)
    manager.consume = consume_wrapper(manager.consume)

    return manager
