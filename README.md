# 深入理解 AI Agent：设计原理与工程实践

[![Stars](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE) [![PDF](https://img.shields.io/badge/PDF-%E4%B8%8B%E8%BD%BD-success.svg)](#-电子书) [![Languages](https://img.shields.io/badge/翻译-5%20种%20语言-informational.svg)](#-电子书)

**中文** ← 当前 · [台灣正體](docs/zh-TW/README.md) · [English](docs/en/README.md) · [Tiếng Việt](docs/vi/README.md) · [தமிழ்](docs/ta/README.md)

**Agent = LLM + 上下文 + 工具**——本书围绕这个核心公式，用 10 章把 AI Agent 从原理讲到工程实战。全书正文、配图、**88 个配套实验**全部开源，欢迎亲手把实验跑一遍。

| 📚 **10 章** 正文，从基础到生产 | 📂 **88 个** 配套项目（70+ 可独立运行） | 🌐 **5 种** 语言：中 / 台灣正體 / 英 / 泰 / 越 |
| :---: | :---: | :---: |

## 📖 电子书

> 📥 **直接下载**（全书正文，开源免费）。以下链接始终指向 main 分支的最新构建；固定版本见 [Releases](https://github.com/bojieli/ai-agent-book/releases)：
> - **中文（原版）**：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.epub)
> - **台灣正體**（社区翻译，by [@tigercosmos](https://github.com/tigercosmos)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.epub)
> - **英文**（社区翻译，by [@nsdevaraj](https://github.com/nsdevaraj)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.epub)
> - **泰米尔语**（社区翻译，by [@nsdevaraj](https://github.com/nsdevaraj)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.epub)
> - **越南语**（社区翻译，by [@toanalien](https://github.com/toanalien)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.epub)

中文正文源码位于 [`book/`](book/)；台灣正體/英文/泰米尔/越南语版本为社区贡献（可能滞后于中文原版），分别位于 [`book-zhtw/`](book-zhtw/)、[`book-en/`](book-en/)、[`book-ta/`](book-ta/)、[`book-vi/`](book-vi/)。

可使用统一的构建脚本生成中文、台灣正體、英文、泰米尔语和越南语 EPUB 3 电子书。请参阅 [EPUB 构建说明](EPUB.md)。

<details>
<summary><b>🔧 想自行编译 PDF？</b>（需 pandoc / xelatex / ElegantBook）</summary>

- **正文源码**：`book/introduction.md`（引言）、`book/chapter1.md` ~ `book/chapter10.md`（第一至第十章）、`book/afterword.md`（后记）
- **编译**：安装 pandoc、xelatex、ElegantBook 文档类与相关字体后，运行

  ```bash
  cd book && bash build_pdf.sh
  ```

  图表由 `book/gen_*_figs.py` 生成、存于 `book/images/`，排版细节见 `book/preamble.tex` 与 `book/*.lua`。

</details>

## 📑 内容速览（第 1–10 章）

全书围绕核心公式 **Agent = LLM + 上下文 + 工具** 展开，十章层层递进：

| 章 | 主题 | 一句话核心 | 正文 | 代码 |
| :--: | --- | --- | :--: | :--: |
| 1 | 🚀 **Agent 基础知识** | 「模型即 Agent」新范式 + **Agent = LLM + 上下文 + 工具**；Harness 工程才是竞争力 | [读](book/chapter1.md) | [4](chapter1/README.md) |
| 2 | 🎯 **上下文工程** | 上下文决定能力上限：KV Cache、提示工程、Agent Skills、上下文压缩 | [读](book/chapter2.md) | [9](chapter2/README.md) |
| 3 | 📚 **用户记忆和知识库** | 跨会话记住用户、接入外部知识：用户记忆、RAG、结构化索引、知识图谱 | [读](book/chapter3.md) | [13](chapter3/README.md) |
| 4 | 🛠️ **工具** | 工具是 Agent 的双手：MCP 协议、感知/执行/协作三类工具、事件驱动异步 Agent、主动工具发现 | [读](book/chapter4.md) | [7](chapter4/README.md) |
| 5 | 💻 **Coding Agent 与代码生成** | 代码是「能创造新工具的工具」，生产级 Coding Agent 全景 | [读](book/chapter5.md) | [12](chapter5/README.md) |
| 6 | 🎯 **Agent 的评估** | 把表现变成可比较信号：评估环境、指标、统计显著性、评估驱动选型 | [读](book/chapter6.md) | [10](chapter6/README.md) |
| 7 | 🧠 **模型后训练** | 预训练/SFT/RL 三阶段：何时选 SFT、何时选 RL，工具调用内化、样本效率 | [读](book/chapter7.md) | [14](chapter7/README.md) |
| 8 | 🔄 **Agent 的自我进化** | 不改权重也能成长：经验学习、从工具使用者到创造者 | [读](book/chapter8.md) | [6](chapter8/README.md) |
| 9 | 🎙️ **多模态与实时交互** | 从文本扩展到语音、GUI、物理世界：语音三范式、Computer Use、机器人 | [读](book/chapter9.md) | [7](chapter9/README.md) |
| 10 | 🤝 **多 Agent 协作** | 群体智能高于个体：协作框架、上下文共享/隔离、涌现的「Agent 社会」 | [读](book/chapter10.md) | [6](chapter10/README.md) |

> 💡 **读** = 在 GitHub 网页直接读章节正文（markdown）；**N** = 该章配套项目数，点击查看代码。项目类型说明（✅ 可运行 / 📖 复现 / 🚧 设计）见各章 README。
>
> 📚 如何高效阅读本书？详见 **[学习建议](docs/zh-CN/LEARNING.md)**（核心理念、学习路径、难度分级、实践建议）。

## 🔑 API 密钥

建议申请下面几个平台的 API Key 方便学习。模型选型可参考 [这篇指南](https://01.me/2025/07/llm-api-setup/)。

| 平台 | 链接 | 特色 |
| --- | --- | --- |
| **Kimi**（月之暗面） | <https://platform.moonshot.cn/> | Kimi 系列，Coding、Agent 能力强 |
| **智谱 GLM** | <https://open.bigmodel.cn/> | GLM-5.2 等，Coding、Agent 能力强 |
| **Siliconflow** | <https://siliconflow.cn/> | 各种开源模型（DeepSeek、Qwen 等） |
| **火山引擎** | <https://www.volcengine.com/product/ark> | 字节豆包闭源模型，国内访问延迟低 |
| **OpenRouter** | <https://openrouter.ai/> | 一站式访问 Gemini / Claude / GPT-5 等海外模型（官方 API 需海外 IP/支付方式，OpenAI 还需海外身份认证） |

## 📦 附录 · 外部仓库获取

第 6、7、9、10 章的评测基准、训练框架、机器人平台等 20 个外部仓库**未内置**（出于体积与版权），需要自行克隆到对应目录。

### 一键克隆脚本

<details>
<summary><b>🔧 展开克隆命令</b>（共 20 个外部仓库）</summary>

```bash
# 第 6 章 · 评测基准
git clone https://github.com/google-research/android_world.git         chapter6/android_world
git clone https://huggingface.co/datasets/gaia-benchmark/GAIA          chapter6/GAIA
git clone https://github.com/xlang-ai/OSWorld.git                      chapter6/OSWorld
git clone https://github.com/SWE-bench/SWE-bench.git                   chapter6/SWE-bench
git clone https://github.com/sierra-research/tau2-bench.git            chapter6/tau2-bench
git clone https://github.com/laude-institute/terminal-bench.git        chapter6/terminal-bench

# 第 7 章 · 训练框架（bojieli/* 为本书适配的分支）
git clone https://github.com/bojieli/minimind.git                      chapter7/MiniMind-pretrain/minimind      # 实验 7-3 从零训 LLM
git clone https://github.com/bojieli/minimind-v.git                    chapter7/MiniMind-pretrain/minimind-v    # 实验 7-4 从零训 VLM（投影层）
git clone https://github.com/bojieli/AdaptThink.git                    chapter7/AdaptThink-original
git clone https://github.com/bojieli/AWorld.git                        chapter7/AWorld
git clone https://github.com/bojieli/SFTvsRL.git                       chapter7/SFTvsRL
git clone https://github.com/bojieli/verl.git                          chapter7/verl
git clone https://github.com/thinking-machines-lab/tinker-cookbook.git chapter7/tinker-cookbook
git clone https://github.com/bojieli/lighteval.git                     chapter7/Intuitor/lighteval
git clone https://github.com/19PINE-AI/rlvp.git                        chapter7/RLVP/rlvp                       # 实验 7-14 RLVP 论文代码
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git                 chapter7/SimpleVLA-RL/SimpleVLA-RL       # 实验 7-13 视觉-语言-动作 RL

# 第 9 章 · 浏览器自动化与 Claude 示例
git clone https://github.com/browser-use/browser-use.git               chapter9/browser-use
git clone https://github.com/anthropics/claude-quickstarts.git         chapter9/claude-quickstarts

# 第 10 章 · 双 Agent 架构（已独立为 TalkAct 项目）+ 斯坦福 AI 小镇
git clone https://github.com/19PINE-AI/TalkAct.git                     chapter10/use-computer-while-calling
git clone https://github.com/joonspk-research/generative_agents.git    chapter10/generative_agents             # 实验 10-7 斯坦福 AI 小镇
```

> 各项目 README 如标注了特定 commit，请按说明 `git checkout` 到对应版本以保证复现一致。第 10 章 `use-computer-while-calling` 已发展为独立维护的 [19PINE-AI/TalkAct](https://github.com/19PINE-AI/TalkAct)，本仓库只保留指向它的说明文档。

</details>

### 其它复现路径

下面这些实验无专属 clone 命令，但有特定的复现方式：

| 实验 | 类型 | 说明 |
| --- | :--: | --- |
| 6-2 / 6-3 / 6-4 / 6-9 | 📝 读者练习 | 人肉基准、记忆评估、JSON Cards vs RAG、记忆选型——改造复用第 3 章 `user-memory` / `user-memory-evaluation` / `contextual-retrieval` |
| 5-12 | 📝 读者练习 | 能创造 Agent 的 Agent——基于 `chapter5/coding-agent` 自举扩展 |
| 7-8 | 📝 读者练习 | Prompt 蒸馏——落地实现见 `chapter8/prompt-distillation`（跨章复用） |
| 7-9 | 📝 读者练习 | CoT 蒸馏 `[扩展]`——书中给出实验设计与验收标准，无专属代码 |
| 6-11 | 🤖 仿真评估 | OpenVLA + RoboTwin2——VLA 训练/环境依赖见 `chapter7/SimpleVLA-RL` 的 README |
| 9-8 / 9-9 | 🔧 真实硬件 | XLeRobot 遥操作与 LLM Agent 控制——需 SO-100 机械臂，[Teleop](https://xlerobot.readthedocs.io/en/latest/software/getting_started/XLeRobot_teleop.html) · [LLM Agent](https://xlerobot.readthedocs.io/en/latest/software/getting_started/LLM_agent.html) |
| 9-10 | 🔧 真实硬件 | RGB 零样本 Sim2Real 抓取——[`StoneT2000/lerobot-sim2real`](https://github.com/StoneT2000/lerobot-sim2real)（仿真可纯 GPU，部署需 SO-100） |

## 🤝 贡献

本书与配套代码全部开源，非常欢迎社区通过 Pull Request 参与共建：

| 类型 | 说明 |
| --- | --- |
| 📝 **书籍内容改进** | 勘误、补充、更清晰的表述，或新增前沿进展（正文见 `book/chapter*.md`） |
| 🐛 **代码改进与 Bug 修复** | 让配套项目更健壮、更易用、更贴近生产实践 |
| 🧪 **新的实践项目** | 为某个实验补充/替换更好的实现，或贡献全新的示例项目 |
| 🎨 **配图设计改进** | 让 `book/images/` 中的图表更清晰美观（配图由 `book/gen_*_figs.py` 生成） |
| 🌐 **新语言翻译** | 欢迎翻译成更多语言，可参考台灣正體（`book-zhtw/`）、英文（`book-en/`）、泰米尔语（`book-ta/`）、越南语（`book-vi/`）的组织方式 |

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

---

## 附录 · 本仓库工程子项目（非书稿正文）

| 目录 | 说明 |
|------|------|
| [`jiyaojun/`](jiyaojun/) | **纪要君生产架构脱敏重建**（Meeting Work Unit）：Skill Pack、Bounded Agent Loop、Session Journal、ACL-first Hybrid RAG、Dialog/Pipeline。详见 [`jiyaojun/README.md`](jiyaojun/README.md) · [`docs/meeting-assistant/`](docs/meeting-assistant/) |
| [`llm-safety-platform/`](llm-safety-platform/) | **LLM 安全控制面脱敏重建**：L1–L4、五态决策、Dual-Gate、发布审批与审计哈希链；与纪要君独立。 |
| `jiyaojun-preview/` | 原始预览，**只读参考** |

### 纪要君 M4 R1 旗舰闭环（2026-08-06）

- `jiyaojun/app/connectors/jira_simulator.py`：Jira 确定性模拟（幂等 / timeout / fail / transition / webhook 回调）。
- `jiyaojun/app/demo/r1_flagship_loop.py`：技术评审 → HITL → 缺陷 → 企微 msgid → webhook 关闭 Continuum → 下一场 briefing 不召回已关闭项。
- `jiyaojun/app/api/bff.py`：`internal_connector_webhook` 同步关闭 `SeriesContinuumBridge` open item。
- `jiyaojun/app/scheduler/celery_tasks.py`：默认 `JIYAOJUN_CELERY_PIPELINE=orchestrator` 走真实 `Orchestrator.bind_and_run`；`stub` 保留占位。
- 验收：`cd jiyaojun && python -m app.demo.r1_flagship_loop`；`run_all` 默认无 env 全绿。

### 纪要君 RAG（2026-08-06）

- 真分块：`app/knowledge/chunking.py`（标题/说话人轮次 + 可配置 overlap）
- 测评：`python -m app.eval.retrieval_quality` → Hit@k / MRR / nDCG / Faithfulness
- 问答接地：Dialog/BFF 知识问题返回 citation，不再空回声

### P7 简历事实收口（2026-08-06）

已对照两个脱敏重建工程的代码、架构文档和全量门禁，重写 [`简历_new/个人简历.md`](简历_new/个人简历.md) 与 [`简历_new/个人简历_纪要君架构版.md`](简历_new/个人简历_纪要君架构版.md)：

- **纪要君**：补齐技术负责人角色、Meeting Work Unit、Skill Pack、Bounded Agent Loop、Session Journal / Context Compaction、Continuum、ACL-first Hybrid RAG、HITL 与统一写回运行时。
- **安全控制面**：补齐 L1–L4、五态 SafetyDecision、Dual-Gate、publish profile、critical 双人审批、审计哈希链与私有化 SPI 边界。
- **口径约束**：生产结果与脱敏回归指标分开陈述；shim/static 语料通过不表述为生产零事故；进程内调度、Mock Planner、single-writer 等边界保留在架构材料中。
- **证据索引**：新增 [`简历_new/简历事实证据映射.md`](简历_new/简历事实证据映射.md)，逐项标明生产监控口径、代码证据、测试命令和面试边界。

### 本轮代码修正与验证（2026-08-06）

- `jiyaojun/app/eval/retrieval_quality.py`：修正 source 级 nDCG 重复 chunk 计分，避免指标大于 1；新增回归测试并更新项目 README。修正后 Hit@5=1.0、MRR=0.9286、nDCG@5=0.9473、Faithfulness=0.932。
- `llm-safety-platform/app/api/main.py`：FastAPI 启动初始化从废弃的 `on_event` 迁移到 `lifespan`；更新项目 README。
- 全量门禁：纪要君 117 项 pytest 与 `run_all` 通过；安全控制面 pytest 103 项、`run_all`、dual_gate ci/release/full 通过。

### Agent Skills 切换（2026-08-06）

- **卸载 Superpowers**：已删除 Cursor 插件缓存 `~/.cursor/plugins/cache/cursor-public/superpowers`（注册表 `installedIds` 本已为空）。本机若仍保留参考仓库 `~/Projects/superpowers`，与 Cursor 插件无关，可按需自行删除。
- **安装 mattpocock/skills**：通过 `npx skills@latest add mattpocock/skills -g -a cursor --skill '*' -y` 全局安装全部 **35** 个 skills，主目录为 `~/.agents/skills/`，并软链到 `~/.cursor/skills` 方便 Cursor 发现。
- **常用入口**：`/ask-matt`、`/grill-with-docs`（口语里常叫 grill-me-doc，和 `/grill-me` 是一对：后者纯追问不落文档，前者会边问边写 ADR/`CONTEXT.md`）、`/setup-matt-pocock-skills`（每个仓库建议先跑一次做 issue tracker / triage / domain docs 配置）、`/tdd`、`/implement`。
- **更新方式**：`npx skills update`（需本机 Node；已放在 `~/.local/node`，可按需把该路径加入 `PATH`）。
- **2026-08-06 补充**：确认 `grill-me-doc` = 官方名 `grill-with-docs`，已在上一轮 35 个 skills 中安装于 `~/.agents/skills/grill-with-docs/`，无需重复安装。

### 项目升级领域共识（2026-08-06）

- 新增 [`CONTEXT-MAP.md`](CONTEXT-MAP.md)，明确“会议工作管理”与“AI 安全治理”两个上下文及单向依赖。
- 新增 [`jiyaojun/CONTEXT.md`](jiyaojun/CONTEXT.md) 与 [`llm-safety-platform/CONTEXT.md`](llm-safety-platform/CONTEXT.md)，统一会议工作单元、跨会连续体、安全判决、攻击门/正常业务门等领域语言。
- 两个项目统一定位为**生产架构脱敏重建**；目标是求职展示与企业二次接入，后续投入按纪要君 70% / 安全平台 30%，单人周期 8～12 周。
- 最终形态：本地真实开源基础设施替换核心存储/调度 Mock，模型通过外部 OpenAI-compatible 商业 API 接入；纪要君单向接入安全控制面；提供一键启动、正常路径、故障路径和指标看板。
- 架构决策：[`ADR-0001`](docs/adr/0001-meeting-agent-depends-on-safety-control-plane.md) 固化单向安全依赖与“更严格结果生效”；[`ADR-0002`](docs/adr/0002-openai-compatible-commercial-model-api.md) 固化商业模型 API 的 OpenAI-compatible 接入、凭据外置与离线确定性替身。
- 外部模型安全边界：[`ADR-0003`](docs/adr/0003-commercial-model-data-egress-and-budget.md) 规定只允许脱敏后的 public/internal 内容出站，商业 Judge 仅处理灰区，并设置 token、每日调用和月度费用上限。
- 本地验证栈采用分层 Compose：Core（PostgreSQL/Redis/SeaweedFS/Qdrant）、Worker（Celery）、Identity（Keycloak）、Secrets（OpenBao）和 Observability（OpenTelemetry/Prometheus/Grafana/Tempo）；Jira/企微仅实现确定性契约模拟。MinIO 社区仓库已归档，不作为新增依赖。
- 连接协议：[`ADR-0004`](docs/adr/0004-safety-integration-protocol.md) 规定模型代理与工具授权使用两条安全接口；完整阶段、故障矩阵和验收线见 [`docs/PROJECT-UPGRADE-ROADMAP.md`](docs/PROJECT-UPGRADE-ROADMAP.md)，任务依赖与验收命令见 [`docs/PROJECT-UPGRADE-TASKS.md`](docs/PROJECT-UPGRADE-TASKS.md)。

### 升级第一阶段实施（2026-08-06）

- 新增 [`deploy/local/docker-compose.yml`](deploy/local/docker-compose.yml)：本地 Core 使用 PostgreSQL 16、Redis 7、SeaweedFS 4.40 和 Qdrant 1.18.2；两个项目共享实例但隔离数据库/Redis DB。
- MinIO 社区仓库已归档，因此对象存储改为仍维护、Apache 2.0、支持 ARM64 的 SeaweedFS；业务只依赖 S3-compatible 契约。
- 新增 [`deploy/local/.env.example`](deploy/local/.env.example) 与 [`scripts/verify_local_stack.py`](scripts/verify_local_stack.py)，商业模型凭据默认空，Docker/服务异常输出机器可读 JSON 和非零退出码。
- 纪要君新增基础设施配置契约 `jiyaojun/app/config.py`；安全平台扩展 OpenAI-compatible 模型地址、模型名、超时、token、每日调用和月预算契约，`ModelProxy` 使用配置化超时与输出 token 上限。
- 修正 `ModelProxy` 白名单判定：`mock-llm` 在白名单中不再意外放行任意真实模型，真实模型必须逐项授权。
- 新增 9 项离线配置/健康检查单测；Compose `config`、四容器运行态健康、双数据库初始化、Qdrant API 与“停止单服务后明确失败、恢复后全绿”均已验证。

### M2.1 纪要君持久化（2026-08-06）

- `jiyaojun/migrations/002_app_runtime.sql`：应用运行时表（`app_meeting`、`app_session_journal_entry`、`app_task_projection`、`app_work_link`）。
- `jiyaojun/app/persistence/`：PostgreSQL 连接、幂等迁移、任务投影、`python -m app.persistence.migrate`。
- `PostgresJournalRepository` / `PostgresMeetingStore` / Redis `SessionProjectionCache` + `IdempotencyCache`；`app/runtime/factory.py` 按 env 切换。
- postgres 模式下 `DialogSessionService.with_settings` 通过 `TaskProjectionJournalHook` 同步写 `app_task_projection`，并按配置装配调度器。
- 默认 `storage_backend=memory`、`redis_backend=memory`；离线门禁全绿，集成测试在 Core 起来后跑。

### M2.2 Celery Worker（2026-08-06）

- `JIYAOJUN_SCHEDULER_BACKEND=memory|celery`（默认 memory）；`build_scheduler` 切换 `InProcessScheduler` / `CeleryScheduler`。
- Celery broker/result 使用 Redis DB2（`JIYAOJUN_CELERY_BROKER_URL=redis://127.0.0.1:56379/2`）；纪要君缓存仍用 DB1。
- `run_pipeline_job` 长流水线任务；`IdempotencyCache` 防重复写回；`app_task_projection` 可选持久化。
- Compose 可选 profile `worker`；`DialogSessionService.with_settings` 已按配置切换调度器。
- **边界**：`DialogSessionService` 默认进程内调度；Celery 生产需独立 Worker。M3 安全接入已完成。

### M2.3 Qdrant / SeaweedFS（2026-08-06）

- `JIYAOJUN_VECTOR_BACKEND=memory|qdrant`、`JIYAOJUN_OBJECT_BACKEND=mock|s3`；factory 提供 `build_vector_index` / `build_object_store`。
- `QdrantHybridIndex`：ACL-first payload 过滤 + dense 检索 + sparse 应用侧重排；`S3ObjectStore` 对接 SeaweedFS path-style。
- 集成测试覆盖重启后可检索、ACL 负例空召回、对象上传下载一致性。

### M3 纪要君单向接入安全控制面（2026-08-06）

- `jiyaojun/app/safety/`：出站门禁、预算、离线/HTTP 网关、双重授权、`SafetyRoutedLLMClient`。
- 模型只走 `/v1/chat/completions`；工具在业务授权后走 **`/v1/tools/authorize`（干跑）**，本地再执行；取更严格结果（ADR-0001/0004）。
- `confidential/critical` 出站时 `external_provider_calls=0`；网关不可用 fail-closed，不得扩大业务权限。
- 默认无 `JIYAOJUN_SAFETY_GATEWAY_URL` → `OfflineSafetyGateway`；`run_all` 全绿。
- 安全平台：`ToolRuntime.authorize` + `POST /v1/tools/authorize`。
- 验收：`pytest jiyaojun/tests/safety/test_m3_safety_gateway.py`、`llm-safety-platform/tests/test_tools_authorize.py`。

### M5 身份 / 密钥 / 观测 / 故障矩阵（2026-08-06）

- Compose 可选 profile：`identity`（Keycloak）、`secrets`（OpenBao）、`observability`（OTel/Prometheus/Grafana/Tempo）。
- `jiyaojun/app/observability/telemetry.py`：模型 / RAG / HITL / 工具授权 / 写回 span；可选 `JIYAOJUN_OTEL_ENDPOINT` OTLP 导出。
- `python -m app.eval.fault_matrix`：7 类强制故障（超时、Qdrant、Worker 重启、重复 webhook、PG 不可用、安全阻断、预算耗尽），各含终态/审计/指标/恢复说明；已纳入 `run_all`。
- 安全平台：`audit_lock.simulate_dual_writer_fork` 证明双副本分叉可检测；可选 `SAFETY_AUDIT_ADVISORY_LOCK=1`。

### M6 质量与交付（2026-08-06）

- RAG 黄金集 **70** 条、Agent 故事 **30**、ACL/密封/跨域负例 **22**；`python -m app.eval.m6_quality_gates` 校验规模 + 性能（安全 P99≤80ms、RAG P95≤500ms、流水线 P95≤120s）。
- 一键：`scripts/demo_one_click.sh` / `scripts/demo_faults.sh`；手册 [`docs/ops/OPERATOR-MANUAL.md`](docs/ops/OPERATOR-MANUAL.md)；证据模板 [`docs/ops/EVIDENCE-REPORT.md`](docs/ops/EVIDENCE-REPORT.md)；kind+Helm [`docs/ops/KIND-HELM.md`](docs/ops/KIND-HELM.md)。
- 商业 Judge：`sample_limit=100`，发布前 `SAFETY_JUDGE_SAMPLE_LIMIT=300`；无 URL 时 skip。
