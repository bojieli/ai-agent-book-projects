# 第 6 章 · 互動：觀察與動作空間的擴展

> 從文字擴充套件到語音、GUI、物理世界：語音三典範、Computer Use、機器人

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter6.md)

## 如何閱讀實驗

正文用短小的機制 skeleton 說明控制流；實驗目錄放完整的 SDK 適配、日誌、測試與驗收證據，不需要逐行讀完每個檔案。

- **Starter:** 先讀目標、最小指令與驗收條件；可從 [live-audio](live-audio/);
- **Builder:** 沿著入口、核心迴圈、狀態／訊息 schema、工具與驗證器閱讀。
- **Maintainer:** 最後再看測試、證據 manifest、失敗處理、回滾路徑與 provider adapter。

第一次閱讀可先跳過憑證載入、展示層和 provider 相容層；要重現數字時再回來查看。

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 6-1 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | FastAPI 事件驅動 Agent，原生非同步整合前三組 MCP 工具，透過 HTTP API 接收 Web/IM/GitHub/計時器事件 |
| 6-2 | [async-agent](async-agent/) | ✅ | asyncio 單執行緒事件驅動框架 Flux：事件佇列按緊急度分派、非同步工具並行、執行中打斷、長任務取消與狀態查詢 |
| 6-3 | [live-audio](live-audio/) | ✅ | 即時語音聊天，整合 VAD + ASR（Whisper/SenseVoice）+ LLM（GPT-4o/Gemini/Doubao）+ TTS（Fish Audio），WebSocket 低延遲 |
| Add-on | [phone-agent](phone-agent/) | 🚧 | 官方 `pine-voice` SDK 的 direct/ReAct 路徑已實作，但未提供獲授權且同意參與的 E.164 目的號碼；預檢明確記錄未撥號、無 transcript，test double 不算驗收。 |
| 6-4 | [streaming-speech](streaming-speech/) | ✅ | 音訊按遞增長度分塊餵 ASR，每段立刻出文字降首包延遲，對比「整句到齊再識別」的高準確/高延遲 |
| 6-5 | [end-to-end-speech](end-to-end-speech/) | ✅ | 已在單張 RTX PRO 6000 上真實本機執行固定 revision 的 MiniCPM-o 4.5；端到端與自級聯皆為 3/4，但語義與副語言錯誤互補，並保留真實 24kHz 語音輸出與完整驗收證據。 |
| 6-6 | [controllable-tts](controllable-tts/) | 🚧 | 真實 Fish Audio S1 4×3×2 參考音庫與 A/B/C 媒體通過結構門禁；仍缺定性聽測與「接近真人客服」評估。 |
| 6-7 | `claude-quickstarts/computer-use-demo/` | 📖 | 外部 `anthropics/claude-quickstarts` 固定於 `9bcc95e…`；正文對應容器化 Ubuntu 桌面＋Claude agent loop 的 Computer Use demo，不是整個 quickstarts。 |
| 6-8 | `browser-use/` | 📖 | 外部 `browser-use/browser-use` 固定於 `ec9277c…`；正文用 `use_vision=True` 視覺 CLI 在 Google 查舊金山天氣並保留動作/截圖軌跡。 |
| 6-9 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | 真機 XLeRobot 遙操作同一個整理桌面任務：把紅色杯子放入托盤、黃色廢紙放入垃圾盒，最後重新觀察並確認狀態。 |
| 6-10 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | 在模擬器中測量同一桌面任務的理想控制上限；不代表真機已經執行。 |
| 6-11 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | 使用 Gemini Robotics-ER 1.5 自主控制真機 XLeRobot 完成同一整理桌面任務。 |
| 6-12 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | 在模擬器中比較同一任務的開環、逐步檢查與預測式閉環策略。 |
| 6-13 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | 改變背景、物體外觀、光照與視覺雜訊，對同一桌面任務進行 RGB 跨環境測試。 |

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，配置好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **進行中** | 已有實作，但正文要求的真實執行、授權參與者、硬體或驗收證據尚未完整 |
