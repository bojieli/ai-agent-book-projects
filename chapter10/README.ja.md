# 第10章 · マルチ Agent の協調

> 集団的知性は個々の知性を超えうる。マルチ Agent の分類フレームワーク、それが本当に単一の Agent を上回るのはいつか、コンテキストを共有する協調と共有しない協調、失敗モード、そして創発する「Agent 社会」。

← [メイン README に戻る](../docs/ja/README.md) · 📖 [章の本文を読む](../book-ja/chapter10.ja.md)

## 付随プロジェクト

| 実験 | プロジェクト | 種類 | 説明 |
| :--: | --- | :--: | --- |
| 10-1 | [staged-system-prompt](staged-system-prompt/) | ✅ | 同じ Coding Agent が、タスクの異なる実行段階（要件明確化 → コード実装 → コードレビュー）で異なるシステムプロンプトとツールセットを読み込む。これにより、単一の会話の中で異なる役割を演じ、異なる挙動を示すことができる。その間、対話履歴とタスク状態は各段階で継続的に共有される。レビューが失敗した場合は、実装段階へ戻ることができる。 |
| 10-2 | [multi-role-transfer](multi-role-transfer/) | ✅ | 共有コンテキスト下での連鎖的なハンドオフを示す。単一のセッションに複数の専門的な役割の Agent が含まれ、それぞれが独自のシステムプロンプトと専用のツールセットを持つ。`transfer_to_agent` ツールを用いて、Agent はタスクの進捗に基づいていつ別の役割に切り替えるかを自律的に決定する。同じ対話履歴を共有しているため、ハンドオフ時に完全なコンテキストが自然に保持される。 |
| 10-3 | [book-translation](book-translation/) | 🚧 | 4役 Manager と単一 Agent 対照には実モデルの小規模結果がある。本文どおり図版とコードを多く含む技術書を使い、品質・効率・token・資源消費を完全比較する作業が残る。 |
| 10-4 | `use-computer-while-calling/` | 📖 | 外部 [TalkAct](https://github.com/19PINE-AI/TalkAct) の固定コミット `7d70007…`。fast/slow Agent は実際に並行実行され、プロセス内 `SharedState` ブラックボード（rolling digest、transcript/action log）と双方向テキストキューで情報を共有する。この版は WebSocket bridge ではない。checkout は同梱されないため、正確な clone と benchmark の入口はメイン README の付録を参照。 |
| 10-5 | [autonomous-phone-registration](autonomous-phone-registration/) | 🚧 | Playwright が実フォームを観測し、実 LLM が `initiate_phone_call_agent` の呼び出しを自律判断する。明示同意が必要な Twilio/ローカル音声経路は検証・再質問・質問と入力の並行処理・秘匿化トレース・任意送信に対応。現在の証拠はスクリプト回答によるブラウザ/LLM/並行処理のみで、PSTN と人間音声は `not_run` のためライブ受入は未完了。 |
| 10-6 | [parallel-web-research](parallel-web-research/) | ✅ | N 個の独立 Playwright ブラウザセッションが実在する大学サイト 10 件を検索し、実 LLM が引用可能な証拠を抽出する。保存済み受入証拠は監視、timeout/error 隔離、単一決済、カスケード終了 ack、資源解放、同一サイトでの 3.142× 並列高速化を含む。 |
| 10-7 | `generative_agents/` | 📖 | スタンフォードの「AI タウン」生成的 Agent（実験 10-7 対応）。外部リポジトリ `joonspk-research/generative_agents` を各自でクローンする必要がある（メイン README の付録を参照） |
| 10-8 | [voice-werewolf](voice-werewolf/) | 🚧 | 自席コンテキストだけを見る実 LLM ユーザーシミュレータを追加し、ツール呼び出しと合成音声＋実 OpenRouter 音声 ASR を必須化。厳格な再検証は誤転写を棄権扱いした初期 2 実行を不合格にした。影響のない v2 は E2E・分離・ルール勝者・3 サイクルを通過したが、村人が占い師を誤追放して戦略評価は不合格。 |
## プロジェクトの種類

| アイコン | 種類 | 意味 |
| :--: | --- | --- |
| ✅ | **単独実行** | このリポジトリに完全なコードがあり、API キーを設定すれば実行できる |
| 📖 | **再現ガイド** | `git clone` が必要な**外部リポジトリ**に依存する詳細ドキュメント |
| 🚧 | **進行中** | 実装または必須の受入証拠が未完了。実行可能コードがあっても完全受入を意味しない |
