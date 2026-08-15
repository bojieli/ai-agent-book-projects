from asyncio import iscoroutine
import wrapt
import time
import traceback
import aworld.trace.constants as trace_constants
from typing import Collection, Any, Union, Sequence
from aworld.trace.instrumentation import Instrumentor
from aworld.trace.instrumentation import semconv
from aworld.trace.base import (
    Tracer,
    SpanType,
    get_tracer_provider_silent
)
from aworld.logs.util import logger
from aworld.metrics.context_manager import MetricContext
from aworld.metrics.template import MetricTemplate
from aworld.metrics.metric import MetricType

tool_duration_histogram = MetricTemplate(
    type=MetricType.HISTOGRAM,
    name="tool_step_duration",
    unit="s",
    description="tool step run duration",
)

tool_step_counter = MetricTemplate(
    type=MetricType.COUNTER,
    name="tool_step_counter",
    unit="time",
    description="Number of tool step run",
)


def get_tool_name(tool_name: str,
                  action: Union['ActionModel', Sequence['ActionModel']]) -> tuple[str, trace_constants.RunType]:
    if tool_name == "mcp" and action:
        try:
            if isinstance(action, (list, tuple)):
                action = action[0]
            mcp_name = action.action_name.split("__")[0]
            return (mcp_name, trace_constants.RunType.MCP)
        except ValueError:
            logger.warning(traceback.format_exc())
            return (tool_name, trace_constants.RunType.MCP)
    return (tool_name, trace_constants.RunType.TOOL)


def get_tool_span_attributes(instance, message: 'Message'):
    run_type = trace_constants.RunType.TOOL
    action = message.payload
    agent_id = None
    tool_name = instance.name()
    if isinstance(action, (list, tuple)):
        action = action[0]
        if action:
            agent_id = action.agent_name
            tool_name, run_type = get_tool_name(action.tool_name, action)
    return {
        semconv.TOOL_NAME: tool_name,
        semconv.AGENT_ID: agent_id,
        semconv.AGENT_NAME: _get_agent_name_from_id(agent_id),
        semconv.TASK_ID: message.context.task_id if (message.context and message.context.task_id) else "",
        semconv.SESSION_ID: message.context.session_id if (message.context and message.context.session_id) else "",
        semconv.USER_ID: message.context.user if (message.context and message.context.user) else "",
        trace_constants.ATTRIBUTES_MESSAGE_RUN_TYPE_KEY: run_type.value
    }


def _end_span(span):
    if span:
        span.end()


def _get_agent_name_from_id(agent_id):
    if agent_id and '---' in agent_id:
        return agent_id.split('---', 1)[0]
    return agent_id


def _record_metric(duration, attributes, exception=None):
    if MetricContext.metric_initialized():
        MetricContext.histogram_record(tool_duration_histogram, duration, labels=attributes)
        if exception:
            run_counter_attr = {
                semconv.TOOL_STEP_SUCCESS: "0",
                "error.type": exception.__class__.__name__,
                **attributes
            }
        else:
            run_counter_attr = {
                semconv.TOOL_STEP_SUCCESS: "1",
                **attributes
            }
        MetricContext.count(tool_step_counter, 1, labels=run_counter_attr)


def _record_exception(span, start_time, exception, attributes):
    try:
        duration = time.time() - start_time if "start_time" in locals() else 0
        if span.is_recording:
            span.record_exception(exception=exception)
        _record_metric(duration, attributes, exception)
    except Exception as e:
        logger.warning(f"tool instrument record exception error.{e}")


def _record_response(instance,
                     start_time,
                     response,
                     attributes):
    try:
        duration = time.time() - start_time if "start_time" in locals() else 0
        _record_metric(duration, attributes)
    except Exception as e:
        logger.warning(f"tool instrument record response error.{e}")


def _async_step_class_wrapper(tracer: Tracer):
    async def _async_step_wrapper(wrapped, instance, args, kwargs):
        span = None
        message = args[0] or kwargs.get("message")
        attributes = get_tool_span_attributes(instance, message)
        if tracer:
            span = tracer.start_span(
                name=trace_constants.SPAN_NAME_PREFIX_TOOL + "step",
                span_type=SpanType.SERVER,
                attributes=attributes
            )
        start_time = time.time()
        try:
            response = await wrapped(*args, **kwargs)
            _record_response(instance, start_time, response, attributes)
        except Exception as e:
            _record_exception(span=span,
                              start_time=start_time,
                              exception=e,
                              attributes=attributes
                              )
            _end_span(span)
            raise e
        _end_span(span)
        return response
    return _async_step_wrapper


def _step_class_wrapper(tracer: Tracer):
    def _step_wrapper(wrapped, instance, args, kwargs):
        span = None
        message = args[0] or kwargs.get("message")
        attributes = get_tool_span_attributes(instance, message)
        if tracer:
            span = tracer.start_span(
                name=trace_constants.SPAN_NAME_PREFIX_TOOL + "step",
                span_type=SpanType.SERVER,
                attributes=attributes
            )
        start_time = time.time()
        try:
            response = wrapped(*args, **kwargs)
            _record_response(instance, start_time, response, attributes)
        except Exception as e:
            _record_exception(span=span,
                              start_time=start_time,
                              exception=e,
                              attributes=attributes
                              )
            _end_span(span)
            raise e
        _end_span(span)
        return response
    return _step_wrapper

async def _async_step_instance_wrapper(tracer: Tracer):

    @wrapt.decorator
    async def _awrapper(wrapped, instance, args, kwargs):
        wrapper_func = _async_step_class_wrapper(tracer=tracer)
        return await wrapper_func(wrapped, instance, args, kwargs)

    return _awrapper

def _step_instance_wrapper(tracer: Tracer):

    @wrapt.decorator
    def _wrapper(wrapped, instance, args, kwargs):
        wrapper_func = _step_class_wrapper(tracer)
        return wrapper_func(wrapped, instance, args, kwargs)

    return _wrapper

class ToolInstrumentor(Instrumentor):

    def instrumentation_dependencies(self) -> Collection[str]:
        return ()

    def _instrument(self, **kwargs):
        agent_trace_enabled = kwargs.get("trace_enabled", False)
        tracer_provider = get_tracer_provider_silent()
        tracer = None
        if tracer_provider and agent_trace_enabled:
            tracer = tracer_provider.get_tracer(
                "aworld.trace.instrumentation.tool")

        wrapt.wrap_function_wrapper(
            "aworld.core.tool.base",
            "AsyncBaseTool.step",
            _async_step_class_wrapper(tracer=tracer)
        )

        wrapt.wrap_function_wrapper(
            "aworld.core.tool.base",
            "AsyncTool.step",
            _async_step_class_wrapper(tracer=tracer)
        )

        wrapt.wrap_function_wrapper(
            "aworld.core.tool.base",
            "BaseTool.step",
            _step_class_wrapper(tracer=tracer)
        )

        wrapt.wrap_function_wrapper(
            "aworld.core.tool.base",
            "Tool.step",
            _step_class_wrapper(tracer=tracer)
        )

    def _uninstrument(self, **kwargs: Any):
        pass


def wrap_tool(tool):
    try:
        tracer_provider = get_tracer_provider_silent()
        if not tracer_provider:
            return tool
        tracer = tracer_provider.get_tracer(
            "aworld.trace.instrumentation.tool")

        async_wrapper = _async_step_instance_wrapper(tracer)
        wrapper = _step_instance_wrapper(tracer)
        if iscoroutine(tool.step):
            tool.step = async_wrapper(tool.step)
        else:
            tool.step = wrapper(tool.step)
    except Exception:
        logger.warning(traceback.format_exc())

    return tool