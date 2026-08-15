import abc
from collections import Counter
from typing import (
    Any,
    List,
    Dict,
    Generator,
    AsyncGenerator,
)

from aworld.models.model_response import ModelResponse


class LLMProviderBase(abc.ABC):
    """Base class for large language model providers, defines unified interface."""

    def __init__(self,
                 api_key: str = None,
                 base_url: str = None,
                 model_name: str = None,
                 sync_enabled: bool = None,
                 async_enabled: bool = None,
                 **kwargs):
        """Initialize provider.

        Args:
            api_key: API key.
            base_url: Service URL.
            model_name: Model name.
            **kwargs: Other parameters.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.kwargs = kwargs
        # Determine whether to initialize sync and async providers
        self.need_sync = sync_enabled if sync_enabled is not None else async_enabled is not True
        self.need_async = async_enabled if async_enabled is not None else sync_enabled is not True

        # Initialize providers based on flags
        self.provider = self._init_provider() if self.need_sync else None
        self.async_provider = self._init_async_provider() if self.need_async else None
        self.stream_tool_buffer=[]

    @abc.abstractmethod
    def _init_provider(self):
        """Initialize specific provider instance, to be implemented by subclasses.
        Returns:
            Provider instance.
        """

    def _init_async_provider(self):
        """Initialize async provider instance. Optional for subclasses that don't need async support.
        Only called if async provider is needed.

        Returns:
            Async provider instance.
        """
        return None

    @classmethod
    def supported_models(cls) -> list[str]:
        return []

    def preprocess_messages(self, messages: List[Dict[str, str]]) -> Any:
        """Preprocess messages, convert OpenAI format messages to specific provider required format.

        Args:
            messages: OpenAI format message list [{"role": "system", "content": "..."}, ...].

        Returns:
            Converted messages, format determined by specific provider.
        """
        return messages

    @abc.abstractmethod
    def postprocess_response(self, response: Any) -> ModelResponse:
        """Post-process response, convert provider response to unified ModelResponse.

        Args:
            response: Original response from provider.

        Returns:
            ModelResponse: Unified format response object.
            
        Raises:
            LLMResponseError: When LLM response error occurs.
        """

    def postprocess_stream_response(self, chunk: Any) -> ModelResponse:
        """Post-process streaming response chunk, convert provider chunk to unified ModelResponse.

        Args:
            chunk: Original response chunk from provider.
            
        Returns:
            ModelResponse: Unified format response object for the chunk.
            
        Raises:
            LLMResponseError: When LLM response error occurs.
        """

    async def acompletion(self,
                          messages: List[Dict[str, str]],
                          temperature: float = 0.0,
                          max_tokens: int = None,
                          stop: List[str] = None,
                          **kwargs) -> ModelResponse:
        """Asynchronously call model to generate response.
        
        Args:
            messages: Message list, format is [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}].
            temperature: Temperature parameter.
            max_tokens: Maximum number of tokens to generate.
            stop: List of stop sequences.
            **kwargs: Other parameters.

        Returns:
            ModelResponse: Unified model response object.
            
        Raises:
            LLMResponseError: When LLM response error occurs.
            RuntimeError: When async provider is not initialized.
        """
        if not self.async_provider:
            raise RuntimeError(
                "Async provider not initialized. Make sure 'async_enabled' parameter is set to True in initialization.")


    @abc.abstractmethod
    def completion(self,
                   messages: List[Dict[str, str]],
                   temperature: float = 0.0,
                   max_tokens: int = None,
                   stop: List[str] = None,
                   **kwargs) -> ModelResponse:
        """Synchronously call model to generate response.

        Args:
            messages: Message list, format is [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}].
            temperature: Temperature parameter.
            max_tokens: Maximum number of tokens to generate.
            stop: List of stop sequences.
            **kwargs: Other parameters.

        Returns:
            ModelResponse: Unified model response object.
            
        Raises:
            LLMResponseError: When LLM response error occurs.
            RuntimeError: When sync provider is not initialized.
        """

    def stream_completion(self,
                          messages: List[Dict[str, str]],
                          temperature: float = 0.0,
                          max_tokens: int = None,
                          stop: List[str] = None,
                          **kwargs) -> Generator[ModelResponse, None, None]:
        """Synchronously call model to generate streaming response.

        Args:
            messages: Message list, format is [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}].
            temperature: Temperature parameter.
            max_tokens: Maximum number of tokens to generate.
            stop: List of stop sequences.
            **kwargs: Other parameters.

        Returns:
            Generator yielding ModelResponse chunks.
            
        Raises:
            LLMResponseError: When LLM response error occurs.
            RuntimeError: When sync provider is not initialized.
        """

    async def astream_completion(self,
                                 messages: List[Dict[str, str]],
                                 temperature: float = 0.0,
                                 max_tokens: int = None,
                                 stop: List[str] = None,
                                 **kwargs) -> AsyncGenerator[ModelResponse, None]:
        """Asynchronously call model to generate streaming response.

        Args:
            messages: Message list, format is [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}].
            temperature: Temperature parameter.
            max_tokens: Maximum number of tokens to generate.
            stop: List of stop sequences.
            **kwargs: Other parameters.

        Returns:
            AsyncGenerator yielding ModelResponse chunks.
            
        Raises:
            LLMResponseError: When LLM response error occurs.
            RuntimeError: When async provider is not initialized.
        """

    def _accumulate_chunk_usage(self, usage: Dict[str, int], chunk_usage: Dict[str, int]):
        """Accumulate usage statistics from chunk into the main usage dictionary.

        Args:
            usage: Dictionary to accumulate usage into (will be modified)
            chunk_usage: Usage statistics from the current chunk
        """
        if not chunk_usage:
            return

        usage.update(dict(Counter(usage) + Counter(chunk_usage)))

    def speech_to_text(self, audio_file, language, prompt, **kwargs) -> ModelResponse:
        pass

    async def aspeech_to_text(self, audio_file, language, prompt, **kwargs) -> ModelResponse:
        pass

