# 第 3 章 · 使用者記憶和知識庫

> 跨會話記住使用者、接入外部知識：使用者記憶、RAG、結構化索引、知識圖譜

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter3.md)

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 3-1, 3-2 | [user-memory](user-memory/) | ✅ | 長期使用者記憶系統，讓 Agent 記住偏好與歷史互動、提供個性化服務 |
| 3-1 | [user-memory-evaluation](user-memory-evaluation/) | ✅ | 系統化評估使用者記憶系統的準確性、相關性和有效性 |
| 3-2 | [mem0](mem0/) · [memobase](memobase/) | ✅ | 用 mem0、Memobase 兩個開源框架各實現一版使用者記憶，作為實驗 3-2 的對照實現 |
| 3-3 | [log-sanitization](log-sanitization/) | ✅ | 智慧日誌脫敏系統，基於本地 Ollama 模型檢測並脫敏日誌中的金鑰和 PII 敏感資料 |
| 3-4 | [dense-embedding](dense-embedding/) | ✅ | 向量相似性搜尋服務，對比 ANNOY（樹）與 HNSW（圖）兩種 ANN 演算法的權衡 |
| 3-5 | [sparse-embedding](sparse-embedding/) | ✅ | 從零實現基於 BM25 的稀疏向量搜尋引擎，視覺化內部工作機制 |
| 3-6 | [retrieval-pipeline](retrieval-pipeline/) | ✅ | 稠密 + 稀疏 + 神經重排序的完整流水線，用測試用例展示混合檢索的互補效果 |
| 3-7 | [structured-index](structured-index/) | ✅ | 實現並對比 RAPTOR（遞迴抽象樹）與 GraphRAG（知識圖譜）兩種結構化索引 |
| 3-8 | [agentic-rag](agentic-rag/) | ✅ | 對比 Non-Agentic 與 Agentic RAG，展示 ReAct 主導的迭代檢索在司法問答上的優勢 |
| 3-9 | [agentic-rag-for-user-memory](agentic-rag-for-user-memory/) | ✅ | 用 Agentic RAG 管理使用者對話歷史，實現跨會話記憶檢索 |
| 3-10 | [contextual-retrieval](contextual-retrieval/) | ✅ | 實現 Anthropic 的上下文感知檢索，為分塊生成前綴摘要，失敗率降低 49–67% |
| 3-11 | [contextual-retrieval-for-user-memory](contextual-retrieval-for-user-memory/) | ✅ | 結合 Advanced JSON Cards 與上下文感知 RAG，形成雙層記憶結構實現主動服務 |
| 3-12 | [structured-knowledge-extraction](structured-knowledge-extraction/) | ✅ | 以司法判例跑通「因子發現 → 聚類原型 → 對話式建議」三段流水線 |

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，配置好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **設計文件** | 僅包含架構與實現方案，可執行程式碼仍在完善中 |
