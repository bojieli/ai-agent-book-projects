const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

function sha256(filePath) {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function isRealStage(stage) {
  return Boolean(
    stage &&
    stage.execution === 'real' &&
    stage.mock !== true &&
    stage.probe_only !== true &&
    stage.fallback_used !== true
  );
}

function validateExperimentEvidence(evidence, evidenceDir) {
  const source = evidence?.source_media || {};
  const vad = evidence?.stages?.vad || {};
  const asr = evidence?.stages?.asr || {};
  const llm = evidence?.stages?.llm || {};
  const tts = evidence?.stages?.tts || {};

  const sourcePath = source.path ? path.resolve(evidenceDir, source.path) : '';
  const segmentPath = vad.segment_path ? path.resolve(evidenceDir, vad.segment_path) : '';
  const outputPath = tts.output_path ? path.resolve(evidenceDir, tts.output_path) : '';
  const sourceAuthentic = Boolean(
    source.capture_method === 'browser_microphone_over_websocket' &&
    sourcePath && fs.existsSync(sourcePath) &&
    source.sha256 === sha256(sourcePath) &&
    source.sample_rate_hz === 16000 &&
    source.channels === 1 &&
    source.bits_per_sample === 16
  );
  const segmentAuthentic = Boolean(
    segmentPath && fs.existsSync(segmentPath) && vad.segment_sha256 === sha256(segmentPath)
  );
  const outputAuthentic = Boolean(
    outputPath && fs.existsSync(outputPath) && tts.output_sha256 === sha256(outputPath) &&
    Number(tts.output_bytes) > 1000 && Number(tts.output_duration_seconds) > 0
  );

  const gates = {
    schema_and_scope: evidence?.schema_version === 1 && evidence?.experiment === '6-3',
    real_websocket_microphone_media: sourceAuthentic,
    real_silero_vad_endpoint: Boolean(
      isRealStage(vad) &&
      vad.implementation === 'Silero VAD ONNX' &&
      vad.model_sha256 &&
      vad.endpoint_detected === true &&
      vad.forced_endpoint === false &&
      Number(vad.max_silence_ms) === 500 &&
      Number(vad.observed_trailing_silence_ms) >= 500 &&
      segmentAuthentic
    ),
    real_asr: Boolean(
      isRealStage(asr) && asr.inference_completed === true &&
      asr.provider && asr.model && String(asr.transcript || '').trim()
    ),
    real_streaming_llm: Boolean(
      isRealStage(llm) && llm.api_request_completed === true && llm.streamed === true &&
      llm.provider && llm.model && Number(llm.first_token_seconds) > 0 &&
      String(llm.response || '').trim()
    ),
    real_tts_media: Boolean(
      isRealStage(tts) && tts.api_request_completed === true &&
      tts.provider && tts.model && Number(tts.first_audio_byte_seconds) > 0 && outputAuthentic
    ),
    measured_stage_latencies: ['vad', 'asr', 'llm', 'tts'].every(
      name => Number(evidence?.stages?.[name]?.latency_seconds) > 0
    ),
    provenance_complete: Boolean(
      evidence?.provenance?.host?.platform &&
      evidence?.provenance?.host?.architecture &&
      evidence?.provenance?.runtime?.node &&
      evidence?.provenance?.runtime?.onnxruntime_node &&
      source.original_sha256 === source.sha256
    ),
    no_mock_probe_or_fallback: [vad, asr, llm, tts].every(isRealStage),
  };
  return {
    gates,
    passed: Object.values(gates).every(Boolean),
    statement: 'Passing proves one saved real microphone turn completed Silero VAD -> real ASR -> real LLM -> real TTS. It does not benchmark concurrency or production load.',
  };
}

module.exports = { sha256, validateExperimentEvidence };
