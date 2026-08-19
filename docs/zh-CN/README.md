# 深入理解 AI Agent：设计原理与工程实践

[![PDF](https://img.shields.io/badge/PDF-%E4%B8%8B%E8%BD%BD-success.svg)](#-电子书) [![在线阅读](https://img.shields.io/badge/🌐_在线阅读-bojieli.github.io-success?style=flat-square)](https://bojieli.github.io/ai-agent-book/) [![Stars](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](../../LICENSE) [![Languages](https://img.shields.io/badge/翻译-14%20种%20语言-informational.svg)](#-电子书)
[![Trending GitHub Project of the Day](https://img.shields.io/badge/GitHub%20Trending-Project%20of%20the%20Day-orange?logo=github)](https://github.com/trending)

**中文** ← 当前 · [English](../en/README.md) · [Español](../es/README.md) · [Bahasa Indonesia](../id/README.md) · [العربية](../ar/README.md) · [繁體中文（台灣）](../zh-TW/README.md) · [Русский](../ru/README.md) · [Tiếng Việt](../vi/README.md) · [தமிழ்](../ta/README.md) · [日本語](../ja/README.md) · [Türkçe](../tr/README.md) · [한국어](../ko/README.md) · [Magyar](../hu/README.md) · [עברית](../../README.he.md)

> 📥 **[下载 PDF / EPUB](#-电子书)**（推荐）— 推荐使用 PDF / EPUB 离线阅读，排版最佳；也可[在线阅读](https://bojieli.github.io/ai-agent-book/)（支持多语言切换、章节折叠、全文搜索，每次推送自动更新）。

**Agent = LLM + 上下文 + 工具**——本书围绕这个核心公式，用 10 章把 AI Agent 从原理讲到工程实战。全书正文、配图、**103 个配套实验**全部开源，欢迎亲手把实验跑一遍。

> 📢 **2.0 版变更（相较 1.4 版）**：本仓库书稿版本已由 1.4 升级为 2.0。2.0 版将原第四章中的“异步交互”部分与原第九章中关于“多模态 Agent”的内容合并，重组为新的第六章“交互：观察与动作空间的扩展”。原第六章“Agent 的评估”、第七章“模型后训练”和第八章“Agent 的持续进化”依次后移一章，现分别为第七、八、九章。
>
> 如果你看到的是旧版 PDF，建议[下载最新版 PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf)。新版还包含许多内容修正与调整，请以最新版为准。

| 📚 **10 章** 正文，从基础到生产 | 📂 **103 个** 配套实验（含本地项目与外部复现轨道） | 🌐 **14 种** 语言：中 / 英 / 西 / 印尼 / 阿 / 繁體中文（台灣） / 俄 / 泰米尔 / 越 / 日 / 土耳其 / 韩 / 匈牙利 / 希伯来 |
| :---: | :---: | :---: |

## 📖 电子书

> 📥 **离线下载**（推荐，全书正文，开源免费）。以下链接始终指向 main 分支的最新构建；固定版本见 [Releases](https://github.com/bojieli/ai-agent-book/releases)：
> - **中文（原版）**：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.epub)
> - **英文**（社区翻译，by [@nsdevaraj](https://github.com/nsdevaraj)、[@whanyu1212](https://github.com/whanyu1212)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.epub)
> - **西班牙语**（社区翻译，by [@santhreal](https://github.com/santhreal)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.epub)
> - **繁体中文（台湾）**（社区翻译，by [@tigercosmos](https://github.com/tigercosmos)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.epub)
> - **俄语**（社区翻译，by [@ui99ru](https://github.com/ui99ru)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.epub)
> - **泰米尔语**（社区翻译，by [@nsdevaraj](https://github.com/nsdevaraj)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.epub)
> - **越南语**（社区翻译，by [@toanalien](https://github.com/toanalien)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.epub)
> - **日语**（社区翻译，by [@eltociear](https://github.com/eltociear)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.epub)
> - **阿拉伯语**（社区翻译，by [@TheSyBuilder](https://github.com/TheSyBuilder)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.epub)
> - **土耳其语**（社区翻译，by [@memisemre](https://github.com/memisemre)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.epub)
> - **韩语**（社区翻译，by [@JeongJaeSoon](https://github.com/JeongJaeSoon)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.epub)
>
> 🌐 也可[在线阅读](https://bojieli.github.io/ai-agent-book/)——支持多语言切换、章节折叠、全文搜索，以及配套实验直链。每次推送 main 自动重建。

中文正文源码位于 [`book/`](../../book/)；英文/西班牙语/阿拉伯语/繁体中文（台湾）/俄语/泰米尔语/越南语/日语/土耳其语/韩语版为社区贡献（可能滞后于中文原版），分别位于 [`book-en/`](../../book-en/)、[`book-es/`](../../book-es/)、[`book-ar/`](../../book-ar/)、[`book-zhtw/`](../../book-zhtw/)、[`book-ru/`](../../book-ru/)、[`book-ta/`](../../book-ta/)、[`book-vi/`](../../book-vi/)、[`book-ja/`](../../book-ja/)、[`book-tr/`](../../book-tr/)、[`book-ko/`](../../book-ko/)。

<details>
<summary><b>🔧 自行编译 PDF / EPUB？</b>（PDF 需 pandoc / xelatex / ElegantBook）</summary>

- **EPUB**：使用共享构建脚本，详见 [EPUB 构建说明](../../EPUB.md)
- **正文源码**：`book/introduction.md`（引言）、`book/chapter1.md` ~ `book/chapter10.md`（第一至第十章）、`book/afterword.md`（后记）
- **编译**：安装 pandoc、xelatex、ElegantBook 文档类与相关字体后，运行

  ```bash
  cd book && bash build_pdf.sh
  ```

  图表以 SVG 文件存于 `book/images/`，编译时直接使用；排版细节见 `book/preamble.tex` 与 `book/*.lua`。

</details>

## 📑 内容速览（第 1–10 章）

全书围绕核心公式 **Agent = LLM + 上下文 + 工具** 展开，十章层层递进：

| 章 | 主题 | 一句话核心 | 正文 | 实验 |
| :--: | --- | --- | :--: | :--: |
| 1 | 🚀 **AI Agent 入门** | **Agent = LLM + 上下文 + 工具**；Harness 工程才是竞争力 | [读](../../book/chapter1.md) | [3](../../chapter1/README.md) |
| 2 | 🎯 **上下文工程** | 上下文决定能力上限：KV Cache、提示工程、Agent Skills、上下文压缩 | [读](../../book/chapter2.md) | [10](../../chapter2/README.md) |
| 3 | 📚 **用户记忆和知识库** | 跨会话记住用户、接入外部知识：用户记忆、RAG、结构化索引、知识图谱 | [读](../../book/chapter3.md) | [12](../../chapter3/README.md) |
| 4 | 🛠️ **工具** | 工具是 Agent 的双手：MCP 协议、感知/执行/协作三类工具与主动工具发现 | [读](../../book/chapter4.md) | [5](../../chapter4/README.md) |
| 5 | 💻 **Coding Agent 与通用 Agent** | 代码是「能创造新工具的工具」，生产级 Coding Agent 全景 | [读](../../book/chapter5.md) | [13](../../chapter5/README.md) |
| 6 | 🎙️ **交互：观察与动作空间的扩展** | 从模态与时序两个维度扩展 Agent 的观察与动作空间：异步与事件驱动、语音交互、Computer Use 和机器人操作 | [读](../../book/chapter6.md) | [13](../../chapter6/README.md) |
| 7 | 🎯 **Agent 的评估** | 把表现变成可比较信号：评估环境、指标、统计显著性、评估驱动选型 | [读](../../book/chapter7.md) | [13](../../chapter7/README.md) |
| 8 | 🧠 **模型后训练** | 预训练/SFT/RL 三阶段：何时选 SFT、何时选 RL，工具调用内化、样本效率 | [读](../../book/chapter8.md) | [19](../../chapter8/README.md) |
| 9 | 🔄 **Agent 的持续进化** | 从运行轨迹获得学习信号，更新知识、指令、程序与参数 | [读](../../book/chapter9.md) | [9](../../chapter9/README.md) |
| 10 | 🤝 **多 Agent 协作** | 群体智能高于个体：协作框架、上下文共享/隔离、涌现的「Agent 社会」 | [读](../../book/chapter10.md) | [6](../../chapter10/README.md) |

> 💡 **读** = 在 GitHub 网页直接读章节正文（markdown）；**N** = 该章配套项目数，点击查看代码。项目类型说明（✅ 可运行 / 📖 复现 / 🚧 设计）见各章 README。
>
> 📚 如何高效阅读本书？详见 **[学习建议](LEARNING.md)**（核心理念、学习路径、难度分级、实践建议）。

## 💻 运行配套实验

项目统一支持 **Python 3.11–3.13**。请在仓库根目录按章节安装依赖；将 `ch1` 替换为 `ch2` ~ `ch10` 即可安装对应章节：

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
- 浏览器、CUDA、FFmpeg、Ollama、Playwright 浏览器及外部仓库等系统依赖，请继续参考各实验 README。第 8 章部分内置第三方组件需要 Python 3.12+。

## 🔑 API 密钥

建议申请下面几个平台的 API Key 方便学习。模型选型可参考 [这篇指南](https://01.me/2025/07/llm-api-setup/)。

| 平台 | 链接 | 备注 | 访问端点 |
| --- | --- | --- | --- |
| **Kimi**（Moonshot） | <https://platform.moonshot.cn/> | Kimi 系列，长上下文和 Agent 能力强 | 中国大陆 |
| **智谱 GLM** | <https://open.bigmodel.cn/> | GLM-4.6 等，中文能力突出，性价比高 | 中国大陆 |
| **Siliconflow** | <https://siliconflow.cn/> | 各类开源模型（DeepSeek、Qwen 等），国内快速接入 | 中国大陆 |
| **DeepSeek** | <https://platform.deepseek.com/> | DeepSeek 官方 API | 全球 + 中国大陆 |
| **Krill AI** | [www.krill-ai.net](https://www.krill-ai.net/register?invite=Q8D3L35725) | 一站式接入全球及国内主流模型（OpenAI、Claude、Gemini、Grok、Kimi、GLM、DeepSeek、Qwen、Minimax） | 全球 + 中国大陆 |
| **OpenRouter** | <https://openrouter.ai/> | 一站式接入全球及国内主流模型（GPT、Claude、Gemini、Kimi、GLM、DeepSeek、Qwen 等） | 全球 |

## 💎 赞助

感谢 **Krill AI** 赞助本项目！Krill 提供 GPT / Claude / Gemini 及众多国产模型的官方稳定极速 API 中转，支持企业级定制、开票及 7×16h 专属技术支持，并独家适配 WebSocket 连接实现极速首 Token 响应。

Krill 为本书读者提供专属优惠：通过 [此链接](https://www.krill-ai.net/register?invite=Q8D3L35725) 注册并在充值时输入优惠码 "ai-agent-book"，即可享受首单 Codex 方案 23% 折扣！

> 🧪 实验执行状态、证据及未达验收条件另行记录于 [`EXPERIMENT_STATUS.md`](../EXPERIMENT_STATUS.md)；clone 或安装源码不构成完成证明。

## 📦 附录 · 获取外部仓库

第 6、7、8、10 章的 23 个外部仓库（基准测试、训练框架、机器人平台）因体积和许可原因**未打包**，需自行 clone 到对应目录。

### 一键 clone 脚本

<details>
<summary><b>🔧 展开 clone 命令</b>（23 个外部仓库）</summary>

```bash
# 第 6 章 · GUI 与机器人外部复现轨道
git clone https://github.com/browser-use/browser-use.git               chapter6/browser-use
git clone https://github.com/anthropics/claude-quickstarts.git         chapter6/claude-quickstarts
git clone https://github.com/Vector-Wangel/XLeRobot.git                chapter6/XLeRobot                       # 实验 6-9、6-11 共用
git clone https://github.com/Grigorij-Dudnik/RoboCrew.git              chapter6/RoboCrew                       # 实验 6-10、6-11
git clone https://github.com/StoneT2000/lerobot-sim2real.git           chapter6/lerobot-sim2real                # 实验 6-13

# 第 7 章 · 评估基准
git clone https://github.com/google-research/android_world.git         chapter7/android_world
git clone https://huggingface.co/datasets/gaia-benchmark/GAIA         chapter7/GAIA
git clone https://github.com/xlang-ai/OSWorld.git                      chapter7/OSWorld
git clone https://github.com/SWE-bench/SWE-bench.git                   chapter7/SWE-bench
git clone https://github.com/sierra-research/tau2-bench.git            chapter7/tau2-bench
git clone https://github.com/laude-institute/terminal-bench.git        chapter7/terminal-bench

# 第 8 章 · 训练框架（bojieli/* 为本书适配 fork）
git clone https://github.com/bojieli/minimind.git                      chapter8/MiniMind-pretrain/minimind      # 实验 8-3 从零训练 LLM
git clone https://github.com/bojieli/minimind-v.git                    chapter8/MiniMind-pretrain/minimind-v    # 实验 8-4 从零训练 VLM（投影层）
git clone https://github.com/bojieli/AdaptThink.git                    chapter8/AdaptThink-original
git clone https://github.com/bojieli/AWorld.git                        chapter8/AWorld
git clone https://github.com/bojieli/SFTvsRL.git                       chapter8/SFTvsRL
git clone https://github.com/bojieli/verl.git                          chapter8/verl
git clone https://github.com/bojieli/SandboxFusion.git                 chapter8/SandboxFusion                  # 实验 8-14 代码沙箱
git clone https://github.com/thinking-machines-lab/tinker-cookbook.git chapter8/tinker-cookbook
git clone https://github.com/19PINE-AI/rlvp.git                        chapter8/RLVP/rlvp                       # 实验 8-16 RLVP 论文代码
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git                 chapter8/SimpleVLA-RL/SimpleVLA-RL      # 实验 8-13 视觉-语言-动作 RL

# 第 10 章 · 双 Agent 架构（现为独立 TalkAct 项目）+ Stanford AI Town
git clone https://github.com/19PINE-AI/TalkAct.git                     chapter10/use-computer-while-calling
git clone https://github.com/joonspk-research/generative_agents.git    chapter10/generative_agents             # 实验 10-5 Stanford AI Town
```

> 如果项目 README 指定了特定 commit，请 `git checkout` 到该版本以保证可复现性。第 10 章的 `use-computer-while-calling` 已发展为独立维护的 [19PINE-AI/TalkAct](https://github.com/19PINE-AI/TalkAct)；本仓库仅保留指针文档。

</details>

## 🤝 贡献

本书及配套代码完全开源，欢迎提交 Pull Request：

| 类型 | 说明 |
| --- | --- |
| 📝 **正文内容** | 勘误、补充、更清晰的表达或新进展（正文在 `book/chapter*.md`） |
| 🐛 **代码改进与 Bug 修复** | 让配套项目更健壮、更易用、更接近生产级 |
| 🧪 **新实验项目** | 添加/替换更好的实验实现，或贡献新示例 |
| 🎨 **图表设计** | 直接改进 `book/images/` 下的 SVG 图表 |
| 🌐 **新翻译** | 欢迎翻译为更多语言；参考英文（`book-en/`）、阿拉伯语（`book-ar/`）、繁体中文/台湾（`book-zhtw/`）、俄语（`book-ru/`）、泰米尔语（`book-ta/`）、越南语（`book-vi/`）、日语（`book-ja/`）、土耳其语（`book-tr/`）、韩语（`book-ko/`） |

提交前请运行相关实验确认可复现；也欢迎先开 issue 讨论想法。

## 📄 许可证

本项目基于 [Apache License 2.0](../../LICENSE) 开源。详见 [`LICENSE`](../../LICENSE) 文件。部分子项目可能包含各自的许可证信息，请参考对应子项目。

## ⭐ Star 历史

<a href="https://star-history.com/#bojieli/ai-agent-book&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../../assets/star-history-dark.png" />
    <source media="(prefers-color-scheme: light)" srcset="../../assets/star-history-light.png" />
    <img alt="Star History Chart" src="../../assets/star-history-light.png" width="100%" />
  </picture>
</a>

<sub>由 [`scripts/gen_star_history.py`](../../scripts/gen_star_history.py) 生成，[GitHub Actions](../../.github/workflows/star-history.yml) 每日更新 · 点击图片查看实时数据</sub>
