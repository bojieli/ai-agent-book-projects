# 第 6 章 · 交互：观察与动作空间的扩展

> 从模态与时序两个维度扩展 Agent 的观察与动作空间：异步与事件驱动、语音交互、Computer Use 和机器人操作

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter6.md)

## 如何阅读实验

正文 skeleton 统一了“持续观察 → 受限动作 → 新观察 → 验收/抢占”的闭环；完整媒体、浏览器和机器人代码分层阅读：

- **Starter**：从 [live-audio](live-audio/) 的级联入口理解 VAD → ASR → LLM → TTS；
- **Builder**：再读 [computer-use-open-model](computer-use-open-model/) 的截图/动作/验证循环，以及 [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) 的五个有边界技能；
- **Maintainer**：最后检查取消、不可逆动作门禁、真实观察证据、硬件急停和 sim-to-real 评估。首次可跳过前端样式、模型下载和设备驱动。

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 6-1 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | FastAPI 事件驱动 Agent，原生异步集成前三组 MCP 工具，通过 HTTP API 接收 Web/IM/GitHub/定时器事件 |
| 6-2 | [async-agent](async-agent/) | ✅ | asyncio 单线程事件驱动框架 Flux：事件队列按紧急度分派、异步工具并行、运行中打断、长任务取消与状态查询 |
| 6-3 | [live-audio](live-audio/) | ✅ | [真实单轮证据](live-audio/backend/validation/real_pipeline_20260729_localwhisper_ark_fish/evidence.json)完成麦克风媒体 → Silero VAD → 本地 Whisper → ARK 流式 LLM → Fish S1；5 个媒体/模型 hash 当前均匹配，但证据本身没有顶层 hash manifest，且不代表并发或生产负载基准 |
| 附加 | [phone-agent](phone-agent/) | ✅ | 使用稳定的非编号项目标识；[完整音频 canonical run](phone-agent/validation/runs/phone-agent-webrtc-audio-20260731-v1/manifest.json)跑通直接/ReAct 两组，并保留完整的 WebRTC、ASR、LLM 与 TTS 证据 |
| 6-4 | [streaming-speech](streaming-speech/) | ✅ | [canonical 本地验收](streaming-speech/validation/runs/exp6-4-qwen2audio-whisper-provenance-20260730-v3/manifest.json)运行 Qwen2-Audio 递增前缀与 600ms VAD + Whisper：8/8 执行/溯源门禁通过，但预期行为只复现 2/6，实测前缀 8.4–11.3s，不能声称真流式低延迟 |
| 6-5 | [end-to-end-speech](end-to-end-speech/) | ✅ | [真实本地运行](end-to-end-speech/validation/runs/exp6-5-minicpmo45-20260801-v1/evidence.json)在单张 RTX PRO 6000 上执行固定 revision 的 MiniCPM-o 4.5：端到端与自级联均为 3/4，但语义/副语言失败互补；真实 24kHz 语音输出及 [11/11 验收](end-to-end-speech/validation/runs/exp6-5-minicpmo45-20260801-v1/acceptance.json)已保留 |
| 6-6 | [controllable-tts](controllable-tts/) | ✅ | 真实 Fish Audio S1 4×3×2=24 条参考音库与 A/B/C 媒体齐全；三次位置平衡的真实 Voxtral 音频盲评中 C 组最高且真人客服感 4.67/5，但 B>A 未复现；[验收](controllable-tts/validation/acceptance.json)将完成状态与负结果分开报告 |
| 6-7 | [Anthropic 原生 Computer Use 记录](claude-computer-use-native/) + `claude-quickstarts/computer-use-demo/` | ✅ | [正式运行](claude-computer-use-native/validation/runs/exp6-7-anthropic-native-20260803-v2/acceptance.json)从固定源码本地构建镜像，用 `claude-sonnet-4-5-20250929` 完成 16 次真实响应与 15 个原生 `computer` 动作；Google reCAPTCHA 未交互，转向可见 Open-Meteo JSON 后回答 70.2°F、晴朗，全部确定性门禁通过 |
| 6-8 | [computer-use-open-model](computer-use-open-model/) + `browser-use/` | ✅ | [正式开放模型运行](computer-use-open-model/validation/latest.json)使用 `qwen/qwen3-vl-32b-instruct`：Google CAPTCHA 后转 weather.com，16 步完成；16/16 API 响应模型一致、15 张截图、只读动作和答案 grounding 全部通过确定性验收 |
| 6-9 | [xlerobot-teleoperation](xlerobot-teleoperation/) | ✅ | 真机遥操作 XLeRobot 整理桌面：把红色杯子放进托盘、把黄色废纸放进垃圾盒，最后重新观察并确认状态 |
| 6-10 | [xlerobot-teleoperation](xlerobot-teleoperation/) | ✅ | 在模拟器中测量同一桌面任务的理想控制上限，不代表真机已经运行 |
| 6-11 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | ✅ | 使用 Gemini Robotics-ER 1.5 自主驱动真实 XLeRobot 完成同一整理桌面任务 |
| 6-12 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | ✅ | 在模拟器中比较开环、逐步检查和预测式闭环三种同任务策略 |
| 6-13 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | ✅ | 对同一桌面任务进行 RGB 跨环境测试，检查视觉策略对背景、外观、光照和噪声变化的适应性 |

## 实验 6-7 / 6-8 的供应商可移植路径

6-7 的 Anthropic Demo 是参考实现；6-8 的
[开放模型 companion](computer-use-open-model/)把 browser-use 的视觉 Agent 接到
OpenAI-compatible Chat Completions：默认示例通过 OpenRouter 调用开放权重
`qwen/qwen3-vl-32b-instruct`，也支持读者自己的 vLLM/SGLang 或其他兼容托管端点。
“开放模型”指权重/许可证开放，API 网关本身仍可能是商业服务；实验回执必须分别记录
requested model 与提供商实际返回的 model ID。

```bash
cd chapter6/computer-use-open-model
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium

export OPENROUTER_API_KEY='replace-with-your-key'
python main.py --dry-run
python main.py \
  --task "Open Google, search for San Francisco weather today, and report the temperature and conditions. Do not sign in or change any external data." \
  --max-steps 25 \
  --record-video
```

自托管时改设 `OPEN_MODEL_API_KEY=local`、`OPEN_MODEL_BASE_URL` 与
`OPEN_MODEL_MODEL` 即可。端点必须支持图片输入和结构化 JSON 动作；不支持原生
`json_schema` 时可设 `OPEN_MODEL_SCHEMA_MODE=prompt`，但应把这种兼容模式单列为
不同实验配置。不同模型的结果不能合并成 Anthropic 复现结果。

## 实验 6-7 至 6-13 外部复现锚点

6-7/6-8 的上游 SHA 来自 2026-07-30 工作区 checkout 的 `origin` 与 `HEAD`。6-8 的[开放模型正式运行](computer-use-open-model/validation/latest.json)已经用真实 Qwen3-VL API 与 Chromium 完成 browser-use 路径；6-7 则用 Anthropic 凭据从固定 Dockerfile 本地构建镜像，[运行证据](claude-computer-use-native/validation/runs/exp6-7-anthropic-native-20260803-v2/trajectory.json)记录了 15/25 个动作内绕开 Google reCAPTCHA、读取可见 Open-Meteo 数据并以 `end_turn` 完成任务的过程。早期 401 与两个未通过任务门禁的真实尝试仍作为失败证据保留，不计入正式结果。6-10、6-12 与 6-13 的**本地 GPU 自包含验收已经完成**；6-9、6-11 所需的真实硬件运行仍需单独的设备、授权和安全证据。

| 实验 | 权威上游 → 本地路径 | 固定提交 | 锁与入口 |
| :--: | --- | --- | --- |
| 6-7 | [`anthropics/claude-quickstarts`](https://github.com/anthropics/claude-quickstarts) → `chapter6/claude-quickstarts`；具体项目 `computer-use-demo/` | `9bcc95e316e5ef6542b4c9d0469f4078829eead5` | 从该目录的 `Dockerfile` 本地构建；固定源码中的 Dockerfile SHA-256 为 `3aa1f36a491f8f88d81a04c6a89b4cc9f9acd20ad946304c13419736da7c0ead`，但构建输入仍有可变项 |
| 6-8 | [`browser-use/browser-use`](https://github.com/browser-use/browser-use) → `chapter6/browser-use`；本书可移植入口 `chapter6/computer-use-open-model/main.py` | `ec9277c5001f2cb78ee419c927775a3cfc227ff8` | checkout 包版本 `0.9.5`；本书入口固定 `use_vision=True`、`max_actions_per_step=1`，默认请求开放权重 Qwen3-VL 32B，并接受任意合格 OpenAI-compatible base URL。该上游提交**没有跟踪 `uv.lock`，且 `.gitignore` 明确忽略它** |
| 6-9 | [`Vector-Wangel/XLeRobot`](https://github.com/Vector-Wangel/XLeRobot) → `chapter6/XLeRobot` | `3d14695e40c9c68229c0aacffca6053c75cd3eb6` | `software/examples/{4_xlerobot_teleop_keyboard,5_xlerobot_teleop_xbox,7_xlerobot_teleop_joycon,8_xlerobot_teleop_vr}.py`；精确 blob 与安全门禁见[复现 companion](xlerobot-teleoperation/) |
| 6-10 | 同一 [`Vector-Wangel/XLeRobot`](https://github.com/Vector-Wangel/XLeRobot) → `chapter6/XLeRobot`；[`Grigorij-Dudnik/RoboCrew`](https://github.com/Grigorij-Dudnik/RoboCrew) → `chapter6/RoboCrew` | XLeRobot：`3d14695e40c9c68229c0aacffca6053c75cd3eb6`；RoboCrew v0.3.1：`c749148f29bd14e61347f9fc3530c343fff0d994` | XLeRobot 的 `docs/en/source/software/getting_started/LLM_agent.md` + RoboCrew planner；五个桌面操作工具、动作条件世界模型与证据门禁见[复现 companion](gemini-xlerobot-navigation/) |
| 6-11 | [`Vector-Wangel/XLeRobot`](https://github.com/Vector-Wangel/XLeRobot) → `chapter6/XLeRobot`；[`Grigorij-Dudnik/RoboCrew`](https://github.com/Grigorij-Dudnik/RoboCrew) → `chapter6/RoboCrew` | XLeRobot：`3d14695e40c9c68229c0aacffca6053c75cd3eb6`；RoboCrew v0.3.1：`c749148f29bd14e61347f9fc3530c343fff0d994` | Gemini Robotics-ER 1.5 自主控制真机的同一整理桌面任务；工具契约与安全边界见[复现 companion](gemini-xlerobot-navigation/) |
| 6-12 | `gemini-xlerobot-navigation` 的桌面模拟器 | — | 同一任务的开环、逐步检查和预测式闭环对照；只使用非致动模拟执行器 |
| 6-13 | [`StoneT2000/lerobot-sim2real`](https://github.com/StoneT2000/lerobot-sim2real) → `chapter6/lerobot-sim2real` | `87d6c1d969f6e0ca4dc5697940804e231118a63a` | 同一整理桌面任务的 RGB 跨环境测试；阶段与安全边界见[复现 companion](rgb-sim2real-grasping/) |

6-9 至 6-13 的固定源码获取命令如下；XLeRobot checkout 由 6-9 至 6-12 共用：

```bash
git clone https://github.com/Vector-Wangel/XLeRobot.git chapter6/XLeRobot
git -C chapter6/XLeRobot fetch origin 3d14695e40c9c68229c0aacffca6053c75cd3eb6
git -C chapter6/XLeRobot checkout --detach 3d14695e40c9c68229c0aacffca6053c75cd3eb6
test "$(git -C chapter6/XLeRobot rev-parse HEAD)" = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"

git clone https://github.com/Grigorij-Dudnik/RoboCrew.git chapter6/RoboCrew
git -C chapter6/RoboCrew fetch origin c749148f29bd14e61347f9fc3530c343fff0d994
git -C chapter6/RoboCrew checkout --detach c749148f29bd14e61347f9fc3530c343fff0d994
test "$(git -C chapter6/RoboCrew rev-parse HEAD)" = "c749148f29bd14e61347f9fc3530c343fff0d994"

git clone https://github.com/StoneT2000/lerobot-sim2real.git chapter6/lerobot-sim2real
git -C chapter6/lerobot-sim2real fetch origin 87d6c1d969f6e0ca4dc5697940804e231118a63a
git -C chapter6/lerobot-sim2real checkout --detach 87d6c1d969f6e0ca4dc5697940804e231118a63a
test "$(git -C chapter6/lerobot-sim2real rev-parse HEAD)" = "87d6c1d969f6e0ca4dc5697940804e231118a63a"
```

这些命令只建立真实硬件扩展所需的固定源码起点。XLeRobot/RoboCrew/Sim2Real 的 companion 中保存过源码审计或非致动预检，但当前工作区没有这三个源码 checkout；历史预检不等于真机执行。本地 GPU 桌面模拟和 RGB 训练则由各实验目录中的自包含脚本完成，并有独立的证据门禁。

从仓库根目录复现实验 6-7 的源码版本并本地构建：

```bash
git clone https://github.com/anthropics/claude-quickstarts.git chapter6/claude-quickstarts
git -C chapter6/claude-quickstarts checkout --detach 9bcc95e316e5ef6542b4c9d0469f4078829eead5
test "$(git -C chapter6/claude-quickstarts rev-parse HEAD)" = "9bcc95e316e5ef6542b4c9d0469f4078829eead5"
cd chapter6/claude-quickstarts/computer-use-demo

RECEIPT_DIR="$HOME/ai-agent-book-receipts/6-7-9bcc95e"
mkdir -p "$RECEIPT_DIR"
git rev-parse HEAD | tee "$RECEIPT_DIR/source-sha.txt"
shasum -a 256 Dockerfile | tee "$RECEIPT_DIR/dockerfile-sha256.txt"
docker version | tee "$RECEIPT_DIR/docker-version.txt"

# 先解析并保存这次构建实际采用的 base-image digest，再禁止 build 重新拉取标签。
docker pull ubuntu:22.04 | tee "$RECEIPT_DIR/base-image-pull.txt"
docker image inspect ubuntu:22.04 --format '{{json .RepoDigests}}' | tee "$RECEIPT_DIR/base-image-repodigests.json"
docker build --pull=false --iidfile "$RECEIPT_DIR/built-image-id.txt" . -t ai-agent-book-computer-use:9bcc95e
docker image inspect ai-agent-book-computer-use:9bcc95e --format '{{.Id}}' | tee "$RECEIPT_DIR/built-image-id-inspect.txt"

export ANTHROPIC_API_KEY='replace-with-your-api-key'
docker run --rm -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" -p 5900:5900 -p 8501:8501 -p 6080:6080 -p 8080:8080 -it ai-agent-book-computer-use:9bcc95e
```

打开 `http://localhost:8080` 后再提交正文任务。除上述构建回执外，还应在同一 `RECEIPT_DIR` 保存原样任务文本、实际模型 ID、按顺序的 computer-use 动作、每步截图/观察、最终回答、停止原因和完成/失败状态；容器能启动不等于实验完成。不要用远端可变标签 `computer-use-demo-latest` 的镜像 ID 代替本地构建回执。

即使保存了当次 `ubuntu:22.04` digest，该 Dockerfile 仍执行在线 `apt`/PPA 安装，并从未固定 commit 的默认分支克隆 `pyenv`；系统包仓库和若干下载输入也没有内容锁。因此上述回执只能重建“本次究竟运行了什么”的审计链，不能把该镜像声称为位级可重复。

从仓库根目录复现实验 6-8：

```bash
git clone https://github.com/browser-use/browser-use.git chapter6/browser-use
git -C chapter6/browser-use checkout --detach ec9277c5001f2cb78ee419c927775a3cfc227ff8
test "$(git -C chapter6/browser-use rev-parse HEAD)" = "ec9277c5001f2cb78ee419c927775a3cfc227ff8"
cd chapter6/browser-use

RECEIPT_DIR="$HOME/ai-agent-book-receipts/6-8-ec9277c"
mkdir -p "$RECEIPT_DIR"
git rev-parse HEAD | tee "$RECEIPT_DIR/source-sha.txt"
uv --version | tee "$RECEIPT_DIR/uv-version.txt"

# 上游没有提交 uv.lock：先为本次解析生成并保存 lock，之后才可使用 --locked。
uv lock
cp uv.lock "$RECEIPT_DIR/uv.lock"
shasum -a 256 uv.lock | tee "$RECEIPT_DIR/uv-lock-sha256.txt"
uv sync --locked
uv run browser-use --version | tee "$RECEIPT_DIR/browser-use-version.txt"
uvx playwright --version | tee "$RECEIPT_DIR/playwright-version-before-install.txt"
uv run browser-use install 2>&1 | tee "$RECEIPT_DIR/browser-install.txt"
uvx playwright install --list | tee "$RECEIPT_DIR/playwright-browsers.txt"

export OPENROUTER_API_KEY='replace-with-your-api-key'
export BROWSER_USE_LOGGING_LEVEL=debug
uv run python ../computer-use-open-model/main.py \
  --task "Open Google, search for San Francisco weather today, and report the temperature and conditions. Do not sign in or change any external data." \
  --output-dir "$RECEIPT_DIR/open-model-run" \
  --max-steps 25 \
  --record-video 2>&1 | tee "$RECEIPT_DIR/action-log.txt"

# 将 debug 日志中实际选择的 executable_path 填到这里；不能只记录“安装过 Chromium”。
BROWSER_PATH='/absolute/path/reported-by-LocalBrowserWatchdog'
test -x "$BROWSER_PATH"
printf '%s\n' "$BROWSER_PATH" | tee "$RECEIPT_DIR/chromium-path.txt"
"$BROWSER_PATH" --version | tee "$RECEIPT_DIR/chromium-version.txt"
shasum -a 256 "$BROWSER_PATH" | tee "$RECEIPT_DIR/chromium-sha256.txt"
```

本书入口固定 `use_vision=True`、每步最多一个动作并最多运行 25 步；开放模型默认值为 `qwen/qwen3-vl-32b-instruct`，并非 `gpt-4.1`。runner 自动保存提供商响应、逐步截图、动作序列、最终答案、失败状态和 artifact hash；仍需独立核对天气答案与轨迹，不能仅凭模型自己的 `done` 宣称完成。若改用上游 `examples/ui/command_line.py`，它仍默认 `gpt-4.1` 且不会按本书格式自动落盘完整证据。

这里保存的是**本次本地生成的** `uv.lock`，不是上游锁；初次 `uv lock` 的解析仍受当时包索引影响。`browser-use install` 还会在 Linux 上调用可变的 `uvx playwright install chromium --with-deps --no-shell`，在 macOS/Windows 上调用 `uvx playwright install chromium --no-shell`，因此 Playwright/Chromium 不受项目 lock 约束。固定入口的 `BrowserSession()` 又可能优先选择已有的系统 Chrome，而不是刚下载的 Playwright Chromium；这正是必须记录实际 executable path、版本和二进制哈希的原因。只有把生成的 lock、安装器版本、浏览器二进制和轨迹回执一起归档，才能准确描述当次运行，仍不能把上游 6-8 环境称为位级固定。

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **进行中** | 已有实现，但正文要求的真实运行、授权参与者、硬件或验收证据尚未完整 |
