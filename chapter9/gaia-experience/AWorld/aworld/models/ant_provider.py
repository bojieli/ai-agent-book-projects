import ast
import asyncio
import datetime
import html
import json
import os
import time

from typing import (
    Any,
    List,
    Dict,
    Generator,
    AsyncGenerator,
)
from binascii import b2a_hex

from aworld.config.conf import ClientType
from aworld.core.llm_provider import LLMProviderBase
from aworld.models.llm_http_handler import LLMHTTPHandler
from aworld.models.model_response import ModelResponse, LLMResponseError, ToolCall
from aworld.logs.util import logger
from aworld.utils import import_package
from aworld.models.utils import usage_process

MODEL_NAMES = {
    "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-sonnet-20240620", "claude-3-opus-20240229"],
    "openai": ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "o3-mini", "gpt-4o-mini"],
}


# Custom JSON encoder to handle ToolCall and other special types
class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle ToolCall objects and other special types."""

    def default(self, obj):
        # Handle objects with to_dict method
        if hasattr(obj, 'to_dict') and callable(obj.to_dict):
            return obj.to_dict()

        # Handle objects with __dict__ attribute (most custom classes)
        if hasattr(obj, '__dict__'):
            return obj.__dict__

        # Let the base class handle it (will raise TypeError if not serializable)
        return super().default(obj)


class AntProvider(LLMProviderBase):
    """Ant provider implementation.
    """

    def _init_provider(self):
        """Initialize Ant provider.

        Returns:
            Ant provider instance.
        """
        import_package("Crypto", install_name="pycryptodome")

        # Get API key
        api_key = self.api_key

        if not api_key:
            env_var = "ANT_API_KEY"
            api_key = os.getenv(env_var, "")
            self.api_key = api_key
            if not api_key:
                raise ValueError(
                    f"ANT API key not found, please set {env_var} environment variable or provide it in the parameters")

        if api_key and api_key.startswith("ak_info:"):
            ak_info_str = api_key[len("ak_info:"):]
            try:
                ak_info = json.loads(ak_info_str)
                for key, value in ak_info.items():
                    os.environ[key] = value
                    if key == "ANT_API_KEY":
                        api_key = value
                        self.api_key = api_key
            except Exception as e:
                logger.warn(f"Invalid ANT API key startswith ak_info: {api_key}")

        self.stream_api_key = os.getenv("ANT_STREAM_API_KEY", "")

        base_url = self.base_url
        if not base_url:
            base_url = os.getenv("ANT_ENDPOINT", "https://zdfmng.alipay.com")
            self.base_url = base_url

        self.aes_key = os.getenv("ANT_AES_KEY", "")

        self.is_http_provider = True
        self.kwargs["client_type"] = ClientType.HTTP
        logger.info(f"Using HTTP provider for Ant")
        self.http_provider = LLMHTTPHandler(
            base_url=base_url,
            api_key=api_key,
            model_name=self.model_name,
        )
        self.is_http_provider = True
        return self.http_provider

    def _init_async_provider(self):
        """Initialize async Ant provider.

        Returns:
            Async Ant provider instance.
        """
        # Get API key
        if not self.provider:
            provider = self._init_provider()
            return provider

    @classmethod
    def supported_models(cls) -> list[str]:
        return [""]

    def _aes_encrypt(self, data, key):
        """AES encryption function. If data is not a multiple of 16 [encrypted data must be a multiple of 16!], pad it to a multiple of 16.

        Args:
            key: Encryption key
            data: Data to encrypt

        Returns:
            Encrypted data
        """
        from Crypto.Cipher import AES

        iv = "1234567890123456"
        cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
        block_size = AES.block_size

        # Check if data is a multiple of 16, if not, pad with b'\0'
        if len(data) % block_size != 0:
            add = block_size - (len(data) % block_size)
        else:
            add = 0
        data = data.encode('utf-8') + b'\0' * add
        encrypted = cipher.encrypt(data)
        result = b2a_hex(encrypted)
        return result.decode('utf-8')

    def _build_openai_params(self,
                             messages: List[Dict[str, str]],
                             temperature: float = 0.0,
                             max_tokens: int = None,
                             stop: List[str] = None,
                             **kwargs) -> Dict[str, Any]:
        openai_params = {
            "model": kwargs.get("model_name", self.model_name or ""),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stop": stop
        }

        supported_params = [
            "frequency_penalty", "logit_bias", "logprobs", "top_logprobs",
            "presence_penalty", "response_format", "seed", "stream", "top_p",
            "user", "function_call", "functions", "tools", "tool_choice"
        ]

        for param in supported_params:
            if param in kwargs:
                openai_params[param] = kwargs[param]

        return openai_params

    def _build_claude_params(self,
                             messages: List[Dict[str, str]],
                             temperature: float = 0.0,
                             max_tokens: int = None,
                             stop: List[str] = None,
                             **kwargs) -> Dict[str, Any]:
        claude_params = {
            "model": kwargs.get("model_name", self.model_name or ""),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stop": stop
        }

        supported_params = [
            "top_p", "top_k", "reasoning_effort", "tools", "tool_choice"
        ]

        for param in supported_params:
            if param in kwargs:
                claude_params[param] = kwargs[param]

        return claude_params

    def _get_visit_info(self):
        visit_info = {
            "visitDomain": self.kwargs.get("ant_visit_domain") or os.getenv("ANT_VISIT_DOMAIN", "BU_general"),
            "visitBiz": self.kwargs.get("ant_visit_biz") or os.getenv("ANT_VISIT_BIZ", ""),
            "visitBizLine": self.kwargs.get("ant_visit_biz_line") or os.getenv("ANT_VISIT_BIZ_LINE", "")
        }
        if not visit_info["visitBiz"] or not visit_info["visitBizLine"]:
            return None
        return visit_info

    def _get_service_param(self,
                           message_key: str,
                           output_type: str = "request",
                           messages: List[Dict[str, str]] = None,
                           temperature: float = 0.0,
                           max_tokens: int = None,
                           stop: List[str] = None,
                           **kwargs
                           ) -> Dict[str, Any]:
        """Get service name from model name.
        Returns:
            Service name.
        """
        if messages:
            for message in messages:
                if message["role"] == "assistant" and "tool_calls" in message and message["tool_calls"]:
                    if message["content"] is None: message["content"] = ""
                    processed_tool_calls = []
                    for tool_call in message["tool_calls"]:
                        if isinstance(tool_call, dict):
                            processed_tool_calls.append(tool_call)
                        elif isinstance(tool_call, ToolCall):
                            processed_tool_calls.append(tool_call.to_dict())
                    message["tool_calls"] = processed_tool_calls
        query_conditions = {
            "messageKey": message_key,
        }
        param = {"cacheInterval": -1, }
        visit_info = self._get_visit_info()
        if not visit_info:
            raise LLMResponseError(
                f"AntProvider#Invalid visit_info, please set ANT_VISIT_BIZ and ANT_VISIT_BIZ_LINE environment variable or provide it in the parameters",
                self.model_name or "unknown"
            )
        param.update(visit_info)
        if self.model_name.startswith("claude"):
            query_conditions.update(self._build_claude_params(messages, temperature, max_tokens, stop, **kwargs))
            param.update({
                "serviceName": "amazon_claude_chat_completions_dataview",
                "queryConditions": query_conditions,
            })
        elif output_type == "pull":
            param.update({
                "serviceName": "chatgpt_response_query_dataview",
                "queryConditions": query_conditions
            })
        else:
            query_conditions = {
                "model": self.model_name,
                "n": "1",
                "api_key": self.api_key,
                "messageKey": message_key,
                "outputType": "PULL",
                "messages": messages,
            }
            query_conditions.update(self._build_openai_params(messages, temperature, max_tokens, stop, **kwargs))
            param.update({
                "serviceName": "asyn_chatgpt_prompts_completions_query_dataview",
                "queryConditions": query_conditions,
            })
        return param

    def _gen_message_key(self):
        def _timestamp():
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            return timestamp

        timestamp = _timestamp()
        message_key = "llm_call_%s" % (timestamp)
        return message_key

    def _build_request_data(self, param: Dict[str, Any]):
        param_data = json.dumps(param)
        encrypted_param_data = self._aes_encrypt(param_data, self.aes_key)
        post_data = {"encryptedParam": encrypted_param_data}
        return post_data

    def _build_chat_query_request_data(self,
                                       message_key: str,
                                       messages: List[Dict[str, str]],
                                       temperature: float = 0.0,
                                       max_tokens: int = None,
                                       stop: List[str] = None,
                                       **kwargs):
        param = self._get_service_param(message_key, "request", messages, temperature, max_tokens, stop, **kwargs)
        query_data = self._build_request_data(param)
        return query_data

    def _post_chat_query_request(self,
                                 messages: List[Dict[str, str]],
                                 temperature: float = 0.0,
                                 max_tokens: int = None,
                                 stop: List[str] = None,
                                 **kwargs):
        message_key = self._gen_message_key()
        post_data = self._build_chat_query_request_data(message_key,
                                                        messages,
                                                        model_name=self.model_name,
                                                        temperature=temperature,
                                                        max_tokens=max_tokens,
                                                        stop=stop,
                                                        **kwargs)
        response = self.http_provider.sync_call(post_data, endpoint="commonQuery/queryData")
        return message_key, response

    def _valid_chat_result(self, body):
        if "data" not in body or not body["data"]:
            return False
        if "values" not in body["data"] or not body["data"]["values"]:
            return False
        if "response" not in body["data"]["values"] and "data" not in body["data"]["values"]:
            return False
        return True

    def _build_chat_pull_request_data(self, message_key):
        param = self._get_service_param(message_key, "pull")

        pull_data = self._build_request_data(param)
        return pull_data

    def _pull_chat_result(self, message_key, response: Dict[str, Any], timeout):
        if self.model_name.startswith("claude"):
            if self._valid_chat_result(response):
                x = response["data"]["values"]["data"]
                ast_str = ast.literal_eval("'" + x + "'")
                result = html.unescape(ast_str)
                data = json.loads(result)
                return data
            else:
                raise LLMResponseError(
                    f"Invalid response from Ant API, response: {response}",
                    self.model_name or "unknown"
                )

        post_data = self._build_chat_pull_request_data(message_key)
        url = 'commonQuery/queryData'
        headers = {
            'Content-Type': 'application/json'
        }

        # Start polling until valid result or timeout
        start_time = time.time()
        elapsed_time = 0

        while elapsed_time < timeout:
            response = self.http_provider.sync_call(post_data, endpoint=url, headers=headers)

            logger.debug(f"Poll attempt at {elapsed_time}s, response: {response}")

            # Check if valid result is received
            if self._valid_chat_result(response):
                x = response["data"]["values"]["response"]
                ast_str = ast.literal_eval("'" + x + "'")
                result = html.unescape(ast_str)
                data = json.loads(result)
                return data
            elif (not response.get("success")) or ("data" in response and response["data"]):
                err_code = response.get("data", {}).get("errorCode", "")
                err_msg = response.get("data", {}).get("errorMessage", "")
                if err_code or err_msg:
                    raise LLMResponseError(
                        f"Request failed: {response}",
                        self.model_name or "unknown"
                    )

            # If no result, wait 1 second and query again
            time.sleep(1)
            elapsed_time = time.time() - start_time
            logger.debug(f"Polling... Elapsed time: {elapsed_time:.1f}s")

        # Timeout handling
        raise LLMResponseError(
            f"Timeout after {timeout} seconds waiting for response from Ant API",
            self.model_name or "unknown"
        )

    async def _async_pull_chat_result(self, message_key, response: Dict[str, Any], timeout):
        if self.model_name.startswith("claude"):
            if self._valid_chat_result(response):
                x = response["data"]["values"]["data"]
                ast_str = ast.literal_eval("'" + x + "'")
                result = html.unescape(ast_str)
                data = json.loads(result)
                return data
            elif (not response.get("success")) or ("data" in response and response["data"]):
                err_code = response.get("data", {}).get("errorCode", "")
                err_msg = response.get("data", {}).get("errorMessage", "")
                if err_code or err_msg:
                    raise LLMResponseError(
                        f"Request failed: {response}",
                        self.model_name or "unknown"
                    )

        post_data = self._build_chat_pull_request_data(message_key)
        url = 'commonQuery/queryData'
        headers = {
            'Content-Type': 'application/json'
        }

        # Start polling until valid result or timeout
        start_time = time.time()
        elapsed_time = 0

        while elapsed_time < timeout:
            response = await self.http_provider.async_call(post_data, endpoint=url, headers=headers)

            logger.debug(f"Poll attempt at {elapsed_time}s, response: {response}")

            # Check if valid result is received
            if self._valid_chat_result(response):
                x = response["data"]["values"]["response"]
                ast_str = ast.literal_eval("'" + x + "'")
                result = html.unescape(ast_str)
                data = json.loads(result)
                return data
            elif (not response.get("success")) or ("data" in response and response["data"]):
                err_code = response.get("data", {}).get("errorCode", "")
                err_msg = response.get("data", {}).get("errorMessage", "")
                if err_code or err_msg:
                    raise LLMResponseError(
                        f"Request failed: {response}",
                        self.model_name or "unknown"
                    )

            # If no result, wait 1 second and query again
            await asyncio.sleep(1)
            elapsed_time = time.time() - start_time
            logger.debug(f"Polling... Elapsed time: {elapsed_time:.1f}s")

        # Timeout handling
        raise LLMResponseError(
            f"Timeout after {timeout} seconds waiting for response from Ant API",
            self.model_name or "unknown"
        )

    def _convert_completion_message(self, message: Dict[str, Any], is_finished: bool = False) -> ModelResponse:
        """Convert Ant completion message to OpenAI format.

        Args:
            message: Ant completion message.

        Returns:
            OpenAI format message.
        """
        # Generate unique ID
        response_id = f"ant-{hash(str(message)) & 0xffffffff:08x}"

        # Get content
        content = message.get("completion", "")

        # Create message object
        message_dict = {
            "role": "assistant",
            "content": content,
            "is_chunk": True
        }

        # Keep original contextId and sessionId
        if "contextId" in message:
            message_dict["contextId"] = message["contextId"]
        if "sessionId" in message:
            message_dict["sessionId"] = message["sessionId"]

        usage = {
            "completion_tokens": message.get("completionToken", 0),
            "prompt_tokens": message.get("promptTokens", 0),
            "total_tokens": message.get("completionToken", 0) + message.get("promptTokens", 0)
        }

        # process tool calls
        tool_calls = message.get("toolCalls", [])
        for tool_call in tool_calls:
            index = tool_call.get("index", 0)
            name = tool_call.get("function", {}).get("name")
            arguments = tool_call.get("function", {}).get("arguments")
            if index >= len(self.stream_tool_buffer):
                self.stream_tool_buffer.append({
                    "id": tool_call.get("id"),
                    "type": "function",
                    "function": {
                        "name": name,
                        "arguments": arguments
                    }
                })
            else:
                self.stream_tool_buffer[index]["function"]["arguments"] += arguments

        if is_finished and self.stream_tool_buffer:
            message_dict["tool_calls"] = self.stream_tool_buffer.copy()
            processed_tool_calls = []
            for tool_call in self.stream_tool_buffer:
                processed_tool_calls.append(ToolCall.from_dict(tool_call))
            tool_resp = ModelResponse(
                id=response_id,
                model=self.model_name or "ant",
                content=content,
                tool_calls=processed_tool_calls,
                usage=usage,
                raw_response=message,
                message=message_dict
            )
            self.stream_tool_buffer = []
            return tool_resp

        # Build and return ModelResponse object directly
        return ModelResponse(
            id=response_id,
            model=self.model_name or "ant",
            content=content,
            tool_calls=None,  # TODO: add tool calls
            usage=usage,
            raw_response=message,
            message=message_dict
        )

    def preprocess_stream_call_message(self, messages: List[Dict[str, str]], ext_params: Dict[str, Any]) -> Dict[
        str, str]:
        """Preprocess messages, use Ant format directly.

        Args:
            messages: Ant format message list.

        Returns:
            Processed message list.
        """
        param = {
            "messages": messages,
            "sessionId": "TkQUldjzOgYSKyTrpor3TA==",
            "model": self.model_name,
            "needMemory": False,
            "stream": True,
            "contextId": "contextId_34555fd2d246447fa55a1a259445a427",
            "platform": "AWorld"
        }
        for k in ext_params.keys():
            if k not in param:
                param[k] = ext_params[k]
        return param

    def postprocess_response(self, response: Any) -> ModelResponse:
        """Process Ant response.

        Args:
            response: Ant response object.

        Returns:
            ModelResponse object.

        Raises:
            LLMResponseError: When LLM response error occurs.
        """
        if ((not isinstance(response, dict) and (not hasattr(response, 'choices') or not response.choices))
                or (isinstance(response, dict) and not response.get("choices"))):
            error_msg = ""
            if hasattr(response, 'error') and response.error and isinstance(response.error, dict):
                error_msg = response.error.get('message', '')
            elif hasattr(response, 'msg'):
                error_msg = response.msg

            raise LLMResponseError(
                error_msg if error_msg else "Unknown error",
                self.model_name or "unknown",
                response
            )

        return ModelResponse.from_openai_response(response)

    def postprocess_stream_response(self, chunk: Any) -> ModelResponse:
        """Process Ant stream response chunk.

        Args:
            chunk: Ant response chunk.

        Returns:
            ModelResponse object.

        Raises:
            LLMResponseError: When LLM response error occurs.
        """
        # Check if chunk contains error
        if hasattr(chunk, 'error') or (isinstance(chunk, dict) and chunk.get('error')):
            error_msg = chunk.error if hasattr(chunk, 'error') else chunk.get('error', 'Unknown error')
            raise LLMResponseError(
                error_msg,
                self.model_name or "unknown",
                chunk
            )

        if isinstance(chunk, dict) and ('completion' in chunk):
            return self._convert_completion_message(chunk)

        # If chunk is already in OpenAI format, use standard processing method
        return ModelResponse.from_openai_stream_chunk(chunk)

    def completion(self,
                   messages: List[Dict[str, str]],
                   temperature: float = 0.0,
                   max_tokens: int = None,
                   stop: List[str] = None,
                   **kwargs) -> ModelResponse:
        """Synchronously call Ant to generate response.

        Args:
            messages: Message list.
            temperature: Temperature parameter.
            max_tokens: Maximum number of tokens to generate.
            stop: List of stop sequences.
            **kwargs: Other parameters.

        Returns:
            ModelResponse object.

        Raises:
            LLMResponseError: When LLM response error occurs.
        """
        if not self.provider:
            raise RuntimeError(
                "Sync provider not initialized. Make sure 'sync_enabled' parameter is set to True in initialization.")

        try:
            start_time = time.time()
            message_key, response = self._post_chat_query_request(messages, temperature, max_tokens, stop, **kwargs)
            timeout = kwargs.get("response_timeout", self.kwargs.get("timeout", 180))
            result = self._pull_chat_result(message_key, response, timeout)
            logger.info(f"completion cost time: {time.time() - start_time}s.")

            resp = self.postprocess_response(result)
            usage_process(resp.usage)
            return resp
        except Exception as e:
            if isinstance(e, LLMResponseError):
                raise e
            logger.warn(f"Error in Ant completion: {e}")
            raise LLMResponseError(str(e), kwargs.get("model_name", self.model_name or "unknown"))

    async def acompletion(self,
                          messages: List[Dict[str, str]],
                          temperature: float = 0.0,
                          max_tokens: int = None,
                          stop: List[str] = None,
                          **kwargs) -> ModelResponse:
        """Asynchronously call Ant to generate response.

        Args:
            messages: Message list.
            temperature: Temperature parameter.
            max_tokens: Maximum number of tokens to generate.
            stop: List of stop sequences.
            **kwargs: Other parameters.

        Returns:
            ModelResponse object.

        Raises:
            LLMResponseError: When LLM response error occurs.
        """
        if not self.async_provider:
            self._init_async_provider()

        start_time = time.time()
        try:
            message_key, response = self._post_chat_query_request(messages, temperature, max_tokens, stop, **kwargs)
            timeout = kwargs.get("response_timeout", self.kwargs.get("timeout", 180))
            result = await self._async_pull_chat_result(message_key, response, timeout)
            logger.info(f"completion cost time: {time.time() - start_time}s.")

            resp = self.postprocess_response(result)
            usage_process(resp.usage)
            return resp

        except Exception as e:
            if isinstance(e, LLMResponseError):
                raise e
            logger.warn(f"Error in async Ant completion: {e}")
            raise LLMResponseError(str(e), kwargs.get("model_name", self.model_name or "unknown"))

    def stream_completion(self,
                          messages: List[Dict[str, str]],
                          temperature: float = 0.0,
                          max_tokens: int = None,
                          stop: List[str] = None,
                          **kwargs) -> Generator[ModelResponse, None, None]:
        """Synchronously call Ant to generate streaming response.

        Args:
            messages: Message list.
            temperature: Temperature parameter.
            max_tokens: Maximum number of tokens to generate.
            stop: List of stop sequences.
            **kwargs: Other parameters.

        Returns:
            Generator yielding ModelResponse chunks.

        Raises:
            LLMResponseError: When LLM response error occurs.
        """
        if not self.provider:
            raise RuntimeError(
                "Sync provider not initialized. Make sure 'sync_enabled' parameter is set to True in initialization.")

        start_time = time.time()
        # Generate message_key
        timestamp = int(time.time())
        self.message_key = f"llm_call_{timestamp}"
        message_key_literal = self.message_key  # Ensure it's a direct string literal
        self.aes_key = kwargs.get("aes_key", self.aes_key)

        # Add streaming parameter
        kwargs["stream"] = True
        processed_messages = self.preprocess_stream_call_message(messages,
                                                                 self._build_openai_params(temperature, max_tokens,
                                                                                           stop, **kwargs))
        if not processed_messages:
            raise LLMResponseError("Failed to get post data", self.model_name or "unknown")

        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

        try:
            # Send request
            # response = self.http_provider.sync_call(processed_messages[0], endpoint="commonQuery/queryData")
            headers = {
                "Content-Type": "application/json",
                "X_ACCESS_KEY": self.stream_api_key
            }
            response_stream = self.http_provider.sync_stream_call(processed_messages, endpoint="chat/completions",
                                                                  headers=headers)
            if response_stream:
                for chunk in response_stream:
                    if not chunk:
                        continue

                    # Process special markers
                    if isinstance(chunk, dict) and "status" in chunk:
                        if chunk["status"] == "done":
                            # Stream completion marker, can choose to end
                            logger.info("Received [DONE] marker, stream completed")
                            yield self._convert_completion_message(chunk, is_finished=True)
                            yield ModelResponse.from_special_marker("done", self.model_name, chunk)
                            break
                        elif chunk["status"] == "revoke":
                            # Revoke marker, need to notify the frontend to revoke the displayed content
                            logger.info("Received [REVOKE] marker, content should be revoked")
                            yield ModelResponse.from_special_marker("revoke", self.model_name, chunk)
                            continue
                        elif chunk["status"] == "fail":
                            # Fail marker
                            logger.error("Received [FAIL] marker, request failed")
                            raise LLMResponseError("Request failed", self.model_name or "unknown")
                        elif chunk["status"] == "cancel":
                            # Request was cancelled
                            logger.warning("Received [CANCEL] marker, stream was cancelled")
                            raise LLMResponseError("Stream was cancelled", self.model_name or "unknown")
                        continue

                    # Process normal response chunks
                    resp = self.postprocess_stream_response(chunk)
                    self._accumulate_chunk_usage(usage, resp.usage)
                    yield resp
                usage_process(usage)

            logger.info(f"stream_completion cost time: {time.time() - start_time}s.")
        except Exception as e:
            if isinstance(e, LLMResponseError):
                raise e
            logger.error(f"Error in Ant stream completion: {e}")
            raise LLMResponseError(str(e), kwargs.get("model_name", self.model_name or "unknown"))

    async def astream_completion(self,
                                 messages: List[Dict[str, str]],
                                 temperature: float = 0.0,
                                 max_tokens: int = None,
                                 stop: List[str] = None,
                                 **kwargs) -> AsyncGenerator[ModelResponse, None]:
        """Asynchronously call Ant to generate streaming response.

        Args:
            messages: Message list.
            temperature: Temperature parameter.
            max_tokens: Maximum number of tokens to generate.
            stop: List of stop sequences.
            **kwargs: Other parameters.

        Returns:
            AsyncGenerator yielding ModelResponse chunks.

        Raises:
            LLMResponseError: When LLM response error occurs.
        """
        if not self.async_provider:
            self._init_async_provider()

        start_time = time.time()
        # Generate message_key
        timestamp = int(time.time())
        self.message_key = f"llm_call_{timestamp}"
        message_key_literal = self.message_key  # Ensure it's a direct string literal
        self.aes_key = kwargs.get("aes_key", self.aes_key)

        # Add streaming parameter
        kwargs["stream"] = True
        processed_messages = self.preprocess_stream_call_message(messages,
                                                                 self._build_openai_params(temperature, max_tokens,
                                                                                           stop, **kwargs))
        if not processed_messages:
            raise LLMResponseError("Failed to get post data", self.model_name or "unknown")

        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        try:
            headers = {
                "Content-Type": "application/json",
                "X_ACCESS_KEY": self.stream_api_key
            }
            logger.info(f"astream_completion request data: {processed_messages}")

            async for chunk in self.http_provider.async_stream_call(processed_messages, endpoint="chat/completions",
                                                                    headers=headers):
                if not chunk:
                    continue

                # Process special markers
                if isinstance(chunk, dict) and "status" in chunk:
                    if chunk["status"] == "done":
                        # Stream completion marker, can choose to end
                        logger.info("Received [DONE] marker, stream completed")
                        yield ModelResponse.from_special_marker("done", self.model_name, chunk)
                        break
                    elif chunk["status"] == "revoke":
                        # Revoke marker, need to notify the frontend to revoke the displayed content
                        logger.info("Received [REVOKE] marker, content should be revoked")
                        yield ModelResponse.from_special_marker("revoke", self.model_name, chunk)
                        continue
                    elif chunk["status"] == "fail":
                        # Fail marker
                        logger.error("Received [FAIL] marker, request failed")
                        raise LLMResponseError("Request failed", self.model_name or "unknown")
                    elif chunk["status"] == "cancel":
                        # Request was cancelled
                        logger.warning("Received [CANCEL] marker, stream was cancelled")
                        raise LLMResponseError("Stream was cancelled", self.model_name or "unknown")
                    continue

                # Process normal response chunks
                resp = self.postprocess_stream_response(chunk)
                self._accumulate_chunk_usage(usage, resp.usage)
                yield resp
            usage_process(usage)

            logger.info(f"astream_completion cost time: {time.time() - start_time}s.")
        except Exception as e:
            if isinstance(e, LLMResponseError):
                raise e
            logger.warn(f"Error in async Ant stream completion: {e}")
            raise LLMResponseError(str(e), kwargs.get("model_name", self.model_name or "unknown"))
