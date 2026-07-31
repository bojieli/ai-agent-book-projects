# Experiment 10-8 · Live voice Werewolf Agent system

The default path is the book's full experiment: a 6–8 seat game with exactly one real human and 5–7 independent AI Agents, two Werewolves, one Seer, one Witch, and Villagers. The human's role is assigned by the same seeded random shuffle as every AI role. The code-driven Judge—not an LLM—owns the state machine, night/day/vote phases, skill inventory, deaths, and deterministic win rule.

## Live two-way voice

`python demo.py` is no longer an all-AI text demonstration. It creates a real human seat and a `LiveVoiceSession`:

1. AI/Judge speech is sent to a real OpenAI TTS endpoint and played immediately.
2. Human speech is captured from the microphone with energy VAD and end-of-speech silence detection.
3. Captured WAV audio is sent to a real OpenAI ASR endpoint.
4. Spoken player numbers drive human night skills and voting; daytime speech is broadcast to every Agent context.
5. During public AI speech, microphone activity cancels playback, transcribes the barge-in, and records it as a public interruption turn. Headphones are recommended to prevent acoustic echo from triggering the detector.

Audio files and a timestamped `voice_trace.json` record TTS, ASR latency, and interruptions. `--no-interruptions` disables barge-in for noisy rooms.

## Information asymmetry and strategy acceptance

Every player owns a separate `memory`. The Judge has only three delivery capabilities: public broadcast, single-player private send, and Werewolf-team send. The same boundary applies to the human seat. The post-game audit proves Werewolf teammates never enter good-player contexts, Seer investigations enter only the Seer context, and all public events reach everyone.

The game also records role-labelled actions and runs a real LLM post-game acceptance judge over four explicit criteria: Werewolf concealment, Seer reveal timing/evidence, Villager evidence-based reasoning, and general role consistency. It quotes logged evidence and may return `insufficient`; it cannot substitute an Agent's unsupported claim for observed actions.
The returned JSON is schema-checked: all four named criteria need a valid
`pass|fail|insufficient` status, and every passing criterion needs evidence. A bare
model claim of `overall_pass: true` cannot pass the gate.

`artifacts/acceptance_report.json` records:

- one human and the randomized human role;
- exact role counts and player count;
- completed night–day–vote cycles and deterministic winner;
- privacy audit result;
- real strategy audit;
- whether both real ASR and TTS occurred, plus barge-in count.

The live acceptance result requires 6–8 players, the exact role mix, one human, privacy pass, at least three complete cycles, and observed ASR + TTS events.
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
python demo.py --confirm-human-consent                # 1 consenting human + 6 real LLM Agents
python demo.py --confirm-human-consent --human-seat 3 # human is P3; role remains randomized
```

The direct OpenAI key must have Audio API quota. AI reasoning and the post-game strategy audit can independently use ARK or Moonshot via their OpenAI-compatible endpoints.
The live path refuses to open the microphone unless `--confirm-human-consent` is present.

Supplemental paths are retained but are not accepted as the voice experiment:

```bash
python demo.py --ai-only          # real LLM, all-AI text diagnostic
python demo.py --offline          # deterministic CI/privacy supplement
pytest -q
```

## Current validation boundary

Unit tests pass for the exact roster/human-seat contract, cross-seed human-role
randomization, spoken vote parsing, three-cycle accounting, both deterministic win
conditions, strict strategy-audit schema, privacy side-channel controls, and barge-in
cancel/transcribe mechanics using mocked audio primitives. The consent test proves the
default command exits before constructing the live session. Separate safe probes reached
the real OpenAI Speech endpoint and sent a generated one-second non-human WAV to the real
ASR endpoint; both were rejected with `429 insufficient_quota`. No microphone or human
audio was used, so no live-human acceptance claim is made for that credential.
Supply a funded Audio API key and a consenting microphone participant to generate the
acceptance report.

Machine-readable evidence under [`validation/`](validation/) separates the passing offline privacy supplement, the partial ARK gameplay run, and the still-incomplete live acceptance gates. It records that zero calls were placed and no human audio was captured in this audit.
A separate safe ARK run exercised the strict post-game audit against deterministic
offline actions. Its schema passed and all four strategy criteria correctly failed; the
artifact is explicitly `supplemental_only` because it had no human, no voice, only two
cycles, and did not evaluate real-LLM player behavior.

---

## 中文说明

默认命令现在就是书中的完整路径：6–8 人、1 名真人、5–7 个独立 AI Agent、2 狼人、1 预言家、1 女巫、其余村民。真人通过麦克风说话，OpenAI ASR 转写；AI/法官通过真实 TTS 播放；公开发言期间真人可以插话并中断播放。夜间技能、白天发言和投票都能由真人语音完成。

法官继续严格控制私有上下文，并在赛后自动检查信息隔离。除此之外，真实 LLM 会基于已记录的发言/行为验收狼人隐藏、预言家跳身份时机、村民逻辑和角色一致性。`--ai-only` 与 `--offline` 只是补充诊断，不是语音验收路径。
