# Active Tool Selection / 主动工具选择

> Educational implementation of active tool discovery for LLM agents (MCP-Zero style), with measurable comparison of `all-tools` / `retrieval` / `active` strategies.  
> 面向 LLM Agent 的主动工具发现教学实现（MCP-Zero 风格），可度量对比 `all-tools` / `retrieval` / `active` 三种策略。

← [Chapter 4 index / 返回第 4 章目录](../README.md)

---

## English

An educational implementation of active tool discovery for LLM agents, inspired by the MCP-Zero paper ([arXiv:2506.01056](https://arxiv.org/pdf/2506.01056)).

### Overview

Traditional LLM agents inject all available tool schemas into prompts, creating massive context overhead and reducing agents to passive tool selectors. This project demonstrates **active tool discovery**, where agents autonomously identify capability gaps and request specific tools on-demand.

#### The Problem

Current tool integration approaches face critical limitations:

1. **Massive Context Overhead**: Injecting all tools can consume 100k+ tokens
2. **Passive Selection**: Agents select from pre-defined options rather than actively discovering
3. **Poor Scalability**: Context grows with ecosystem size, not task needs
4. **Lost Autonomy**: Tool selection delegated to external retrieval systems

#### The Solution: Active Tool Discovery

This project implements three core mechanisms from MCP-Zero:

1. **Active Tool Request**: Agents generate structured requests specifying their exact tool requirements
2. **Hierarchical Semantic Routing**: Two-stage matching algorithm (server-level → tool-level)
3. **Iterative Capability Extension**: Progressive toolchain building as task understanding evolves

### Strategy Comparison

This experiment turns tool selection into a measurable benchmark comparing three strategies on the **same task set**:

| Strategy | Description | Tools in context |
|------|------|----------------|
| `all-tools` | Inject all tools at once (traditional passive baseline) | All N tools |
| `retrieval` | Semantic top-k retrieval then inject (`RetrievalToolAgent`) | top-k only |
| `active` | MCP-Zero style active discovery: model iteratively requests tools (`ActiveToolAgent`) | grows on demand |

Entry point: `demo_comparison.py` with full argparse CLI:

```bash
# Offline only (deterministic, no API key): recall vs token cost vs scale
python demo_comparison.py --offline

# Pad catalog to 200 tools (synthetic distractors); watch token cost diverge
python demo_comparison.py --offline --num-tools 200

# End-to-end three-strategy compare (needs API key): correct tool calls, tokens, latency
python demo_comparison.py --strategy compare

# Single query, one strategy
python demo_comparison.py --query "Deploy version 2.0 to production" --strategy retrieval

# Save JSON results
python demo_comparison.py --offline --output results.json
```

Run `python demo_comparison.py --help` for all flags (`--strategy / --query / --num-tools /
--top-k / --model / --output / --offline / --legacy-demos`).

#### Offline benchmark (deterministic, no API)

`benchmark.py` provides a small labeled set (10 tasks, each with a ground-truth tool) and measures, **without any API call**:

- **Retrieval recall@k**: whether ground-truth tools land in the injected set
- **Schema tokens**: token cost of injected tool schemas (estimated from schema, deterministic)

Measured output of `python demo_comparison.py --offline` (top-k=5, 10 tasks):

| Strategy | Tools in context | Schema tokens | Recall (ground-truth reachable) |
|------|------|------|------|
| all-tools (full inject) | 35 | 3,857 | 100% |
| retrieval (top-5) | 5 | 551 | 100% |

As the catalog grows, `all-tools` token cost scales linearly; `retrieval` stays flat (measured):

| Catalog size | all-tools tokens | retrieval(top-5) tokens | retrieval recall |
|------|------|------|------|
| 35 | 3,857 | 551 | 100% |
| 100 | 10,292 | 539 | 100% |
| 200 | 20,258 | 540 | 100% |
| 400 | 40,258 | 540 | 100% |

> Conclusion: retrieval-style on-demand selection keeps 100% recall while cutting schema tokens from thousands to hundreds, and does not inflate with ecosystem size—quantitative evidence for “turn tool selection into knowledge retrieval.” Numbers are deterministic from `--offline`.

#### End-to-end accuracy (needs API key)

With `OPENAI_API_KEY` set, `--strategy compare` actually calls the model and measures whether each strategy **invokes the ground-truth tool** (accuracy), plus mean tokens and latency. Online only—not part of the offline path.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Active Tool Agent                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  1. Analyze Task & Identify Capability Gaps            │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  2. Generate Structured Tool Request                    │ │
│  │     <tool_request>                                      │ │
│  │       server: GitHub for repository operations          │ │
│  │       tool: search repositories by keyword              │ │
│  │     </tool_request>                                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Hierarchical Semantic Router                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Stage 1: Server-Level Routing                         │ │
│  │  • Match request to relevant servers/domains            │ │
│  │  • Filter by platform requirements                      │ │
│  │  • Return top-K servers                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Stage 2: Tool-Level Routing                           │ │
│  │  • Rank tools within selected servers                   │ │
│  │  • Semantic similarity matching                         │ │
│  │  • Return relevant tools                                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│               Tool Knowledge Base                            │
│                                                              │
│  8 Servers × 35 Tools (optionally padded with distractors): │
│  • GitHub: Repository management (5 tools)                  │
│  • Filesystem: File operations (5 tools)                    │
│  • Database: SQL operations (5 tools)                       │
│  • Web: HTTP requests (4 tools)                             │
│  • Analytics: Data analysis (4 tools)                       │
│  • Communication: Email/messaging (4 tools)                 │
│  • DevOps: Deployment/monitoring (4 tools)                  │
│  • Cloud: Infrastructure management (4 tools)               │
└─────────────────────────────────────────────────────────────┘
```

### Components

#### Core Files

- **`agent.py`**: Three agent implementations (one per strategy)
  - `ActiveToolAgent`: MCP-Zero style on-demand discovery (`active`)
  - `RetrievalToolAgent`: one-shot semantic retrieval of top-k tools (`retrieval`)
  - `PassiveToolAgent`: traditional approach with all tools pre-loaded (`all-tools`)

- **`benchmark.py`**: Labeled benchmark + offline evaluation
  - 10 tasks, each labeled with its ground-truth tool
  - `build_catalog(num_tools)`: real catalog, optionally padded with distractors
  - `evaluate_offline(...)`: deterministic recall@k / token-cost measurement (no API)

- **`tool_knowledge_base.py`**: Comprehensive tool catalog
  - 8 servers (domains) with 35 tools
  - Organized by platform/functionality
  - Simulates MCP ecosystem

- **`semantic_router.py`**: Hierarchical tool discovery
  - Two-stage semantic matching
  - TF-IDF based similarity
  - Structured request parsing

- **`config.py`**: Configuration settings
  - LLM provider settings
  - Routing thresholds
  - Agent parameters

#### Demo Scripts

- **`quickstart.py`**: Quick demonstration (⭐ Start here!)
- **`demo_comparison.py`**: Comprehensive comparison
- **`examples.py`**: Multiple use case examples

### Quick Start

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Configure API Key

```bash
cp env.example .env
# Edit .env and add your API key
```

> **Universal OpenRouter fallback**: if `OPENAI_API_KEY` is not set but
> `OPENROUTER_API_KEY` is, `config.py` automatically routes through OpenRouter
> (`base_url=https://openrouter.ai/api/v1`) and maps the model id to
> `provider/model` form (`gpt-*` → `openai/…`, `claude-*` →
> `anthropic/claude-opus-4.8`). Existing `OPENAI_BASE_URL`/`OPENAI_MODEL`
> overrides are preserved.

#### 3. Run Quick Start

```bash
python quickstart.py
```

This will demonstrate:
- Active tool discovery process
- Passive tool injection (for comparison)
- Efficiency metrics and insights

### Performance Comparison

See the measured, reproducible numbers in **Strategy Comparison** above.
The offline table (schema-token cost + retrieval recall) is generated deterministically by
`python demo_comparison.py --offline` — no API key required. End-to-end accuracy/latency across
the three strategies requires an API key (`--strategy compare`).

> Note: earlier drafts of this README quoted round illustrative figures for token savings. Those
> have been replaced with the actual measured output of the offline benchmark to avoid fabricated
> numbers.

### Key Concepts

#### Active Tool Request

Instead of pre-loading tools, agents explicitly request what they need:

```python
<tool_request>
server: GitHub for repository management
tool: search repositories by stars and language
</tool_request>
```

#### Hierarchical Semantic Routing

Two-stage algorithm reduces search complexity:

1. **Stage 1**: Match to relevant servers (platforms)
   - "GitHub operations" → GitHub server
   - "File management" → Filesystem server

2. **Stage 2**: Match to specific tools within servers
   - "search repositories" → `github_search_repos`
   - "read file" → `fs_read_file`

#### Iterative Capability Extension

Tools are discovered progressively:

```
Turn 1: Need GitHub access
  → Load GitHub tools

Turn 2: Need to analyze downloaded files
  → Additionally load filesystem tools

Turn 3: Need to visualize results
  → Additionally load analytics tools
```

Toolchain grows with task complexity, not ecosystem size.

### Examples

#### Example 1: Simple Task

```python
from agent import ActiveToolAgent

agent = ActiveToolAgent()
result = agent.execute_task("Search for Python ML repositories on GitHub")

# Agent discovers and loads only GitHub tools
print(f"Tools loaded: {result['metrics']['tools_loaded']}")  # 2-3 tools
print(f"Tokens used: {result['metrics']['tokens_used']}")    # ~2,000
```

#### Example 2: Multi-Domain Task

```python
task = """
1. Query database for user data
2. Analyze with statistics
3. Create visualization
4. Email report to team
"""

result = agent.execute_task(task)

# Agent builds cross-domain toolchain:
# Database → Analytics → Communication
print(f"Tools: {result['tools_loaded']}")
```

#### Example 3: Comparison

```python
from agent import ActiveToolAgent, PassiveToolAgent

# Active approach
active = ActiveToolAgent()
active_result = active.execute_task(task)

# Passive approach
passive = PassiveToolAgent()
passive_result = passive.execute_task(task)

# Compare efficiency
reduction = (1 - active_result['metrics']['tokens_used'] / 
             passive_result['metrics']['tokens_used']) * 100
print(f"Token reduction: {reduction:.1f}%")  # Typically 90-98%
```

### Running Demonstrations

#### 1. Quick Start (Recommended first)

```bash
python quickstart.py
```

Shows basic active vs passive comparison.

#### 2. Strategy Comparison Benchmark (main experiment)

```bash
python demo_comparison.py --offline   # deterministic, no API key needed
python demo_comparison.py             # + end-to-end accuracy/latency if API key present
```

By default it prints:
- Offline strategy table: retrieval recall@k vs. tool-schema token cost (deterministic)
- Scaling table: token cost as the catalog grows to hundreds of tools
- End-to-end table (with API key): accuracy / tokens / latency for `all-tools`, `retrieval`, `active`

The original narrative demos (semantic-routing walk-through, iterative discovery, etc.) are still
available via `--legacy-demos`. See the Strategy Comparison section and `python demo_comparison.py --help` for all flags.

#### 3. Use Case Examples

```bash
python examples.py
```

Demonstrates:
- GitHub workflow
- Data pipeline
- DevOps automation
- Multi-turn discovery
- Efficiency metrics

### Use Cases

#### Ideal for Active Discovery

1. **Task-Specific Operations**: Known scope, specific tools needed
2. **Large Tool Ecosystems**: 50+ tools where most are irrelevant
3. **Multi-Turn Conversations**: Tools needed evolve over time
4. **Token-Constrained Environments**: Limited context windows

#### When Passive Might Work

1. **Small Tool Sets**: <10 tools total
2. **All Tools Relevant**: Every tool likely to be used
3. **Single-Turn Tasks**: No iterative refinement

### Configuration

Edit `config.py` or set environment variables:

```python
# LLM Configuration
OPENAI_API_KEY = "your-api-key"
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-5.6-luna"

# Routing Configuration
SIMILARITY_THRESHOLD = 0.15  # Min similarity for tool match
TOP_K_SERVERS = 3            # Number of servers to search
TOP_K_TOOLS = 5              # Tools to return per server

# Agent Configuration
MAX_TOOL_REQUESTS = 5       # Max discovery iterations
```

### Educational Value

This project demonstrates:

#### Software Engineering Principles

- **Separation of Concerns**: Router, knowledge base, agent cleanly separated
- **Scalability**: Efficient with 10 or 1,000 tools
- **Modularity**: Easy to add new servers/tools

#### AI Agent Design Patterns

- **Active vs Passive**: Fundamental architectural difference
- **Hierarchical Search**: Reduces complexity from O(n) to O(log n)
- **Semantic Matching**: Beyond keyword matching

#### Real-World Applications

- **Tool Ecosystems**: MCP, LangChain, AutoGen
- **Agent Frameworks**: Building production-ready agents
- **Context Management**: Handling long contexts efficiently

### Technical Details

#### Semantic Routing Implementation

Uses TF-IDF vectorization with cosine similarity:

```python
# Server-level
server_vector = vectorizer.transform([request])
similarities = cosine_similarity(server_vector, server_embeddings)

# Tool-level
tool_vector = vectorizer.transform([request])
tool_similarities = cosine_similarity(tool_vector, tool_embeddings)

# Combined score
final_score = 0.3 * server_score + 0.7 * tool_score
```

#### Token Estimation

Approximates tokens in tool schemas:

```python
def count_tokens_in_schema(schema):
    # Rough estimation: 1 token ≈ 4 characters
    schema_str = json.dumps(schema)
    return len(schema_str) // 4
```

### Key Insights

1. **Autonomy Matters**: Agents should control their capability acquisition
2. **Context is Expensive**: Every token counts at scale
3. **Semantic Matching Works**: TF-IDF sufficient for tool discovery
4. **Iteration Enables Flexibility**: Static tool sets can't anticipate needs
5. **Hierarchical Search Scales**: Two-stage routing maintains performance

### References

- **MCP-Zero Paper**: [arXiv:2506.01056](https://arxiv.org/pdf/2506.01056)
- **Model Context Protocol**: [Official Repository](https://github.com/modelcontextprotocol)
- **Tool Learning Survey**: [ACM Computing Surveys](https://dl.acm.org/doi/10.1145/3708498)

### Extending the Project

#### Add New Tools

```python
# In tool_knowledge_base.py
new_tool = ToolDefinition(
    name="your_tool_name",
    description="What the tool does",
    parameters={...},
    server="server_name"
)
```

#### Add New Server

```python
# Create tools for the server
tools = [...]

# Add server
servers.append(ServerDefinition(
    name="your_server",
    description="Server description",
    tools=tools
))
```

#### Customize Routing

```python
# In config.py
SIMILARITY_THRESHOLD = 0.5  # More strict matching
TOP_K_SERVERS = 5           # Search more servers
```

### Troubleshooting

#### API Key Issues

```bash
# Verify .env file
cat .env

# Should contain:
OPENAI_API_KEY=sk-...
```

#### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

#### Low Similarity Scores

```bash
# Lower threshold in config.py
SIMILARITY_THRESHOLD = 0.2
```

### Future Enhancements

Potential improvements:

1. **Better Embeddings**: Use sentence-transformers or OpenAI embeddings
2. **Caching**: Cache tool embeddings for faster routing
3. **Feedback Loop**: Learn from tool usage patterns
4. **Multi-Agent**: Tool sharing between agent instances
5. **Real Tools**: Connect to actual APIs instead of simulation

### License

MIT License - See LICENSE file for details

### Acknowledgments

- Inspired by MCP-Zero paper by Xiang Fei, Xiawu Zheng, and Hao Feng
- Based on Model Context Protocol (MCP) ecosystem
- Built for educational purposes in AI Agent development

**Ready to get started?** Run `python quickstart.py` to see active tool discovery in action!

---

## 中文

面向 LLM Agent 的主动工具发现教学实现，灵感来自 MCP-Zero 论文（[arXiv:2506.01056](https://arxiv.org/pdf/2506.01056)）。

### 概述

传统 LLM Agent 会把全部可用工具 schema 注入提示词，造成巨大上下文开销，并把 Agent 降为被动的工具选择器。本项目演示**主动工具发现**：Agent 自主识别能力缺口，并按需请求具体工具。

#### 问题

当前工具集成方式有关键局限：

1. **巨大上下文开销**：注入全部工具可能消耗 100k+ token
2. **被动选择**：Agent 只从预定义选项里选，而非主动发现
3. **扩展性差**：上下文随生态规模增长，而非随任务需要增长
4. **自主性丧失**：工具选择交给外部检索系统

#### 方案：主动工具发现

本项目实现 MCP-Zero 的三项核心机制：

1. **主动工具请求**：Agent 生成结构化请求，精确描述所需工具
2. **分层语义路由**：两阶段匹配（server 级 → tool 级）
3. **迭代能力扩展**：随任务理解演进逐步构建工具链

### 三种策略对比

本实验把"工具选择"问题落到可度量的基准上，对比三种策略在**同一批任务**上的表现：

| 策略 | 说明 | 上下文里的工具 |
|------|------|----------------|
| `all-tools` | 一次性注入全部工具（传统被动式基线） | 全部 N 个 |
| `retrieval` | 按任务语义检索 top-k 个工具后再注入（工具检索 / RAG 式，`RetrievalToolAgent`） | 仅 top-k 个 |
| `active` | MCP-Zero 式主动发现：模型迭代地请求所需工具（`ActiveToolAgent`） | 按需增长 |

评测入口是 `demo_comparison.py`，带完整的 `argparse` 命令行：

```bash
# 仅离线对比（确定性，无需 API Key）：召回率 vs token 成本 vs 随规模的扩展性
python demo_comparison.py --offline

# 把工具目录扩充到 200 个（合成干扰工具补齐），观察 token 成本的分化
python demo_comparison.py --offline --num-tools 200

# 三种策略端到端对比（需要 API Key）：模型是否真的调用了正确的工具、token、延迟
python demo_comparison.py --strategy compare

# 只对单条查询运行某种策略
python demo_comparison.py --query "Deploy version 2.0 to production" --strategy retrieval

# 保存结果为 JSON
python demo_comparison.py --offline --output results.json
```

运行 `python demo_comparison.py --help` 查看全部参数（`--strategy / --query / --num-tools /
--top-k / --model / --output / --offline / --legacy-demos`）。

#### 离线基准（确定性，无需 API）

`benchmark.py` 提供了一个带**标准答案工具**的小型基准集（10 个任务，每个任务标注了应当被选中的
工具），并在**不调用任何 API** 的情况下度量两件事：

- **Retrieval recall@k**：标准答案工具是否落在被注入上下文的工具集合里；
- **Schema tokens**：注入的工具描述占用的 token 数（由 schema 直接估算，确定性可复现）。

下表是 `python demo_comparison.py --offline` 的**实测输出**（top-k=5，10 个任务）：

| 策略 | 上下文工具数 | Schema tokens | 召回率（标准答案可达） |
|------|------|------|------|
| all-tools（全部注入） | 35 | 3,857 | 100% |
| retrieval（top-5） | 5 | 551 | 100% |

随着工具目录增长，`all-tools` 的 token 成本线性膨胀，而 `retrieval` 基本持平（实测）：

| 目录规模 | all-tools tokens | retrieval(top-5) tokens | retrieval 召回率 |
|------|------|------|------|
| 35 | 3,857 | 551 | 100% |
| 100 | 10,292 | 539 | 100% |
| 200 | 20,258 | 540 | 100% |
| 400 | 40,258 | 540 | 100% |

> 结论：检索式按需选择在保持 100% 召回率的同时，把工具描述的 token 成本从数千压到数百，且不随
> 生态规模膨胀。这正是本章"把工具选择转化为知识检索"的量化体现。上述数字由 `--offline` 路径
> 确定性生成，可直接复现。

#### 端到端准确率（需要 API Key）

在配置 `OPENAI_API_KEY` 后，`--strategy compare` 会真正调用模型，度量每种策略下模型**是否调用了
标准答案工具**（accuracy）、平均 token 与平均延迟。这一部分需要联网与 API，故不在离线路径中运行。

### 架构

（与英文侧相同的架构图，见 English 部分 Architecture。）

### 组件

#### 核心文件

- **`agent.py`**：三种策略各一个 Agent 实现
  - `ActiveToolAgent`：MCP-Zero 式按需发现（`active`）
  - `RetrievalToolAgent`：一次性语义检索 top-k（`retrieval`）
  - `PassiveToolAgent`：传统全量预加载（`all-tools`）

- **`benchmark.py`**：带标注的基准 + 离线评估
  - 10 个任务，每个标注标准答案工具
  - `build_catalog(num_tools)`：真实目录，可选用干扰工具补齐
  - `evaluate_offline(...)`：确定性 recall@k / token 成本（无 API）

- **`tool_knowledge_base.py`**：工具目录
  - 8 个 server（领域）× 35 个工具
  - 按平台/功能组织
  - 模拟 MCP 生态

- **`semantic_router.py`**：分层工具发现
  - 两阶段语义匹配
  - 基于 TF-IDF 的相似度
  - 结构化请求解析

- **`config.py`**：配置
  - LLM 提供商
  - 路由阈值
  - Agent 参数

#### 演示脚本

- **`quickstart.py`**：快速演示（⭐ 从这里开始）
- **`demo_comparison.py`**：综合对比
- **`examples.py`**：多场景示例

### 快速开始

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置 API Key

```bash
cp env.example .env
# Edit .env and add your API key
```

> **OpenRouter 通用兜底**：若未设置 `OPENAI_API_KEY` 但设置了
> `OPENROUTER_API_KEY`，`config.py` 会自动改走 OpenRouter
> （`base_url=https://openrouter.ai/api/v1`），并把模型 id 映射为
> `provider/model` 形式（`gpt-*` → `openai/…`，`claude-*` →
> `anthropic/claude-opus-4.8`）。已有 `OPENAI_BASE_URL`/`OPENAI_MODEL`
> 覆盖会保留。

#### 3. 运行快速开始

```bash
python quickstart.py
```

将演示：
- 主动工具发现过程
- 被动工具注入（对照）
- 效率指标与洞察

### 性能对比

见上文**三种策略对比**中的实测、可复现数字。
离线表（schema token 成本 + 检索召回）由 `python demo_comparison.py --offline` 确定性生成，无需 API Key。
端到端准确率/延迟需要 API Key（`--strategy compare`）。

> 说明：更早草稿中曾用圆整示意数字描述 token 节省；现已替换为离线基准的真实输出，避免虚构数字。

### 关键概念

#### 主动工具请求

不预加载工具，而是显式请求所需能力：

```python
<tool_request>
server: GitHub for repository management
tool: search repositories by stars and language
</tool_request>
```

#### 分层语义路由

两阶段算法降低搜索复杂度：

1. **阶段 1**：匹配相关 server（平台）
   - "GitHub operations" → GitHub server
   - "File management" → Filesystem server

2. **阶段 2**：在 server 内匹配具体工具
   - "search repositories" → `github_search_repos`
   - "read file" → `fs_read_file`

#### 迭代能力扩展

工具随对话逐步发现：

```
Turn 1: Need GitHub access
  → Load GitHub tools

Turn 2: Need to analyze downloaded files
  → Additionally load filesystem tools

Turn 3: Need to visualize results
  → Additionally load analytics tools
```

工具链随任务复杂度增长，而非随生态规模增长。

### 示例

#### 示例 1：简单任务

```python
from agent import ActiveToolAgent

agent = ActiveToolAgent()
result = agent.execute_task("Search for Python ML repositories on GitHub")

# Agent discovers and loads only GitHub tools
print(f"Tools loaded: {result['metrics']['tools_loaded']}")  # 2-3 tools
print(f"Tokens used: {result['metrics']['tokens_used']}")    # ~2,000
```

#### 示例 2：跨领域任务

```python
task = """
1. Query database for user data
2. Analyze with statistics
3. Create visualization
4. Email report to team
"""

result = agent.execute_task(task)

# Agent builds cross-domain toolchain:
# Database → Analytics → Communication
print(f"Tools: {result['tools_loaded']}")
```

#### 示例 3：对比

```python
from agent import ActiveToolAgent, PassiveToolAgent

# Active approach
active = ActiveToolAgent()
active_result = active.execute_task(task)

# Passive approach
passive = PassiveToolAgent()
passive_result = passive.execute_task(task)

# Compare efficiency
reduction = (1 - active_result['metrics']['tokens_used'] / 
             passive_result['metrics']['tokens_used']) * 100
print(f"Token reduction: {reduction:.1f}%")  # Typically 90-98%
```

### 运行演示

#### 1. 快速开始（推荐先跑）

```bash
python quickstart.py
```

展示基本的主动 vs 被动对比。

#### 2. 策略对比基准（主实验）

```bash
python demo_comparison.py --offline   # deterministic, no API key needed
python demo_comparison.py             # + end-to-end accuracy/latency if API key present
```

默认打印：
- 离线策略表：检索 recall@k vs 工具 schema token 成本（确定性）
- 扩展性表：目录扩到数百工具时的 token 成本
- 端到端表（有 API Key）：`all-tools` / `retrieval` / `active` 的 accuracy / tokens / latency

原叙事型演示（语义路由 walk-through、迭代发现等）仍可通过 `--legacy-demos` 使用。见策略对比节与 `python demo_comparison.py --help`。

#### 3. 用例示例

```bash
python examples.py
```

演示：
- GitHub 工作流
- 数据流水线
- DevOps 自动化
- 多轮发现
- 效率指标

### 适用场景

#### 适合主动发现

1. **任务范围明确**：已知范围、只需特定工具
2. **大型工具生态**：50+ 工具且多数无关
3. **多轮对话**：所需工具随时间演化
4. **Token 受限环境**：上下文窗口有限

#### 被动方式可能够用

1. **小工具集**：总数 <10
2. **全部相关**：每个工具都很可能用到
3. **单轮任务**：无需迭代细化

### 配置

编辑 `config.py` 或设置环境变量：

```python
# LLM Configuration
OPENAI_API_KEY = "your-api-key"
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-5.6-luna"

# Routing Configuration
SIMILARITY_THRESHOLD = 0.15  # Min similarity for tool match
TOP_K_SERVERS = 3            # Number of servers to search
TOP_K_TOOLS = 5              # Tools to return per server

# Agent Configuration
MAX_TOOL_REQUESTS = 5       # Max discovery iterations
```

### 教育价值

本项目演示：

#### 软件工程原则

- **关注点分离**：Router、知识库、Agent 清晰分离
- **可扩展性**：10 或 1,000 工具都高效
- **模块化**：易于新增 server/工具

#### AI Agent 设计模式

- **主动 vs 被动**：根本架构差异
- **分层搜索**：复杂度从 O(n) 降到 O(log n)
- **语义匹配**：超越关键词匹配

#### 现实应用

- **工具生态**：MCP、LangChain、AutoGen
- **Agent 框架**：构建生产级 Agent
- **上下文管理**：高效处理长上下文

### 技术细节

#### 语义路由实现

使用 TF-IDF 向量化与余弦相似度：

```python
# Server-level
server_vector = vectorizer.transform([request])
similarities = cosine_similarity(server_vector, server_embeddings)

# Tool-level
tool_vector = vectorizer.transform([request])
tool_similarities = cosine_similarity(tool_vector, tool_embeddings)

# Combined score
final_score = 0.3 * server_score + 0.7 * tool_score
```

#### Token 估算

近似估算工具 schema 的 token：

```python
def count_tokens_in_schema(schema):
    # Rough estimation: 1 token ≈ 4 characters
    schema_str = json.dumps(schema)
    return len(schema_str) // 4
```

### 关键洞察

1. **自主性很重要**：Agent 应掌控能力获取
2. **上下文昂贵**：规模下每个 token 都重要
3. **语义匹配有效**：TF-IDF 足以做工具发现
4. **迭代带来灵活**：静态工具集无法预知需求
5. **分层搜索可扩展**：两阶段路由保持性能

### 参考文献

- **MCP-Zero 论文**：[arXiv:2506.01056](https://arxiv.org/pdf/2506.01056)
- **Model Context Protocol**：[官方仓库](https://github.com/modelcontextprotocol)
- **工具学习综述**：[ACM Computing Surveys](https://dl.acm.org/doi/10.1145/3708498)

### 扩展项目

#### 添加新工具

```python
# In tool_knowledge_base.py
new_tool = ToolDefinition(
    name="your_tool_name",
    description="What the tool does",
    parameters={...},
    server="server_name"
)
```

#### 添加新 Server

```python
# Create tools for the server
tools = [...]

# Add server
servers.append(ServerDefinition(
    name="your_server",
    description="Server description",
    tools=tools
))
```

#### 自定义路由

```python
# In config.py
SIMILARITY_THRESHOLD = 0.5  # More strict matching
TOP_K_SERVERS = 5           # Search more servers
```

### 故障排除

#### API Key 问题

```bash
# Verify .env file
cat .env

# Should contain:
OPENAI_API_KEY=sk-...
```

#### 导入错误

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

#### 相似度过低

```bash
# Lower threshold in config.py
SIMILARITY_THRESHOLD = 0.2
```

### 未来增强

可能的改进方向：

1. **更好的嵌入**：sentence-transformers 或 OpenAI embeddings
2. **缓存**：缓存工具嵌入以加速路由
3. **反馈环**：从工具使用模式中学习
4. **多 Agent**：实例间共享工具
5. **真实工具**：对接真实 API 而非模拟

### 许可证

MIT License - 详见 LICENSE 文件

### 致谢

- 灵感来自 Xiang Fei、Xiawu Zheng、Hao Feng 的 MCP-Zero 论文
- 基于 Model Context Protocol（MCP）生态
- 为 AI Agent 教学用途构建

**准备好开始了？** 运行 `python quickstart.py` 亲眼看看主动工具发现。

---

## Notes / 说明

- Related experiment: [active-tool-discovery](../active-tool-discovery/) (Experiment 4-6, embedding-based `discover_tools`).  
- 相关实验：[active-tool-discovery](../active-tool-discovery/)（实验 4-6，基于嵌入的 `discover_tools`）。  
- Offline path is fully deterministic without API keys.  
- 离线路径完全确定性，无需 API Key。
