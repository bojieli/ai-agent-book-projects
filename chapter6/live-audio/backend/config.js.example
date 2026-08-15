const config = {
  // API Keys
  OPENAI_API_KEY: process.env.OPENAI_API_KEY || 'your-openai-api-key-here',
  OPENROUTER_API_KEY: process.env.OPENROUTER_API_KEY || 'your-openrouter-api-key-here',
  ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY || 'your-anthropic-api-key-here',
  ARK_API_KEY: process.env.ARK_API_KEY || 'your-ark-api-key-here',
  SILICONFLOW_API_KEY: process.env.SILICONFLOW_API_KEY || 'your-siliconflow-api-key-here',
  
  // Provider Selection
  ASR_PROVIDER: 'siliconflow', // 'openai' (whisper-1) or 'siliconflow' (SenseVoice)
  LLM_PROVIDER: 'openrouter', // 'openrouter' (gpt-5.6-luna, default), 'openai', 'openrouter-gemini', 'ark'
  TTS_PROVIDER: 'siliconflow', // 'siliconflow' (CosyVoice2, keep current)

  // ASR Configuration
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
  
  // LLM Configuration
  LLM_PROVIDERS: {
    // OpenRouter with a current cheap flagship chat model (default / recommended:
    // gpt-5.6* on OpenAI direct needs org verification, OpenRouter avoids that step).
    openrouter: {
      apiUrl: 'https://openrouter.ai/api/v1/chat/completions',
      model: 'openai/gpt-5.6-luna',
      apiKey: 'OPENROUTER_API_KEY'
    },
    openai: {
      apiUrl: 'https://api.openai.com/v1/chat/completions',
      model: 'gpt-5.6-luna',
      apiKey: 'OPENAI_API_KEY'
    },
    'openrouter-gpt4o': {
      apiUrl: 'https://openrouter.ai/api/v1/chat/completions',
      model: 'openai/gpt-4o',
      apiKey: 'OPENROUTER_API_KEY'
    },
    'openrouter-gemini': {
      apiUrl: 'https://openrouter.ai/api/v1/chat/completions',
      model: 'google/gemini-2.5-flash',
      apiKey: 'OPENROUTER_API_KEY'
    },
    ark: {
      apiUrl: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
      model: 'doubao-seed-1-6-flash-250615',
      apiKey: 'ARK_API_KEY'
    }
  },
  
  // TTS Configuration (keep current)
  TTS_PROVIDERS: {
    siliconflow: {
      apiUrl: 'https://api.siliconflow.cn/v1/audio/speech',
      model: 'FunAudioLLM/CosyVoice2-0.5B',
      voice: 'FunAudioLLM/CosyVoice2-0.5B:diana',
      apiKey: 'SILICONFLOW_API_KEY'
    }
  },
  
  // Legacy support (will be deprecated)
  LLM_MODEL: 'gpt-5.6-luna',
  LLM_API_URL: 'https://api.openai.com/v1/chat/completions',
  STT_API_URL: 'https://api.openai.com/v1/audio/transcriptions',
  STT_MODEL: 'whisper-1',
  TTS_API_URL: 'https://api.siliconflow.cn/v1/audio/speech',
  
  // Common Configuration
  VISION_MAX_TOKENS: 4096,
  
  // Silero VAD Configuration
  VAD_THRESHOLD: 0.5,                  // Speech probability threshold for Silero VAD (0.0 to 1.0)
  VAD_FRAME_LENGTH: 512,               // Frame length for VAD analysis (samples)
  VAD_MIN_SPEECH_DURATION: 250,        // Minimum speech duration in ms
  VAD_MAX_SILENCE_DURATION: 500,       // Maximum silence duration before ending speech in ms
  AUDIO_SAMPLE_RATE: 16000,            // Sample rate for audio processing (required for Silero VAD)
  AUDIO_CHUNK_SIZE: 4096,              // Audio chunk size for processing
  
  // Server Configuration
  LISTEN_PORT: 8848,
  LISTEN_HOST: '0.0.0.0',
  SYSTEM_PROMPT: 'You are a helpful AI assistant.',
  CANCEL_PLAYBACK_TIME_THRESHOLD: 3000,
};

module.exports = config;
