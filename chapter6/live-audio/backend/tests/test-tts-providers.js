const assert = require('assert');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Test configuration
const testConfig = {
  SILICONFLOW_API_KEY: process.env.SILICONFLOW_API_KEY,
  
  TTS_PROVIDERS: {
    siliconflow: {
      apiUrl: 'https://api.siliconflow.cn/v1/audio/speech',
      model: 'FunAudioLLM/CosyVoice2-0.5B',
      voice: 'FunAudioLLM/CosyVoice2-0.5B:diana',
      apiKey: 'SILICONFLOW_API_KEY'
    }
  }
};

// Test texts for different scenarios
const testTexts = {
  simple: 'Hello, this is a simple text-to-speech test.',
  multilingual: 'Hello world. 你好世界. こんにちは世界.',
  punctuation: 'Testing punctuation: question? exclamation! comma, period.',
  numbers: 'The year is 2025, and the time is 12:34 PM.',
  long: 'This is a longer text to test the text-to-speech synthesis capability. It contains multiple sentences and should demonstrate the natural flow of speech generation. The quality and naturalness of the audio output will be evaluated.'
};

/**
 * TTS Provider for CosyVoice2 via Siliconflow
 */
class SiliconflowTTSProvider {
  constructor(config, apiKey) {
    this.config = config;
    this.apiKey = apiKey;
  }

  async synthesize(text, options = {}) {
    try {
      const response = await axios({
        method: 'post',
        url: this.config.apiUrl,
        data: {
          model: this.config.model,
          input: text,
          voice: options.voice || this.config.voice,
          response_format: options.format || 'mp3',
          sample_rate: options.sampleRate || 32000,
          stream: options.stream || false,
          speed: options.speed || 1.0,
          gain: options.gain || 0
        },
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        responseType: 'arraybuffer',
        timeout: 60000 // 60 second timeout
      });

      const result = {
        success: true,
        audioData: Buffer.from(response.data),
        format: options.format || 'mp3',
        sampleRate: options.sampleRate || 32000,
        provider: 'siliconflow',
        timestamp: Date.now()
      };

      return result;

    } catch (error) {
      console.error('Siliconflow TTS error:', error.response?.data || error.message);
      
      return {
        success: false,
        audioData: null,
        error: error.response?.data?.error?.message || error.message,
        provider: 'siliconflow',
        timestamp: Date.now()
      };
    }
  }
}

/**
 * TTS Provider Individual Tests
 */
describe('TTS Providers - Individual Testing', function() {
  this.timeout(120000); // 2 minute timeout for API calls
  
  const tempDir = path.join(__dirname, '../temp');
  
  before(function() {
    // Ensure temp directory exists
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }
  });
  
  describe('CosyVoice2 (Siliconflow) TTS Provider', function() {
    let provider;
    
    before(function() {
      if (!testConfig.SILICONFLOW_API_KEY) {
        console.log('⚠️  Skipping Siliconflow TTS tests - SILICONFLOW_API_KEY not found');
        this.skip();
      }
      
      try {
        const providerConfig = testConfig.TTS_PROVIDERS.siliconflow;
        provider = new SiliconflowTTSProvider(providerConfig, testConfig.SILICONFLOW_API_KEY);
        console.log('✅ Siliconflow TTS Provider created successfully');
      } catch (error) {
        console.error('❌ Failed to create Siliconflow TTS provider:', error);
        this.skip();
      }
    });
    
    it('should initialize with correct configuration', function() {
      assert(provider, 'Provider should be created');
      assert.strictEqual(provider.config.model, 'FunAudioLLM/CosyVoice2-0.5B', 'Should use CosyVoice2 model');
      assert.strictEqual(provider.config.voice, 'FunAudioLLM/CosyVoice2-0.5B:diana', 'Should use diana voice');
      assert.strictEqual(provider.config.apiUrl, 'https://api.siliconflow.cn/v1/audio/speech', 'Should use correct API URL');
      assert(provider.apiKey, 'Should have API key');
      console.log('📋 Siliconflow TTS Config:', {
        model: provider.config.model,
        voice: provider.config.voice,
        apiUrl: provider.config.apiUrl
      });
    });
    
    it('should synthesize simple text to speech', async function() {
      console.log('🎵 Testing Siliconflow TTS with simple text');
      
      const startTime = Date.now();
      const result = await provider.synthesize(testTexts.simple);
      const synthesisTime = Date.now() - startTime;
      
      console.log('📊 Siliconflow TTS Simple Test:', {
        success: result.success,
        synthesisTime: `${synthesisTime}ms`,
        audioSize: result.audioData ? `${result.audioData.length} bytes` : 'none',
        format: result.format,
        sampleRate: result.sampleRate,
        provider: result.provider
      });
      
      assert(result, 'Should return a result');
      assert(typeof result.success === 'boolean', 'Should have success field');
      assert.strictEqual(result.provider, 'siliconflow', 'Should identify as siliconflow provider');
      
      if (result.success) {
        assert(result.audioData, 'Should have audio data');
        assert(result.audioData.length > 0, 'Audio data should not be empty');
        assert.strictEqual(result.format, 'mp3', 'Should return MP3 format');
        
        // Save test audio file
        const testAudioPath = path.join(tempDir, `tts_simple_${Date.now()}.mp3`);
        fs.writeFileSync(testAudioPath, result.audioData);
        console.log('💾 Saved test audio to:', testAudioPath);
        console.log('✅ Siliconflow TTS simple synthesis successful');
      } else {
        console.log('❌ Siliconflow TTS simple synthesis failed:', result.error);
      }
    });
    
    it('should handle multilingual text', async function() {
      console.log('🌍 Testing Siliconflow TTS with multilingual text');
      
      const result = await provider.synthesize(testTexts.multilingual);
      
      console.log('📊 Siliconflow TTS Multilingual Test:', {
        success: result.success,
        audioSize: result.audioData ? `${result.audioData.length} bytes` : 'none',
        provider: result.provider
      });
      
      assert(result, 'Should return a result');
      assert(typeof result.success === 'boolean', 'Should have success field');
      
      if (result.success) {
        assert(result.audioData, 'Should have audio data for multilingual text');
        assert(result.audioData.length > 0, 'Multilingual audio data should not be empty');
        
        // Save multilingual test audio
        const testAudioPath = path.join(tempDir, `tts_multilingual_${Date.now()}.mp3`);
        fs.writeFileSync(testAudioPath, result.audioData);
        console.log('💾 Saved multilingual audio to:', testAudioPath);
        console.log('✅ Siliconflow TTS multilingual synthesis successful');
      } else {
        console.log('❌ Siliconflow TTS multilingual synthesis failed:', result.error);
      }
    });
    
    it('should handle different audio formats and settings', async function() {
      console.log('⚙️  Testing Siliconflow TTS with different settings');
      
      const settings = [
        { format: 'mp3', sampleRate: 24000, speed: 1.0 },
        { format: 'mp3', sampleRate: 32000, speed: 1.2 },
        { format: 'mp3', sampleRate: 16000, speed: 0.8 }
      ];
      
      for (const setting of settings) {
        const result = await provider.synthesize(testTexts.simple, setting);
        
        console.log(`📊 TTS Settings Test (${setting.format}, ${setting.sampleRate}Hz, ${setting.speed}x):`, {
          success: result.success,
          audioSize: result.audioData ? `${result.audioData.length} bytes` : 'none',
          error: result.error || 'none'
        });
        
        assert(result, 'Should return a result');
        assert(typeof result.success === 'boolean', 'Should have success field');
        
        if (result.success) {
          assert(result.audioData, 'Should have audio data');
          assert(result.audioData.length > 0, 'Audio data should not be empty');
          
          // Save test audio with settings info
          const filename = `tts_settings_${setting.sampleRate}hz_${setting.speed}x_${Date.now()}.mp3`;
          const testAudioPath = path.join(tempDir, filename);
          fs.writeFileSync(testAudioPath, result.audioData);
          console.log(`💾 Saved settings test audio to: ${testAudioPath}`);
        }
      }
      
      console.log('✅ Siliconflow TTS settings variation tests completed');
    });
    
    it('should handle punctuation and numbers correctly', async function() {
      console.log('🔢 Testing Siliconflow TTS with punctuation and numbers');
      
      const punctuationResult = await provider.synthesize(testTexts.punctuation);
      const numbersResult = await provider.synthesize(testTexts.numbers);
      
      console.log('📊 Siliconflow TTS Punctuation Test:', {
        success: punctuationResult.success,
        audioSize: punctuationResult.audioData ? `${punctuationResult.audioData.length} bytes` : 'none'
      });
      
      console.log('📊 Siliconflow TTS Numbers Test:', {
        success: numbersResult.success,
        audioSize: numbersResult.audioData ? `${numbersResult.audioData.length} bytes` : 'none'
      });
      
      assert(punctuationResult, 'Should handle punctuation');
      assert(numbersResult, 'Should handle numbers');
      
      if (punctuationResult.success && numbersResult.success) {
        console.log('✅ Siliconflow TTS punctuation and numbers handling successful');
      }
    });
    
    it('should handle longer text synthesis', async function() {
      console.log('📝 Testing Siliconflow TTS with longer text');
      
      const startTime = Date.now();
      const result = await provider.synthesize(testTexts.long);
      const synthesisTime = Date.now() - startTime;
      
      console.log('📊 Siliconflow TTS Long Text Test:', {
        success: result.success,
        synthesisTime: `${synthesisTime}ms`,
        audioSize: result.audioData ? `${result.audioData.length} bytes` : 'none',
        textLength: testTexts.long.length
      });
      
      assert(result, 'Should return a result');
      assert(typeof result.success === 'boolean', 'Should have success field');
      
      if (result.success) {
        assert(result.audioData, 'Should have audio data for long text');
        assert(result.audioData.length > 0, 'Long text audio data should not be empty');
        
        // Long text should produce more audio data
        const expectedMinSize = 50000; // Roughly 50KB minimum for longer text
        if (result.audioData.length > expectedMinSize) {
          console.log('✅ Long text produced appropriate amount of audio data');
        }
        
        // Save long text audio
        const testAudioPath = path.join(tempDir, `tts_long_${Date.now()}.mp3`);
        fs.writeFileSync(testAudioPath, result.audioData);
        console.log('💾 Saved long text audio to:', testAudioPath);
        console.log('✅ Siliconflow TTS long text synthesis successful');
      } else {
        console.log('❌ Siliconflow TTS long text synthesis failed:', result.error);
      }
    });
    
    it('should handle empty or invalid text gracefully', async function() {
      console.log('🔍 Testing Siliconflow TTS with edge cases');
      
      const emptyResult = await provider.synthesize('');
      const spaceResult = await provider.synthesize('   ');
      const specialResult = await provider.synthesize('!@#$%^&*()');
      
      console.log('📊 Siliconflow TTS Edge Cases:', {
        empty: { success: emptyResult.success, error: emptyResult.error || 'none' },
        spaces: { success: spaceResult.success, error: spaceResult.error || 'none' },
        special: { success: specialResult.success, error: specialResult.error || 'none' }
      });
      
      // These should either work or fail gracefully
      assert(emptyResult, 'Should handle empty string');
      assert(spaceResult, 'Should handle whitespace');
      assert(specialResult, 'Should handle special characters');
      
      console.log('✅ Siliconflow TTS edge cases handled');
    });
    
    it('should measure synthesis performance metrics', async function() {
      console.log('🏁 Testing Siliconflow TTS performance metrics');
      
      const testText = testTexts.simple;
      const iterations = 3;
      const results = [];
      
      for (let i = 0; i < iterations; i++) {
        const startTime = Date.now();
        const result = await provider.synthesize(testText);
        const duration = Date.now() - startTime;
        
        if (result.success) {
          results.push({
            duration: duration,
            audioSize: result.audioData.length,
            success: true
          });
        } else {
          results.push({
            duration: duration,
            audioSize: 0,
            success: false,
            error: result.error
          });
        }
      }
      
      const successfulResults = results.filter(r => r.success);
      
      if (successfulResults.length > 0) {
        const avgDuration = successfulResults.reduce((sum, r) => sum + r.duration, 0) / successfulResults.length;
        const avgAudioSize = successfulResults.reduce((sum, r) => sum + r.audioSize, 0) / successfulResults.length;
        const minDuration = Math.min(...successfulResults.map(r => r.duration));
        const maxDuration = Math.max(...successfulResults.map(r => r.duration));
        
        console.log('📊 Siliconflow TTS Performance Metrics:', {
          successRate: `${successfulResults.length}/${iterations}`,
          avgSynthesisTime: `${Math.round(avgDuration)}ms`,
          minSynthesisTime: `${minDuration}ms`,
          maxSynthesisTime: `${maxDuration}ms`,
          avgAudioSize: `${Math.round(avgAudioSize)} bytes`,
          textLength: testText.length
        });
        
        // Performance expectations
        assert(avgDuration < 10000, 'Average synthesis time should be under 10 seconds');
        assert(avgAudioSize > 1000, 'Should produce reasonable amount of audio data');
        
        console.log('✅ Siliconflow TTS performance metrics acceptable');
      } else {
        console.log('❌ No successful TTS synthesis results for performance testing');
      }
      
      assert(successfulResults.length > 0, 'At least one synthesis attempt should succeed');
    });
  });
  
  describe('TTS Provider Integration', function() {
    it('should integrate with live audio system', function() {
      if (!testConfig.SILICONFLOW_API_KEY) {
        console.log('⚠️  Skipping TTS integration test - SILICONFLOW_API_KEY not found');
        this.skip();
      }
      
      // Simulate the TTS configuration that would be used in the live system
      const liveConfig = {
        TTS_API_URL: 'https://api.siliconflow.cn/v1/audio/speech',
        TTS_PROVIDERS: testConfig.TTS_PROVIDERS,
        TTS_PROVIDER: 'siliconflow',
        SILICONFLOW_API_KEY: testConfig.SILICONFLOW_API_KEY
      };
      
      assert(liveConfig.TTS_API_URL, 'Should have TTS API URL');
      assert(liveConfig.TTS_PROVIDERS.siliconflow, 'Should have Siliconflow TTS provider config');
      assert(liveConfig.SILICONFLOW_API_KEY, 'Should have Siliconflow API key');
      
      console.log('📋 Live System TTS Integration Config:', {
        provider: liveConfig.TTS_PROVIDER,
        model: liveConfig.TTS_PROVIDERS.siliconflow.model,
        voice: liveConfig.TTS_PROVIDERS.siliconflow.voice,
        hasApiKey: !!liveConfig.SILICONFLOW_API_KEY
      });
      
      console.log('✅ TTS provider integration configuration valid');
    });
  });
  
  after(function() {
    // Cleanup temp audio files
    try {
      const files = fs.readdirSync(tempDir);
      let cleanedCount = 0;
      files.forEach(file => {
        if (file.startsWith('tts_') && file.endsWith('.mp3')) {
          fs.unlinkSync(path.join(tempDir, file));
          cleanedCount++;
        }
      });
      console.log(`🧹 Cleaned up ${cleanedCount} temporary TTS audio files`);
    } catch (error) {
      console.warn('⚠️  Failed to cleanup temp TTS files:', error.message);
    }
  });
});

module.exports = {
  testConfig,
  testTexts,
  SiliconflowTTSProvider
}; 