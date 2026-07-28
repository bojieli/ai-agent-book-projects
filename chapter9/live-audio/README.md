## English

# Live Voice Chat Demo

A real-time voice chat demo featuring speech-to-text, AI conversation, and text-to-speech capabilities. The application supports multiple AI service providers and provides a seamless conversational experience with minimal latency.

> This is the companion code for **实验 9-1「构建传统语音 Agent」** in 《深入理解 AI Agent》第 9 章. It implements the **cascaded** voice pipeline (VAD → ASR → LLM → TTS) discussed there: the frontend captures the microphone and streams audio over a WebSocket; the backend runs Silero VAD to detect end-of-speech (~500 ms of silence), then routes the utterance through pluggable ASR, LLM, and TTS providers and streams synthesized audio back for playback.

## Features

- 🎤 Real-time voice input with Voice Activity Detection (VAD)
- 🤖 AI-powered conversations with **multiple provider support**
- 🔊 Text-to-speech synthesis
- ⚡ Low-latency audio streaming
- 📊 Real-time latency monitoring and logging
- 🎯 WebSocket-based communication
- 🔧 **Flexible provider selection** for ASR, LLM, and TTS services

## Supported AI Providers

### ASR (Automatic Speech Recognition)
- **OpenAI Whisper**: High accuracy, excellent language support
- **SenseVoice** (via Siliconflow): Low latency, cost-effective, auto language detection

### LLM (Large Language Model)
- **OpenAI GPT-4o**: Excellent reasoning, balanced performance
- **OpenRouter GPT-4o**: No geographic restrictions, unified interface
- **OpenRouter Gemini**: Fast response, optimized for real-time chat
- **ARK Doubao**: Low latency in China, optimized for Chinese language

### TTS (Text-to-Speech)
- **CosyVoice2** (via Siliconflow): Natural voice synthesis, multiple system voices

## Architecture Overview

The system consists of a frontend-backend architecture with real-time audio processing and **pluggable provider architecture**:

### Frontend (Next.js)
- **Audio Capture**: Uses Web Audio API to capture microphone input
- **Audio Processing**: Client-side audio processing and streaming to backend
- **WebSocket Communication**: Sends audio stream to backend and receives responses
- **Audio Playback**: Plays back TTS audio responses from the backend

### Backend (Node.js)
- **WebSocket Server**: Handles real-time audio streaming and client connections
- **Voice Activity Detection**: Server-side Silero VAD processing to detect speech boundaries with high accuracy
- **Multi-Provider Support**: Flexible ASR, LLM, and TTS provider integration
- **Provider Factories**: Dynamic provider creation and switching capabilities

### Data Flow
```
User Speech → WebSocket → Backend VAD → Multi-Provider STT → Multi-Provider LLM → TTS → Audio Response
```

### Ports

| Component | Port | Notes |
|-----------|------|-------|
| Backend (WebSocket server) | **8848** | Set by `LISTEN_PORT` in `backend/config.js`. The frontend connects to `ws://localhost:8848`. |
| Frontend (Next.js dev server) | **3000** | Open http://localhost:3000 in the browser. |

The frontend learns the backend port from the `WEBSOCKET_PORT` environment variable (see `frontend/.env.example`). It must match the backend's `LISTEN_PORT`.

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- **FFmpeg** - Required for audio processing and format conversion
- **Google Chrome** (recommended) - Best performance and compatibility for real-time audio
  - Not recommended: Safari, Edge, or other browsers due to WebAudio API limitations
- **API keys** from the supported providers (see Configuration section)

### Installing FFmpeg

#### macOS (using Homebrew)
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows
- Download from https://ffmpeg.org/download.html
- Or use Chocolatey: `choco install ffmpeg`
- Make sure `ffmpeg` is in your PATH

## Project Structure

```
/backend
- server.js: Main WebSocket server with provider integration
- config.js: Multi-provider configuration settings
- utils/
  - providers/
    - asrProviders.js: ASR provider implementations (OpenAI, Siliconflow)
    - llmProviders.js: LLM provider implementations (OpenAI, OpenRouter, ARK)
  - vad.js: Voice Activity Detection implementation
  - speechToText.js: Provider-aware STT service
  - textProcessor.js: Text preprocessing utilities
- tests/
  - provider-tests.js: Comprehensive provider testing
- run-tests.js: Test runner with environment validation
- utils/providers/: Provider configuration (ASR / LLM / TTS)
- package.json: Backend dependencies and scripts
```

```
/frontend
- pages/: Next.js pages
  - index.tsx: Main application interface
- components/: Reusable UI components
- public/: Static assets
  - audioWorklet.js: Audio processing and VAD implementation
- next.config.js: Next.js configuration
- tailwind.config.js: Tailwind CSS settings
- package.json: Frontend dependencies and scripts
```

## Installation

1. Clone the repository
2. Install backend dependencies: 
   ```bash
   cd backend && npm install
   ```
3. Install frontend dependencies: 
   ```bash
   cd frontend && npm install
   ```
4. Download the Silero VAD model (already included in this repo at `backend/models/silero_vad.onnx`; only needed if missing):
   ```bash
   cd backend/models
   wget https://huggingface.co/deepghs/silero-vad-onnx/resolve/main/silero_vad.onnx
   ```
5. Configure the frontend's WebSocket port (defaults to 8848 if omitted):
   ```bash
   cd frontend && cp .env.example .env   # sets WEBSOCKET_PORT=8848 to match the backend
   ```

After installing, verify your environment (Node version, FFmpeg, VAD model, provider keys) without needing a microphone or browser:

```bash
cd backend && npm run check    # or: node check-setup.js
```

This prints which prerequisites are satisfied and which selected providers have their API keys set. It exits non-zero only if a hard prerequisite (Node < 16, missing FFmpeg, or missing VAD model) is absent.

## Configuration

### Provider-Based Configuration

The system now supports **multiple AI service providers** for maximum flexibility. You can mix and match different providers for ASR, LLM, and TTS services.

### 1. Environment Variables Setup

Set up your API keys as environment variables:

```bash
# Required for OpenAI services
export OPENAI_API_KEY="your-openai-api-key"

# Required for OpenRouter services  
export OPENROUTER_API_KEY="your-openrouter-api-key"

# Required for ARK (Doubao) services
export ARK_API_KEY="your-ark-api-key"

# Required for Siliconflow services (ASR and TTS)
export SILICONFLOW_API_KEY="your-siliconflow-api-key"

# For future use
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 2. Provider Selection

1. This repo already ships a ready-to-edit `backend/config.js`. If it is missing (e.g. a fresh checkout that ignores it), copy the example first:
   ```bash
   cp backend/config.js.example backend/config.js
   ```

2. Edit `backend/config.js` to select your preferred providers:
   ```javascript
   const config = {
     // Provider Selection - Choose your preferred providers
     ASR_PROVIDER: 'siliconflow',      // 'openai' (whisper-1) or 'siliconflow' (SenseVoice)
     LLM_PROVIDER: 'openrouter',       // 'openrouter' (gpt-5.6-luna, default), 'openai', 'openrouter-gemini', 'ark'
     TTS_PROVIDER: 'siliconflow',      // 'siliconflow' (CosyVoice2)
     
     // API Keys (loaded from environment variables)
     OPENAI_API_KEY: process.env.OPENAI_API_KEY,
     OPENROUTER_API_KEY: process.env.OPENROUTER_API_KEY,
     ARK_API_KEY: process.env.ARK_API_KEY,
     SILICONFLOW_API_KEY: process.env.SILICONFLOW_API_KEY,
     
     // ... other configuration options
   };
   ```

### 3. Recommended Provider Combinations

#### Default / Recommended (works anywhere with an OpenRouter key)
```javascript
ASR_PROVIDER: 'siliconflow',      // SenseVoice
LLM_PROVIDER: 'openrouter',       // openai/gpt-5.6-luna via OpenRouter (avoids gpt-5.6* org verification)
TTS_PROVIDER: 'siliconflow',      // CosyVoice2
```

#### For Real-time Performance (Low Latency in China)
```javascript
ASR_PROVIDER: 'siliconflow',      // SenseVoice
LLM_PROVIDER: 'ark',              // Doubao (fast in China); or 'openrouter' for gpt-5.6-luna
TTS_PROVIDER: 'siliconflow',      // CosyVoice2
```

#### For Best Accuracy
```javascript
ASR_PROVIDER: 'openai',           // Accurate Whisper
LLM_PROVIDER: 'openrouter',       // openai/gpt-5.6-luna via OpenRouter
TTS_PROVIDER: 'siliconflow'       // CosyVoice2
```

### 4. API Key Requirements

You only need the API keys for the providers you plan to use:

| Provider | ASR | LLM | TTS | Required API Key |
|----------|-----|-----|-----|------------------|
| OpenAI | ✅ Whisper | ✅ gpt-5.6-luna | ❌ | `OPENAI_API_KEY` |
| OpenRouter | ❌ | ✅ gpt-5.6-luna, Gemini | ❌ | `OPENROUTER_API_KEY` |
| ARK (Doubao) | ❌ | ✅ Doubao | ❌ | `ARK_API_KEY` |
| Siliconflow | ✅ SenseVoice | ❌ | ✅ CosyVoice2 | `SILICONFLOW_API_KEY` |

### 5. Configuration Validation

The system includes comprehensive validation and testing tools:

```bash
# Test all configured providers
npm run test:providers

# Run the full test suite with environment validation
node run-tests.js
```

### Legacy Configuration Support

The system maintains backward compatibility with the previous hardcoded configuration format, but using the new provider selection is strongly recommended for better flexibility.

## Usage

1. **Set up your API keys** (see Configuration section)

2. **Configure your preferred providers** in `backend/config.js`

3. (Optional) **Verify your setup**: `cd backend && npm run check`

4. Start the backend server (WebSocket server on port **8848**): 
   ```bash
   cd backend && npm start
   ```
   You should see `Server is running on 0.0.0.0:8848`.

5. Start the frontend development server (on port **3000**): 
   ```bash
   cd frontend && npm run dev
   ```

6. Open http://localhost:3000 in your browser (Chrome recommended)

7. Click "Start Recording" and grant microphone permission to begin a conversation

**Expected behavior**: after you finish speaking, the backend detects ~500 ms of silence (VAD), transcribes your speech (ASR), streams an LLM reply, and synthesizes it back as audio (TTS) that plays automatically. The on-screen log panel shows per-stage latency (WebSocket RTT, transcription, LLM, TTS). If you start speaking again while the assistant is talking, playback is interrupted.

## Testing

### Provider Testing

Test individual providers and all combinations:

```bash
cd backend

# Test all providers with your API keys
node run-tests.js

# Test specific providers only
npm run test:providers

# Install test dependencies if needed
npm install
```

The test suite will automatically skip providers for which you don't have API keys configured.

### Test Coverage

- ✅ ASR provider functionality (OpenAI Whisper, SenseVoice)
- ✅ LLM provider functionality (OpenAI, OpenRouter GPT-4o, OpenRouter Gemini, ARK Doubao)  
- ✅ TTS provider functionality (CosyVoice2 via Siliconflow)
- ✅ All provider combinations (8 ASR+LLM combinations)
- ✅ Dynamic provider switching
- ✅ Error handling and fallback mechanisms

## Troubleshooting

### Common Issues

1. **Missing API Keys**: Ensure required environment variables are set
2. **FFmpeg Not Found**: Ensure FFmpeg is installed and available in your system PATH
   - Test with: `ffmpeg -version`
   - If not found, refer to the FFmpeg installation instructions above
3. **Network Issues**: Check connectivity to API endpoints
4. **Rate Limiting**: Consider switching providers or implementing retry logic
5. **Geographic Restrictions**: Use OpenRouter for global access
6. **ONNX Runtime Issues**: The backend uses ONNX Runtime for voice activity detection
   - Usually resolved by the `onnxruntime-node` package automatically
   - On some systems, you may need additional system libraries

### Performance Optimization

- **Low Latency**: Use Siliconflow ASR + OpenRouter Gemini
- **High Accuracy**: Use OpenAI ASR + OpenAI LLM
- **China Deployment**: Use Siliconflow ASR + ARK LLM

For provider configuration, see [`backend/config.js.example`](backend/config.js.example) and the provider implementations under [`backend/utils/providers/`](backend/utils/providers).

## License

MIT

---

## 中文

# 实时语音聊天演示

一个具备语音转文本、AI 对话和文本转语音能力的实时语音聊天演示。该应用支持多家 AI 服务提供商，以极低延迟提供流畅的对话体验。

> 这是《深入理解 AI Agent》第 9 章 **实验 9-1「构建传统语音 Agent」**的配套代码。它实现了书中讨论的**级联式**语音流水线（VAD → ASR → LLM → TTS）：前端采集麦克风音频并通过 WebSocket 以流的形式传输；后端运行 Silero VAD，通过约 500 ms 的静音检测语音结束，随后将话语依次交给可插拔的 ASR、LLM 和 TTS 提供商，并将合成音频流式返回播放。

## 功能特性

- 🎤 采用语音活动检测（VAD）的实时语音输入
- 🤖 支持**多家提供商**的 AI 对话
- 🔊 文本转语音合成
- ⚡ 低延迟音频流
- 📊 实时延迟监控与日志记录
- 🎯 基于 WebSocket 的通信
- 🔧 可灵活选择 ASR、LLM 和 TTS 服务提供商

## 支持的 AI 提供商

### ASR（自动语音识别）
- **OpenAI Whisper**：准确率高，语言支持出色
- **SenseVoice**（通过 Siliconflow）：低延迟、经济实惠、自动检测语言

### LLM（大语言模型）
- **OpenAI GPT-4o**：推理能力出色、性能均衡
- **OpenRouter GPT-4o**：无地域限制、统一接口
- **OpenRouter Gemini**：响应迅速，针对实时聊天优化
- **ARK Doubao**：在中国低延迟，针对中文优化

### TTS（文本转语音）
- **CosyVoice2**（通过 Siliconflow）：自然语音合成，提供多种系统音色

## 架构概览

系统采用前后端架构，具备实时音频处理和**可插拔的提供商架构**：

### 前端（Next.js）
- **音频采集**：使用 Web Audio API 采集麦克风输入
- **音频处理**：在客户端处理音频并将其流式传输至后端
- **WebSocket 通信**：向后端发送音频流并接收响应
- **音频播放**：播放后端返回的 TTS 音频响应

### 后端（Node.js）
- **WebSocket 服务器**：处理实时音频流和客户端连接
- **语音活动检测**：在服务端运行 Silero VAD，以高准确率检测语音边界
- **多提供商支持**：灵活集成 ASR、LLM 和 TTS 提供商
- **提供商工厂**：支持动态创建和切换提供商

### 数据流
```text
用户语音 → WebSocket → 后端 VAD → 多提供商 STT → 多提供商 LLM → TTS → 音频响应
```

### 端口

| 组件 | 端口 | 说明 |
|-----------|------|-------|
| 后端（WebSocket 服务器） | **8848** | 由 `backend/config.js` 中的 `LISTEN_PORT` 设置。前端连接到 `ws://localhost:8848`。 |
| 前端（Next.js 开发服务器） | **3000** | 在浏览器中打开 http://localhost:3000。 |

前端从 `WEBSOCKET_PORT` 环境变量获取后端端口（参见 `frontend/.env.example`）。它必须与后端的 `LISTEN_PORT` 一致。

## 前置条件

- Node.js（v16 或更高版本）
- npm 或 yarn
- **FFmpeg**——音频处理和格式转换所必需
- **Google Chrome**（推荐）——实时音频的性能和兼容性最佳
  - 不推荐：Safari、Edge 或其他浏览器，因为 WebAudio API 存在限制
- 支持的提供商所需的 **API key**（参见“配置”一节）

### 安装 FFmpeg

#### macOS（使用 Homebrew）
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows
- 从 https://ffmpeg.org/download.html 下载
- 或使用 Chocolatey：`choco install ffmpeg`
- 确保 `ffmpeg` 位于 PATH 中

## 项目结构

```text
/backend
- server.js: 集成提供商的主 WebSocket 服务器
- config.js: 多提供商配置设置
- utils/
  - providers/
    - asrProviders.js: ASR 提供商实现（OpenAI、Siliconflow）
    - llmProviders.js: LLM 提供商实现（OpenAI、OpenRouter、ARK）
  - vad.js: 语音活动检测实现
  - speechToText.js: 感知提供商的 STT 服务
  - textProcessor.js: 文本预处理工具
- tests/
  - provider-tests.js: 完整的提供商测试
- run-tests.js: 带环境校验的测试运行器
- utils/providers/: 提供商配置（ASR / LLM / TTS）
- package.json: 后端依赖和脚本
```

```text
/frontend
- pages/: Next.js 页面
  - index.tsx: 主应用界面
- components/: 可复用 UI 组件
- public/: 静态资源
  - audioWorklet.js: 音频处理与 VAD 实现
- next.config.js: Next.js 配置
- tailwind.config.js: Tailwind CSS 设置
- package.json: 前端依赖和脚本
```

## 安装

1. 克隆仓库
2. 安装后端依赖：
   ```bash
   cd backend && npm install
   ```
3. 安装前端依赖：
   ```bash
   cd frontend && npm install
   ```
4. 下载 Silero VAD 模型（本仓库已在 `backend/models/silero_vad.onnx` 包含该文件；仅在文件缺失时需要）：
   ```bash
   cd backend/models
   wget https://huggingface.co/deepghs/silero-vad-onnx/resolve/main/silero_vad.onnx
   ```
5. 配置前端的 WebSocket 端口（省略时默认为 8848）：
   ```bash
   cd frontend && cp .env.example .env   # 将 WEBSOCKET_PORT=8848 设为与后端一致
   ```

安装完成后，无需麦克风或浏览器即可检查环境（Node 版本、FFmpeg、VAD 模型和提供商 key）：

```bash
cd backend && npm run check    # 或：node check-setup.js
```

该命令会打印哪些前置条件已经满足，以及所选提供商是否已设置 API key。只有在缺少硬性前置条件（Node < 16、缺少 FFmpeg 或缺少 VAD 模型）时才会以非零状态退出。

## 配置

### 基于提供商的配置

系统现在支持**多家 AI 服务提供商**，以获得最大的灵活性。ASR、LLM 和 TTS 服务可以自由混合搭配不同提供商。

### 1. 设置环境变量

将 API key 设置为环境变量：

```bash
# OpenAI 服务所必需
export OPENAI_API_KEY="your-openai-api-key"

# OpenRouter 服务所必需
export OPENROUTER_API_KEY="your-openrouter-api-key"

# ARK（Doubao）服务所必需
export ARK_API_KEY="your-ark-api-key"

# Siliconflow 服务（ASR 和 TTS）所必需
export SILICONFLOW_API_KEY="your-siliconflow-api-key"

# 留作将来使用
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 2. 选择提供商

1. 本仓库已经提供可直接编辑的 `backend/config.js`。如果该文件缺失（例如全新检出时被忽略），请先复制示例：
   ```bash
   cp backend/config.js.example backend/config.js
   ```

2. 编辑 `backend/config.js`，选择偏好的提供商：
   ```javascript
   const config = {
     // 提供商选择——选择偏好的提供商
     ASR_PROVIDER: 'siliconflow',      // 'openai'（whisper-1）或 'siliconflow'（SenseVoice）
     LLM_PROVIDER: 'openrouter',       // 'openrouter'（gpt-5.6-luna，默认）、'openai'、'openrouter-gemini'、'ark'
     TTS_PROVIDER: 'siliconflow',      // 'siliconflow'（CosyVoice2）

     // API Key（从环境变量加载）
     OPENAI_API_KEY: process.env.OPENAI_API_KEY,
     OPENROUTER_API_KEY: process.env.OPENROUTER_API_KEY,
     ARK_API_KEY: process.env.ARK_API_KEY,
     SILICONFLOW_API_KEY: process.env.SILICONFLOW_API_KEY,

     // ……其他配置选项
   };
   ```

### 3. 推荐的提供商组合

#### 默认 / 推荐（只要有 OpenRouter key 即可在任何地方使用）
```javascript
ASR_PROVIDER: 'siliconflow',      // SenseVoice
LLM_PROVIDER: 'openrouter',       // 通过 OpenRouter 使用 openai/gpt-5.6-luna（避免 gpt-5.6* 组织验证）
TTS_PROVIDER: 'siliconflow',      // CosyVoice2
```

#### 实时性能优先（在中国低延迟）
```javascript
ASR_PROVIDER: 'siliconflow',      // SenseVoice
LLM_PROVIDER: 'ark',              // Doubao（在中国速度快）；也可用 'openrouter' 运行 gpt-5.6-luna
TTS_PROVIDER: 'siliconflow',      // CosyVoice2
```

#### 准确率优先
```javascript
ASR_PROVIDER: 'openai',           // 高准确率的 Whisper
LLM_PROVIDER: 'openrouter',       // 通过 OpenRouter 使用 openai/gpt-5.6-luna
TTS_PROVIDER: 'siliconflow'       // CosyVoice2
```

### 4. API Key 要求

只需配置计划使用的提供商所需的 API key：

| 提供商 | ASR | LLM | TTS | 所需 API Key |
|----------|-----|-----|-----|------------------|
| OpenAI | ✅ Whisper | ✅ gpt-5.6-luna | ❌ | `OPENAI_API_KEY` |
| OpenRouter | ❌ | ✅ gpt-5.6-luna、Gemini | ❌ | `OPENROUTER_API_KEY` |
| ARK（Doubao） | ❌ | ✅ Doubao | ❌ | `ARK_API_KEY` |
| Siliconflow | ✅ SenseVoice | ❌ | ✅ CosyVoice2 | `SILICONFLOW_API_KEY` |

### 5. 配置校验

系统包含完整的校验与测试工具：

```bash
# 测试所有已配置的提供商
npm run test:providers

# 运行带环境校验的完整测试套件
node run-tests.js
```

### 旧版配置支持

系统继续向后兼容先前的硬编码配置格式，但强烈建议使用新的提供商选择机制，以获得更好的灵活性。

## 使用方法

1. **设置 API key**（参见“配置”一节）

2. 在 `backend/config.js` 中**配置偏好的提供商**

3. （可选）**验证配置**：`cd backend && npm run check`

4. 启动后端服务器（WebSocket 服务器使用端口 **8848**）：
   ```bash
   cd backend && npm start
   ```
   此时应看到 `Server is running on 0.0.0.0:8848`。

5. 启动前端开发服务器（使用端口 **3000**）：
   ```bash
   cd frontend && npm run dev
   ```
   此时应看到 `Server is running on 0.0.0.0:3000`。

6. 在浏览器中打开 http://localhost:3000（推荐 Chrome）

7. 点击“Start Recording”并授予麦克风权限，开始对话

**预期行为**：说话结束后，后端检测约 500 ms 的静音（VAD），转录语音（ASR），以流的形式生成 LLM 回复，再将其合成为自动播放的音频（TTS）。屏幕日志面板会显示各阶段延迟（WebSocket RTT、转录、LLM、TTS）。如果在助手说话时再次开口，播放会被打断。

## 测试

### 提供商测试

测试各个提供商和所有组合：

```bash
cd backend

# 使用 API key 测试所有提供商
node run-tests.js

# 仅测试指定提供商
npm run test:providers

# 如有需要，安装测试依赖
npm install
```

测试套件会自动跳过未配置 API key 的提供商。

### 测试覆盖范围

- ✅ ASR 提供商功能（OpenAI Whisper、SenseVoice）
- ✅ LLM 提供商功能（OpenAI、OpenRouter GPT-4o、OpenRouter Gemini、ARK Doubao）
- ✅ TTS 提供商功能（通过 Siliconflow 使用 CosyVoice2）
- ✅ 所有提供商组合（8 种 ASR+LLM 组合）
- ✅ 动态切换提供商
- ✅ 错误处理和回退机制

## 故障排查

### 常见问题

1. **缺少 API Key**：确保已经设置所需的环境变量
2. **找不到 FFmpeg**：确保 FFmpeg 已安装且位于系统 PATH 中
   - 使用 `ffmpeg -version` 测试
   - 如果找不到，请参阅上面的 FFmpeg 安装说明
3. **网络问题**：检查与 API 端点的连通性
4. **速率限制**：考虑切换提供商或实现重试逻辑
5. **地域限制**：使用 OpenRouter 获得全球访问能力
6. **ONNX Runtime 问题**：后端使用 ONNX Runtime 进行语音活动检测
   - 通常会由 `onnxruntime-node` 包自动解决
   - 在某些系统上，可能需要额外的系统库

### 性能优化

- **低延迟**：使用 Siliconflow ASR + OpenRouter Gemini
- **高准确率**：使用 OpenAI ASR + OpenAI LLM
- **中国部署**：使用 Siliconflow ASR + ARK LLM

提供商配置请参见 [`backend/config.js.example`](backend/config.js.example)，实现代码位于 [`backend/utils/providers/`](backend/utils/providers)。

## 许可证

MIT
