## English

# Experiment 9-5: Control-Marker-Driven Controllable TTS

A runnable companion project for Experiment 9-5 of "Deep Understanding of AI Agents".

Core idea: The main LLM's output is not just text, but also includes **control markers** (emotion/speech rate/style/pause/laughter, etc.); the execution layer parses these markers, maps them to corresponding timbre/style profiles in a **reference voice library**, and then synthesizes speech. This way, decisions about "where to pause and what tone to use" are delegated to the LLM. The same text, with different control markers, can synthesize speech with different styles, emotions, and rhythms.

## Provider Adaptation (Important)

Experiment 9-5 in the book uses **Fish Audio S1** for voice cloning: uses 3-10 seconds of reference audio for zero-shot cloning of the same timbre, builds a reference voice library covering emotion × speech rate × style, selects reference voices via control markers, and Fish Audio ensures **consistent timbre** across different reference voices with only changes in prosody and emotion.

This environment lacks a usable Fish Audio key, so **OpenAI TTS** is used instead to demonstrate the **exact same concept**:

| Book (Fish Audio) | This Project (OpenAI TTS) |
| --- | --- |
| Voice cloning ensures consistent timbre | Entire library uses a fixed `voice` (alloy), timbre unchanged |
| Prosody/emotion of each reference voice | Each profile corresponds to a set of `instructions` style prompts |
| Control markers select reference voice | Control markers parsed -> select `(emotion, speed, style)` profile |

- Preferred model **`gpt-4o-mini-tts`**: Supports the `instructions` parameter, allowing precise control of emotion/speech rate/tone with a Chinese prompt, closest to the semantics of "control marker → stylized speech".
- If the preferred model is unavailable, the code **automatically falls back to `tts-1`**: Does not support instructions; keeps the same fixed `voice` (alloy) and approximates style with the `speed` parameter + text/silence pauses.

**Must use a direct OpenAI Key**: This experiment only uses the TTS speech synthesis endpoint (`gpt-4o-mini-tts` / `tts-1`). These audio endpoints are only available through direct OpenAI connection—OpenRouter only handles chat completions and has no audio synthesis endpoint, so it cannot fall back to `OPENROUTER_API_KEY`. Offline viewing of the voice library/marker mapping (`--list-voices` / `--dump-mapping`) does not require any key.

> Limitation: OpenAI TTS cannot **natively generate** non-verbal sounds like laughter or sighs like Fish Audio can. This project approximates `<laugh>` / `[SIGH]` with emotion-matching onomatopoeia (e.g., "Haha," "Ahh—"), while `[PAUSE]`/`[THINKING]` and other pauses use ffmpeg to generate **real silence** that can be verified for duration by ffprobe.

## Control Marker → TTS Parameter Mapping

### State Markers (persist until changed by a similar marker)

| Marker | Chinese Form | Effect |
| --- | --- | --- |
| `[EMO:neutral\|happy\|frustrated\|thinking]` | `[情感=中性\|高兴\|沮丧\|思考]` | Switch emotion |
| `[SPEED:normal\|fast\|slow]` / `[SPEED:0.8x]` | `[语速=正常\|快\|慢]` | Switch speech rate |
| `[STYLE:formal\|casual]` | `[风格=正式\|轻松]` | Switch tone |

The three dimensions combine to form a profile in the reference voice library (e.g., `happy_fast_formal`), which is then assembled into an `instructions` prompt for `gpt-4o-mini-tts`.

### Inline Markers (one-time events)

| Marker | Effect |
| --- | --- |
| `[THINKING]` | Switch to "thinking/slow/formal" reference voice + insert 0.5s pause |
| `[SEARCHING]` | Same as above, 0.4s pause (searching hesitation) |
| `[PAUSE]` / `<pause>` / `[停顿]` | Insert 0.5s silence |
| `[BREATH]` / `<breath>` | Insert 0.4s breathing pause |
| `[SIGH]` / `<sigh>` | Sigh onomatopoeia "Ahh—" + 0.3s pause |
| `[LAUGH:small]` / `<laugh>` | Light laugh onomatopoeia "Haha," (cheerful tone) |
| `<emphasis>…</emphasis>` / `[强调]…[/强调]` | Append "emphasize" prompt for the wrapped text |

### Reference Voice Library

`voice_library.py` generates **24 profiles** from the Cartesian product of emotion(4) × speech rate(3) × style(2), all with a fixed `voice=alloy` (consistent timbre), differing only in `instructions`. Can be viewed by running it standalone:

```bash
python voice_library.py
```

## Installation and Execution

```bash
pip install -r requirements.txt          # Requires ffmpeg/ffprobe installed on the system
cp env.example .env                       # Fill in a valid OPENAI_API_KEY
python demo.py                            # Generates output/*.mp3
```

`demo.py` does two things:

1. **Comparison of three configurations** (as required by the book), using the same text with markers:
   - `A_no_markers.mp3` No control markers (fluent but mechanical)
   - `B_single_voice.mp3` Single reference voice (natural but emotionally monotone)
   - `C_voice_library.mp3` Multiple reference voice library (switches emotion/speech rate/pause based on markers)
2. **Same text / different control markers** → multiple different style audio files: `variant_*.mp3`.

During execution, it prints the "control marker → parameter" parsing process for each audio file, along with ffprobe duration information.

Common parameters (`python demo.py --help`):

| Parameter | Effect |
| --- | --- |
| `--quick` | Only run the three-configuration comparison (A/B/C), skip the 5 style variants, reducing TTS calls and time |
| `--text text` | Only synthesize this custom text (can embed control markers, e.g., `[EMO:happy][THINKING]…`) |
| `--emotion / --speed / --style` | Specify emotion/speech rate/tone for `--text` (equivalent to adding corresponding state markers before the text) |
| `-o / --output path` | Output mp3 path for `--text` mode (default `output/custom.mp3`) |
| `--list-voices` | **Offline** (no API key needed): Print the complete reference voice library (24 profiles and their instructions) |
| `--dump-mapping` | **Offline** (no API key needed): Print the control marker → action mapping table, and demonstrate the parsing process on example text |

## Example Expected Output (Real Excerpt)

```text
Preferred model: gpt-4o-mini-tts (automatically falls back to tts-1 if unavailable)

Comparison experiment: Same text with control markers, three configurations
[EMO:happy][SPEED:fast]Great! Your order has been confirmed.[THINKING]Hmm, let me check the delivery time...[EMO:neutral][SPEED:normal]It is expected to arrive tomorrow afternoon.
[C] Multiple reference voice library (parse control markers -> switch reference voice per segment + pauses)
    -- Control marker parsing process --
  [EMO:happy]            -> emotion = happy
  [SPEED:fast]           -> speech rate = fast
  [THINKING]             -> Switch to thinking/slow/formal reference voice
  [THINKING] pause          -> Insert silence 500ms
    -- Synthesis segments --
    · [happy_fast_formal         ] gpt-4o-mini-tts  voice=alloy text='Great! Your order has been confirmed.'    · [Silence 500ms]
    · [thinking_slow_formal      ] gpt-4o-mini-tts  voice=alloy text='Hmm, let me check the delivery time...'
    · [neutral_normal_formal     ] gpt-4o-mini-tts  voice=alloy text='It is expected to arrive tomorrow afternoon.'  => output/C_voice_library.mp3  |  format_name=mp3  duration=11.324000  ...
```

Comparing the ffprobe durations of the three configurations reveals the difference: C (multiple reference voice library) is longer (approximately 11.3s) than A/B (approximately 8.5s) due to the inserted real silence pauses, and each segment uses a different `(emotion, speech rate, style)` profile. (Each run will actually call OpenAI TTS, so duration/byte count will have slight fluctuations.)

## File Descriptions

| File | Description |
| --- | --- |
| `voice_library.py` | Reference voice library + control dimension → instructions mapping |
| `markup.py` | Control marker parser: text with markers → list of segments (speech/silence) |
| `tts.py` | OpenAI TTS synthesis + ffmpeg silence generation/concatenation |
| `demo.py` | Demo entry point, three-configuration comparison + style variants |

---

## 中文

# 实验 9-5：控制标记驱动的可控 TTS

《深入理解 AI Agent》实验 9-5 的可运行配套项目。

核心思路：让主 LLM 的输出不只是文本，还带上**控制标记**（情感 / 语速 / 风格 /
停顿 / 笑声等）；执行层解析这些标记，映射到一个**参考语音库**里对应的音色/风格档案，
再合成语音。这样「在哪里该停顿、该用什么语气」的决策交给了 LLM，同一段文本在不同
控制标记下能合成出不同风格、情感、节奏的语音。

## Provider 适配（重要）

书中实验 9-5 使用 **Fish Audio S1** 的声音克隆：用 3-10 秒参考语音零样本克隆同一
音色，构建覆盖情绪 × 语速 × 风格的参考语音库，靠控制标记选择参考语音，Fish Audio
保证不同参考语音之间**音色一致**、只有韵律和情感变化。

本环境无 Fish Audio 可用 key，因此改用 **OpenAI TTS** 演示**完全相同的思路**：

| 书中（Fish Audio） | 本项目（OpenAI TTS） |
| --- | --- |
| 声音克隆保证音色一致 | 全库固定同一个 `voice`（alloy），音色不变 |
| 每条参考语音的韵律/情感 | 每个档案对应一段 `instructions` 风格提示词 |
| 控制标记选参考语音 | 控制标记解析后 -> 选 `(情绪,语速,风格)` 档案 |

- 首选模型 **`gpt-4o-mini-tts`**：支持 `instructions` 参数，可用一段中文提示词精确
  控制情感/语速/口吻，最贴近「控制标记 → 风格化语音」的语义。
- 若首选模型不可用，代码**自动兜底到 `tts-1`**：不支持 instructions，仍用固定 `voice`（alloy），
  改用 `speed` 参数 + 文本/静音停顿近似。

**必须用 OpenAI 直连 Key**：本实验只用 TTS 语音合成端点（`gpt-4o-mini-tts` / `tts-1`），
这类音频端点只有 OpenAI 直连才有——OpenRouter 只做聊天补全、无音频合成端点，故无法回退到
`OPENROUTER_API_KEY`。离线查看语音库/标记映射（`--list-voices` / `--dump-mapping`）则无需任何 Key。

> 局限：OpenAI TTS 无法像 Fish Audio 那样**原生生成**笑声/叹气等非语言音。本项目对
> `<laugh>` / `[SIGH]` 用「匹配情绪的拟声词」（如“哈哈，”“唉——”）近似，`[PAUSE]`/
> `[THINKING]` 等停顿则用 ffmpeg 生成**真实静音**插入，可被 ffprobe 验证时长。

## 控制标记 → TTS 参数 映射

### 状态标记（持续生效，直到被同类标记改变）

| 标记 | 中文写法 | 作用 |
| --- | --- | --- |
| `[EMO:neutral\|happy\|frustrated\|thinking]` | `[情感=中性\|高兴\|沮丧\|思考]` | 切换情绪 |
| `[SPEED:normal\|fast\|slow]` / `[SPEED:0.8x]` | `[语速=正常\|快\|慢]` | 切换语速 |
| `[STYLE:formal\|casual]` | `[风格=正式\|轻松]` | 切换口吻 |

三个维度组合成参考语音库的一个档案（如 `happy_fast_formal`），
再拼成一段 `instructions` 提示词交给 `gpt-4o-mini-tts`。

### 内联标记（一次性事件）

| 标记 | 作用 |
| --- | --- |
| `[THINKING]` | 切到「思考/慢速/正式」参考语音 + 插入 0.5s 停顿 |
| `[SEARCHING]` | 同上，停顿 0.4s（搜索性犹豫） |
| `[PAUSE]` / `<pause>` / `[停顿]` | 插入 0.5s 静音 |
| `[BREATH]` / `<breath>` | 插入 0.4s 换气停顿 |
| `[SIGH]` / `<sigh>` | 叹气拟声词「唉——」+ 0.3s 停顿 |
| `[LAUGH:small]` / `<laugh>` | 轻笑拟声词「哈哈，」（欢快音色） |
| `<emphasis>…</emphasis>` / `[强调]…[/强调]` | 对包裹文本追加「加重强调」提示词 |

### 参考语音库

`voice_library.py` 由 情绪(4) × 语速(3) × 风格(2) 笛卡尔积生成 **24 条**档案，全部固定
`voice=alloy`（音色一致），仅 `instructions` 不同。可单独运行查看：

```bash
python voice_library.py
```

## 安装与运行

```bash
pip install -r requirements.txt          # 需系统已装 ffmpeg/ffprobe
cp env.example .env                       # 填入有效的 OPENAI_API_KEY
python demo.py                            # 生成 output/*.mp3
```

`demo.py` 做两件事：

1. **三种配置对比**（书中要求），同一段带标记文本：
   - `A_no_markers.mp3` 无控制标记（流畅但机械）
   - `B_single_voice.mp3` 单一参考语音（自然但情感单调）
   - `C_voice_library.mp3` 多参考语音库（按标记切换情感/语速/停顿）
2. **同文本 / 不同控制标记** → 多个不同风格音频：`variant_*.mp3`。

运行时会打印每个音频的「控制标记 → 参数」解析过程，以及 ffprobe 时长信息。

常用参数（`python demo.py --help`）：

| 参数 | 作用 |
| --- | --- |
| `--quick` | 只跑三种配置对比（A/B/C），跳过 5 个风格变体，减少 TTS 调用与耗时 |
| `--text 文本` | 只合成这一段自定义文本（可内嵌控制标记，如 `[情感=高兴][THINKING]…`） |
| `--emotion / --speed / --style` | 为 `--text` 指定情绪/语速/口吻（等价于在文本前加对应状态标记） |
| `-o / --output 路径` | `--text` 模式的输出 mp3 路径（默认 `output/custom.mp3`） |
| `--list-voices` | **离线**（无需 API key）：打印完整参考语音库（24 条档案及其 instructions） |
| `--dump-mapping` | **离线**（无需 API key）：打印控制标记 → 动作映射表，并演示对示例文本的解析过程 |

## 预期输出示例（真实节选）

```text
首选模型: gpt-4o-mini-tts（不可用时自动兜底 tts-1）

对比实验：同一段带控制标记的文本，三种配置
原始文本: [EMO:happy][SPEED:fast]太好了！您的订单已确认。[THINKING]嗯，让我查一下发货时间...[EMO:neutral][SPEED:normal]预计明天下午送达。

[C] 多参考语音库（解析控制标记 -> 逐段切换参考语音 + 停顿）
    -- 控制标记解析过程 --
  [EMO:happy]            -> 情绪 = happy
  [SPEED:fast]           -> 语速 = fast
  [THINKING]             -> 切换到 思考/慢速/正式 参考语音
  [THINKING] 停顿          -> 插入静音 500ms
    -- 合成片段 --
    · [happy_fast_formal         ] gpt-4o-mini-tts  voice=alloy text='太好了！您的订单已确认。'
    · [静音 500ms]
    · [thinking_slow_formal      ] gpt-4o-mini-tts  voice=alloy text='嗯，让我查一下发货时间...'
    · [neutral_normal_formal     ] gpt-4o-mini-tts  voice=alloy text='预计明天下午送达。'
  => output/C_voice_library.mp3  |  format_name=mp3  duration=11.324000  ...
```

对照三种配置的 ffprobe 时长即可看出差异：C（多参考语音库）因插入真实静音停顿，
比 A/B（8.5s 左右）更长（约 11.3s），且各片段用了不同的 `(情绪,语速,风格)` 档案。
（每次运行会真实调用 OpenAI TTS，时长/字节数会有小幅波动。）

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `voice_library.py` | 参考语音库 + 控制维度 → instructions 映射 |
| `markup.py` | 控制标记解析器：带标记文本 → 片段列表(语音/静音) |
| `tts.py` | OpenAI TTS 合成 + ffmpeg 生成静音/拼接 |
| `demo.py` | 演示入口，三种配置对比 + 风格变体 |
