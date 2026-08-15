import copy
import json
import aworld.trace.instrumentation.semconv as semconv
from aworld.models.model_response import ModelResponse, ToolCall
from aworld.trace.base import Span
from aworld.trace.instrumentation.openai.inout_parse import should_trace_prompts, need_flatten_messages
from aworld.logs.util import logger
from aworld.utils.serialized_util import to_serializable


def parser_request_params(kwargs, instance: 'aworld.models.llm.LLMModel'):
    attributes = {
        semconv.GEN_AI_SYSTEM: instance.provider_name,
        semconv.GEN_AI_REQUEST_MODEL: instance.provider.model_name,
        semconv.GEN_AI_REQUEST_MAX_TOKENS: kwargs.get("max_tokens", ""),
        semconv.GEN_AI_REQUEST_TEMPERATURE: kwargs.get("temperature", ""),
        semconv.GEN_AI_REQUEST_STOP_SEQUENCES: str(kwargs.get("stop", [])),
        semconv.GEN_AI_REQUEST_FREQUENCY_PENALTY: kwargs.get("frequency_penalty", ""),
        semconv.GEN_AI_REQUEST_PRESENCE_PENALTY: kwargs.get("presence_penalty", ""),
        semconv.GEN_AI_REQUEST_USER: kwargs.get("user", ""),
        semconv.GEN_AI_REQUEST_EXTRA_HEADERS: kwargs.get("extra_headers", ""),
        semconv.GEN_AI_REQUEST_STREAMING: kwargs.get("stream", ""),
        semconv.GEN_AI_REQUEST_TOP_P: kwargs.get("top_p", ""),
        semconv.GEN_AI_OPERATION_NAME: "chat"
    }
    return attributes


async def handle_request(span: Span, kwargs, instance):
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
                    semconv.GEN_AI_PROMPT: covert_to_jsonstr(messages)
                })
        tools = kwargs.get("tools")
        if tools:
            if need_flatten_messages():
                attributes.update(parse_prompt_tools(tools))
            else:
                attributes.update({
                    semconv.GEN_AI_PROMPT_TOOLS: covert_to_jsonstr(tools)
                })

        filterd_attri = {k: v for k, v in attributes.items()
                         if (v and v != "")}

        span.set_attributes(filterd_attri)
    except Exception as e:
        logger.warning(f"trace handle openai request error: {e}")


def get_common_attributes_from_response(instance: 'LLMModel', is_async, is_streaming):
    operation = "acompletion" if is_async else "completion"
    if is_streaming:
        operation = "astream_completion" if is_async else "stream_completion"
    return {
        semconv.GEN_AI_SYSTEM: instance.provider_name,
        semconv.GEN_AI_RESPONSE_MODEL: instance.provider.model_name,
        semconv.GEN_AI_METHOD_NAME: operation,
        semconv.GEN_AI_SERVER_ADDRESS: instance.provider.base_url
    }


def accumulate_stream_response(chunk: ModelResponse, complete_response: dict):
    from aworld.utils.common import nest_dict_counter
    # logger.info(f"accumulate_stream_response chunk= {chunk}")

    complete_response["model"] = chunk.model
    complete_response["id"] = chunk.id
    if chunk.content:
        complete_response["content"] += chunk.content
    if chunk.tool_calls:
        complete_response["tool_calls"].extend(chunk.tool_calls)
    if chunk.error:
        complete_response["error"] = chunk.error
    complete_response["usage"] = nest_dict_counter(
        complete_response["usage"], chunk.usage)


def record_stream_token_usage(complete_response, request_kwargs) -> tuple[int, int]:
    '''
        return (prompt_usage, completion_usage)
    '''
    # logger.info(
    #     f"record_stream_token_usage complete_response= {complete_response}")
    usage = complete_response.get("usage", {})
    if usage:
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        return (prompt_tokens, completion_tokens)
    return (0, 0)


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
            content = json.dumps(content, ensure_ascii=False)
            attributes.update({f"{prefix}.content": content})
        if msg.get("tool_call_id"):
            attributes.update({
                f"{prefix}.tool_call_id": msg.get("tool_call_id")})
        tool_calls = msg.get("tool_calls")
        # logger.info(f"input tool_calls={tool_calls}")
        if tool_calls:
            for i, tool_call in enumerate(tool_calls):
                if isinstance(tool_call, dict):
                    function = tool_call.get('function')
                    attributes.update({
                        f"{prefix}.tool_calls.{i}.id": tool_call.get("id")})
                    attributes.update({
                        f"{prefix}.tool_calls.{i}.name": function.get("name")})
                    attributes.update({
                        f"{prefix}.tool_calls.{i}.arguments": function.get("arguments")})
                elif isinstance(tool_call, ToolCall):
                    function = tool_call.function
                    attributes.update({
                        f"{prefix}.tool_calls.{i}.id": tool_call.id})
                    attributes.update({
                        f"{prefix}.tool_calls.{i}.name": function.name})
                    attributes.update({
                        f"{prefix}.tool_calls.{i}.arguments": function.arguments})
    return attributes


def parse_prompt_tools(tools):
    attributes = {}
    for i, tool in enumerate(tools):
        prefix = f"{semconv.GEN_AI_PROMPT_TOOLS}.{i}"
        if isinstance(tool, dict):
            tool_type = tool.get("type")
            attributes.update({
                f"{prefix}.type": tool_type})
            if tool.get(tool_type):
                attributes.update({
                    f"{prefix}.name": tool.get(tool_type).get("name")})
    return attributes


def parse_response_message(tool_calls) -> dict:
    attributes = {}
    prefix = semconv.GEN_AI_COMPLETION_TOOL_CALLS
    if tool_calls:
        if need_flatten_messages():
            for i, tool_call in enumerate(tool_calls):
                function = tool_call.get("function")
                attributes.update(
                    {f"{prefix}.{i}.id": tool_call.get("id")})
                attributes.update(
                    {f"{prefix}.{i}.name": function.get("name")})
                attributes.update(
                    {f"{prefix}.{i}.arguments": function.get("arguments")})
        else:
            attributes.update({
                prefix: covert_to_jsonstr(tool_calls)
            })
    return attributes


def response_to_dic(response: ModelResponse) -> dict:
    logger.info(f"completion response= {response}")
    return response.to_dict()


def covert_to_jsonstr(obj):
    try:
        return json.dumps(to_serializable(obj), ensure_ascii=False)
    except:
        logger.warning(f"covert_to_jsonstr error: {obj.__class__.__name__}")
        return str(obj)
