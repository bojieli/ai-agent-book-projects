# 第 2 章 · 上下文工程

> 上下文決定能力上限：KV Cache、提示工程、Agent Skills、上下文壓縮

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter2.md)

## 如何閱讀實驗

正文用短小的機制 skeleton 說明控制流；實驗目錄放完整的 SDK 適配、日誌、測試與驗收證據，不需要逐行讀完每個檔案。

- **Starter:** 先讀目標、最小指令與驗收條件；可從 [context-compression](context-compression/);
- **Builder:** 沿著入口、核心迴圈、狀態／訊息 schema、工具與驗證器閱讀。
- **Maintainer:** 最後再看測試、證據 manifest、失敗處理、回滾路徑與 provider adapter。

第一次閱讀可先跳過憑證載入、展示層和 provider 相容層；要重現數字時再回來查看。

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 2-1 | [local_llm_serving](local_llm_serving/) | ✅ | 跨平台本地 LLM 部署，自動選 vLLM/Ollama 後端，展示 0.6B 小模型也能有出色工具呼叫 |
| 2-2, 2-8 | [attention_visualization](attention_visualization/) | ✅ | 視覺化 LLM 完整 token 序列與注意力權重分佈，理解模型如何處理上下文、推理與呼叫工具 |
| 2-3 | [kv-cache](kv-cache/) | ✅ | 探索不同上下文管理模式對 KV Cache 的影響，示範錯誤模式如何破壞快取效率 |
| 2-4 | [prompt-engineering](prompt-engineering/) | ✅ | 擴充 Tau-Bench，量化語氣風格、指令組織、工具描述等因素對任務完成率的影響 |
| 2-5 | [prompt-injection](prompt-injection/) | ✅ | 3 種攻擊場景 × 4 種防禦設定的對照實驗，直觀展示逐層疊加防禦後注入成功率下降 |
| 2-6 | [agent-skills-ppt](agent-skills-ppt/) | ✅ | 復現 Agent Skills「漸進式揭露」，按需載入完整流程後用 python-pptx 產生真實 `.pptx` |
| 2-7 | 正文實驗 | 🚧 | 從個人範文建立「去 AI 味」寫作 Skill；練習觸發條件、規則、示例、作用域與迭代維護，不依賴獨立程式專案 |
| 2-9 | [system-hint](system-hint/) | ✅ | 研究系統提示對 Agent 行為的影響，探索如何透過最佳化系統提示提升效能 |
| 2-10 | [context-compression](context-compression/) | ✅ | 實作並對比摘要、關鍵資訊擷取、語意壓縮等多種策略，保持能力的同時減少 token |

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，設定好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **設計文件** | 僅包含架構與實作方案，可執行程式碼仍在完善中 |
