# 第 9 章 · 多模态与实时交互

> 从文本扩展到语音、GUI、物理世界：语音三范式、Computer Use、机器人

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter9.md)

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | 实时语音聊天，集成 VAD + ASR（Whisper/SenseVoice）+ LLM（GPT-4o/Gemini/Doubao）+ TTS（Fish Audio），WebSocket 低延迟 |
| 9-2 | [phone-agent](phone-agent/) | 🚧 | 官方 `pine-voice` SDK 的直接/ReAct 双臂已实现，但当前没有获授权且同意参与的 E.164 目的号码；[预检](phone-agent/validation/preflight.json)明确记录未拨号、无 transcript，test double 不作验收 |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | 实际 Qwen2-Audio 递增前缀全量重编码，检测声学事件并测每块延迟；与 600ms VAD + 开源 Whisper 在正常/停顿/噪声三场景对照 |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | 🚧 | Step-Audio R1 customized-vLLM 四卡部署与真实 audio client 已实现，但当前无可用 Step-Audio endpoint 且主机无 CUDA；[阻塞证据](end-to-end-speech/validation/blocker.json)拒绝用替代模型伪装完成 |
| 9-5 | [controllable-tts](controllable-tts/) | 🚧 | 真实 Fish Audio S1 4×3×2=24 条参考音库与三组 A/B/C 媒体已通过结构门；[验收](controllable-tts/validation/acceptance.json)仍明确缺定性听测和“接近真人客服”主张评估 |
| 9-6 | `claude-quickstarts/computer-use-demo/` | 📖 | 正文对应 Anthropic Computer Use Demo，不是整个 quickstarts 集合；容器内 Ubuntu 桌面 + Claude computer-use agent loop |
| 9-7 | `browser-use/` | 📖 | `browser-use/browser-use` 外部 checkout；正文任务使用视觉浏览器 Agent 打开 Google 查询旧金山天气并检查动作轨迹 |
| 9-8 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | 外部复现轨：XLeRobot [官方仓库固定提交](https://github.com/Vector-Wangel/XLeRobot/tree/3d14695e40c9c68229c0aacffca6053c75cd3eb6)的键盘/Xbox/Joy-Con/VR 遥操作；当前仅通过源码与非致动预检，尚无真机四模式及取放擦任务证据 |
| 9-9 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | 外部复现轨：[XLeRobot 固定提交](https://github.com/Vector-Wangel/XLeRobot/tree/3d14695e40c9c68229c0aacffca6053c75cd3eb6) + [RoboCrew](https://github.com/Grigorij-Dudnik/RoboCrew)，严格使用 `gemini-robotics-er-1.5-preview`、角度标注和前进/左转/右转三工具；当前无模型 API 或真机导航证据 |
| 9-10 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | 外部复现轨：[`lerobot-sim2real` 固定提交](https://github.com/StoneT2000/lerobot-sim2real/tree/87d6c1d969f6e0ca4dc5697940804e231118a63a)的五阶段 RGB→PPO→SO-100 流程；3–4 阶段可纯 GPU，固定版第 1 阶段会连接并 reset 真机；本机缺 ManiSkill/NVIDIA，亦无授权真机证据 |

## 实验 9-6 / 9-7 外部复现锚点

SHA 来自 2026-07-30 当前工作区 checkout 的 `origin` 与 `HEAD`。这里只核验了源码、依赖锁状态和入口命令；**没有启动容器、浏览器或真实模型调用**。

| 实验 | 权威上游 → 本地路径 | 固定提交 | 锁与入口 |
| :--: | --- | --- | --- |
| 9-6 | [`anthropics/claude-quickstarts`](https://github.com/anthropics/claude-quickstarts) → `chapter9/claude-quickstarts`；具体项目 `computer-use-demo/` | `9bcc95e316e5ef6542b4c9d0469f4078829eead5` | 从该目录的 `Dockerfile` 本地构建；固定源码中的 Dockerfile SHA-256 为 `3aa1f36a491f8f88d81a04c6a89b4cc9f9acd20ad946304c13419736da7c0ead`，但构建输入仍有可变项 |
| 9-7 | [`browser-use/browser-use`](https://github.com/browser-use/browser-use) → `chapter9/browser-use` | `ec9277c5001f2cb78ee419c927775a3cfc227ff8` | checkout 包版本 `0.9.5`；视觉入口为 `examples/ui/command_line.py`（`use_vision=True`、`max_actions_per_step=1`、OpenAI 默认模型 `gpt-4.1`）。该提交**没有跟踪 `uv.lock`，且 `.gitignore` 明确忽略它** |

从仓库根目录复现 9-6 的源码版本并本地构建：

```bash
git clone https://github.com/anthropics/claude-quickstarts.git chapter9/claude-quickstarts
git -C chapter9/claude-quickstarts checkout --detach 9bcc95e316e5ef6542b4c9d0469f4078829eead5
test "$(git -C chapter9/claude-quickstarts rev-parse HEAD)" = "9bcc95e316e5ef6542b4c9d0469f4078829eead5"
cd chapter9/claude-quickstarts/computer-use-demo

RECEIPT_DIR="$HOME/ai-agent-book-receipts/9-6-9bcc95e"
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

从仓库根目录复现 9-7：

```bash
git clone https://github.com/browser-use/browser-use.git chapter9/browser-use
git -C chapter9/browser-use checkout --detach ec9277c5001f2cb78ee419c927775a3cfc227ff8
test "$(git -C chapter9/browser-use rev-parse HEAD)" = "ec9277c5001f2cb78ee419c927775a3cfc227ff8"
cd chapter9/browser-use

RECEIPT_DIR="$HOME/ai-agent-book-receipts/9-7-ec9277c"
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

export OPENAI_API_KEY='replace-with-your-api-key'
export BROWSER_USE_LOGGING_LEVEL=debug
uv run python examples/ui/command_line.py --provider openai --query "Open Google, search for San Francisco weather today, and report the temperature and conditions" 2>&1 | tee "$RECEIPT_DIR/action-log.txt"

# 将 debug 日志中实际选择的 executable_path 填到这里；不能只记录“安装过 Chromium”。
BROWSER_PATH='/absolute/path/reported-by-LocalBrowserWatchdog'
test -x "$BROWSER_PATH"
printf '%s\n' "$BROWSER_PATH" | tee "$RECEIPT_DIR/chromium-path.txt"
"$BROWSER_PATH" --version | tee "$RECEIPT_DIR/chromium-version.txt"
shasum -a 256 "$BROWSER_PATH" | tee "$RECEIPT_DIR/chromium-sha256.txt"
```

该入口固定使用 `gpt-4.1`、`use_vision=True`、每步最多一个动作并最多运行 25 步，但没有“每步自动落盘带 SoM 标注截图”的命令行开关。正文要求的截图、动作序列、最终答案和完成状态必须在会话期间另行保存，不能仅凭最终天气文本宣称已复现完整观察链。

这里保存的是**本次本地生成的** `uv.lock`，不是上游锁；初次 `uv lock` 的解析仍受当时包索引影响。`browser-use install` 还会在 Linux 上调用可变的 `uvx playwright install chromium --with-deps --no-shell`，在 macOS/Windows 上调用 `uvx playwright install chromium --no-shell`，因此 Playwright/Chromium 不受项目 lock 约束。固定入口的 `BrowserSession()` 又可能优先选择已有的系统 Chrome，而不是刚下载的 Playwright Chromium；这正是必须记录实际 executable path、版本和二进制哈希的原因。只有把生成的 lock、安装器版本、浏览器二进制和轨迹回执一起归档，才能准确描述当次运行，仍不能把上游 9-7 环境称为位级固定。

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **进行中** | 已有实现，但正文要求的真实运行、授权参与者、硬件或验收证据尚未完整 |
