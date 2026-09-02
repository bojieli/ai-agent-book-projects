# Local LLM Serving & Tool Calling / 本地 LLM 服务部署与工具调用

> Companion material for *AI Agents in Depth*, Chapter 2 — **Experiment 2-1 ★: Local LLM service deployment and tool calling**.  
> 配套《深入理解 AI Agent》第 2 章 **实验 2-1 ★：本地 LLM 服务部署与工具调用**。

← [Chapter 2 index / 返回第 2 章目录](../README.md)

---

## English

### Overview

Cross-platform demo of LLM tool calling via standard OpenAI-compatible APIs. The default root `ch2` install uses Ollama explicitly; Linux/WSL GPU users can add the `vllm` extra and run vLLM explicitly.

### Features

- **Universal entry:** single `main.py` for all platforms
- **Backend paths:**
  - **vLLM** on Linux/WSL2 with NVIDIA GPU after installing the `vllm` extra
  - **Ollama** on macOS, native Windows, or Linux without GPU
- **Standard tool calling** only (OpenAI-compatible format)
- **Built-in tools:** weather, calculator, time, currency, PDF parse, code interpreter
- **Interactive & single-task modes**
- **Streaming:** real-time thinking, tool calls, and responses

### Quick start

```bash
# 1. From the repository root, install the shared Chapter 2 environment
uv sync --locked --python 3.12 --extra ch2

# Optional GPU/vLLM path on supported Linux/WSL NVIDIA setups:
# uv sync --locked --python 3.12 --extra ch2 --extra vllm

# Activate before changing directories:
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

# pip fallback when uv is not installed:
# python -m pip install -e ".[ch2]"
# Linux/WSL GPU/vLLM pip fallback: python -m pip install -e ".[ch2,vllm]"

# 2. Enter project
cd chapter2/local_llm_serving

# Single-project compatibility path, still supported during migration:
# python -m pip install -r requirements.txt

# 3. Run
# Default root ch2 install:
python main.py --backend ollama
# Linux/WSL GPU path, only after installing --extra vllm:
# python check_compatibility.py
# python main.py --backend vllm
```

### Prerequisites

**All platforms:** Python 3.12 and the root `ch2` extra (`uv sync --locked --python 3.12 --extra ch2`).

Use `--extra vllm` only for the Linux/WSL GPU path; the default `ch2` install keeps local serving usable with Ollama without pulling the Linux/GPU vLLM stack. Use explicit `--backend` flags so CUDA presence does not select a backend you did not install.

#### macOS
```bash
brew install ollama
ollama serve          # separate terminal
ollama pull qwen3:0.6b
```

#### Windows
**Native Windows always uses Ollama**, including systems with an NVIDIA GPU. Install it from [ollama.com](https://ollama.com/download/windows), then run `ollama pull qwen3:0.6b` and `python main.py --backend ollama`.

Official vLLM GPU execution requires Linux. To use vLLM on a Windows machine, run the project inside WSL2 (with CUDA support) or a Linux container. Community-maintained native Windows ports are outside this project's supported setup.

#### Linux
**With NVIDIA GPU:** install the `vllm` extra, then run `python main.py --backend vllm`.

**Without GPU:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
systemctl start ollama
ollama pull qwen3:0.6b
```

### Usage

```bash
python main.py --backend ollama     # default install or native Windows
python main.py --backend vllm       # Linux/WSL2 GPU after --extra vllm
python main.py --backend ollama --mode single --task "What's the weather in Tokyo?"
python main.py --backend ollama --mode interactive
python main.py --backend ollama --info
```

#### In code

```python
from main import ToolCallingAgent

agent = ToolCallingAgent(backend="ollama")  # default install or native Windows
# agent = ToolCallingAgent(backend="vllm")  # Linux/WSL GPU after --extra vllm
response = agent.chat("What's the weather in Tokyo?")
print(response)
response = agent.chat("Tell me a joke", use_tools=False)
agent.reset_conversation()
```

#### Custom tools

```python
from tools import ToolRegistry

registry = ToolRegistry()

def my_custom_tool(param1: str, param2: int) -> str:
    return f"Processed {param1} with {param2}"

registry.register_tool(
    name="my_custom_tool",
    function=my_custom_tool,
    description="My custom tool description",
    parameters={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "First parameter"},
            "param2": {"type": "integer", "description": "Second parameter"}
        },
        "required": ["param1", "param2"]
    }
)
```

### Project structure

```
local_llm_serving/
├── main.py              # Main entry with explicit backend flags
├── benchmark.py         # Serving benchmark: throughput / TTFT / KV cache / batching
├── agent.py             # vLLM agent
├── ollama_native.py     # Ollama native tool calling
├── tools.py             # Tool implementations
├── config.py            # Config
├── server.py            # vLLM server manager
├── check_compatibility.py
├── requirements.txt
├── env.example
└── README.md
```

### Built-in tools

1. **get_current_temperature** — Open-Meteo (no API key)
2. **get_current_time** — timezones
3. **convert_currency** — simulated rates
4. **parse_pdf** — URL or local file
5. **code_interpreter** — execute Python

### Streaming

Shows internal thinking, tool calls, results, and streamed final text.

```bash
python main.py --backend ollama              # streaming on by default
python main.py --backend ollama --no-stream
# toggle during chat with /stream
```

```python
from main import ToolCallingAgent

agent = ToolCallingAgent(backend="ollama")
for chunk in agent.chat("What's the weather in Tokyo?", stream=True):
    chunk_type = chunk.get("type")
    content = chunk.get("content", "")
    if chunk_type == "thinking":
        print(f"Thinking: {content}")
    elif chunk_type == "tool_call":
        print(f"Tool: {content['name']}")
    elif chunk_type == "tool_result":
        print(f"Result: {content}")
    elif chunk_type == "content":
        print(content, end="", flush=True)
```

```bash
python demo_streaming.py
python test_streaming.py --mode compare
```

#### Where the reasoning goes: the `thinking` field vs. `<think>` in `content`

A common surprise when running this experiment: the book says a chain-of-thought model reasons inside `<think>` tags, yet nothing resembling `<think>` ever appears in `content` — the reasoning shows up in a separate `thinking` field instead. Both are true. `<think>` is a tag in the model's **raw token stream**; Ollama parses it out before the response reaches your client.

You can observe each layer yourself against a running Ollama. The outputs below were captured on Ollama 0.20.7 + `qwen3:0.6b`; the reasoning wording differs from run to run, but the message shape does not.

**1. Non-streaming `/api/chat` — reasoning arrives in its own `thinking` field:**

```bash
curl -s http://localhost:11434/api/chat -d '{
  "model": "qwen3:0.6b", "stream": false, "think": true,
  "messages": [{"role": "user", "content": "What is 17 * 23? Answer with just the number."}]
}' | python -m json.tool
```

```jsonc
{
  "message": {
    "role": "assistant",
    "content": "391",                    // clean answer, no <think> tag
    "thinking": "Okay, so I need to find 17 multiplied by 23. Let me think ..."
  }
}
```

**2. Streaming — the same reasoning arrives as incremental `thinking` deltas**, while `content` stays empty until the model finishes thinking:

```bash
curl -sN http://localhost:11434/api/chat -d '{
  "model": "qwen3:0.6b", "stream": true, "think": true,
  "messages": [{"role": "user", "content": "What is the weather in Tokyo?"}]
}' | head -3
```

```jsonc
{"message":{"role":"assistant","content":"","thinking":"Okay"},"done":false}
{"message":{"role":"assistant","content":"","thinking":","},"done":false}
{"message":{"role":"assistant","content":"","thinking":" the"},"done":false}
```

**3. The tag really is in the raw token stream.** Bypass both the chat template (`raw: true`) and Ollama's thinking parser (`think: false`), and `<think>` reappears:

```bash
curl -s http://localhost:11434/api/generate -d '{
  "model": "qwen3:0.6b", "raw": true, "stream": false, "think": false,
  "options": {"num_predict": 60},
  "prompt": "<|im_start|>user\nWhat is 17 * 23?<|im_end|>\n<|im_start|>assistant\n"
}' | python -c "import json,sys; print(json.load(sys.stdin)['response'][:120])"
```

```text
<think>
Okay, so I need to find 17 multiplied by 23. Hmm, let me think. First, I remember that multiplying numbers can b
```

So the `thinking` field and the `<think>` tag are two presentations of the same tokens: the model emits the tag, and the server decides whether you see it raw or pre-parsed.

**How this project handles it.** `OllamaNativeAgent._chat_with_think_fallback()` sends `think=True`, so cases 1 and 2 are the normal path: `chat_stream()` reads `message.thinking` and yields `{"type": "thinking", ...}` chunks. The `<think>` / `</think>` string parsing you will also find in `chat_stream()` covers the other case, where a server hands the tag back inline in `content`. Models with no thinking support at all (qwen2.5, llama3.2, gemma, …) reject `think=True` with HTTP 400; `_chat_with_think_fallback()` catches that once per model, retries without `think`, and caches the decision — you simply get no thinking chunks for those models.

### Serving benchmark (`benchmark.py`)

Companion to Experiment 2-1: measure **serving** metrics (throughput / latency / batching / KV cache) on a local small model via OpenAI-compatible APIs (vLLM or Ollama).

**All numbers come from the real server; the script synthesizes nothing.** Use `--dry-run` offline to inspect planned requests.

#### Scenarios (`--scenario`)

| Scenario | What it measures | Book point |
|----------|------------------|------------|
| `throughput` | Single-stream decode tok/s and TTFT | Exp 2-1 point 2: >100 tok/s on M2-class machines |
| `kv-cache` | Prefix cache **hit vs miss** TTFT | Exp 2-1 point 5: change system-prompt start → full prefix recompute |
| `batching` | Aggregate throughput vs concurrency | Continuous batching trade-offs |
| `all` | Run all of the above (default) | — |

#### Usage

```bash
# 1. Start a server (pick one)
python server.py                            # vLLM (Linux/WSL2 + NVIDIA GPU)
ollama serve && ollama pull qwen3:0.6b      # Ollama (Mac / no GPU)

# 2. Run benchmark
# If you use Ollama, add --backend ollama to every command below.
python benchmark.py --scenario all --output results.json
python benchmark.py --scenario kv-cache
python benchmark.py --scenario batching --concurrency 1,2,4,8

python benchmark.py --dry-run
python benchmark.py --help
```

#### Main flags

- `--backend {vllm,ollama}` — default URL/model (vLLM `Qwen3-0.6B` @ `:8000/v1`, Ollama `qwen3:0.6b` @ `:11434/v1`)
- `--base-url` / `--model` / `--api-key` — override connection
- `--repeats` — repeats for throughput / kv-cache (default 5)
- `--max-tokens` / `--temperature`
- `--prefix-tokens` — shared prefix length for kv-cache (default 1024)
- `--concurrency` — batching concurrency list, comma-separated (default `1,2,4,8`)
- `--output` — write JSON results

> `kv-cache` needs server prefix caching (vLLM automatic prefix caching is on by default). Hit group keeps the system prompt byte-identical; miss group inserts a unique counter only at the **start** of the system prompt so the whole prefix invalidates—demonstrating “once the system prompt is fixed, don’t change it.”

### Complete manuscript campaign (`run_experiment.py`)

The benchmark above measures individual serving properties. The acceptance
campaign additionally exercises the manuscript's complete Vancouver example:
Qwen3 emits two raw XML tool calls in one turn, the time and weather tools run
concurrently, their results are returned through the chat template, and the
model decides to stop. It then records five matched prefix-cache hit/miss pairs.
The exact rendered token stream, every Ollama stream chunk, model digest,
server token counts/durations, wall-clock TTFT, hashes, and a credential scan
are retained; no output is synthesized.

```bash
ollama serve                         # separate terminal, if not already running
ollama pull qwen3:0.6b
python run_experiment.py \
  --output runs/exp2-1-qwen3-0.6b-$(date +%Y%m%d-%H%M%S)
```

The frozen design is [experiment_protocol.json](experiment_protocol.json).
`manifest.json` is the completion receipt and `evidence.json` is the raw
auditable record. Local inference costs $0 in API fees; the report does not
generalize the measured throughput to other hardware.

### Configuration

Copy `env.example` to `.env`:

```bash
MODEL_NAME=Qwen/Qwen3-0.6B
VLLM_HOST=localhost
VLLM_PORT=8000
LOG_LEVEL=INFO
```

### Tool calling format

Standard OpenAI-compatible:

```json
{
  "tool_calls": [{
    "id": "call_123",
    "type": "function",
    "function": {
      "name": "get_weather",
      "arguments": {"location": "Tokyo"}
    }
  }]
}
```

### Troubleshooting

- **Ollama not found:** Mac `brew install ollama && ollama serve`; Windows [ollama.com](https://ollama.com/download/windows); Linux install script above
- **No models:** `ollama pull qwen3:0.6b`
- **CUDA not available:** install drivers/CUDA for the vLLM path, or run `python main.py --backend ollama`
- **Native Windows with CUDA:** use Ollama on native Windows; use WSL2 or a Linux container for vLLM
- **Compatibility:** `python check_compatibility.py` is for the Linux/WSL2 vLLM path; native Windows should use `python main.py --backend ollama`.

### Supported models

**Default:** Qwen3 0.6B (small, decent tool calling).  
**Also good for tools:** Qwen3 8B+, Llama 3.1/3.2 8B+, Mistral Nemo.  
**vLLM:** default Qwen3-0.6B; any vLLM-supported model can be configured.

### How it works

1. Detect OS and GPU
2. Linux/WSL2 + NVIDIA GPU → vLLM; native Windows, macOS, or Linux without CUDA → Ollama
3. Both use standard OpenAI tool calling
4. Tool results are fed back into the model

### References

- [vLLM Documentation](https://docs.vllm.ai/)
- [Ollama Documentation](https://ollama.com/)
- [OpenAI Tool Calling](https://platform.openai.com/docs/guides/function-calling)

---

## 中文

### 概述

跨平台本地 LLM 工具调用演示，统一使用 OpenAI 兼容 API。默认根目录 `ch2` 安装显式使用 Ollama；Linux/WSL GPU 用户可额外安装 `vllm` extra 后显式运行 vLLM。

### 功能

- **统一入口：** 单一 `main.py` 覆盖各平台
- **后端路径：**
  - Linux/WSL2 + NVIDIA GPU，且已安装 `vllm` extra → **vLLM**
  - macOS、原生 Windows、无 GPU 的 Linux → **Ollama**
- **仅标准工具调用**（OpenAI 兼容格式）
- **内置工具：** 天气、时间、汇率、PDF、代码解释器等
- **交互与单任务模式**
- **流式输出：** 实时展示思考、工具调用与回复

### 快速开始

```bash
# 在仓库根目录安装统一的第 2 章环境
uv sync --locked --python 3.12 --extra ch2

# 支持的 Linux/WSL NVIDIA 环境如需 GPU/vLLM，可改用：
# uv sync --locked --python 3.12 --extra ch2 --extra vllm

# 切换目录前先激活环境：
# macOS/Linux：
source .venv/bin/activate
# Windows PowerShell：.venv\Scripts\Activate.ps1
# Windows cmd：.venv\Scripts\activate.bat

# 未安装 uv 时可用 pip 兜底：
# python -m pip install -e ".[ch2]"
# Linux/WSL GPU/vLLM pip 兜底：python -m pip install -e ".[ch2,vllm]"

cd chapter2/local_llm_serving

# 迁移期间仍支持单项目兼容路径：
# python -m pip install -r requirements.txt

# 默认根目录 ch2 安装：
python main.py --backend ollama
# Linux/WSL GPU 路径，仅在安装 --extra vllm 后使用：
# python check_compatibility.py
# python main.py --backend vllm
```

### 前置条件

**全平台：** Python 3.12，并安装根目录 `ch2` extra（`uv sync --locked --python 3.12 --extra ch2`）。

只有走 Linux/WSL GPU/vLLM 路径时才需要额外选择 `--extra vllm`；默认 `ch2` 安装保留 Ollama 路径，不会拉取 Linux/GPU vLLM 栈。请显式传入 `--backend`，避免仅因检测到 CUDA 而选择未安装的后端。

#### macOS
```bash
brew install ollama
ollama serve
ollama pull qwen3:0.6b
```

#### Windows
**原生 Windows 始终使用 Ollama**，包括装有 NVIDIA GPU 的系统。从 [ollama.com](https://ollama.com/download/windows) 安装 Ollama，再运行 `ollama pull qwen3:0.6b` 和 `python main.py --backend ollama`。

vLLM 官方 GPU 执行环境要求 Linux。若要在 Windows 机器上使用 vLLM，请在支持 CUDA 的 WSL2 或 Linux 容器中运行本项目。社区维护的原生 Windows 移植版不属于本项目支持的配置。

#### Linux
**有 NVIDIA GPU：** 安装 `vllm` extra 后运行 `python main.py --backend vllm`。

**无 GPU：**
```bash
curl -fsSL https://ollama.com/install.sh | sh
systemctl start ollama
ollama pull qwen3:0.6b
```

### 用法

```bash
python main.py --backend ollama     # 默认安装或原生 Windows
python main.py --backend vllm       # Linux/WSL2 GPU，需先安装 --extra vllm
python main.py --backend ollama --mode single --task "What's the weather in Tokyo?"
python main.py --backend ollama --mode interactive
python main.py --backend ollama --info
```

#### 在代码中使用

```python
from main import ToolCallingAgent

agent = ToolCallingAgent(backend="ollama")  # 默认安装或原生 Windows
# agent = ToolCallingAgent(backend="vllm")  # Linux/WSL GPU，需先安装 --extra vllm
response = agent.chat("What's the weather in Tokyo?")
print(response)
response = agent.chat("Tell me a joke", use_tools=False)
agent.reset_conversation()
```

#### 添加自定义工具

```python
from tools import ToolRegistry

registry = ToolRegistry()

def my_custom_tool(param1: str, param2: int) -> str:
    return f"Processed {param1} with {param2}"

registry.register_tool(
    name="my_custom_tool",
    function=my_custom_tool,
    description="My custom tool description",
    parameters={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "First parameter"},
            "param2": {"type": "integer", "description": "Second parameter"}
        },
        "required": ["param1", "param2"]
    }
)
```

### 项目结构

```
local_llm_serving/
├── main.py              # 主入口，支持显式后端参数
├── benchmark.py         # 服务基准：吞吐 / TTFT / KV Cache / 批处理
├── agent.py             # vLLM Agent
├── ollama_native.py     # Ollama 原生工具调用
├── tools.py             # 工具实现
├── config.py            # 配置
├── server.py            # vLLM 服务管理
├── check_compatibility.py
├── requirements.txt
├── env.example
└── README.md
```

### 内置工具

1. **get_current_temperature** — Open-Meteo（无需 API Key）
2. **get_current_time** — 多时区时间
3. **convert_currency** — 模拟汇率
4. **parse_pdf** — URL 或本地 PDF
5. **code_interpreter** — 执行 Python

### 流式模式

展示内部思考、工具调用、工具结果与逐字最终回复。

```bash
python main.py --backend ollama              # 默认开启流式
python main.py --backend ollama --no-stream
# 对话中用 /stream 切换
```

```python
from main import ToolCallingAgent

agent = ToolCallingAgent(backend="ollama")
for chunk in agent.chat("What's the weather in Tokyo?", stream=True):
    chunk_type = chunk.get("type")
    content = chunk.get("content", "")
    if chunk_type == "thinking":
        print(f"Thinking: {content}")
    elif chunk_type == "tool_call":
        print(f"Tool: {content['name']}")
    elif chunk_type == "tool_result":
        print(f"Result: {content}")
    elif chunk_type == "content":
        print(content, end="", flush=True)
```

```bash
python demo_streaming.py
python test_streaming.py --mode compare
```

#### 思考内容到底在哪里：`thinking` 字段与 `content` 里的 `<think>`

跑这个实验时常见的困惑：书里说支持思维链的模型会先在 `<think>` 标签内思考，但实际跑起来 `content` 里根本看不到 `<think>`，思考内容出现在一个单独的 `thinking` 字段里。两种说法都没错——`<think>` 是模型**原始 token 流**里的标签，Ollama 在把响应交给客户端之前就已经把它解析掉了。

对着运行中的 Ollama，可以自己逐层观察。下面的输出实测于 Ollama 0.20.7 + `qwen3:0.6b`——思考文字每次采样都不同，但消息结构是固定的。

**1. 非流式 `/api/chat`——思考内容在独立的 `thinking` 字段里：**

```bash
curl -s http://localhost:11434/api/chat -d '{
  "model": "qwen3:0.6b", "stream": false, "think": true,
  "messages": [{"role": "user", "content": "What is 17 * 23? Answer with just the number."}]
}' | python -m json.tool
```

```jsonc
{
  "message": {
    "role": "assistant",
    "content": "391",                    // 干净的答案，没有 <think> 标签
    "thinking": "Okay, so I need to find 17 multiplied by 23. Let me think ..."
  }
}
```

**2. 流式——同一份思考内容以 `thinking` 增量逐块到达**，模型思考完之前 `content` 一直是空字符串：

```bash
curl -sN http://localhost:11434/api/chat -d '{
  "model": "qwen3:0.6b", "stream": true, "think": true,
  "messages": [{"role": "user", "content": "What is the weather in Tokyo?"}]
}' | head -3
```

```jsonc
{"message":{"role":"assistant","content":"","thinking":"Okay"},"done":false}
{"message":{"role":"assistant","content":"","thinking":","},"done":false}
{"message":{"role":"assistant","content":"","thinking":" the"},"done":false}
```

**3. 标签确实存在于原始 token 流里。** 同时绕开 chat template（`raw: true`）和 Ollama 的思考解析（`think: false`），`<think>` 就露出来了：

```bash
curl -s http://localhost:11434/api/generate -d '{
  "model": "qwen3:0.6b", "raw": true, "stream": false, "think": false,
  "options": {"num_predict": 60},
  "prompt": "<|im_start|>user\nWhat is 17 * 23?<|im_end|>\n<|im_start|>assistant\n"
}' | python -c "import json,sys; print(json.load(sys.stdin)['response'][:120])"
```

```text
<think>
Okay, so I need to find 17 multiplied by 23. Hmm, let me think. First, I remember that multiplying numbers can b
```

所以 `thinking` 字段和 `<think>` 标签是同一批 token 的两种呈现方式：标签由模型生成，而你看到的是原样还是解析后的结果，取决于服务端。

**本项目如何处理。** `OllamaNativeAgent._chat_with_think_fallback()` 会传入 `think=True`，因此情况 1、2 是常规路径：`chat_stream()` 读取 `message.thinking` 并产出 `{"type": "thinking", ...}` 块。`chat_stream()` 里那段 `<think>` / `</think>` 字符串解析逻辑对应的是另一种情况——服务端把标签原样放在 `content` 里返回。至于完全不支持思考的模型（qwen2.5、llama3.2、gemma 等），它们会对 `think=True` 返回 HTTP 400，`_chat_with_think_fallback()` 每个模型只捕获一次，之后不带 `think` 重试并缓存该判断，此时就不会有任何 thinking 块。

### 服务基准（`benchmark.py`）

实验 2-1 的配套基准，测量本地小模型在 **serving** 层面的吞吐 / 延迟 / 批处理 / KV Cache，经 OpenAI 兼容接口工作（vLLM 与 Ollama 均可）。

**所有数字都来自真实服务端实测，脚本本身不产生任何合成数据。** 服务未启动时可用 `--dry-run` 离线查看将要发出的请求配置。

#### 场景（`--scenario`）

| 场景 | 说明 | 对应书中要点 |
|------|------|-------------|
| `throughput` | 单流解码吞吐（tok/s）与首 token 延迟（TTFT） | 实验 2-1 第 2 点：M2 上 >100 tok/s |
| `kv-cache` | 前缀缓存 **命中 vs 未命中** 的 TTFT 对比 | 实验 2-1 第 5 点：改动系统提示词开头 → 缓存失效 |
| `batching` | 不同并发度下的聚合吞吐 | 连续批处理如何提升系统吞吐 |
| `all` | 依次运行以上全部（默认） | — |

#### 用法

```bash
# 1. 先启动服务端（二选一）
python server.py                            # vLLM（Linux/WSL2 + NVIDIA GPU）
ollama serve && ollama pull qwen3:0.6b      # Ollama（Mac / 无 GPU）

# 2. 运行基准
# 如果使用 Ollama 后端，请在以下每条命令中添加 --backend ollama参数
python benchmark.py --scenario all --output results.json
python benchmark.py --scenario kv-cache
python benchmark.py --scenario batching --concurrency 1,2,4,8

python benchmark.py --dry-run
python benchmark.py --help
```

#### 主要参数

- `--backend {vllm,ollama}`：推断默认地址与模型名（vLLM `Qwen3-0.6B` @ `:8000/v1`，Ollama `qwen3:0.6b` @ `:11434/v1`）
- `--base-url` / `--model` / `--api-key`：覆盖默认连接配置
- `--repeats`：`throughput` / `kv-cache` 的重复次数（默认 5）
- `--max-tokens` / `--temperature`：生成参数
- `--prefix-tokens`：`kv-cache` 场景共享前缀的近似长度（默认 1024）
- `--concurrency`：`batching` 并发度列表，逗号分隔（默认 `1,2,4,8`）
- `--output`：将结果写入 JSON

> 说明：`kv-cache` 依赖服务端前缀缓存（vLLM automatic prefix caching 默认开启）。命中组保持系统提示词逐字节不变；未命中组每次只在系统提示词**开头**插入唯一计数串，前缀被改写导致缓存全部失效——这正是书中「系统提示词一旦定下来就不要改」的实测演示。

### 配置

复制 `env.example` 为 `.env`：

```bash
MODEL_NAME=Qwen/Qwen3-0.6B
VLLM_HOST=localhost
VLLM_PORT=8000
LOG_LEVEL=INFO
```

### 工具调用格式

标准 OpenAI 兼容格式（见英文节 JSON 示例）。

### 故障排除

- **找不到 Ollama：** Mac `brew install ollama && ollama serve`；Windows 官网安装；Linux 用安装脚本
- **没有模型：** `ollama pull qwen3:0.6b`
- **CUDA 不可用：** 为 vLLM 路径安装驱动/CUDA，或运行 `python main.py --backend ollama`
- **原生 Windows 有 CUDA：** 原生 Windows 请使用 Ollama；如需 vLLM，请使用 WSL2 或 Linux 容器
- **兼容性检查：** `python check_compatibility.py` 仅用于 Linux/WSL2 vLLM 路径；原生 Windows 请使用 `python main.py --backend ollama`。

### 支持的模型

**默认：** Qwen3 0.6B。  
**工具调用表现较好：** Qwen3 8B+、Llama 3.1/3.2 8B+、Mistral Nemo。  
**vLLM：** 默认 Qwen3-0.6B，可配置任意 vLLM 支持的模型。

### 工作原理

1. 检测操作系统与 GPU  
2. Linux/WSL2 + NVIDIA GPU → vLLM；原生 Windows、macOS 或无 CUDA 的 Linux → Ollama
3. 两端均使用标准 OpenAI 工具调用  
4. 工具结果回灌模型生成最终回复  

### 参考

- [vLLM Documentation](https://docs.vllm.ai/)
- [Ollama Documentation](https://ollama.com/)
- [OpenAI Tool Calling](https://platform.openai.com/docs/guides/function-calling)

---

## Notes / 说明

- Educational demo; license as provided in-repo for course use.  
- 教学演示用途；按仓库既有授权用于课程学习。
