const config = require('../config');
const ort = require('onnxruntime-node');
const path = require('path');
const fs = require('fs');

class VoiceActivityDetector {
  constructor(options = {}) {
    this.threshold = options.threshold || config.VAD_THRESHOLD || 0.5;
    this.frameLength = options.frameLength || config.VAD_FRAME_LENGTH || 512;
    this.minSpeechDuration = options.minSpeechDuration || config.VAD_MIN_SPEECH_DURATION || 250;
    this.maxSilenceDuration = options.maxSilenceDuration || config.VAD_MAX_SILENCE_DURATION || 500;
    this.sampleRate = options.sampleRate || config.AUDIO_SAMPLE_RATE || 16000;
    
    // Silero VAD specific parameters
    this.sileroFrameLength = 512; // Fixed frame length for Silero VAD
    this.sileroSampleRate = 16000; // Fixed sample rate for Silero VAD
    
    // State variables
    this.isSpeaking = false;
    this.speechStartTime = null;
    this.lastSpeechTime = null;
    this.audioBuffer = Buffer.alloc(0);
    this.speechBuffer = Buffer.alloc(0);
    
    // ONNX Runtime session
    this.session = null;
    this.isInitialized = false;
    this.initializationPromise = null;
    
    // Silero VAD state
    this.state = null;
    this.sr = null;
    
    // Initialize the Silero VAD
    this.initializationPromise = this.initializeSileroVAD();
  }

  /**
   * Initialize the Silero VAD ONNX model
   */
  async initializeSileroVAD() {
    try {
      console.log('Initializing Silero VAD...');
      
      // Load the ONNX model
      const modelPath = path.join(__dirname, '../models/silero_vad.onnx');
      
      if (!fs.existsSync(modelPath)) {
        throw new Error(`Silero VAD model not found at ${modelPath}`);
      }
      
      // Create ONNX Runtime session
      this.session = await ort.InferenceSession.create(modelPath, {
        executionProviders: ['cpu'],
        graphOptimizationLevel: 'all',
        enableMemPattern: true
      });
      
      // Initialize state tensors for Silero VAD
      this.resetSileroState();
      
      this.isInitialized = true;
      console.log('Silero VAD initialized successfully');
      
    } catch (error) {
      console.error('Failed to initialize Silero VAD:', error);
      throw error;
    }
  }

  /**
   * Reset Silero VAD state tensors
   */
  resetSileroState() {
    // Initialize state tensor for Silero VAD
    // The state tensor combines h and c LSTM hidden states
    this.state = new ort.Tensor('float32', new Float32Array(2 * 1 * 128).fill(0.0), [2, 1, 128]);
    this.sr = new ort.Tensor('int64', new BigInt64Array([BigInt(this.sileroSampleRate)]), [1]);
  }

  /**
   * Convert Buffer to Float32Array for Silero VAD
   * @param {Buffer} buffer - PCM 16-bit audio buffer
   * @returns {Float32Array} Normalized audio samples
   */
  bufferToFloat32Array(buffer) {
    const samples = new Float32Array(buffer.length / 2);
    for (let i = 0; i < samples.length; i++) {
      // Convert 16-bit PCM to normalized float (-1 to 1)
      const sample = buffer.readInt16LE(i * 2);
      samples[i] = sample / 32768.0;
    }
    return samples;
  }

  /**
   * Run Silero VAD inference on audio chunk
   * @param {Float32Array} audioSamples - Normalized audio samples
   * @returns {Promise<number>} Speech probability (0-1)
   */
  async runSileroVAD(audioSamples) {
    if (!this.session || !this.isInitialized) {
      throw new Error('Silero VAD not initialized');
    }

    try {
      // Create input tensor
      const inputTensor = new ort.Tensor('float32', audioSamples, [1, audioSamples.length]);
      
      // Run inference
      const feeds = {
        input: inputTensor,
        state: this.state,
        sr: this.sr
      };
      
      const results = await this.session.run(feeds);
      
      // Update state tensor for next inference
      this.state = results.stateN;
      
      // Get speech probability
      const speechProb = results.output.data[0];
      
      return speechProb;
      
    } catch (error) {
      console.error('Error running Silero VAD inference:', error);
      return 0.0; // Return silence probability on error
    }
  }

  /**
   * Process audio chunk and detect voice activity using Silero VAD
   * @param {Buffer} audioChunk - Raw audio data
   * @returns {Promise<Array>} VAD result with detection status and audio data
   */
  async processAudioChunk(audioChunk) {
    // Wait for initialization if not complete
    if (!this.isInitialized) {
      await this.initializationPromise;
    }

    const currentTime = Date.now();
    const results = [];
    
    // Add to buffer
    this.audioBuffer = Buffer.concat([this.audioBuffer, audioChunk]);
    
    // Process audio in chunks suitable for Silero VAD (512 samples)
    const chunkSize = this.sileroFrameLength * 2; // 16-bit = 2 bytes per sample
    
    while (this.audioBuffer.length >= chunkSize) {
      const chunk = this.audioBuffer.slice(0, chunkSize);
      this.audioBuffer = this.audioBuffer.slice(chunkSize);
      
      try {
        // Convert to Float32Array for Silero VAD
        const audioSamples = this.bufferToFloat32Array(chunk);
        
        // Run Silero VAD inference
        const speechProb = await this.runSileroVAD(audioSamples);
        
        // Check if speech is detected
        const isVoiceActive = speechProb > this.threshold;
        
        if (isVoiceActive) {
          if (!this.isSpeaking) {
            // Speech started
            this.isSpeaking = true;
            this.speechStartTime = currentTime;
            this.speechBuffer = Buffer.alloc(0);
            console.log('Silero VAD: Speech started (prob:', speechProb.toFixed(3), ')');
            // Emit the rising edge so the server can tell the client to barge
            // in. Without this the client's 'speech_start' handler is dead and
            // the assistant keeps talking over the user.
            results.push({ type: 'speech_start', timestamp: currentTime });
          }
          
          this.lastSpeechTime = currentTime;
          this.speechBuffer = Buffer.concat([this.speechBuffer, chunk]);
          
        } else if (this.isSpeaking) {
          // Check if silence duration exceeds threshold
          const silenceDuration = currentTime - this.lastSpeechTime;
          
          if (silenceDuration > this.maxSilenceDuration) {
            // Speech ended
            const speechDuration = currentTime - this.speechStartTime;
            
            if (speechDuration >= this.minSpeechDuration) {
              console.log('Silero VAD: Speech ended', { 
                duration: speechDuration, 
                bufferSize: this.speechBuffer.length 
              });
              
              results.push({
                type: 'speech_end',
                audioData: this.speechBuffer,
                duration: speechDuration,
                timestamp: currentTime
              });
            }
            
            this.isSpeaking = false;
            this.speechStartTime = null;
            this.lastSpeechTime = null;
            this.speechBuffer = Buffer.alloc(0);
          } else {
            // Still in speech, add chunk to buffer
            this.speechBuffer = Buffer.concat([this.speechBuffer, chunk]);
          }
        }
        
      } catch (error) {
        console.error('Error processing audio chunk with Silero VAD:', error);
        // Continue processing other chunks
      }
    }
    
    return results;
  }

  /**
   * Force end current speech session
   * @returns {Promise<Object|null>} Final speech data if available
   */
  async forceEndSpeech() {
    if (this.isSpeaking && this.speechBuffer.length > 0) {
      const currentTime = Date.now();
      const speechDuration = currentTime - this.speechStartTime;
      
      if (speechDuration >= this.minSpeechDuration) {
        const result = {
          type: 'speech_end',
          audioData: this.speechBuffer,
          duration: speechDuration,
          timestamp: currentTime
        };
        
        this.isSpeaking = false;
        this.speechStartTime = null;
        this.lastSpeechTime = null;
        this.speechBuffer = Buffer.alloc(0);
        
        return result;
      }
    }
    
    this.reset();
    return null;
  }

  /**
   * Reset VAD state
   */
  reset() {
    this.isSpeaking = false;
    this.speechStartTime = null;
    this.lastSpeechTime = null;
    this.audioBuffer = Buffer.alloc(0);
    this.speechBuffer = Buffer.alloc(0);
    
    // Reset Silero VAD state
    if (this.isInitialized) {
      this.resetSileroState();
    }
  }

  /**
   * Get current VAD state
   * @returns {Object} Current state information
   */
  getState() {
    return {
      isSpeaking: this.isSpeaking,
      speechDuration: this.speechStartTime ? Date.now() - this.speechStartTime : 0,
      bufferSize: this.speechBuffer.length,
      threshold: this.threshold,
      isInitialized: this.isInitialized
    };
  }

  /**
   * Cleanup resources
   */
  async cleanup() {
    if (this.session) {
      try {
        await this.session.release();
      } catch (error) {
        console.error('Error releasing ONNX session:', error);
      }
      this.session = null;
    }
    
    this.state = null;
    this.sr = null;
    this.isInitialized = false;
    this.reset();
  }
}

module.exports = VoiceActivityDetector; 