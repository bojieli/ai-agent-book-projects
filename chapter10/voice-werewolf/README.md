# Experiment 10-8 · Voice Werewolf with a real-LLM user simulator

The experiment supports two first-class user seats: a consenting live human, or an independent real-LLM user simulator for unattended end-to-end testing. Both use the same seeded role shuffle and protected private memory in a 6–8 seat game with two Werewolves, one Seer, one Witch, and Villagers. The code-driven Judge—not an LLM—owns the state machine, night/day/vote phases, skill inventory, deaths, and deterministic win rule.

## Automated user simulator

`python demo.py --simulate-user` does not insert canned answers or turn the user into an ordinary omniscient AI player:

1. The simulator receives only the private and public memory authorized for its randomized seat.
2. A separately configurable real LLM must call the sole legal tool for the turn: `speak_publicly` or `choose_player`.
3. The chosen utterance is synthesized into a real waveform. The automatic provider order is OpenAI Audio, local `espeak` plus OpenRouter native-audio ASR, then local `espeak` plus Gemini ASR.
4. The game consumes only the real ASR transcript. It never receives the LLM's pre-audio utterance directly.
5. For skills and votes, the parsed ASR action must exactly equal the tool-selected action; a mismatch fails closed and is retained as `simulator_action_mismatch`.

The OpenRouter speech path records response IDs, provider-reported models, token usage (including nonzero audio tokens), audio hashes, transcripts, and latency without retaining credentials. The local synthesizer is a real audio component rather than an API; both the user reasoning call and audio transcription call are real external model APIs.

## Live two-way voice

`python demo.py` is no longer an all-AI text demonstration. It creates a real human seat and a `LiveVoiceSession`:

1. AI/Judge speech is sent to a real OpenAI TTS endpoint and played immediately.
2. Human speech is captured from the microphone with energy VAD and end-of-speech silence detection.
3. Captured WAV audio is sent to a real OpenAI ASR endpoint.
4. Spoken player numbers drive human night skills and voting; daytime speech is broadcast to every Agent context.
5. During public AI speech, microphone activity cancels playback, transcribes the barge-in, and records it as a public interruption turn. Headphones are recommended to prevent acoustic echo from triggering the detector.

Audio files and a timestamped `voice_trace.json` record TTS, ASR latency, and interruptions. `--no-interruptions` disables barge-in for noisy rooms.

## Information asymmetry and strategy acceptance

Every player owns a separate `memory`. The Judge has only three delivery capabilities: public broadcast, single-player private send, and Werewolf-team send. The same boundary applies to both kinds of user seat. The post-game audit proves Werewolf teammates never enter good-player contexts, Seer investigations enter only the Seer context, and all public events reach everyone.

The game also records role-labelled actions and runs a real LLM post-game acceptance judge over four explicit criteria: Werewolf concealment, Seer reveal timing/evidence, Villager evidence-based reasoning, and general role consistency. It quotes logged evidence and may return `insufficient`; it cannot substitute an Agent's unsupported claim for observed actions.
The returned JSON is schema-checked: all four named criteria need a valid
`pass|fail|insufficient` status, and every passing criterion needs evidence. A bare
model claim of `overall_pass: true` cannot pass the gate.

`artifacts/acceptance_report.json` records:

- exactly one user seat, its kind, and its randomized role;
- exact role counts and player count;
- completed night–day–vote cycles and deterministic winner;
- privacy audit result;
- real strategy audit;
- whether real LLM tools, TTS, ASR, and action agreement occurred, plus barge-in count for a human run.

The end-to-end result requires 6–8 players, the exact role mix, one protected user seat, privacy pass, observed ASR + TTS, a rule-based winner, and—on the simulator path—real tool calls and matching audio-round-trip actions. The stricter experiment-wide result additionally requires at least three complete cycles and all four strategy criteria in the same run.
The Judge increments the cycle counter only after night, day discussion, and voting all
finish. Reaching the safety round limit without a rule-based winner is reported as
`未决`, not silently awarded to either faction, and therefore cannot pass acceptance.

## Run

```bash
# From the repository root: use the shared Chapter 10 environment
uv sync --locked --python 3.12 --extra ch10

# Activate it before changing directories:
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

# pip fallback when uv is not installed:
# python -m pip install -e ".[ch10]"

cd chapter10/voice-werewolf

# Single-project compatibility path, still supported during migration:
# python -m pip install -r requirements.txt

cp env.example .env
python demo.py --simulate-user \
  --model google/gemini-2.5-flash \
  --simulator-model anthropic/claude-sonnet-4 \
  --simulator-speech-provider openrouter-system # unattended real-API E2E
python demo.py --confirm-human-consent                # 1 consenting human + 6 real LLM Agents
python demo.py --confirm-human-consent --human-seat 3 # human is P3; role remains randomized
```

The simulator can use `OPENROUTER_API_KEY` alone when `espeak` and `ffmpeg` are installed. It can instead use a funded `OPENAI_API_KEY`, or `GEMINI_API_KEY` with local synthesis. AI reasoning and the post-game strategy audit can also use ARK or Moonshot via their OpenAI-compatible endpoints.
The live path refuses to open the microphone unless `--confirm-human-consent` is present.

Text-only and deterministic paths remain supplemental:

```bash
python demo.py --ai-only          # real LLM, all-AI text diagnostic
python demo.py --offline          # deterministic CI/privacy supplement
pytest -q
```

## Real validation results (2026-08-01)

The retained [`validation/runs/`](validation/runs/) evidence contains three formal eight-seat games and an independent validation file for each. The independent validator supersedes the run's embedded status when it finds a boundary defect. Credential scans over reports, validations, and logs found zero hits.

- `exp10-8-simulated-user-openrouter-20260801`: the embedded report claimed action agreement and all four strategy criteria passed, but strict revalidation correctly rejects its abstention because ASR returned `P1 is not`, not an explicit abstention.
- `...-v2`: the unaffected formal E2E result. It completed three full cycles with two user tool/audio/ASR actions, unique response IDs and nonzero audio-token receipts, information isolation, and a rule-based winner. The independent strategy judge failed Villager reasoning because the simulated Villager voted out the uncontested Seer.
- `...-v3`: used `anthropic/claude-sonnet-4` for the user and retained four tool/audio/ASR actions. Strict revalidation rejects two ambiguous abstentions, and the strategy judge also caught a Werewolf fabricating a public event.

The parser now fails closed unless an abstention transcript explicitly contains `abstain`, `skip`, `none`, or the supported Chinese equivalents; the synthetic utterance is the real-audio-probed phrase “I choose to abstain.” The unaffected v2 run is positive end-to-end verification and useful negative strategy evidence. Its strict overall result remains incomplete because strategy failed; stale embedded status and gates from different games are deliberately not combined. A real human microphone session is still optional manual coverage for VAD and barge-in, not a blocker for automated system E2E.

---

## 中文说明

系统现在有两条正式用户路径：授权真人麦克风，以及 `--simulate-user` 独立真实 LLM 用户模拟器。模拟器只读本席上下文，必须调用发言/选人工具；工具表达先生成真实音频，再由真实 ASR 转写，游戏只消费转写结果，选人不一致时失败关闭。真人路径继续覆盖 VAD、播放与打断。

2026-08-01 的严格复核否决了两个把误转写当成弃权的早期运行，并据此加固了解析器。未受影响的 v2 运行真实通过端到端、隔离、规则胜负与 3 循环，但村民误逐预言家导致策略失败。因此端到端已经实测，严格总体门禁仍为 `incomplete`。`--ai-only` 与 `--offline` 只是补充诊断。
