# Experiment 10-5 · Autonomous phone/browser orchestration

This companion implements the experiment as written. A real Playwright Computer Use Agent opens an arbitrary registration URL and inspects the rendered form. A real LLM sees the page observation, known user context, and an optional `initiate_phone_call_agent(purpose, required_info)` tool. With `tool_choice=auto`, the model—not a Python field-count rule—decides whether to spawn a Phone Agent.

The default transport is a private local WebRTC call (`--phone-transport webrtc`). It opens a participant page, negotiates an offer/answer pair, and carries agent and participant audio on two RTP tracks. Agent prompts also cross a data channel as non-sensitive captions; answers never use that channel. The remote peer records the participant track ephemerally for ASR, then discards both media and transcript. No E.164 number, PSTN provider, tunnel, or public webhook is required. The old Twilio and direct-microphone transports remain optional.

## Exact concurrency and failure behavior

- Phone and Computer Agents run as independent `asyncio` tasks with separate loops.
- Each valid spoken value immediately emits `info_collected`; the Phone Agent asks the next question without awaiting `field_filled`.
- The Computer Agent fills the actual page concurrently. `timing_evidence.overlap_checks` proves whether “ask next” preceded the prior fill completion.
- HTML types, patterns, options, and format hints become `FieldSpec` validators. Invalid speech emits `format_invalid`, gives precise feedback, and is re-asked up to three times.
- Page/selector errors are returned as `fill_error`; submission is blocked when any error remains.
- Any unexpected Phone/Computer exception cancels the still-running peer, closes the
  call and all media tracks, and then lets the top-level `finally` close the browser.
  Cleanup is idempotent on normal and exceptional exits.
- `--submit` is opt-in so a demonstration cannot accidentally create an account.
- The decision and every message timestamp are written to JSON. Spoken personal values are redacted from console and disk traces.

## Setup and local WebRTC call

```bash
cd chapter10/autonomous-phone-registration
pip install -r requirements.txt
playwright install chromium
cp env.example .env

python demo.py --confirm-consent --url 'https://your-site.example/register'
```

The command opens both the target form and a local participant call page. Speak after
each question, then click **Finish answer**. Localhost is a browser secure context, so
microphone access works without a certificate. The program refuses to open any live
audio path unless `--confirm-consent` is present; the focused suite verifies that the
refusal occurs before constructing a browser or media channel.

Speech provider selection is independent of WebRTC. `WEBRTC_SPEECH_PROVIDER=auto`
prefers local `say`/`espeak` TTS plus Gemini ASR when those are configured, otherwise
it uses OpenAI TTS/ASR. `local-whisper` keeps both stages local and requires
`openai-whisper` plus a cached/downloadable checkpoint:

```bash
WEBRTC_SPEECH_PROVIDER=local-whisper \
WHISPER_PYTHON=/path/to/python-with-whisper \
WHISPER_MODEL=tiny \
python demo.py --confirm-consent --url 'https://your-site.example/register'
```

`--submit` remains an explicit opt-in. Without it, the agents fill and validate the
form but do not create an account. The full acceptance runner submits only to its own
localhost endpoint.

Optional legacy transports:

```bash
python demo.py --confirm-consent --phone-transport local --url 'https://demoqa.com/automation-practice-form'
python demo.py --confirm-consent --phone-transport twilio --url 'https://demoqa.com/automation-practice-form'
```

## Tests and full acceptance

```bash
pytest -q

# Real LLM + Playwright + WebRTC/RTP + TTS/ASR + localhost submission.
# Values are safe synthetic data; they still cross the audio media path and ASR.
WEBRTC_SPEECH_PROVIDER=local-whisper \
WHISPER_PYTHON=/path/to/python-with-whisper \
python run_acceptance.py
```

The formal 2026-07-31 run is committed at
[`validation/runs/exp10-5-webrtc-20260731-v7/`](validation/runs/exp10-5-webrtc-20260731-v7/).
A real ARK response (ID and usage retained) autonomously selected six required fields.
The call completed one offer, one answer, seven media recordings, 9 TTS turns and 7
local Whisper turns. Both RTP directions carried packets and bytes. A deliberately
invalid spoken email caused `format_invalid` and a second question; all five adjacent
ask/fill intervals overlapped; exactly one redacted six-field submission reached the
localhost endpoint. All 9 acceptance gates pass. The manifest binds the runtime and
artifacts with SHA-256 hashes, and the secret/value scan is empty.

This run uses a safe synthesized participant so it is automated and reproducible. It
proves the real media, ASR, orchestration, validation, privacy, and submission paths;
it is not a human usability study or a test of TURN/NAT traversal. A human call uses
the same WebRTC path with `--webrtc-answers-json` omitted.

---

## 中文说明

本项目完整实现实验 10-5：Playwright Computer Use Agent 先访问真实注册页并读取表单；真实 LLM 在 `tool_choice=auto` 下自主决定是否调用 `initiate_phone_call_agent(purpose, required_info)`，代码没有用“字段数大于 N”代替模型决策。

默认路径现在是本机浏览器 WebRTC 通话，不需要手机号、PSTN 服务商、公开 webhook 或隧道。页面会完成真实 offer/answer，并用双向 RTP 音轨传输 Agent 语音和用户麦克风；回答只从远端音轨的临时录音进入 ASR，不会通过文本通道旁路，也不会保留原始音频或 transcript。Phone Agent 每拿到一个有效值就立即发给 Computer Agent，然后直接问下一项，不等待网页填写完成；格式错误会反馈并重问，页面错误会阻止提交，`--submit` 仍须显式授权。

正式 v7 验收以安全合成参与者跑通真实 ARK 自主工具调用、Playwright、WebRTC/RTP、本机 TTS、真实本机 Whisper ASR、格式重问、问填并行和一次 localhost 表单提交：9/9 门禁通过，源码与产物 hash 均已固定，日志中只保留 `<redacted>`。这证明完整技术链路，不等同于真人可用性或跨 NAT/TURN 测试；省略 `--webrtc-answers-json` 即进入同一媒体路径的真人麦克风模式。
