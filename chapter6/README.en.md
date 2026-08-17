# Chapter 6 · Interaction: Expanding the Observation and Action Spaces

> Extends perception and action from text to voice, GUI, and the physical world. Three voice paradigms (cascaded/end-to-end full-modal/full-duplex), streaming voice perception and synthesis, Computer Use, and robotic manipulation.

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter6.md)

## How to Read the Experiments

The prose uses short mechanism skeletons to explain control flow; the experiment directory contains complete SDK adapters, logs, tests, and acceptance evidence. You do not need to read every file line by line.

- **Starter:** Start with the goal, minimum command, and acceptance conditions; begin with [live-audio](live-audio/);
- **Builder:** Follow the entry point, core loop, state/message schema, tools, and verifier.
- **Maintainer:** Then read tests, evidence manifests, failure handling, rollback paths, and provider adapters.

On a first pass, skip credential loading, presentation code, and provider-compatibility layers; return when reproducing a number.

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 6-1 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | A modern event-driven Agent built with FastAPI, integrating all tools from the first three MCP servers by default. It uses a native asynchronous architecture for clean MCP tool loading and receives multi-source events (Web, Instant Messaging, GitHub, Timers, etc.) via HTTP API. Provides automatic API documentation (Swagger UI) and background monitoring capabilities. |
| 6-2 | [async-agent](async-agent/) | ✅ | Implement the core of an event-driven asynchronous Agent framework (Flux) based on a single-threaded asyncio model: an inbox event queue dispatches tasks by urgency (interrupt/immediate/queue), supports parallel execution of asynchronous tools, allows interrupting the current turn during execution, and provides cancellation and status querying for simulated long-running tasks. Decision-making is performed by a real LLM (function calling). |
| 6-3 | [live-audio](live-audio/) | ✅ | A real-time voice chat demo integrating speech-to-text, AI dialogue, and text-to-speech. Supports multiple AI service providers (OpenAI, OpenRouter, ARK, Siliconflow), providing a low-latency conversational experience. |
| Add-on | [phone-agent](phone-agent/) | ✅ | The retained direct/ReAct campaign runs browser-microphone RTP through real local Whisper, a real external LLM and TTS back over downlink RTP; both arms pass 20/20 gates and independent hash validation. PSTN/E.164 is outside this local WebRTC acceptance scope. |
| 6-4 | [streaming-speech](streaming-speech/) | ✅ | Demonstrates the core trade-off of streaming speech perception: chunk continuous audio into segments of increasing length and feed them to the ASR. Each received segment produces a "current partial recognition result" to achieve extremely low first-chunk latency for early text output. The cost is that early chunks, lacking the context of the latter half of the sentence, may be erroneous, gradually converging as audio accumulates. This contrasts with the high-accuracy/high-latency approach of "waiting for the entire sentence before recognition." |
| 6-5 | [end-to-end-speech](end-to-end-speech/) | ✅ | A [real local run](end-to-end-speech/validation/runs/exp6-5-minicpmo45-20260801-v1/evidence.json) executed pinned MiniCPM-o 4.5 on one RTX PRO 6000: end-to-end and self-cascade both scored 3/4 with complementary semantic/paralinguistic failures; a real 24kHz speech output and [11/11 acceptance](end-to-end-speech/validation/runs/exp6-5-minicpmo45-20260801-v1/acceptance.json) are retained. |
| 6-6 | [controllable-tts](controllable-tts/) | ✅ | Fish Audio S1 produced the 24-reference library and A/B/C media; a three-pass position-balanced Voxtral listening study rated the multi-reference arm highest and evaluated the near-human claim. The expected C > B > A ordering did not fully reproduce because A outscored B. |
| 6-7 | [Anthropic native Computer Use record](claude-computer-use-native/) + `claude-quickstarts/computer-use-demo/` | ✅ | A [validated native run](claude-computer-use-native/validation/runs/exp6-7-anthropic-native-20260803-v2/acceptance.json) built the pinned Dockerfile locally and completed 16 real `claude-sonnet-4-5-20250929` responses plus 15 native `computer` actions. It did not interact with Google reCAPTCHA; visible Open-Meteo JSON grounded the final 70.2°F, clear-sky answer, and every deterministic gate passes. |
| 6-8 | [computer-use-open-model](computer-use-open-model/) + `browser-use/` | ✅ | A real open-model visual browser run used `qwen/qwen3-vl-32b-instruct` for 16/16 calls, recovered from a Google CAPTCHA through weather.com, and retained 15 screenshots, the complete action trajectory, grounded answer evidence, and verified hashes. |
| 6-9 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | Real XLeRobot teleoperation for one desk-tidying task: put the red cup in the tray, put the yellow waste paper in the waste bin, then re-observe and verify the state. |
| 6-10 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Simulator measurement of the ideal-control upper bound for the same desk task; it does not claim that the real robot has run. |
| 6-11 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Gemini Robotics-ER 1.5 autonomously drives the real XLeRobot on the same desk-tidying task. |
| 6-12 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Simulator comparison of open-loop, stepwise-checking, and predictive closed-loop strategies for the same task. |
| 6-13 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | RGB cross-environment test for the same desk task, varying backgrounds, object appearance, lighting, and visual noise. |

## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **In Progress** | An implementation exists, but required live execution, authorization, hardware, or manuscript acceptance evidence is incomplete |
