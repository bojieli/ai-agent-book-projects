# 第7章 · モデルのポストトレーニング

> 事前学習、SFT、RL の 3 段階を包括的に見渡す。SFT と RL のどちらを選ぶか、RLHF、アルゴリズムの比較、データと環境、そしてモデルにツール呼び出しを教えサンプル効率を高めるための最先端の探求。

← [メイン README に戻る](../docs/ja/README.md) · 📖 [章の本文を読む](../book-ja/chapter7.ja.md)

## 付随プロジェクト

| 実験 | プロジェクト | 種類 | 説明 |
| :--: | --- | :--: | --- |
| 7-1, 7-2 | [learning-from-experience](../chapter1/learning-from-experience/) | ✅ | 同じ宝探し環境で Q-learning と LLM Agent を実行し、経験から学習する。 |
| 7-8 | [prompt-distillation](../chapter8/prompt-distillation/) | ✅ | 教師の例を学生 prompt に蒸留し、品質とコストを比較する。 |
| 7-3, 7-4 | [MiniMind-pretrain](MiniMind-pretrain/) | 📖 | 小型言語モデルをゼロから事前学習し、事前学習の完全なプロセスと主要技術を理解する。 |
| 7-5 | [continued-pretraining](continued-pretraining/) | ✅ | ドメイン固有のデータで継続事前学習を行い、対象ドメインにおけるモデルの性能を向上させる。 |
| 7-6 | [sesame](sesame/) | ✅ | Sesame CSM 音声 SFT：LoRA で 1B TTS モデルを微調整し、`<laugh>`・`<sigh>` などのパラ言語タグで表現を制御 |
| 7-6 | [orpheus](orpheus/) | ✅ | Orpheus 3B 音声 SFT：LoRA で TTS モデルを微調整し、参照音声の連結で文をまたいだ音色の一貫した声の複製を実現 |
| 7-7 | [MultilingualReasoning](MultilingualReasoning/) | ✅ | 複数の言語環境におけるモデルの推論能力を訓練し、言語横断タスクの性能を向上させる。 |
| 7-9 | [cot-distillation](cot-distillation/) | ✅ | OpenRouter 経由で Claude などの最先端モデルから CoT 軌跡を蒸留し、ルール検証器でフィルタリングして SFT データを生成する（実験 7-9 対応） |
| 7-10 | [AdaptThink](AdaptThink/) | 📖 | 推論モデルに、問題の難易度に基づいて推論モード（Thinking と NoThinking）を適応的に選択させる。制約付き最適化と重要度サンプリングを通じて、精度を向上させながら推論コストを大幅に削減する（45〜69%）。DeepSeek-R1-Distill-Qwen モデルに基づき、DAPO アルゴリズムを用いて訓練する。 |
| 7-11 | `SFTvsRL/` | 📖 | 教師ありファインチューニング（SFT）と強化学習（RL）が異なるタスクで持つ有効性を体系的に比較し、両手法の長所、短所、適した適用シナリオを分析する。 |
| 7-12 | [SpatialReasoning](SpatialReasoning/) | 📖 | 位置、方向、距離などの空間関係を含む問題を処理するため、モデルの空間推論能力の訓練に焦点を当てる。 |
| 7-13 | [SimpleVLA-RL](SimpleVLA-RL/) | 📖 | 強化学習の訓練において視覚、言語、行動を組み合わせ、モデルが視覚入力を理解して対応する行動を実行できるようにする。 |
| 7-14 | [retool](retool/) | 📖 | 複数ターンの対話とコードサンドボックスを用いて、大規模言語モデルの数学的推論能力を強化する。SFT と RL の 2 段階の訓練プロセスを通じて、モデルはコード実行環境を用いて数学問題の解決を支援することを学ぶ。Qwen2.5-32B-Instruct に基づき、AIME 2024 データセットで DAPO アルゴリズムと SandboxFusion サンドボックスを用いて訓練する。 |
| 7-15 | `AWorld/` · [AWorld-train](AWorld-train/) | 📖 | AWorld フレームワークに基づいて身体化された Agent を訓練し、Agent が仮想環境で複雑なタスクを実行し、経験から学習できるようにする。 |
| 7-16 | [RLVP](RLVP/) | 📖 | 結果に報酬を与え、経路にペナルティを課す（RLVP）事後学習の研究（実験 7-16 対応）。完全な訓練・評価コードは独立した論文リポジトリ `19PINE-AI/rlvp` にあり、各自でクローンが必要 |
| 7-17 | [premature-completion-dpo](premature-completion-dpo/) | ✅ | GPU 上の早期完了 bad case に対する DPO 修正。 |
| 7-18 | [curly-quote-sft](curly-quote-sft/) | ✅ | 監査済みスコープ依存中国語曲線引用符 SFT：10 文書ジャンル・9 プログラミング言語で train/holdout/boundary=1024/256/256、Qwen3-8B は exact 96.9%/97.7%、保護領域保持率 100%。 |
| 7-19 | [exact-copy-sft](exact-copy-sft/) | ✅ | 監査済み byte-exact 特殊文字列コピー SFT：1024/256/256 件、Qwen3-8B は holdout 78.9%、boundary 80.1%、Qwen3/Qwen2.5/Mistral tokenizer 監査付き。 |
| — | `verl/` | 📖 | verl は、大規模言語モデルの RLHF 訓練のために特別に設計された効率的な強化学習フレームワークで、PPO、GRPO、DAPO などのさまざまなアルゴリズムをサポートする。 |
| — | [Intuitor](Intuitor/) | ✅ | モデルの直感的推論能力を訓練し、詳細な思考連鎖を必要とせずに迅速かつ合理的な判断を下せるようにする。 |
| — | `tinker-cookbook/` | 📖 | モデル訓練のためのさまざまな実践的なコツとベストプラクティスを収集する。 |

## プロジェクトの種類

| アイコン | 種類 | 意味 |
| :--: | --- | --- |
| ✅ | **単独実行** | このリポジトリに完全なコードがあり、API キーを設定すれば実行できる |
| 📖 | **再現ガイド** | `git clone` が必要な**外部リポジトリ**に依存する詳細ドキュメント |
| 🚧 | **設計ドキュメント** | アーキテクチャ/実装計画のみで、実行可能なコードは未完成 |
