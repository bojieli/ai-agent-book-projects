# 第 8 章 · 模型後訓練

> 預訓練／Mid-training／SFT／RL 四階段：長上下文課程與資料構造、SFT 協定固化、RL 環境與獎勵，以及從單輪到多輪的樣本效率。

← [返回主目錄](../docs/zh-TW/README.md) · 📖 [讀本章正文](../book/chapter8.md)

## 如何閱讀實驗

正文用短小的機制 skeleton 說明控制流；實驗目錄放完整的 SDK 適配、日誌、測試與驗收證據，不需要逐行讀完每個檔案。

- **Starter:** 先讀目標、最小指令與驗收條件；可從 [cot-distillation](cot-distillation/);
- **Builder:** 沿著入口、核心迴圈、狀態／訊息 schema、工具與驗證器閱讀。
- **Maintainer:** 最後再看測試、證據 manifest、失敗處理、回滾路徑與 provider adapter。

第一次閱讀可先跳過憑證載入、展示層和 provider 相容層；要重現數字時再回來查看。

## 配套專案

| 編號 | 專案 | 型別 | 一句話說明 |
| :--: | --- | :--: | --- |
| 8-1, 8-2 | [learning-from-experience](../chapter1/learning-from-experience/) | ✅ | 在同一尋寶環境執行 Q-learning 與 LLM Agent，從經驗中學習。 |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | ✅ | 將教師範例蒸餾為學生 prompt，並比較品質與成本。 |
| 8-3, 8-4 | [MiniMind-pretrain](MiniMind-pretrain/) | 📖 | 從零預訓練小型 LLM/VLM，理解完整預訓練流程與關鍵技術 |
| 8-5 | [continued-pretraining](continued-pretraining/) | ✅ | 在特定領域資料上持續預訓練，提升目標領域表現 |
| 8-6 | [sesame](sesame/) | ✅ | Sesame CSM 語音 SFT：LoRA 微調 1B TTS 模型，用 `<laugh>`、`<sigh>` 等副語言標記控制表達 |
| 8-6 | [orpheus](orpheus/) | ✅ | Orpheus 3B 語音 SFT：LoRA 微調 TTS 模型，拼接參考音訊實現跨句音色一致的聲音複刻 |
| 8-7 | [MultilingualReasoning](MultilingualReasoning/) | ✅ | 訓練模型在多語言環境下的推理能力，提升跨語言任務表現 |
| 8-9 | [cot-distillation](cot-distillation/) | ✅ | 經 OpenRouter 呼叫 Claude 等前沿模型蒸餾 CoT 軌跡，規則驗證器過濾後生成 SFT 資料（實驗 8-9 配套） |
| 8-10 | [AdaptThink](AdaptThink/) | 📖 | 讓推理模型按問題難度自適應選 Thinking/NoThinking，約束最佳化 + 重要性取樣降成本 45–69% 同時提升準確率 |
| 8-11 | `SFTvsRL/` | 📖 | 系統性對比監督微調與強化學習在不同任務上的效果與適用場景 |
| 8-12 | [SpatialReasoning](SpatialReasoning/) | 📖 | 訓練模型的空間推理能力，處理位置、方向、距離等空間關係 |
| 8-13 | [SimpleVLA-RL](SimpleVLA-RL/) | 📖 | 視覺-語言-動作 RL，讓模型理解視覺輸入並執行相應動作 |
| 8-14 | [retool](retool/) | 📖 | 多輪對話 + 程式碼沙箱提升數學推理，SFT→RL 兩階段；Qwen2.5-32B + AIME 2024 + DAPO + SandboxFusion |
| 8-15 | `AWorld/` · [AWorld-train](AWorld-train/) | 📖 | 基於 AWorld 框架訓練具身 Agent，在虛擬環境中執行任務並從經驗中學習 |
| 8-16 | [RLVP](RLVP/) | 📖 | 獎勵結果、懲罰路徑（RLVP）後訓練研究（實驗 8-16 配套）；完整訓練/評估程式碼在獨立論文倉庫 `19PINE-AI/rlvp`，需自行克隆 |
| 8-17 | [premature-completion-dpo](premature-completion-dpo/) | ✅ | 在 GPU 上以 DPO 修復過早完成 bad case |
| 8-18 | [curly-quote-sft](curly-quote-sft/) | ✅ | 經資料審核的作用域敏感中文彎引號 SFT：10 種文章體裁、9 種程式語言，train/holdout/boundary=1024/256/256；Qwen3-8B exact 96.9%/97.7%，保護區保留率 100% |
| 8-19 | [exact-copy-sft](exact-copy-sft/) | ✅ | 經資料審核的特殊字串 byte-exact 複製 SFT：1024/256/256 筆；Qwen3-8B holdout 78.9%、boundary 80.1%，另有 Qwen3/Qwen2.5/Mistral tokenizer 審核 |
| — | `verl/` | 📖 | 為 LLM RLHF 設計的高效 RL 框架，支援 PPO/GRPO/DAPO 等 |
| — | [Intuitor](Intuitor/) | ✅ | 訓練模型的直覺推理，快速做出合理判斷而不依賴詳細思考鏈 |
| — | `tinker-cookbook/` | 📖 | 收集各種模型訓練的實用技巧與最佳實踐 |

## 專案型別說明

| 圖示 | 型別 | 含義 |
| :--: | --- | --- |
| ✅ | **可獨立執行** | 本倉庫自帶完整程式碼，配置好 API Key 即可執行 |
| 📖 | **復現指南** | 依賴需自行 `git clone` 的**外部倉庫**（訓練框架、評測基準等） |
| 🚧 | **設計文件** | 僅包含架構與實現方案，可執行程式碼仍在完善中 |
