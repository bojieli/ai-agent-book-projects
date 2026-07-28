# Multimodal Agent — Three Extraction Paradigms / 多模态 Agent——三种抽取范式对比

> Companion material for *AI Agents in Depth*, Chapter 3 — **Experiment 3-7**: native multimodal vs extract-to-text vs tool-based analysis.  
> 配套《深入理解 AI Agent》第 3 章 **实验 3-7**：原生多模态 vs 先抽文本 vs 工具化分析。

← [Chapter 3 index / 返回第 3 章目录](../README.md)

---

## English

### Features — three extraction modes

1. **Native Multimodality**: model built-in multimodal  
   - Gemini 2.5 Pro: PDF, image, audio  
   - GPT-5/GPT-4o: images (OpenAI multimodal format)  
   - Doubao 1.6: images  

2. **Extract to Text**: convert first, then reason  
   - PDF OCR (Gemini or GPT-5)  
   - Image captions (GPT-5 or Doubao 1.6)  
   - Audio: Whisper or Gemini  

3. **Multimodal analysis tools**: add-on for follow-ups  
   - Image / audio / PDF analysis tools  

### Architecture

```
MultimodalAgent
├── Configuration (config.py)
├── Agent Core (agent.py) — messages, history, modes, streaming
└── Multimodal Tools — image, audio, PDF analysis
```

### Installation

```bash
cd chapter3/multimodal-agent
pip install -r requirements.txt
cp env.example .env
# Edit .env with API keys
export $(cat .env | xargs)   # optional on Unix
```

### Quick offline start (no API key)

Generate a chart-bearing sample so Experiment 3-7 is measurable—**exact quarterly figures live only in the chart bars**, not surrounding text:

```bash
python create_sample.py           # or: python demo.py --generate-sample
# → test_files/sample_chart.png, test_files/sample_report.pdf
```

Then compare three paradigms (needs vision API key):

```bash
python demo.py \
  --file test_files/sample_chart.png \
  --query "Which quarter had the highest revenue, and what was the exact value?" \
  --model gpt-5.6-luna
```

Chinese `--help` on `demo.py` / `main.py` / `create_sample.py`.

### Usage

#### Interactive

```bash
python main.py --interactive
```

Commands: `/file <path>`, `/mode <native|extract_to_text>`, `/model <name>`, `/tools <on|off>`, `/history`, `/clear`, `/quit`.

#### Single file

```bash
python main.py --file document.pdf --query "What is the main topic?"
python main.py --mode extract_to_text --file image.jpg --query "Describe this image"
python main.py --tools --mode extract_to_text --file audio.mp3 --query "What's the content?"
```

#### Programmatic

```python
import asyncio
from agent import MultimodalAgent, MultimodalContent
from config import ExtractionMode

async def example():
    agent = MultimodalAgent(
        model="gemini-3.5-flash",
        mode=ExtractionMode.NATIVE,
        enable_tools=True
    )
    content = MultimodalContent(type="pdf", path="document.pdf")
    result = await agent.process_multimodal_content(content, "Summarize this document")
    print(result)
    async for chunk in agent.chat("Tell me more about the key points", stream=True):
        print(chunk, end="", flush=True)

asyncio.run(example())
```

### Demo comparison

```bash
python demo.py --file document.pdf --query "What are the key findings?" --model gpt-5.6-luna
python demo.py document.pdf "What are the key findings?"   # positional still works
python demo.py --file test_files/sample_chart.png \
  --query "Which quarter had the highest revenue?" \
  --model gpt-5.6-luna --skip-model-comparison --output result.txt
```

Runs: (1) native (2) extract-to-text (3) extract + tools (4) cross-model unless skipped.

| Flag | Description |
|------|-------------|
| `--file` / positional | Image / PDF / audio |
| `--query` / positional | Question |
| `--model` | Default `gemini-3.5-flash` |
| `--skip-model-comparison` | Only three-paradigm compare |
| `--generate-sample` | Offline sample then exit |
| `--output`, `-o` | Transcript file |

### Mode comparison

| Mode | Advantages | Disadvantages | Best for |
|------|------------|---------------|----------|
| **Native** | Full context; better vision | Limited models; more tokens | Mixed complex docs |
| **Extract to Text** | Any text model; cacheable | Loses visual context | Text-heavy / cost |
| **With Tools** | Follow-ups; selective depth | More API calls | Interactive Q&A |

### Supported files / models

- PDF (best native Gemini), images (JPEG/PNG/GIF/BMP/WebP), audio (MP3/WAV/M4A/FLAC/AAC/OGG)  
- Size limits: PDF/images 20MB, audio 25MB  

| Model | Native PDF | Native Image | Native Audio | Extract | Tools |
|-------|------------|--------------|--------------|---------|-------|
| Gemini 2.5 Pro | ✅ | ✅ | ✅ | ✅ | ✅ |
| GPT-5/GPT-4o | ❌ | ✅ | ❌ | ✅ | ✅ |
| Doubao 1.6 | ❌ | ✅ | ❌ | ✅ | ✅ |

### API keys

- `GOOGLE_API_KEY` or `GEMINI_API_KEY` — PDF/audio native  
- `OPENAI_API_KEY` — GPT + Whisper  
- `DOUBAO_API_KEY` or `ARK_API_KEY`  

### Testing / best practices

```bash
python test_multimodal.py
```

Prefer native when vision/audio fidelity matters; extract-to-text for cost/cache; tools for multi-turn. Validate files and keys; handle rate limits.

### License

MIT License — educational project.

---

## 中文

### 功能——三种抽取模式

1. **原生多模态**：直接用模型内置能力（Gemini PDF/图/音频；GPT/豆包图像等）  
2. **先抽文本再推理**：PDF OCR、图像描述、Whisper/Gemini 转写  
3. **多模态分析工具**：跟进问题的图像 / 音频 / PDF 工具  

### 架构

```
MultimodalAgent
├── Configuration (config.py)
├── Agent Core (agent.py)
└── Multimodal Tools
```

### 安装

```bash
cd chapter3/multimodal-agent
pip install -r requirements.txt
cp env.example .env
# 编辑 API Key
export $(cat .env | xargs)   # Unix 可选
```

### 离线快速开始（无需 API Key）

生成带图表的样例报告——**精确季度数字只在柱状图里**，方便测三种范式取舍：

```bash
python create_sample.py
```

再对比三种范式（需视觉 API Key）：

```bash
python demo.py \
  --file test_files/sample_chart.png \
  --query "Which quarter had the highest revenue, and what was the exact value?" \
  --model gpt-5.6-luna
```

各 CLI 均有中文 `--help`。

### 用法

```bash
python main.py --interactive
# /file /mode /model /tools /history /clear /quit

python main.py --file document.pdf --query "What is the main topic?"
python main.py --mode extract_to_text --file image.jpg --query "Describe this image"
python main.py --tools --mode extract_to_text --file audio.mp3 --query "What's the content?"
```

程序化用法见 English 节 `asyncio` 示例。

### 对比演示

```bash
python demo.py --file document.pdf --query "What are the key findings?" --model gpt-5.6-luna
python demo.py --file test_files/sample_chart.png \
  --query "Which quarter had the highest revenue?" \
  --model gpt-5.6-luna --skip-model-comparison --output result.txt
```

| 标志 | 说明 |
|------|------|
| `--file` | 多模态文件 |
| `--query` | 问题 |
| `--model` | 默认 `gemini-3.5-flash` |
| `--skip-model-comparison` | 只做三范式对比 |
| `--generate-sample` | 离线生成样例后退出 |
| `--output`, `-o` | 保存完整记录 |

### 模式对比

| 模式 | 优势 | 劣势 | 适用 |
|------|------|------|------|
| **原生** | 上下文与视觉完整 | 模型支持有限、token 多 | 复杂混排文档 |
| **抽文本** | 通用、可缓存 | 丢视觉细节 | 文本向 / 控成本 |
| **工具** | 可追问、按需深挖 | 多次 API | 交互式问答 |

### 文件与模型能力

支持 PDF / 常见图像 / 常见音频；大小限制 PDF/图 20MB、音频 25MB。能力矩阵与 English 表相同。

### API Key

- `GOOGLE_API_KEY` 或 `GEMINI_API_KEY`  
- `OPENAI_API_KEY`  
- `DOUBAO_API_KEY` 或 `ARK_API_KEY`  

### 测试

```bash
python test_multimodal.py
```

### 许可

MIT — 教学项目。

---

## Notes / 说明

### OpenRouter 通用回退 / Universal OpenRouter fallback

Chat / vision can route via OpenRouter when `OPENROUTER_API_KEY` is set and primary keys are missing. **Audio transcription (Whisper) and native-PDF extraction still need direct OpenAI/Gemini keys.**
