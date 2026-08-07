# 深入理解 AI Agent：设计原理与工程实践

[![PDF](https://img.shields.io/badge/PDF-%E4%B8%8B%E8%BD%BD-success.svg)](#-电子书) [![在线阅读](https://img.shields.io/badge/🌐_在线阅读-bojieli.github.io-success?style=flat-square)](https://bojieli.github.io/ai-agent-book/) [![Stars](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE) [![Languages](https://img.shields.io/badge/翻译-13%20种%20语言-informational.svg)](#-电子书)
[![Trending GitHub Project of the Day](https://img.shields.io/badge/GitHub%20Trending-Project%20of%20the%20Day-orange?logo=github)](https://github.com/trending)

**中文** ← 当前 · [English](docs/en/README.md) · [Español](docs/es/README.md) · [Bahasa Indonesia](docs/id/README.md) · [العربية](docs/ar/README.md) · [繁體中文（台灣）](docs/zh-TW/README.md) · [Русский](docs/ru/README.md) · [Tiếng Việt](docs/vi/README.md) · [தமிழ்](docs/ta/README.md) · [日本語](docs/ja/README.md) · [Türkçe](docs/tr/README.md) · [한국어](docs/ko/README.md) · [Magyar](docs/hu/README.md)

> 📥 **[下载 PDF / EPUB](#-电子书)**（推荐）— 推荐使用 PDF / EPUB 离线阅读，排版最佳；也可[在线阅读](https://bojieli.github.io/ai-agent-book/)（支持多语言切换、章节折叠、全文搜索，每次推送自动更新）。

**Agent = LLM + 上下文 + 工具**——本书围绕这个核心公式，用 10 章把 AI Agent 从原理讲到工程实战。全书正文、配图、**95 个配套实验**全部开源，欢迎亲手把实验跑一遍。

| 📚 **10 章** 正文，从基础到生产 | 📂 **95 个** 配套实验（含本地项目与外部复现轨道） | 🌐 **13 种** 语言：中 / 英 / 西 / 印尼 / 阿 / 繁體中文（台灣） / 俄 / 泰米尔 / 越 / 日 / 土耳其 / 韩 / 匈牙利 |
| :---: | :---: | :---: |

## 📖 电子书

> 📥 **离线下载**（推荐，全书正文，开源免费）。以下链接始终指向 main 分支的最新构建；固定版本见 [Releases](https://github.com/bojieli/ai-agent-book/releases)：
> - **中文（原版）**：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.epub)
> - **英文**（社区翻译，by [@nsdevaraj](https://github.com/nsdevaraj)、[@whanyu1212](https://github.com/whanyu1212)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.epub)
> - **西班牙语**（社区翻译，by [@santhreal](https://github.com/santhreal)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.epub)
> - **印度尼西亚语**（社区翻译，by [@jojixyz666](https://github.com/jojixyz666)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-id.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-id.epub)
> - **繁體中文（台灣）**（社区翻译，by [@tigercosmos](https://github.com/tigercosmos)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.epub)
> - **俄语**（社区翻译，by [@ui99ru](https://github.com/ui99ru)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.epub)
> - **泰米尔语**（社区翻译，by [@nsdevaraj](https://github.com/nsdevaraj)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.epub)
> - **越南语**（社区翻译，by [@toanalien](https://github.com/toanalien)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.epub)
> - **日语**（社区翻译，by [@eltociear](https://github.com/eltociear)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.epub)
> - **阿拉伯语**（社区翻译，by [@TheSyBuilder](https://github.com/TheSyBuilder)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.epub)
> - **土耳其语**（社区翻译，by [@memisemre](https://github.com/memisemre)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.epub)
> - **韩语**（社区翻译，by [@JeongJaeSoon](https://github.com/JeongJaeSoon)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.epub)
> - **匈牙利语（Magyar）**（社区翻译，by [@barmivalami0-ux](https://github.com/barmivalami0-ux)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-hu.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-hu.epub)
>
> 🌐 也可[在线阅读](https://bojieli.github.io/ai-agent-book/) — 支持多语言切换、章节折叠、全文搜索、配套实验直达，每次 main 分支推送后自动重新构建。

中文正文源码位于 [`book/`](book/)；英文/西班牙语/印度尼西亚语/阿拉伯语/繁體中文（台灣）/俄语/泰米尔/越南语/日语/土耳其语/韩语/匈牙利语版本为社区贡献（可能滞后于中文原版），分别位于 [`book-en/`](book-en/)、[`book-es/`](book-es/)、[`book-id/`](book-id/)、[`book-ar/`](book-ar/)、[`book-zhtw/`](book-zhtw/)、[`book-ru/`](book-ru/)、[`book-ta/`](book-ta/)、[`book-vi/`](book-vi/)、[`book-ja/`](book-ja/)、[`book-tr/`](book-tr/)、[`book-ko/`](book-ko/)、[`book-hu/`](book-hu/)。

<details>
<summary><b>🔧 想自行编译 PDF / EPUB？</b>（PDF 需 pandoc / xelatex / ElegantBook）</summary>

- **EPUB**：使用统一的构建脚本，详情请参阅 [EPUB 构建说明](EPUB.md)
- **正文源码**：`book/introduction.md`（引言）、`book/chapter1.md` ~ `book/chapter10.md`（第一至第十章）、`book/afterword.md`（后记）
- **编译**：安装 pandoc、xelatex、ElegantBook 文档类与相关字体后，运行

  ```bash
  cd book && bash build_pdf.sh
  ```

  图表以 SVG 文件存于 `book/images/`，编译时直接使用；排版细节见 `book/preamble.tex` 与 `book/*.lua`。

</details>

## 📑 内容速览（第 1–10 章）

全书围绕核心公式 **Agent = LLM + 上下文 + 工具** 展开，十章层层递进：

| 章 | 主题 | 一句话核心 | 正文 | 代码 |
| :--: | --- | --- | :--: | :--: |
| 1 | 🚀 **Agent 基础知识** | **Agent = LLM + 上下文 + 工具**；Harness 工程才是竞争力 | [读](book/chapter1.md) | [4](chapter1/README.md) |
| 2 | 🎯 **上下文工程** | 上下文决定能力上限：KV Cache、提示工程、Agent Skills、上下文压缩 | [读](book/chapter2.md) | [9](chapter2/README.md) |
| 3 | 📚 **用户记忆和知识库** | 跨会话记住用户、接入外部知识：用户记忆、RAG、结构化索引、知识图谱 | [读](book/chapter3.md) | [13](chapter3/README.md) |
| 4 | 🛠️ **工具** | 工具是 Agent 的双手：MCP 协议、感知/执行/协作三类工具、事件驱动异步 Agent、主动工具发现 | [读](book/chapter4.md) | [7](chapter4/README.md) |
| 5 | 💻 **Coding Agent 与代码生成** | 代码是「能创造新工具的工具」，生产级 Coding Agent 全景 | [读](book/chapter5.md) | [13](chapter5/README.md) |
| 6 | 🎯 **Agent 的评估** | 把表现变成可比较信号：评估环境、指标、统计显著性、评估驱动选型 | [读](book/chapter6.md) | [13](chapter6/README.md) |
| 7 | 🧠 **模型后训练** | 预训练/SFT/RL 三阶段：何时选 SFT、何时选 RL，工具调用内化、样本效率 | [读](book/chapter7.md) | [16](chapter7/README.md) |
| 8 | 🔄 **Agent 的持续进化** | 从运行轨迹获得学习信号，更新知识、指令、程序与参数 | [读](book/chapter8.md) | [9](chapter8/README.md) |
| 9 | 🎙️ **多模态与实时交互** | 从文本扩展到语音、GUI、物理世界：语音三范式、Computer Use、机器人 | [读](book/chapter9.md) | [10](chapter9/README.md) |
| 10 | 🤝 **多 Agent 协作** | 群体智能高于个体：协作框架、上下文共享/隔离、涌现的「Agent 社会」 | [读](book/chapter10.md) | [8](chapter10/README.md) |

> 💡 **读** = 在 GitHub 网页直接读章节正文（markdown）；**N** = 该章配套项目数，点击查看代码。项目类型说明（✅ 可运行 / 📖 复现 / 🚧 设计）见各章 README。
>
> 📚 如何高效阅读本书？详见 **[学习建议](docs/zh-CN/LEARNING.md)**（核心理念、学习路径、难度分级、实践建议）。

## 💻 运行配套实验

项目统一支持 **Python 3.10+**。请在仓库根目录按章节安装依赖；将 `ch1` 替换为 `ch2` ~ `ch10` 即可安装对应章节：

```bash
# 推荐：使用提交到仓库的 uv.lock，获得可复现的章节环境
uv sync --locked --extra ch1

# 未安装 uv 时：使用 pip 从 pyproject.toml 重新解析
python -m pip install -e ".[ch1]"
```

运行会调用模型的实验前，请按该实验 README 配置凭据：支持根目录配置的实验可复制 `.env.example` 为 `.env` 并填入至少一个提供商 Key；有些实验要求在自身目录放 `.env` 或直接导出环境变量。只有在实验 README 或 CLI 明确列出 `ollama` 时，才可启动本地 Ollama 并添加 `--provider ollama`。

安装后可从仓库根目录运行实验，例如：

```bash
uv run python chapter1/context/main.py
# 使用 pip 安装时也可直接运行：python chapter1/context/main.py
```

- `uv` 安装方法见 [官方文档](https://docs.astral.sh/uv/getting-started/installation/)；`pip` 仍受支持，但不会使用锁文件。
- 各实验现有的 `requirements.txt` 在迁移期间继续有效，适合只运行单个项目或需要特殊版本约束的情况。
- `all` 是不含本地训练栈的 CPU 友好组合，并不代表每个实验；`uv sync` 每次都会精确同步当前选择，使用特殊 extra 时请合并到同一条命令，例如 `uv sync --locked --extra ch2 --extra vllm` 或 `uv sync --locked --extra ch7 --extra unsloth`；pip 对应为 `python -m pip install -e ".[ch2,vllm]"`。
- 浏览器、CUDA、FFmpeg、Ollama、Playwright 浏览器及外部仓库等系统依赖，请继续参考各实验 README。部分浏览器和记忆实验需要 Python 3.11+，第 8 章部分内置第三方组件需要 Python 3.12+。

## 🔑 API 密钥

建议申请下面几个平台的 API Key 方便学习。模型选型可参考 [这篇指南](https://01.me/2025/07/llm-api-setup/)。

| 平台 | 链接 | 特色 | 访问节点 |
| --- | --- | --- | --- |
| **Kimi**（月之暗面） | <https://platform.moonshot.cn/> | Kimi 系列，Coding、Agent 能力强 | 中国大陆 |
| **智谱 GLM** | <https://open.bigmodel.cn/> | GLM-5.2 等，Coding、Agent 能力强 | 中国大陆 |
| **Siliconflow** | <https://siliconflow.cn/> | 各种开源模型（DeepSeek、Qwen 等），中国大陆访问速度快 | 中国大陆 |
| **DeepSeek** | <https://platform.deepseek.com/> | DeepSeek 官方 API | 全球 + 中国大陆 |
| **Krill AI** | [www.krill-ai.net](https://www.krill-ai.net/register?invite=Q8D3L35725) | 一站式访问全球及国内主流模型（OpenAI、Claude、Gemini、Grok、Kimi、GLM、DeepSeek、Qwen、Minimax） | 全球 + 中国大陆 |
| **OpenRouter** | <https://openrouter.ai/> | 一站式访问全球及国内主流模型（GPT、Claude、Gemini、Kimi、GLM、DeepSeek、Qwen 等） | 全球 |

## 💎 赞助商

感谢 **Krill AI** 赞助本项目！Krill 提供 GPT / Claude / Gemini / 多款国产模型的官方稳定极速 API 中转服务，支持企业级定制、报销开票、7×16h 专属技术支持，更有独家适配的 WebSocket 连接方式，畅享极速首字速度。

Krill 为本书读者提供特别优惠：使用[此链接](https://www.krill-ai.net/register?invite=Q8D3L35725)注册并在充值时填写优惠码「ai-agent-book」，首次购买 Codex 套餐可享 77 折优惠！

> 🧪 配套实验的执行状态、证据与未完成门禁单独记录在 [`docs/EXPERIMENT_STATUS.md`](docs/EXPERIMENT_STATUS.md)；克隆或安装源码不代表实验完成。

## 📦 附录 · 外部仓库获取

本附录列出第 6、7、9、10 章与实验直接映射的 22 个外部仓库，另含 1 个辅助训练 cookbook；它们**不作为本书源码内置依赖**（出于体积与版权），需要自行克隆到对应目录。部分训练项目还会按各自 README 拉取模型、数据集和模拟器依赖，不计入这 22 个直接映射。以下版本来自 2026-07-30 工作区 checkout 或同日只读上游审计；固定源码只建立复现起点，不代表训练、硬件、浏览器或多 Agent 实验已经执行。

### 一键克隆脚本

<details>
<summary><b>🔧 展开克隆命令</b>（共 23 个 checkout：22 个实验映射 + 1 个辅助 cookbook）</summary>

```bash
# 第 6 章 · 评测基准
git clone https://github.com/google-research/android_world.git chapter6/android_world && git -C chapter6/android_world checkout --detach 0e95d641e244504c22087cc29b013f3b2428a261
git clone https://huggingface.co/datasets/gaia-benchmark/GAIA chapter6/GAIA && git -C chapter6/GAIA checkout --detach 682dd723ee1e1697e00360edccf2366dc8418dd9
git clone https://github.com/xlang-ai/OSWorld.git chapter6/OSWorld && git -C chapter6/OSWorld checkout --detach 8365edc975efd0477a0d62444a5beed562ab5a7b
git clone https://github.com/SWE-bench/SWE-bench.git chapter6/SWE-bench && git -C chapter6/SWE-bench checkout --detach 5cd4be9fb23971679cbbafe5a0ecade27cef99be
git clone https://github.com/sierra-research/tau2-bench.git chapter6/tau2-bench && git -C chapter6/tau2-bench checkout --detach 8d005b0e5b9e4af0bc055886fa7f95fc86d1710e
git clone https://github.com/laude-institute/terminal-bench.git chapter6/terminal-bench && git -C chapter6/terminal-bench checkout --detach 8384a179b1b8688f6ea5233a4d9d51218df1ac96

# 第 7 章 · 训练框架（bojieli/* 为本书适配的分支）
git clone https://github.com/bojieli/minimind.git chapter7/MiniMind-pretrain/minimind && git -C chapter7/MiniMind-pretrain/minimind fetch origin 8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795 && git -C chapter7/MiniMind-pretrain/minimind checkout --detach 8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795 && test "$(git -C chapter7/MiniMind-pretrain/minimind rev-parse HEAD)" = "8bdc5d97d5845a8c1ac2ed56a5b8b4c0d0fb0795"  # 实验 7-3
git clone https://github.com/bojieli/minimind-v.git chapter7/MiniMind-pretrain/minimind-v && git -C chapter7/MiniMind-pretrain/minimind-v fetch origin ead791c530fa5f9a3549dbfe9e11ec732d18d2e5 && git -C chapter7/MiniMind-pretrain/minimind-v checkout --detach ead791c530fa5f9a3549dbfe9e11ec732d18d2e5 && test "$(git -C chapter7/MiniMind-pretrain/minimind-v rev-parse HEAD)" = "ead791c530fa5f9a3549dbfe9e11ec732d18d2e5"  # 实验 7-4
git clone https://github.com/bojieli/AdaptThink.git chapter7/AdaptThink-original && git -C chapter7/AdaptThink-original checkout --detach 0033ad172dd53ac64004b763477407014f21b838  # 实验 7-10
git clone https://github.com/bojieli/SFTvsRL.git chapter7/SFTvsRL && git -C chapter7/SFTvsRL checkout --detach fef0a4a3367260a0934be1e40b01e4021698e023  # 实验 7-11、7-12
git clone https://github.com/bojieli/AWorld.git chapter7/AWorld && git -C chapter7/AWorld checkout --detach a52d61d6d483e66b22ef16970eae5bbf4f4ab2ec  # 实验 7-15
git clone https://github.com/bojieli/verl.git chapter7/verl && git -C chapter7/verl checkout --detach 1593fc3a8cf894debdc3dece2a23ed739c282789  # 实验 7-14 ReTool 配方；7-15 训练后端
git clone https://github.com/bojieli/SandboxFusion.git chapter7/SandboxFusion && git -C chapter7/SandboxFusion fetch origin 4a0d573ebd64c98234c190a9d1d49e4276199a0c && git -C chapter7/SandboxFusion checkout --detach 4a0d573ebd64c98234c190a9d1d49e4276199a0c && test "$(git -C chapter7/SandboxFusion rev-parse HEAD)" = "4a0d573ebd64c98234c190a9d1d49e4276199a0c"  # 实验 7-14 代码沙箱
git clone https://github.com/thinking-machines-lab/tinker-cookbook.git chapter7/tinker-cookbook && git -C chapter7/tinker-cookbook checkout --detach fc8449187041cf102905f3f751e6d2eac7f9f754
git clone https://github.com/19PINE-AI/rlvp.git chapter7/RLVP/rlvp && git -C chapter7/RLVP/rlvp fetch origin 1ad30bc7e338911fb733739393d92c420f4d8bee && git -C chapter7/RLVP/rlvp checkout --detach 1ad30bc7e338911fb733739393d92c420f4d8bee && test "$(git -C chapter7/RLVP/rlvp rev-parse HEAD)" = "1ad30bc7e338911fb733739393d92c420f4d8bee"  # 实验 7-16
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git chapter7/SimpleVLA-RL/SimpleVLA-RL && git -C chapter7/SimpleVLA-RL/SimpleVLA-RL checkout --detach 7c51662df27b586f9e8a1ab35fcf849f2b8852f9  # 实验 7-13

# 第 9 章 · GUI 与机器人外部复现轨道
git clone https://github.com/anthropics/claude-quickstarts.git chapter9/claude-quickstarts && git -C chapter9/claude-quickstarts checkout --detach 9bcc95e316e5ef6542b4c9d0469f4078829eead5  # 实验 9-6 使用 computer-use-demo/
git clone https://github.com/browser-use/browser-use.git chapter9/browser-use && git -C chapter9/browser-use checkout --detach ec9277c5001f2cb78ee419c927775a3cfc227ff8  # 实验 9-7
git clone https://github.com/Vector-Wangel/XLeRobot.git chapter9/XLeRobot && git -C chapter9/XLeRobot fetch origin 3d14695e40c9c68229c0aacffca6053c75cd3eb6 && git -C chapter9/XLeRobot checkout --detach 3d14695e40c9c68229c0aacffca6053c75cd3eb6 && test "$(git -C chapter9/XLeRobot rev-parse HEAD)" = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"  # 实验 9-8、9-9 共用
git clone https://github.com/Grigorij-Dudnik/RoboCrew.git chapter9/RoboCrew && git -C chapter9/RoboCrew fetch origin c749148f29bd14e61347f9fc3530c343fff0d994 && git -C chapter9/RoboCrew checkout --detach c749148f29bd14e61347f9fc3530c343fff0d994 && test "$(git -C chapter9/RoboCrew rev-parse HEAD)" = "c749148f29bd14e61347f9fc3530c343fff0d994"  # 实验 9-9；RoboCrew v0.3.1
git clone https://github.com/StoneT2000/lerobot-sim2real.git chapter9/lerobot-sim2real && git -C chapter9/lerobot-sim2real fetch origin 87d6c1d969f6e0ca4dc5697940804e231118a63a && git -C chapter9/lerobot-sim2real checkout --detach 87d6c1d969f6e0ca4dc5697940804e231118a63a && test "$(git -C chapter9/lerobot-sim2real rev-parse HEAD)" = "87d6c1d969f6e0ca4dc5697940804e231118a63a"  # 实验 9-10

# 第 10 章 · 双 Agent 架构（已独立为 TalkAct 项目）+ 斯坦福 AI 小镇
git clone https://github.com/19PINE-AI/TalkAct.git chapter10/use-computer-while-calling && git -C chapter10/use-computer-while-calling fetch origin 7d70007f72d45ddfc1a14e8e229b6d444e4919a2 && git -C chapter10/use-computer-while-calling checkout --detach 7d70007f72d45ddfc1a14e8e229b6d444e4919a2 && test "$(git -C chapter10/use-computer-while-calling rev-parse HEAD)" = "7d70007f72d45ddfc1a14e8e229b6d444e4919a2"  # 实验 10-4
git clone https://github.com/joonspk-research/generative_agents.git chapter10/generative_agents && git -C chapter10/generative_agents fetch origin fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4 && git -C chapter10/generative_agents checkout --detach fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4 && test "$(git -C chapter10/generative_agents rev-parse HEAD)" = "fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4"  # 实验 10-7
```

> 上述九个当前缺失的 checkout（7-3、7-4、7-16、7-14 的 SandboxFusion、9-8/9-9 共用的 XLeRobot、9-9 的 RoboCrew、9-10 的 `lerobot-sim2real`、10-4、10-7）也已固定到不可变 SHA；命令会 detached checkout 并用 `rev-parse HEAD` 做相等性校验。第 10 章 `use-computer-while-calling` 已发展为独立维护的 [19PINE-AI/TalkAct](https://github.com/19PINE-AI/TalkAct)。源码存在或安装成功都不是实验完成声明。

</details>

## 🤝 贡献

本书与配套代码全部开源，非常欢迎社区通过 Pull Request 参与共建：

| 类型 | 说明 |
| --- | --- |
| 📝 **书籍内容改进** | 勘误、补充、更清晰的表述，或新增前沿进展（正文见 `book/chapter*.md`） |
| 🐛 **代码改进与 Bug 修复** | 让配套项目更健壮、更易用、更贴近生产实践 |
| 🧪 **新的实践项目** | 为某个实验补充/替换更好的实现，或贡献全新的示例项目 |
| 🎨 **配图设计改进** | 直接改进 `book/images/` 中已签入的 SVG 图表，让它们更清晰美观 |
| 🌐 **新语言翻译** | 欢迎翻译成更多语言，可参考英文（`book-en/`）、阿拉伯语（`book-ar/`）、繁體中文（台灣）版（`book-zhtw/`）、俄语（`book-ru/`）、泰米尔语（`book-ta/`）、越南语（`book-vi/`）、日语（`book-ja/`）、土耳其语（`book-tr/`）、韩语（`book-ko/`）、匈牙利语（`book-hu/`）的组织方式 |

提交前建议先把相关实验亲手跑一遍、确认可复现；也欢迎先提 issue 讨论想法。

## 📄 许可证

本项目采用 [Apache License 2.0](LICENSE) 开源许可证，详见 [`LICENSE`](LICENSE) 文件。部分子项目可能包含各自的许可证信息，请以子项目中的说明为准。

## ⭐ Star History

<a href="https://star-history.com/#bojieli/ai-agent-book&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/star-history-dark.png" />
    <source media="(prefers-color-scheme: light)" srcset="assets/star-history-light.png" />
    <img alt="Star History Chart" src="assets/star-history-light.png" width="100%" />
  </picture>
</a>

<sub>由 [`scripts/gen_star_history.py`](scripts/gen_star_history.py) 生成，[GitHub Actions](.github/workflows/star-history.yml) 每日自动更新 · 点击图片查看实时数据</sub>
