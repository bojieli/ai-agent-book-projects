# 第 1 章 · Agent 基礎知識

> **Agent = LLM + 上下文 + 工具**；Harness 工程才是競爭力

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter1.md)

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 1-1 | [context](context/) | ✅ | 系統性消融實驗展示 Agent 上下文各元件的重要性；支援 SiliconFlow Qwen、字節 Doubao、月之暗面 Kimi 等多提供商 |
| 1-2 | [web-search-agent](web-search-agent/) | ✅ | Kimi K3 模型即 Agent，具備基礎深度搜尋能力，能進行多輪搜尋和資訊整合 |
| 1-3 | [search-codegen](search-codegen/) | ✅ | GPT-5 原生工具整合，綜合利用網路搜尋與程式碼沙箱實現複雜分析 |
| 7-1, 7-2 | [learning-from-experience](learning-from-experience/) | ✅ | 對比 Q-learning 與基於 LLM 的上下文學習，復現 Shunyu Yao 的 "The Second Half"：LLM 以 250–400 倍樣本效率超越傳統 RL |

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，配置好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **設計文件** | 僅包含架構與實現方案，可執行程式碼仍在完善中 |
