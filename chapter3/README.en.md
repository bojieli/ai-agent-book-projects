# Chapter 3 · User Memory and Knowledge Bases

> Enables Agents to remember users across sessions and access external knowledge. Covers user memory systems, basic RAG pipelines, and knowledge organization and retrieval beyond flat text (structured indexes, knowledge graphs, etc.).

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter3.md)

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 3-1, 3-2 | [user-memory](user-memory/) | ✅ | Builds a long-term user memory system, enabling the Agent to remember user preferences and historical interactions to provide personalized services. |
| 3-1 | [user-memory-evaluation](user-memory-evaluation/) | ✅ | Systematically evaluates the accuracy, relevance, and effectiveness of user memory systems, including multiple test scenarios and evaluation metrics. |
| 3-2 | [mem0](mem0/) · [memobase](memobase/) | ✅ | Implements a version of user memory using each of the two open-source memory frameworks, mem0 and Memobase, serving as a comparative implementation for Experiment 3-2 "Memory Strategy Comparison," facilitating horizontal comparison of extraction forms and answer quality across different memory solutions. |
| 3-3 | [log-sanitization](log-sanitization/) | ✅ | Intelligent log sanitization that uses a local Ollama model to detect and redact secrets and PII while preserving debug value. |
| 3-4 | [dense-embedding](dense-embedding/) | ✅ | Builds a vector similarity search service, comparing ANNOY (tree-based) and HNSW (graph-based) approximate nearest neighbor index algorithms. Demonstrates the trade-offs between different indexing strategies in terms of performance, memory usage, and update capability. |
| 3-5 | [sparse-embedding](sparse-embedding/) | ✅ | Implements a sparse vector search engine based on the BM25 algorithm from scratch. Provides rich logging and visualization interfaces to understand the internal workings of the search engine, including term frequency weight calculation and inverted index principles. |
| 3-6 | [retrieval-pipeline](retrieval-pipeline/) | ✅ | Builds a complete retrieval pipeline combining dense retrieval, sparse retrieval, and neural re-ranking. Systematically demonstrates the complementary advantages of hybrid retrieval in different scenarios through carefully designed test cases. |
| 3-7 | [structured-index](structured-index/) | ✅ | Implements and compares two structured indexing approaches: RAPTOR (hierarchical trees with recursive summarization) and GraphRAG (knowledge graphs). |
| 3-8 | [agentic-rag](agentic-rag/) | ✅ | Compare the performance differences between traditional Non-Agentic RAG and Agentic RAG. Show how an Agent, using the ReAct pattern, leads iterative information retrieval, significantly improving answer quality when handling complex judicial Q&A. |
| 3-9 | [agentic-rag-for-user-memory](agentic-rag-for-user-memory/) | ✅ | Apply the Agentic RAG framework to manage user conversation history. Leverage multi-turn iterative search capabilities to handle memory retrieval across sessions, enabling basic recall and cross-session retrieval capabilities. |
| 3-10 | [contextual-retrieval](contextual-retrieval/) | ✅ | Implement the contextual retrieval technique proposed by Anthropic. By generating prefix summaries containing core context for text chunks, it addresses the context loss problem of traditional chunking methods, reducing retrieval failure rates by 49-67%. |
| 3-11 | [contextual-retrieval-for-user-memory](contextual-retrieval-for-user-memory/) | ✅ | Apply contextual retrieval techniques to user memory construction. Combine Advanced JSON Cards with Contextual RAG to form a dual-layer memory structure, enabling higher-level proactive service capabilities. |
| 3-12 | [structured-knowledge-extraction](structured-knowledge-extraction/) | ✅ | Using judicial precedents as an example, implement a three-stage pipeline: "Bottom-up factor discovery → Case prototype clustering → Conversational advisory Agent". Without predefined rigid fields, the LLM autonomously discovers factors from a large number of cases and summarizes them into a modular schema (core factors + charge-specific extension factors). Cases are then clustered into several prototypes, and the importance of each factor for each prototype is calculated. The Agent matches new case facts to the most similar prototype, asks for missing information based on factor importance, and provides evidence-based advice (with a legal disclaimer). |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
