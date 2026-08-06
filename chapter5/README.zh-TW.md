# 第 5 章 · Coding Agent 與程式碼生成

> 程式碼是「能創造新工具的工具」，生產級 Coding Agent 全景

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter5.md)

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 5-1 | [code-for-math](code-for-math/) | ✅ | 同模型同題集對比「純思維鏈」與「程式碼輔助」，後者用 sympy/numpy/scipy 在沙箱執行，準確率顯著更高 |
| 5-2 | [code-for-logic](code-for-logic/) | ✅ | 把「騎士與無賴」轉化為 CSP，用 `python-constraint` 定義約束並求解，對比自然語言推理與程式碼輔助 |
| 5-3 | [small-model-codified-rules](small-model-codified-rules/) | ✅ | τ-bench 航空客服對照實驗：把退款規則從提示詞搬進程式碼/工具後，小模型成功率與一致性大幅提升 |
| 5-4 | [paper-to-ppt](paper-to-ppt/) | ✅ | 把「做 PPT」重構為程式碼生成：Proposer 寫 Slidev，Reviewer 真渲染成 PNG 用 Vision LLM 檢查迭代 |
| 5-5 | [paper-to-video](paper-to-video/) | ✅ | 在「論文 → PPT」基礎上生成講解詞、TTS 合成、ffmpeg 逐頁同步成帶旁白的講解視訊 |
| 5-6 | [video-edit](video-edit/) | ✅ | 一段多場景視訊 + 一句自然語言需求，兩步 Vision 定位剪出片段，Reviewer 抽幀核對不合格則迭代 |
| 5-7 | [adaptive-log-parser](adaptive-log-parser/) | ✅ | 遇到無法解析的新格式時不報錯，交給程式碼 Agent 生成 `parse` 函式，測試透過後熱更新進引擎，全程無人介入 |
| 5-8 | [log-diagnosis](log-diagnosis/) | ✅ | 診斷 Agent 讀取真實 HTTP 軌跡、架構文件與 PRD，定位根因、生成迴歸測試並在修復前後重放；正式活動透過官方 GitHub MCP 建立真實 Issue 並保存脫敏收據 |
| 5-9 | [dynamic-form](dynamic-form/) | ✅ | 資訊不全時動態生成含級聯邏輯的 HTML 表單讓使用者一次性補全，彙總 JSON 交回 Agent |
| 5-10 | [erp-agent](erp-agent/) | ✅ | 中文自然語言轉 SQL 由 DB 執行，artifact 模式讓 LLM 只生成 SQL 製品不搬運資料，省 token 又防錯 |
| 5-11 | [conversational-ui](conversational-ui/) | ✅ | 自然語言提 UI 客製需求（顏色/字型/文案/佈局），Agent 改 React 原始碼借 Vite HMR 即時生效 |
| 5-12 | [permission-embedded-data-objects](permission-embedded-data-objects/) | ✅ | PostgreSQL 之上的物件儲存，在動態生成的應用程式碼之下強制執行授權、驗證與參照完整性 |
| 5-13 | [agent-creator](agent-creator/) | ✅ | 比較「複製已驗證範例後修改」與「從零生成」兩種 Agent 建立方式；兩臂均完成編譯、測試與真實 Kimi K3 工具呼叫驗證 |

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，設定好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **設計文件** | 僅包含架構與實現方案，可執行程式碼仍在完善中 |
