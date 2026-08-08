# 第8章 · Agent の自己進化

> 重みを変えずに成長する。3 つの学習パラダイム、経験からの学習、そして「ツールの利用者」から「ツールの創造者」への道のりを通じて、Agent を「賢い」段階から「熟練した」段階へと進化させる。

← [メイン README に戻る](../docs/ja/README.md) · 📖 [章の本文を読む](../book-ja/chapter8.ja.md)

## 付随プロジェクト

| 実験 | プロジェクト | 種類 | 説明 |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | 実験 8-1：環境の結果・プロセスルール・言語 Rubric を組み合わせ、証拠付きのカスタマーサービス軌跡診断を形成する |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | 実験 8-2：成功・部分成功・失敗の軌跡を比較し、軌跡横断の Markdown 経験ドキュメントを生成する |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | 実験 8-3：失敗軌跡から最小の Prompt パッチを生成し、境界セットと保持セットでリリースを制御する |
| 8-4 | [browser-use-rpa](browser-use-rpa/) | ✅ | 実験 8-4：ブラウザ軌跡を状態述語付きのワークフローにコンパイルし、リセット再生で検証する |
| 8-5 | [self-modifying-agent](self-modifying-agent/) | ✅ | 実験 8-5：繰り返しの障害をトリガーに、リトライ/サーキットブレーカーのコードパッチ、回帰テスト、カナリアリリースとロールバックを行う |
| 8-6 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Hermes に本書全体と自分のソースを渡す。改善を選んで自分を書き換え、Reviewer の拒否を次の学習に変えながら受理まで進む |
| 8-7 | [self-evolution-eval](self-evolution-eval/) | ✅ | 実験 8-7：学習・転移・ルール変化・保持の 4 段階で長期的な進化を評価する |
| 8-8 | [harness-safety-gate](harness-safety-gate/) | ✅ | 高リスク操作の確認ゲート |
| 8-9 | [ai-style-skill](ai-style-skill/) | ✅ | 執筆フィードバックを検証可能な Skill に変換する。章では曲線引用符 Skill を監査済み合成データと追加学習に接続し、exact-copy の tokenizer/Harness 障害を分離する |

上記の実験はすべて、API キー不要のオフライン入口とユニットテストを提供する。実モデルやブラウザが必要な拡張パスは各プロジェクトの README に記載されている。

## 補足事例

| 実験 | プロジェクト | 関係 |
| :--: | --- | --- |
| 7-8 | [prompt-distillation](prompt-distillation/) | Prompt 蒸留とパラメータ化学習の章横断プロジェクト。訓練手法は第 7 章に属する |
| — | [self-evolving-tools](self-evolving-tools/) | Alita 式のツール発見・カプセル化・再利用。「経験をプログラムとして書き出す」ことの補足事例 |

## プロジェクトの種類

| アイコン | 種類 | 意味 |
| :--: | --- | --- |
| ✅ | **単独実行** | このリポジトリに完全なコードがあり、API キーを設定すれば実行できる |
| 📖 | **再現ガイド** | `git clone` が必要な**外部リポジトリ**に依存する詳細ドキュメント |
| 🚧 | **設計ドキュメント** | アーキテクチャ/実装計画のみで、実行可能なコードは未完成 |
