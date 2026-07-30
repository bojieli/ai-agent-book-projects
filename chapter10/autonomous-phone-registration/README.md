# Experiment 10-5 · Autonomous phone/browser orchestration

This companion implements the experiment as written. A real Playwright Computer Use Agent opens an arbitrary registration URL and inspects the rendered form. A real LLM sees the page observation, known user context, and an optional `initiate_phone_call_agent(purpose, required_info)` tool. With `tool_choice=auto`, the model—not a Python field-count rule—decides whether to spawn a Phone Agent.

The exact acceptance transport is one real outbound Twilio PSTN call (`--phone-transport twilio`, the default). Twilio `Say` and speech `Gather` provide live TTS/ASR while the call remains open. `--phone-transport local` provides an OpenAI TTS → speaker → microphone → OpenAI ASR development path. `--scripted-json` is only a unit/integration supplement and is explicitly labelled non-acceptance in program output.

## Exact concurrency and failure behavior

- Phone and Computer Agents run as independent `asyncio` tasks with separate loops.
- Each valid spoken value immediately emits `info_collected`; the Phone Agent asks the next question without awaiting `field_filled`.
- The Computer Agent fills the actual page concurrently. `timing_evidence.overlap_checks` proves whether “ask next” preceded the prior fill completion.
- HTML types, patterns, options, and format hints become `FieldSpec` validators. Invalid speech emits `format_invalid`, gives precise feedback, and is re-asked up to three times.
- Page/selector errors are returned as `fill_error`; submission is blocked when any error remains.
- Any unexpected Phone/Computer exception cancels the still-running peer, closes the
  phone transport, and then lets the top-level `finally` close the browser. The Twilio
  close operation is idempotent on normal and exceptional exits.
- `--submit` is opt-in so a demonstration cannot accidentally create an account.
- The decision and every message timestamp are written to JSON. Spoken personal values are redacted from console and disk traces.

## Setup and real PSTN run

```bash
cd chapter10/autonomous-phone-registration
pip install -r requirements.txt
playwright install chromium
cp env.example .env

# Expose localhost:8765 through an HTTPS tunnel, put its public origin in
# TWILIO_WEBHOOK_BASE_URL, then run:
python demo.py --confirm-consent --url 'https://your-site.example/register'
```

Twilio requires `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, a Twilio caller number, the user's consented destination number, and a public HTTPS webhook. Request signatures are validated before any speech result enters the Agent bus.
The program refuses to place the call unless `--confirm-consent` is present.
The focused suite verifies that refusal occurs before constructing the browser or live
audio channel; it does not place a test call or open a microphone.

Local live-audio development:

```bash
python demo.py --confirm-consent --phone-transport local --url 'https://demoqa.com/automation-practice-form'
```

Automated supplement (not voice acceptance):

```bash
pytest -q
python demo.py --headless --scripted-json '{"firstName":"Alice","lastName":"Tan","gender":"Female","userNumber":"9123456789"}'
```

The companion was rechecked against the real DemoQA form and a real ARK tool-calling
endpoint after the focused fixes: 13 controls were discovered, the model autonomously
called the Phone Agent tool, four required fields were filled, all three adjacent
question/fill intervals overlapped, and the browser closed. A live call still requires
working caller credentials and a consenting human at runtime.

Machine-readable evidence is committed under [`validation/`](validation/). The real browser/LLM artifact marks those gates `pass`, but marks PSTN and ASR/TTS `not_run` and the overall status `incomplete`; scripted values are redacted and explicitly non-acceptance.
The same artifact marks real form submission `not_run`: the focused suite proves that
`task_completed` triggers exactly one submission when the browser is explicitly opted
in, but this audit was not authorized to create an external form/account side effect.

---

## 中文说明

本项目完整实现实验 10-5：Playwright Computer Use Agent 先访问真实注册页并读取表单；真实 LLM 在 `tool_choice=auto` 下自主决定是否调用 `initiate_phone_call_agent(purpose, required_info)`，代码没有用“字段数大于 N”代替模型决策。

默认 `twilio` 路径会真正拨打一次 PSTN 电话，通过 Twilio `Say`/speech `Gather` 完成 TTS/ASR；`local` 路径用于本机麦克风联调。Phone Agent 每拿到一个有效值就立即发给 Computer Agent，然后直接问下一项，不等待网页填写完成。消息时间线会客观记录“问一个、填一个”的并行重叠。格式错误会反馈并重新询问，页面错误会阻止提交。个人字段值不会写入日志。
