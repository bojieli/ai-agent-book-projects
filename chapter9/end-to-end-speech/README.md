## English

# Experiment 9-4 Companion: End-to-End Speech Reasoning vs. Cascaded Pipeline

Corresponds to Chapter 9 of *Deep Understanding of AI Agents*, **Experiment 9-4 ★★★: Using Step-Audio R1 for End-to-End Speech Reasoning**.

## Purpose

The core of Experiment 9-4 in the book is the **end-to-end speech reasoning model Step-Audio R1**: a single model that directly "listens → thinks → speaks", combining ASR, LLM, and TTS into one. It transmits paralinguistic information (emotion, tone, speech rate, ambient sound) directly in the latent space, resulting in lower latency and more natural prosody.

Since Step-Audio R1 has no public endpoint and requires multi-GPU deployment, it is difficult for readers to run directly. Therefore, this demo uses OpenAI's speech-to-speech model `gpt-audio` as a **real, runnable end-to-end representative**: it also takes "audio in → single model → audio out", returning a spoken answer and its transcription in a single call, with **no** separate ASR/LLM/TTS stages in between. The demo lets you **compare the same problem** across real end-to-end and cascaded pipelines, allowing you to directly observe the differences in **latency** and **information loss (tone, paralinguistics)**—the latencies for both paths are measured in real-time during this run, and both output audio files are validated with `ffprobe`.

The demo provides two task types (`--task`), corresponding to the two comparison axes in the book:

- **`math` (default)**: Verbally presented math problems (Spoken-MQA style). The answer depends only on "what was said," so the accuracy of cascaded and end-to-end approaches is comparable (corresponding to the "Self-Cascading" section in 9.3). Therefore, this task primarily compares **latency**.
- **`paralinguistic`**: A phrase where "the answer depends on how it is said." In the cascaded pipeline, ASR compresses speech into plain text, so the LLM only receives the literal words. Any emotional judgment is **Textual Surrogate Reasoning** (Section 9.3, "The Problem of Textual Surrogate Reasoning")—guessing emotion from vocabulary. The end-to-end model, however, directly hears acoustic features (speech rate, pitch) and responds accordingly. This task compares the **information loss** dimension, which is the core problem that **MGRD (Modality-Grounded Reasoning Distillation)** in the book aims to solve.

## Principle: Three Speech Paradigms

The book categorizes speech architectures into three paradigms (chapter9.md "Three Paradigms of Speech Architecture"):

| Paradigm | Structure | Characteristics |
|----------|-----------|-----------------|
| **Cascaded** | ASR → LLM → TTS (three independent models in series) | Clear modules, independently tunable, good interpretability; but latency accumulates serially, models connect via plain text interfaces, and emotion/speech rate/tone/ambient sound are almost entirely lost at the interface |
| **End-to-End Omni** | Single model "listens→thinks→speaks" (Step-Audio R1, gpt-audio, etc.) | Lower latency, preserves paralinguistic information, natural prosody, can "think while speaking"; cost is large training data requirements and poor interpretability. **Still assumes "turn-taking," using VAD to segment turns** |
| **Full-Duplex** | Single model listens and speaks simultaneously, removing the "turn-taking" assumption (Moshi, GPT-Live) | Continuously processes input and output simultaneously, making decisions multiple times per second about whether to speak/listen/stop/interrupt; this demo does not cover this |

This demo focuses on the **comparison** between the first two paradigms: End-to-End (Paradigm 2) vs. Cascaded (Paradigm 1).

**Step-Audio R1 is a representative of Paradigm 2 that internalizes "reasoning" within a single model**: it truly reasons based on acoustic features through MGRD (Modality-Grounded Reasoning Distillation) and achieves "thinking while speaking" through the MPS dual-brain architecture. `gpt-audio` is a representative of the same paradigm (audio in, single model, audio out) that readers can directly call.

## Running

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure Key
cp env.example .env
# Edit .env, fill in a valid OPENAI_API_KEY (requires access to gpt-audio / whisper-1 / tts-1).
# Audio endpoints (end-to-end gpt-audio, cascaded ASR/TTS) are only available via direct OpenAI connection—OpenRouter has no audio endpoints.
# Therefore, this experiment requires a direct OpenAI API Key. Optional: additionally configure OPENROUTER_API_KEY, then the plain-text
# LLM reasoning in the cascaded pipeline will automatically switch to OpenRouter's gpt-5.6-luna (bypassing organizational identity verification for direct gpt-5.6* connections).

# 3. Run (default: math task, runs both end-to-end + cascaded on the same problem, prints real latency comparison)
python demo.py

# Paralinguistic task: highlights the advantage of end-to-end over cascaded (end-to-end hears tone, cascaded only sees text)
python demo.py --task paralinguistic

# Use a real emotional recording as input (better demonstrates tonal differences than TTS synthesis; mutually exclusive with --question)
python demo.py --task paralinguistic --audio-input my_voice.wav

# Run only end-to-end / custom question / change voice / change output directory
python demo.py --skip-cascade
python demo.py --question "The high-speed train from Beijing to Shanghai takes 4 hours. If I depart at 9:00, what time will I arrive?"
python demo.py --voice nova --output-dir out
python demo.py --help

# Switch to a self-deployed real Step-Audio R1 (overrides environment variables)
python demo.py --step-audio-endpoint http://localhost:8000/v1/audio/chat

# 4. (Optional) Listen to the generated speech answers
ffplay audio/answer_end_to_end.wav   # End-to-end
ffplay audio/answer_cascade.mp3      # Cascaded
```

See all CLI parameters with `python demo.py --help`: `--task`, `--question`, `--audio-input`, `--e2e-model`, `--step-audio-endpoint`, `--voice`, `--output-dir`, `--skip-cascade`. The default behavior (`python demo.py` runs the math task, end-to-end + cascaded comparison) remains consistent with the previous version.

Requires `ffprobe`/`ffplay` (for validation, listening to audio): `brew install ffmpeg` (macOS).

## Example Expected Output (Real Excerpt)

```text
Paradigm 2: End-to-End Speech Reasoning (backend=gpt-audio, model=gpt-audio)
Form: Audio in → Single model "listens→thinks→speaks" → Audio out (single call, no separate ASR/LLM/TTS stages)
[Single Stage] End-to-End (listens→thinks→speaks, single model call)  |  Latency=7.21s
    Speech answer transcription (produced incidentally by the model, not an intermediate text stage): Let's calculate: Xiao Ming has 12 yuan, buys 3 pencils... finally has no money left.
    ffprobe validation: {'format': 'wav', 'duration(seconds)': 20.75, ...}
End-to-End Total Latency (single model forward pass): 7.21s

Paradigm 1 (Comparison Baseline): Cascaded Pipeline ASR → LLM → TTS
[Stage 1] ASR Speech Recognition  |  Model=whisper-1  |  Latency=1.35s
[Stage 2] LLM Reasoning          |  Model=gpt-5.6-luna  |  Latency=1.92s
[Stage 3] TTS Speech Synthesis   |  Model=tts-1  |  Latency=3.66s
Cascaded Total Latency (serial sum of stages): 6.94s

End-to-End vs Cascaded: Real Latency Comparison
【1】Measured Total Latency  End-to-End 7.21s; Cascaded ASR(1.35)+LLM(1.92)+TTS(3.66)=6.94s
【3】Table 9-1 from the book (cited from Step-Audio R1 paper, not produced by this demo)
    MPS Speak-First 92.8% / Full TBS 93.0% ……
```

### Real Excerpt from Paralinguistic Task (`--task paralinguistic`, one real run)

For the same sentence "Alright, that's it then. I have no objections." (TTS synthesized, relatively flat emotion), the responses from the two paths:

```text
[Stage 1] ASR Speech Recognition  |  whisper-1  → 「Alright, that's it then. I have no objections.」   ← The cascaded LLM only receives this plain text

Responses from both paths to the same audio segment (allowing direct comparison of whether "how it was said" was heard):
    Cascaded (relying only on ASR text, Textual Surrogate Reasoning) → "It sounds like you're a bit resigned, maybe not entirely satisfied with this decision. ..."
    End-to-End (directly hearing acoustic features)        → "It sounds like you're a bit resigned, your speech rate isn't fast, and your pitch is quite steady. ..."
```

The difference is clear: **Cascaded** can only guess resignation from the literal words "no objections" and cannot cite any acoustic basis (the "Textual Surrogate Reasoning" from the book); **End-to-End** directly references acoustic features like "speech rate isn't fast, pitch is quite steady"—this is precisely what MGRD in the book aims to teach models: "thinking with your ears." Note that the default input is TTS synthesized, with relatively flat emotion, which weakens the difference; using `--audio-input` to feed a real emotional recording will make the contrast more apparent.

**Regarding Table 9-1**: The Spoken-MQA / URO-Bench scores printed in the demo are **cited from the Step-Audio R1 paper** (reproduced as Table 9-1 in the book), not generated by this demo—the only real outputs from this demo are the measured latencies and the two real audio files. Latency numbers fluctuate with network conditions and OpenAI load; `gpt-audio` produces the entire audio segment in a single forward pass. A truly streaming end-to-end model (like Step-Audio R1's MPS) can further reduce **time-to-first-token** by "thinking while speaking," a benefit not captured by this demo's total segment latency.

## How to Adapt for Real Step-Audio R1

The backend for the end-to-end path is switchable:

- **Default**: `STEP_AUDIO_ENDPOINT` not configured → uses `gpt-audio` (model name can be overridden with `E2E_MODEL`).
- **Real Step-Audio R1**: After deploying on multi-GPU, write the service address into `STEP_AUDIO_ENDPOINT`, and the demo's end-to-end path will switch to it. `speech_model.py`'s `EndToEndSpeechModel._run_step_audio` provides the call skeleton for "upload audio, retrieve audio"; request bodies vary by deployment scheme (vLLM / custom HTTP service), so adapt as needed.

## Limitations

- `gpt-audio` is a **representative** of the end-to-end paradigm, not Step-Audio R1 itself: it does not expose MPS's streaming time-to-first-token, nor does it have the paralinguistic benchmark scores reported in the Step-Audio R1 paper. Table 9-1 is therefore a **citation**, not a reproduction.
- The demo constructs input using "text TTS → input speech" solely for a demonstration loop; in real scenarios, input comes from the user's microphone, carrying richer paralinguistic information, and the loss in the cascaded pipeline is more pronounced.
- The relative latency of end-to-end vs. cascaded will fluctuate with network conditions, model load, and answer length; a single run does not represent a stable conclusion. The paradigm difference (whether paralinguistic information is preserved) is a more robust dimension for comparison.

## Files

- `demo.py`: Runnable main program (`python demo.py`), runs both end-to-end + cascaded on the same problem and prints a real comparison.
- `speech_model.py`: `EndToEndSpeechModel` (gpt-audio / switchable to Step-Audio R1) and `CascadedSpeechModel` (whisper-1 → gpt-5.6-luna → tts-1).
- `requirements.txt` / `env.example`: Dependencies and environment variable template.
- `audio/`: Input/output audio generated at runtime (ignored in `.gitignore`).

---

## 中文

# 实验 9-4 配套：端到端语音思考 vs 级联流水线

对应《深入理解 AI Agent》第 9 章 **实验 9-4 ★★★：使用 Step-Audio R1 实现端到端语音思考**。

## 目的

书中实验 9-4 的核心是**端到端语音思考模型 Step-Audio R1**：单一模型直接「听 → 想 → 说」，把 ASR、LLM、TTS 三段合而为一，在隐空间中直接传递副语言信息（情绪、语气、语速、环境声），延迟更低、韵律更自然。

Step-Audio R1 无公开 endpoint、需多卡 GPU 部署，读者难以直接跑通。本 demo 因此用 OpenAI 的 speech-to-speech 模型 `gpt-audio` 作为**真实可跑的端到端代表**：它同样是「音频进 → 单模型 → 音频出」，一次调用就返回语音答案与其转写，中间**没有**独立的 ASR/LLM/TTS 三段。demo 让你**同题对照**端到端与级联两条真实管道，直观看到二者在**延迟**与**信息损失（语气、副语言）**上的差异——两条路的延迟都是本次运行真实测得，两段输出音频都用 `ffprobe` 校验。

demo 提供两类任务（`--task`），对应书中两条对照轴：

- **`math`（默认）**：口述数学题（Spoken-MQA 风格）。答案只取决于「说了什么」，级联与端到端准确率相当（对应书 9.3「自级联」一节），因此这一任务主要对照**延迟**维度。
- **`paralinguistic`**：一句「答案取决于怎么说」的话。级联在 ASR 处把语音压成纯文本，LLM 拿到的只有字面，任何情绪判断都是**文本代理思考**（Textual Surrogate Reasoning，书中 9.3「文本代理思考问题」）——凭词汇猜情绪；端到端则直接听声学特征（语速、音调），据此回应。这一任务对照**信息损失**维度，正是书中 **MGRD（模态锚定思考蒸馏）** 要解决的核心问题。

## 原理：三种语音范式

书中把语音架构分为三种范式（chapter9.md「语音架构的三种范式」）：

| 范式 | 结构 | 特点 |
|------|------|------|
| **级联（Cascaded）** | ASR → LLM → TTS 三个独立模型串联 | 模块清晰、可独立调优、可解释性好；但延迟串行累加，模型间以纯文本接口相连，情绪/语速/语调/环境声在交接时几乎全部丢失 |
| **端到端全模态（Omni / End-to-End）** | 单一模型「听→想→说」（Step-Audio R1、gpt-audio 等） | 延迟更低、保留副语言信息、韵律自然，可「边想边说」；代价是训练数据需求大、可解释性差。**仍假设「轮流说话」，靠 VAD 划分轮次** |
| **全双工（Full-Duplex）** | 单模型边听边说，取消「轮流」假设（Moshi、GPT-Live） | 持续同时处理输入与输出，每秒多次决策该说/该听/该停/该打断；本 demo 不涉及 |

本 demo 聚焦前两种范式的**对照**：端到端（范式二）vs 级联（范式一）。

**Step-Audio R1 是范式二里把「思考」也内化进单模型的代表**：通过 MGRD（模态锚定思考蒸馏）真正基于声学特征思考，通过 MPS 双脑架构实现「边想边说」。`gpt-audio` 是同一范式（音频进单模型出音频）里读者可直接调用的代表。

## 运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 Key
cp env.example .env
# 编辑 .env，填入有效的 OPENAI_API_KEY（需有权访问 gpt-audio / whisper-1 / tts-1）。
# 音频端点（端到端 gpt-audio、级联 ASR/TTS）只有 OpenAI 直连才有——OpenRouter 无音频端点，
# 故本实验必须用 OpenAI 直连 Key。可选：额外配 OPENROUTER_API_KEY，则级联中间的纯文本
# LLM 思考自动改走 OpenRouter 的 gpt-5.6-luna（绕开 gpt-5.6* 直连的组织实名认证）。

# 3. 运行（默认：math 任务，同题跑通端到端 + 级联，并打印真实延迟对照）
python demo.py

# 副语言任务：凸显端到端相对级联的优势（端到端听得到语气，级联只看到字面）
python demo.py --task paralinguistic

# 用真实带情绪的录音作输入（比 TTS 合成更能体现语气差异；与 --question 互斥）
python demo.py --task paralinguistic --audio-input my_voice.wav

# 只跑端到端 / 自定义提问 / 换音色 / 换输出目录
python demo.py --skip-cascade
python demo.py --question "从北京到上海高铁 4 小时，我 9 点出发，几点到？"
python demo.py --voice nova --output-dir out
python demo.py --help

# 切到自部署的真实 Step-Audio R1（覆盖环境变量）
python demo.py --step-audio-endpoint http://localhost:8000/v1/audio/chat

# 4.（可选）试听生成的语音答案
ffplay audio/answer_end_to_end.wav   # 端到端
ffplay audio/answer_cascade.mp3      # 级联
```

CLI 全部参数见 `python demo.py --help`：`--task`、`--question`、`--audio-input`、`--e2e-model`、`--step-audio-endpoint`、`--voice`、`--output-dir`、`--skip-cascade`。默认行为（`python demo.py` 跑 math 任务、端到端 + 级联对照）与改造前保持一致。

依赖 `ffprobe`/`ffplay`（用于校验、试听音频）：`brew install ffmpeg`（macOS）。

## 预期输出示例（真实节选）

```text
范式二：端到端语音思考（后端=gpt-audio，模型=gpt-audio）
形态：音频进 → 单模型「听→想→说」→ 音频出（一次调用，无独立 ASR/LLM/TTS 段）
[单阶段] 端到端（听→想→说，单模型一次调用）  |  延迟=7.21s
    语音答案转写（模型顺带产出，非中间文本阶段）：咱们先算一下：小明有12块钱，买了3支铅笔……最后不剩钱了。
    ffprobe 校验：{'格式': 'wav', '时长(秒)': 20.75, ...}
端到端总延迟（单模型一次前向）：7.21s

范式一（对照基线）：级联流水线 ASR → LLM → TTS
[阶段 1] ASR 语音识别  |  模型=whisper-1  |  延迟=1.35s
[阶段 2] LLM 思考      |  模型=gpt-5.6-luna  |  延迟=1.92s
[阶段 3] TTS 语音合成  |  模型=tts-1  |  延迟=3.66s
级联总延迟（各阶段串行相加）：6.94s

端到端 vs 级联：真实延迟对照
【1】实测总延迟  端到端 7.21s；级联 ASR(1.35)+LLM(1.92)+TTS(3.66)=6.94s
【3】书中表 9-1（引自 Step-Audio R1 论文，非本 demo 产出）
    MPS Speak-First 92.8% / 完整 TBS 93.0% ……
```

### 副语言任务的真实节选（`--task paralinguistic`，一次真实运行）

同一句「行吧，那就这样吧，我没什么意见。」（TTS 合成，情感偏平），两条路的回答：

```text
[阶段 1] ASR 语音识别  |  whisper-1  → 「行吧,那就这样吧,我没什么意见」   ← 级联 LLM 只拿得到这行纯文本

两条路对同一段音频的回答（可直观对比是否「听到了怎么说」）：
    级联（只凭 ASR 文本，文本代理思考）→ 「听起来你有些无奈，可能对这个决定不太满意。……」
    端到端（直接听声学特征）        → 「听起来你有点无奈，语速不快，音调挺平稳的。……」
```

差异一目了然：**级联**只能从字面「没什么意见」猜出无奈，说不出任何声学依据（书中「文本代理思考」）；**端到端**则直接引用了「语速不快、音调平稳」这类声学特征——这正是书中 MGRD 想让模型学会的「用耳朵思考」。注意默认输入是 TTS 合成、情感偏平，差异已被削弱；用 `--audio-input` 喂一段真实带情绪的录音，对照会更明显。

**关于表 9-1**：demo 里打印的 Spoken-MQA / URO-Bench 分数是**引自 Step-Audio R1 论文**（书中表 9-1 转引），并非本 demo 跑出来的——本 demo 真实产出的只有实测延迟与两段真实音频。延迟数字随网络与 OpenAI 负载波动；`gpt-audio` 是「一次前向出整段音频」，真流式的端到端（如 Step-Audio R1 的 MPS）还能「边想边说」把**首字延迟**进一步压低，这一点非本 demo 的整段延迟所能体现。

## 如何适配真实 Step-Audio R1

端到端一路的后端可切换：

- **默认**：不配置 `STEP_AUDIO_ENDPOINT` → 用 `gpt-audio`（模型名可用 `E2E_MODEL` 覆盖）。
- **真实 Step-Audio R1**：自行多卡 GPU 部署后，把服务地址写入 `STEP_AUDIO_ENDPOINT`，demo 的端到端一路即改走它。`speech_model.py` 的 `EndToEndSpeechModel._run_step_audio` 给出了「上传音频、取回音频」的调用骨架；不同部署方案（vLLM / 自定义 HTTP 服务）的请求体各异，接入时按需改写。

## 局限

- `gpt-audio` 是端到端范式的**代表**，不是 Step-Audio R1 本身：它没有暴露 MPS「边想边说」的流式首字延迟，也没有 Step-Audio R1 论文报告的副语言基准分数。表 9-1 因此是**引用**而非复现。
- demo 用「文本 TTS → 输入语音」构造输入，仅为演示闭环；真实场景中输入来自用户麦克风，副语言信息更丰富，级联的损失也更明显。
- 端到端与级联的延迟高低会随网络、模型负载、答案长度波动，单次运行不代表稳定结论；范式差异（副语言信息是否保留）才是更稳健的对照维度。

## 文件

- `demo.py`：可运行主程序（`python demo.py`），同题跑通端到端 + 级联并打印真实对照。
- `speech_model.py`：`EndToEndSpeechModel`（gpt-audio / 可切 Step-Audio R1）与 `CascadedSpeechModel`（whisper-1 → gpt-5.6-luna → tts-1）。
- `requirements.txt` / `env.example`：依赖与环境变量样例。
- `audio/`：运行时生成的输入/输出音频（已在 `.gitignore` 中忽略）。
