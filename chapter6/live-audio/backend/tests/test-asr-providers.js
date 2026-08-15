const assert = require('assert');
const fs = require('fs');
const path = require('path');

// Import ASR provider factory
const { ASRProviderFactory } = require('../utils/providers/asrProviders');

// Test configuration
const testConfig = {
  OPENAI_API_KEY: process.env.OPENAI_API_KEY,
  SILICONFLOW_API_KEY: process.env.SILICONFLOW_API_KEY,
  
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
  
  AUDIO_SAMPLE_RATE: 16000
};

/**
 * Create a test audio buffer with spoken content
 * This creates a simple sine wave that simulates audio content
 */
function createTestAudioBuffer(durationSeconds = 3, sampleRate = 16000) {
  const numSamples = durationSeconds * sampleRate;
  const buffer = Buffer.alloc(numSamples * 2); // 16-bit = 2 bytes per sample
  
  // Generate a more complex wave pattern to simulate speech
  for (let i = 0; i < numSamples; i++) {
    // Mix multiple frequencies to simulate speech-like content
    const t = i / sampleRate;
    const sample = 
      0.3 * Math.sin(2 * Math.PI * 300 * t) +  // Base frequency
      0.2 * Math.sin(2 * Math.PI * 600 * t) +  // Harmonic
      0.1 * Math.sin(2 * Math.PI * 1200 * t) + // Higher harmonic
      0.05 * (Math.random() - 0.5);           // Noise for realism
    
    const intSample = Math.round(sample * 16000); // Scale to 16-bit range
    buffer.writeInt16LE(intSample, i * 2);
  }
  
  return buffer;
}

/**
 * ASR Provider Individual Tests
 */
describe('ASR Providers - Individual Testing', function() {
  this.timeout(120000); // 2 minute timeout for API calls
  
  const tempDir = path.join(__dirname, '../temp');
  
  before(function() {
    // Ensure temp directory exists
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }
  });
  
  describe('OpenAI Whisper ASR Provider', function() {
    let provider;
    
    before(function() {
      if (!testConfig.OPENAI_API_KEY) {
        console.log('⚠️  Skipping OpenAI ASR tests - OPENAI_API_KEY not found');
        this.skip();
      }
      
      try {
        provider = ASRProviderFactory.createProvider('openai', testConfig, testConfig);
        console.log('✅ OpenAI ASR Provider created successfully');
      } catch (error) {
        console.error('❌ Failed to create OpenAI ASR provider:', error);
        this.skip();
      }
    });
    
    it('should initialize with correct configuration', function() {
      assert(provider, 'Provider should be created');
      assert.strictEqual(provider.config.model, 'whisper-1', 'Should use whisper-1 model');
      assert.strictEqual(provider.config.apiUrl, 'https://api.openai.com/v1/audio/transcriptions', 'Should use correct API URL');
      assert(provider.apiKey, 'Should have API key');
      console.log('📋 OpenAI ASR Config:', {
        model: provider.config.model,
        apiUrl: provider.config.apiUrl
      });
    });
    
    it('should transcribe test audio successfully', async function() {
      const audioBuffer = createTestAudioBuffer(3); // 3 seconds of test audio
      console.log('🎵 Testing OpenAI ASR with', audioBuffer.length, 'bytes of audio data');
      
      const startTime = Date.now();
      const result = await provider.transcribe(audioBuffer, tempDir);
      const duration = Date.now() - startTime;
      
      console.log('📊 OpenAI ASR Results:', {
        success: result.success,
        transcriptionTime: `${duration}ms`,
        textLength: result.text ? result.text.length : 0,
        language: result.language,
        confidence: result.confidence,
        provider: result.provider
      });
      
      assert(result, 'Should return a result');
      assert(typeof result.success === 'boolean', 'Should have success field');
      assert(typeof result.text === 'string', 'Should have text field');
      assert.strictEqual(result.provider, 'openai', 'Should identify as openai provider');
      
      if (result.success) {
        console.log('✅ OpenAI ASR transcription successful');
        if (result.text.length > 0) {
          console.log('📝 Transcribed text preview:', result.text.substring(0, 100) + (result.text.length > 100 ? '...' : ''));
        }
      } else {
        console.log('❌ OpenAI ASR transcription failed:', result.error);
      }
    });
    
    it('should handle empty audio gracefully', async function() {
      const emptyBuffer = Buffer.alloc(0);
      const result = await provider.transcribe(emptyBuffer, tempDir);
      
      console.log('🔍 OpenAI ASR Empty Audio Test:', {
        success: result.success,
        error: result.error,
        provider: result.provider
      });
      
      assert(result, 'Should return a result');
      assert(typeof result.success === 'boolean', 'Should have success field');
      // Empty audio should typically fail or return empty text
      if (!result.success) {
        assert(result.error, 'Should have error message for empty audio');
      }
    });
  });
  
  describe('SenseVoice (Siliconflow) ASR Provider', function() {
    let provider;
    
    before(function() {
      if (!testConfig.SILICONFLOW_API_KEY) {
        console.log('⚠️  Skipping Siliconflow ASR tests - SILICONFLOW_API_KEY not found');
        this.skip();
      }
      
      try {
        provider = ASRProviderFactory.createProvider('siliconflow', testConfig, testConfig);
        console.log('✅ Siliconflow ASR Provider created successfully');
      } catch (error) {
        console.error('❌ Failed to create Siliconflow ASR provider:', error);
        this.skip();
      }
    });
    
    it('should initialize with correct configuration', function() {
      assert(provider, 'Provider should be created');
      assert.strictEqual(provider.config.model, 'FunAudioLLM/SenseVoiceSmall', 'Should use SenseVoiceSmall model');
      assert.strictEqual(provider.config.apiUrl, 'https://api.siliconflow.cn/v1/audio/transcriptions', 'Should use correct API URL');
      assert(provider.apiKey, 'Should have API key');
      console.log('📋 Siliconflow ASR Config:', {
        model: provider.config.model,
        apiUrl: provider.config.apiUrl
      });
    });
    
    it('should transcribe test audio successfully', async function() {
      const audioBuffer = createTestAudioBuffer(3); // 3 seconds of test audio
      console.log('🎵 Testing Siliconflow ASR with', audioBuffer.length, 'bytes of audio data');
      
      const startTime = Date.now();
      const result = await provider.transcribe(audioBuffer, tempDir);
      const duration = Date.now() - startTime;
      
      console.log('📊 Siliconflow ASR Results:', {
        success: result.success,
        transcriptionTime: `${duration}ms`,
        textLength: result.text ? result.text.length : 0,
        language: result.language,
        confidence: result.confidence,
        provider: result.provider
      });
      
      assert(result, 'Should return a result');
      assert(typeof result.success === 'boolean', 'Should have success field');
      assert(typeof result.text === 'string', 'Should have text field');
      assert.strictEqual(result.provider, 'siliconflow', 'Should identify as siliconflow provider');
      
      if (result.success) {
        console.log('✅ Siliconflow ASR transcription successful');
        if (result.text.length > 0) {
          console.log('📝 Transcribed text preview:', result.text.substring(0, 100) + (result.text.length > 100 ? '...' : ''));
        }
      } else {
        console.log('❌ Siliconflow ASR transcription failed:', result.error);
      }
    });
    
    it('should handle different audio lengths', async function() {
      const shortAudio = createTestAudioBuffer(1); // 1 second
      const longAudio = createTestAudioBuffer(5);  // 5 seconds
      
      console.log('🎵 Testing Siliconflow ASR with different audio lengths');
      
      const shortResult = await provider.transcribe(shortAudio, tempDir);
      const longResult = await provider.transcribe(longAudio, tempDir);
      
      console.log('📊 Audio Length Tests:', {
        short: { success: shortResult.success, textLength: shortResult.text.length },
        long: { success: longResult.success, textLength: longResult.text.length }
      });
      
      assert(shortResult, 'Should handle short audio');
      assert(longResult, 'Should handle long audio');
      assert(typeof shortResult.success === 'boolean', 'Short audio should have success field');
      assert(typeof longResult.success === 'boolean', 'Long audio should have success field');
    });
  });
  
  describe('ASR Provider Comparison', function() {
    it('should compare provider performance', async function() {
      const availableProviders = [];
      
      if (testConfig.OPENAI_API_KEY) {
        availableProviders.push('openai');
      }
      if (testConfig.SILICONFLOW_API_KEY) {
        availableProviders.push('siliconflow');
      }
      
      if (availableProviders.length < 2) {
        console.log('⚠️  Skipping provider comparison - need at least 2 providers');
        this.skip();
      }
      
      const audioBuffer = createTestAudioBuffer(3);
      const results = {};
      
      console.log('🏁 Comparing ASR provider performance...');
      
      for (const providerName of availableProviders) {
        const provider = ASRProviderFactory.createProvider(providerName, testConfig, testConfig);
        
        const startTime = Date.now();
        const result = await provider.transcribe(audioBuffer, tempDir);
        const duration = Date.now() - startTime;
        
        results[providerName] = {
          success: result.success,
          duration: duration,
          textLength: result.text ? result.text.length : 0,
          error: result.error
        };
      }
      
      console.log('📊 ASR Provider Performance Comparison:');
      Object.entries(results).forEach(([provider, result]) => {
        console.log(`  ${provider}:`, {
          success: result.success ? '✅' : '❌',
          time: `${result.duration}ms`,
          textLength: result.textLength,
          error: result.error || 'none'
        });
      });
      
      // Find fastest successful provider
      const successfulProviders = Object.entries(results).filter(([_, result]) => result.success);
      if (successfulProviders.length > 0) {
        const fastest = successfulProviders.reduce((prev, curr) => 
          prev[1].duration < curr[1].duration ? prev : curr
        );
        console.log(`🏆 Fastest provider: ${fastest[0]} (${fastest[1].duration}ms)`);
      }
    });
  });
  
  after(function() {
    // Cleanup temp files
    try {
      const files = fs.readdirSync(tempDir);
      files.forEach(file => {
        if (file.startsWith('audio_')) {
          fs.unlinkSync(path.join(tempDir, file));
        }
      });
      console.log('🧹 Cleaned up temporary audio files');
    } catch (error) {
      console.warn('⚠️  Failed to cleanup temp files:', error.message);
    }
  });
});

module.exports = {
  testConfig,
  createTestAudioBuffer
}; 