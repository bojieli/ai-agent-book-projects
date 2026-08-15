import traceback
from typing import (
    List,
    Dict,
    Union,
    Generator,
    AsyncGenerator,
)
from aworld.config import ConfigDict, ModelConfig
from aworld.config.conf import AgentConfig, ClientType
from aworld.logs.util import logger

from aworld.core.llm_provider import LLMProviderBase
from aworld.models.openai_provider import OpenAIProvider, AzureOpenAIProvider
from aworld.models.anthropic_provider import AnthropicProvider
from aworld.models.ant_provider import AntProvider
from aworld.models.model_response import ModelResponse

# Predefined model names for common providers
MODEL_NAMES = {
    "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-sonnet-20240620", "claude-3-opus-20240229"],
    "openai": ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "o3-mini", "gpt-4o-mini"],
    "azure_openai": ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-35-turbo"],
}

# Endpoint patterns for identifying providers
ENDPOINT_PATTERNS = {
    "openai": ["api.openai.com"],
    "anthropic": ["api.anthropic.com", "claude-api"],
    "azure_openai": ["openai.azure.com"],
    "ant": ["zdfmng.alipay.com"],
}

# Provider class mapping
PROVIDER_CLASSES = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "azure_openai": AzureOpenAIProvider,
    "ant": AntProvider,
}


class LLMModel:
    """Unified large model interface, encapsulates different model implementations, provides a unified completion method.
    """

    def __init__(self, conf: Union[ConfigDict, AgentConfig, ModelConfig] = None, custom_provider: LLMProviderBase = None, **kwargs):
        """Initialize unified model interface.

        Args:
            conf: Agent configuration, if provided, create model based on configuration.
            custom_provider: Custom LLMProviderBase instance, if provided, use it directly.
            **kwargs: Other parameters, may include:
                - base_url: Specify model endpoint.
                - api_key: API key.
                - model_name: Model name.
                - temperature: Temperature parameter.
        """

        # If custom_provider instance is provided, use it directly
        if custom_provider is not None:
            if not isinstance(custom_provider, LLMProviderBase):
                raise TypeError(
                    "custom_provider must be an instance of LLMProviderBase")
            self.provider_name = "custom"
            self.provider = custom_provider
            return
        conf = conf.llm_config if type(conf).__name__ == 'AgentConfig' else conf
        # Get basic parameters
        base_url = kwargs.get("base_url") or (
            conf.llm_base_url if conf else None)
        model_name = kwargs.get("model_name") or (
            conf.llm_model_name if conf else None)
        llm_provider = conf.llm_provider if conf_contains_key(
            conf, "llm_provider") else None

        # Get API key from configuration (if any)
        if conf and conf.llm_api_key:
            kwargs["api_key"] = conf.llm_api_key

        # Identify provider
        self.provider_name = self._identify_provider(
            llm_provider, base_url, model_name)

        # Fill basic parameters
        kwargs['base_url'] = base_url
        kwargs['model_name'] = model_name

        # Fill parameters for llm provider
        kwargs['sync_enabled'] = conf.llm_sync_enabled if conf_contains_key(
            conf, "llm_sync_enabled") else True
        kwargs['async_enabled'] = conf.llm_async_enabled if conf_contains_key(
            conf, "llm_async_enabled") else True
        kwargs['client_type'] = conf.llm_client_type if conf_contains_key(
            conf, "llm_client_type") else ClientType.SDK

        kwargs.update(self._transfer_conf_to_args(conf))

        # Create model provider based on provider_name
        self._create_provider(**kwargs)

    def _transfer_conf_to_args(self, conf: Union[ConfigDict, AgentConfig] = None) -> dict:
        """
        Transfer parameters from conf to args

        Args:
            conf: config object
        """
        if not conf:
            return {}

        # Get all parameters from conf
        if type(conf).__name__ == 'AgentConfig':
            conf_dict = conf.model_dump()
        elif type(conf).__name__ == 'ModelConfig':
            conf_dict = conf.model_dump()
        else:  # ConfigDict
            conf_dict = conf

        ignored_keys = ["llm_provider", "llm_base_url", "llm_model_name", "llm_api_key", "llm_sync_enabled",
                        "llm_async_enabled", "llm_client_type"]
        args = {}
        # Filter out used parameters and add remaining parameters to args
        for key, value in conf_dict.items():
            if key not in ignored_keys and value is not None:
                args[key] = value

        return args

    def _identify_provider(self, provider: str = None, base_url: str = None, model_name: str = None) -> str:
        """Identify LLM provider.

        Identification logic:
        1. If provider is specified and doesn't need to be overridden, use the specified provider.
        2. If base_url is provided, try to identify provider based on base_url.
        3. If model_name is provided, try to identify provider based on model_name.
        4. If none can be identified, default to "openai".

        Args:
            provider: Specified provider.
            base_url: Service URL.
            model_name: Model name.

        Returns:
            str: Identified provider.
        """
        # Default provider
        identified_provider = "openai"

        # Identify provider based on base_url
        if base_url:
            for p, patterns in ENDPOINT_PATTERNS.items():
                if any(pattern in base_url for pattern in patterns):
                    identified_provider = p
                    logger.info(
                        f"Identified provider: {identified_provider} based on base_url: {base_url}")
                    return identified_provider

        # Identify provider based on model_name
        if model_name and not base_url:
            for p, models in MODEL_NAMES.items():
                if model_name in models or any(model_name.startswith(model) for model in models):
                    identified_provider = p
                    logger.info(
                        f"Identified provider: {identified_provider} based on model_name: {model_name}")
                    break

        if provider and provider in PROVIDER_CLASSES and identified_provider and identified_provider != provider:
            logger.warning(
                f"Provider mismatch: {provider} != {identified_provider}, using {provider} as provider")
            identified_provider = provider

        return identified_provider

    def _create_provider(self, **kwargs):
        """Return the corresponding provider instance based on provider.

        Args:
            **kwargs: Parameters, may include:
                - base_url: Model endpoint.
                - api_key: API key.
                - model_name: Model name.
                - temperature: Temperature parameter.
                - timeout: Timeout.
                - max_retries: Maximum number of retries.
        """
        self.provider = PROVIDER_CLASSES[self.provider_name](**kwargs)

    @classmethod
    def supported_providers(cls) -> list[str]:
        return list(PROVIDER_CLASSES.keys())

    def supported_models(self) -> list[str]:
        """Get supported models for the current provider.
        Returns:
            list: Supported models.
        """
        return self.provider.supported_models() if self.provider else []

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
        """
        # Call provider's acompletion method directly
        try:
            return await self.provider.acompletion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                **kwargs
            )
        except AttributeError as e:
            logger.error(f"Provider {self.provider_name} does not support acompletion: {e}")
            raise NotImplementedError(f"Provider {self.provider_name} does not support async completion") from e
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Network error calling {self.provider_name}: {e}")
            raise ConnectionError(f"Failed to connect to {self.provider_name} API") from e
        except Exception as e:
            logger.error(f"Unexpected error calling model {self.provider_name}: {traceback.format_exc()}")
            logger.debug(f"Failed request details - messages: {messages}, kwargs: {kwargs}")
            raise RuntimeError(f"Model call failed: {str(e)}") from e

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
        """
        # Call provider's completion method directly
        return self.provider.completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
            **kwargs
        )

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
        """
        # Call provider's stream_completion method directly
        return self.provider.stream_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
            **kwargs
        )

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
            **kwargs: Other parameters, may include:
                - base_url: Specify model endpoint.
                - api_key: API key.
                - model_name: Model name.

        Returns:
            AsyncGenerator yielding ModelResponse chunks.
        """
        # Call provider's astream_completion method directly
        async for chunk in self.provider.astream_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                **kwargs
        ):
            yield chunk

    def speech_to_text(self,
                       audio_file: str,
                       language: str = None,
                       prompt: str = None,
                       **kwargs) -> ModelResponse:
        """Convert speech to text.

        Args:
            audio_file: Path to audio file or file object.
            language: Audio language, optional.
            prompt: Transcription prompt, optional.
            **kwargs: Other parameters.

        Returns:
            ModelResponse: Unified model response object, with content field containing the transcription result.

        Raises:
            LLMResponseError: When LLM response error occurs.
            NotImplementedError: When provider does not support speech to text conversion.
        """
        return self.provider.speech_to_text(
            audio_file=audio_file,
            language=language,
            prompt=prompt,
            **kwargs
        )

    async def aspeech_to_text(self,
                              audio_file: str,
                              language: str = None,
                              prompt: str = None,
                              **kwargs) -> ModelResponse:
        """Asynchronously convert speech to text.

        Args:
            audio_file: Path to audio file or file object.
            language: Audio language, optional.
            prompt: Transcription prompt, optional.
            **kwargs: Other parameters.

        Returns:
            ModelResponse: Unified model response object, with content field containing the transcription result.

        Raises:
            LLMResponseError: When LLM response error occurs.
            NotImplementedError: When provider does not support speech to text conversion.
        """
        return await self.provider.aspeech_to_text(
            audio_file=audio_file,
            language=language,
            prompt=prompt,
            **kwargs
        )


def register_llm_provider(provider: str, provider_class: type):
    """Register a custom LLM provider.

    Args:
        provider: Provider name.
        provider_class: Provider class, must inherit from LLMProviderBase.
    """
    if not issubclass(provider_class, LLMProviderBase):
        raise TypeError("provider_class must be a subclass of LLMProviderBase")
    PROVIDER_CLASSES[provider] = provider_class


def conf_contains_key(conf: Union[ConfigDict, AgentConfig, ModelConfig], key: str) -> bool:
    """Check if configuration contains a specific key.
    
    Args:
        conf: Configuration object (ConfigDict or AgentConfig).
        key: Key to check for existence.
        
    Returns:
        bool: True if the key exists in the configuration, False otherwise.
        
    Examples:
        >>> conf = AgentConfig(llm_provider="openai")
        >>> conf_contains_key(conf, "llm_provider")
        True
        >>> conf_contains_key(conf, "nonexistent_key")
        False
    """
    if not conf:
        return False
    if type(conf).__name__ == 'AgentConfig':
        return hasattr(conf, key)
    else:
        return key in conf


def get_llm_model(conf: Union[ConfigDict, AgentConfig] = None,
                  custom_provider: LLMProviderBase = None,
                  **kwargs) -> Union[LLMModel, 'ChatOpenAI']:
    """Get a unified LLM model instance.

    Args:
        conf: Agent configuration, if provided, create model based on configuration.
        custom_provider: Custom LLMProviderBase instance, if provided, use it directly.
        **kwargs: Other parameters, may include:
            - base_url: Specify model endpoint.
            - api_key: API key.
            - model_name: Model name.
            - temperature: Temperature parameter.

    Returns:
        Unified model interface.
    """
    # Create and return LLMModel instance directly
    llm_provider = conf.llm_provider if conf_contains_key(
        conf, "llm_provider") else None

    if (llm_provider == "chatopenai"):
        from langchain_openai import ChatOpenAI
        conf = conf.llm_config if type(conf).__name__ == 'AgentConfig' else conf
        base_url = kwargs.get("base_url") or (
            conf.llm_base_url if conf_contains_key(conf, "llm_base_url") else None)
        model_name = kwargs.get("model_name") or (
            conf.llm_model_name if conf_contains_key(conf, "llm_model_name") else None)
        api_key = kwargs.get("api_key") or (
            conf.llm_api_key if conf_contains_key(conf, "llm_api_key") else None)

        return ChatOpenAI(
            model=model_name,
            temperature=kwargs.get("temperature", conf.llm_temperature if conf_contains_key(
                conf, "llm_temperature") else 0.0),
            base_url=base_url,
            api_key=api_key,
        )

    return LLMModel(conf=conf, custom_provider=custom_provider, **kwargs)


def call_llm_model(
        llm_model: LLMModel,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = None,
        stop: List[str] = None,
        stream: bool = False,
        **kwargs
) -> Union[ModelResponse, Generator[ModelResponse, None, None]]:
    """Convenience function to call LLM model.

    Args:
        llm_model: LLM model instance.
        messages: Message list.
        temperature: Temperature parameter.
        max_tokens: Maximum number of tokens to generate.
        stop: List of stop sequences.
        stream: Whether to return a streaming response.
        **kwargs: Other parameters.

    Returns:
        Model response or response generator.
    """
    if stream:
        return llm_model.stream_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
            **kwargs
        )
    else:
        return llm_model.completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
            **kwargs
        )


async def acall_llm_model(
        llm_model: LLMModel,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = None,
        stop: List[str] = None,
        stream: bool = False,
        **kwargs
) -> ModelResponse:
    """Convenience function to asynchronously call LLM model.

    Args:
        llm_model: LLM model instance.
        messages: Message list.
        temperature: Temperature parameter.
        max_tokens: Maximum number of tokens to generate.
        stop: List of stop sequences.
        stream: Whether to return a streaming response.
        **kwargs: Other parameters.

    Returns:
        Model response or response generator.
    """
    return await llm_model.acompletion(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stop=stop,
        **kwargs
    )


async def acall_llm_model_stream(
        llm_model: LLMModel,
        messages: List[Dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = None,
        stop: List[str] = None,
        **kwargs
) -> AsyncGenerator[ModelResponse, None]:
    # Fix: Cannot await an async generator, directly iterate over it
    async for chunk in llm_model.astream_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
            **kwargs
    ):
        yield chunk


def speech_to_text(
        llm_model: LLMModel,
        audio_file: str,
        language: str = None,
        prompt: str = None,
        **kwargs
) -> ModelResponse:
    """Convenience function to convert speech to text.

    Args:
        llm_model: LLM model instance.
        audio_file: Path to audio file or file object.
        language: Audio language, optional.
        prompt: Transcription prompt, optional.
        **kwargs: Other parameters.

    Returns:
        ModelResponse: Unified model response object, with content field containing the transcription result.
    """
    if llm_model.provider_name != "openai":
        raise NotImplementedError(
            f"Speech-to-text functionality is currently only supported for OpenAI compatible provider, current provider: {llm_model.provider_name}")

    return llm_model.speech_to_text(
        audio_file=audio_file,
        language=language,
        prompt=prompt,
        **kwargs
    )


async def aspeech_to_text(
        llm_model: LLMModel,
        audio_file: str,
        language: str = None,
        prompt: str = None,
        **kwargs
) -> ModelResponse:
    """Convenience function to asynchronously convert speech to text.

    Args:
        llm_model: LLM model instance.
        audio_file: Path to audio file or file object.
        language: Audio language, optional.
        prompt: Transcription prompt, optional.
        **kwargs: Other parameters.

    Returns:
        ModelResponse: Unified model response object, with content field containing the transcription result.
    """
    if llm_model.provider_name != "openai":
        raise NotImplementedError(
            f"Speech-to-text functionality is currently only supported for OpenAI compatible provider, current provider: {llm_model.provider_name}")

    return await llm_model.aspeech_to_text(
        audio_file=audio_file,
        language=language,
        prompt=prompt,
        **kwargs
    )
