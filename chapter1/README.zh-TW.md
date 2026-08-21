# 第 1 章 · Agent 基礎知識

> **Agent = LLM + 上下文 + 工具**；Harness 工程才是競爭力

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter1.md)

## 如何閱讀實驗

正文用短小的機制 skeleton 說明控制流；實驗目錄放完整的 SDK 適配、日誌、測試與驗收證據，不需要逐行讀完每個檔案。

- **Starter:** 先讀目標、最小指令與驗收條件；可從 [context](context/);
- **Builder:** 沿著入口、核心迴圈、狀態／訊息 schema、工具與驗證器閱讀。
- **Maintainer:** 最後再看測試、證據 manifest、失敗處理、回滾路徑與 provider adapter。

第一次閱讀可先跳過憑證載入、展示層和 provider 相容層；要重現數字時再回來查看。

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 1-1 | [context](context/) | ✅ | 系統性消融實驗展示 Agent 上下文各元件的重要性；支援 SiliconFlow Qwen、字節 Doubao、月之暗面 Kimi 等多提供商 |
| 1-2 | [web-search-agent](web-search-agent/) | ✅ | Kimi K3 模型即 Agent，具備基礎深度搜尋能力，能進行多輪搜尋和資訊整合 |
| 1-3 | [search-codegen](search-codegen/) | ✅ | GPT-5 原生工具整合，綜合利用網路搜尋與程式碼沙箱實現複雜分析 |
| 1-4 | [image-gen-workflow](image-gen-workflow/) | ✅ | 具體/寬泛兩類需求 × 工作流（kimi-k3 改寫 + 通義萬相）與原生（Gemini / GPT-Image 2）雙路線真實對照：具體需求下原生更忠實（海報文案被改寫節點丟進負面詞），寬泛需求下改寫的場景具象化帶來想象力，但 GPT-Image 2 自己就能補觀點——適配層被模型內化的實證 |
| 7-1, 7-2 | [learning-from-experience](learning-from-experience/) | ✅ | 對比 Q-learning 與基於 LLM 的上下文學習，復現 Shunyu Yao 的 "The Second Half"：LLM 以 250–400 倍樣本效率超越傳統 RL |

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，配置好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **設計文件** | 僅包含架構與實現方案，可執行程式碼仍在完善中 |
