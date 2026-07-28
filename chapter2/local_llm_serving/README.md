# Local LLM Serving & Tool Calling / 本地 LLM 服务部署与工具调用

> Companion material for *AI Agents in Depth*, Chapter 2 — **Experiment 2-1 ★: Local LLM service deployment and tool calling**.  
> 配套《深入理解 AI Agent》第 2 章 **实验 2-1 ★：本地 LLM 服务部署与工具调用**。

← [Chapter 2 index / 返回第 2 章目录](../README.md)

---

## English

### Overview

Cross-platform demo of LLM tool calling via standard OpenAI-compatible APIs. Works on Windows, macOS, and Linux by auto-selecting the best backend.

### Features

- **Universal entry:** single `main.py` for all platforms
- **Automatic backend:**
  - **vLLM** on Linux (including WSL2) with NVIDIA GPU
  - **Ollama** on native Windows, macOS, or Linux without CUDA
- **Standard tool calling** only (OpenAI-compatible format)
- **Built-in tools:** weather, calculator, time, currency, PDF parse, code interpreter
- **Interactive & example modes**
- **Streaming:** real-time thinking, tool calls, and responses

### Quick start

```bash
# 1. Clone / enter project
cd chapter2/local_llm_serving

# 2. Install dependencies
pip install -r requirements.txt

# 3. Check system compatibility
python check_compatibility.py

# 4. Run (auto-detects backend)
python main.py
```

### Prerequisites

**All platforms:** Python 3.10+, `pip install -r requirements.txt`

#### macOS
```bash
brew install ollama
ollama serve          # separate terminal
ollama pull qwen3:0.6b
```

#### Windows
**Native Windows always uses Ollama**, including systems with an NVIDIA GPU. Install it from [ollama.com](https://ollama.com/download/windows), then run `ollama pull qwen3:0.6b`.

Official vLLM GPU execution requires Linux. To use vLLM on a Windows machine, run the project inside WSL2 (with CUDA support) or a Linux container. Community-maintained native Windows ports are outside this project's supported setup.

#### Linux
**With NVIDIA GPU:** CUDA → vLLM automatic.  
**Without GPU:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
systemctl start ollama
ollama pull qwen3:0.6b
```

### Usage

```bash
python main.py                      # auto-detect
python main.py --mode examples
python main.py --mode interactive
python main.py --backend ollama     # force Ollama
python main.py --backend vllm       # force vLLM (Linux/WSL2 + GPU)
python main.py --info
```

#### In code

```python
from main import ToolCallingAgent

agent = ToolCallingAgent()
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
├── main.py              # Main entry (auto-detect backend)
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
python main.py              # streaming on by default
python main.py --no-stream
# toggle during chat with /stream
```

```python
from main import ToolCallingAgent

agent = ToolCallingAgent()
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
python benchmark.py --scenario all --output results.json
python benchmark.py --scenario kv-cache --backend ollama
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
- **CUDA not available:** install drivers/CUDA, or let the script fall back to Ollama
- **Native Windows with CUDA:** Ollama is selected because official vLLM requires Linux; use WSL2 or a Linux container for vLLM
- **Compatibility:** `python check_compatibility.py`

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

跨平台本地 LLM 工具调用演示，统一使用 OpenAI 兼容 API。在 Windows、macOS、Linux 上自动选择最合适的后端。

### 功能

- **统一入口：** 单一 `main.py` 覆盖各平台
- **自动选后端：**
  - Linux（含 WSL2）+ NVIDIA GPU → **vLLM**
  - 原生 Windows、macOS、无 CUDA 的 Linux → **Ollama**
- **仅标准工具调用**（OpenAI 兼容格式）
- **内置工具：** 天气、时间、汇率、PDF、代码解释器等
- **交互与示例模式**
- **流式输出：** 实时展示思考、工具调用与回复

### 快速开始

```bash
cd chapter2/local_llm_serving
pip install -r requirements.txt
python check_compatibility.py
python main.py
```

### 前置条件

**全平台：** Python 3.10+，`pip install -r requirements.txt`

#### macOS
```bash
brew install ollama
ollama serve
ollama pull qwen3:0.6b
```

#### Windows
**原生 Windows 始终使用 Ollama**，包括装有 NVIDIA GPU 的系统。从 [ollama.com](https://ollama.com/download/windows) 安装 Ollama，再运行 `ollama pull qwen3:0.6b`。

vLLM 官方 GPU 执行环境要求 Linux。若要在 Windows 机器上使用 vLLM，请在支持 CUDA 的 WSL2 或 Linux 容器中运行本项目。社区维护的原生 Windows 移植版不属于本项目支持的配置。

#### Linux
**有 NVIDIA GPU：** CUDA → 自动 vLLM。  
**无 GPU：**
```bash
curl -fsSL https://ollama.com/install.sh | sh
systemctl start ollama
ollama pull qwen3:0.6b
```

### 用法

```bash
python main.py                      # 自动检测
python main.py --mode examples
python main.py --mode interactive
python main.py --backend ollama
python main.py --backend vllm       # 仅 Linux/WSL2 + GPU
python main.py --info
```

#### 在代码中使用

```python
from main import ToolCallingAgent

agent = ToolCallingAgent()
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
├── main.py              # 主入口（自动选后端）
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
python main.py              # 默认开启流式
python main.py --no-stream
# 对话中用 /stream 切换
```

```python
from main import ToolCallingAgent

agent = ToolCallingAgent()
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
python benchmark.py --scenario all --output results.json
python benchmark.py --scenario kv-cache --backend ollama
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
- **CUDA 不可用：** 安装驱动/CUDA，或让脚本自动改用 Ollama
- **原生 Windows 有 CUDA：** 仍会选择 Ollama，因为官方 vLLM 要求 Linux；如需 vLLM，请使用 WSL2 或 Linux 容器
- **兼容性检查：** `python check_compatibility.py`

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
