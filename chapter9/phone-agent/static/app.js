const $ = (selector) => document.querySelector(selector);

const state = {
  callId: null,
  plan: null,
  pc: null,
  dc: null,
  stream: null,
  statsTimer: null,
  remoteAudioTrack: false,
  localAudioTrack: false,
  lastStats: null,
};

function mode() {
  return document.querySelector('input[name="mode"]:checked').value;
}

function setStatus(value) {
  $('#status').textContent = value;
  document.body.dataset.status = value;
}

function appendTurn(speaker, text) {
  if (!text) return;
  const p = document.createElement('p');
  p.className = 'turn';
  const b = document.createElement('b');
  b.textContent = speaker === 'agent' ? 'Agent: ' : 'You: ';
  p.append(b, document.createTextNode(text));
  $('#transcript').appendChild(p);
  $('#transcript').scrollTop = $('#transcript').scrollHeight;
}

async function jsonFetch(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {'Content-Type': 'application/json', ...(options.headers || {})},
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
  return data;
}

async function saveEvent(event) {
  if (!state.callId) return;
  try {
    await jsonFetch(`/api/calls/${state.callId}/events`, {
      method: 'POST',
      body: JSON.stringify({event}),
    });
  } catch (error) {
    console.warn('event receipt failed', error);
  }
}

function send(event) {
  if (!state.dc || state.dc.readyState !== 'open') throw new Error('data channel is not open');
  state.dc.send(JSON.stringify(event));
}

async function publishReady() {
  if (!state.pc) return;
  const open = state.dc?.readyState === 'open';
  const connected = ['connected', 'completed'].includes(state.pc.iceConnectionState);
  $('#transport').textContent = `WebRTC · ICE ${state.pc.iceConnectionState} · data ${state.dc?.readyState || 'new'}`;
  if (open && connected) setStatus('connected');
  await saveEvent({
    type: 'rtc.ready',
    ice_connection_state: state.pc.iceConnectionState,
    data_channel_open: open,
    local_audio_track: state.localAudioTrack,
    remote_audio_track: state.remoteAudioTrack,
  });
}

async function collectStats() {
  if (!state.pc) return null;
  const totals = {
    type: 'rtc.stats',
    ice_connection_state: state.pc.iceConnectionState,
    inbound_packets: 0,
    inbound_bytes: 0,
    outbound_packets: 0,
    outbound_bytes: 0,
  };
  const reports = await state.pc.getStats();
  reports.forEach((report) => {
    const kind = report.kind || report.mediaType;
    if (kind !== 'audio') return;
    if (report.type === 'inbound-rtp' && !report.isRemote) {
      totals.inbound_packets += report.packetsReceived || 0;
      totals.inbound_bytes += report.bytesReceived || 0;
    }
    if (report.type === 'outbound-rtp' && !report.isRemote) {
      totals.outbound_packets += report.packetsSent || 0;
      totals.outbound_bytes += report.bytesSent || 0;
    }
  });
  state.lastStats = totals;
  await saveEvent(totals);
  return totals;
}

async function handleServerEvent(event) {
  if (event.type === 'agent.message') {
    appendTurn('agent', event.text);
    if ('speechSynthesis' in window) {
      window.speechSynthesis.speak(new SpeechSynthesisUtterance(event.text));
    }
  }
  if (event.type === 'tool.result') {
    $('#evidence').textContent = JSON.stringify(event, null, 2);
  }
  if (event.type === 'error') {
    setStatus('error');
    $('#evidence').textContent = JSON.stringify(event.error || event, null, 2);
  }
}

function createRequest() {
  if (mode() === 'react') return {mode: 'react', task: $('#task').value};
  return {
    mode: 'direct',
    callee_name: $('#callee-name').value,
    goal: $('#goal').value,
    context: $('#context').value,
    instructions: $('#instructions').value,
  };
}

async function startCall() {
  $('#start').disabled = true;
  setStatus('planning');
  try {
    const created = await jsonFetch('/api/calls', {method: 'POST', body: JSON.stringify(createRequest())});
    state.callId = created.call_id;
    state.plan = created.plan;
    $('#call-id').textContent = state.callId;
    $('#evidence').textContent = JSON.stringify({plan: state.plan}, null, 2);

    const pc = new RTCPeerConnection();
    state.pc = pc;
    const audio = $('#remote-audio');
    pc.ontrack = async (event) => {
      audio.srcObject = event.streams[0];
      state.remoteAudioTrack = event.track.kind === 'audio';
      try { await audio.play(); } catch (error) { console.warn('autoplay pending', error); }
      await publishReady();
    };
    pc.oniceconnectionstatechange = publishReady;
    pc.onconnectionstatechange = publishReady;

    setStatus('requesting microphone');
    state.stream = await navigator.mediaDevices.getUserMedia({audio: true});
    const track = state.stream.getAudioTracks()[0];
    if (!track) throw new Error('no microphone audio track was returned');
    state.localAudioTrack = true;
    pc.addTrack(track, state.stream);

    const dc = pc.createDataChannel('oai-events');
    state.dc = dc;
    dc.onmessage = (message) => handleServerEvent(JSON.parse(message.data)).catch(console.error);
    dc.onclose = publishReady;
    dc.onopen = async () => {
      await publishReady();
      send({type: 'client.ready'});
      $('#text-turn button[type="submit"]').disabled = false;
      if (window.SpeechRecognition || window.webkitSpeechRecognition) $('#speak-turn').disabled = false;
    };

    setStatus('negotiating');
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    const answerResponse = await fetch(`/api/calls/${state.callId}/session`, {
      method: 'POST',
      headers: {'Content-Type': 'application/sdp'},
      body: offer.sdp,
    });
    const answerSdp = await answerResponse.text();
    if (!answerResponse.ok) throw new Error(answerSdp);
    await pc.setRemoteDescription({type: 'answer', sdp: answerSdp});
    state.statsTimer = setInterval(() => collectStats().catch(console.warn), 750);
    $('#hangup').disabled = false;
  } catch (error) {
    setStatus('error');
    $('#evidence').textContent = String(error);
    $('#start').disabled = false;
    throw error;
  }
}

async function sendText(text) {
  const cleaned = text.trim();
  if (!cleaned) return;
  appendTurn('user', cleaned);
  send({type: 'user.message', text: cleaned});
}

async function hangup(reason = 'user_hangup') {
  if (!state.callId) return null;
  if (state.statsTimer) clearInterval(state.statsTimer);
  await collectStats();
  state.stream?.getTracks().forEach((track) => track.stop());
  state.dc?.close();
  state.pc?.close();
  const record = await jsonFetch(`/api/calls/${state.callId}/finish`, {
    method: 'POST',
    body: JSON.stringify({reason}),
  });
  setStatus(record.acceptance.passed ? 'completed' : 'ended');
  $('#evidence').textContent = JSON.stringify(record, null, 2);
  $('#hangup').disabled = true;
  $('#text-turn button[type="submit"]').disabled = true;
  $('#speak-turn').disabled = true;
  return record;
}

document.querySelectorAll('input[name="mode"]').forEach((radio) => {
  radio.addEventListener('change', () => {
    const react = mode() === 'react';
    $('#react-fields').hidden = !react;
    $('#direct-fields').hidden = react;
  });
});
$('#start').addEventListener('click', () => startCall().catch(console.error));
$('#hangup').addEventListener('click', () => hangup().catch(console.error));
$('#text-turn').addEventListener('submit', async (event) => {
  event.preventDefault();
  const input = $('#user-text');
  const text = input.value;
  input.value = '';
  await sendText(text);
});
$('#speak-turn').addEventListener('click', () => {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) return;
  const recognition = new Recognition();
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.onresult = (event) => sendText(event.results[0][0].transcript).catch(console.error);
  recognition.onerror = (event) => { $('#evidence').textContent = `Speech recognition error: ${event.error}`; };
  recognition.start();
});

window.exp92 = {state, startCall, sendText, hangup, collectStats};

const params = new URLSearchParams(window.location.search);
if (params.get('mode') === 'direct') {
  document.querySelector('input[name="mode"][value="direct"]').click();
}
const queryFields = {
  task: '#task',
  callee_name: '#callee-name',
  goal: '#goal',
  context: '#context',
  instructions: '#instructions',
};
Object.entries(queryFields).forEach(([key, selector]) => {
  if (params.has(key)) $(selector).value = params.get(key);
});
