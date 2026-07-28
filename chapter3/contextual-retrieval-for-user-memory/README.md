# Experiment 3-12: Contextual Retrieval for User Memory / 实验 3-12：利用上下文感知检索增强用户记忆

> Companion material for *AI Agents in Depth*, Chapter 3 — dual-layer memory: Contextual RAG + Advanced JSON Cards.  
> 配套《深入理解 AI Agent》第 3 章——双层记忆：上下文感知 RAG + Advanced JSON Cards。

← [Chapter 3 index / 返回第 3 章目录](../README.md)

---

## English

### What this experiment is

Applying contextual retrieval to user memory addresses a core pain point of naive conversation chunking and steps toward higher-level memory. This project implements a dual-layer memory system:

1. **Contextual Retrieval (Contextual RAG)**: precise retrieval over conversation history  
2. **Advanced JSON Cards**: structured storage of core facts  

### Latest updates

#### LLM-Based Memory Card Generation
- **Auto extract**: LLM extracts structured memory cards from conversations  
- **Full structure**: each card includes backstory, person, relationship, and related fields  
- **Graceful fallback**: falls back to keyword extraction when the LLM is unavailable  

#### LLM Judge Integration
- **Auto evaluation**: LLM Judge scores agent answers automatically  
- **Dual path**: import evaluation module or call the API directly  
- **Detailed feedback**: 0–1 score, pass/fail, and reasoning  

#### Enhanced Debugging
- **Memory card dump**: prints full JSON of all memory cards during evaluation  
- **Test case sorting**: test cases listed alphabetically by name  
- **Eval transparency**: clearly shows whether LLM Judge is in use  

### Core ideas

#### 1. Context-enriched conversation chunking

Traditional chunking drops context. An isolated fragment like “OK, book that one” means little until you know the prior turn discussed “a one-way Shanghai→Seattle flight for $500.”

Before indexing conversation history, the system adds a **context generation** step:

- Each conversation chunk gets an LLM-generated prefix summary with key background  
- Context includes time, people, intent, and other cues  
- Greatly improves retrieval accuracy and relevance  

#### 2. Dual-layer memory

**Advanced JSON Cards (always-on memory)**

- Structured, summarized core facts  
- Always fixed in the Agent’s context  
- Metadata such as backstory (source) and relationship (related people)  
- Example: “User Jessica’s passport expires on 2025-02-18”  

**Contextual RAG (on-demand retrieval)**

- Precise access to unstructured raw dialogue detail  
- Quickly finds full context of a specific discussion  
- Acts as “evidence” for decisions  

#### 3. LLM-based memory extraction

The system can extract structured memory cards from dialogue:

```python
# Auto-generate memory cards from conversation
cards = indexer._generate_summary_cards(chunks, conversation_id)

# Example card:
{
    "category": "financial",
    "card_key": "bank_account_primary", 
    "backstory": "用户在开设账户时提供了银行信息",
    "date_created": "2024-01-15 10:30:00",
    "person": "John Smith (primary)",
    "relationship": "primary account holder",
    "bank_name": "Chase Bank",
    "account_type": "checking",
    "account_ending": "4567"
}
```

### Project structure

```
contextual-retrieval-for-user-memory/
├── contextual_chunking.py      # Context-aware chunking
├── advanced_memory_manager.py  # Advanced JSON card manager
├── contextual_indexer.py       # Dual-layer memory indexer (incl. LLM extract)
├── contextual_agent.py         # Agent combining dual-layer memory
├── contextual_evaluator.py     # Evaluation (incl. LLM Judge)
├── contextual_compare.py       # Offline compare: contextual vs plain recall (no API)
├── memory_qa_eval.json         # Controlled memory Q&A set for offline compare
├── main.py                     # Main entry (argparse; --mode compare offline)
├── config.py                   # Config
├── chunker.py                  # Base chunker
├── tools.py                    # Agent tools
└── requirements.txt            # Dependencies
```

### Install and configure

#### 1. Install dependencies

```bash
pip install -r requirements.txt
```

#### 2. Environment variables

Create a `.env` file:

```bash
# LLM Provider Configuration
MOONSHOT_API_KEY=your_api_key_here
ARK_API_KEY=your_api_key_here
SILICONFLOW_API_KEY=your_api_key_here
OPENAI_API_KEY=your_api_key_here

# Default Provider
LLM_PROVIDER=kimi  # Options: kimi, doubao, siliconflow, openai

# Model Settings
LLM_MODEL=kimi-k3  # or another model
```

#### 3. Start the retrieval pipeline (for full e2e eval)

```bash
cd ../retrieval-pipeline
python api_server.py
```

### Usage

#### Offline compare: does contextualization help? (no API; recommended first)

Core claim: **before embedding/indexing memory chunks, generating a “context prefix” per chunk improves recall of out-of-context fragments** (e.g. “OK, book that one”). `--mode compare` is a **fully offline, no API key / no retrieval service** controlled experiment.

It measures “plain” (no prefix) vs “contextual” (prefix then index) on the same context; the only variable is whether the indexed text includes the context prefix. Retrieval is deterministic pure-Python BM25 as an offline stand-in for neural embeddings. Dataset: [`memory_qa_eval.json`](memory_qa_eval.json) (teaching set; override with `--dataset`).

```bash
# Print comparison metrics (Recall@1 / Recall@3 / MRR)
python main.py --mode compare
# Equivalent standalone script:
python contextual_compare.py

# Single-query plain vs contextual Top-K
python main.py --mode compare --query '我最后确认预订的那张机票是哪个航班？'

# Save full results (per-query ranks) to JSON
python main.py --mode compare --output results/compare.json
```

Measured output (12 memory chunks, 8 queries):

```
方法                            Recall@1  Recall@3       MRR
--------------------------------------------------------------------
Plain（直接索引原始块）               0.625     1.000     0.792
Contextual（上下文化后索引）        0.750     1.000     0.875
--------------------------------------------------------------------
提升（Δ）                         +0.125    +0.000    +0.083
```

For queries like “is my Seattle hotel confirmed,” the gold chunk (“yes, book it”) ranks 3rd under Plain and 1st after contextualization—the prefix re-anchors an isolated confirmation to “Hyatt Seattle.”

> Note: this is an **offline lexical proxy** to show mechanism and directional gain without APIs. In production, prefixes are LLM-generated per chunk and indexed with neural embeddings + hybrid search (see `--mode evaluate` below), which needs an API key.

#### End-to-end evaluation (needs API / retrieval service)

```bash
# Interactive UI (default)
python main.py

# Evaluate a category (needs LLM + retrieval pipeline)
python main.py --mode evaluate --category layer1

# Ablate contextualization; set model and output
python main.py --mode evaluate --category layer1 --no-contextual --model gpt-5.6-luna --output results/plain_eval.json
```

Full CLI: `python main.py --help` (includes Chinese descriptions).

#### Interactive menu

Run `python main.py`:

```
Main Menu:
1. 🚀 Demo Mode (Quick Start)
2. 📚 Load & Index Conversations
3. 🎴 Manage Memory Cards
4. 🔍 Test Query
5. 📊 Evaluate All Test Cases (by Category) [LLM Judge]
6. 🎯 Evaluate Specific Test Case [LLM Judge]
7. 📈 Show Statistics
8. ⚙️  Configure Settings
0. Exit
```

#### Evaluation output example

```
============================================================
DEBUG: All Memory Cards in System
============================================================

[financial.bank_account_primary]
{
  "backstory": "用户开设银行账户时提供的信息",
  "date_created": "2024-06-12 14:30:00",
  "person": "Michael James Robertson (primary)",
  "relationship": "primary account holder",
  "bank_name": "First National Bank",
  "account_number": "4429853327",
  "routing_number": "123006800"
}

Total Memory Cards: 5
============================================================

LLM Judge Evaluation Results
============================================================
Reward: 1.000/1.000
Passed: Yes
Reasoning: The agent correctly provided the checking account number...
============================================================
```

### Workflow example

When the user asks “Anything else to prepare for my January Tokyo trip?”:

1. **Fact review**: Agent inspects Advanced JSON Cards  
   - Finds “Tokyo trip” (departs Jan 25)  
   - Finds “passport” (expires Feb 18)  

2. **Link and reason**: compares core facts  
   - Flags passport expiry near flight date  

3. **Detail check**: starts RAG  
   - Searches dialogue chunks about passport / Tokyo flights  
   - Loads full original discussion  

4. **Proactive service**: both memory layers  
   - Advises: “Your passport is about to expire; strongly consider expedited renewal.”  

5. **Auto eval**: LLM Judge  
   - Score: 0.95/1.0  
   - Reason: correctly identified risk and gave appropriate advice  

### References

- [Anthropic's Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
- [RAG survey](https://arxiv.org/abs/2005.11401)
- [Memory Systems in AI Agents](https://arxiv.org/abs/2203.14680)
- [LLM as Judge](https://arxiv.org/abs/2306.05685)

### License

MIT License

---

## 中文

### 本实验是什么

将上下文感知检索技术应用于用户记忆的构建，是解决传统对话历史分块所面临的核心痛点，并迈向更高层次记忆能力的关键。本项目实现了一个双层记忆系统，结合了：

1. **上下文感知检索（Contextual RAG）**：对话历史的精准检索  
2. **高级 JSON 卡片（Advanced JSON Cards）**：结构化的核心事实存储  

### 最新更新

#### LLM-Based Memory Card Generation
- **自动提取**：使用 LLM 从对话中智能提取结构化记忆卡片  
- **完整结构**：每张卡片包含 backstory、person、relationship 等必要字段  
- **智能降级**：当 LLM 不可用时自动降级到关键词提取  

#### LLM Judge Integration  
- **自动评估**：集成 LLM Judge 对 Agent 回答进行自动评分  
- **双路径支持**：支持导入模块或直接 API 调用  
- **详细反馈**：提供 0-1 分数、通过/失败状态和评估理由  

#### Enhanced Debugging
- **内存卡片可视化**：评估时自动打印所有记忆卡片的完整 JSON  
- **测试用例排序**：按名称字母顺序显示测试用例  
- **评估透明度**：清晰显示 LLM Judge 使用状态  

### 核心创新

#### 1. 上下文增强的对话分块

传统的对话分块会丢失上下文信息。例如，一段孤立的对话片段“好的，就订这个吧”本身毫无信息量。只有知道上文是在讨论“从上海到西雅图的、价格为500美元的单程机票”，这段对话才有意义。

本系统在索引对话历史之前，增加了关键的“上下文生成”步骤：

- 每个对话块都会调用 LLM 生成包含关键背景信息的前缀摘要  
- 上下文包括时间、人物和意图等关键线索  
- 极大提升了检索的准确性和相关性  

#### 2. 双层记忆结构

**Advanced JSON Cards（常驻记忆）**

- 存储结构化的、总结性的核心事实  
- 始终固定在 Agent 的上下文中  
- 包含 backstory（信息来源）和 relationship（关联人员）等元数据  
- 如：“用户 Jessica 的护照将于2025年2月18日过期”  

**Contextual RAG（按需检索）**

- 提供对非结构化的原始对话细节的精准访问  
- 快速找到具体讨论的完整上下文  
- 作为决策的“证据”支持  

#### 3. LLM-Based Memory Extraction

系统现在能够从对话中智能提取结构化记忆卡片：

```python
# 自动从对话生成记忆卡片
cards = indexer._generate_summary_cards(chunks, conversation_id)

# 生成的卡片示例：
{
    "category": "financial",
    "card_key": "bank_account_primary", 
    "backstory": "用户在开设账户时提供了银行信息",
    "date_created": "2024-01-15 10:30:00",
    "person": "John Smith (primary)",
    "relationship": "primary account holder",
    "bank_name": "Chase Bank",
    "account_type": "checking",
    "account_ending": "4567"
}
```

### 项目结构

```
contextual-retrieval-for-user-memory/
├── contextual_chunking.py      # 上下文感知分块
├── advanced_memory_manager.py  # 高级JSON卡片管理
├── contextual_indexer.py       # 双层记忆索引器（含LLM提取）
├── contextual_agent.py         # 结合双层记忆的Agent
├── contextual_evaluator.py     # 评估框架（含LLM Judge）
├── contextual_compare.py       # 离线对比脚本：上下文化 vs 原始块的召回（无需 API）
├── memory_qa_eval.json         # 离线对比用的受控记忆问答对照集
├── main.py                     # 主入口（argparse，含 --mode compare 离线对比）
├── config.py                   # 配置管理
├── chunker.py                  # 基础分块器
├── tools.py                    # Agent工具
└── requirements.txt            # 依赖项
```

### 安装与配置

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置环境变量

创建 `.env` 文件：

```bash
# LLM Provider Configuration
MOONSHOT_API_KEY=your_api_key_here
ARK_API_KEY=your_api_key_here
SILICONFLOW_API_KEY=your_api_key_here
OPENAI_API_KEY=your_api_key_here

# Default Provider
LLM_PROVIDER=kimi  # Options: kimi, doubao, siliconflow, openai

# Model Settings
LLM_MODEL=kimi-k3  # 或其他模型
```

#### 3. 启动检索管道服务

```bash
cd ../retrieval-pipeline
python api_server.py
```

### 使用示例

#### 离线对比：上下文化到底有没有用？（无需 API，推荐先跑这个）

本实验的核心论点是：**在把对话记忆块送入嵌入/索引前，先为每块生成一段『上下文前缀』，能提升脱离上下文的孤立片段（如『好的，就订这个吧』）的召回。** `--mode compare` 提供一个**完全离线、无需任何 API Key 或检索服务**的受控对照实验来量化这一点。

它用同一份上下文，分别度量『不拼接（plain）』与『拼接后再索引（contextual）』两种方式的召回，变量只有『索引文本是否含上下文前缀』，因此结果直接反映上下文化本身的贡献。检索采用确定性的 BM25 词法检索（纯 Python、无第三方依赖）作为神经嵌入的离线代理；对照数据集见 [`memory_qa_eval.json`](memory_qa_eval.json)（受控教学集，可用 `--dataset` 替换）。

```bash
# 打印对比指标表（Recall@1 / Recall@3 / MRR）
python main.py --mode compare
# 等价于直接运行独立脚本：
python contextual_compare.py

# 对单条查询做 plain vs contextual 的 Top-K 检索对比
python main.py --mode compare --query '我最后确认预订的那张机票是哪个航班？'

# 保存完整结果（含逐查询名次明细）到 JSON
python main.py --mode compare --output results/compare.json
```

实测输出（12 个记忆块、8 条查询的受控集）：

```
方法                            Recall@1  Recall@3       MRR
--------------------------------------------------------------------
Plain（直接索引原始块）               0.625     1.000     0.792
Contextual（上下文化后索引）        0.750     1.000     0.875
--------------------------------------------------------------------
提升（Δ）                         +0.125    +0.000    +0.083
```

其中『我订的西雅图酒店确认了吗』这类查询，gold 记忆块（『可以，帮我订下来』）在 Plain 下排名第 3、上下文化后升到第 1——正是上下文前缀把孤立确认片段重新锚定回了『西雅图凯悦酒店』的情境。

> 说明：这是一个**离线词法代理**，用于在无 API 环境下清晰地演示上下文化的机制与方向性收益。生产管线中，上下文前缀由 LLM 逐块生成、并用神经嵌入 + 混合检索索引（见下方 `--mode evaluate`），需要配置 API Key。

#### 端到端评估（需 API / 检索服务）

```bash
# 交互式界面（默认）
python main.py

# 评估特定分类（需 LLM 与检索管道服务）
python main.py --mode evaluate --category layer1

# 关闭上下文化做对照，并指定模型与输出
python main.py --mode evaluate --category layer1 --no-contextual --model gpt-5.6-luna --output results/plain_eval.json
```

完整命令行参数见 `python main.py --help`（含中文说明）。

#### 交互式测试界面

运行 `python main.py` 进入交互式界面：

```
Main Menu:
1. 🚀 Demo Mode (Quick Start)
2. 📚 Load & Index Conversations
3. 🎴 Manage Memory Cards
4. 🔍 Test Query
5. 📊 Evaluate All Test Cases (by Category) [LLM Judge]
6. 🎯 Evaluate Specific Test Case [LLM Judge]
7. 📈 Show Statistics
8. ⚙️  Configure Settings
0. Exit
```

#### 评估输出示例

```
============================================================
DEBUG: All Memory Cards in System
============================================================

[financial.bank_account_primary]
{
  "backstory": "用户开设银行账户时提供的信息",
  "date_created": "2024-06-12 14:30:00",
  "person": "Michael James Robertson (primary)",
  "relationship": "primary account holder",
  "bank_name": "First National Bank",
  "account_number": "4429853327",
  "routing_number": "123006800"
}

Total Memory Cards: 5
============================================================

LLM Judge Evaluation Results
============================================================
Reward: 1.000/1.000
Passed: Yes
Reasoning: The agent correctly provided the checking account number...
============================================================
```

### 工作流程示例

当用户询问“为我一月的东京之行，还有什么要准备的吗？”时：

1. **事实回顾**：Agent 首先审视 Advanced JSON Cards 中的内容  
   - 发现“东京之行”信息（1月25日出发）  
   - 发现“护照信息”（2月18日过期）  

2. **关联与推理**：通过对比核心事实  
   - 识别出机票日期与护照过期日期接近的风险  

3. **细节验证**：启动 RAG 检索  
   - 搜索与“护照”和“东京机票”相关的对话片段  
   - 获取原始讨论的所有细节  

4. **主动服务**：结合两种记忆  
   - 给出关键建议：“您的护照即将过期，强烈建议您立即加急办理续签”  

5. **自动评估**：LLM Judge 评估答案  
   - 评分：0.95/1.0  
   - 理由：正确识别风险并给出适当建议  

### 参考资料

- [Anthropic's Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)
- [RAG 技术综述](https://arxiv.org/abs/2005.11401)
- [Memory Systems in AI Agents](https://arxiv.org/abs/2203.14680)
- [LLM as Judge](https://arxiv.org/abs/2306.05685)

### 许可证

MIT License

---

## Notes / 说明

### OpenRouter 通用回退 / Universal OpenRouter fallback

This experiment supports a **universal OpenRouter fallback** for its chat LLM.

- If the primary provider key (e.g. `MOONSHOT_API_KEY` / `KIMI_API_KEY` / `OPENAI_API_KEY` / `DOUBAO_API_KEY` …) is present, behavior is unchanged.
- Else if `OPENROUTER_API_KEY` is set, the chat LLM is automatically routed through OpenRouter (`https://openrouter.ai/api/v1`). Model names are mapped automatically: `gpt-*`/`o1-*` → `openai/…`, `claude-*` → `anthropic/claude-opus-4.8`, `kimi-*` → `moonshotai/kimi-k2.6`, ids already containing `/` are kept as-is, and other provider-native ids (e.g. `doubao-*`) fall back to `openai/gpt-5.6-luna`. Set `OPENROUTER_MODEL` to force a specific OpenRouter model id.
- Else a clear error lists the accepted keys.

Add `OPENROUTER_API_KEY=...` to your `.env` (see `env.example`) to enable it.
