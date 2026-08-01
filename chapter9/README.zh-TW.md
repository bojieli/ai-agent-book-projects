# 第 9 章 · 多模態與即時互動

> 從文字擴充套件到語音、GUI、物理世界：語音三典範、Computer Use、機器人

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter9.md)

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | 即時語音聊天，整合 VAD + ASR（Whisper/SenseVoice）+ LLM（GPT-4o/Gemini/Doubao）+ TTS（Fish Audio），WebSocket 低延遲 |
| 9-2 | [phone-agent](phone-agent/) | 🚧 | 官方 `pine-voice` SDK 的 direct/ReAct 路徑已實作，但未提供獲授權且同意參與的 E.164 目的號碼；預檢明確記錄未撥號、無 transcript，test double 不算驗收。 |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | 音訊按遞增長度分塊餵 ASR，每段立刻出文字降首包延遲，對比「整句到齊再識別」的高準確/高延遲 |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | ✅ | 已在單張 RTX PRO 6000 上真實本機執行固定 revision 的 MiniCPM-o 4.5；端到端與自級聯皆為 3/4，但語義與副語言錯誤互補，並保留真實 24kHz 語音輸出與完整驗收證據。 |
| 9-5 | [controllable-tts](controllable-tts/) | 🚧 | 真實 Fish Audio S1 4×3×2 參考音庫與 A/B/C 媒體通過結構門禁；仍缺定性聽測與「接近真人客服」評估。 |
| 9-6 | `claude-quickstarts/computer-use-demo/` | 📖 | 外部 `anthropics/claude-quickstarts` 固定於 `9bcc95e…`；正文對應容器化 Ubuntu 桌面＋Claude agent loop 的 Computer Use demo，不是整個 quickstarts。 |
| 9-7 | `browser-use/` | 📖 | 外部 `browser-use/browser-use` 固定於 `ec9277c…`；正文用 `use_vision=True` 視覺 CLI 在 Google 查舊金山天氣並保留動作/截圖軌跡。 |
| 9-8 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | 外部 XLeRobot 固定於 `3d14695…`，涵蓋鍵盤/Xbox/Joy-Con/VR 遙操作；目前只有源碼與非致動預檢，沒有獲授權四模式真機與取放擦證據。 |
| 9-9 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | 外部 XLeRobot `3d14695…`＋RoboCrew，精確使用 `gemini-robotics-er-1.5-preview`、角度標註與前進/左轉/右轉工具；尚無獲授權真機導航證據。 |
| 9-10 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | 外部 `lerobot-sim2real` 固定於 `87d6c1d…` 的五階段 RGB→PPO→SO-100 流程；本機缺 ManiSkill/NVIDIA，亦無獲授權實體機器人執行。 |

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，配置好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **進行中** | 已有實作，但正文要求的真實執行、授權參與者、硬體或驗收證據尚未完整 |
