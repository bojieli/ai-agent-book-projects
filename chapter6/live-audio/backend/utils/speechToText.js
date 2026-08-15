const fs = require('fs');
const path = require('path');
const config = require('../config');
const { ASRProviderFactory } = require('./providers/asrProviders');

class SpeechToTextService {
  constructor() {
    this.tempDir = path.join(__dirname, '../temp');
    this.ensureTempDirectory();
    
    // Initialize ASR provider based on configuration
    this.initializeProvider();
  }

  /**
   * Initialize ASR provider based on configuration
   */
  initializeProvider() {
    try {
      const providerName = config.ASR_PROVIDER || 'openai';
      this.asrProvider = ASRProviderFactory.createProvider(providerName, config, config);
      console.log(`ASR Provider initialized: ${providerName}`);
    } catch (error) {
      console.error('Failed to initialize ASR provider:', error);
      throw error;
    }
  }

  /**
   * Switch ASR provider dynamically
   * @param {string} providerName - Provider name to switch to
   */
  switchProvider(providerName) {
    try {
      this.asrProvider = ASRProviderFactory.createProvider(providerName, config, config);
      console.log(`ASR Provider switched to: ${providerName}`);
    } catch (error) {
      console.error('Failed to switch ASR provider:', error);
      throw error;
    }
  }

  /**
   * Ensure temp directory exists
   */
  ensureTempDirectory() {
    if (!fs.existsSync(this.tempDir)) {
      fs.mkdirSync(this.tempDir, { recursive: true });
    }
  }

  /**
   * Transcribe audio using the configured ASR provider
   * @param {Buffer} audioBuffer - Raw audio data
   * @param {Object} options - Transcription options
   * @returns {Promise<Object>} Transcription result
   */
  async transcribeAudio(audioBuffer, options = {}) {
    if (!this.asrProvider) {
      throw new Error('ASR provider not initialized');
    }

    try {
      const result = await this.asrProvider.transcribe(audioBuffer, this.tempDir, options);
      return result;
    } catch (error) {
      console.error('Transcription error:', error);
      return {
        success: false,
        text: '',
        error: error.message,
        timestamp: Date.now(),
        provider: this.asrProvider.config ? 'unknown' : 'uninitialized'
      };
    }
  }

  /**
   * Clean up old temporary files
   */
  cleanupTempFiles() {
    try {
      const files = fs.readdirSync(this.tempDir);
      const now = Date.now();
      const maxAge = 10 * 60 * 1000; // 10 minutes
      
      files.forEach(file => {
        const filePath = path.join(this.tempDir, file);
        const stats = fs.statSync(filePath);
        
        if (now - stats.mtime.getTime() > maxAge) {
          try {
            fs.unlinkSync(filePath);
            console.log('Cleaned up old temp file:', file);
          } catch (error) {
            console.warn('Failed to cleanup old temp file:', file, error.message);
          }
        }
      });
    } catch (error) {
      console.warn('Failed to cleanup temp directory:', error.message);
    }
  }

  /**
   * Check if audio buffer has sufficient content for transcription
   * @param {Buffer} audioBuffer - Audio buffer to check
   * @returns {boolean} True if buffer has sufficient content
   */
  hasSufficientAudio(audioBuffer) {
    if (!audioBuffer || audioBuffer.length === 0) {
      return false;
    }

    // Check minimum duration (at least 0.1 seconds of audio)
    const minSamples = config.AUDIO_SAMPLE_RATE * 0.1; // 0.1 seconds
    const minBytes = minSamples * 2; // 16-bit = 2 bytes per sample
    
    if (audioBuffer.length < minBytes) {
      return false;
    }

    // Since we're using Silero VAD for speech detection, we trust its decision
    // and only check for minimum duration. The energy check is redundant and
    // can reject valid speech that Silero VAD correctly identified.
    return true;
  }

  /**
   * Get current provider information
   * @returns {Object} Current provider information
   */
  getProviderInfo() {
    if (!this.asrProvider) {
      return { provider: 'none', status: 'not initialized' };
    }

    return {
      provider: this.asrProvider.constructor.name,
      model: this.asrProvider.config.model,
      apiUrl: this.asrProvider.config.apiUrl,
      status: 'ready'
    };
  }
}

module.exports = SpeechToTextService; 