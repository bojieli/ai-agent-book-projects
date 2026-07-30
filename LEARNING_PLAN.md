# 《深入理解 AI Agent》学习计划 v2

> **核心公式**：Agent = LLM + 上下文 + 工具
> **设计哲学**：上下文决定上限，工具决定边界，Harness 决定可靠性
> **三条更新路径**：上下文适应（即时）→ 外部产物更新（中期）→ 参数更新（长期）
> **立场**：方向认同，节奏务实——模型每内化一层，Harness 就卸下一层，同时兜住新的能力前沿

总计：10 章正文 + 92 个配套实验（70+ 可独立运行）
预计周期：12 周（每周 8-10 小时）

---

## 前置准备

### API Key 申请（第 1 周前完成）

| 平台 | 用途 | 必要性 |
| :---: | --- | :---: |
| [SiliconFlow](https://siliconflow.cn/) | 开源模型（DeepSeek/Qwen），免费额度 | ⭐ 必需 |
| [Kimi（月之暗面）](https://platform.moonshot.cn/) | Kimi 系列，Agent 能力强 | ⭐ 必需 |
| [智谱 GLM](https://open.bigmodel.cn/) | GLM-5.2，Agent 能力强 | 推荐 |
| [DeepSeek](https://platform.deepseek.com/) | DeepSeek 官方 API | 推荐 |
| [OpenRouter](https://openrouter.ai/) | 一站式多模型访问 | 可选 |

### 环境准备

```bash
cd ~/Desktop/ai-agent-book
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-docs.txt 2>/dev/null
```

### 认知锚点（开始前必须刻进脑子）

学这本书不是学 10 章内容，是围绕一个公式长出直觉：

```
Agent = LLM + 上下文 + 工具
         ↑       ↑        ↑
       大脑    眼睛     手脚
```

每学完一周，回来问自己：这一周的内容，对应公式的哪个变量？如果答不出来，说明没学到位。

---

## 阶段一：建立公式（第 1-3 周）

> **目标**：把 Agent = LLM + 上下文 + 工具 这个公式从文字变成直觉
> **对应**：第 1 章（基础）+ 第 2 章（上下文工程）+ 第 3 章（记忆与知识库）

### Week 1 — 公式的三个变量

| 日 | 任务 | 类型 | 对应变量 | 预计时长 |
| :--: | --- | :---: | :---: | :---: |
| D1 | 📖 阅读 `book/chapter1.md`（Agent 基础知识） | 阅读 | 全局 | 2h |
| D2 | 🧪 运行实验 1-1：`chapter1/context/` — 上下文消融实验 | 实验 | 上下文 | 2h |
| D3 | 📖 阅读 `book/chapter2.md` 前半（KV Cache + 提示工程） | 阅读 | 上下文 | 2h |
| D4 | 🧪 运行实验 2-3：`chapter2/kv-cache/` — KV Cache 探索 | 实验 | 上下文 | 1.5h |
| D5 | 🧪 运行实验 2-4：`chapter2/prompt-engineering/` — 提示工程量化 | 实验 | 上下文 | 2h |

**本周检验**：能画出 Agent 的五部分上下文结构图（静态前缀 + 轨迹），并说出每个部分缺失后会发生什么。

### Week 2 — 上下文：Agent 的眼睛

| 日 | 任务 | 类型 | 核心问题 | 预计时长 |
| :--: | --- | :---: | --- | :---: |
| D1 | 📖 阅读 `book/chapter2.md` 后半（Agent Skills + 状态栏 + 压缩） | 阅读 | 上下文怎么管才不膨胀？ | 2h |
| D2 | 🧪 运行实验 2-6：`chapter2/agent-skills-ppt/` — 按需加载 Skill | 实验 | 工具列表膨胀怎么办？ | 2h |
| D3 | 🧪 运行实验 2-9：`chapter2/context-compression/` — 压缩策略对比 | 实验 | 信息太多怎么办？ | 2h |
| D4 | 🧪 运行实验 2-5：`chapter2/prompt-injection/` — 注入攻防 | 实验 | 上下文的安全边界在哪？ | 2h |
| D5 | 📝 制作知识卡片：上下文工程 6 维度（KV Cache / 提示 / Skills / 状态栏 / 压缩 / 安全） | 总结 | — | 1.5h |

**本周检验**：能回答"上下文决定上限"这句话——为什么去掉任何一个组件，Agent 就废了？

### Week 3 — 跨会话的记忆

| 日 | 任务 | 类型 | 核心问题 | 预计时长 |
| :--: | --- | :---: | --- | :---: |
| D1 | 📖 阅读 `book/chapter3.md`（用户记忆 + RAG 全章） | 阅读 | Agent 怎么跨会话记住东西？ | 2.5h |
| D2 | 🧪 运行实验 3-1/3-2：`chapter3/user-memory/` — 用户记忆系统 | 实验 | 记忆 = 上下文的延伸 | 2h |
| D3 | 🧪 运行实验 3-6：`chapter3/retrieval-pipeline/` — 混合检索 | 实验 | 外部知识怎么接入上下文？ | 2h |
| D4 | 🧪 运行实验 3-9：`chapter3/agentic-rag/` — Agentic RAG | 实验 | Agent 自己决定何时检索 | 2h |
| D5 | 📝 复盘 W1-W3：用公式重新审视所有实验 | 总结 | — | 1.5h |

**阶段一达标**：能解释 Agent 三要素、画出上下文五部分结构、说出 RAG 的三种模式。

---

## 阶段二：手脚与外壳（第 4-6 周）

> **目标**：掌握工具设计原则 + Harness 工程 + 评估方法论
> **核心认知**：工具是手脚，Harness 是缰绳——模型越强，缰绳越关键
> **对应**：第 4 章（工具）+ 第 5 章（Coding Agent）+ 第 6 章（评估）

### Week 4 — 工具：Agent 的手脚

| 日 | 任务 | 类型 | 核心问题 | 预计时长 |
| :--: | --- | :---: | --- | :---: |
| D1 | 📖 阅读 `book/chapter4.md`（工具全章） | 阅读 | 工具怎么设计才不乱用？ | 2.5h |
| D2 | 🧪 运行实验 4-1：`chapter4/perception-tools/` — 感知工具 | 实验 | Agent 能看到什么？ | 2h |
| D3 | 🧪 运行实验 4-2：`chapter4/execution-tools/` — 执行工具 | 实验 | Agent 能改变什么？ | 2h |
| D4 | 🧪 运行实验 4-6：`chapter4/active-tool-discovery/` — 按需发现 | 实验 | 工具太多怎么选？ | 1.5h |
| D5 | 🧪 运行实验 4-5：`chapter4/async-agent/` — 异步事件驱动 | 实验 | 事件触发 ≠ 主动调用 | 2h |

**本周检验**：能说出五类工具（感知/执行/协作/事件触发/用户沟通）的区别，以及 MCP 标准化的意义。

### Week 5 — 代码：元工具 + Harness 实战

| 日 | 任务 | 类型 | 核心问题 | 预计时长 |
| :--: | --- | :---: | --- | :---: |
| D1 | 📖 阅读 `book/chapter5.md`（Coding Agent） | 阅读 | 为什么代码是最强的工具？ | 2.5h |
| D2 | 🧪 运行实验 5-1：`chapter5/code-for-math/` — 代码辅助推理 | 实验 | 代码 > 自然语言推理 | 2h |
| D3 | 🧪 运行实验 5-3：`chapter5/small-model-codified-rules/` — 规则代码化 | 实验 | 规则写进代码 > 写进 prompt | 2h |
| D4 | 🧪 运行实验 5-12：`chapter5/coding-agent/` — 生产级 Coding Agent | 实验 | Harness 怎么兜住代码执行？ | 2.5h |
| D5 | 📝 思考题：Harness 在 Coding Agent 里体现为哪些具体机制？ | 总结 | — | 1.5h |

**本周检验**：能解释"Harness 不是限制模型能力，是把能力引导到正确方向"——马具隐喻。

### Week 6 — 评估：科学方法的地基

| 日 | 任务 | 类型 | 核心问题 | 预计时长 |
| :--: | --- | :---: | --- | :---: |
| D1 | 📖 阅读 `book/chapter6.md`（Agent 评估） | 阅读 | 没有评估就没有进步 | 2.5h |
| D2 | 🧪 运行实验 6-7：`chapter6/agent-cost-analysis/` — 成本分析 | 实验 | 可靠性的代价是多少？ | 2h |
| D3 | 🧪 运行实验 6-8：`chapter6/model-benchmark/` — 模型横评 | 实验 | 怎么选模型？ | 2h |
| D4 | 🧪 运行实验 6-6：`chapter6/elo-leaderboard/` — ELO 排行榜 | 实验 | Agent 之间怎么比？ | 1.5h |
| D5 | 📝 复盘 W4-W6：工具 + Harness + 评估的三角关系 | 总结 | — | 1.5h |

**阶段二达标**：能独立搭建 MCP 工具、理解 Harness 的三层含义（约束/验证/纠正）、会做 Agent 评估。

---

## 阶段三：三条更新路径（第 7-9 周）

> **目标**：理解 Agent 能力更新的三条路径——上下文适应、外部产物、参数更新
> **核心认知**：三者不是互斥分类，是不同时间尺度的协同机制
> **对应**：第 7 章（参数更新）+ 第 8 章（外部产物更新）+ 第 9 章（多模态）

### Week 7 — 参数更新：后训练

| 日 | 任务 | 类型 | 更新路径 | 预计时长 |
| :--: | --- | :---: | :---: | :---: |
| D1 | 📖 阅读 `book/chapter7.md` 前半（预训练 + SFT） | 阅读 | 参数更新（长期） | 2.5h |
| D2 | 🧪 运行实验 7-9：`chapter7/cot-distillation/` — CoT 蒸馏 | 实验 | 低成本获取推理能力 | 2h |
| D3 | 🧪 运行实验 7-5：`chapter7/continued-pretraining/` — 持续预训练 | 实验 | 领域知识怎么训进去？ | 2h |
| D4 | 📖 阅读 `book/chapter7.md` 后半（RL 部分） | 阅读 | SFT 记忆，RL 泛化 | 2h |
| D5 | 📝 对比笔记：SFT vs RL 各自适用什么场景？ | 总结 | — | 1.5h |

**本周检验**：能回答"SFT 记忆、RL 泛化"这句话——什么时候该用哪个。

### Week 8 — 外部产物更新：持续进化

| 日 | 任务 | 类型 | 更新路径 | 预计时长 |
| :--: | --- | :---: | :---: | :---: |
| D1 | 📖 阅读 `book/chapter8.md`（持续进化） | 阅读 | 外部产物更新（中期） | 2h |
| D2 | 🧪 运行实验 8-1：`chapter8/trajectory-verifier/` — 轨迹诊断 | 实验 | 信号从哪来？ | 2h |
| D3 | 🧪 运行实验 8-3：`chapter8/prompt-auto-optimization/` — 自动优化 | 实验 | Prompt 怎么自动改进？ | 2h |
| D4 | 🧪 运行实验 8-5：`chapter8/self-modifying-agent/` — 自修改 | 实验 | Agent 能改自己的代码吗？ | 2.5h |
| D5 | 📝 四种更新载体对比：知识文档 / Prompt+Skill / 程序+Harness / 参数 | 总结 | — | 2h |

**本周检验**：能画出四种更新载体的对比表（可审计性、可回滚性、泛化能力、部署成本）。

### Week 9 — 多模态：上下文的物理延伸

| 日 | 任务 | 类型 | 更新路径 | 预计时长 |
| :--: | --- | :---: | :---: | :---: |
| D1 | 📖 阅读 `book/chapter9.md`（多模态与实时交互） | 阅读 | 上下文从文本扩展到语音/GUI/物理世界 | 2.5h |
| D2 | 🧪 运行实验 9-1：`chapter9/live-audio/` — 实时语音 | 实验 | 语音 Agent 的全链路 | 2h |
| D3 | 🧪 运行实验 9-4：`chapter9/end-to-end-speech/` — 端到端语音 | 实验 | 级联 vs 端到端 | 2h |
| D4 | 🧪 运行实验 9-5：`chapter9/controllable-tts/` — 可控 TTS | 实验 | 副语言标记怎么控制表达？ | 2h |
| D5 | 📝 复盘 W7-W9：三条更新路径如何协同？ | 总结 | — | 1.5h |

**阶段三达标**：能区分 SFT/RL 适用场景、能画出四种更新载体对比表、理解多模态是上下文的延伸而非新维度。

---

## 阶段四：群体与实战（第 10-12 周）

> **目标**：多 Agent 协作 + 综合实战，把公式用活
> **核心认知**：多 Agent 的每个设计决策都能映射到单 Agent 三要素
> **对应**：第 10 章（多 Agent）+ 跨章综合

### Week 10 — 多 Agent：公式的乘法

| 日 | 任务 | 类型 | 核心问题 | 预计时长 |
| :--: | --- | :---: | --- | :---: |
| D1 | 📖 阅读 `book/chapter10.md`（多 Agent 协作） | 阅读 | 多个 Agent 怎么分工？ | 2.5h |
| D2 | 🧪 运行实验 10-1：`chapter10/staged-system-prompt/` — 分阶段提示 | 实验 | 同一 Agent 在不同阶段用不同上下文 | 2h |
| D3 | 🧪 运行实验 10-3：`chapter10/book-translation/` — 管理者模式 | 实验 | 上下文共享 vs 隔离 | 2h |
| D4 | 🧪 运行实验 10-6：`chapter10/parallel-web-research/` — 并行搜索 | 实验 | N 个同构 Agent 怎么协调？ | 2h |
| D5 | 🧪 运行实验 10-8：`chapter10/voice-werewolf/` — 狼人杀 | 实验 | 上下文隔离的极致演示 | 2h |

**本周检验**：能说出多 Agent 协作的三种模式（共享上下文/独立上下文/管理者模式）各自适合什么场景。

### Week 11 — 跨章补全 + 深度实验

| 日 | 任务 | 类型 | 跨章价值 | 预计时长 |
| :--: | --- | :---: | --- | :---: |
| D1 | 🧪 实验 3-11：`chapter3/contextual-retrieval/` — 上下文感知检索 | 实验 | 上下文 × 知识库交叉 | 2h |
| D2 | 🧪 实验 3-8：`chapter3/structured-index/` — RAPTOR vs GraphRAG | 实验 | 知识组织的两种范式 | 2h |
| D3 | 🧪 实验 8-4：`chapter8/browser-use-rpa/` — 浏览器 RPA | 实验 | 工具 × 进化交叉 | 2h |
| D4 | 🧪 实验 5-4：`chapter5/paper-to-ppt/` — 论文转 PPT | 实验 | 代码作为元工具的实用场景 | 2h |
| D5 | 📝 全书实验复盘：每个实验对应公式的哪个变量？ | 总结 | — | 2h |

### Week 12 — 综合实战 + 输出

| 日 | 任务 | 类型 | 预计时长 |
| :--: | --- | :---: | :---: |
| D1 | 🏗️ 三选一部署：`coding-agent` / `agentic-rag` / `async-agent` | 实战 | 3h |
| D2 | 🏗️ 加自定义工具（MCP）或记忆模块，观察三变量如何联动 | 实战 | 3h |
| D3 | 📝 用公式审视全书：每章 3 句话 + 1 个最有价值的实验 | 输出 | 2h |
| D4 | 📝 制作个人 Agent 设计检查清单（基于三变量框架） | 输出 | 2h |
| D5 | 🎯 制定下一步：选定一个 Agent 项目动手做 | 规划 | 1h |

---

## 实验速查表（按公式变量分类）

### 上下文变量 🧠

| 编号 | 实验 | 核心价值 |
| :--: | --- | --- |
| ⭐ 1-1 | context 消融 | 上下文五部分各自不可替代 |
| ⭐ 2-4 | prompt-engineering | 提示工程可量化优化 |
| ⭐ 2-9 | context-compression | 不丢能力的压缩策略 |
| ⭐ 3-1 | user-memory | 跨会话记忆 = 上下文的延伸 |
| ⭐ 3-6 | retrieval-pipeline | 外部知识接入上下文 |
| ⭐ 3-9 | agentic-rag | Agent 自主决定何时检索 |

### 工具变量 🤲

| 编号 | 实验 | 核心价值 |
| :--: | --- | --- |
| ⭐ 4-1 | perception-tools | MCP 协议落地 |
| ⭐ 4-6 | active-tool-discovery | 按需发现 > 全量注入 |
| ⭐ 5-1 | code-for-math | 代码是最强的工具 |
| ⭐ 5-12 | coding-agent | 生产级 Harness 实战 |

### Harness + 评估 🔧

| 编号 | 实验 | 核心价值 |
| :--: | --- | --- |
| ⭐ 6-7 | agent-cost-analysis | 可靠性的代价 |
| ⭐ 6-8 | model-benchmark | 模型选型方法论 |
| ⭐ 8-3 | prompt-auto-optimization | 自动化 Prompt 改进 |
| ⭐ 8-5 | self-modifying-agent | Agent 自修改的边界 |

### 三条更新路径 🔄

| 编号 | 实验 | 更新路径 |
| :--: | --- | :---: |
| ⭐ 7-9 | cot-distillation | 参数更新 |
| ⭐ 8-1 | trajectory-verifier | 外部产物（信号提取） |
| ⭐ 9-1 | live-audio | 上下文延伸（多模态） |

### 多 Agent 👥

| 编号 | 实验 | 核心价值 |
| :--: | --- | --- |
| ⭐ 10-1 | staged-system-prompt | 分阶段 = 不同上下文 |
| ⭐ 10-3 | book-translation | 管理者模式实践 |
| ⭐ 10-6 | parallel-web-research | 并行 Agent 架构 |
| ⭐ 10-8 | voice-werewolf | 上下文隔离的极致演示 |

---

## 学习方法论

### 每个实验的标准流程

```
1. 读 README → 这个实验在验证公式的哪个变量？
2. 安装依赖 → 按 README 指引
3. 运行实验 → 观察输出，记录关键数字
4. 改参数重跑 → 改 1-2 个变量，观察变化
5. 写笔记 → 三句话：做了什么 / 发现了什么 / 对应公式的哪个部分
```

### 笔记模板

```markdown
## [实验编号] [实验名]

**做了什么**：
**关键发现**：
**对应公式的变量**：LLM / 上下文 / 工具 / Harness（勾选）
**与拆书结论的对应**：
**我的疑问**：
```

### 每周复盘必答题

1. 这周学的内容，对应 Agent = LLM + 上下文 + 工具 的哪个变量？
2. 这个变量的上限在哪？瓶颈是什么？
3. Harness 在这里扮演什么角色？

---

## 里程碑检查点

| 周 | 检查点 | 达标标准（用拆书结论检验） |
| :--: | --- | --- |
| W3 | 🟢 公式建立 | 能画出上下文五部分结构图，能解释"上下文决定上限" |
| W6 | 🔵 工程掌握 | 能独立搭 MCP 工具，能解释 Harness 三层含义，会做评估 |
| W9 | 🟣 路径理解 | 能画出四种更新载体对比表，能区分 SFT/RL 适用场景 |
| W12 | 🔴 综合运用 | 能用公式审视任何 Agent 系统，能独立设计多 Agent 方案 |

---

## 附录：推荐补充资源

- [Karpathy: LLM 上下文工程](https://www.youtube.com/watch?v=bO7FirUcT9w) — 上下文工程的直觉来源
- [Anthropic: Building Effective Agents](https://docs.anthropic.com/en/docs/build-with-claude/agentic-patterns) — Agent 设计模式
- [Sutton: The Bitter Lesson](http://www.incompleteideas.net/IncIdeas/BillB.html) — 理解"方向认同，节奏务实"的背景
- [MCP 协议文档](https://modelcontextprotocol.io/) — 工具标准化
- [OpenAI Agents SDK](https://openai.github.io/agents-sdk/) — 生产级 Agent 框架参考

---

*拆书文件：`~/Documents/notes/20260728T091721--拆书-深入理解AIAgent__book.org`*
*更新时间：2026-07-28（v2，基于拆书结论重构）*
*仓库地址：`~/Desktop/ai-agent-book/`*
