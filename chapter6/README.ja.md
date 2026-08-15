# 第6章 · 交互：観察空間と動作空間の拡張

> 知覚と行動をテキストから音声、GUI、そして物理世界へと拡張する。3 つの音声パラダイム（カスケード型/エンドツーエンドの全モーダル型/全二重型）、ストリーミング音声の知覚と合成、Computer Use、そしてロボット操作。

← [メイン README に戻る](../docs/ja/README.md) · 📖 [章の本文を読む](../book-ja/chapter6.ja.md)

## 実験の読み方

本文では短い mechanism skeleton で制御フローを説明し、実験ディレクトリには完全な SDK アダプター、ログ、テスト、受け入れ証拠を置きます。すべてのファイルを一行ずつ読む必要はありません。

- **Starter:** 目的・最小コマンド・受け入れ条件から始め、まず [live-audio](live-audio/);
- **Builder:** エントリポイント、中心ループ、状態／メッセージ schema、ツール、検証器を追います。
- **Maintainer:** 最後にテスト、証拠 manifest、失敗処理、rollback 経路、provider adapter を読みます。

初読では認証情報、表示層、provider 互換層を飛ばし、数値を再現するときに戻ってください。

## 付随プロジェクト

| 実験 | プロジェクト | 種類 | 説明 |
| :--: | --- | :--: | --- |
| 6-1 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | FastAPI で構築された最新のイベント駆動 Agent で、デフォルトで最初の 3 つの MCP サーバーのすべてのツールを統合する。ネイティブな非同期アーキテクチャを用いてクリーンな MCP ツール読み込みを行い、HTTP API を介して複数ソースのイベント（Web、インスタントメッセージング、GitHub、タイマーなど）を受け取る。自動 API ドキュメント（Swagger UI）とバックグラウンド監視機能を提供する。 |
| 6-2 | [async-agent](async-agent/) | ✅ | 単一スレッドの asyncio モデルに基づくイベント駆動非同期 Agent フレームワーク（Flux）の中核を実装する。受信箱イベントキューが緊急度（割り込み/即時/キュー）に応じてタスクをディスパッチし、非同期ツールの並列実行をサポートし、実行中に現在のターンを割り込むことを可能にし、シミュレートされた長時間実行タスクに対するキャンセルと状態照会を提供する。意思決定は実際の LLM（function calling）によって行われる。 |
| 6-3 | [live-audio](live-audio/) | ✅ | 音声認識、AI 対話、音声合成を統合したリアルタイム音声チャットのデモ。複数の AI サービスプロバイダー（OpenAI、OpenRouter、ARK、Siliconflow）をサポートし、低レイテンシの対話体験を提供する。 |
| Add-on | [phone-agent](phone-agent/) | 🚧 | 公式 `pine-voice` SDK の direct/ReAct 経路は実装済みだが、同意・承認済みの E.164 宛先がない。preflight は発信なし・transcript なしを記録し、test double は受入に数えない。 |
| 6-4 | [streaming-speech](streaming-speech/) | ✅ | ストリーミング音声知覚の中核的なトレードオフを示す。連続した音声を徐々に長さを増すセグメントに分割して ASR に供給する。受信した各セグメントは「現在の部分的な認識結果」を生成し、早期のテキスト出力のために極めて低い最初のチャンクのレイテンシを実現する。その代償として、後半の文脈を欠く早期のチャンクは誤る可能性があるが、音声が蓄積するにつれて徐々に収束する。これは「文全体を待ってから認識する」高精度/高レイテンシのアプローチと対照的である。 |
| 6-5 | [end-to-end-speech](end-to-end-speech/) | ✅ | 固定 revision の MiniCPM-o 4.5 を 1 枚の RTX PRO 6000 で実行。end-to-end と self-cascade はともに 3/4 だが意味・副言語の失敗が相補的で、実際の 24kHz 音声出力と検証証拠を保存した。 |
| 6-6 | [controllable-tts](controllable-tts/) | 🚧 | 実 Fish Audio S1 の 4×3×2 参照音声庫と A/B/C メディアは構造 gate を通過。定性 listening study と「人間の客服に近い」評価が残る。 |
| 6-7 | `claude-quickstarts/computer-use-demo/` | 📖 | 外部 `anthropics/claude-quickstarts` を `9bcc95e…` に固定。本文対象はコンテナ化 Ubuntu desktop＋Claude agent loop の Computer Use demo で、quickstarts 全体ではない。 |
| 6-8 | `browser-use/` | 📖 | 外部 `browser-use/browser-use` を `ec9277c…` に固定。本文は `use_vision=True` の visual CLI で Google の San Francisco 天気を検索し、action/screenshot 軌跡を保存する。 |
| 6-9 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | 実機 XLeRobot を遠隔操作し、同じ机の片付け課題（赤いカップをトレーへ、黄色い紙をごみ箱へ、最後に再観察・検証）を行う。 |
| 6-10 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | 同じ机の課題について、シミュレータで理想制御の上限を測る。実機を実行したことを意味しない。 |
| 6-11 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Gemini Robotics-ER 1.5 で実機 XLeRobot を自律制御し、同じ机の片付け課題を行う。 |
| 6-12 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | シミュレータで、同じ課題の開ループ、逐次確認、予測型閉ループを比較する。 |
| 6-13 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | 背景、物体の外観、照明、視覚ノイズを変え、同じ課題を RGB 環境間で評価する。 |

## プロジェクトの種類

| アイコン | 種類 | 意味 |
| :--: | --- | --- |
| ✅ | **単独実行** | このリポジトリに完全なコードがあり、API キーを設定すれば実行できる |
| 📖 | **再現ガイド** | `git clone` が必要な**外部リポジトリ**に依存する詳細ドキュメント |
| 🚧 | **進行中** | 実装はあるが、本文が求める live 実行、許可済み参加者、hardware、または受入証拠が未完了 |
