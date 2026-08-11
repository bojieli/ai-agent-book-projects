# 學習建議

← [返回主目錄](README.md)

## 核心理念：Agent = 模型 + 上下文 + 工具

本書的核心框架是 **Agent = 模型 + 上下文 + 工具**，三個元件協作實現 Agent 的智慧行為：

| 元件 | 比喻 | 職責 |
| :--: | :--: | --- |
| 🧠 **模型（Model）** | 大腦 | 提供理解、推理和決策能力 |
| 💾 **上下文（Context）** | 作業系統 | 系統指令、對話歷史、推理過程、工具互動記錄等 |
| 🤲 **工具（Tools）** | 雙手 | 感知環境、執行操作、與外部世界互動 |

## 學習路徑

全書圍繞「模型 / 上下文 / 工具」三大支柱層層展開。每個篇章都附帶一條關鍵洞察：

| 篇章 | 章節 | 涵蓋內容 | 關鍵洞察 |
| --- | :--: | --- | --- |
| **基礎篇** | 第 1 章 | RL 中的 Agent 定義、傳統 RL vs LLM+RL 樣本效率、「模型即 Agent」新典範 | 先驗知識的重要性超越演算法和環境 |
| **上下文篇** | 第 2–3 章 | 系統提示、KV Cache、上下文壓縮、提示工程；使用者記憶、稠密/稀疏/混合檢索、Agentic RAG | 完整上下文 = 系統指令 + 對話歷史 + 推理過程 + 工具記錄 + 使用者記憶 + 外部知識 |
| **工具篇** | 第 4–5 章 | 感知/執行/協作三類 MCP 工具、事件驅動非同步架構；生產級 Coding Agent 完整實現 | 工具設計應通用化（程式碼直譯器優於計算機），程式碼是能創造新工具的元能力 |
| **模型篇** | 第 6–7 章 | Terminal-Bench/SWE-bench/GAIA/OSWorld/Tau2-Bench 評估基準；SFT、RL、RLHF、樣本效率 | 獨立驗證訊號比「讓模型再想一遍」更可靠；RL 把工具呼叫內化為原生能力 |
| **自我進化篇** | 第 8 章 | 經驗學習、工作流程外化為工具、提示與觀察蒸餾進引數 | 從經驗中學習是 Agent 從「聰明」走向「熟練」的關鍵 |
| **拓展與協作篇** | 第 9–10 章 | 語音/GUI/物理世界的多模態互動；多 Agent 分工協作 | 多 Agent 的每個設計決策都能在單 Agent 三要素中找到對應 |

## 正文與實驗的分工

本書正文不是某個 SDK 的逐步教學。短偽代碼與 skeleton 說明狀態流、停止點與驗證邊界；章級實驗提供完整實作、模型／環境適配、測試、日誌與證據。

| Layer | Read first | Skip for now | Question it answers |
| :--: | --- | --- | --- |
| **Starter** | Project README: goal, minimum command, acceptance conditions; matching prose skeleton | credentials, UI, provider adapters, long raw logs | 這個實驗要證明哪條機制？ |
| **Builder** | entry point, core loop, state/message schema, tools, verifier | compatibility/deployment layers unrelated to the mechanism | 哪個變數改變了行為？ |
| **Maintainer** | tests, failure handling, evidence format, manifest/hash, rollback path | third-party details needed only when changing the experiment | 結果能否複核，失敗是否被如實記錄？ |

## 難度分級

| 級別 | 章節 | 適合讀者 |
| --- | :--: | --- |
| 🟢 入門級 | 第 1–2 章 | 初學者，理解基本概念 |
| 🔵 進階級 | 第 3–4 章 | 有一定程式設計基礎，涉及系統整合 |
| 🟣 高階 | 第 5–6 章 | 較強程式設計能力，涉及複雜系統設計 |
| 🔴 專家級 | 第 7–8 章 | 有深度學習與訓練/自我進化經驗 |
| 🟠 應用級 | 第 9–10 章 | 綜合運用前面所學，建構實際應用 |

## 實踐建議

| # | 建議 | 說明 |
| :--: | --- | --- |
| 1 | 🛠️ **動手實踐** | 每個專案都設計為可獨立執行，建議親自執行並修改程式碼 |
| 2 | 📚 **結合書籍** | 配合 [`book/`](../../book/) 中相應章節閱讀，理解理論與實踐的結合 |
| 3 | 🔬 **實驗對比** | 多個專案包含消融研究和對比實驗，透過對比加深理解 |
| 4 | 🪜 **漸進學習** | 從簡單專案開始，逐步深入複雜系統 |
| 5 | 🔌 **關注協議** | 第 4 章 MCP 伺服器專案展示了標準化工具協議，這是建構可擴充 Agent 的關鍵 |
