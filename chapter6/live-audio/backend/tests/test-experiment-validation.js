const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const { sha256, validateExperimentEvidence } = require('../experiment_validation');

function fixture(dir) {
  fs.writeFileSync(path.join(dir, 'input.wav'), Buffer.from('real-input'));
  fs.writeFileSync(path.join(dir, 'segment.wav'), Buffer.from('real-segment'));
  fs.writeFileSync(path.join(dir, 'output.mp3'), Buffer.alloc(2000, 1));
  const real = { execution: 'real', mock: false, probe_only: false, fallback_used: false, latency_seconds: 0.1 };
  return {
    schema_version: 1, experiment: '6-3',
    provenance: { host: { platform: 'test', architecture: 'test' }, runtime: { node: 'test', onnxruntime_node: 'test' } },
    source_media: { path: 'input.wav', capture_method: 'browser_microphone_over_websocket', sha256: sha256(path.join(dir, 'input.wav')), original_sha256: sha256(path.join(dir, 'input.wav')), sample_rate_hz: 16000, channels: 1, bits_per_sample: 16 },
    stages: {
      vad: { ...real, implementation: 'Silero VAD ONNX', model_sha256: 'abc', endpoint_detected: true, forced_endpoint: false, max_silence_ms: 500, observed_trailing_silence_ms: 512, segment_path: 'segment.wav', segment_sha256: sha256(path.join(dir, 'segment.wav')) },
      asr: { ...real, provider: 'openai', model: 'whisper-1', inference_completed: true, api_request_completed: true, transcript: 'hello' },
      llm: { ...real, provider: 'openai', model: 'gpt-real', api_request_completed: true, streamed: true, first_token_seconds: 0.1, response: 'Hi.' },
      tts: { ...real, provider: 'siliconflow', model: 'CosyVoice', api_request_completed: true, first_audio_byte_seconds: 0.1, output_path: 'output.mp3', output_sha256: sha256(path.join(dir, 'output.mp3')), output_bytes: 2000, output_duration_seconds: 1 },
    },
  };
}

describe('Experiment 6-3 strict evidence gates', () => {
  let dir;
  beforeEach(() => { dir = fs.mkdtempSync(path.join(os.tmpdir(), 'exp6-3-')); });
  afterEach(() => fs.rmSync(dir, { recursive: true, force: true }));

  it('accepts direct real media and all four real stages', () => {
    assert.strictEqual(validateExperimentEvidence(fixture(dir), dir).passed, true);
  });

  for (const field of ['mock', 'probe_only', 'fallback_used']) {
    it(`rejects a stage marked ${field}`, () => {
      const evidence = fixture(dir); evidence.stages.asr[field] = true;
      assert.strictEqual(validateExperimentEvidence(evidence, dir).passed, false);
    });
  }

  it('rejects a forced VAD flush and missing 500ms silence', () => {
    const evidence = fixture(dir);
    evidence.stages.vad.forced_endpoint = true;
    evidence.stages.vad.observed_trailing_silence_ms = 100;
    assert.strictEqual(validateExperimentEvidence(evidence, dir).passed, false);
  });

  it('rejects README claims without hashed output media', () => {
    const evidence = fixture(dir); evidence.stages.tts.output_sha256 = 'claimed-only';
    assert.strictEqual(validateExperimentEvidence(evidence, dir).passed, false);
  });

  it('rejects evidence without reproducibility provenance', () => {
    const evidence = fixture(dir); delete evidence.provenance.runtime.onnxruntime_node;
    assert.strictEqual(validateExperimentEvidence(evidence, dir).passed, false);
  });
});
