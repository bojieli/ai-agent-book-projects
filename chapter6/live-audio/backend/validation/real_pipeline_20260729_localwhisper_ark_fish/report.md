# Experiment 6-3 real traditional-voice validation

- Run ID: `exp6-3-20260729T153334474Z`
- Complete: **true**
- Source: `microphone_input.wav` (5.056 s, saved browser microphone/WebSocket capture)
- VAD: Silero ONNX, 500 ms silence, non-forced endpoint = true
- ASR: local-openai-whisper / whisper-tiny, 2.710 s
- Transcript: 是男朋友叫这样的
- LLM: ark / doubao-seed-1-6-flash-250615, TTFT 0.749 s, total 0.792 s
- Response: 那是男朋友叫这样的呀
- TTS: fish / s1, first byte 2.819 s, total 3.279 s
- Post-endpoint time to first audio byte: 6.279 s

## Strict gates

- schema_and_scope: **true**
- real_websocket_microphone_media: **true**
- real_silero_vad_endpoint: **true**
- real_asr: **true**
- real_streaming_llm: **true**
- real_tts_media: **true**
- measured_stage_latencies: **true**
- provenance_complete: **true**
- no_mock_probe_or_fallback: **true**

Passing proves one saved real microphone turn completed Silero VAD -> real ASR -> real LLM -> real TTS. It does not benchmark concurrency or production load.
