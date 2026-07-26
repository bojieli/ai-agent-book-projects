# Chapter 9 · Multimodal and Real-Time Interaction

> Extends perception and action from text to voice, GUI, and the physical world. Three voice paradigms (cascaded/end-to-end full-modal/full-duplex), streaming voice perception and synthesis, Computer Use, and robotic manipulation.

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter9.md)

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | A real-time voice chat demo integrating speech-to-text, AI dialogue, and text-to-speech. Supports multiple AI service providers (OpenAI, OpenRouter, ARK, Siliconflow), providing a low-latency conversational experience. |
| 9-2 | [phone-agent](phone-agent/) | ✅ | Demonstrates a voice agent "interacting with the outside world via phone calls on behalf of the user": The upper layer is a standard ReAct agent. Upon receiving a natural language task, it autonomously determines the number and purpose of the call, invokes a `make_phone_call` tool (based on a telephony API abstraction) to complete the entire conversation, reads the structured call log, asks follow-up questions as needed by making another call, and finally reports back to the user. |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | Demonstrates the core trade-off of streaming speech perception: chunk continuous audio into segments of increasing length and feed them to the ASR. Each received segment produces a "current partial recognition result" to achieve extremely low first-chunk latency for early text output. The cost is that early chunks, lacking the context of the latter half of the sentence, may be erroneous, gradually converging as audio accumulates. This contrasts with the high-accuracy/high-latency approach of "waiting for the entire sentence before recognition." |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | ✅ | 对应 Step-Audio R1 的端到端语音思考（「听→想→说」），与 ASR→LLM→TTS 级联对比延迟与副语言损失 |
| 9-5 | [controllable-tts](controllable-tts/) | ✅ | The main LLM's output carries control tokens (emotion/speech rate/style/pause/laughter). The execution layer parses these tokens, maps them to corresponding style profiles in a reference speech library, and then synthesizes speech. This delegates decisions about "where to pause and what tone to use" to the LLM, allowing the same text to be synthesized in different styles and emotions. |
| 9-6 | `claude-quickstarts/` | 📖 | Quickstart examples and best practices for the Claude API, covering various use cases. |
| 9-7 | `browser-use/` | 📖 | Browser-Use is a powerful browser automation framework that enables LLMs to control a browser to complete complex tasks. It supports scenarios like form filling, web navigation, and data extraction, serving as a typical implementation of GUI automation (Computer Use). |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
