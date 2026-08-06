# 第6章 · Agent の評価

> Agent の性能を比較可能なシグナルに変える。評価環境、データセット設計、指標体系、統計的有意性、可観測性、評価駆動の選定、そしてプロダクショングレードの内部評価とシミュレーション環境を扱う。

← [メイン README に戻る](../docs/ja/README.md) · 📖 [章の本文を読む](../book-ja/chapter6.ja.md)

## 付随プロジェクト

| 実験 | プロジェクト | 種類 | 説明 |
| :--: | --- | :--: | --- |
| 6-1 | `tau2-bench/` | 📖 | 計算、検索、データ処理などのシナリオを含め、複雑な推論のためにツールを使う Agent の能力の評価に焦点を当てる。 |
| 6-2 | `tau2-bench/` | 📖 | τ²-bench の段階別タスクを手動で完了し、軌跡を記録する。 |
| 6-3 | [user-memory-evaluation](../chapter3/user-memory-evaluation/) | ✅ | 4段階 Rubric を180件の構造化判定に適用し、根拠とハルシネーション拒否を記録する。 |
| 6-4 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | 60ケースを3システムで実行し、コストを完全に集計する。 |
| 6-5 | [user-memory-policy-eval](user-memory-policy-eval/) | ✅ | JSON、Markdown、Python 風のメモリ表現を対象に、実際の OpenRouter 呼び出しと決定論的なポリシーチェックで 11 件の trajectory-prefix 不良ケースを実行する。 |
| 6-11 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | 完全な 4×3×2×60 マトリクスで 1,440/1,440 件の実軌跡をエラーや未課金利用なしに保持し、検索・タスク指標と相互作用分析を完備、独立検証にも合格。 |
| 6-13 | [openvla-robotwin2-eval](openvla-robotwin2-eval/) | ✅ | 単一 GPU の正式実験で各 action-chunk 群 256 エピソードを完了。chunk 1 は 0/256、chunk 25 は 26/256 で、512 rollout のハッシュを保存。 |
| 6-2 | `terminal-bench/` | 📖 | Terminal-Bench は、実際のターミナル環境における AI Agent の性能をテストするためのベンチマークである。コードのコンパイルからモデルの訓練、サーバーのセットアップまで、Agent が実際のエンドツーエンドタスクをどう処理するかを評価する。約 100 タスクのデータセットと実行フレームワークを含み、さまざまな Agent 実装をサポートする。 |
| 6-2 | `SWE-bench/` | 📖 | SWE-bench は、大規模言語モデルが実際の GitHub issue を解決する能力を評価するためのベンチマークである。コードベースと issue の説明が与えられると、モデルは問題を解決するパッチを生成しなければならない。SWE-bench、SWE-bench Lite、SWE-bench Verified、SWE-bench Multimodal という複数のバージョンを含む。 |
| 6-2 | `GAIA/` | 📖 | GAIA は次世代の LLM（ツール拡張、効率的なプロンプティング、検索アクセスなどを備えたもの）を評価することを目的としている。さまざまな程度のツール利用と自律性を必要とし、曖昧さのない回答を持つ 450 以上の非自明な問題を含む。3 つの難易度レベルに分かれている。 |
| 6-2 | `OSWorld/` | 📖 | ファイル管理、アプリケーション操作、システム構成を含む、完全なオペレーティングシステム環境内で複雑なタスクを実行する Agent の能力を評価する。 |
| 6-2, 6-12 | `android_world/` | 📖 | アプリのナビゲーション、UI 操作、タスク完了能力を含む、Android モバイル環境における Agent の性能を評価する。 |
| 6-6 | [tts-quality-eval](tts-quality-eval/) | ✅ | さまざまな TTS 構成（異なるモデル/音声/速度）を用いて同じ難易度の高いテキストセットを合成し、次にマルチモーダルの LLM-as-a-Judge を用いて Rubric に従って各次元（明瞭さ、自然さなど）を採点し、結果を再現可能な構成比較表に集約する。 |
| 6-7 | [elo-leaderboard](elo-leaderboard/) | ✅ | ELO レーティングシステムに基づく Agent 性能リーダーボードを実装し、ペアワイズ比較を通じて異なる Agent の相対的な能力を評価する。 |
| 6-8 | [model-action-threshold](model-action-threshold/) | ✅ | 同一の中立的な Coding Harness の下で、GPT-5.6-sol と Claude Sonnet 5 が探索から最初の編集へ移るしきい値を比較する。18/18 セルが API エラーなしで完了し、[manifest](model-action-threshold/results/exp6-7-action-threshold-20260731-v1/manifest.json) が軌跡と集計を検証可能なハッシュで結び付ける。 |
| 6-9 | [agent-cost-analysis](agent-cost-analysis/) | ✅ | 典型的な複数ターンの Agent タスク（カスタマーサービスの返金）に対して全チェーンのコスト内訳を行う。カスタムの軽量トレーシングシステムを用いて各 LLM 呼び出しの入力/出力/キャッシュトークン、レイテンシ、コストを記録し、集計して「どのステップが最も高価か」を特定し、次に A/B テストを用いて KV Cache に優しい設計とコンテキスト圧縮による実際の節約を定量化する。 |
| 6-10 | [model-benchmark](model-benchmark/) | 🚧 | 複数の OpenAI 互換 LLM API プロバイダーの横断的なベンチマークを実施する。ストリーミングインターフェースを用いて Time to First Token（TTFT）を正確に測定し、並行実行下でのエンドツーエンドレイテンシのパーセンタイル（p50/p95）、スループット、成功率を算出する。単一のコマンドで多次元の比較表を生成し、モデル選定がリーダーボードを見るだけではなく多面的なトレードオフであることを示す。 |
| 6-12 | [android-world](android-world/) | 📖 | 本書による AndroidWorld 上での T3A Agent の評価レポートと失敗分析ノート（実験 6-12 の起点。ベンチマークのソースコードではない） |
| — | [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | 合成 DHIS2 スタイルの集計データに基づき、公衆衛生レポート Agent のツール呼び出し、計算精度、証拠引用、根拠のない主張を客観的に評価する。 |

> バッククォート表記の外部ベンチマークは別途 clone が必要です。[`android-world/`](android-world/)（ハイフン区切り）は本リポジトリ内の **T3A 評価分析ノート**（同ディレクトリの [README](android-world/README.md) を参照）であり、外部の `android_world/` ベンチマークソースとは別パスです。

## プロジェクトの種類

| アイコン | 種類 | 意味 |
| :--: | --- | --- |
| ✅ | **単独実行** | このリポジトリに完全なコードがあり、API キーを設定すれば実行できる |
| 📖 | **再現ガイド** | `git clone` が必要な**外部リポジトリ**に依存する詳細ドキュメント |
| 🚧 | **設計ドキュメント** | アーキテクチャ/実装計画のみで、実行可能なコードは未完成 |
