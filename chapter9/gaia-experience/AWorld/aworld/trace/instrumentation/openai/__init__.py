import wrapt
import time
import openai
import traceback
import aworld.trace.instrumentation.semconv as semconv
from typing import Collection, Any, Union
from aworld.trace.instrumentation import Instrumentor
from aworld.trace.base import (
    Tracer,
    SpanType,
    get_tracer_provider_silent
)
from aworld.trace.constants import ATTRIBUTES_MESSAGE_RUN_TYPE_KEY, RunType
from aworld.trace.instrumentation.openai.inout_parse import (
    run_async,
    handle_openai_request,
    is_streaming_response,
    record_stream_response_chunk,
    parse_openai_response,
    record_stream_token_usage,
    model_as_dict,
    parse_response_message,
)
from aworld.trace.instrumentation.llm_metrics import (
    record_exception_metric,
    record_chat_response_metric,
    record_streaming_time_to_first_token,
    record_streaming_time_to_generate
)
from aworld.logs.util import logger


def _chat_wrapper(tracer: Tracer):

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        model_name = kwargs.get("model", "")
        if not model_name:
            model_name = "OpenAI"
        span_attributes = {}
        span_attributes[ATTRIBUTES_MESSAGE_RUN_TYPE_KEY] = RunType.LLM.value

        span = tracer.start_span(
            name=model_name, span_type=SpanType.CLIENT, attributes=span_attributes)

        run_async(handle_openai_request(span, kwargs, instance))
        start_time = time.time()
        try:
            response = wrapped(*args, **kwargs)
        except Exception as e:
            record_exception(span=span,
                             start_time=start_time,
                             exception=e
                             )
            span.end()
            raise e

        if is_streaming_response(response):
            return WrappedStreamResponse(span=span,
                                         response=response,
                                         instance=instance,
                                         start_time=start_time,
                                         request_kwargs=kwargs
                                         )

        record_completion(span=span,
                          start_time=start_time,
                          response=response,
                          request_kwargs=kwargs,
                          instance=instance
                          )
        span.end()
        return response

    return wrapper


def _achat_class_wrapper(tracer: Tracer):

    async def awrapper(wrapped, instance, args, kwargs):
        model_name = kwargs.get("model", "")
        if not model_name:
            model_name = "OpenAI"
        span_attributes = {}
        span_attributes[ATTRIBUTES_MESSAGE_RUN_TYPE_KEY] = RunType.LLM.value

        span = tracer.start_span(
            name=model_name, span_type=SpanType.CLIENT, attributes=span_attributes)

        await handle_openai_request(span, kwargs, instance)
        start_time = time.time()
        try:
            response = await wrapped(*args, **kwargs)
        except Exception as e:
            record_exception(span=span,
                             start_time=start_time,
                             exception=e
                             )
            span.end()
            raise e

        if is_streaming_response(response):
            return WrappedStreamResponse(span=span,
                                         response=response,
                                         instance=instance,
                                         start_time=start_time,
                                         request_kwargs=kwargs
                                         )
        record_completion(span=span,
                          start_time=start_time,
                          response=response,
                          request_kwargs=kwargs,
                          instance=instance
                          )
        span.end()
        return response

    return awrapper


def _achat_instance_wrapper(tracer: Tracer):

    @wrapt.decorator
    async def _awrapper(wrapped, instance, args, kwargs):
        wrapper_func = _achat_class_wrapper(tracer)
        return await wrapper_func(wrapped, instance, args, kwargs)

    return _awrapper


def record_exception(span, start_time, exception):
    '''
    record openai chat exception to trace and metrics
    '''
    try:
        duration = time.time() - start_time if "start_time" in locals() else 0
        if span.is_recording:
            span.record_exception(exception=exception)
        record_exception_metric(exception=exception, duration=duration)
    except Exception as e:
        logger.warning(f"openai instrument record exception error.{e}")


def record_completion(span,
                      start_time,
                      response,
                      request_kwargs,
                      instance):
    '''
    Record chat completion to trace and metrics
    '''
    duration = time.time() - start_time if "start_time" in locals() else 0
    response_dict = model_as_dict(response)
    attributes = parse_openai_response(
        response_dict, request_kwargs, instance, False)
    usage = response_dict.get("usage")
    choices = response_dict.get("choices")
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")

    span_attributes = {
        **attributes,
        semconv.GEN_AI_USAGE_INPUT_TOKENS: prompt_tokens,
        semconv.GEN_AI_USAGE_OUTPUT_TOKENS: completion_tokens,
        semconv.GEN_AI_DURATION: duration
    }
    span_attributes.update(parse_response_message(choices))
    span.set_attributes(span_attributes)
    record_chat_response_metric(attributes=attributes,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                duration=duration,
                                choices=choices
                                )


class WrappedStreamResponse(wrapt.ObjectProxy):

    def __init__(
        self,
        span,
        response,
        instance=None,
        start_time=None,
        request_kwargs=None
    ):
        super().__init__(response)
        self._span = span
        self._instance = instance
        self._start_time = start_time
        self._complete_response = {"choices": [], "model": ""}
        self._first_token_recorded = False
        self._request_kwargs = request_kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__wrapped__.__exit__(exc_type, exc_val, exc_tb)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.__wrapped__.__aexit__(exc_type, exc_val, exc_tb)

    def __iter__(self):
        return self

    def __aiter__(self):
        return self

    def __next__(self):
        try:
            chunk = self.__wrapped__.__next__()
        except Exception as e:
            if isinstance(e, StopIteration):
                self._close_span()
            raise e
        else:
            self._process_stream_chunk(chunk)
            return chunk

    async def __anext__(self):
        try:
            chunk = await self.__wrapped__.__anext__()
        except Exception as e:
            if isinstance(e, StopAsyncIteration):
                self._close_span()
            raise e
        else:
            self._process_stream_chunk(chunk)
            return chunk

    def _process_stream_chunk(self, chunk):
        record_stream_response_chunk(chunk, self._complete_response)
        if not self._first_token_recorded:
            self._time_of_first_token = time.time()
            duration = self._time_of_first_token - self._start_time
            attribute = parse_openai_response(
                self._complete_response, self._request_kwargs, self._instance, True)
            record_streaming_time_to_first_token(duration, attribute)
            self._first_token_recorded = True

    def _close_span(self):
        duration = None
        first_token_duration = None
        first_token_to_generate_duration = None
        if self._start_time and isinstance(self._start_time, (float, int)):
            duration = time.time() - self._start_time
        if self._time_of_first_token and self._start_time and isinstance(self._start_time, (float, int)):
            first_token_duration = self._time_of_first_token - self._start_time
            first_token_to_generate_duration = time.time() - self._time_of_first_token
        prompt_usage, completion_usage = record_stream_token_usage(
            self._complete_response, self._request_kwargs)
        attributes = parse_openai_response(
            self._complete_response, self._request_kwargs, self._instance, True)
        choices = self._complete_response.get("choices")
        span_attributes = {
            **attributes,
            "llm.prompt_tokens": prompt_usage,
            "llm.completion_tokens": completion_usage,
            "llm.duration": duration,
            "llm.first_token_duration": first_token_duration
        }
        span_attributes.update(parse_response_message(choices))
        self._span.set_attributes(span_attributes)
        record_chat_response_metric(attributes=attributes,
                                    prompt_tokens=prompt_usage,
                                    completion_tokens=completion_usage,
                                    duration=duration,
                                    choices=choices
                                    )
        record_streaming_time_to_generate(
            first_token_to_generate_duration, attributes)

        self._span.end()


class OpenAIInstrumentor(Instrumentor):

    def instrumentation_dependencies(self) -> Collection[str]:
        return ("openai >= 1.0.0",)

    def _instrument(self, **kwargs):
        tracer_provider = kwargs.get("tracer_provider")
        tracer = tracer_provider.get_tracer(
            "aworld.trace.instrumentation.openai")

        wrapt.wrap_function_wrapper(
            "openai.resources.chat.completions",
            "Completions.create",
            _chat_wrapper(tracer=tracer)
        )

        wrapt.wrap_function_wrapper(
            "openai.resources.chat.completions",
            "AsyncCompletions.create",
            _achat_class_wrapper(tracer)
        )

    def _instrument(self, **kwargs: Any):
        pass


def wrap_openai(client: Union[openai.OpenAI, openai.AsyncOpenAI]):
    """Patch the OpenAI client to make it traceable.
       Example:
       client = wrap_openai(openai.OpenAI())
    """
    try:
        tracer_provider = get_tracer_provider_silent()
        if not tracer_provider:
            return
        tracer = tracer_provider.get_tracer(
            "aworld.trace.instrumentation.openai")

        if isinstance(client, openai.OpenAI):
            wrapper = _chat_wrapper(tracer)
            client.chat.completions.create = wrapper(
                client.chat.completions.create)
            logger.info(
                f"[{client.__class__}]client.chat.completions.create be warpped")
        if isinstance(client, openai.AsyncOpenAI):
            awrapper = _achat_instance_wrapper(tracer)
            client.chat.completions.create = awrapper(
                client.chat.completions.create)
            logger.info(
                f"[{client.__class__}]client.chat.completions.create be warpped")
    except Exception:
        logger.warning(traceback.format_exc())

    return client
