# 第 10 章 · 多 Agent 協作

> 群體智慧高於個體：協作框架、上下文共享/隔離、湧現的「Agent 社會」

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter10.md)

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 10-1 | [staged-system-prompt](staged-system-prompt/) | ✅ | 同一 Coding Agent 在需求澄清/實現/審查三階段載入不同提示詞與工具集，對話歷史跨階段共享，審查不透過可回退 |
| 10-2 | [multi-role-transfer](multi-role-transfer/) | ✅ | 共享上下文下的鏈式 handoff：多角色各有獨立提示詞與工具，透過 `transfer_to_agent` 自主切換 |
| 10-3 | [book-translation](book-translation/) | ✅ | 管理者模式拆分翻譯給術語表/翻譯/審校專職 Agent，Manager 只存索引、譯文全落盤，上下文基本恆定 |
| 10-4 | `use-computer-while-calling/` | 📖 | 電話 Agent（Node.js）與瀏覽器 Agent（Python）經 WebSocket 直接通訊無協調器並行協作；程式碼已獨立為 [TalkAct](https://github.com/19PINE-AI/TalkAct)，本倉庫不內建該目錄（克隆命令見主 README 附錄） |
| 10-6 | [parallel-web-research](parallel-web-research/) | ✅ | N 個同構子 Agent 並行搜尋，命中即級聯終止；訊息匯流排/並行派發/即時監控/競態處理均真實實現 |
| 10-7 | `generative_agents/` | 📖 | 史丹佛「AI 小鎮」生成式智慧體（實驗 10-7 配套）；外部倉庫 `joonspk-research/generative_agents`，需自行克隆（見主 README 附錄） |
| 10-8 | [voice-werewolf](voice-werewolf/) | ✅ | 用多 Agent 狼人殺演示「上下文不共享」的資訊許可權：玩家私有上下文嚴格隔離，確定性法官投遞資訊並審計 |

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，配置好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **設計文件** | 僅包含架構與實現方案，可執行程式碼仍在完善中 |
