import asyncio
import os
import threading
import copy
import json
import openai
from importlib.metadata import version
from aworld.logs.util import logger
from aworld.trace.base import Span
from aworld.utils import import_package
import aworld.trace.instrumentation.semconv as semconv

_PYDANTIC_VERSION = version("pydantic")


def should_trace_prompts():
    '''Determine whether it is necessary to record the message
    '''
    return (os.getenv("SHOULD_TRACE_PROMPTS") or "true").lower() == "true"


def need_flatten_messages():
    '''Determine whether it is necessary to flatten the messages
    '''
    return (os.getenv("TRACE_FLATTEN_MESSAGES") or "false").lower() == "true"


def run_async(method):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        thread = threading.Thread(target=lambda: asyncio.run(method))
        thread.start()
        thread.join()
    else:
        asyncio.run(method)


async def handle_openai_request(span: Span, kwargs, instance):
    if not span or not span.is_recording():
        return
    try:
        attributes = parser_request_params(kwargs, instance)
        if should_trace_prompts():
            messages = kwargs.get("messages")
            if need_flatten_messages():
                attributes.update(parse_request_message(messages))
            else:
                attributes.update({
                    semconv.GEN_AI_PROMPT: str(messages),
                })
        span.set_attributes(attributes)
    except ValueError as e:
        logger.warning(f"trace handle openai request error: {e}")


def parser_request_params(kwargs, instance):
    attributes = {
        semconv.GEN_AI_SYSTEM: "OpenAI",
        semconv.GEN_AI_REQUEST_MODEL: kwargs.get("model", ""),
        semconv.GEN_AI_REQUEST_MAX_TOKENS: kwargs.get("max_tokens", ""),
        semconv.GEN_AI_REQUEST_TEMPERATURE: kwargs.get("temperature", ""),
        semconv.GEN_AI_REQUEST_TOP_P: kwargs.get("top_p", ""),
        semconv.GEN_AI_REQUEST_FREQUENCY_PENALTY: kwargs.get("frequency_penalty", ""),
        semconv.GEN_AI_REQUEST_PRESENCE_PENALTY: kwargs.get("presence_penalty", ""),
        semconv.GEN_AI_REQUEST_USER: kwargs.get("user", ""),
        semconv.GEN_AI_REQUEST_EXTRA_HEADERS: kwargs.get("extra_headers", ""),
        semconv.GEN_AI_REQUEST_STREAMING: kwargs.get("stream", ""),
        semconv.GEN_AI_OPERATION_NAME: "chat"
    }

    client = instance._client
    if isinstance(client, (openai.AsyncOpenAI, openai.OpenAI)):
        attributes.update({"llm.base_url": str(client.base_url)})

    filterd_attri = {k: v for k, v in attributes.items()
                     if (v and v != "")}
    return filterd_attri


def is_streaming_response(response):
    return isinstance(response, openai.Stream) or isinstance(response, openai.AsyncStream)


def parse_openai_response(response, request_kwargs, instance, is_streaming):
    return {
        semconv.GEN_AI_RESPONSE_MODEL: response.get("model") or request_kwargs.get("model") or None,
        semconv.GEN_AI_SERVER_ADDRESS: _get_openai_base_url(instance)
    }


def record_stream_token_usage(complete_response, request_kwargs) -> tuple[int, int]:
    '''
        return (prompt_usage, completion_usage)
    '''
    prompt_usage = 0
    completion_usage = 0

    # prompt_usage
    if request_kwargs and request_kwargs.get("messages"):
        prompt_content = ""
        model_name = complete_response.get(
            "model") or request_kwargs.get("model") or "gpt-4"
        for msg in request_kwargs.get("messages"):
            if msg.get("content"):
                prompt_content += msg.get("content")
        if model_name:
            prompt_usage = get_token_count_from_string(
                prompt_content, model_name)

    # completion_usage
    if complete_response.get("choices"):
        completion_content = ""
        model_name = complete_response.get("model") or "gpt-4"

        for choice in complete_response.get("choices"):
            if choice.get("message") and choice.get("message").get("content"):
                completion_content += choice["message"]["content"]

        if model_name:
            completion_usage = get_token_count_from_string(
                completion_content, model_name)

    return (prompt_usage, completion_usage)


def _get_openai_base_url(instance):
    if hasattr(instance, "_client"):
        client = instance._client  # pylint: disable=protected-access
        if isinstance(client, (openai.AsyncOpenAI, openai.OpenAI)):
            return str(client.base_url)

    return ""


def get_token_count_from_string(string: str, model_name: str):
    import_package("tiktoken")
    import tiktoken

    if tiktoken_encodings.get(model_name) is None:
        try:
            encoding = tiktoken.encoding_for_model(model_name)
        except KeyError as ex:
            logger.warning(
                f"Failed to get tiktoken encoding for model_name {model_name}, error: {str(ex)}")
            return None

        tiktoken_encodings[model_name] = encoding
    else:
        encoding = tiktoken_encodings.get(model_name)

    token_count = len(encoding.encode(string))
    return token_count


def record_stream_response_chunk(chunk, complete_response):
    chunk = model_as_dict(chunk)
    complete_response["model"] = chunk.get("model")
    complete_response["id"] = chunk.get("id")

    # prompt filter results
    if chunk.get("prompt_filter_results"):
        complete_response["prompt_filter_results"] = chunk.get(
            "prompt_filter_results")

    for choice in chunk.get("choices"):
        index = choice.get("index")
        if len(complete_response.get("choices")) <= index:
            complete_response["choices"].append(
                {"index": index, "message": {"content": "", "role": ""}})
        complete_choice = complete_response.get("choices")[index]
        if choice.get("finish_reason"):
            complete_choice["finish_reason"] = choice.get("finish_reason")
        if choice.get("content_filter_results"):
            complete_choice["content_filter_results"] = choice.get(
                "content_filter_results")

        delta = choice.get("delta")

        if delta and delta.get("content"):
            complete_choice["message"]["content"] += delta.get("content")

        if delta and delta.get("role"):
            complete_choice["message"]["role"] = delta.get("role")
        if delta and delta.get("tool_calls"):
            tool_calls = delta.get("tool_calls")
            if not isinstance(tool_calls, list) or len(tool_calls) == 0:
                continue

            if not complete_choice["message"].get("tool_calls"):
                complete_choice["message"]["tool_calls"] = []

            for tool_call in tool_calls:
                i = int(tool_call["index"])
                if len(complete_choice["message"]["tool_calls"]) <= i:
                    complete_choice["message"]["tool_calls"].append(
                        {"id": "", "function": {"name": "", "arguments": ""}}
                    )

                span_tool_call = complete_choice["message"]["tool_calls"][i]
                span_function = span_tool_call["function"]
                tool_call_function = tool_call.get("function")

                if tool_call.get("id"):
                    span_tool_call["id"] = tool_call.get("id")
                if tool_call_function and tool_call_function.get("name"):
                    span_function["name"] = tool_call_function.get("name")
                if tool_call_function and tool_call_function.get("arguments"):
                    span_function["arguments"] += tool_call_function.get(
                        "arguments")


def parse_request_message(messages):
    '''
    flatten request message to attributes
    '''
    attributes = {}
    for i, msg in enumerate(messages):
        prefix = f"{semconv.GEN_AI_PROMPT}.{i}"
        attributes.update({f"{prefix}.role": msg.get("role")})
        if msg.get("content"):
            content = copy.deepcopy(msg.get("content"))
            content = json.dumps(content)
            attributes.update({f"{prefix}.content": content})
        if msg.get("tool_call_id"):
            attributes.update({
                f"{prefix}.tool_call_id": msg.get("tool_call_id")})
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            for i, tool_call in enumerate(tool_calls):
                tool_call = model_as_dict(tool_call)
                function = tool_call.get("function")
                attributes.update({
                    f"{prefix}.tool_calls.{i}.id": tool_call.get("id")})
                attributes.update({
                    f"{prefix}.tool_calls.{i}.name": function.get("name")})
                attributes.update({
                    f"{prefix}.tool_calls.{i}.arguments": function.get("arguments")})
    return attributes


def parse_response_message(choices) -> dict:
    attributes = {}
    if not should_trace_prompts():
        return attributes
    for choice in choices:
        index = choice.get("index")
        prefix = f"{semconv.GEN_AI_COMPLETION}.{index}"
        attributes.update(
            {f"{prefix}.finish_reason": choice.get("finish_reason")})

        message = choice.get("message")
        if not message:
            continue

        attributes.update({f"{prefix}.role": message.get("role")})

        if message.get("refusal"):
            attributes.update({f"{prefix}.refusal": message.get("refusal")})
        else:
            attributes.update({f"{prefix}.content": message.get("content")})

        function_call = message.get("function_call")
        if function_call:
            attributes.update(
                {f"{prefix}.tool_calls.0.name": function_call.get("name")})
            attributes.update(
                {f"{prefix}.tool_calls.0.arguments": function_call.get("arguments")})

        tool_calls = message.get("tool_calls")
        if tool_calls:
            for i, tool_call in enumerate(tool_calls):
                function = tool_call.get("function")
                attributes.update(
                    {f"{prefix}.tool_calls.{i}.id": tool_call.get("id")})
                attributes.update(
                    {f"{prefix}.tool_calls.{i}.name": function.get("name")})
                attributes.update(
                    {f"{prefix}.tool_calls.{i}.arguments": function.get("arguments")})
    return attributes


def model_as_dict(model):
    if isinstance(model, dict):
        return model
    if _PYDANTIC_VERSION < "2.0.0":
        return model.dict()
    if hasattr(model, "model_dump"):
        return model.model_dump()
    elif hasattr(model, "parse"):  # Raw API response
        return model_as_dict(model.parse())
    else:
        return model
