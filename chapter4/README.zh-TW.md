# 第 4 章 · 工具

> 工具是 Agent 的雙手：MCP 協議、感知/執行/協作三類工具、事件驅動非同步 Agent、主動工具發現

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter4.md)

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | 感知工具 MCP：網路搜尋、多模態理解、檔案系統、公共資料來源（DuckDuckGo/Open-Meteo/Yahoo/OpenStreetMap），大多無需 API Key |
| 4-2 | [multimodal-agent](multimodal-agent/) | ✅ | Multimodal processing: compare native multimodal, extract-to-text, and tool-based analysis. |
| 4-3 | [execution-tools](execution-tools/) | ✅ | 執行工具 MCP：檔案操作、程式碼直譯器、虛擬終端機、外部系統整合，LLM 二次審批防誤操作 |
| 4-4 | [collaboration-tools](collaboration-tools/) | ✅ | 協作工具 MCP：瀏覽器自動化、HITL、Email/Telegram/Slack/Discord 通知、計時器，支援管理員審批 |
| 4-5 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | FastAPI 事件驅動 Agent，原生非同步整合前三組 MCP 工具，透過 HTTP API 接收 Web/IM/GitHub/計時器事件 |
| 4-6 | [async-agent](async-agent/) | ✅ | asyncio 單執行緒事件驅動框架 Flux：事件佇列按緊急度分派、非同步工具並行、執行中打斷、長任務取消與狀態查詢 |
| 4-7 | [active-tool-discovery](active-tool-discovery/) | ✅ | 對比「全量注入 120+ 工具 schema」與「少量基礎工具 + discover_tools 元工具按需檢索」，省 token 防錯選 |
| — | [active-tool-selection](active-tool-selection/) | ✅ | 讓 Agent 根據任務需求主動選擇最合適的工具組合，而非被動接受預定義工具集 |

> 此外，[`chapter4/docker-compose.yml`](docker-compose.yml) 與 [`chapter4/DOCKER_DEPLOYMENT.md`](DOCKER_DEPLOYMENT.md) 提供了將上述 MCP 工具伺服器容器化部署的參考方案。

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，設定好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **設計文件** | 僅包含架構與實現方案，可執行程式碼仍在完善中 |
