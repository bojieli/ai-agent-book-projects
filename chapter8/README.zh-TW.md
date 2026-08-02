# 第 8 章 · Agent 的自我進化

> 不改權重也能成長：經驗學習、從工具使用者到創造者

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter8.md)

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | 實驗 8-1：用環境結果、過程規則和語言 Rubric 形成帶證據的客服軌跡診斷 |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | 基於 AWorld + GAIA 的「學習-應用」閉環：自動總結成功軌跡為結構化經驗，在新任務中檢索應用 |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | 以 tau-bench 航空客服「過度轉接」為例，Coding Agent 讀/改 prompt 檔案 → 重新評測 → 驗證閉環 |
| 8-4 | [browser-use-rpa](browser-use-rpa/) | ✅ | 瀏覽器工作流錄製系統，把重複操作封裝為引數化工具，從 LLM 推理切換到自動化執行可加速 3–5 倍 |
| 8-5 | [self-modifying-agent](self-modifying-agent/) | ✅ | 實驗 8-5：由重複故障觸發重試/熔斷程式碼補丁、迴歸、灰度與回滾 |
| 8-6 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | 將五次 fresh reviewer 拒絕送回 Hermes 持續自我修正，第六次終局接受；44 項聚焦測試通過，但未執行下游消融 |
| 8-7 | [self-evolution-eval](self-evolution-eval/) | ✅ | 實驗 8-7：三臂、3 seeds、14 任務的長期學習、遷移、規則替換與保留評估 |

以上實驗都提供無需 API Key 的離線入口和單元測試；需要真實模型或瀏覽器的擴充路徑在各專案 README 中另行說明。

## 補充案例

| 編號 | 專案 | 關係 |
| :--: | --- | --- |
| 7-8 | [prompt-distillation](prompt-distillation/) | 將複雜提示的效果蒸餾進模型引數，減少推理提示長度，把上下文經驗固化為引數化知識 |
| — | [self-evolving-tools](self-evolving-tools/) | Alita 式「最小預定義，最大自我進化」：五個通用元工具，自己上網找庫/讀文件/沙箱測試並封裝複用 |

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，配置好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **設計文件** | 僅包含架構與實現方案，可執行程式碼仍在完善中 |
