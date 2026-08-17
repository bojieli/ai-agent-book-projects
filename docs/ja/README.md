# AI Agent 徹底解説: 設計原理とエンジニアリング実践

[![Stars](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](../../LICENSE) [![PDF](https://img.shields.io/badge/PDF-download-success.svg)](#-電子書籍) [![Languages](https://img.shields.io/badge/translations-13%20languages-informational.svg)](#-電子書籍)
[![Trending GitHub Project of the Day](https://img.shields.io/badge/GitHub%20Trending-Project%20of%20the%20Day-orange?logo=github)](https://github.com/trending)

**[中文](../../README.md) · [English](../en/README.md) · [Español](../es/README.md) · [Bahasa Indonesia](../id/README.md) · [العربية](../ar/README.md) · [繁體中文（台灣）](../zh-TW/README.md) · [Русский](../ru/README.md) · [Tiếng Việt](../vi/README.md) · [தமிழ்](../ta/README.md) · 日本語 ← 現在 · [Türkçe](../tr/README.md) · [한국어](../ko/README.md) · [Magyar](../hu/README.md)**

**Agent = LLM + コンテキスト + ツール** — 本書はこの中核となる公式を軸に、全10章を通じて AI エージェントを原理からエンジニアリング実践まで解説します。本文、図版、**103 個の付随実験**はすべてオープンソースです。ぜひ自分の手で実験を動かしてみてください。

> 🚧 **バージョン 2.0 への再編を進めています：** 本書はバージョン 1.4 から 2.0 へ移行し、内容を新しい学習経路に沿って再構成しました。第 6〜9 章は現在、「交互作用：観察空間と行動空間の拡張」「Agent の評価」「モデルのポストトレーニング」「Agent の継続的進化」です。公開済み PDF は一時的に旧構成のままの場合があります。章の配置・番号・実験入口については、この README とリポジトリ内の本文を正とします。

| 📚 基礎から本番まで **10 章** の本文 | 📂 **103 個** の付随プロジェクト（70 個以上が単独実行可能） | 🌐 **13 言語**: 中 / 英 / 西 / インドネシア / アラビア / 繁體中文（台灣） / 露 / タミル / 越 / 日 / 土 / 韓 / ハンガリー |
| :---: | :---: | :---: |

## 📖 電子書籍

> 📥 **ダウンロード**（全文、無料でオープンソース）。以下のリンクは常に `main` ブランチの最新ビルドを指します。固定版は [Releases](https://github.com/bojieli/ai-agent-book/releases) ページを参照してください。
> - **中国語（原版）**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.epub)
> - **英語**（コミュニティ翻訳、[@nsdevaraj](https://github.com/nsdevaraj)、[@whanyu1212](https://github.com/whanyu1212)）: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.epub)
> - **スペイン語**（コミュニティ翻訳、[@santhreal](https://github.com/santhreal)）: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.epub)
> - **アラビア語**（コミュニティ翻訳、[@TheSyBuilder](https://github.com/TheSyBuilder)）: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.epub)
> - **繁体字中国語（台湾）**（コミュニティ翻訳、[@tigercosmos](https://github.com/tigercosmos)）: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.epub)
> - **ロシア語**（コミュニティ翻訳、[@ui99ru](https://github.com/ui99ru)）: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.epub)
> - **タミル語**（コミュニティ翻訳、[@nsdevaraj](https://github.com/nsdevaraj)）: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.epub)
> - **ベトナム語**（コミュニティ翻訳、[@toanalien](https://github.com/toanalien)）: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.epub)
> - **日本語**（コミュニティ翻訳、[@eltociear](https://github.com/eltociear)）: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.epub)
> - **トルコ語**（コミュニティ翻訳、[@memisemre](https://github.com/memisemre)）: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.epub)
> - **韓国語**（コミュニティ翻訳、[@JeongJaeSoon](https://github.com/JeongJaeSoon)）: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.epub)

中国語の本文ソースは [`book/`](../../book/) にあります。英語/スペイン語/アラビア語/繁体字中国語（台湾）/ロシア語/タミル語/ベトナム語/日本語/トルコ語/韓国語版はコミュニティによる貢献であり（中国語原版より遅れる場合があります）、それぞれ [`book-en/`](../../book-en/)、[`book-es/`](../../book-es/)、[`book-ar/`](../../book-ar/)、[`book-zhtw/`](../../book-zhtw/)、[`book-ru/`](../../book-ru/)、[`book-ta/`](../../book-ta/)、[`book-vi/`](../../book-vi/)、[`book-ja/`](../../book-ja/)、[`book-tr/`](../../book-tr/)、[`book-ko/`](../../book-ko/) にあります。

<details>
<summary><b>🔧 自分で PDF / EPUB をビルドしますか？</b>（PDF には pandoc / xelatex / ElegantBook が必要）</summary>

- **EPUB**: 共通のビルドスクリプトを使用します。[EPUB ビルド手順](../../EPUB.md) を参照してください
- **アラビア語 PDF**: `cd book-ar && bash build_pdf.sh` でビルドできます
- **本文ソース**: `book/introduction.md`（引言）、`book/chapter1.md` ～ `book/chapter10.md`（第1〜10章）、`book/afterword.md`（後記）
- **ビルド**: pandoc、xelatex、ElegantBook ドキュメントクラスと必要なフォントをインストールしてから、次を実行します

  ```bash
  cd book && bash build_pdf.sh
  ```

  図版は SVG ファイルとして `book/images/` に保存され、ビルド時に直接使用されます。組版の詳細は `book/preamble.tex` と `book/*.lua` を参照してください。

</details>

## 📑 内容早わかり（第1〜10章）

本書は中核となる公式 **Agent = LLM + コンテキスト + ツール** を軸に展開し、10章が段階的に積み上がります。

| 章 | テーマ | 一言でいうと | 本文 | コード |
| :--: | --- | --- | :--: | :--: |
| 1 | 🚀 **AI Agent 入門** | **Agent = LLM + コンテキスト + ツール**。Harness エンジニアリングこそが真の競争力 | [読む](../../book-ja/chapter1.ja.md) | [3](../../chapter1/README.ja.md) |
| 2 | 🎯 **コンテキストエンジニアリング** | コンテキストが能力の上限を決める: KV Cache、プロンプトエンジニアリング、Agent Skills、コンテキスト圧縮 | [読む](../../book-ja/chapter2.ja.md) | [10](../../chapter2/README.ja.md) |
| 3 | 📚 **ユーザーメモリと知識ベース** | セッションをまたいでユーザーを記憶し、外部知識を接続する: ユーザーメモリ、RAG、構造化インデックス、ナレッジグラフ | [読む](../../book-ja/chapter3.ja.md) | [12](../../chapter3/README.ja.md) |
| 4 | 🛠️ **ツール** | ツールは Agent の手足: MCP、知覚・実行・協調ツール、能動的なツール発見 | [読む](../../book-ja/chapter4.ja.md) | [5](../../chapter4/README.ja.md) |
| 5 | 💻 **Coding Agent とコード生成** | コードは「新しいツールを生み出せるツール」。本番グレードの Coding Agent の全体像 | [読む](../../book-ja/chapter5.ja.md) | [13](../../chapter5/README.ja.md) |
| 6 | 🎙️ **交互作用：観察空間と行動空間の拡張** | モダリティと時間という二つの次元から Agent の観察・行動空間を拡張する：非同期・イベント駆動、音声対話、Computer Use、ロボティクス | [読む](../../book-ja/chapter6.ja.md) | [13](../../chapter6/README.ja.md) |
| 7 | 🎯 **Agent の評価** | パフォーマンスを比較可能なシグナルに変える: 評価環境、指標、統計的有意性、評価駆動の選定 | [読む](../../book-ja/chapter7.ja.md) | [13](../../chapter7/README.ja.md) |
| 8 | 🧠 **モデルのポストトレーニング** | 事前学習/SFT/RL の3段階: いつ SFT を選び、いつ RL を選ぶか、ツール呼び出しの内在化、サンプル効率 | [読む](../../book-ja/chapter8.ja.md) | [19](../../chapter8/README.ja.md) |
| 9 | 🔄 **Agent の継続的進化** | 運用軌跡を学習シグナルへ変換し、知識・指示・プログラム・パラメータを更新する | [読む](../../book-ja/chapter9.ja.md) | [9](../../chapter9/README.ja.md) |
| 10 | 🤝 **マルチ Agent 協調** | 集合知は個を上回る: 協調フレームワーク、コンテキストの共有/隔離、創発する「Agent 社会」 | [読む](../../book-ja/chapter10.ja.md) | [6](../../chapter10/README.ja.md) |
> 💡 **読む** = GitHub 上で章の本文（markdown）を読む。**N** = その章の付随プロジェクト数。クリックでコードを表示。プロジェクトの種類（✅ 単独実行 / 📖 再現 / 🚧 設計）は各章の README で説明しています。
>
> 📚 本書を効率的に読むには？ **[学習のヒント](LEARNING.md)**（中核となる考え方、学習パス、難易度レベル、実践のヒント）を参照してください。

## 💻 付属実験を実行する

共通の対応範囲は **Python 3.11～3.13** です。リポジトリのルートで章ごとに依存関係をインストールします。別の章では `ch1` を `ch2` ～ `ch10` に置き換えてください。

```bash
# 推奨：コミット済みの uv.lock を使用し、再現可能な章別環境を構築
uv sync --locked --extra ch1

# uv を使わない場合：pip で pyproject.toml から再解決
python -m pip install -e ".[ch1]"
```

モデルを呼び出す実験を実行する前に、その実験の README に従って認証情報を設定してください。ルート設定に対応する実験では `.env.example` を `.env` にコピーして少なくとも1つの provider key を入力できますが、一部の実験では実験ディレクトリ内の `.env` または環境変数の export が必要です。ローカル Ollama と `--provider ollama` は、その実験の README または CLI が明示している場合にのみ使用してください。

インストール後はリポジトリのルートから実験を実行できます。

```bash
uv run python chapter1/context/main.py
# pip でインストールした場合：python chapter1/context/main.py
```

- `uv` の導入方法は[公式ガイド](https://docs.astral.sh/uv/getting-started/installation/)を参照してください。`pip` も引き続き利用できますが、ロックファイルは使用しません。
- 移行期間中は各実験の `requirements.txt` も引き続きサポートします。単独プロジェクトや特殊なバージョン制約に適しています。
- `all` は CPU 向けの広範な構成であり、すべての実験を含むわけではありません。`uv sync` は毎回現在の選択に正確に同期するため、特殊な extra は同じコマンドにまとめてください。例: `uv sync --locked --extra ch2 --extra vllm` または `uv sync --locked --extra ch7 --extra unsloth`。pip では `python -m pip install -e ".[ch2,vllm]"` です。
- ブラウザ、CUDA、FFmpeg、Ollama、Playwright ブラウザ、外部リポジトリなどのシステム依存関係は各実験の README に従ってください。第8章の一部の同梱サードパーティコンポーネントには Python 3.12 以上が必要です。

## 🔑 API キー

学習を円滑に進めるため、いくつかのプラットフォームで API キーを申請することをおすすめします。モデル選定については [このガイド](https://01.me/2025/07/llm-api-setup/) を参照してください。

| プラットフォーム | リンク | 備考 |
| --- | --- | --- |
| **Kimi**（Moonshot） | <https://platform.moonshot.cn/> | Kimi シリーズ。長文コンテキストと Agent 能力に強い |
| **Zhipu GLM** | <https://open.bigmodel.cn/> | GLM-4.6 など。中国語能力が高くコストパフォーマンスに優れる |
| **Siliconflow** | <https://siliconflow.cn/> | さまざまなオープンソースモデル（DeepSeek、Qwen など） |
| **Volcano Engine** | <https://www.volcengine.com/product/ark> | ByteDance Doubao（クローズドソース）。中国国内で低レイテンシ |
| **OpenRouter** | <https://openrouter.ai/> | Gemini / Claude / GPT-5 などにワンストップでアクセス（公式 API は海外 IP/決済が必要。OpenAI は海外での本人確認も必要） |

> 🧪 実験の実行状況、証拠、未達の受け入れ条件は [`EXPERIMENT_STATUS.md`](../EXPERIMENT_STATUS.md) で別途管理しています。ソースコードの clone やインストールだけでは実験完了の証明になりません。

## 📦 付録 · 外部リポジトリの取得

第6・7・9・10章のベンチマーク、訓練フレームワーク、ロボットプラットフォーム向けの23個の外部リポジトリは（サイズとライセンスの都合上）**同梱されていません**。対応するディレクトリに clone する必要があります。

### 一括 clone スクリプト

<details>
<summary><b>🔧 clone コマンドを展開</b>（23個の外部リポジトリ）</summary>

```bash
# 第6章 · 評価ベンチマーク
git clone https://github.com/google-research/android_world.git         chapter7/android_world
git clone https://huggingface.co/datasets/gaia-benchmark/GAIA          chapter7/GAIA
git clone https://github.com/xlang-ai/OSWorld.git                      chapter7/OSWorld
git clone https://github.com/SWE-bench/SWE-bench.git                   chapter7/SWE-bench
git clone https://github.com/sierra-research/tau2-bench.git            chapter7/tau2-bench
git clone https://github.com/laude-institute/terminal-bench.git        chapter7/terminal-bench

# 第8章 · 訓練フレームワーク（bojieli/* は書籍向けに調整された fork）
git clone https://github.com/bojieli/minimind.git                      chapter8/MiniMind-pretrain/minimind      # 実験 8-3 LLM をゼロから訓練
git clone https://github.com/bojieli/minimind-v.git                    chapter8/MiniMind-pretrain/minimind-v    # 実験 8-4 VLM をゼロから訓練（投影層）
git clone https://github.com/bojieli/AdaptThink.git                    chapter8/AdaptThink-original
git clone https://github.com/bojieli/AWorld.git                        chapter8/AWorld
git clone https://github.com/bojieli/SFTvsRL.git                       chapter8/SFTvsRL
git clone https://github.com/bojieli/verl.git                          chapter8/verl
git clone https://github.com/bojieli/SandboxFusion.git chapter8/SandboxFusion && git -C chapter8/SandboxFusion fetch origin 4a0d573ebd64c98234c190a9d1d49e4276199a0c && git -C chapter8/SandboxFusion checkout --detach 4a0d573ebd64c98234c190a9d1d49e4276199a0c && test "$(git -C chapter8/SandboxFusion rev-parse HEAD)" = "4a0d573ebd64c98234c190a9d1d49e4276199a0c"  # Exp 8-14 code sandbox
git clone https://github.com/thinking-machines-lab/tinker-cookbook.git chapter8/tinker-cookbook
git clone https://github.com/19PINE-AI/rlvp.git                        chapter8/RLVP/rlvp                       # 実験 8-16 RLVP 論文コード
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git                 chapter8/SimpleVLA-RL/SimpleVLA-RL       # 実験 8-13 vision-language-action RL

# 第9章 · ブラウザ自動化と Claude サンプル
git clone https://github.com/browser-use/browser-use.git               chapter6/browser-use
git clone https://github.com/anthropics/claude-quickstarts.git         chapter6/claude-quickstarts
git clone https://github.com/Vector-Wangel/XLeRobot.git chapter6/XLeRobot && git -C chapter6/XLeRobot fetch origin 3d14695e40c9c68229c0aacffca6053c75cd3eb6 && git -C chapter6/XLeRobot checkout --detach 3d14695e40c9c68229c0aacffca6053c75cd3eb6 && test "$(git -C chapter6/XLeRobot rev-parse HEAD)" = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"  # Exp 6-9/6-11 shared
git clone https://github.com/Grigorij-Dudnik/RoboCrew.git chapter6/RoboCrew && git -C chapter6/RoboCrew fetch origin c749148f29bd14e61347f9fc3530c343fff0d994 && git -C chapter6/RoboCrew checkout --detach c749148f29bd14e61347f9fc3530c343fff0d994 && test "$(git -C chapter6/RoboCrew rev-parse HEAD)" = "c749148f29bd14e61347f9fc3530c343fff0d994"  # Exp 6-10/6-11; RoboCrew v0.3.1
git clone https://github.com/StoneT2000/lerobot-sim2real.git chapter6/lerobot-sim2real && git -C chapter6/lerobot-sim2real fetch origin 87d6c1d969f6e0ca4dc5697940804e231118a63a && git -C chapter6/lerobot-sim2real checkout --detach 87d6c1d969f6e0ca4dc5697940804e231118a63a && test "$(git -C chapter6/lerobot-sim2real rev-parse HEAD)" = "87d6c1d969f6e0ca4dc5697940804e231118a63a"  # Exp 6-13

# 第10章 · デュアル Agent アーキテクチャ（現在は独立した TalkAct プロジェクト）+ Stanford AI Town
git clone https://github.com/19PINE-AI/TalkAct.git                     chapter10/use-computer-while-calling
git clone https://github.com/joonspk-research/generative_agents.git    chapter10/generative_agents             # 実験 10-5 Stanford AI Town
```

> プロジェクトの README が特定のコミットを指定している場合は、再現性のためにそのバージョンへ `git checkout` してください。第10章の `use-computer-while-calling` は独立して保守される [19PINE-AI/TalkAct](https://github.com/19PINE-AI/TalkAct) へと発展しました。本リポジトリにはポインタのドキュメントのみを残しています。

</details>

## 🤝 コントリビュート

本書と付随コードは完全にオープンソースです。Pull Request を大歓迎します。

| 種類 | 備考 |
| --- | --- |
| 📝 **本文の内容** | 誤字修正、加筆、より分かりやすい表現、あるいは新しい動向（本文は `book/chapter*.md`） |
| 🐛 **コードの改善とバグ修正** | 付随プロジェクトをより堅牢に、使いやすく、本番対応にする |
| 🧪 **新しい実践プロジェクト** | 実験のより良い実装を追加/置換、あるいは新しいサンプルを提供 |
| 🎨 **図版の設計** | `book/images/` にコミット済みの SVG 図版を直接改善する |
| 🌐 **新しい翻訳** | より多くの言語への翻訳を歓迎します。英語（`book-en/`）、アラビア語（`book-ar/`）、繁体字中国語/台湾（`book-zhtw/`）、ロシア語（`book-ru/`）、タミル語（`book-ta/`）、ベトナム語（`book-vi/`）、日本語（`book-ja/`）、トルコ語（`book-tr/`）、韓国語（`book-ko/`）を参考にしてください |

提出前に、該当する実験を実行して再現性を確認してください。まず issue を立ててアイデアを議論するのも歓迎です。

## 📄 ライセンス

本プロジェクトは [Apache License 2.0](../../LICENSE) の下でライセンスされています。詳細は [`LICENSE`](../../LICENSE) ファイルを参照してください。一部のサブプロジェクトには独自のライセンス情報が含まれる場合があります。詳しくは各サブプロジェクトを参照してください。

## ⭐ Star 履歴

<a href="https://star-history.com/#bojieli/ai-agent-book&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../../assets/star-history-dark.png" />
    <source media="(prefers-color-scheme: light)" srcset="../../assets/star-history-light.png" />
    <img alt="Star History Chart" src="../../assets/star-history-light.png" width="100%" />
  </picture>
</a>

<sub>[`scripts/gen_star_history.py`](../../scripts/gen_star_history.py) によって生成され、[GitHub Actions](../../.github/workflows/star-history.yml) によって毎日更新されます · 画像をクリックするとライブデータを表示</sub>
