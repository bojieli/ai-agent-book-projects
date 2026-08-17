#!/usr/bin/env node
const axios = require('axios');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const config = require('./config');
const VoiceActivityDetector = require('./utils/vad');
const { ASRProviderFactory } = require('./utils/providers/asrProviders');
const { LLMProviderFactory } = require('./utils/providers/llmProviders');
const { sha256, validateExperimentEvidence } = require('./experiment_validation');

function arg(name, fallback) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

function requireCredential(name) {
  const value = process.env[name];
  if (!value || value.startsWith('your-')) throw new Error(`Required real credential is not set: ${name}`);
  return value;
}

function redact(value) {
  let text = String(value || '');
  for (const [name, secret] of Object.entries(process.env)) {
    if ((name.includes('KEY') || name.includes('TOKEN')) && secret) text = text.split(secret).join('[REDACTED]');
  }
  return text.replace(/\b(?:sk|ak)-[A-Za-z0-9_-]{12,}\b/g, '[REDACTED]').slice(0, 3000);
}

function parsePcmWav(filePath) {
  const raw = fs.readFileSync(filePath);
  if (raw.length < 44 || raw.subarray(0, 4).toString() !== 'RIFF' || raw.subarray(8, 12).toString() !== 'WAVE') {
    throw new Error('Input must be a PCM WAV file');
  }
  const format = raw.readUInt16LE(20);
  const channels = raw.readUInt16LE(22);
  const sampleRate = raw.readUInt32LE(24);
  const bits = raw.readUInt16LE(34);
  if (format !== 1 || channels !== 1 || sampleRate !== 16000 || bits !== 16) {
    throw new Error(`Expected PCM 16kHz mono 16-bit WAV; got format=${format}, channels=${channels}, sampleRate=${sampleRate}, bits=${bits}`);
  }
  return { raw, pcm: raw.subarray(44), channels, sampleRate, bits };
}

function wavBuffer(pcm, sampleRate = 16000) {
  const header = Buffer.alloc(44);
  header.write('RIFF', 0); header.writeUInt32LE(36 + pcm.length, 4); header.write('WAVE', 8);
  header.write('fmt ', 12); header.writeUInt32LE(16, 16); header.writeUInt16LE(1, 20);
  header.writeUInt16LE(1, 22); header.writeUInt32LE(sampleRate, 24);
  header.writeUInt32LE(sampleRate * 2, 28); header.writeUInt16LE(2, 32); header.writeUInt16LE(16, 34);
  header.write('data', 36); header.writeUInt32LE(pcm.length, 40);
  return Buffer.concat([header, pcm]);
}

function mediaProbe(filePath) {
  const output = execFileSync('ffprobe', [
    '-v', 'error', '-show_entries', 'format=duration,size,format_name', '-of', 'json', filePath,
  ], { encoding: 'utf8' });
  const format = JSON.parse(output).format || {};
  return {
    duration_seconds: Number(format.duration),
    size_bytes: Number(format.size),
    format_name: format.format_name,
  };
}

function commandVersion(command, args) {
  try {
    return execFileSync(command, args, { encoding: 'utf8' }).split('\n')[0].trim();
  } catch (_) {
    return null;
  }
}

function resolveWhisperPython(requested) {
  if (requested) return requested;
  const launcher = execFileSync('which', ['whisper'], { encoding: 'utf8' }).trim();
  const firstLine = fs.readFileSync(launcher, 'utf8').split('\n')[0];
  if (!firstLine.startsWith('#!')) throw new Error(`Cannot resolve Python from Whisper launcher: ${launcher}`);
  return firstLine.slice(2).trim();
}

function buildProvenance() {
  const dependencies = require('./package.json').dependencies || {};
  return {
    host: {
      platform: os.platform(),
      release: os.release(),
      architecture: os.arch(),
      cpu_model: os.cpus()[0]?.model || 'unknown',
      logical_cpu_count: os.cpus().length,
      total_memory_bytes: os.totalmem(),
    },
    runtime: {
      node: process.version,
      onnxruntime_node: dependencies['onnxruntime-node'] || null,
      axios: dependencies.axios || null,
      ffprobe: commandVersion('ffprobe', ['-version']),
    },
    timing_clock: 'process.hrtime.bigint monotonic clock',
  };
}

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function runVad(pcm, outputDir) {
  const detector = new VoiceActivityDetector({ maxSilenceDuration: 500 });
  await detector.initializationPromise;
  const started = process.hrtime.bigint();
  const events = [];
  const frameBytes = 512 * 2;
  try {
    for (let offset = 0; offset + frameBytes <= pcm.length; offset += frameBytes) {
      const frame = pcm.subarray(offset, offset + frameBytes);
      events.push(...await detector.processAudioChunk(frame));
      await sleep(32);
    }
  } finally {
    await detector.cleanup();
  }
  const endpoints = events.filter(event => event.type === 'speech_end');
  const ended = endpoints.sort((left, right) => right.audioData.length - left.audioData.length)[0];
  if (!ended) throw new Error('Silero did not observe a non-forced endpoint after 500 ms silence');
  const segmentPath = path.join(outputDir, 'vad_segment.wav');
  fs.writeFileSync(segmentPath, wavBuffer(ended.audioData));
  return {
    execution: 'real', mock: false, probe_only: false, fallback_used: false,
    implementation: 'Silero VAD ONNX',
    model: 'models/silero_vad.onnx',
    model_sha256: sha256(path.join(__dirname, 'models', 'silero_vad.onnx')),
    threshold: 0.5,
    max_silence_ms: 500,
    endpoint_detected: true,
    detected_endpoint_count: endpoints.length,
    selected_endpoint: 'longest detected speech segment',
    forced_endpoint: false,
    observed_trailing_silence_ms: ended.observedSilenceDuration,
    speech_duration_ms: ended.duration,
    latency_seconds: Number(process.hrtime.bigint() - started) / 1e9,
    segment_path: 'vad_segment.wav',
    segment_sha256: sha256(segmentPath),
    segment_bytes: fs.statSync(segmentPath).size,
  };
}

function runLocalWhisper(segmentPath, requestedPython, modelName) {
  const python = resolveWhisperPython(requestedPython);
  const script = [
    'import hashlib, json, pathlib, sys, time',
    'import torch, whisper',
    'audio, model_name = sys.argv[1], sys.argv[2]',
    'cache = pathlib.Path.home() / ".cache" / "whisper" / (model_name + ".pt")',
    'started = time.perf_counter()',
    'model = whisper.load_model(model_name)',
    'loaded = time.perf_counter()',
    'result = model.transcribe(audio, fp16=False, verbose=False)',
    'finished = time.perf_counter()',
    'payload = {"text": str(result.get("text") or "").strip(), "language": result.get("language") or "unknown",',
    ' "model_load_seconds": loaded-started, "inference_seconds": finished-loaded,',
    ' "python": sys.version.split()[0], "torch": torch.__version__, "whisper": getattr(whisper, "__version__", "unknown"),',
    ' "model_path": str(cache), "model_sha256": hashlib.sha256(cache.read_bytes()).hexdigest() if cache.exists() else None}',
    'print("EXPERIMENT_JSON=" + json.dumps(payload, ensure_ascii=False))',
  ].join('\n');
  const started = process.hrtime.bigint();
  const output = execFileSync(python, ['-c', script, segmentPath, modelName], {
    encoding: 'utf8', maxBuffer: 10 * 1024 * 1024,
  });
  const marker = output.split('\n').find(line => line.startsWith('EXPERIMENT_JSON='));
  if (!marker) throw new Error('Local Whisper returned no structured result');
  const result = JSON.parse(marker.slice('EXPERIMENT_JSON='.length));
  if (!result.text) throw new Error('Local Whisper returned an empty transcript');
  return {
    execution: 'real', mock: false, probe_only: false, fallback_used: false,
    provider: 'local-openai-whisper', model: `whisper-${modelName}`,
    inference_completed: true, api_request_completed: false, external_request: false,
    latency_seconds: Number(process.hrtime.bigint() - started) / 1e9,
    transcript: result.text, language: result.language,
    runtime: { python: result.python, torch: result.torch, openai_whisper: result.whisper },
    model_path: result.model_path, model_sha256: result.model_sha256,
    model_load_seconds: result.model_load_seconds,
    model_inference_seconds: result.inference_seconds,
    provider_reported_cost_usd: 0,
    cost_note: 'Local open-source Whisper inference; no external ASR charge.',
  };
}

async function runAsr(segmentPath, providerName, evidenceDir, options = {}) {
  if (providerName === 'local-whisper') {
    return runLocalWhisper(segmentPath, options.whisperPython, options.whisperModel || 'tiny');
  }
  const providerConfig = config.ASR_PROVIDERS[providerName];
  if (!providerConfig) throw new Error(`Unknown ASR provider: ${providerName}`);
  requireCredential(providerConfig.apiKey);
  const provider = ASRProviderFactory.createProvider(providerName, config, config);
  const pcm = parsePcmWav(segmentPath).pcm;
  const tempDir = path.join(evidenceDir, '.asr-temp');
  fs.mkdirSync(tempDir, { recursive: true });
  const started = process.hrtime.bigint();
  const result = await provider.transcribe(pcm, tempDir, {});
  fs.rmSync(tempDir, { recursive: true, force: true });
  if (!result.success || !String(result.text || '').trim()) throw new Error(`Real ASR failed: ${result.error || 'empty transcript'}`);
  return {
    execution: 'real', mock: false, probe_only: false, fallback_used: false,
    provider: providerName,
    model: providerConfig.model,
    inference_completed: true, api_request_completed: true, external_request: true,
    latency_seconds: Number(process.hrtime.bigint() - started) / 1e9,
    transcript: String(result.text).trim(),
    language: result.language || 'unknown',
    provider_request_id: result.requestId || null,
    provider_response_model: result.responseModel || providerConfig.model,
    billed_input_audio_seconds: mediaProbe(segmentPath).duration_seconds,
    provider_reported_cost_usd: null,
    cost_note: 'The transcription response did not expose a monetary charge; consult the provider billing ledger.',
  };
}

async function runLlm(transcript, providerName, requestedModel) {
  if (!config.LLM_PROVIDERS[providerName]) throw new Error(`Unknown LLM provider: ${providerName}`);
  const providerConfig = { ...config.LLM_PROVIDERS[providerName] };
  requireCredential(providerConfig.apiKey);
  if (requestedModel) providerConfig.model = requestedModel;
  const localConfig = { ...config, LLM_PROVIDERS: { ...config.LLM_PROVIDERS, [providerName]: providerConfig } };
  const provider = LLMProviderFactory.createProvider(providerName, localConfig, localConfig);
  const started = process.hrtime.bigint();
  const result = await provider.createChatCompletion([
    { role: 'system', content: 'Reply to the user in the same language using one short, natural sentence suitable for speech.' },
    { role: 'user', content: transcript },
  ], { max_tokens: 80, temperature: 0, stream_options: { include_usage: true } });
  if (!result.success) throw new Error(`Real LLM failed: ${result.error}`);
  let buffer = '', response = '', firstToken = null, usage = null, finishReason = null;
  for await (const chunk of result.response.data) {
    buffer += chunk.toString();
    const lines = buffer.split('\n'); buffer = lines.pop() || '';
    for (const line of lines) {
      if (!line.startsWith('data: ') || line.trim() === 'data: [DONE]') continue;
      const data = JSON.parse(line.slice(6));
      const piece = data.choices?.[0]?.delta?.content || '';
      if (piece && firstToken === null) firstToken = Number(process.hrtime.bigint() - started) / 1e9;
      response += piece;
      if (data.usage) usage = data.usage;
      if (data.choices?.[0]?.finish_reason) finishReason = data.choices[0].finish_reason;
    }
  }
  if (!response.trim() || firstToken === null) throw new Error('Real LLM stream returned no text');
  return {
    execution: 'real', mock: false, probe_only: false, fallback_used: false,
    provider: providerName, model: providerConfig.model, streamed: true,
    api_request_completed: true, external_request: true, first_token_seconds: firstToken,
    latency_seconds: Number(process.hrtime.bigint() - started) / 1e9,
    response: response.trim(),
    provider_request_id: result.response.headers?.['x-request-id'] || result.response.headers?.['request-id'] || null,
    finish_reason: finishReason,
    usage,
    provider_reported_cost_usd: usage?.cost != null && Number.isFinite(Number(usage.cost)) ? Number(usage.cost) : null,
    cost_note: usage?.cost == null ? 'The streamed response did not expose a monetary charge; consult the provider billing ledger.' : null,
  };
}

function resolveFishReferenceId(requested) {
  if (requested) return { id: requested, source: 'command line or FISH_TTS_REFERENCE_ID' };
  const manifestPath = path.resolve(__dirname, '..', '..', 'controllable-tts', 'reference_audio', 'manifest.json');
  if (!fs.existsSync(manifestPath)) {
    throw new Error('Fish TTS requires FISH_TTS_REFERENCE_ID or the authorized Experiment 6-6 reference manifest');
  }
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  if (!manifest.source_reference_id) throw new Error('Fish reference manifest has no source_reference_id');
  return { id: manifest.source_reference_id, source: path.relative(__dirname, manifestPath) };
}

function runFishTts(text, outputDir, options = {}) {
  requireCredential('FISH_API_KEY');
  const python = options.fishPython || resolveWhisperPython();
  const reference = resolveFishReferenceId(options.fishReferenceId);
  const outputPath = path.join(outputDir, 'assistant_response.mp3');
  const script = [
    'import json, os, pathlib, sys, time',
    'from fish_audio_sdk import Session, TTSRequest',
    'text, reference_id, output = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])',
    'started = time.perf_counter(); first = None; chunks = []',
    'for chunk in Session(os.environ["FISH_API_KEY"]).tts(TTSRequest(text=text, reference_id=reference_id, format="mp3"), backend="s1"):',
    '    if first is None: first = time.perf_counter() - started',
    '    chunks.append(chunk)',
    'output.write_bytes(b"".join(chunks)); finished = time.perf_counter() - started',
    'print("EXPERIMENT_JSON=" + json.dumps({"first_byte_seconds": first, "latency_seconds": finished, "bytes": output.stat().st_size}))',
  ].join('\n');
  const output = execFileSync(python, ['-c', script, text, reference.id, outputPath], {
    encoding: 'utf8', maxBuffer: 10 * 1024 * 1024,
  });
  const marker = output.split('\n').find(line => line.startsWith('EXPERIMENT_JSON='));
  if (!marker) throw new Error('Fish Audio returned no structured result');
  const result = JSON.parse(marker.slice('EXPERIMENT_JSON='.length));
  const probe = mediaProbe(outputPath);
  return {
    execution: 'real', mock: false, probe_only: false, fallback_used: false,
    provider: 'fish', model: 's1', voice: 'authorized zero-shot reference',
    api_request_completed: true, external_request: true,
    first_audio_byte_seconds: result.first_byte_seconds,
    latency_seconds: result.latency_seconds,
    output_path: 'assistant_response.mp3', output_sha256: sha256(outputPath),
    output_bytes: result.bytes, output_duration_seconds: probe.duration_seconds,
    output_format: probe.format_name,
    reference_id_sha256: crypto.createHash('sha256').update(reference.id).digest('hex'),
    reference_id_source: reference.source,
    billed_input_characters: [...text].length,
    provider_reported_cost_usd: null,
    cost_note: 'The Fish Audio SDK response did not expose a monetary charge; consult the provider billing ledger.',
  };
}

async function runTts(text, providerName, outputDir, options = {}) {
  if (providerName === 'fish') return runFishTts(text, outputDir, options);
  if (providerName !== 'siliconflow') throw new Error(`Unknown TTS provider: ${providerName}`);
  const providerConfig = config.TTS_PROVIDERS[providerName];
  const apiKey = requireCredential(providerConfig.apiKey);
  const started = process.hrtime.bigint();
  const response = await axios.post(providerConfig.apiUrl, {
    model: providerConfig.model, input: text, voice: providerConfig.voice,
    response_format: 'mp3', sample_rate: 32000, stream: true, speed: 1, gain: 0,
  }, {
    headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    responseType: 'stream', timeout: 120000,
  });
  let firstByte = null;
  const chunks = [];
  for await (const chunk of response.data) {
    if (firstByte === null) firstByte = Number(process.hrtime.bigint() - started) / 1e9;
    chunks.push(chunk);
  }
  const audio = Buffer.concat(chunks);
  const outputPath = path.join(outputDir, 'assistant_response.mp3');
  fs.writeFileSync(outputPath, audio);
  const probe = mediaProbe(outputPath);
  return {
    execution: 'real', mock: false, probe_only: false, fallback_used: false,
    provider: providerName, model: providerConfig.model, voice: providerConfig.voice,
    api_request_completed: response.status >= 200 && response.status < 300, external_request: true,
    first_audio_byte_seconds: firstByte,
    latency_seconds: Number(process.hrtime.bigint() - started) / 1e9,
    output_path: 'assistant_response.mp3', output_sha256: sha256(outputPath),
    output_bytes: audio.length, output_duration_seconds: probe.duration_seconds,
    output_format: probe.format_name,
    provider_request_id: response.headers?.['x-request-id'] || response.headers?.['request-id'] || null,
    billed_input_characters: [...text].length,
    provider_reported_cost_usd: null,
    cost_note: 'The speech response did not expose a monetary charge; consult the provider billing ledger.',
  };
}

function renderReport(e) {
  const a = e.acceptance;
  return `# Experiment 6-3 real traditional-voice validation\n\n` +
    `- Run ID: \`${e.run_id}\`\n- Complete: **${e.experiment_complete}**\n` +
    `- Source: \`${e.source_media.path}\` (${e.source_media.duration_seconds.toFixed(3)} s, saved browser microphone/WebSocket capture)\n` +
    `- VAD: Silero ONNX, 500 ms silence, non-forced endpoint = ${e.stages.vad.endpoint_detected}\n` +
    `- ASR: ${e.stages.asr.provider} / ${e.stages.asr.model}, ${e.stages.asr.latency_seconds.toFixed(3)} s\n` +
    `- Transcript: ${e.stages.asr.transcript}\n` +
    `- LLM: ${e.stages.llm.provider} / ${e.stages.llm.model}, TTFT ${e.stages.llm.first_token_seconds.toFixed(3)} s, total ${e.stages.llm.latency_seconds.toFixed(3)} s\n` +
    `- Response: ${e.stages.llm.response}\n` +
    `- TTS: ${e.stages.tts.provider} / ${e.stages.tts.model}, first byte ${e.stages.tts.first_audio_byte_seconds.toFixed(3)} s, total ${e.stages.tts.latency_seconds.toFixed(3)} s\n` +
    `- Post-endpoint time to first audio byte: ${e.latency.post_endpoint_to_first_audio_byte_seconds.toFixed(3)} s\n\n` +
    `## Strict gates\n\n${Object.entries(a.gates).map(([k,v]) => `- ${k}: **${v}**`).join('\n')}\n\n` +
    `${a.statement}\n`;
}

async function main() {
  const input = path.resolve(arg('--input', path.join(__dirname, 'recordings', 'recording_2025-02-06T14-51-38-205Z.wav')));
  const outputDir = path.resolve(arg('--output-dir', path.join(__dirname, 'validation', `real_pipeline_${new Date().toISOString().slice(0,10).replaceAll('-', '')}`)));
  const asrProvider = arg('--asr-provider', 'local-whisper');
  const whisperPython = arg('--whisper-python', process.env.WHISPER_PYTHON);
  const whisperModel = arg('--whisper-model', 'tiny');
  const llmProvider = arg('--llm-provider', 'openrouter-gemini');
  const llmModel = arg('--llm-model', config.LLM_PROVIDERS[llmProvider]?.model);
  const ttsProvider = arg('--tts-provider', 'fish');
  const fishPython = arg('--fish-python', process.env.FISH_PYTHON);
  const fishReferenceId = arg('--fish-reference-id', process.env.FISH_TTS_REFERENCE_ID);
  if (fs.existsSync(outputDir)) throw new Error(`Output directory already exists: ${outputDir}`);
  fs.mkdirSync(outputDir, { recursive: true });
  const wav = parsePcmWav(input);
  const sourceCopy = path.join(outputDir, 'microphone_input.wav');
  fs.copyFileSync(input, sourceCopy);
  const probe = mediaProbe(sourceCopy);
  const evidence = {
    schema_version: 1, experiment: '6-3', run_id: `exp6-3-${new Date().toISOString().replace(/[-:.]/g, '')}`,
    generated_at_utc: new Date().toISOString(), credentials_persisted: false,
    provenance: buildProvenance(),
    source_media: {
      path: 'microphone_input.wav', capture_method: 'browser_microphone_over_websocket',
      original_repository_path: path.relative(path.join(__dirname, '..'), input),
      sha256: sha256(sourceCopy), size_bytes: fs.statSync(sourceCopy).size,
      original_sha256: sha256(input),
      duration_seconds: probe.duration_seconds, sample_rate_hz: wav.sampleRate,
      channels: wav.channels, bits_per_sample: wav.bits,
      provenance_note: 'Existing real microphone capture saved by live-audio/backend/server.js; replayed through the production Silero class for reproducible validation.',
    }, stages: {}, experiment_complete: false,
  };
  try {
    evidence.stages.vad = await runVad(wav.pcm, outputDir);
    evidence.stages.asr = await runAsr(
      path.join(outputDir, evidence.stages.vad.segment_path), asrProvider, outputDir,
      { whisperPython, whisperModel },
    );
    evidence.stages.llm = await runLlm(evidence.stages.asr.transcript, llmProvider, llmModel);
    evidence.stages.tts = await runTts(
      evidence.stages.llm.response, ttsProvider, outputDir,
      { fishPython, fishReferenceId },
    );
    evidence.latency = {
      post_endpoint_to_first_audio_byte_seconds:
        evidence.stages.asr.latency_seconds + evidence.stages.llm.first_token_seconds + evidence.stages.tts.first_audio_byte_seconds,
      complete_serial_pipeline_seconds: ['vad','asr','llm','tts'].reduce((n,k) => n + evidence.stages[k].latency_seconds, 0),
      measurement_clock: 'process.hrtime.bigint monotonic clock',
    };
    evidence.cost = {
      paid_external_requests: [evidence.stages.asr, evidence.stages.llm, evidence.stages.tts]
        .filter(stage => stage.external_request === true).length,
      provider_reported_total_usd: [evidence.stages.asr, evidence.stages.llm, evidence.stages.tts]
        .map(stage => stage.provider_reported_cost_usd)
        .filter(value => Number.isFinite(value))
        .reduce((sum, value) => sum + value, 0),
      complete: [evidence.stages.asr, evidence.stages.llm, evidence.stages.tts]
        .every(stage => Number.isFinite(stage.provider_reported_cost_usd)),
      note: 'A zero total is not a zero-cost claim when complete=false; some providers omit per-request charges.',
    };
    evidence.acceptance = validateExperimentEvidence(evidence, outputDir);
    evidence.experiment_complete = evidence.acceptance.passed;
  } catch (error) {
    evidence.error = redact(error?.stack || error);
    evidence.acceptance = validateExperimentEvidence(evidence, outputDir);
  }
  fs.writeFileSync(path.join(outputDir, 'evidence.json'), JSON.stringify(evidence, null, 2) + '\n');
  if (evidence.experiment_complete) fs.writeFileSync(path.join(outputDir, 'report.md'), renderReport(evidence));
  console.log(`Evidence: ${path.join(outputDir, 'evidence.json')}`);
  if (!evidence.experiment_complete) throw new Error(evidence.error || 'Strict acceptance gates failed');
}

main().catch(error => { console.error(redact(error.message)); process.exit(1); });
