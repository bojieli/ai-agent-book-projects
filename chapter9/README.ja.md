# 第9章 · Agent の自己進化

> 重みを変えずに成長する。3 つの学習パラダイム、経験からの学習、そして「ツールの利用者」から「ツールの創造者」への道のりを通じて、Agent を「賢い」段階から「熟練した」段階へと進化させる。

← [メイン README に戻る](../docs/ja/README.md) · 📖 [章の本文を読む](../book-ja/chapter9.ja.md)

## 実験の読み方

本文では短い mechanism skeleton で制御フローを説明し、実験ディレクトリには完全な SDK アダプター、ログ、テスト、受け入れ証拠を置きます。すべてのファイルを一行ずつ読む必要はありません。

- **Starter:** 目的・最小コマンド・受け入れ条件から始め、まず [trajectory-verifier](trajectory-verifier/);
- **Builder:** エントリポイント、中心ループ、状態／メッセージ schema、ツール、検証器を追います。
- **Maintainer:** 最後にテスト、証拠 manifest、失敗処理、rollback 経路、provider adapter を読みます。

初読では認証情報、表示層、provider 互換層を飛ばし、数値を再現するときに戻ってください。

## 付随プロジェクト

| 実験 | プロジェクト | 種類 | 説明 |
| :--: | --- | :--: | --- |
| 9-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | 実験 9-1：環境の結果・プロセスルール・言語 Rubric を組み合わせ、証拠付きのカスタマーサービス軌跡診断を形成する |
| 9-2 | [gaia-experience](gaia-experience/) | ✅ | 実験 9-2：成功・部分成功・失敗の軌跡を比較し、軌跡横断の Markdown 経験ドキュメントを生成する |
| 9-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | 実験 9-3：失敗軌跡から最小の Prompt パッチを生成し、境界セットと保持セットでリリースを制御する |
| 9-4 | 本文の対照実験 | 🚧 | 実験 9-4：ユーザーフィードバックから「要件明確化 + Spec 確認」Skill を進化させる。本文は三アームの A/B 設計、指標、リリース基準を示すが、付随する実装は未提供 |
| 9-5 | [browser-use-rpa](browser-use-rpa/) | ✅ | 実験 9-5：ブラウザ軌跡を状態述語付きのワークフローにコンパイルし、リセット再生で検証する |
| 9-6 | [self-modifying-agent](self-modifying-agent/) | ✅ | 実験 9-6：繰り返しの障害をトリガーに、リトライ/サーキットブレーカーのコードパッチ、回帰テスト、カナリアリリースとロールバックを行う |
| 9-7 | [harness-safety-gate](harness-safety-gate/) | ✅ | 高リスク操作の確認ゲート |
| 9-8 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Hermes に本書全体と自分のソースを渡す。改善を選んで自分を書き換え、Reviewer の拒否を次の学習に変えながら受理まで進む |
| 9-9 | [self-evolution-eval](self-evolution-eval/) | ✅ | 実験 9-9：学習・転移・ルール変化・保持の 4 段階で長期的な進化を評価する |

上記の実験はすべて、API キー不要のオフライン入口とユニットテストを提供する。実モデルやブラウザが必要な拡張パスは各プロジェクトの README に記載されている。

## 補足事例

| 実験 | プロジェクト | 関係 |
| :--: | --- | --- |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | Prompt 蒸留とパラメータ化学習の章横断プロジェクト。訓練手法は第 8 章に属する |
| — | [self-evolving-tools](self-evolving-tools/) | Alita 式のツール発見・カプセル化・再利用。「経験をプログラムとして書き出す」ことの補足事例 |
| — | [ai-style-skill](ai-style-skill/) | 執筆フィードバックを検証可能な Skill に変換する。章では曲線引用符 Skill を監査済み合成データと追加学習に接続し、exact-copy の tokenizer/Harness 障害を分離する |

## プロジェクトの種類

| アイコン | 種類 | 意味 |
| :--: | --- | --- |
| ✅ | **単独実行** | このリポジトリに完全なコードがあり、API キーを設定すれば実行できる |
| 📖 | **再現ガイド** | `git clone` が必要な**外部リポジトリ**に依存する詳細ドキュメント |
| 🚧 | **設計ドキュメント** | アーキテクチャ/実装計画のみで、実行可能なコードは未完成 |
