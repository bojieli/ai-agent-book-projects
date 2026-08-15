const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');

/**
 * Base ASR Provider class
 */
class BaseASRProvider {
  constructor(config, apiKey) {
    this.config = config;
    this.apiKey = apiKey;
  }

  /**
   * Convert raw audio buffer to WAV format
   * @param {Buffer} audioBuffer - Raw PCM audio data
   * @param {Object} options - Audio format options
   * @returns {Buffer} WAV formatted audio data
   */
  createWavBuffer(audioBuffer, options = {}) {
    const sampleRate = options.sampleRate || 16000;
    const channels = options.channels || 1;
    const bitsPerSample = options.bitsPerSample || 16;
    
    const byteRate = sampleRate * channels * bitsPerSample / 8;
    const blockAlign = channels * bitsPerSample / 8;
    const dataSize = audioBuffer.length;
    const fileSize = 36 + dataSize;
    
    const header = Buffer.alloc(44);
    
    // RIFF header
    header.write('RIFF', 0);
    header.writeUInt32LE(fileSize, 4);
    header.write('WAVE', 8);
    
    // fmt chunk
    header.write('fmt ', 12);
    header.writeUInt32LE(16, 16); // PCM format chunk size
    header.writeUInt16LE(1, 20);  // PCM format
    header.writeUInt16LE(channels, 22);
    header.writeUInt32LE(sampleRate, 24);
    header.writeUInt32LE(byteRate, 28);
    header.writeUInt16LE(blockAlign, 32);
    header.writeUInt16LE(bitsPerSample, 34);
    
    // data chunk
    header.write('data', 36);
    header.writeUInt32LE(dataSize, 40);
    
    return Buffer.concat([header, audioBuffer]);
  }

  async transcribe(audioBuffer, options = {}) {
    throw new Error('transcribe method must be implemented by subclass');
  }
}

/**
 * OpenAI Whisper ASR Provider
 */
class OpenAIASRProvider extends BaseASRProvider {
  async transcribe(audioBuffer, tempDir, options = {}) {
    try {
      // Create WAV buffer
      const wavBuffer = this.createWavBuffer(audioBuffer, {
        sampleRate: 16000,
        channels: 1,
        bitsPerSample: 16
      });

      // Create temporary file
      const tempFileName = `audio_${Date.now()}_${Math.random().toString(36).substring(2)}.wav`;
      const tempFilePath = path.join(tempDir, tempFileName);
      
      // Write audio to temporary file
      fs.writeFileSync(tempFilePath, wavBuffer);

      try {
        // Create form data
        const formData = new FormData();
        formData.append('file', fs.createReadStream(tempFilePath));
        formData.append('model', this.config.model);
        formData.append('response_format', 'json');
        
        if (options.language) {
          formData.append('language', options.language);
        }
        
        if (options.prompt) {
          formData.append('prompt', options.prompt);
        }

        // Make API request
        const response = await axios({
          method: 'post',
          url: this.config.apiUrl,
          data: formData,
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            ...formData.getHeaders()
          },
          timeout: 30000 // 30 second timeout
        });

        const result = {
          success: true,
          text: response.data.text || '',
          language: response.data.language || 'unknown',
          duration: response.data.duration || 0,
          confidence: response.data.confidence || 1.0,
          requestId: response.headers?.['x-request-id'] || response.headers?.['request-id'] || null,
          responseModel: response.data.model || this.config.model,
          timestamp: Date.now(),
          provider: 'openai'
        };

        console.log('OpenAI ASR Result:', {
          text: result.text,
          language: result.language,
          duration: result.duration
        });

        return result;

      } finally {
        // Clean up temporary file
        try {
          fs.unlinkSync(tempFilePath);
        } catch (cleanupError) {
          console.warn('Failed to cleanup temp file:', cleanupError.message);
        }
      }

    } catch (error) {
      console.error('OpenAI ASR error:', error.response?.data || error.message);
      
      return {
        success: false,
        text: '',
        error: error.response?.data?.error?.message || error.message,
        timestamp: Date.now(),
        provider: 'openai'
      };
    }
  }
}

/**
 * SenseVoice via Siliconflow ASR Provider
 */
class SiliconflowASRProvider extends BaseASRProvider {
  async transcribe(audioBuffer, tempDir, options = {}) {
    try {
      // Create WAV buffer
      const wavBuffer = this.createWavBuffer(audioBuffer, {
        sampleRate: 16000,
        channels: 1,
        bitsPerSample: 16
      });

      // Create temporary file
      const tempFileName = `audio_${Date.now()}_${Math.random().toString(36).substring(2)}.wav`;
      const tempFilePath = path.join(tempDir, tempFileName);
      
      // Write audio to temporary file
      fs.writeFileSync(tempFilePath, wavBuffer);

      try {
        // Create form data
        const formData = new FormData();
        formData.append('file', fs.createReadStream(tempFilePath));
        formData.append('model', this.config.model);
        formData.append('response_format', 'json');
        
        // SenseVoice specific parameters
        if (options.language) {
          formData.append('language', options.language);
        } else {
          // SenseVoice supports auto language detection
          formData.append('language', 'auto');
        }
        
        if (options.prompt) {
          formData.append('prompt', options.prompt);
        }

        // Make API request
        const response = await axios({
          method: 'post',
          url: this.config.apiUrl,
          data: formData,
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            ...formData.getHeaders()
          },
          timeout: 30000 // 30 second timeout
        });

        const result = {
          success: true,
          text: response.data.text || '',
          language: response.data.language || 'unknown',
          duration: response.data.duration || 0,
          confidence: response.data.confidence || 1.0,
          requestId: response.headers?.['x-request-id'] || response.headers?.['request-id'] || null,
          responseModel: response.data.model || this.config.model,
          timestamp: Date.now(),
          provider: 'siliconflow'
        };

        console.log('SenseVoice ASR Result:', {
          text: result.text,
          language: result.language,
          duration: result.duration
        });

        return result;

      } finally {
        // Clean up temporary file
        try {
          fs.unlinkSync(tempFilePath);
        } catch (cleanupError) {
          console.warn('Failed to cleanup temp file:', cleanupError.message);
        }
      }

    } catch (error) {
      console.error('SenseVoice ASR error:', error.response?.data || error.message);
      
      return {
        success: false,
        text: '',
        error: error.response?.data?.error?.message || error.message,
        timestamp: Date.now(),
        provider: 'siliconflow'
      };
    }
  }
}

/**
 * ASR Provider Factory
 */
class ASRProviderFactory {
  static createProvider(providerName, config, globalConfig) {
    const providerConfig = config.ASR_PROVIDERS[providerName];
    if (!providerConfig) {
      throw new Error(`ASR provider ${providerName} not found in configuration`);
    }

    // Get API key from global config
    const apiKey = globalConfig[providerConfig.apiKey];
    if (!apiKey) {
      throw new Error(`API key ${providerConfig.apiKey} not found in configuration`);
    }

    switch (providerName) {
      case 'openai':
        return new OpenAIASRProvider(providerConfig, apiKey);
      case 'siliconflow':
        return new SiliconflowASRProvider(providerConfig, apiKey);
      default:
        throw new Error(`Unsupported ASR provider: ${providerName}`);
    }
  }
}

module.exports = {
  BaseASRProvider,
  OpenAIASRProvider,
  SiliconflowASRProvider,
  ASRProviderFactory
};
