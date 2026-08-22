# 第4章 · ツール

> ツールは Agent の手である。ツールの分類と一般的な設計原則、MCP プロトコルとツール選択の課題、3 種類のツール（知覚、実行、協調）、イベント駆動の非同期 Agent について論じる。

← [メイン README に戻る](../docs/ja/README.md) · 📖 [章の本文を読む](../book-ja/chapter4.ja.md)

## 実験の読み方

本文では短い mechanism skeleton で制御フローを説明し、実験ディレクトリには完全な SDK アダプター、ログ、テスト、受け入れ証拠を置きます。すべてのファイルを一行ずつ読む必要はありません。

- **Starter:** 目的・最小コマンド・受け入れ条件から始め、まず [execution-tools](execution-tools/);
- **Builder:** エントリポイント、中心ループ、状態／メッセージ schema、ツール、検証器を追います。
- **Maintainer:** 最後にテスト、証拠 manifest、失敗処理、rollback 経路、provider adapter を読みます。

初読では認証情報、表示層、provider 互換層を飛ばし、数値を再現するときに戻ってください。

## 付随プロジェクト

| 実験 | プロジェクト | 種類 | 説明 |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | Web 検索、マルチモーダル理解、ファイルシステム操作、公開データソースへのアクセス機能を提供する、包括的な知覚ツール群を構築する。ほとんどの機能は無料かつオープンな API（DuckDuckGo、Open-Meteo、Yahoo Finance、OpenStreetMap など）に基づいており、API キーを必要としない。 |
| 4-2 | [multimodal-agent](multimodal-agent/) | ✅ | Multimodal processing: compare native multimodal, extract-to-text, and tool-based analysis. |
| 4-3 | [execution-tools](execution-tools/) | ✅ | ファイル操作、コードインタープリタ、仮想ターミナル、外部システム統合を含む、安全機構を備えた実行ツール群を実装する。二次的な LLM 承認機構によって危険な操作を防ぎ、複雑な出力を自動的に要約し、コードに対して構文検証を行う。 |
| 4-4 | [collaboration-tools](collaboration-tools/) | ✅ | ブラウザ自動化（browser-use フレームワーク）、Human-in-the-Loop、マルチチャネル通知（Email、Telegram、Slack、Discord）、タイマー管理を含む、包括的な協調能力を提供する。機密操作に対する管理者承認とスケジュールされたタスクのディスパッチをサポートする。 |
| 4-5 | [active-tool-discovery](active-tool-discovery/) | ✅ | 「120 以上のすべてのツールスキーマを注入する」方式と「能動的なオンデマンド発見」方式という 2 つのパラダイムを比較する。後者はシステムプロンプトにいくつかの基本ツールと `discover_tools` メタツールのみを残し、埋め込み類似度を用いてツールライブラリから最も関連性の高い 3〜5 個の専用ツールを取得する。これによりトークンを節約し、過度に長いリストからモデルが汎用ツールを誤って選択・誤用することを防ぐ。 |
| — | [active-tool-selection](active-tool-selection/) | ✅ | インテリジェントなツール選択機構を実装し、Agent が事前定義されたツールセットを受動的に受け入れるのではなく、タスク要件に基づいて最適なツールの組み合わせを能動的に選択できるようにする。 |

> さらに、`chapter4/docker-compose.yml` と `chapter4/DOCKER_DEPLOYMENT.md` は、前述の MCP ツールサーバーをコンテナ化してデプロイするための参考ソリューションを提供する。
## プロジェクトの種類

| アイコン | 種類 | 意味 |
| :--: | --- | --- |
| ✅ | **単独実行** | このリポジトリに完全なコードがあり、API キーを設定すれば実行できる |
| 📖 | **再現ガイド** | `git clone` が必要な**外部リポジトリ**に依存する詳細ドキュメント |
| 🚧 | **設計ドキュメント** | アーキテクチャ/実装計画のみで、実行可能なコードは未完成 |
