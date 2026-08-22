# 第 9 章 · Agent 的自我進化

> 不改權重也能成長：經驗學習、從工具使用者到創造者

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter9.md)

## 如何閱讀實驗

正文用短小的機制 skeleton 說明控制流；實驗目錄放完整的 SDK 適配、日誌、測試與驗收證據，不需要逐行讀完每個檔案。

- **Starter:** 先讀目標、最小指令與驗收條件；可從 [trajectory-verifier](trajectory-verifier/);
- **Builder:** 沿著入口、核心迴圈、狀態／訊息 schema、工具與驗證器閱讀。
- **Maintainer:** 最後再看測試、證據 manifest、失敗處理、回滾路徑與 provider adapter。

第一次閱讀可先跳過憑證載入、展示層和 provider 相容層；要重現數字時再回來查看。

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 9-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | 實驗 9-1：用環境結果、過程規則和語言 Rubric 形成帶證據的客服軌跡診斷 |
| 9-2 | [gaia-experience](gaia-experience/) | ✅ | 基於 AWorld + GAIA 的「學習-應用」閉環：自動總結成功軌跡為結構化經驗，在新任務中檢索應用 |
| 9-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | 以 tau-bench 航空客服「過度轉接」為例，Coding Agent 讀/改 prompt 檔案 → 重新評測 → 驗證閉環 |
| 9-4 | 正文實驗 | 🚧 | 實驗 9-4：從使用者回饋進化「需求澄清 + Spec 確認」Skill，正文提供三臂 A/B 設計與發布門檻 |
| 9-5 | [browser-use-rpa](browser-use-rpa/) | ✅ | 實驗 9-5：瀏覽器工作流錄製系統，把重複操作封裝為參數化工具，透過重置與回放驗證 |
| 9-6 | [self-modifying-agent](self-modifying-agent/) | ✅ | 實驗 9-6：由重複故障觸發重試/熔斷程式碼補丁、迴歸、灰度與回滾 |
| 9-7 | [harness-safety-gate](harness-safety-gate/) | ✅ | 實驗 9-7：由使用者糾正與事後審計進化高風險操作確認門禁 |
| 9-8 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | 實驗 9-8：把整本書與原始碼交給 Hermes；它讀完後選擇一項改進、親手修改自己，並把每次 Reviewer 退回變成下一輪學習，直到通過 |
| 9-9 | [self-evolution-eval](self-evolution-eval/) | ✅ | 實驗 9-9：三臂、3 seeds、14 任務的長期學習、遷移、規則替換與保留評估 |

以上實驗都提供無需 API Key 的離線入口和單元測試；需要真實模型或瀏覽器的擴充路徑在各專案 README 中另行說明。

## 補充案例

| 編號 | 專案 | 關係 |
| :--: | --- | --- |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | 將複雜提示的效果蒸餾進模型引數，減少推理提示長度，把上下文經驗固化為引數化知識 |
| — | [self-evolving-tools](self-evolving-tools/) | Alita 式「最小預定義，最大自我進化」：五個通用元工具，自己上網找庫/讀文件/沙箱測試並封裝複用 |
| — | [ai-style-skill](ai-style-skill/) | 寫作型 Skill 補充案例；正文示例已移至第二章 |

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，配置好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **設計文件** | 僅包含架構與實現方案，可執行程式碼仍在完善中 |
