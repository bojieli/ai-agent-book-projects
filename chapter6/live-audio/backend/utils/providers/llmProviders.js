const axios = require('axios');

function providerErrorMessage(error) {
  const data = error.response?.data;
  if (data && typeof data === 'object' && !data.readable) {
    return data.error?.message || data.message || error.message;
  }
  return error.response?.status
    ? `HTTP ${error.response.status}: ${error.response.statusText || error.message}`
    : error.message;
}

/**
 * Base LLM Provider class
 */
class BaseLLMProvider {
  constructor(config, apiKey) {
    this.config = config;
    this.apiKey = apiKey;
  }

  async createChatCompletion(messages, options = {}) {
    throw new Error('createChatCompletion method must be implemented by subclass');
  }

  /**
   * Prepare headers for API request
   * @returns {Object} Headers object
   */
  getHeaders() {
    return {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Prepare request payload
   * @param {Array} messages - Chat messages
   * @param {Object} options - Additional options
   * @returns {Object} Request payload
   */
  getRequestPayload(messages, options = {}) {
    return {
      model: this.config.model,
      messages: messages,
      stream: true,
      max_tokens: options.max_tokens || 4096,
      ...options
    };
  }
}

/**
 * OpenAI LLM Provider
 */
class OpenAILLMProvider extends BaseLLMProvider {
  async createChatCompletion(messages, options = {}) {
    try {
      const payload = this.getRequestPayload(messages, options);
      const headers = this.getHeaders();

      console.log('OpenAI LLM Request:', {
        model: payload.model,
        messagesCount: messages.length,
        stream: payload.stream
      });

      const response = await axios.post(
        this.config.apiUrl,
        payload,
        {
          headers: headers,
          cancelToken: options.cancelToken,
          responseType: 'stream'
        }
      );

      return {
        success: true,
        response: response,
        provider: 'openai'
      };

    } catch (error) {
      const message = providerErrorMessage(error);
      console.error('OpenAI LLM error:', message);
      return {
        success: false,
        error: message,
        provider: 'openai'
      };
    }
  }
}

/**
 * OpenRouter LLM Provider (supports both GPT-4o and Gemini)
 */
class OpenRouterLLMProvider extends BaseLLMProvider {
  getHeaders() {
    return {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': 'https://live-audio-chat.local',
      'X-Title': 'Live Audio Chat'
    };
  }

  async createChatCompletion(messages, options = {}) {
    try {
      const payload = this.getRequestPayload(messages, options);
      const headers = this.getHeaders();

      console.log('OpenRouter LLM Request:', {
        model: payload.model,
        messagesCount: messages.length,
        stream: payload.stream
      });

      const response = await axios.post(
        this.config.apiUrl,
        payload,
        {
          headers: headers,
          cancelToken: options.cancelToken,
          responseType: 'stream'
        }
      );

      return {
        success: true,
        response: response,
        provider: 'openrouter'
      };

    } catch (error) {
      const message = providerErrorMessage(error);
      console.error('OpenRouter LLM error:', message);
      return {
        success: false,
        error: message,
        provider: 'openrouter'
      };
    }
  }
}

/**
 * ARK (Doubao) LLM Provider
 */
class ARKLLMProvider extends BaseLLMProvider {
  getHeaders() {
    return {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json'
    };
  }

  getRequestPayload(messages, options = {}) {
    // ARK API format is similar to OpenAI but may have slight differences
    return {
      model: this.config.model,
      messages: messages,
      stream: true,
      max_tokens: options.max_tokens || 4096,
      temperature: options.temperature || 0.7,
      ...options
    };
  }

  async createChatCompletion(messages, options = {}) {
    try {
      const payload = this.getRequestPayload(messages, options);
      const headers = this.getHeaders();

      console.log('ARK (Doubao) LLM Request:', {
        model: payload.model,
        messagesCount: messages.length,
        stream: payload.stream
      });

      const response = await axios.post(
        this.config.apiUrl,
        payload,
        {
          headers: headers,
          cancelToken: options.cancelToken,
          responseType: 'stream'
        }
      );

      return {
        success: true,
        response: response,
        provider: 'ark'
      };

    } catch (error) {
      const message = providerErrorMessage(error);
      console.error('ARK (Doubao) LLM error:', message);
      return {
        success: false,
        error: message,
        provider: 'ark'
      };
    }
  }
}

/**
 * LLM Provider Factory
 */
class LLMProviderFactory {
  static createProvider(providerName, config, globalConfig) {
    const providerConfig = config.LLM_PROVIDERS[providerName];
    if (!providerConfig) {
      throw new Error(`LLM provider ${providerName} not found in configuration`);
    }

    // Get API key from global config
    const apiKey = globalConfig[providerConfig.apiKey];
    if (!apiKey) {
      throw new Error(`API key ${providerConfig.apiKey} not found in configuration`);
    }

    switch (providerName) {
      case 'openai':
        return new OpenAILLMProvider(providerConfig, apiKey);
      case 'openrouter':
      case 'openrouter-gpt':
      case 'openrouter-gemini':
        return new OpenRouterLLMProvider(providerConfig, apiKey);
      case 'ark':
        return new ARKLLMProvider(providerConfig, apiKey);
      default:
        throw new Error(`Unsupported LLM provider: ${providerName}`);
    }
  }
}

module.exports = {
  BaseLLMProvider,
  OpenAILLMProvider,
  OpenRouterLLMProvider,
  ARKLLMProvider,
  LLMProviderFactory
};
