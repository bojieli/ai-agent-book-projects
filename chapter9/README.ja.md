# 第9章 · マルチモーダルとリアルタイムインタラクション

> 知覚と行動をテキストから音声、GUI、そして物理世界へと拡張する。3 つの音声パラダイム（カスケード型/エンドツーエンドの全モーダル型/全二重型）、ストリーミング音声の知覚と合成、Computer Use、そしてロボット操作。

← [メイン README に戻る](../docs/ja/README.md) · 📖 [章の本文を読む](../book-ja/chapter9.ja.md)

## 付随プロジェクト

| 実験 | プロジェクト | 種類 | 説明 |
| :--: | --- | :--: | --- |
| 9-1 | [live-audio](live-audio/) | ✅ | 音声認識、AI 対話、音声合成を統合したリアルタイム音声チャットのデモ。複数の AI サービスプロバイダー（OpenAI、OpenRouter、ARK、Siliconflow）をサポートし、低レイテンシの対話体験を提供する。 |
| 9-2 | [phone-agent](phone-agent/) | 🚧 | 公式 `pine-voice` SDK の direct/ReAct 経路は実装済みだが、同意・承認済みの E.164 宛先がない。preflight は発信なし・transcript なしを記録し、test double は受入に数えない。 |
| 9-3 | [streaming-speech](streaming-speech/) | ✅ | ストリーミング音声知覚の中核的なトレードオフを示す。連続した音声を徐々に長さを増すセグメントに分割して ASR に供給する。受信した各セグメントは「現在の部分的な認識結果」を生成し、早期のテキスト出力のために極めて低い最初のチャンクのレイテンシを実現する。その代償として、後半の文脈を欠く早期のチャンクは誤る可能性があるが、音声が蓄積するにつれて徐々に収束する。これは「文全体を待ってから認識する」高精度/高レイテンシのアプローチと対照的である。 |
| 9-4 | [end-to-end-speech](end-to-end-speech/) | ✅ | 固定 revision の MiniCPM-o 4.5 を 1 枚の RTX PRO 6000 で実行。end-to-end と self-cascade はともに 3/4 だが意味・副言語の失敗が相補的で、実際の 24kHz 音声出力と検証証拠を保存した。 |
| 9-5 | [controllable-tts](controllable-tts/) | 🚧 | 実 Fish Audio S1 の 4×3×2 参照音声庫と A/B/C メディアは構造 gate を通過。定性 listening study と「人間の客服に近い」評価が残る。 |
| 9-6 | `claude-quickstarts/computer-use-demo/` | 📖 | 外部 `anthropics/claude-quickstarts` を `9bcc95e…` に固定。本文対象はコンテナ化 Ubuntu desktop＋Claude agent loop の Computer Use demo で、quickstarts 全体ではない。 |
| 9-7 | `browser-use/` | 📖 | 外部 `browser-use/browser-use` を `ec9277c…` に固定。本文は `use_vision=True` の visual CLI で Google の San Francisco 天気を検索し、action/screenshot 軌跡を保存する。 |
| 9-8 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | 外部 XLeRobot `3d14695…` の keyboard/Xbox/Joy-Con/VR teleoperation。source と非駆動 preflight のみで、許可済み四方式の実機・pick/place/wipe 証拠はない。 |
| 9-9 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | 外部 XLeRobot `3d14695…`＋RoboCrew。厳密に `gemini-robotics-er-1.5-preview`、角度注釈、forward/left/right tools を使う。許可済み実機 navigation 証拠はない。 |
| 9-10 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | 外部 `lerobot-sim2real` `87d6c1d…` の五段階 RGB→PPO→SO-100 pipeline。ManiSkill/NVIDIA と許可済み実ロボット実行がない。 |
## プロジェクトの種類

| アイコン | 種類 | 意味 |
| :--: | --- | --- |
| ✅ | **単独実行** | このリポジトリに完全なコードがあり、API キーを設定すれば実行できる |
| 📖 | **再現ガイド** | `git clone` が必要な**外部リポジトリ**に依存する詳細ドキュメント |
| 🚧 | **進行中** | 実装はあるが、本文が求める live 実行、許可済み参加者、hardware、または受入証拠が未完了 |
