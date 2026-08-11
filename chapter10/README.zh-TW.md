# 第 10 章 · 多 Agent 協作

> 群體智慧高於個體：協作框架、上下文共享/隔離、湧現的「Agent 社會」

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter10.md)

## 如何閱讀實驗

正文用短小的機制 skeleton 說明控制流；實驗目錄放完整的 SDK 適配、日誌、測試與驗收證據，不需要逐行讀完每個檔案。

- **Starter:** 先讀目標、最小指令與驗收條件；可從 [parallel-web-research](parallel-web-research/);
- **Builder:** 沿著入口、核心迴圈、狀態／訊息 schema、工具與驗證器閱讀。
- **Maintainer:** 最後再看測試、證據 manifest、失敗處理、回滾路徑與 provider adapter。

第一次閱讀可先跳過憑證載入、展示層和 provider 相容層；要重現數字時再回來查看。

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 10-1 | [multi-role-transfer](multi-role-transfer/) | ✅ | [正式 v2 對照](multi-role-transfer/validation/comparison/runs/exp10-1-qwen35flash-20260809-v2/REPORT.md)保留 30 對任務、12 條邊界軌跡、289 份模型回執、31 份 Tavily 回執與 60 次交換順序盲測；修復 Skill 首步跳過問題後，Skill 通過 15/30、Transfer 2/30，並固定成本/延遲權衡 |
| 10-2 | [book-translation](book-translation/) | 🚧 | 四角色 Manager 與單 Agent 對照已有真實模型小樣本；仍需依正文使用含大量插圖與程式碼的技術書，完整比較品質、效率、token 與資源消耗。 |
| 10-3 | `use-computer-while-calling/` + [autonomous-phone-registration](autonomous-phone-registration/) | 📖 / 🚧 | 外部 [TalkAct](https://github.com/19PINE-AI/TalkAct) 固定於 `7d70007…`：fast/slow Agent 真正並行，透過行程內 `SharedState` 黑板（滾動摘要、transcript/action log）與雙向文字佇列共享資訊；此版本不是 WebSocket bridge。本倉庫不內建該 checkout，精確克隆與 benchmark 入口見主 README 附錄。 Playwright 觀察真實表單，真實 LLM 自主決定呼叫 `initiate_phone_call_agent`；需明確同意的 Twilio/本機語音路徑支援校驗、重問、提問/填寫並行、脫敏軌跡與選擇性提交。目前證據僅以 scripted 回答驗證瀏覽器/LLM/並行，PSTN 與真人音訊仍為 `not_run`，因此真人驗收尚未完成。 |
| 10-4 | [parallel-web-research](parallel-web-research/) | ✅ | N 個獨立 Playwright 瀏覽器工作階段搜尋十個真實大學網站，真實 LLM 擷取可引用證據；驗收保留監控、逾時/錯誤隔離、單次結算、級聯終止確認、資源清理與同站 3.142× 並行加速。 |
| 10-5 | `generative_agents/` | 📖 | 史丹佛「AI 小鎮」生成式智慧體（實驗 10-5 配套）；外部倉庫 `joonspk-research/generative_agents`，需自行克隆（見主 README 附錄） |
| 10-6 | [voice-werewolf](voice-werewolf/) | 🚧 | 新增真實 LLM 使用者模擬器：只讀本席上下文、必須呼叫工具，且僅能經合成音訊與真實 OpenRouter 音訊 ASR 入局。嚴格複核否決了兩個把誤轉寫當棄權的早期執行；未受影響的 v2 通過端到端、隔離、規則勝負與三循環，但村民錯逐預言家導致策略失敗。 |

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，配置好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **進行中** | 實作或實驗要求的驗收證據尚未完整；可能已有可執行程式碼，但不代表完整驗收 |
