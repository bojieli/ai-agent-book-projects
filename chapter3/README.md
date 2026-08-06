# 第 3 章 · 用户记忆和知识库

> 跨会话记住用户、接入外部知识：用户记忆、RAG、结构化索引、知识图谱

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter3.md)

可复现实验的逐项验收条件与规范证据路径见
[EXPERIMENT_LEDGER.md](EXPERIMENT_LEDGER.md)；项目可运行不等同于实验已通过，
最终状态以各项目的 `validation/latest.json` 为准。

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 3-1, 3-2 | [user-memory](user-memory/) | ✅ | 长期用户记忆系统，让 Agent 记住偏好与历史交互、提供个性化服务 |
| 3-1, 6-3 | [user-memory-evaluation](user-memory-evaluation/) | ✅ | 三层用户记忆评估集；实验 6-3 的四档多维 Rubric、逐维证据与幻觉一票否决 |
| 3-2 | [mem0](mem0/) · [memobase](memobase/) | ✅ | 用 mem0、Memobase 两个开源框架各实现一版用户记忆，作为实验 3-2 的对照实现 |
| 3-3 | [log-sanitization](log-sanitization/) | ✅ | 智能日志脱敏系统，基于本地 Ollama 模型检测并脱敏日志中的密钥和 PII 敏感数据 |
| 3-4 | [dense-embedding](dense-embedding/) | ✅ | 向量相似性搜索服务，对比 ANNOY（树）与 HNSW（图）两种 ANN 算法的权衡 |
| 3-5 | [sparse-embedding](sparse-embedding/) | ✅ | 从零实现基于 BM25 的稀疏向量搜索引擎，可视化内部工作机制 |
| 3-6 | [retrieval-pipeline](retrieval-pipeline/) | ✅ | 稠密 + 稀疏 + 神经重排序的完整流水线，用测试用例展示混合检索的互补效果 |
| 3-7 | [structured-index](structured-index/) | ✅ | 实现并对比 RAPTOR（递归抽象树）与 GraphRAG（知识图谱）两种结构化索引 |
| 3-8 | [agentic-rag](agentic-rag/) | ✅ | 对比 Non-Agentic 与 Agentic RAG，展示 ReAct 主导的迭代检索在司法问答上的优势 |
| 3-9 | [agentic-rag-for-user-memory](agentic-rag-for-user-memory/) | ✅ | 用 Agentic RAG 管理用户对话历史，实现跨会话记忆检索 |
| 3-10 | [contextual-retrieval](contextual-retrieval/) | ✅ | 实现 Anthropic 的上下文感知检索，为分块生成前缀摘要，失败率降低 49–67% |
| 3-11 | [contextual-retrieval-for-user-memory](contextual-retrieval-for-user-memory/) | ✅ | 结合 Advanced JSON Cards 与上下文感知 RAG，形成双层记忆结构实现主动服务 |
| 3-12 | [structured-knowledge-extraction](structured-knowledge-extraction/) | ✅ | 以司法判例跑通「因子发现 → 聚类原型 → 对话式建议」三段流水线 |

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **设计文档** | 仅包含架构与实现方案，可运行代码仍在完善中 |
