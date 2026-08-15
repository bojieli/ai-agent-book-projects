class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.inputBuffer = [];
    
    // Remove VAD parameters - now using server-side Silero VAD only
    // The client-side VAD was primarily for debugging and is no longer needed
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || !input[0]) return true;

    // Convert to mono
    const monoInput = new Float32Array(input[0].length);
    for (let i = 0; i < input[0].length; i++) {
      let sum = 0;
      for (let channel = 0; channel < input.length; channel++) {
        sum += input[channel][i];
      }
      monoInput[i] = sum / input.length;
    }

    // Process in chunks - removed VAD processing
    const CHUNK_SIZE = 1024;
    this.inputBuffer.push(...monoInput);

    while (this.inputBuffer.length >= CHUNK_SIZE) {
      const chunk = this.inputBuffer.slice(0, CHUNK_SIZE);
      this.inputBuffer = this.inputBuffer.slice(CHUNK_SIZE);

      // Convert to 16-bit PCM
      const pcmData = new Int16Array(chunk.length);
      for (let i = 0; i < chunk.length; i++) {
        const s = Math.max(-1, Math.min(1, chunk[i]));
        pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }

      // Send the data - server-side Silero VAD will handle speech detection
      this.port.postMessage(pcmData.buffer, [pcmData.buffer]);
    }

    return true;
  }
}

class EchoProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.audioBuffer = [];
    this.playbackPosition = 0;
    this.isPlaying = false;
    this.sampleRate = 16000;
    this.isMuted = false;
    this.outputBufferSize = 2048;
    this.outputBuffer = new Float32Array(this.outputBufferSize);
    this.outputBufferPosition = 0;
    this.hasNotifiedQueueEmpty = false;  // Track if we've sent the queue empty notification

    this.port.onmessage = (event) => {
      if (event.data instanceof Float32Array) {
        if (!this.isMuted) {
          const audioData = event.data;
          const newBuffer = new Float32Array(audioData.length);
          newBuffer.set(audioData);
          
          if (!this.isPlaying) {
            this.audioBuffer = Array.from(newBuffer);
            this.playbackPosition = 0;
            this.outputBufferPosition = 0;
            this.hasNotifiedQueueEmpty = false;  // Reset notification flag when starting new playback
          } else {
            this.audioBuffer.push(...Array.from(newBuffer));
          }
          
          this.isPlaying = true;
        }
      } else if (event.data.type === 'clear') {
        // Clear the buffer and stop playback
        this.audioBuffer = [];
        this.playbackPosition = 0;
        this.outputBufferPosition = 0;
        this.isPlaying = false;
        this.isMuted = true;
        this.hasNotifiedQueueEmpty = false;
        // Notify that the queue is empty after clearing
        this.port.postMessage({ type: 'queue_empty' });
      } else if (event.data.type === 'unmute') {
        this.isMuted = false;
        this.hasNotifiedQueueEmpty = false;
      } else if (event.data.type === 'mute') {
        this.isMuted = true;
        this.audioBuffer = [];
        this.playbackPosition = 0;
        this.isPlaying = false;
        this.hasNotifiedQueueEmpty = false;
        // Notify that the queue is empty after muting
        this.port.postMessage({ type: 'queue_empty' });
      }
    };
  }

  process(inputs, outputs, parameters) {
    const output = outputs[0];
    
    // If muted or not playing, output silence
    if (this.isMuted || !this.isPlaying || this.audioBuffer.length === 0) {
      for (let channel = 0; channel < output.length; channel++) {
        output[channel].fill(0);
      }
      
      // Send queue_empty notification if we haven't already
      if (this.isPlaying && !this.hasNotifiedQueueEmpty) {
        this.port.postMessage({ type: 'queue_empty' });
        this.hasNotifiedQueueEmpty = true;
        this.isPlaying = false;
      }
      
      return true;
    }

    const outputChannel = output[0];
    const bufferSize = outputChannel.length;
    
    if (this.isPlaying && this.audioBuffer.length > 0) {
      // Fill the output buffer
      for (let i = 0; i < bufferSize; i++) {
        if (this.playbackPosition < this.audioBuffer.length) {
          const sample = this.audioBuffer[this.playbackPosition];
          for (let channel = 0; channel < output.length; channel++) {
            output[channel][i] = sample;
          }
          this.playbackPosition++;
        } else {
          // End of buffer reached
          for (let channel = 0; channel < output.length; channel++) {
            output[channel][i] = 0;
          }
          
          // If we've played everything, reset and notify
          if (this.playbackPosition >= this.audioBuffer.length && !this.hasNotifiedQueueEmpty) {
            this.isPlaying = false;
            this.playbackPosition = 0;
            this.audioBuffer = [];
            this.port.postMessage({ type: 'queue_empty' });
            this.hasNotifiedQueueEmpty = true;
          }
        }
      }
    } else {
      // Output silence if we're not playing
      for (let channel = 0; channel < output.length; channel++) {
        output[channel].fill(0);
      }
    }

    return true;
  }
}

registerProcessor('audio-processor', AudioProcessor);
registerProcessor('echo-processor', EchoProcessor);
