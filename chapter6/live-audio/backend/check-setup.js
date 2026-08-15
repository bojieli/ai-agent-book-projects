#!/usr/bin/env node

/**
 * check-setup.js — Headless environment verifier for the Live Voice Chat demo (实验 9-1).
 *
 * Runs WITHOUT any API keys, microphone, or browser. It only checks that the
 * local prerequisites for the cascaded VAD -> ASR -> LLM -> TTS pipeline are in
 * place, and reports which providers you have credentials for, so a reader can
 * confirm their setup before opening the browser UI.
 *
 * Usage:
 *   node check-setup.js
 *
 * Exit code 0 means the backend can start; non-zero means a hard prerequisite
 * (Node version, VAD model, or a loadable config) is missing.
 */

const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

let hardFailures = 0;
let warnings = 0;

const ok = (msg) => console.log(`  ✅ ${msg}`);
const warn = (msg) => { console.log(`  ⚠️  ${msg}`); warnings++; };
const fail = (msg) => { console.log(`  ❌ ${msg}`); hardFailures++; };

console.log('🔍 Live Voice Chat — setup check (实验 9-1)');
console.log('='.repeat(60));

// 1. Node version (README requires v16+)
console.log('\nNode.js runtime:');
const major = parseInt(process.versions.node.split('.')[0], 10);
if (major >= 16) {
  ok(`Node ${process.version} (>= v16 required)`);
} else {
  fail(`Node ${process.version} is too old; v16 or higher is required`);
}

// 2. FFmpeg (used by server.js to convert incoming audio for ASR)
console.log('\nFFmpeg (audio format conversion):');
try {
  const out = execFileSync('ffmpeg', ['-version'], { encoding: 'utf8' });
  ok(`ffmpeg found: ${out.split('\n')[0]}`);
} catch (e) {
  fail('ffmpeg not found on PATH. Install it (e.g. `brew install ffmpeg`) — see README.');
}

// 3. Silero VAD model file
console.log('\nSilero VAD model:');
const modelPath = path.join(__dirname, 'models', 'silero_vad.onnx');
if (fs.existsSync(modelPath)) {
  const kb = (fs.statSync(modelPath).size / 1024).toFixed(0);
  ok(`silero_vad.onnx present (${kb} KB)`);
} else {
  fail(`Missing ${modelPath}. Download it — see README "Download the Silero VAD model".`);
}

// 4. Config loads, and report selected providers + key availability
console.log('\nConfiguration & providers:');
let config;
try {
  config = require('./config');
  ok('config.js loaded');
} catch (e) {
  fail(`config.js failed to load: ${e.message}`);
}

if (config) {
  // Map each selected provider to the env var its credentials come from.
  const keyFor = {
    asr: (config.ASR_PROVIDERS[config.ASR_PROVIDER] || {}).apiKey,
    llm: (config.LLM_PROVIDERS[config.LLM_PROVIDER] || {}).apiKey,
    tts: (config.TTS_PROVIDERS[config.TTS_PROVIDER] || {}).apiKey,
  };

  const stageLine = (stage, provider, envVar) => {
    if (!provider || !envVar) {
      fail(`${stage.toUpperCase()}: provider "${provider}" is not defined in config.js`);
      return;
    }
    const val = process.env[envVar];
    const placeholder = !val || /your-.*-api-key-here/.test(val);
    if (placeholder) {
      warn(`${stage.toUpperCase()}: provider "${provider}" selected, but ${envVar} is not set`);
    } else {
      ok(`${stage.toUpperCase()}: provider "${provider}" ready (${envVar} set)`);
    }
  };

  stageLine('asr', config.ASR_PROVIDER, keyFor.asr);
  stageLine('llm', config.LLM_PROVIDER, keyFor.llm);
  stageLine('tts', config.TTS_PROVIDER, keyFor.tts);

  console.log('\nServer will listen on:');
  ok(`ws://${config.LISTEN_HOST}:${config.LISTEN_PORT} (WebSocket) — frontend must use WEBSOCKET_PORT=${config.LISTEN_PORT}`);
}

// Summary
console.log('\n' + '='.repeat(60));
if (hardFailures === 0 && warnings === 0) {
  console.log('✅ Setup looks good. Start the backend with: npm start');
} else if (hardFailures === 0) {
  console.log(`⚠️  Prerequisites OK, but ${warnings} provider key(s) missing.`);
  console.log('   The backend will start; set the missing API key(s) before recording.');
} else {
  console.log(`❌ ${hardFailures} hard prerequisite(s) missing — fix these before running the backend.`);
}

process.exit(hardFailures === 0 ? 0 : 1);
