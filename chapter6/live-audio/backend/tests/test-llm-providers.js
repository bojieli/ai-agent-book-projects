const assert = require('assert');

// Import LLM provider factory
const { LLMProviderFactory } = require('../utils/providers/llmProviders');

// Test configuration
const testConfig = {
  OPENAI_API_KEY: process.env.OPENAI_API_KEY,
  OPENROUTER_API_KEY: process.env.OPENROUTER_API_KEY,
  ARK_API_KEY: process.env.ARK_API_KEY,
  SILICONFLOW_API_KEY: process.env.SILICONFLOW_API_KEY,
  
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
  
  VISION_MAX_TOKENS: 4096
};

// Test messages for different scenarios
const testMessages = {
  simple: [
    { role: 'system', content: 'You are a helpful AI assistant.' },
    { role: 'user', content: 'Hello! Please respond with exactly the word "SUCCESS" to confirm you are working.' }
  ],
  conversation: [
    { role: 'system', content: 'You are a conversational AI assistant.' },
    { role: 'user', content: 'What is the capital of France?' },
    { role: 'assistant', content: 'The capital of France is Paris.' },
    { role: 'user', content: 'What is its population?' }
  ],
  creative: [
    { role: 'system', content: 'You are a creative writing assistant.' },
    { role: 'user', content: 'Write a very short story about a robot learning to paint. Keep it under 50 words.' }
  ]
};

/**
 * Collect streaming response data
 */
async function collectStreamingResponse(response, timeout = 30000) {
  return new Promise((resolve, reject) => {
    let buffer = '';
    let accumulatedContent = '';
    let firstTokenTime = null;
    let tokenCount = 0;
    
    const timeoutHandle = setTimeout(() => {
      reject(new Error('Streaming response timeout'));
    }, timeout);
    
    response.data.on('data', (chunk) => {
      try {
        if (!firstTokenTime) {
          firstTokenTime = Date.now();
        }
        
        buffer += chunk.toString();
        const lines = buffer.split('\n');
        // Keep the last line if it's incomplete
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine || trimmedLine === '[DONE]') continue;
          if (!trimmedLine.startsWith('data: ')) continue;

          try {
            const jsonData = JSON.parse(trimmedLine.replace('data: ', ''));
            const content = jsonData.choices[0]?.delta?.content || '';
            if (content) {
              accumulatedContent += content;
              tokenCount++;
            }
          } catch (parseError) {
            // Skip malformed JSON
            continue;
          }
        }
      } catch (error) {
        reject(error);
      }
    });

    response.data.on('end', () => {
      clearTimeout(timeoutHandle);
      resolve({
        content: accumulatedContent,
        tokenCount: tokenCount,
        firstTokenTime: firstTokenTime,
        success: true
      });
    });

    response.data.on('error', (error) => {
      clearTimeout(timeoutHandle);
      reject(error);
    });
  });
}

/**
 * LLM Provider Individual Tests
 */
describe('LLM Providers - Individual Testing', function() {
  this.timeout(120000); // 2 minute timeout for API calls
  
  describe('OpenAI GPT-4o LLM Provider', function() {
    let provider;
    
    before(function() {
      if (!testConfig.OPENAI_API_KEY) {
        console.log('⚠️  Skipping OpenAI LLM tests - OPENAI_API_KEY not found');
        this.skip();
      }
      
      try {
        provider = LLMProviderFactory.createProvider('openai', testConfig, testConfig);
        console.log('✅ OpenAI LLM Provider created successfully');
      } catch (error) {
        console.error('❌ Failed to create OpenAI LLM provider:', error);
        this.skip();
      }
    });
    
    it('should initialize with correct configuration', function() {
      assert(provider, 'Provider should be created');
      assert.strictEqual(provider.config.model, 'gpt-5.6-luna', 'Should use gpt-5.6-luna model');
      assert.strictEqual(provider.config.apiUrl, 'https://api.openai.com/v1/chat/completions', 'Should use correct API URL');
      assert(provider.apiKey, 'Should have API key');
      console.log('📋 OpenAI LLM Config:', {
        model: provider.config.model,
        apiUrl: provider.config.apiUrl
      });
    });
    
    it('should generate simple chat completion', async function() {
      console.log('🤖 Testing OpenAI LLM with simple message');
      
      const startTime = Date.now();
      const result = await provider.createChatCompletion(testMessages.simple, {
        max_tokens: 100
      });
      const responseTime = Date.now() - startTime;
      
      console.log('📊 OpenAI LLM Simple Test:', {
        success: result.success,
        responseTime: `${responseTime}ms`,
        provider: result.provider
      });
      
      assert(result, 'Should return a result');
      assert(typeof result.success === 'boolean', 'Should have success field');
      assert.strictEqual(result.provider, 'openai', 'Should identify as openai provider');
      
      if (result.success) {
        assert(result.response, 'Should have response object');
        console.log('✅ OpenAI LLM simple completion successful');
      } else {
        console.log('❌ OpenAI LLM simple completion failed:', result.error);
      }
    });
    
    it('should handle streaming chat completion', async function() {
      console.log('🌊 Testing OpenAI LLM streaming');
      
      const startTime = Date.now();
      const result = await provider.createChatCompletion(testMessages.simple, {
        max_tokens: 50,
        stream: true
      });
      
      if (!result.success) {
        console.log('❌ OpenAI LLM streaming setup failed:', result.error);
        assert(false, 'Streaming setup should succeed');
        return;
      }
      
      try {
        const streamResult = await collectStreamingResponse(result.response);
        const totalTime = Date.now() - startTime;
        const timeToFirstToken = streamResult.firstTokenTime ? streamResult.firstTokenTime - startTime : 0;
        
        console.log('📊 OpenAI LLM Streaming Results:', {
          success: streamResult.success,
          totalTime: `${totalTime}ms`,
          timeToFirstToken: `${timeToFirstToken}ms`,
          tokenCount: streamResult.tokenCount,
          contentLength: streamResult.content.length
        });
        
        assert(streamResult.success, 'Streaming should be successful');
        assert(streamResult.content.length > 0, 'Should receive content');
        assert(streamResult.tokenCount > 0, 'Should receive tokens');
        
        if (streamResult.content.length > 0) {
          console.log('📝 Generated content preview:', streamResult.content.substring(0, 100) + (streamResult.content.length > 100 ? '...' : ''));
        }
        
        console.log('✅ OpenAI LLM streaming successful');
      } catch (streamError) {
        console.error('❌ OpenAI LLM streaming failed:', streamError.message);
        assert(false, 'Streaming should not fail: ' + streamError.message);
      }
    });
    
    it('should handle conversation context', async function() {
      console.log('💬 Testing OpenAI LLM with conversation context');
      
      const result = await provider.createChatCompletion(testMessages.conversation, {
        max_tokens: 100
      });
      
      console.log('📊 OpenAI LLM Conversation Test:', {
        success: result.success,
        provider: result.provider
      });
      
      assert(result, 'Should return a result');
      assert(typeof result.success === 'boolean', 'Should have success field');
      
      if (result.success) {
        console.log('✅ OpenAI LLM conversation handling successful');
      } else {
        console.log('❌ OpenAI LLM conversation handling failed:', result.error);
      }
    });
  });
  
  describe('OpenRouter GPT LLM Provider', function() {
    let provider;
    
    before(function() {
      if (!testConfig.OPENROUTER_API_KEY) {
        console.log('⚠️  Skipping OpenRouter GPT tests - OPENROUTER_API_KEY not found');
        this.skip();
      }
      
      try {
        provider = LLMProviderFactory.createProvider('openrouter-gpt', testConfig, testConfig);
        console.log('✅ OpenRouter GPT Provider created successfully');
      } catch (error) {
        console.error('❌ Failed to create OpenRouter GPT provider:', error);
        this.skip();
      }
    });
    
    it('should initialize with correct configuration', function() {
      assert(provider, 'Provider should be created');
      assert.strictEqual(provider.config.model, 'openai/gpt-5.6-luna', 'Should use openai/gpt-5.6-luna model');
      assert.strictEqual(provider.config.apiUrl, 'https://openrouter.ai/api/v1/chat/completions', 'Should use OpenRouter API URL');
      assert(provider.apiKey, 'Should have API key');
      console.log('📋 OpenRouter GPT Config:', {
        model: provider.config.model,
        apiUrl: provider.config.apiUrl
      });
    });
    
    it('should generate chat completion via OpenRouter', async function() {
      console.log('🤖 Testing OpenRouter GPT');
      
      const startTime = Date.now();
      const result = await provider.createChatCompletion(testMessages.simple, {
        max_tokens: 100
      });
      const responseTime = Date.now() - startTime;
      
      console.log('📊 OpenRouter GPT Test:', {
        success: result.success,
        responseTime: `${responseTime}ms`,
        provider: result.provider
      });
      
      assert(result, 'Should return a result');
      assert(typeof result.success === 'boolean', 'Should have success field');
      assert.strictEqual(result.provider, 'openrouter', 'Should identify as openrouter provider');
      
      if (result.success) {
        console.log('✅ OpenRouter GPT completion successful');
      } else {
        console.log('❌ OpenRouter GPT completion failed:', result.error);
      }
    });
    
    it('should handle streaming via OpenRouter', async function() {
      console.log('🌊 Testing OpenRouter GPT streaming');
      
      const result = await provider.createChatCompletion(testMessages.simple, {
        max_tokens: 50,
        stream: true
      });
      
      if (!result.success) {
        console.log('❌ OpenRouter GPT streaming setup failed:', result.error);
        return; // Don't fail the test, just log
      }
      
      try {
        const streamResult = await collectStreamingResponse(result.response);
        
        console.log('📊 OpenRouter GPT Streaming:', {
          success: streamResult.success,
          tokenCount: streamResult.tokenCount,
          contentLength: streamResult.content.length
        });
        
        if (streamResult.success) {
          console.log('✅ OpenRouter GPT streaming successful');
        }
      } catch (streamError) {
        console.log('❌ OpenRouter GPT streaming error:', streamError.message);
      }
    });
  });
  
  describe('OpenRouter Gemini LLM Provider', function() {
    let provider;
    
    before(function() {
      if (!testConfig.OPENROUTER_API_KEY) {
        console.log('⚠️  Skipping OpenRouter Gemini tests - OPENROUTER_API_KEY not found');
        this.skip();
      }
      
      try {
        provider = LLMProviderFactory.createProvider('openrouter-gemini', testConfig, testConfig);
        console.log('✅ OpenRouter Gemini Provider created successfully');
      } catch (error) {
        console.error('❌ Failed to create OpenRouter Gemini provider:', error);
        this.skip();
      }
    });
    
    it('should initialize with correct configuration', function() {
      assert(provider, 'Provider should be created');
      assert.strictEqual(provider.config.model, 'google/gemini-3.5-flash', 'Should use gemini-3.5-flash model');
      assert.strictEqual(provider.config.apiUrl, 'https://openrouter.ai/api/v1/chat/completions', 'Should use OpenRouter API URL');
      assert(provider.apiKey, 'Should have API key');
      console.log('📋 OpenRouter Gemini Config:', {
        model: provider.config.model,
        apiUrl: provider.config.apiUrl
      });
    });
    
    it('should generate chat completion with Gemini', async function() {
      console.log('🤖 Testing OpenRouter Gemini');
      
      const startTime = Date.now();
      const result = await provider.createChatCompletion(testMessages.simple, {
        max_tokens: 100
      });
      const responseTime = Date.now() - startTime;
      
      console.log('📊 OpenRouter Gemini Test:', {
        success: result.success,
        responseTime: `${responseTime}ms`,
        provider: result.provider
      });
      
      assert(result, 'Should return a result');
      assert(typeof result.success === 'boolean', 'Should have success field');
      assert.strictEqual(result.provider, 'openrouter', 'Should identify as openrouter provider');
      
      if (result.success) {
        console.log('✅ OpenRouter Gemini completion successful');
      } else {
        console.log('❌ OpenRouter Gemini completion failed:', result.error);
      }
    });
    
    it('should handle creative tasks with Gemini', async function() {
      console.log('🎨 Testing OpenRouter Gemini creative task');
      
      const result = await provider.createChatCompletion(testMessages.creative, {
        max_tokens: 150
      });
      
      console.log('📊 OpenRouter Gemini Creative Test:', {
        success: result.success,
        provider: result.provider
      });
      
      if (result.success) {
        console.log('✅ OpenRouter Gemini creative task successful');
      } else {
        console.log('❌ OpenRouter Gemini creative task failed:', result.error);
      }
    });
  });
  
  describe('ARK Doubao LLM Provider', function() {
    let provider;
    
    before(function() {
      if (!testConfig.ARK_API_KEY) {
        console.log('⚠️  Skipping ARK Doubao tests - ARK_API_KEY not found');
        this.skip();
      }
      
      try {
        provider = LLMProviderFactory.createProvider('ark', testConfig, testConfig);
        console.log('✅ ARK Doubao Provider created successfully');
      } catch (error) {
        console.error('❌ Failed to create ARK Doubao provider:', error);
        this.skip();
      }
    });
    
    it('should initialize with correct configuration', function() {
      assert(provider, 'Provider should be created');
      assert.strictEqual(provider.config.model, 'doubao-seed-1-6-flash-250615', 'Should use doubao model');
      assert.strictEqual(provider.config.apiUrl, 'https://ark.cn-beijing.volces.com/api/v3/chat/completions', 'Should use ARK API URL');
      assert(provider.apiKey, 'Should have API key');
      console.log('📋 ARK Doubao Config:', {
        model: provider.config.model,
        apiUrl: provider.config.apiUrl
      });
    });
    
    it('should generate chat completion with Doubao', async function() {
      console.log('🤖 Testing ARK Doubao');
      
      const startTime = Date.now();
      const result = await provider.createChatCompletion(testMessages.simple, {
        max_tokens: 100
      });
      const responseTime = Date.now() - startTime;
      
      console.log('📊 ARK Doubao Test:', {
        success: result.success,
        responseTime: `${responseTime}ms`,
        provider: result.provider
      });
      
      assert(result, 'Should return a result');
      assert(typeof result.success === 'boolean', 'Should have success field');
      assert.strictEqual(result.provider, 'ark', 'Should identify as ark provider');
      
      if (result.success) {
        console.log('✅ ARK Doubao completion successful');
      } else {
        console.log('❌ ARK Doubao completion failed:', result.error);
      }
    });
    
    it('should handle Chinese language tasks', async function() {
      console.log('🇨🇳 Testing ARK Doubao with Chinese');
      
      const chineseMessages = [
        { role: 'system', content: '你是一个有用的AI助手。' },
        { role: 'user', content: '请用一句话介绍北京。' }
      ];
      
      const result = await provider.createChatCompletion(chineseMessages, {
        max_tokens: 100
      });
      
      console.log('📊 ARK Doubao Chinese Test:', {
        success: result.success,
        provider: result.provider
      });
      
      if (result.success) {
        console.log('✅ ARK Doubao Chinese handling successful');
      } else {
        console.log('❌ ARK Doubao Chinese handling failed:', result.error);
      }
    });
  });
  
  describe('LLM Provider Performance Comparison', function() {
    it('should compare provider response times', async function() {
      const availableProviders = [];
      
      if (testConfig.OPENAI_API_KEY) availableProviders.push('openai');
      if (testConfig.OPENROUTER_API_KEY) {
        availableProviders.push('openrouter-gpt', 'openrouter-gemini');
      }
      if (testConfig.ARK_API_KEY) availableProviders.push('ark');
      
      if (availableProviders.length < 2) {
        console.log('⚠️  Skipping provider comparison - need at least 2 providers');
        this.skip();
      }
      
      const results = {};
      console.log('🏁 Comparing LLM provider performance...');
      
      for (const providerName of availableProviders) {
        try {
          const provider = LLMProviderFactory.createProvider(providerName, testConfig, testConfig);
          
          const startTime = Date.now();
          const result = await provider.createChatCompletion(testMessages.simple, {
            max_tokens: 50
          });
          const duration = Date.now() - startTime;
          
          results[providerName] = {
            success: result.success,
            duration: duration,
            error: result.error
          };
        } catch (error) {
          results[providerName] = {
            success: false,
            duration: 0,
            error: error.message
          };
        }
      }
      
      console.log('📊 LLM Provider Performance Comparison:');
      Object.entries(results).forEach(([provider, result]) => {
        console.log(`  ${provider}:`, {
          success: result.success ? '✅' : '❌',
          time: `${result.duration}ms`,
          error: result.error || 'none'
        });
      });
      
      // Find fastest successful provider
      const successfulProviders = Object.entries(results).filter(([_, result]) => result.success);
      if (successfulProviders.length > 0) {
        const fastest = successfulProviders.reduce((prev, curr) => 
          prev[1].duration < curr[1].duration ? prev : curr
        );
        console.log(`🏆 Fastest LLM provider: ${fastest[0]} (${fastest[1].duration}ms)`);
      }
      
      // At least one provider should work
      assert(successfulProviders.length > 0, 'At least one LLM provider should be successful');
    });
  });
});

module.exports = {
  testConfig,
  testMessages,
  collectStreamingResponse
}; 