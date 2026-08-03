# Chapter 9 · Multimodal and Real-Time Interaction

> Extends perception and action from text to voice, GUI, and the physical world. Three voice paradigms (cascaded/end-to-end full-modal/full-duplex), streaming voice perception and synthesis, Computer Use, and robotic manipulation.

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter9.md)

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | A real-time voice chat demo integrating speech-to-text, AI dialogue, and text-to-speech. Supports multiple AI service providers (OpenAI, OpenRouter, ARK, Siliconflow), providing a low-latency conversational experience. |
| 9-2 | [phone-agent](phone-agent/) | ✅ | The retained direct/ReAct campaign runs browser-microphone RTP through real local Whisper, a real external LLM and TTS back over downlink RTP; both arms pass 20/20 gates and independent hash validation. PSTN/E.164 is outside this local WebRTC acceptance scope. |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | Demonstrates the core trade-off of streaming speech perception: chunk continuous audio into segments of increasing length and feed them to the ASR. Each received segment produces a "current partial recognition result" to achieve extremely low first-chunk latency for early text output. The cost is that early chunks, lacking the context of the latter half of the sentence, may be erroneous, gradually converging as audio accumulates. This contrasts with the high-accuracy/high-latency approach of "waiting for the entire sentence before recognition." |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | ✅ | A [real local run](end-to-end-speech/validation/runs/exp9-4-minicpmo45-20260801-v1/evidence.json) executed pinned MiniCPM-o 4.5 on one RTX PRO 6000: end-to-end and self-cascade both scored 3/4 with complementary semantic/paralinguistic failures; a real 24kHz speech output and [11/11 acceptance](end-to-end-speech/validation/runs/exp9-4-minicpmo45-20260801-v1/acceptance.json) are retained. |
| 9-5 | [controllable-tts](controllable-tts/) | ✅ | Fish Audio S1 produced the 24-reference library and A/B/C media; a three-pass position-balanced Voxtral listening study rated the multi-reference arm highest and evaluated the near-human claim. The expected C > B > A ordering did not fully reproduce because A outscored B. |
| 9-6 | [Anthropic native Computer Use record](claude-computer-use-native/) + `claude-quickstarts/computer-use-demo/` | ✅ | A [validated native run](claude-computer-use-native/validation/runs/exp9-6-anthropic-native-20260803-v2/acceptance.json) built the pinned Dockerfile locally and completed 16 real `claude-sonnet-4-5-20250929` responses plus 15 native `computer` actions. It did not interact with Google reCAPTCHA; visible Open-Meteo JSON grounded the final 70.2°F, clear-sky answer, and every deterministic gate passes. |
| 9-7 | [computer-use-open-model](computer-use-open-model/) + `browser-use/` | ✅ | A real open-model visual browser run used `qwen/qwen3-vl-32b-instruct` for 16/16 calls, recovered from a Google CAPTCHA through weather.com, and retained 15 screenshots, the complete action trajectory, grounded answer evidence, and verified hashes. |
| 9-8 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | External XLeRobot pinned to `3d14695…` for keyboard/Xbox/Joy-Con/VR teleoperation. Only source/non-actuating preflight exists; no authorized four-mode hardware run or pick/place/wipe evidence. |
| 9-9 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | External XLeRobot `3d14695…` plus RoboCrew, using exactly `gemini-robotics-er-1.5-preview`, angle annotation, and forward/left/right tools. No authorized robot/navigation run exists. |
| 9-10 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | External `lerobot-sim2real` pinned to `87d6c1d…` for the five-stage RGB→PPO→SO-100 pipeline. The host lacks ManiSkill/NVIDIA and no authorized physical robot run exists. |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **In Progress** | An implementation exists, but required live execution, authorization, hardware, or manuscript acceptance evidence is incomplete |
