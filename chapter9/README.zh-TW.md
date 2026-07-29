# 第 9 章 · 多模態與即時互動

> 從文字擴充套件到語音、GUI、物理世界：語音三典範、Computer Use、機器人

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter9.md)

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | 即時語音聊天，整合 VAD + ASR（Whisper/SenseVoice）+ LLM（GPT-4o/Gemini/Doubao）+ TTS（Fish Audio），WebSocket 低延遲 |
| 9-2 | [phone-agent](phone-agent/) | ✅ | 標準 ReAct Agent 自行想清號碼與目標，呼叫 `make_phone_call`（電話語音 API 抽象）完成通話並按需追問再撥 |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | 音訊按遞增長度分塊餵 ASR，每段立刻出文字降首包延遲，對比「整句到齊再識別」的高準確/高延遲 |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | ✅ | 對應 Step-Audio R1 的端到端語音思考（「聽→想→說」），與 ASR→LLM→TTS 級聯對比延遲與副語言損失 |
| 9-5 | [controllable-tts](controllable-tts/) | ✅ | LLM 輸出帶控制標記（情感/語速/停頓/笑聲），執行層解析對映到參考語音庫風格檔案再合成 |
| 9-6 | `claude-quickstarts/` | 📖 | Claude API 快速入門示例與最佳實踐，涵蓋各種使用場景 |
| 9-7 | `browser-use/` | 📖 | LLM 驅動的瀏覽器自動化框架，表單填寫/網頁導航/資料提取，支援多種 LLM 與雲/沙箱部署 |

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，配置好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **設計文件** | 僅包含架構與實現方案，可執行程式碼仍在完善中 |
