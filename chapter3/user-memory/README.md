# User Memory System / 用户记忆系统

> Companion material for *AI Agents in Depth*, Chapter 3 — long-term user memory with separated conversation vs background processing, multiple memory modes, multi-provider support.  
> 配套《深入理解 AI Agent》第 3 章——长期用户记忆：对话与后台记忆处理分离、多种记忆模式、多模型提供商。

← [Chapter 3 index / 返回第 3 章目录](../README.md)

---

## English

### Key features

- **Separated architecture**: conversational agent vs background memory processor  
- **Memory modes**: notes → enhanced notes → JSON cards → advanced JSON cards  
- **Providers**: Kimi/Moonshot, SiliconFlow, Doubao, OpenRouter  
- **React + tools** for structured memory ops  
- **Streaming** with tool calls  
- **Evaluation** integration with `user-memory-evaluation`  
- **Background processing** on conversation intervals  
- **Persistent** JSON storage + conversation history  

### Installation

Python 3.8+, at least one LLM API key.

```bash
cd chapter3/user-memory
pip install -r requirements.txt
cp env.example .env
# MOONSHOT_API_KEY / SILICONFLOW_API_KEY / DOUBAO_API_KEY / OPENROUTER_API_KEY
```

### Quick start

```bash
python quickstart.py

python main.py --mode interactive --user your_name
# interactive: memory | process | save | reset | quit/exit

python main.py --mode demo --memory-mode enhanced_notes
python main.py --mode evaluation --memory-mode advanced_json_cards
```

### Architecture

```
User Interface
  → Conversational Agent (dialogue, read memory, stream; no direct writes)
  → Background Memory Processor (analyze, update via tools)
  → Memory Manager (notes / JSON cards storage)
```

**Core modules:** `conversational_agent.py`, `background_memory_processor.py`, `agent.py` (UserMemoryAgent + tools), `memory_manager.py`.

### Memory modes

1. **`notes`** — short facts/preferences  
2. **`enhanced_notes`** — contextual paragraphs  
3. **`json_cards`** — hierarchical JSON  
4. **`advanced_json_cards`** — full cards with backstory, person, relationship, timestamps  

### Execution modes

```bash
python main.py --mode interactive \
    --user john_doe \
    --memory-mode enhanced_notes \
    --conversation-interval 2

python main.py --mode demo --provider siliconflow --memory-mode json_cards
python main.py --mode evaluation --memory-mode advanced_json_cards --provider kimi
```

### Providers

| Provider | Models (examples) | Notes |
|----------|-------------------|--------|
| Kimi/Moonshot | kimi-k3 | Chinese, general |
| SiliconFlow | Qwen3-235B-… | High performance |
| Doubao | doubao-seed-1-6-thinking-… | ByteDance |
| OpenRouter | Gemini / GPT / Claude | Multi-model |

```bash
python main.py --provider siliconflow --model "Qwen/Qwen3-235B-A22B-Thinking-2507"
python main.py --provider openrouter --model "google/gemini-3.5-flash"
python main.py --provider doubao --model "doubao-seed-1-6-thinking-250715"
```

### API usage

```python
from conversational_agent import ConversationalAgent, ConversationConfig
from config import MemoryMode

agent = ConversationalAgent(
    user_id="user123",
    provider="kimi",
    config=ConversationConfig(enable_memory_context=True, temperature=0.7),
    memory_mode=MemoryMode.ENHANCED_NOTES
)
response = agent.chat("Hi, I'm Alice and I work at TechCorp")
```

```python
from background_memory_processor import BackgroundMemoryProcessor, MemoryProcessorConfig

processor = BackgroundMemoryProcessor(
    user_id="user123",
    provider="kimi",
    config=MemoryProcessorConfig(conversation_interval=2, enable_auto_processing=True),
    memory_mode=MemoryMode.JSON_CARDS
)
processor.start_background_processing()
results = processor.process_recent_conversations()
```

```python
from agent import UserMemoryAgent, UserMemoryConfig

agent = UserMemoryAgent(
    user_id="user123",
    provider="siliconflow",
    config=UserMemoryConfig(enable_memory_updates=True, memory_mode=MemoryMode.ADVANCED_JSON_CARDS)
)
result = agent.execute_task("Remember that I prefer Python and my email is john@example.com")
```

### Evaluation

```bash
python main.py --mode evaluation --memory-mode advanced_json_cards
```

Uses test cases from `user-memory-evaluation` (histories → question → score/feedback; 60+ cases).

### Advanced configuration

```bash
PROVIDER=kimi
MODEL_TEMPERATURE=0.3
MODEL_MAX_TOKENS=4096
MEMORY_MODE=enhanced_notes
MAX_MEMORY_ITEMS=100
MEMORY_UPDATE_TEMPERATURE=0.2
SESSION_TIMEOUT=3600
MAX_CONTEXT_LENGTH=8000
MEMORY_STORAGE_DIR=data/memories
CONVERSATION_HISTORY_DIR=data/conversations
```

```bash
python main.py \
    --mode interactive \
    --user custom_user \
    --memory-mode advanced_json_cards \
    --provider openrouter \
    --model "google/gemini-3.5-flash" \
    --conversation-interval 3 \
    --background-processing True \
    --no-verbose
```

### Project structure

```
user-memory/
├── main.py, quickstart.py, agent.py
├── conversational_agent.py, background_memory_processor.py
├── memory_manager.py, config.py, conversation_history.py
├── memory_operation_formatter.py, run_evaluation.py, locomo_benchmark.py
├── PROVIDERS.md, requirements.txt, env.example
├── data/{memories,conversations}/, logs/
```

### Development smoke tests

```bash
python quickstart.py
python -c "from memory_manager import NotesMemoryManager; m=NotesMemoryManager('smoke'); print(m.consolidate_memories())"
```

### Notes / license

Background processing is async; tools logged; streaming supported; state persists. Educational materials.

---

## 中文

### 关键特性

- **分离架构**：对话 Agent 与后台记忆处理器解耦  
- **多种记忆模式**：简单笔记 → 增强笔记 → JSON 卡片 → Advanced JSON Cards  
- **多提供商**：Kimi、SiliconFlow、豆包、OpenRouter  
- **React + 工具** 结构化记忆操作  
- **流式输出**、**评测集成**、**按间隔后台更新**、**JSON 持久化**  

### 安装

```bash
cd chapter3/user-memory
pip install -r requirements.txt
cp env.example .env
# 配置 MOONSHOT_API_KEY / SILICONFLOW_API_KEY / DOUBAO_API_KEY / OPENROUTER_API_KEY
```

### 快速开始

```bash
python quickstart.py
python main.py --mode interactive --user your_name
# memory | process | save | reset | quit/exit

python main.py --mode demo --memory-mode enhanced_notes
python main.py --mode evaluation --memory-mode advanced_json_cards
```

### 架构

用户界面 → **ConversationalAgent**（对话、读记忆、流式）+ **BackgroundMemoryProcessor**（分析并写记忆）→ **MemoryManager**（笔记/JSON 卡片）。

核心文件：`conversational_agent.py`、`background_memory_processor.py`、`agent.py`、`memory_manager.py`。

### 记忆模式

1. **`notes`** — 短事实  
2. **`enhanced_notes`** — 带上下文的段落  
3. **`json_cards`** — 层次化 JSON  
4. **`advanced_json_cards`** — 含 backstory / person / relationship 等完整卡片  

### 运行模式

```bash
python main.py --mode interactive --user john_doe --memory-mode enhanced_notes --conversation-interval 2
python main.py --mode demo --provider siliconflow --memory-mode json_cards
python main.py --mode evaluation --memory-mode advanced_json_cards --provider kimi
```

### 提供商

见 English 表与 `--provider` / `--model` 示例。

### 编程接口

见 English 节 `ConversationalAgent` / `BackgroundMemoryProcessor` / `UserMemoryAgent` 示例。

### 评测

```bash
python main.py --mode evaluation --memory-mode advanced_json_cards
```

对接 `user-memory-evaluation` 的用例与打分。

### 高级配置与项目结构

环境变量、`main.py` CLI 参数、目录树与 English 节相同。

### 冒烟测试

```bash
python quickstart.py
python -c "from memory_manager import NotesMemoryManager; m=NotesMemoryManager('smoke'); print(m.consolidate_memories())"
```

### 说明

记忆后台异步处理；工具调用可记录；支持流式；状态跨会话持久。教学材料。

---

## Notes / 说明

### OpenRouter 通用回退 / Universal OpenRouter fallback

Primary provider keys take precedence; else `OPENROUTER_API_KEY` routes chat LLM via OpenRouter with automatic model id mapping. See `env.example`. Related: [`../user-memory-evaluation/`](../user-memory-evaluation/), [`../mem0/`](../mem0/), [`../memobase/`](../memobase/).
