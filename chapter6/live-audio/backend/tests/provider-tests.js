const assert = require('assert');
const fs = require('fs');
const path = require('path');

// Import provider factories
const { ASRProviderFactory } = require('../utils/providers/asrProviders');
const { LLMProviderFactory } = require('../utils/providers/llmProviders');

// Import services
const SpeechToTextService = require('../utils/speechToText');

// Mock configuration for testing
const testConfig = {
  // API Keys from environment variables
  OPENAI_API_KEY: process.env.OPENAI_API_KEY,
  OPENROUTER_API_KEY: process.env.OPENROUTER_API_KEY,
  ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
  ARK_API_KEY: process.env.ARK_API_KEY,
  SILICONFLOW_API_KEY: process.env.SILICONFLOW_API_KEY,
  
  // Provider configurations
  ASR_PROVIDERS: {
    openai: {
      apiUrl: 'https://api.openai.com/v1/audio/transcriptions',
      model: 'whisper-1',
      apiKey: 'OPENAI_API_KEY'
    },
    siliconflow: {
      apiUrl: 'https://api.siliconflow.cn/v1/audio/transcriptions',
      model: 'FunAudioLLM/SenseVoiceSmall',
      apiKey: 'SILICONFLOW_API_KEY'
    }
  },
  
  LLM_PROVIDERS: {
    openai: {
      apiUrl: 'https://api.openai.com/v1/chat/completions',
      model: 'gpt-5.6-luna',
      apiKey: 'OPENAI_API_KEY'
    },
    'openrouter-gpt': {
      apiUrl: 'https://openrouter.ai/api/v1/chat/completions',
      model: 'openai/gpt-5.6-luna',
      apiKey: 'OPENROUTER_API_KEY'
    },
    'openrouter-gemini': {
      apiUrl: 'https://openrouter.ai/api/v1/chat/completions',
      model: 'google/gemini-3.5-flash',
      apiKey: 'OPENROUTER_API_KEY'
    },
    ark: {
      apiUrl: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
      model: 'doubao-seed-1-6-flash-250615',
      apiKey: 'ARK_API_KEY'
    }
  },
  
  // Audio configuration
  AUDIO_SAMPLE_RATE: 16000,
  VISION_MAX_TOKENS: 4096
};

/**
 * Create a sample audio buffer for testing
 * This creates a simple sine wave audio buffer
 */
function createTestAudioBuffer(durationSeconds = 2, sampleRate = 16000) {
  const numSamples = durationSeconds * sampleRate;
  const buffer = Buffer.alloc(numSamples * 2); // 16-bit = 2 bytes per sample
  
  // Generate a simple sine wave at 440Hz
  const frequency = 440;
  for (let i = 0; i < numSamples; i++) {
    const sample = Math.sin(2 * Math.PI * frequency * i / sampleRate) * 0.5;
    const intSample = Math.round(sample * 32767);
    buffer.writeInt16LE(intSample, i * 2);
  }
  
  return buffer;
}

/**
 * Test suite for ASR providers
 */
describe('ASR Provider Tests', function() {
  this.timeout(60000); // 60 second timeout for API calls
  
  const asrProviders = ['openai', 'siliconflow'];
  
  asrProviders.forEach(providerName => {
    describe(`${providerName} ASR Provider`, function() {
      let provider;
      
      before(function() {
        // Skip test if API key is not available
        const apiKeyName = testConfig.ASR_PROVIDERS[providerName].apiKey;
        if (!testConfig[apiKeyName]) {
          this.skip();
        }
        
        try {
          provider = ASRProviderFactory.createProvider(providerName, testConfig, testConfig);
        } catch (error) {
          console.error(`Failed to create ${providerName} provider:`, error);
          this.skip();
        }
      });
      
      it('should be created successfully', function() {
        assert(provider, 'Provider should be created');
        assert(provider.config, 'Provider should have config');
        assert(provider.apiKey, 'Provider should have API key');
      });
      
      it('should transcribe test audio', async function() {
        const audioBuffer = createTestAudioBuffer(2); // 2 seconds of audio
        const tempDir = path.join(__dirname, '../temp');
        
        // Ensure temp directory exists
        if (!fs.existsSync(tempDir)) {
          fs.mkdirSync(tempDir, { recursive: true });
        }
        
        const result = await provider.transcribe(audioBuffer, tempDir);
        
        assert(result, 'Should return a result');
        assert(typeof result.success === 'boolean', 'Should have success field');
        assert(typeof result.text === 'string', 'Should have text field');
        assert(result.provider === providerName, 'Should have correct provider name');
        
        console.log(`${providerName} ASR Result:`, {
          success: result.success,
          text: result.text.substring(0, 100) + (result.text.length > 100 ? '...' : ''),
          language: result.language,
          provider: result.provider
        });
      });
    });
  });
  
  describe('SpeechToTextService Integration', function() {
    asrProviders.forEach(providerName => {
      it(`should work with ${providerName} provider`, async function() {
        // Skip test if API key is not available
        const apiKeyName = testConfig.ASR_PROVIDERS[providerName].apiKey;
        if (!testConfig[apiKeyName]) {
          this.skip();
        }
        
        // Override config for this test
        const originalConfig = require('../config');
        Object.assign(originalConfig, testConfig);
        originalConfig.ASR_PROVIDER = providerName;
        
        const sttService = new SpeechToTextService();
        const audioBuffer = createTestAudioBuffer(2);
        
        const result = await sttService.transcribeAudio(audioBuffer);
        
        assert(result, 'Should return a result');
        assert(typeof result.success === 'boolean', 'Should have success field');
        assert(typeof result.text === 'string', 'Should have text field');
        
        console.log(`STT Service with ${providerName}:`, {
          success: result.success,
          text: result.text.substring(0, 100) + (result.text.length > 100 ? '...' : ''),
          provider: result.provider
        });
      });
    });
  });
});

/**
 * Test suite for LLM providers
 */
describe('LLM Provider Tests', function() {
  this.timeout(60000); // 60 second timeout for API calls
  
  const llmProviders = ['openai', 'openrouter-gpt', 'openrouter-gemini', 'ark'];
  const testMessages = [
    { role: 'system', content: 'You are a helpful AI assistant.' },
    { role: 'user', content: 'Hello! Please respond with a short greeting.' }
  ];
  
  llmProviders.forEach(providerName => {
    describe(`${providerName} LLM Provider`, function() {
      let provider;
      
      before(function() {
        // Skip test if API key is not available
        const apiKeyName = testConfig.LLM_PROVIDERS[providerName].apiKey;
        if (!testConfig[apiKeyName]) {
          this.skip();
        }
        
        try {
          provider = LLMProviderFactory.createProvider(providerName, testConfig, testConfig);
        } catch (error) {
          console.error(`Failed to create ${providerName} provider:`, error);
          this.skip();
        }
      });
      
      it('should be created successfully', function() {
        assert(provider, 'Provider should be created');
        assert(provider.config, 'Provider should have config');
        assert(provider.apiKey, 'Provider should have API key');
      });
      
      it('should generate chat completion', async function() {
        const result = await provider.createChatCompletion(testMessages, {
          max_tokens: 100
        });
        
        assert(result, 'Should return a result');
        assert(typeof result.success === 'boolean', 'Should have success field');
        assert(result.provider === providerName.split('-')[0], 'Should have correct provider name');
        
        if (result.success) {
          assert(result.response, 'Should have response object');
          console.log(`${providerName} LLM Result: Success`);
        } else {
          console.log(`${providerName} LLM Result:`, result.error);
        }
      });
      
      it('should stream chat completion', async function() {
        const result = await provider.createChatCompletion(testMessages, {
          max_tokens: 50,
          stream: true
        });
        
        assert(result, 'Should return a result');
        
        if (result.success) {
          assert(result.response, 'Should have response object');
          assert(result.response.data, 'Should have data stream');
          
          // Test streaming by collecting some data
          let receivedData = false;
          const timeout = setTimeout(() => {
            if (!receivedData) {
              console.log(`${providerName}: No data received within timeout`);
            }
          }, 10000);
          
          result.response.data.on('data', (chunk) => {
            receivedData = true;
            clearTimeout(timeout);
            console.log(`${providerName} LLM Streaming: Received data chunk`);
          });
          
          result.response.data.on('error', (error) => {
            clearTimeout(timeout);
            console.error(`${providerName} LLM Streaming Error:`, error.message);
          });
          
        } else {
          console.log(`${providerName} LLM Streaming Result:`, result.error);
        }
      });
    });
  });
});

/**
 * Integration tests for all provider combinations
 */
describe('Provider Integration Tests', function() {
  this.timeout(120000); // 2 minute timeout for integration tests
  
  const testCombinations = [
    { asr: 'openai', llm: 'openai', description: 'OpenAI ASR + OpenAI LLM' },
    { asr: 'openai', llm: 'openrouter-gpt', description: 'OpenAI ASR + OpenRouter GPT' },
    { asr: 'openai', llm: 'openrouter-gemini', description: 'OpenAI ASR + OpenRouter Gemini' },
    { asr: 'openai', llm: 'ark', description: 'OpenAI ASR + ARK Doubao' },
    { asr: 'siliconflow', llm: 'openai', description: 'SenseVoice ASR + OpenAI LLM' },
    { asr: 'siliconflow', llm: 'openrouter-gpt', description: 'SenseVoice ASR + OpenRouter GPT' },
    { asr: 'siliconflow', llm: 'openrouter-gemini', description: 'SenseVoice ASR + OpenRouter Gemini' },
    { asr: 'siliconflow', llm: 'ark', description: 'SenseVoice ASR + ARK Doubao' }
  ];
  
  testCombinations.forEach(combination => {
    it(`should work with ${combination.description}`, async function() {
      // Check if API keys are available
      const asrApiKey = testConfig.ASR_PROVIDERS[combination.asr].apiKey;
      const llmApiKey = testConfig.LLM_PROVIDERS[combination.llm].apiKey;
      
      if (!testConfig[asrApiKey] || !testConfig[llmApiKey]) {
        this.skip();
      }
      
      try {
        // Create providers
        const asrProvider = ASRProviderFactory.createProvider(combination.asr, testConfig, testConfig);
        const llmProvider = LLMProviderFactory.createProvider(combination.llm, testConfig, testConfig);
        
        // Test ASR
        const audioBuffer = createTestAudioBuffer(2);
        const tempDir = path.join(__dirname, '../temp');
        if (!fs.existsSync(tempDir)) {
          fs.mkdirSync(tempDir, { recursive: true });
        }
        
        const asrResult = await asrProvider.transcribe(audioBuffer, tempDir);
        assert(asrResult.success !== undefined, 'ASR should return result');
        
        // Test LLM with a simple message
        const messages = [
          { role: 'system', content: 'You are a helpful assistant.' },
          { role: 'user', content: 'Say hello in one word.' }
        ];
        
        const llmResult = await llmProvider.createChatCompletion(messages, {
          max_tokens: 10
        });
        
        assert(llmResult.success !== undefined, 'LLM should return result');
        
        console.log(`Integration Test - ${combination.description}:`, {
          asr: { success: asrResult.success, provider: asrResult.provider },
          llm: { success: llmResult.success, provider: llmResult.provider }
        });
        
      } catch (error) {
        console.error(`Integration test failed for ${combination.description}:`, error.message);
        throw error;
      }
    });
  });
});

/**
 * Provider switching tests
 */
describe('Provider Switching Tests', function() {
  it('should switch ASR providers dynamically', function() {
    const originalConfig = require('../config');
    Object.assign(originalConfig, testConfig);
    
    const sttService = new SpeechToTextService();
    const originalProvider = sttService.getProviderInfo();
    
    // Try switching to different provider
    const availableProviders = ['openai', 'siliconflow'];
    const newProvider = availableProviders.find(p => p !== originalProvider.provider);
    
    if (newProvider && testConfig[testConfig.ASR_PROVIDERS[newProvider].apiKey]) {
      sttService.switchProvider(newProvider);
      const newProviderInfo = sttService.getProviderInfo();
      
      assert(newProviderInfo.provider !== originalProvider.provider, 'Provider should change');
      console.log('ASR Provider switched from', originalProvider.provider, 'to', newProviderInfo.provider);
    } else {
      console.log('Skipping ASR provider switching test - insufficient API keys');
    }
  });
});

// Export test configuration for use in other test files
module.exports = {
  testConfig,
  createTestAudioBuffer
}; 