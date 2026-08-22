# 第 4 章 · 工具

> 工具是 Agent 的雙手：MCP 協議、感知/執行/協作三類工具、事件驅動非同步 Agent、主動工具發現

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter4.md)

## 如何閱讀實驗

正文用短小的機制 skeleton 說明控制流；實驗目錄放完整的 SDK 適配、日誌、測試與驗收證據，不需要逐行讀完每個檔案。

- **Starter:** 先讀目標、最小指令與驗收條件；可從 [execution-tools](execution-tools/);
- **Builder:** 沿著入口、核心迴圈、狀態／訊息 schema、工具與驗證器閱讀。
- **Maintainer:** 最後再看測試、證據 manifest、失敗處理、回滾路徑與 provider adapter。

第一次閱讀可先跳過憑證載入、展示層和 provider 相容層；要重現數字時再回來查看。

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | 感知工具 MCP：網路搜尋、多模態理解、檔案系統、公共資料來源（DuckDuckGo/Open-Meteo/Yahoo/OpenStreetMap），大多無需 API Key |
| 4-2 | [multimodal-agent](multimodal-agent/) | ✅ | Multimodal processing: compare native multimodal, extract-to-text, and tool-based analysis. |
| 4-3 | [execution-tools](execution-tools/) | ✅ | 執行工具 MCP：檔案操作、程式碼直譯器、虛擬終端機、外部系統整合，LLM 二次審批防誤操作 |
| 4-4 | [collaboration-tools](collaboration-tools/) | ✅ | 協作工具 MCP：瀏覽器自動化、HITL、Email/Telegram/Slack/Discord 通知、計時器，支援管理員審批 |
| 4-5 | [active-tool-discovery](active-tool-discovery/) | ✅ | 對比「全量注入 120+ 工具 schema」與「少量基礎工具 + discover_tools 元工具按需檢索」，省 token 防錯選 |
| — | [active-tool-selection](active-tool-selection/) | ✅ | 讓 Agent 根據任務需求主動選擇最合適的工具組合，而非被動接受預定義工具集 |

> 此外，[`chapter4/docker-compose.yml`](docker-compose.yml) 與 [`chapter4/DOCKER_DEPLOYMENT.md`](DOCKER_DEPLOYMENT.md) 提供了將上述 MCP 工具伺服器容器化部署的參考方案。

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，設定好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **設計文件** | 僅包含架構與實現方案，可執行程式碼仍在完善中 |
