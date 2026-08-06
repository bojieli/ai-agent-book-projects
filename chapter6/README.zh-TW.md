# 第 6 章 · Agent 的評估

> 把表現變成可比較訊號：評估環境、指標、統計顯著性、評估驅動選型

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter6.md)

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 6-1 | `tau2-bench/` | 📖 | 專注評估 Agent 使用工具進行複雜推理（計算、搜尋、資料處理）的能力 |
| 6-2 | `tau2-bench/` | 📖 | 人工完成 τ²-bench 分級任務並記錄軌跡。 |
| 6-3 | [user-memory-evaluation](../chapter3/user-memory-evaluation/) | ✅ | 四級 Rubric 已在 180 條結構化評判上執行，保留證據並設置幻覺一票否決。 |
| 6-4 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | 在三個系統上執行 60 個案例，並完成成本核算。 |
| 6-5 | [user-memory-policy-eval](user-memory-policy-eval/) | ✅ | 以真實 OpenRouter 呼叫與確定性政策檢查，在 JSON、Markdown 與類 Python 記憶表示上執行 11 個 trajectory-prefix 錯誤案例。 |
| 6-11 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | 完整 4×3×2×60 矩陣保留 1,440/1,440 條真實軌跡，無錯誤或未計價使用，並具備完整檢索/任務指標、互動分析與通過的獨立驗證。 |
| 6-13 | [openvla-robotwin2-eval](openvla-robotwin2-eval/) | ✅ | 單 GPU 正式實驗完成每個 action-chunk 組 256 回合；chunk 1 為 0/256、chunk 25 為 26/256，並保留 512 個 rollout 雜湊。 |
| 6-2 | `terminal-bench/` | 📖 | 測試 Agent 在真實終端機環境的端到端能力（編譯/訓練/部署），約 100 任務 + 執行框架 |
| 6-2 | `SWE-bench/` | 📖 | 評估 LLM 解決真實 GitHub 問題的能力，含 SWE-bench/Lite/Verified/Multimodal 多個版本 |
| 6-2 | `GAIA/` | 📖 | 評估下一代 LLM 的工具/搜尋/自主能力，450+ 個答案明確的非平凡問題，分 3 級難度 |
| 6-2 | `OSWorld/` | 📖 | 評估 Agent 在完整 OS 環境執行複雜任務的能力：檔案管理、應用操作、系統設定 |
| 6-2, 6-12 | `android_world/` | 📖 | 評估 Agent 在 Android 環境的應用導覽、UI 互動與任務完成能力（外部基準倉庫） |
| 6-6 | [tts-quality-eval](tts-quality-eval/) | ✅ | 多種 TTS 設定合成挑戰文字，LLM-as-a-Judge 按 Rubric 逐維度打分，輸出可復現對比表 |
| 6-7 | [elo-leaderboard](elo-leaderboard/) | ✅ | 基於 ELO 評分的 Agent 效能排行榜，透過對戰比較相對能力 |
| 6-8 | [model-action-threshold](model-action-threshold/) | ✅ | 在同一個中性的 Coding Harness 下，比較 GPT-5.6-sol 與 Claude Sonnet 5 從探索轉入首次修改的門檻；18/18 個單元均無 API 錯誤完成，[manifest](model-action-threshold/results/exp6-7-action-threshold-20260731-v1/manifest.json) 以可驗證雜湊綁定軌跡與彙總 |
| 6-9 | [agent-cost-analysis](agent-cost-analysis/) | ✅ | 多輪 Agent 任務（客服退款）全鏈路成本拆解 + KV-cache 友善設計/上下文壓縮的 A/B 節省量化 |
| 6-10 | [model-benchmark](model-benchmark/) | 🚧 | 對多家 OpenAI 相容 API 橫向壓測 TTFT、p50/p95 延遲、吞吐與成功率，一條命令出對比表 |
| 6-12 | [android-world](android-world/) | 📖 | 本書對 T3A Agent 在 AndroidWorld 上的評估報告與失敗分析筆記（實驗 6-12 起點；非基準原始碼） |
| — | [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | 基於合成 DHIS2 風格彙總資料，客觀評估公共衛生報告 Agent 的工具呼叫、計算準確性、證據引用與無依據聲明 |

> 📖 表中帶反引號的外部基準需自行克隆。[`android-world/`](android-world/)（連字號）是本倉庫內的 **T3A 評估分析筆記**（見該目錄 [README](android-world/README.md)），與外部 `android_world/` 基準原始碼不是同一路徑。

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，設定好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **設計文件** | 僅包含架構與實現方案，可執行程式碼仍在完善中 |
