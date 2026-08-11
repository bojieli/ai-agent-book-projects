# Multimodality and Real-Time Interaction

The previous chapters explored how Agents operate in a text-based world, interacting with digital systems through context, tools, and code. But an Agent's world extends beyond text and APIs. The moment it needs to understand a spoken command, find and click the right button on a screen, or steer a robotic arm to grasp an object, it enters new territory: **multimodal real-time interaction**. This shift from pure text input and output to **multimodal perception and real-time response** is the crucial step that takes an Agent beyond the "dialog box." "Multimodal" simply means handling multiple forms of information at once—text, speech, images, video, and actions—rather than text alone.

First, let us define the scope of this chapter. Static image and document understanding—examining a screenshot, reading a chart, or parsing a PDF—has already become a natural part of the Agent workflows in previous chapters. For today's multimodal LLMs, these single-input understanding tasks are relatively mature and require no special architecture. This chapter tackles a different class of problems: three scenarios in which **real-time constraints make multimodal problems hard**—voice dialogue, GUI operation, and robot control. In these settings, input arrives continuously and output must meet a strict time budget, fundamentally changing the architecture. Real-time understanding of continuous visual streams, or video, remains an open problem for Agents at the time of writing. We will return to it when the Computer Use section examines the limits of frame-by-frame screenshots, and again in the end-of-chapter questions. One more boundary: in this book's framework, multimodal **generation** (image or video generation) is simply an ordinary tool call, as covered in Chapter 5 on Multimedia Generation. The Agent uses it as an external tool, so it raises none of the real-time interaction challenges addressed here and remains outside the chapter's main thread.

Voice interaction, Computer Use, and robot operation may seem like three entirely different fields, but systems in all three run into strikingly similar problems: they must process several modalities at once, and they are acutely sensitive to latency. A pause of more than two seconds in a voice conversation makes people restless; millisecond-level jitter in robot control can cause a collision. Together, these constraints push all three scenarios in the same architectural direction: away from the **serial pipeline** (like a factory assembly line, where one step must finish before the next begins) and toward the **end-to-end model** (a unified model that goes directly from input to output, eliminating intermediate handoffs).

This chapter unfolds along the following lines:

1.  First, we use three voice-architecture paradigms as a framework: cascaded (a VAD-ASR-LLM-TTS pipeline), end-to-end omnimodal (Omni, a single model that still relies on turn-taking), and full-duplex (Moshi and GPT-Live, which listen and speak simultaneously). We compare their latency and trade-offs by asking how far each paradigm moves beyond VAD's assumption of discrete turns. The cascaded section also discusses replacing VAD + ASR with streaming voice perception.
2.  Next, we examine how the thinking architecture reconciles the conflict between "real-time response" and "deep thinking": from simple parallelization of fast and slow, to the decoupled approach where a background reasoning model acts as a "strategist" (GPT-Live delegation, Pine AI, etc.), to Step-Audio R1's "internalization" of thinking into a single model that "thinks while speaking."
3.  Then, we discuss how more human-like speech synthesis optimizes the execution layer.
4.  Finally, we extend the perspective to Computer Use (enabling AI to operate a computer screen like a human) and robot operation, observing how the same latency and multimodality issues manifest in these two scenarios.

Two more theoretical themes carry across these scenarios and deserve special attention: the **thinking architecture** (how fast and slow thinking collaborate) and the **fast-slow interface** that follows from it (the **Latent Bridge**—what fast and slow models can exchange besides text). Although introduced in the context of voice, these ideas are not limited to it. The Computer Use and robotics sections encounter the same question of when to consult a slow strategist, so keep both themes in mind.

## Voice: The Most Natural Human-Machine Interface

Voice is not merely text turned into sound. Speaking is roughly four times faster than typing and leaves the hands and eyes free, so it naturally places an Agent in a continuous input-output loop where the user may interrupt at any moment. Dictation converts speech into text; a voice Agent lets the user collaborate with the Agent directly. Both support the whisper-coding workflow introduced earlier.

This section covers two directions: the user speaking to an Agent, and an Agent speaking to the outside world on the user's behalf. The voice model determines what the Agent can answer; the interaction architecture determines whether it can hear clearly, respond in time, hand over naturally, and complete confirmations and tool calls during a call. We first examine interaction timing, then cognitive timing and expressive quality.

### Interaction timing: from cascaded to full-duplex

OpenAI's GPT-Live introduction describes three voice-interaction paradigms—cascaded, turn-based, and full-duplex[^ch9-12]. They are not a simple old-to-new replacement; they trade latency, cost, and observability in different ways:

| Paradigm | Core structure | Main advantage | Main limitation |
| --- | --- | --- | --- |
| Cascaded | VAD → ASR → LLM → TTS | Clear modules that are easy to replace and debug | Latency accumulates and paralinguistic information is lost at interfaces |
| End-to-end Omni | One model listens, thinks, and speaks | Lower latency and better preservation of tone, emotion, and ambient sound | Still turn-based; training and debugging cost more |
| Full-duplex | Continuously listens, speaks, and decides | Overlapping speech, natural interruption, and continuous streams | Training, control, and evaluation are more complex |

The common thread is escaping the assumption that people must speak one at a time, and escaping VAD's guess about who has the floor. Cascaded and Omni systems still divide interaction into turns; full-duplex makes turn ownership a continuous model decision.

[^ch9-12]: OpenAI. *Introducing GPT-Live.* 2026-07-08. https://openai.com/index/introducing-gpt-live/ The cascaded / turn-based / full-duplex taxonomy comes from the article's summary of three generations of ChatGPT Voice; its “end-to-end omnimodal (Omni)” term corresponds to the “turn-based voice models” category.

### Paradigm 1 · Cascaded pipeline

Most commercial voice assistants still use a serial pipeline (Figure 9-1): VAD decides when the user has finished, ASR converts audio to text, the LLM understands and generates a reply, and TTS speaks it. Modularity lets each component be optimized independently, but every boundary can add waiting time.

![Figure 9-1: Serial voice Agent pipeline](images/fig9-1.svg)

| Module | Role | Typical bottleneck |
| --- | --- | --- |
| VAD | Decide whether speech has ended | Silence thresholds add waiting and split turns incorrectly |
| ASR | Convert audio to text | Recognition latency and loss of context |
| LLM | Understand, reason, and generate | Time to first token; reasoning adds more waiting |
| TTS | Convert text to speech | First-packet synthesis and playback buffering |

For a short reply without reasoning, VAD, ASR, LLM, and TTS waiting time accumulates serially (Figure 9-2). The real value depends on input length, model, hardware, network, and load.

![Figure 9-2: Latency waterfall for a serial response](images/fig9-2.svg)

Production queueing amplifies idle latency further (Figure 9-3), but capacity planning is outside this chapter's scope.

![Figure 9-3: Queueing latency curve](images/fig9-3.svg)

> **Experiment 9-1 ★: Build a traditional voice Agent**
>
> Connect the microphone, Silero VAD, local Whisper, a streaming LLM, and Fish S1 TTS over WebSocket to establish the cascaded baseline. The retained real single-turn evidence shows that the media and model chain ran end to end; it is not a concurrency or production-load benchmark. Code and acceptance records are in [chapter9/live-audio](../chapter9/live-audio/).

> **Add-on: Build a WebRTC voice Agent that “calls the user”**
>
> A phone Agent does not require PSTN. Browser WebRTC can reproduce the loop of opening a session, asking for missing information, repeating it for confirmation, and saving structured results. When an external organization must be contacted, replace the same tool contract with a compliant PSTN/SIP provider. The complete media path, direct/ReAct comparison, and acceptance evidence are in [chapter9/phone-agent](../chapter9/phone-agent/). The project retains its historical \`exp9-2\` run identifiers but no longer occupies a numbered manuscript experiment.

#### From serial to streaming perception

Figure 9-2 describes the fully serial case in which each stage waits for the previous one. A production system can retain the modular split while producing increments as early as possible:

- **Streaming ASR** continuously produces a provisional transcript while the user speaks, then confirms the final text at the turn boundary.
- **Segmented LLM output** sends the first speakable sentence to TTS without waiting for the full reply.
- **Incremental TTS** returns audio chunks so later generation, synthesis, and playback overlap.

“Streaming every stage” does not make ASR, LLM, and TTS fully parallel from start to finish. In a standard cascade, ASR overlaps with the user's speech and TTS overlaps with the LLM's later tokens, but the final reply still depends on a stable transcript. A more aggressive system starts the LLM from a partial transcript; if later text changes, it must cancel, restart, or correct the generation. Speculation requires explicit commit, invalidation, and rollback mechanisms; enabling \`stream\` alone does not provide them.

Ordinary streaming also cannot remove VAD's silence wait. A traditional VAD + ASR front end has three problems:

1. **Accumulated latency:** it must wait through silence before confirming the end.
2. **Lost information:** a voiced/unvoiced bit cannot express hesitation, emotion, backchannels, or ambient sound.
3. **Broken context:** email addresses, names, and proper nouns may be split across chunks and misrecognized.

A truly streaming model needs a causal or chunked encoder with incremental decoding. Whisper's decoder is autoregressive, but its encoder expects a complete audio segment, so it should not be called a causal streaming model. RNN-T and streaming Conformer ASR have long been used in industry; the focus here is semantic listening built on an LLM backbone.

An LLM-based streaming-audio model can emit text and semantic events from continuous audio, placing recognition and part of understanding in one model. It keeps the conversation context from the beginning and can use world knowledge for brands, names, and proper nouns. Simulated chunking is still not a performance promise for a causal model.

If the only goal is deciding whether the user has finished, endpointing can be built into the streaming recognizer. The model combines semantics and silence to judge whether an utterance is complete. Training labels must contain only information visible at decision time, or hindsight will produce a judgment that cannot be reproduced online[^ch9-11]. This is lighter than a complete audio-capable LLM.

The model can emit acoustic-event markers as well as words:

- **speak_start/end, interrupt:** speech boundaries and interruption intent;
- **emotion:** emotion and hesitation;
- **laugh, sigh, noise:** paralinguistic and environmental sound.

Together with text tokens, these markers form one event stream. The Agent can detect hesitation, interruption, and environmental changes without compressing every sound into plain text.

[^ch9-11]: For the diagnosis of embedding turn judgment in the recognizer and the problem of hindsight-based labels, see Bojie Li and Noah Shi. *The Trade-off Was in the Labels: Causal Supervision for Turn-Aware Streaming ASR.* 2026 (forthcoming).

> **Experiment 9-2 ★: Simulate streaming voice perception with Qwen2-Audio**
>
> Qwen2-Audio is not itself a streaming model. This experiment simulates continuous perception with increasing audio prefixes and compares it with 600 ms VAD + Whisper. It shows how full context changes pause and noise behavior, but every prefix re-encodes earlier audio, so its timings are not a promise for a causal streaming model.
>
> The canonical run passed all execution and provenance gates but reproduced only 2/6 expected behaviors: increasing-prefix calls took 8.4–11.3 seconds, the pause sample missed \`silence\`, and the noise sample still misclassified \`cough/laughter\`. This negative result tests mechanisms and failure modes; it does not support a “100–200 ms true streaming perception” claim. See [chapter9/streaming-speech](../chapter9/streaming-speech/) for the complete record.

### Paradigm 2 · End-to-end omnimodal models (Omni)

Even with streaming perception, a cascade passes listening, thinking, and speaking through discrete interfaces; emotion, intonation, and ambient sound may be lost when audio becomes plain text. Omni uses one model to listen to audio, generate a reply, and speak it, which can preserve those signals at the cost of higher training, debugging, and component-replacement costs (Figure 9-4).

The end-to-end advantage is mainly latency and non-text information, not necessarily accuracy. A self-cascade first transcribes with the same model and then answers from the transcript: when text carries the task information, it may correct a perception error; when the answer depends on speech rate, emotion, or ambient sound, the text bottleneck irreversibly loses evidence. The key question is not whether there is an intermediate representation, but what information it carries[^ch9-13].

Omni still assumes turn-taking and generally uses VAD or semantic endpointing to assign the floor. A pause in a spoken sequence of numbers can still be mistaken for the end; streaming perception improves the judgment but does not remove turns.

[^ch9-13]: For a complete cross-modal measurement of when cascade and end-to-end accuracy advantages reverse, and how task nature predicts the direction, see Li, Bojie and Noah Shi. *The Cascade Gap: When and Why Self-Cascades Help Multimodal Agents.* 2026 (forthcoming).

![Figure 9-4: End-to-end omnimodal speech-model comparison](images/fig9-4.svg)

Realtime speech APIs sit between cascaded and Omni systems: the model handles audio natively, but interaction control still relies on VAD, interruption, and asynchronous tool calls. Qwen3-Omni's Thinker-Talker and MiniCPM-o's local path show that this approach can combine thinking, expression, and multimodal input at different model sizes. The useful comparison is not a leaderboard; it is how end-to-end and self-cascade paths fail on different tasks.

> **Experiment 9-3 ★★: Run MiniCPM-o 4.5 locally—end-to-end versus self-cascade**
>
> Fix one local MiniCPM-o 4.5 revision, disable thinking mode, and compare direct audio answers with the same model's self-cascade: transcribe first, then answer from the transcript. This measures whether audio information is preserved, **not** the later “think while speaking” capability.
>
> **Table 9-1.** Local MiniCPM-o 4.5 end-to-end and self-cascade results (four mechanism checks, not a benchmark)
>
> | Task type | End-to-end | Self-cascade | Observation |
> | --- | ---: | ---: | --- |
> | Semantic arithmetic (2) | 1/2 | 2/2 | Self-cascade corrected one transcription error |
> | Paralinguistic speaking rate (2) | 2/2 | 1/2 | The plain-text transcript erased the fast/slow distinction |
> | Total | 3/4 | 3/4 | Equal totals, complementary failures |
>
> The sample is small, so it cannot establish which path is generally more accurate or faster. Hardware, versions, raw outputs, and real audio-to-audio evidence are in [chapter9/end-to-end-speech](../chapter9/end-to-end-speech/).

Step-Audio 2 demonstrates an end-to-end path that processes raw audio and emits text and speech; it focuses on emotion, speaking rate, intonation, and ambient sound beyond semantics. Step-Audio R1 extends this path by internalizing reasoning in the audio model; it will serve as the example for “thinking while speaking.”

### Paradigm 3 · Full-duplex interactive models

Omni still divides conversation into “the user speaks” and “the model speaks,” but simultaneous interpreting and similar tasks require overlap. A full-duplex model therefore does not presuppose turns: it listens and speaks continuously and repeatedly decides whether to continue, pause, interrupt, or call a tool.

Kyutai's **Moshi** (2024) was an early research example. It models the user's and the model's audio streams in parallel, so overlapping speech and interruption can be natural behaviors.

Thinking Machines Lab calls this an **Interaction Model**[^ch9-14]: interaction is built into the model instead of assembled around it with VAD and other external harnesses. Its micro-turn mechanism advances in short audio blocks, preserving silence, overlap, and interruption as continuous context. It can delegate the full conversation to a background reasoning model while it keeps the conversation alive, then incorporate the result at a suitable moment.

[^ch9-14]: Thinking Machines Lab, “Interaction Models: A Scalable Approach to Human-AI Collaboration,” 2026-05. https://thinkingmachines.ai/blog/interaction-models/

OpenAI's GPT-Live brings the full-duplex path to production scale: it continuously processes input and generates output, can wait, backchannel, be interrupted, and handle realtime translation. Like the Interaction Model, it delegates complex work to a background model while the foreground model maintains the conversation.

The narrative is: cascades guess turns from silence thresholds; streaming perception upgrades the judgment to the semantic level; full-duplex turns the switch itself into a continuous decision.

### Cognitive timing: realtime interaction and deep thinking

Interaction quality and intelligence ceiling are different dimensions. The foreground model must respond while the user is still engaged; the background model can spend longer thinking. The following three designs are trade-offs, not a linear progression. The first two can wrap a cascade or Omni model; only the third unifies thinking and expression in one end-to-end audio model.

| Design | Foreground | Background | Main risk |
| --- | --- | --- | --- |
| Fast filler, slow correction | Give an immediate answer | Re-think and supplement it | Contradiction |
| Fast interaction, slow advice | Keep the conversation alive and choose wording | Supply advice or tool results | A constrained interface |
| Unified thinking and expression | Think and speak together | Share model state with expression | High training and replacement cost |

#### Solution 1: Fast thinking for fillers, slow thinking for answers

Fast thinking can give a holding response within a few hundred milliseconds while slow thinking performs a deeper derivation in the background. Simple questions may be processed twice, while hard questions can produce contradictions: the fast model recommends a purchase, then the slow model discovers that a key feature is missing. The root cause is two independent instances thinking separately.

![Figure 9-5: Fast/slow thinking architecture and design alternatives](images/fig9-5.svg)

#### Solution 2: Fast thinking for interaction, slow thinking for advice

The background model can send advice through a status bar or dedicated interface while the foreground model keeps the conversation alive and decides how to phrase it. This is more stable than Solution 1, but communication is still indirect: the foreground can misunderstand the advice and cannot see the background's intermediate reasoning. Before the background finishes, follow-up questions still rely on the foreground model. It can naturally wait for a result, but it cannot truly think while speaking.

#### Solution 3: End-to-end unification of thinking and expression (using Step-Audio R1)

This design internalizes reasoning directly in an end-to-end audio model. Step-Audio R1 uses two complementary mechanisms: **Modality-Grounded Reasoning Distillation (MGRD)** grounds thinking in acoustic features, while the **MPS dual-brain architecture** lets planning and expression proceed in parallel. The first helps the model think correctly; the second helps it speak in time.

Ideally, the model infers emotion from pitch, rhythm, and intonation rather than only from the transcript. “Text-proxy thinking” substitutes negative words in lyrics for analysis of melody and acoustics. MGRD selects reasoning traces that actually cite acoustic features, trains on them, and uses reinforcement learning to prevent guessing without thinking.

MPS lets the planning brain continuously emit thought segments; the expression brain combines each segment with the partial reply and immediately generates speech. The pipeline runs in parallel, so the listener need not wait for the entire chain of reasoning before hearing the first sentence (Figure 9-6).

![Figure 9-6: Step-Audio R1 MGRD and MPS dual-brain architecture](images/fig9-6.svg)

A unified model implements “thinking while speaking” most directly, but thinking and realtime expression must be retrained together. A decoupled design makes it easier to swap the background brain; a unified design suits specialized scenarios that demand the most natural interaction. These are trade-offs, not simple substitutes.

### More human-like speech synthesis

Traditional TTS can expose its machine identity by being too smooth and pausing too little. Pauses, filler words, and occasional repetition signal uncertainty and thought in human speech.

The main LLM can emit control markers in addition to text, such as **THINKING**, **EMO:happy**, and **SPEED:0.8x**; TTS maps them to pauses, prosody, speaking rate, laughter, sighs, and other nonverbal audio. The implementation can be a TTS trained to understand control markers, or voice cloning with reference clips for different emotions and styles.

> **Experiment 9-4 ★★: Control token-driven TTS with Fish Audio**
>
> Use Fish Audio S1 to build a multi-reference voice library and compare three configurations: no control markers, one reference clip, and multiple reference clips. The execution layer selects matching emotion, speaking rate, and style from the markers.
>
> The multi-reference configuration scored highest in three position-balanced blind listening passes (human-customer-service likeness 4.67/5), but the complete planned ordering was not reproduced because the no-marker arm outscored the single-reference arm. This result suggests that expressive control helps, but a small listening study is not a general speech-quality conclusion. The complete 24-reference library, A/B/C media, and acceptance record are in [chapter9/controllable-tts](../chapter9/controllable-tts/).

## Computer Use: GUI Automation Agents

By now you may have noticed that this chapter devotes far more space to voice than to the two scenarios that follow. This is deliberate. Among real-time multimodal systems, voice technology has progressed the furthest and therefore provides the best reference point. It has traced the full arc from the original problem—excessive latency in serial pipelines—through end-to-end models, full-duplex interaction, and thinking while speaking, to today's relatively mature designs. That is why we have told its story in full. As you read the Computer Use and robotics sections, compare them with this trajectory: how far has each field progressed, and where does each remain stuck?

These three scenarios seem different but face the same core challenges: real-time perception, low-latency decision-making, and continuous interaction. Next, we turn to visual interaction, or Computer Use, expanding the perspective from the auditory to the visual modality: what if an Agent could not only understand speech but also "see" the screen and operate its graphical interface?

Computer Use, also known as GUI automation, allows AI to use software like a human by observing the screen and operating the mouse and keyboard—for example, opening a browser to search for information, filling in data in a spreadsheet application, or adjusting configurations in system settings. Its core is a **Perceive-Think-Act** loop (Figure 9-6):

1.  The Agent takes a screenshot of the current screen.
2.  A multimodal model receives the screenshot and task instruction, and outputs a thought and a specific action.
3.  The execution layer performs the action in the real environment (moving the mouse, clicking, typing text, etc.).
4.  It waits for the interface to respond, takes another screenshot, and enters the next loop iteration.

![Figure 9-6: Computer Use Agent's Perceive-Think-Act Loop](images/fig9-7.svg)

There are three key design dimensions in this loop: **Action Space** (what operations the Agent can perform), **Visual Grounding** (how to find the target element in the screenshot), and **Model Architecture** (how to generate the correct action from the screenshot).

### Action Space Design

Anthropic defines three types of tools that constitute a complete interaction capability (Figure 9-7):

![Figure 9-7: Computer Use Action Space](images/fig9-8.svg)

**GUI Operation Tool** (`computer` tool): Mouse operations include moving (`mouse_move`), left/right/middle clicks, double-clicking or triple-clicking, dragging (`left_click_drag`), and more precise press/release actions (`left_mouse_down` and `left_mouse_up`). Scrolling (`scroll`) supports four directions and can be combined with modifier keys. Keyboard operations include typing character by character (`type`, with a 12ms interval between characters to simulate real typing), key combinations (`key`, e.g., `Ctrl+C`), and holding a key (`hold_key`). Perception actions include taking a screenshot, retrieving the cursor position (`cursor_position`), and waiting (`wait`).

**Command Execution Tool** (bash tool): Provides a persistent bash terminal session with a 120-second timeout. It uses a sentinel string to detect command completion and maintains environment state across multiple calls (e.g., after `cd` to a directory, the next call remains in that directory).

**File Editing Tool** (`str_replace_editor`): Enables safe editing through string matching and supports view, create, replace, insert, and undo operations. It is more precise than overwriting an entire file and less likely to modify unrelated content accidentally.

> **Experiment 9-5 ★: Running Computer Use (Anthropic Reference Path or Open-Model Path)**
>
> Path A uses the Anthropic Computer Use Demo. Its container packages a complete Ubuntu desktop environment, including a browser, terminal, and other common tools. The frontend receives a task, while the backend sends the instructions and screenshots to Claude and then executes the mouse, keyboard, terminal, or editing actions returned by the model. This path is intended for understanding the native `computer` tool protocol; it does not require every reader to have access to the Anthropic API.
>
> Path B uses this book's [`chapter9/computer-use-open-model`](../chapter9/computer-use-open-model/) companion. By default, it drives browser-use with the open-weight Qwen3-VL 32B Instruct model, either through the OpenRouter hosted API or by pointing `OPEN_MODEL_BASE_URL` to self-hosted vLLM/SGLang or another compatible endpoint. The endpoint must accept screenshots and support native JSON Schema; if it supports only ordinary JSON, the schema-in-prompt compatibility mode can be enabled explicitly.
>
> Both paths use the same read-only task and acceptance contract: a maximum of 25 steps, one action per step, and retention of the model/endpoint identity, raw provider responses, step-by-step screenshots, action sequence, final answer, and stop reason. Different models must be reported as separate experimental arms; an open-model result must not be presented as a Claude reproduction, nor should successful container startup be treated as task completion. Action intervals and planning quality are measured outcomes, not assumptions of a 2–5-second interval or inevitable superiority over other models.
>

### Visual Grounding

In each iteration of the loop, the model needs to accurately locate the target element in the screenshot—"Where is the search box?" "What are the coordinates of the submit button?" This is the visual grounding problem. Currently, there are **two main approaches**: one is to turn localization into a **multiple-choice problem**—first annotate the interface elements with numbers, and the model only needs to select one; the other is **pure coordinate prediction**—letting the model "look" at the screenshot and report coordinates directly, just like a human. The multiple-choice approach has two implementation methods: **pure visual annotation** (the original Set-of-Mark, using a segmentation model to segment candidate regions in the image) and **structured element indexing** (DOM/Accessibility Tree, directly reading the interface's inherent structure). The common advantage of the multiple-choice approach is that it transforms the open-ended problem of "find the button in the screenshot and predict its coordinates" into a closed-ended one of "choose one from the already annotated elements"—just as multiple-choice questions are easier to answer correctly than fill-in-the-blank questions in an exam, the model only needs to say "click [123]" instead of "click the blue button approximately 200 pixels to the right of the top-left corner of the screen."

**Set-of-Mark: Visual Annotation Method.**

The original Set-of-Mark (SoM) was proposed by Microsoft Research in 2023, initially to unlock the visual grounding capabilities of GPT-4V. It is a **purely visual** method: it uses image segmentation models (SAM, SEEM, etc.) to automatically segment candidate regions in the screenshot, overlays a numbered marker on each region, and the model sees an image with numbers. The model only needs to report the number, and the system converts it into the center coordinates of the corresponding region. The entire process does not require a DOM or any internal interface structure, so it is equally applicable to native desktop software and game interfaces—as long as the segmentation model can identify the candidate regions.

**Structured Element Indexing: A Structured Implementation of the SoM Idea on the Web.**

When the interface itself provides structured information, annotation can be more precise. Before rendering, modern web pages define a complete element structure (the DOM tree) and semantic roles that identify buttons, input fields, and other controls. Accessibility trees provide similar information for many desktop applications. Rather than asking a segmentation model to guess which region is a button from pixels alone, the system can query the interface directly for its clickable elements. Web Agent systems such as `browser-use` do exactly this: they enumerate and number interactive elements from the DOM. This is a structured implementation of the SoM idea for the web (Figure 9-8). The process has four steps:

1. Obtain the structured representation (DOM tree) and accessibility information for the page through the browser's debugging interface (CDP, Chrome DevTools Protocol)
2. Automatically detect which elements are interactive (buttons, input boxes, links, etc.)
3. Annotate each interactive element with a unique ID and draw bounding boxes on the screenshot
4. Simultaneously generate a text list describing the element corresponding to each ID

```text
Screenshot: [Key elements in the image are annotated with IDs like [1], [2], [3], [4]]

Elements:
[1] <input type="text" placeholder="Search" aria-label="Search" />
[2] <button id="submit-btn" aria-label="Submit form" />
[3] <input type="text" placeholder="Enter your name" value="" />
[4] <a href="/docs" aria-label="Documentation" />
```

The model only needs to output an ID, and the system automatically clicks the center of the corresponding element. This approach does not save tokens because all annotation data must still be sent to the model, but it provides accurate, stable localization while avoiding the missed detections and false positives that segmentation models can introduce.


![Figure 9-8: Set-of-Mark vs. Structured Element Indexing (browser-use implementation)](images/fig9-9.svg)

**Pure Coordinate Prediction.**

The third route skips annotation and asks the model to output coordinates directly. Systems such as **SeeClick** and Claude's computer use rely on vision models trained on massive datasets of GUI screenshots paired with element positions. These models learn to map natural-language descriptions (e.g., "click the submit button") directly to precise screenshot coordinates, relying on visual perception much like a human user.

In coordinate prediction schemes, the model's understanding of coordinates is highly dependent on the resolution used during training (Figure 9-9). Claude was trained using XGA (1024×768), WXGA (1280×800), and FWXGA (1366×768). If the input screenshot resolution does not match, the model's predicted coordinates will systematically shift—like measuring a distance on a small map and then applying it directly to a large map. Therefore, a bidirectional coordinate scaling mechanism must be implemented at the tool layer, and the target resolution must be **selected based on the aspect ratio** to avoid non-uniform stretching that distorts the image and consequently biases coordinate judgment. For example, if the actual screen resolution is 2560×1440 (16:9), the most suitable target among Claude's three supported options is FWXGA (1366×768), which has an aspect ratio closest to 16:9. The screenshot is proportionally scaled to 1366×768 and fed to the model; after the model outputs the click coordinates (683, 384), they are inversely mapped to the real coordinates (683×2560/1366, 384×1440/768) ≈ (1280, 720). Conversely, if a 16:9 image is forcibly stretched into the 4:3 1024×768, the image will be horizontally compressed, causing the model's predicted coordinates to systematically shift.


![Figure 9-9: Resolution Matching and Bidirectional Coordinate Scaling](images/fig9-10.svg)


The choice among the three routes can be summarized as follows: **when structured information is available, prioritize DOM/accessibility-tree indexing** for the most accurate and stable localization. **When it is unavailable**—in native desktop software such as Photoshop, canvas/WebGL-rendered interfaces, or games—**use either visual annotation (the original SoM route) or coordinate prediction**. Visual annotation turns localization into a multiple-choice problem, making it friendlier to general-purpose models without specialized training. Coordinate prediction eliminates the annotation step and is more direct for models trained specifically on GUI localization. Both approaches still struggle with small elements and dense interfaces.

> **Experiment 9-6 ★: Using browser-use to Implement Automated Browser Operations**
>
> Use Playwright, a browser-automation framework, together with a multimodal model to implement browser operations driven by natural language. Enable SoM visualization and save a screenshot with annotated bounding boxes before every decision. The model interface is not limited to OpenAI or Anthropic; the book provides an API configuration for the open Qwen3-VL model and retains a generic OpenAI-compatible base URL for other hosted services or self-hosted inference.
>
> Test task "Open Google and query San Francisco weather": after startup, a screenshot shows the Google search page with numbered interactive elements. The model selects the search box, enters "San Francisco weather today," submits the search, and then extracts the temperature and conditions from the results page. During acceptance, independently verify the answer and trajectory and record the actual step count and elapsed time. "5 steps and about 20 seconds" can only be an observation from a particular run, not a fixed result stated without an execution receipt.
>
> The book's preserved official open-model run used `qwen/qwen3-vl-32b-instruct` on OpenRouter. When the model encountered a CAPTCHA on Google Search at step 4, it did not claim success; it switched to weather.com and, at step 16, read 64°F, Sunny, feels like 62°F, high 74°F, and low 55°F from San Francisco's Today page. All 16 of 16 API responses reported the requested Qwen3-VL model, and 15 valid step screenshots plus the read-only action trajectory passed independent deterministic acceptance. This result demonstrates that the open-model API path runs successfully; it does not mean that the Anthropic-native `computer` tool arm has been reproduced.

### A Computer Use Agent That Can Watch Animations and Hear Sound

So far, Computer Use perception has rested on an implicit assumption: **the screen is static**—take a screenshot, reason about the next step, click, and take the next screenshot. Real screens play videos, flash notifications that vanish in seconds, and play audio from meetings. An Agent that opens its eyes only once every 3–5 seconds and has no ears at all is blind and deaf to everything that happens between two frames. Watching a screen recording, joining a meeting, following a voice prompt, catching a dialog box before it disappears—this whole category of everyday computer work is effectively off-limits to today's Computer Use Agent.

What truly needs to be redesigned here is not the "action interface," but the "**observation interface**"[^ch9-9]. The core idea is to decouple **observation** (continuous, adaptive, multimodal) from **action** (discrete), creating a perceptual middleware layer that sits between the environment and any off-the-shelf Computer Use model without requiring retraining. We can call this the Agent–Computer Observation Interface (AOI). It has three "gated" components: First, **inter-frame keyframe capture**—use a very cheap pixel gate to skip nearly unchanged frames, then use a small model to determine if a meaningful change has occurred, capturing a frame only when there is a change, resulting in near-zero cost for static screens; Second, **volume-gated speech transcription**—only invoke speech recognition when there is sound, giving the Agent "ears" for the first time; Third, and most critically, **converting observations into persistent textual descriptions**—have the model describe the captured frame in a single sentence (e.g., "The popup just said the release date has been changed to April 28th"), and **even if the original image is later cleared from the context, this text remains in memory**, carrying the dynamic information forward in textual form.

The counterintuitive finding is that what really matters is not frame selection but converting selected frames into persistent text, because text is the modality LLM Agents handle best. Across eight models, ranging from 7B-parameter models to frontier-scale systems, this middleware delivered gains of +17 to +48 percentage points without any retraining, with the widest gap on voice tasks: with the perceptual layer in place, the Agent could finally complete voice tasks that had been "audible but unactionable." It is not a one-size-fits-all configuration, though—on some newer models, injecting too many image tokens crowds out reasoning and drags performance down. So the components should be **chosen per model**, not switched on wholesale. It is the same lesson as the Set-of-Mark-versus-coordinate-prediction trade-off: there is no silver bullet in perception schemes; you configure them to suit the model's temperament.

[^ch9-9]: For the complete mechanism and per-model ablation of the three components—gated keyframes, on-demand transcription, and narrating frames into persistent text—see Bojie Li and Noah Shi. *Agent-Computer Observation Interfaces Enable Dynamic Computer Use.* arXiv:2606.29472, 2026.

### World Models for Computer Use

The observation interface answers “what happened between screenshots?” by making dynamic changes arrive sooner and persist in memory. It does not by itself remove the planning overhead: a standard Computer Use Agent may still repeat the serial “screenshot—think—click” loop and reconsider the next step after every action. **OSWorld-Human** shows that human-level task accuracy can coexist with substantially more steps and waiting time than a person needs.

People operate a desktop predictively. They anticipate the consequence of an action; when the observed state agrees with that prediction, they continue along the existing plan instead of replanning from scratch. Only a mismatch sends them back to observation and planning. This is speculative execution, and a world model makes it available to an Agent. **A world model solves the other half of the problem**: it predicts what the desktop may become after an action, so the Agent can continue directly when reality matches the prediction and replan or stop when it does not.

A desktop state is more than pixels: it includes the active window and focus, scroll position, input contents, loading and permission state, and network responses. Actions include clicking, typing, scrolling, dragging, and waiting. A useful world model encodes the current state, predicts state changes for candidate actions, and passes those predictions to the planner. It need not render a photorealistic future screenshot; task-relevant state differences are enough to rank actions, prepare the next step during loading, and gate irreversible operations.

Induction Labs’ **Photon-1** is one recent example. It compresses frames into discrete latent tokens and autoregressively predicts the next state representation after an action. Its attached image generator visualizes latent states but is not required for inference. The result should be treated as a predictive sidecar, not as a replacement for fresh screenshots or structured state checks in the real environment.

### Mobile: Ecosystem Barriers Are Harder Than Technology

Computer Use is also expanding to mobile devices. Mobile and desktop systems do differ technically: instead of relying on mouse coordinates and keyboard input, the mobile action space typically uses the system's accessibility-service API (e.g., Android's `AccessibilityService`) to read interface elements and issue clicks or enter text. Interaction also shifts from a mouse pointer to touch gestures, changing the meaning of coordinates. The same `(x, y)` position might indicate a tap, a long press, or the starting point of a swipe, so the action must also specify a gesture type. Mobile benchmarks such as AndroidWorld, introduced in Chapter 6, evaluate an Agent's ability to complete tasks in real applications within this action space.

However, what truly hinders mobile Computer Use is often not these technical differences, but ecosystem barriers. Some phone manufacturers have attempted to integrate AI assistants into consumer-grade phones so that the assistants can automatically operate everyday apps like WeChat, Taobao, and Alipay, but they quickly encountered platform restrictions.

This reveals a unique challenge for Computer Use: **ecosystem barriers**. The fundamental reason behind these restrictions is a conflict of business models. The core monetization logic of traditional internet applications is **traffic and attention**: users see ads while scrolling through feeds, are guided by recommendation algorithms when searching for products, and make impulse purchases while browsing pages. When an Agent operates on the user's behalf, that monetization chain is bypassed entirely: the AI ignores ads, makes no impulse purchases, heads straight for the goal, finishes the task, and leaves. For platforms that live on advertising and traffic, every Agent operation erodes the foundation of the business model.

This means that Computer Use faces not only technical countermeasures such as CAPTCHAs, but also a **structural conflict of interest**. This conflict will be difficult to resolve in the short term and poses a greater obstacle to consumer adoption than purely technical problems.

### Real-Time Performance: The Unsolved Core Challenge

**OSWorld**, whose evaluation methodology is described in Chapter 6, is a widely used benchmark for Computer Use that tests an Agent's ability to complete cross-application tasks in real Ubuntu/Windows/macOS environments. Early general-purpose models achieved only about a 20% success rate on this benchmark. Subsequent specialized models and more powerful general-purpose models have continuously pushed the success rate higher, gradually approaching human-level performance as of this writing. However, success rate is far from the finish line—the real bottleneck has shifted from "can it do it correctly?" to "can it do it quickly?"

The **OSWorld-Human** efficiency study yields a sobering finding: even when the task ultimately succeeds, the Agent needs markedly more steps than a human, and per-step inference latency keeps growing as the task progresses—the longer the context, the slower the model decides, so late steps often take far longer than early ones. A document-formatting tweak that takes a human tens of seconds may take an Agent several minutes to complete. **Human-level accuracy is not the same as practical usability; efficiency is the true bottleneck.**

The root cause mirrors the speech scenario: in the serial "screenshot-think-click" loop, even with every stage optimized to the hilt, the step-by-step accumulation of delay remains unacceptable. The deeper problem is that today's Computer Use cannot think ahead at all. If an Agent could predict its next move while executing the current one—working out where to click next while the page is still loading—it could overlap thinking with execution and cut total latency sharply (the same demand as thinking-while-speaking earlier in this chapter and the "continuous thinking" asynchronous Agent of Chapter 4, recast here as thinking-while-operating).

Unlike the speech domain, there is currently no systematic solution for improving the real-time performance of Computer Use itself—making the "screenshot-think-click" loop faster—and it remains stuck in a discrete loop of frame-by-frame screenshots. However, a workaround has already been proven effective, using the fast-slow decoupling that appears repeatedly in this chapter: since it is difficult to make a slow Computer Use agent faster, **don't make the user wait for it**. Use two models concurrently: a fast model for speech and a slow model for computer operation[^ch9-10]. The fast model handles real-time voice conversation, while the cutting-edge VLM operates step-by-step in the browser. The two communicate only through a minimal "plain text contract": each time the slow Agent performs an action, it updates a rolling status summary ("Filling out the form, still need your date of birth"). The fast Agent uses this to answer the user in real time and relays any new information the user provides verbally to the slow Agent. Crucially, **the fast Agent must never say "done" until the status summary confirms completion**. This is the scenario of "talking on the phone while letting the computer operate itself." In experiments, this decoupling made voice responses about 15 times faster than a single model that operates and speaks at once (median latency 0.58 seconds vs. 8.64 seconds), with no loss in task success rate. Remove the text channel between fast and slow, and success collapses to zero—the key information users give verbally can no longer reach the browser. This is the same idea as the Latent Bridge earlier and thinking-while-speaking in the speech scenario: when one component is inherently slow, let a fast one fill the user's waiting time—and that "plain text contract" is, at bottom, the Agent Status Bar concept introduced in Chapter 2. Speeding up the Computer Use loop itself may well be the next important research direction, but hiding the slowness behind fast-slow decoupling is already a workable answer.

[^ch9-10]: The complete design of the speech-operation fast-slow decoupling and the "plain text contract" can be found in Bojie Li and Noah Shi. *Talking While Acting: Real-Time Voice for Slow Computer-Use Agents.* 2026 (forthcoming).

## Robot Manipulation: From Real-Time Control to Training and Generalization

Voice Agents fight latency in the auditory modality; Computer Use does so in the visual modality. When an Agent must control a robot in the physical world, latency and multimodality bite harder still—actions have irreversible consequences, and one collision can damage the object or the robot itself. This section first shows how robots tame the real-time control problem with a two-layer architecture and action chunking, then turns to the harder problem they face today—training and generalization: where the data comes from, and how models transfer across tasks and platforms.

### Hardware Is Not the Bottleneck; Algorithms Are

Why have robots not been widely adopted in open-ended, general-purpose settings? Is the bottleneck hardware or algorithms? The XLeRobot project provides a compelling counterexample: when remotely controlled by a human through a VR headset, a dual-arm wheeled robot costing less than $1,000 can already perform a wide range of household tasks smoothly. Unitree robots can likewise handle more complex household tasks requiring dexterous hands when operated by a human. Teleoperation latency is around 100-200ms, close to the response time required for physical interaction. On today's low-cost platforms, sensor resolution, actuator precision, and control frequency—the number of times per second a robot updates its action commands—are already sufficient for practical tasks. Lower control frequencies produce less fluid motion and increase jitter or deviation from the target trajectory.

This claim needs a clear boundary: the teleoperation example demonstrates only that existing low-cost hardware, combined with human intelligence, is sufficient for **household manipulation tasks that rely primarily on visual feedback**. It does not mean that the hardware is adequate in every respect. The absence of tactile sensing and the cost and reliability of dexterous hands remain well-known limitations. For tasks that depend heavily on precise force control and tactile feedback, hardware may indeed be the bottleneck. The statement "hardware is not the bottleneck" is therefore limited to the class of tasks discussed in this section.

For these tasks, the real gap lies in the algorithmic layer, which is elaborated in the following two subsections.

> **Experiment 9-7 ★: XLeRobot Teleoperation Experience**
>
> **Goal:** On a real XLeRobot, a human operator teleoperates the robot through the same task: put the red cup in the tray, put the yellow waste paper in the waste bin, then re-observe and verify the desktop state.
>
> **Principle:** A few-hundred-dollar arm can complete this multi-step task under human teleoperation. For this task, the hardware body is not the bottleneck; the gap lies in perception, planning, timing, closed-loop control, and failure recovery.

### Two-Layer Architecture: Separation of Planning and Control

Robots need to make decisions at two different time scales to complete complex household tasks. The first layer is slower **long-horizon planning**: decomposing a high-level instruction like "tidy the desk" into a sequence of sub-goals (move the red cup to the tray, put the yellow waste paper in the bin, then verify the final state). This requires understanding environmental semantics, reasoning about task dependencies, and planning multi-step action sequences—similar to how a person thinks about "what to do first and what to do next" before starting. The second layer is faster **VLA control** (Vision-Language-Action model): executing each specific operation ("approach the cup," "grasp it," "place it in the tray"), continuously outputting control signals based on the current visual input and language instruction to ensure smooth and coherent robot motion.

This two-layer architecture separates responsibilities effectively: long-horizon planning handles "what to do," while VLA control handles "how to do it." The combination of slow high-level decision-making and fast low-level execution closely parallels the fast-slow architecture described earlier for speech: both assign complex reasoning and real-time response to different modules. The planning/control split, however, corresponds to slow deep reasoning versus fast real-time response, not to the thinking/expression split between MPS's Formulation Brain and Articulation Brain in Solution 3. MPS separates thinking from speaking; the robotics architecture separates global planning from real-time execution. The two architectures therefore divide the work along different dimensions.

Real-time constraints have not disappeared; they have been pushed down into the VLA control layer, where **Action Chunking** helps mitigate them (see the "VLA Control" subsection below). The model generates a short sequence of future actions in a single inference, and the control thread replays them at high frequency, amortizing inference latency over the execution of the entire sequence. This creates an unavoidable trade-off between smoothness and responsiveness: longer chunks spread the latency over more actions and produce smoother motion, but the model receives no new visual input during that interval and therefore reacts more slowly to sudden changes, such as an object being moved or a hand blocking the way. The two-layer architecture does not eliminate this tension; it merely relocates it.

The chapter's focus now shifts: in robotics, the real-time tension has been partly relieved by two-layer decoupling and action chunking, while **training and generalization**—how to obtain enough demonstration data and make models generalize across tasks and platforms—have become the central concerns. The following subsections extend the themes of Chapter 6's simulation environments and Chapter 7's reinforcement learning into the physical world.

This new challenge falls chiefly on the VLA control layer. Think of VLA as "VLM + action output": the **VLM** (Vision-Language Model—a large model that understands both images and text) handles perception and reasoning, while the VLA must also act—and action is where the real difficulty lies. Today, the VLA control layer is trained primarily through imitation learning, or **behavior cloning**, which learns mappings from observations to actions using large collections of human demonstrations. OpenVLA, RT-2, and π₀ all fall into this category. Reinforcement learning has emerged more recently as a complementary technique. Although RL-trained VLAs can perform well on individual tasks, they often generalize poorly. For example, SimpleVLA-RL from Chapter 7 reports strong single-task results on LIBERO, but it is trained separately for each task rather than as one unified model that generalizes zero-shot across all tasks. This one-training-run-per-task pattern means that each new task requires fresh data collection and retraining.

The following two sections delve into the specific technical solutions for long-horizon planning and VLA control, respectively.

### Long-Horizon Planning: From VLM to Specialized Embodied Reasoning Models

General-purpose VLMs already possess decent embodied reasoning capabilities. Google DeepMind's **Gemini Robotics-ER 1.5** is specifically optimized for Embodied Reasoning (understanding the position, movement, and causal relationships of objects in the physical world). It achieves an average of 62.8% across 15 academic benchmarks (Point-Bench, RefSpatial, RoboSpatial, BLINK, etc.), surpassing GPT-4o (60.6%) and Gemini 2.5 Pro (59.3%). Key advantages include: advanced spatial understanding and object localization, temporal reasoning (predicting action consequences like "what happens if I push this cup"), task sequencing (decomposing high-level instructions into smaller steps), and native support for thinking mechanisms and tool calls.[^ch9-2]

[^ch9-2]: Google DeepMind, "Gemini Robotics-ER 1.5." https://deepmind.google/models/gemini-robotics/gemini-robotics-er/

> **Experiment 9-8 ★: Measuring the Ideal-Control Upper Bound for the Same Task in Simulation**
>
> **Goal:** Run the same desk-tidying task with an ideal controller that makes no perception or action-selection errors, establishing a reproducible upper bound.
>
> **Principle:** This is a reference for the control ceiling, not evidence that the real robot has been run.

> **Experiment 9-9 ★★: Autonomous Control of a Real XLeRobot with Gemini Robotics-ER 1.5**
>
> **Goal:** Replace the human operator with an Agent that observes the desktop and calls bounded pick, place, and verify skills, while keeping the real XLeRobot, task, and success criteria from Experiment 9-7 unchanged.
>
> **Principle:** The direct comparison exposes gaps in perception, planning, timing, closed-loop control, and recovery—not a new mechanical limitation of the robot body.

### VLA Control: From Demonstration Data to Cross-Embodiment Generalization

In the execution layer of the two-layer architecture, three representative models—RT-2, OpenVLA, and π₀—all focus on VLA control, i.e., outputting robot actions in real time based on camera images and language instructions (Figure 9-10). They follow two different approaches to action representation: discrete action tokens and continuous trajectory generation.


![Figure 9-10: VLA Architecture (Vision-Language-Action)](images/fig9-11.svg)


**RT-2 and OpenVLA: The Discrete Action Token Route.**

**RT-2** pioneered this route: it directly fine-tunes a large-scale vision-language model, discretizing the robot's continuous actions into tokens and outputting them autoregressively one by one, like generating text. It leverages the generalization ability of the pre-trained model to improve zero-shot transfer to new objects and instructions. **OpenVLA** follows RT-2's action representation scheme, unifying the language model and vision encoder in a single architecture. It takes images and text instructions as input and outputs action tokens. Training is done in two stages: first, pre-training on the large-scale cross-platform dataset Open X-Embodiment (covering real-world manipulation demonstrations from over 20 robot platforms) to learn general manipulation knowledge (action patterns like "grasp" and "place" are common across different robots); second, fine-tuning with a small amount of data for a specific platform. Because their action representations are similar, the practical difference emphasized here lies in openness and engineering choices: RT-2 and its training data are internal to Google, while OpenVLA is fully open-source—an open-source backbone model (Llama 2 plus a vision encoder) paired with public datasets, making the OpenVLA stack reproducible and extensible by the wider community.

**Action Chunking: A Universal Frequency Compensation Technique in the VLA Domain.**

Because large-model inference is slow, VLAs run inference at much lower frequencies than traditional robot controllers operate. Traditional control typically runs at 50-1000Hz, whereas VLA inference usually runs at only about 1-10Hz—a gap that can range from one to three orders of magnitude. The original OpenVLA illustrates this problem: it outputs only one action per inference, at roughly 6Hz using single-step autoregressive prediction, and its jerky motion is one of its most criticized shortcomings. **Action Chunking** is a general technique for bridging this gap. First proposed by ACT (Zhao et al., 2023) and later adopted by π₀, OpenVLA-OFT, and others, it has the model generate a short sequence of future actions in each inference rather than a single action. In a typical π₀ configuration, for example, the model generates a 0.5-1 second chunk containing 25-50 actions at a 50Hz control frequency. The control thread executes those actions sequentially at high frequency while the model generates the next batch asynchronously in the background. As long as inference finishes before the current action batch finishes executing, the robot can maintain continuous, smooth motion—much like video buffering prevents playback from stuttering by loading content in advance.

**π₀: The Continuous Trajectory Generation Route.**

The true divide in action representation is not between RT-2 and OpenVLA, but between **discrete tokens and continuous trajectory generation**. **π₀** follows the latter route: rather than predicting discrete action tokens one by one, it uses flow matching, a continuous generation method related to diffusion models, to begin with random noise and iteratively "denoise" it into a smooth, continuous action trajectory. This representation pairs naturally with action chunking and performs better on tasks such as dexterous manipulation that demand precise, fluid motion. As an analogy, the discrete-token approach resembles choosing commands such as "5 degrees left" and "3 cm forward" one at a time from a menu. Continuous trajectory generation is more like an artist sketching the entire curve and then refining it stroke by stroke.

### Sim2Real Transfer: The Gap from Simulation to Reality

Chapter 6's simulation section already explained where the sim-to-real gap comes from and how domain randomization counters it, so we won't repeat that here. In a nutshell: simulation can never perfectly reproduce real-world physics, visuals, and hardware, so training randomizes those parameters over a wide range, forcing the policy to learn a representation robust to those variations (Figure 9-11). What follows is how that principle lands on a real robotic arm.

![Figure 9-11: Sim2Real Gap and Domain Randomization](images/fig9-12.svg)

This approach has produced several notable successes. OpenAI's Dactyl project achieved in-hand cube reorientation, and subsequent work used Automatic Domain Randomization (ADR) to solve a Rubik's Cube with one hand. ETH Zurich's ANYmal quadruped has demonstrated robust locomotion over difficult outdoor terrain such as snow and gravel.

What this chapter adds are the two engineering steps you cannot skip when taking domain randomization to a real robot. The first is **calibrating the randomization range**: the range cannot be set on a hunch. Too narrow, and it misses real-world variation; too wide, and training gets harder and yields a suboptimal policy that "handles everything, masters nothing." In practice, the distribution of key parameters (friction coefficient, motor response delay) is first **measured and calibrated** from real-world data and sampled within that range; if the sim-trained policy's performance drops noticeably on the real robot, the range is widened step by step until the sim-to-real gap converges to something acceptable. The second is **visual alignment**: precisely calibrating camera pose between simulation and reality (environment alignment), and randomly splicing real-world background images into the simulated render (greenscreen background replacement) so that the simulation looks as much as possible like what the real robot sees. The paired experiments below illustrate these principles.

> **Experiment 9-10 ★★: Comparing Three Autonomous Loops in Simulation**
>
> **Goal:** Keep the task and tools fixed while comparing open-loop execution, stepwise checking, and predictive closed-loop control.
>
> **Principle:** Stepwise checking enables local failure recovery; a world model permits continuation when prediction agrees with reality and replanning when it diverges. The final state is always confirmed with a fresh observation.

> **Experiment 9-11 ★★★: RGB Cross-Environment Test for the Same Task**
>
> **Goal:** Vary backgrounds, object appearance, lighting, and visual noise while keeping the desk-tidying task fixed, testing whether a vision policy learned in simulation remains robust across RGB environments.
>
> **Principle:** Visual diversity can improve robustness, but it does not replace real-robot calibration or a complete safety and verification loop.
>

### 2026 Update: Aligned Desk-Tidying Experiments

The robot experiments now use one bounded task throughout: **put the red cup in the tray, put the yellow waste paper in the waste bin, then re-observe and verify the desktop state**. XLeRobot is a few-hundred-dollar arm, and a human can complete this multi-step task through teleoperation. That is direct evidence that, for this task, the hardware body is not the bottleneck; the autonomous gap lies in perception, planning, timing, closed-loop control, and recovery.

The five experiments are deliberately paired:

1. **Experiment 9-7**: teleoperate the real XLeRobot and establish the human-controlled hardware upper bound.
2. **Experiment 9-8**: measure the ideal-control upper bound for the same task in a non-actuating simulator.
3. **Experiment 9-9**: replace the human with Gemini Robotics-ER 1.5 and autonomously control the real XLeRobot.
4. **Experiment 9-10**: compare open-loop, stepwise-checking, and predictive closed-loop strategies in the same simulator.
5. **Experiment 9-11**: vary backgrounds, object appearance, lighting, and visual noise to test RGB cross-environment robustness.

The earlier navigation example is not part of this experiment sequence: a fixed-base arm should be evaluated on a task it can physically perform.

The planner still expresses the task as a dependency graph with preconditions and success checks:

1. “Move to the desk and stop 30 cm from its edge.”
2. “Put the yellow waste paper in the waste bin; verify its new location.”
3. “Keep the red cup stable and place it in the tray; verify that it is inside.”
4. “Re-observe the desktop and verify both placements.”
5. “Stop in a safe posture when the final state is confirmed.”

This is a dependency graph, not a paragraph of prose. If the user says “put the laptop away first,” the system updates the goal priority. If the cup falls, it stops at a safe point, records facts such as cup.orientation=fallen and laptop.at_risk=true, invalidates the stale suffix, and replans: protect the laptop, contain the spill, re-observe, then resume only the unaffected tasks. Completed actions are not repeated. Emergency events cancel the current chunk; ordinary updates wait for the next safe point.

### Streaming execution

Planning and execution can overlap. Once a safe prefix is complete, the planner streams a complete command to the executor while continuing to plan the suffix. A command event must be complete and auditable:

```text
{"type":"command.commit","seq":12,"command_id":"desk-02","command":"put paper in bin","preconditions":["paper.visible","bin.reachable"],"success":"paper_count=0","cancel_at":"before_grasp"}
```

The executor reports started, succeeded, cancelled, or failed. The planner uses these observations to update dependencies and applies backpressure when the queue is stale or full. Streaming reduces time to the first safe action; it does not authorize executing partial JSON or unverified model thoughts.

### Why current VLAs generalize poorly

OpenVLA is not literally trained by updating only its projector: the original work reports full fine-tuning as well as frozen-vision, last-layer, and LoRA variants. The deeper criticism remains valid. A huge text/image pretraining corpus is connected to a much smaller robot dataset through a narrow adaptation path, and downstream low-cost adaptation often concentrates new behavior in a projector, LoRA modules, or an action head. Behavior cloning learns “observation + instruction → action chunk,” not counterfactual physical consequences. Embodiment-specific action spaces and stale action chunks further limit transfer. A language backbone knows the word “cup”; it does not thereby know how friction, liquid, contact, and power cables behave.

### World models

A world model learns an actionable transition:

```text
state + candidate action -> predicted future state -> select and verify an action
```

It is broader than V-JEPA alone. The family includes latent predictive models (V-JEPA 2), interactive generative models (Genie 3 and Cosmos), World-Action Models (GeniWorld and Robust-WAM), latent-action learning from unlabeled video (LAWM-3D), and model-based RL (Dreamer and MuZero). The value is to learn from observation at scale, test counterfactual actions before execution, separate shared dynamics from embodiment-specific control, and replan when prediction and reality diverge.

Recent 2026 preprints explore shared dynamics priors and embodiment-specific heads (DyPES-VLA), visual-action representations for OOD closed-loop manipulation (GeniWorld), 3D-aware latent actions from human video (LAWM-3D), semantic foresight alignment (Robust-WAM), and asynchronous real-time deployment. These are promising research results, not solved generalization.

## Chapter Summary

On the surface the three scenarios could hardly differ more, yet the twin hurdles of latency and multimodality shadow them all. Voice Agents have evolved from serial pipelines to end-to-end and full-duplex systems, and from separate fast and slow thinking to thinking while speaking. Computer Use now approaches human accuracy on benchmarks like OSWorld, but it takes far more steps than a human, and each step takes longer as the task progresses—an efficiency gap with no systematic solution yet. For robots performing visually guided manipulation tasks, the bottleneck has moved from hardware to the VLA control layer's ability to generalize across tasks (tactile sensing and dexterous hands remain unresolved hardware limitations). The next chapter turns to collaboration among multiple Agents—a challenge of a different dimension.

## Mechanism skeletons

The following sketches isolate the control relationships discussed in this chapter.

### Streaming cancellation

```python
while audio_is_arriving:
    partial = asr.push(audio_chunk)
    if endpoint_is_probable(partial):
        candidate = llm.start(partial)
        if later_audio_changes_meaning(partial):
            cancel(candidate)                 # speculative cancellation
        else:
            tts.enqueue_stable_segments(candidate)

on_final_transcript(text):
    commit_or_restart(text)
```

### Computer Use safety loop

```python
observation = capture_screenshot_and_accessibility_tree()
proposal = model.decide(task, observation)
action = validate_schema_and_coordinates(proposal)

if action.is_irreversible and not user_or_policy_approval(action):
    stop("approval required")
else:
    execute_in_sandbox_or_scoped_session(action)
    new_observation = capture_after_settle()
    if not verify_goal_progress(new_observation, action):
        rollback_if_possible_or_replan()
```

### Action-chunk preemption

```python
chunk = vla(current_observation, skill)
for action in chunk:
    low_level.execute(action)
    if safety_event() or observation_changed_significantly():
        low_level.stop()
        discard_remaining(chunk)
        reobserve_and_replan()
        break
```

Keep the boundary explicit: observations and evidence come from the environment, while the Harness decides what may be executed.

## Thought Questions

1. ★★ The end-to-end model for voice Agents merges ASR-LLM-TTS into a single model, reducing latency but losing modularity. If the end-to-end model makes an error in a specific stage (e.g., speech recognition), debugging and fixing it is much harder than in a serial pipeline. How would you design an observability system for an end-to-end voice Agent?
2. ★ Step-Audio R1 achieves "thinking while speaking" through the MPS dual-brain architecture. However, humans, when "thinking while speaking," often say things before they have fully thought them through, self-correct, or use filler words. Should an Agent's "thinking while speaking" mimic these human characteristics?
3. ★★ SoM (Set-of-Mark) and its structured variants (DOM element indexing) convert Computer Use's visual localization from open-ended coordinate prediction to closed-set ID selection, but they all require detecting and annotating UI elements first—whether via a segmentation model or the DOM. If the interface contains non-standard controls or dynamically changing elements, the annotations may be incomplete or inaccurate. In such cases, should we fall back to coordinate prediction?
4. ★★ Thousand-dollar robot platforms like XLeRobot make teleoperation data collection inexpensive. However, the quality of teleoperation data depends heavily on the operator's skill. How would low-quality data from an unskilled operator affect the training of a VLA model? How can low-quality data be automatically filtered during the data collection phase?
5. ★★★ This chapter covers three interaction modalities: voice, Computer Use, and robotics. A common trend across these modalities is the evolution from serial pipelines to end-to-end models. If this trend continues, what might the Agent interaction layer look like in five years?
6. ★★★ Current Computer Use operates in a discrete "screenshot → action → screenshot" loop, where each observation is a static frame. But human perception of a screen is continuous—we see animations play, observe loading progress, and understand video content. This means today's Computer Use cannot handle tasks requiring temporal visual understanding. How would you redesign the perception layer to support understanding of continuous visual streams?
7. ★★ DOM/Accessibility Tree element indexing works well on standard web applications, but an increasing number of software interfaces (Canvas/WebGL rendering, cross-platform custom-drawn controls) do not provide accessible structured information, relying solely on visual annotation or coordinate prediction. Do you think Computer Use should bet on a purely visual approach, or maintain both structured and visual paths? What are the costs and benefits of maintaining both paths?
8. ★★ VLA models use action chunking—as mentioned in the text, π₀'s typical configuration generates 25-50 future actions at 50Hz—to hide inference latency within execution time. However, if the environment changes suddenly during execution (e.g., an object is moved), the pre-generated action sequence becomes invalid. How can we balance the efficiency advantage of action chunking with the need for responsiveness to environmental changes?
9. ★★★ All three scenarios in this chapter (voice, Computer Use, robotics) face the latency problem of the "perceive-think-act" loop and are evolving toward parallelized fast and slow thinking. In voice, this manifests as "correcting after misspeaking"; in Computer Use, as "clicking first, then looking"; in robotics, as "taking a step, then looking." How can we ensure that these actions based on fast thinking do not lead to irreversible consequences?
