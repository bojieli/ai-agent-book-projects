## English

# Experiment 9-3: Streaming Speech Perception

Companion to Chapter 9 of "Understanding AI Agents" – Experiment 9-3: Using Qwen2-Audio to Simulate Streaming Speech Perception.

## Objective

Demonstrate the core trade-off of **streaming speech perception**: feed continuous audio to ASR in **incrementally growing chunks**, producing a "current partial recognition result" after each small segment. This achieves extremely low **first-packet latency** for obtaining text; the cost is that early chunks, **lacking the latter half of the sentence context** and with speech cut off mid-stream, may produce **incomplete or erroneous** recognition, which gradually **converges** to the correct text as more audio accumulates. As a baseline, "wait for the complete audio and then recognize once" is the most accurate, but requires waiting for the entire sentence plus inference, resulting in the **highest latency for the first character**.

The phenomenon from the original experiment in the book: in a sentence with a pause, "大概两点左右" (around two o'clock) was misrecognized as "大概零点左右" (around midnight) in an overly early chunk. This demo replicates this "cost of premature decision" with a similar phenomenon.
## Model Adaptation Notes (Important)

- The original experiment in the book used **Qwen2-Audio** (a native audio model capable of outputting acoustic event tokens like `<|noise|>`).
  However, it currently **has no directly callable key/endpoint**, so this demo uses an **available ASR alternative**:
  **OpenAI Whisper (`whisper-1`)**, reading the `OPENAI_API_KEY`.
- Choosing Whisper is appropriate: like Qwen2-Audio, it is a **non-streaming model that takes the entire segment as input** – the encoder needs the full audio segment to start working and is **non-incremental** (each longer prefix requires re-encoding from scratch).
  Therefore, "slicing by increasing prefixes and recognizing each slice" perfectly reproduces the mechanism and cost of "simulated streaming" described in the book.
- The test audio is synthesized on the fly using **OpenAI TTS (`tts-1`)**. The sentence contains time information "两点半" (two thirty). When the first half is truncated, it is prone to incomplete/erroneous recognition.
- **Must use a direct OpenAI Key**: This experiment only uses audio endpoints (ASR `whisper-1` / TTS `tts-1`). These endpoints are only available via direct OpenAI connection – OpenRouter only handles chat completions and has no audio endpoints, so it cannot fall back to `OPENROUTER_API_KEY`. If you only want to verify the chunking/timing logic, use `python demo.py --offline`, which requires no Key.

Compared to true streaming models (e.g., Qwen3-Omni using chunked/causal encoders), the latency numbers in this demo only reflect the overhead of "chunk granularity + re-encoding each chunk from scratch" and do not equal the first-packet latency of true streaming; this is also explained in the book.

## Streaming Chunking Mechanism

1. Synthesize the entire Chinese test audio using TTS (approx. 7–8 seconds), saved as `audio/sentence.wav`.
2. Use `ffmpeg` to slice out "all audio received so far" at increasing lengths: `t = 0.5s, 1.0s, 1.5s ...`,
   simulating the continuous arrival of an audio stream.
3. For each prefix chunk, call Whisper to obtain the "current partial recognition result", recording the **single-chunk recognition latency** and **cumulative arrival latency**.
4. Baseline: At the end, recognize the **entire** audio segment once, recording its result and latency.
5. Print a per-chunk recognition table + full-segment baseline, quantifying the latency/accuracy trade-off between "first available recognition" and "full-segment recognition".

## Running

```bash
cd chapter9/streaming-speech
pip install -r requirements.txt          # Also requires ffmpeg on the machine: brew install ffmpeg
cp env.example .env                       # Fill in OPENAI_API_KEY (or directly export)
python demo.py                             # Default: TTS synthesis + 0.5s granularity simulated-streaming (growing-prefix) recognition via real Whisper calls
python demo.py --quick                     # Increase chunk granularity to 1.5s, reducing Whisper calls to ~1/3
python demo.py --sentence "..." --chunk-step 0.5   # Custom test sentence and chunk granularity
python demo.py --audio my.wav              # Use an existing audio file as input, skip TTS synthesis
python demo.py --compare-chunks            # Cross-granularity (0.5/1.0/2.0s) latency comparison table
python demo.py --offline                   # Offline self-test: no network, no ffmpeg, no Key, uses a synthetic recognizer
python demo.py --offline --compare-chunks  # Offline synthetic cross-granularity latency comparison table
python demo.py --output result.json        # Save results (per-chunk table/comparison table) as JSON
python demo.py --help                      # View all parameters
```

Common parameters (`python demo.py --help`):

- `--sentence`: Test sentence (default is a sentence with time information similar to the one in the book).
- `--chunk-step`: Chunk granularity (seconds), default 0.5. Smaller values mean more chunks and slower processing.
- `--quick`: Increase granularity to 1.5s for a quick demo (Whisper calls reduced to ~1/3).
- `--audio PATH`: Use an existing audio file as input, skip TTS synthesis (ignored in offline mode).
- `--compare-chunks [S1,S2,...]`: Run once for each specified chunk granularity, output a cross-granularity latency comparison table; if no value is given, defaults to `0.5,1.0,2.0` (seconds).
- `--offline`: **Offline self-test**, no network, no ffmpeg, no Key needed. Uses a **synthetic recognizer** (SYNTHETIC) to drive the same chunking/timing logic – text is revealed proportionally to the prefix, latency values are synthetic, **only validates the process, does not represent any real model performance**.
- `--duration SEC`: Total duration of the segment in offline mode (default is estimated based on sentence length).
- `--tts-model` / `--voice` / `--asr-model` / `--language`: Override TTS/ASR models and language (defaults are `tts-1` / `alloy` / `whisper-1` / `zh`).
- `--output PATH`: Save results as JSON.

## Real Run Output (Excerpt, for Reference)

A real run (sentence: "Please help me reschedule tomorrow afternoon's meeting to 2:30, the location is still Conference Room 3, and don't forget to notify everyone.", total duration 7.75s) per-chunk recognition:
```text
Chunk#01  Audio Prefix  0.5s | Recognition: Could you please                         ← Premature truncation: misrecognition + incomplete
Chunk#03  Audio Prefix  1.5s | Recognition: Could you please reschedule tomorrow afternoon's
Chunk#05  Audio Prefix  2.5s | Recognition: ...to two o'clock                       ← Time only half heard
Chunk#06  Audio Prefix  3.0s | Recognition: ...to two thirty                     ← Converges after context is supplemented
Chunk#10  Audio Prefix  5.0s | Recognition: ...the location is still in Sichuan                 ← Truncation misrecognition (should be "Conference Room 3")
Chunk#12  Audio Prefix  6.0s | Recognition: ...the location is still in Conference Room 3           ← Converges with more audio
Chunk#14  Audio Prefix  7.0s | Recognition: ...don't forget to notify me                   ← Another premature misjudgment (should be "notify everyone")
Chunk#16  Audio Prefix  7.8s | Recognition: ...don't forget to notify everyone (Complete and correct)
Full Segment Recognition (wait for complete audio): Could you please reschedule tomorrow afternoon's meeting to 2:30 PM? The location is still Conference Room 3. Don't forget to notify everyone.  Wait time: 7.75s (recording) + 2.25s (inference)
First available streaming recognition: Only ~0.5s of audio needed to produce a partial result, obtaining the first version 7.25s earlier than the full segment.
```

It can be seen: streaming chunking advances the latency of the "first partial result" from "after recording the full sentence (7.75s)" to "after receiving 0.5s of audio", but the cost is **premature decision misrecognitions** in early chunks like "你帮我→你们" (you help me → you all), "三号会议室→四川" (Conference Room 3 → Sichuan), "通知大家→通知我" (notify everyone → notify me), which gradually converge as audio accumulates. Full segment recognition is the most accurate but has the highest latency. This is the **latency vs. accuracy trade-off** of streaming speech perception.
> Note: Each run makes real calls to TTS + Whisper, so the specific recognized text and latency numbers will fluctuate slightly;
> the table above is the result of one particular real run. The positions of misrecognitions in early chunks may vary between runs, but the pattern of "early inaccuracy, convergence with more audio" is stably reproduced.

## File Description

- `demo.py`: Main program (synthesize audio → incremental chunk streaming recognition → full segment baseline).
- `requirements.txt`: Python dependencies (also requires ffmpeg/ffprobe on the machine).
- `env.example`: Environment variable example, copy to `.env` and fill in `OPENAI_API_KEY`.
- `audio/`: Audio generated at runtime (gitignored).

---

## 中文

# 实验 9-3：模拟流式语音感知（Streaming Speech Perception）

配套《深入理解 AI Agent》第 9 章「实验 9-3：使用 Qwen2-Audio 模拟流式语音感知」。

## 目的

演示**流式语音感知**的核心权衡：把连续音频**按递增长度分块**喂给 ASR，每收到一小段
就产出「当前部分识别结果」，从而以极低的**首包延迟**尽早拿到文本；代价是——早期分块
因为**缺少后半句上下文**、语音被拦腰截断，识别可能**不完整或出错**，随着音频累积才逐步
**收敛**到正确文本。作为对照，「等完整音频到齐再识别一次」最准，但必须等整句说完 + 推理，
**首字延迟最高**。

书中原实验的现象是：带停顿的句子里「大概两点左右」在过早分块中被误识别为「大概零点
左右」。本 demo 用同类现象复现这一「过早决策的代价」。

## 模型适配说明（重要）

- 书中原实验用 **Qwen2-Audio**（音频原生模型，可输出 `<|noise|>` 等声学事件 token）。
  但其当前**没有可直接调用的 key/endpoint**，故本 demo 改用**可用的 ASR 替代**：
  **OpenAI Whisper（`whisper-1`）**，读取 `OPENAI_API_KEY`。
- 选择 Whisper 恰好合适：它和 Qwen2-Audio 一样是**整段输入的非流式模型**——编码器需要
  一整段音频才能开始工作、且**非增量**（每处理一个更长的前缀都要从头重新编码识别）。
  因此「按递增前缀切块、逐块识别」正好复现书中所述「模拟流式」的机制与代价。
- 测试音频用 **OpenAI TTS（`tts-1`）** 现场合成，句子含时间信息「两点半」，前半句被截断
  时容易识别不全 / 出错。
- **必须用 OpenAI 直连 Key**：本实验只用音频端点（ASR `whisper-1` / TTS `tts-1`），
  这类端点只有 OpenAI 直连才有——OpenRouter 只做聊天补全、无音频端点，故无法回退到
  `OPENROUTER_API_KEY`。若只想验证分块/计时逻辑，用 `python demo.py --offline` 即可，无需任何 Key。

与真正的流式模型（如采用分块/因果编码器的 Qwen3-Omni）相比，本 demo 的延迟数字只反映
「分块粒度 + 每块从头识别」的开销，并不等于真流式的首包延迟；这一点书中也已说明。

## 流式分块机制

1. 用 TTS 合成整段中文测试音频（约 7~8 秒），保存为 `audio/sentence.wav`。
2. 用 `ffmpeg` 按递增长度切出「到目前为止收到的全部音频」：`t = 0.5s, 1.0s, 1.5s ...`，
   模拟音频流不断到达。
3. 每个前缀块调用 Whisper 得到「当前部分识别结果」，记录**单块识别延迟**与**累计到达延迟**。
4. 对照：仅在结尾对**整段**音频识别一次，记录其结果与延迟。
5. 打印逐块识别表 + 整段对照，量化「首个可用识别」与「整段识别」的延迟/准确率权衡。

## 运行

```bash
cd chapter9/streaming-speech
pip install -r requirements.txt          # 另需本机 ffmpeg：brew install ffmpeg
cp env.example .env                       # 填入 OPENAI_API_KEY（或直接 export）
python demo.py                             # 默认：TTS 合成 + 0.5s 粒度、真实调用 Whisper 的模拟流式（递增前缀）识别
python demo.py --quick                     # 分块粒度放大到 1.5s，Whisper 调用减到约 1/3
python demo.py --sentence "..." --chunk-step 0.5   # 自定义测试句与分块粒度
python demo.py --audio my.wav              # 用现成音频作输入，跳过 TTS 合成
python demo.py --compare-chunks            # 跨 0.5/1.0/2.0s 的分块粒度延迟对照表
python demo.py --offline                   # 离线自检：不联网、不需 ffmpeg，用合成识别器
python demo.py --offline --compare-chunks  # 离线合成的跨粒度延迟对照表
python demo.py --output result.json        # 结果（逐块表/对照表）另存为 JSON
python demo.py --help                      # 查看全部参数
```

常用参数（`python demo.py --help`）：

- `--sentence`：测试句（默认为书中同类的带时间信息的句子）。
- `--chunk-step`：分块粒度（秒），默认 0.5，越小分块越多越慢。
- `--quick`：把粒度放大到 1.5s 快速演示（Whisper 调用约 1/3）。
- `--audio PATH`：用现成音频文件作输入，跳过 TTS 合成（离线模式忽略）。
- `--compare-chunks [S1,S2,...]`：在多个分块粒度上各跑一遍，输出跨粒度延迟对照表；不带值时用默认 `0.5,1.0,2.0`（秒）。
- `--offline`：**离线自检**，不联网、不需 ffmpeg、不需 Key，用**合成识别器**（SYNTHETIC）驱动同一套分块/计时逻辑——文本按前缀比例揭示、延迟为合成值，**仅验证流程、不代表任何真实模型性能**。
- `--duration SEC`：离线模式下的整段时长（缺省按句子长度估算）。
- `--tts-model` / `--voice` / `--asr-model` / `--language`：覆盖 TTS/ASR 模型与语言（默认 `tts-1` / `alloy` / `whisper-1` / `zh`）。
- `--output PATH`：把结果另存为 JSON。

## 真实运行输出（节选，供参考）

一次真实运行（句子：「麻烦你帮我把明天下午的会议改到两点半，地点还是在三号会议室，
别忘了通知大家。」，整段 7.75s）的逐块识别：

```text
块#01  音频前缀  0.5s | 识别：麻烦你们                         ← 过早截断：误识别 + 不完整
块#03  音频前缀  1.5s | 识别：麻烦你帮我把明天下午的
块#05  音频前缀  2.5s | 识别：...改到两点                       ← 时间只听到一半
块#06  音频前缀  3.0s | 识别：...改到两点半                     ← 补足上下文后收敛
块#10  音频前缀  5.0s | 识别：...地点还是在四川                 ← 截断误识别（应为「三号会议室」）
块#12  音频前缀  6.0s | 识别：...地点还是在三号会议室           ← 随音频增长收敛
块#14  音频前缀  7.0s | 识别：...别忘了通知我                   ← 又一处过早误判（应为「通知大家」）
块#16  音频前缀  7.8s | 识别：...别忘了通知大家（完整正确）

整段识别（等完整音频）：麻烦你帮我把明天下午的会议改到两点半 地点还是在三号会议室 别忘了通知大家
  需等待：7.75s（录完）+ 2.25s（推理）
流式首个可用识别：仅需约 0.5s 音频即产出部分结果，比整段提前 7.25s 拿到第一版
```

可见：流式分块把「首个部分结果」的延迟从「录完整句（7.75s）之后」提前到「收到 0.5s 音频」，
但代价是早期块出现「你帮我→你们」「三号会议室→四川」「通知大家→通知我」等**过早决策误识别**，
随音频累积逐步收敛。整段识别最准，延迟最高。这正是流式语音感知的**延迟 vs 准确率权衡**。

> 注：每次运行会真实调用 TTS + Whisper，具体识别文本与延迟数字会略有波动；
> 上表为某一次真实运行的结果，不同运行早期块的误识别位置可能不同，但「早期不准、
> 随音频收敛」的规律稳定复现。

## 文件说明

- `demo.py`：主程序（合成音频 → 递增分块流式识别 → 整段对照）。
- `requirements.txt`：Python 依赖（另需本机 ffmpeg / ffprobe）。
- `env.example`：环境变量示例，复制为 `.env` 填入 `OPENAI_API_KEY`。
- `audio/`：运行时生成的音频（已 gitignore）。
