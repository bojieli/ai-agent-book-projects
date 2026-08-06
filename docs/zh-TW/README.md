# 深入理解 AI Agent：設計原理與工程實踐

[![PDF](https://img.shields.io/badge/PDF-%E4%B8%8B%E8%BC%89-success.svg)](#-電子書) [![線上閱讀](https://img.shields.io/badge/🌐_線上閱讀-bojieli.github.io-success?style=flat-square)](https://bojieli.github.io/ai-agent-book/) [![Stars](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](../../LICENSE) [![Languages](https://img.shields.io/badge/翻譯-13%20種%20語言-informational.svg)](#-電子書)
[![Trending GitHub Project of the Day](https://img.shields.io/badge/GitHub%20Trending-Project%20of%20the%20Day-orange?logo=github)](https://github.com/trending)

**[中文](../../README.md) · [English](../en/README.md) · [Español](../es/README.md) · [Bahasa Indonesia](../id/README.md) · [العربية](../ar/README.md) · 繁體中文（台灣） ← 當前 · [Русский](../ru/README.md) · [Tiếng Việt](../vi/README.md) · [தமிழ்](../ta/README.md) · [日本語](../ja/README.md) · [Türkçe](../tr/README.md) · [한국어](../ko/README.md) · [Magyar](../hu/README.md)**

> 📥 **[下載 PDF / EPUB](#-電子書)**（推薦）— 推薦使用 PDF / EPUB 離線閱讀，排版最佳；也可[線上閱讀](https://bojieli.github.io/ai-agent-book/)（支援多語言切換、章節摺疊、全文搜尋，每次 main 分支推送後自動重新構建）。

**Agent = LLM + 上下文 + 工具**——本書圍繞這個核心公式，用 10 章把 AI Agent 從原理講到工程實戰。全書正文、配圖、**93 個配套實驗**全部開源，歡迎親手把實驗跑一遍。

| 📚 **10 章** 正文，從基礎到生產 | 📂 **93 個** 配套專案（70+ 可獨立執行） | 🌐 **13 種** 語言：中 / 英 / 西 / 印尼 / 阿拉伯 / 繁體中文（台灣） / 俄 / 泰米爾 / 越 / 日 / 土耳其 / 韓 / 匈牙利 |
| :---: | :---: | :---: |

## 📖 電子書

> 📥 **直接下載**（推薦，全書正文，開源免費）。以下連結始終指向 main 分支的最新建置；固定版本見 [Releases](https://github.com/bojieli/ai-agent-book/releases)：
> - **中文（原版）**：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.epub)
> - **英文**（社群翻譯，by [@nsdevaraj](https://github.com/nsdevaraj)、[@whanyu1212](https://github.com/whanyu1212)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.epub)
> - **西班牙語**（社群翻譯，by [@santhreal](https://github.com/santhreal)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.epub)
> - **阿拉伯語**（社群翻譯，by [@TheSyBuilder](https://github.com/TheSyBuilder)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.epub)
> - **繁體中文（台灣）**（社群翻譯，by [@tigercosmos](https://github.com/tigercosmos)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.epub)
> - **俄語**（社群翻譯，by [@ui99ru](https://github.com/ui99ru)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.epub)
> - **泰米爾語**（社群翻譯，by [@nsdevaraj](https://github.com/nsdevaraj)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.epub)
> - **越南語**（社群翻譯，by [@toanalien](https://github.com/toanalien)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.epub)
> - **日語**（社群翻譯，by [@eltociear](https://github.com/eltociear)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.epub)
> - **土耳其語**（社群翻譯，by [@memisemre](https://github.com/memisemre)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.epub)
> - **韓語**（社群翻譯，by [@JeongJaeSoon](https://github.com/JeongJaeSoon)）：[PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.epub)
>
> 🌐 也可[線上閱讀](https://bojieli.github.io/ai-agent-book/) — 支援多語言切換、章節摺疊、全文搜尋、配套實驗直達，每次 main 分支推送後自動重新構建。

中文正文原始碼位於 [`book/`](../../book/)；英文/西班牙語/阿拉伯語/繁體中文（台灣）/俄語/泰米爾/越南語/日語/土耳其語/韓語版本為社群貢獻（可能滯後於中文原版），分別位於 [`book-en/`](../../book-en/)、[`book-es/`](../../book-es/)、[`book-ar/`](../../book-ar/)、[`book-zhtw/`](../../book-zhtw/)、[`book-ru/`](../../book-ru/)、[`book-ta/`](../../book-ta/)、[`book-vi/`](../../book-vi/)、[`book-ja/`](../../book-ja/)、[`book-tr/`](../../book-tr/)、[`book-ko/`](../../book-ko/)。

<details>
<summary><b>🔧 想自行編譯 PDF / EPUB？</b>（PDF 需 pandoc / xelatex / ElegantBook）</summary>

- **EPUB**：使用統一的建置腳本，詳情請參閱 [EPUB 建置說明](../../EPUB.md)
- **正文原始碼**：`book/introduction.md`（引言）、`book/chapter1.md` ~ `book/chapter10.md`（第一至第十章）、`book/afterword.md`（後記）
- **編譯**：安裝 pandoc、xelatex、ElegantBook 文件類與相關字型後，執行

  ```bash
  cd book && bash build_pdf.sh
  ```

  圖表以 SVG 檔案存於 `book/images/`，編譯時直接使用；排版細節見 `book/preamble.tex` 與 `book/*.lua`。

</details>

## 📑 內容速覽（第 1–10 章）

全書圍繞核心公式 **Agent = LLM + 上下文 + 工具** 展開，十章層層遞進：

| 章 | 主題 | 一句話核心 | 正文 | 程式碼 |
| :--: | --- | --- | :--: | :--: |
| 1 | 🚀 **Agent 基礎知識** | **Agent = LLM + 上下文 + 工具**；Harness 工程才是競爭力 | [讀](../../book-zhtw/chapter1.zhtw.md) | [4](../../chapter1/README.zh-TW.md) |
| 2 | 🎯 **上下文工程** | 上下文決定能力上限：KV Cache、提示工程、Agent Skills、上下文壓縮 | [讀](../../book-zhtw/chapter2.zhtw.md) | [9](../../chapter2/README.zh-TW.md) |
| 3 | 📚 **使用者記憶和知識庫** | 跨會話記住使用者、接入外部知識：使用者記憶、RAG、結構化索引、知識圖譜 | [讀](../../book-zhtw/chapter3.zhtw.md) | [12](../../chapter3/README.zh-TW.md) |
| 4 | 🛠️ **工具** | 工具是 Agent 的雙手：MCP 協議、感知/執行/協作三類工具、事件驅動非同步 Agent、主動工具發現 | [讀](../../book-zhtw/chapter4.zhtw.md) | [8](../../chapter4/README.zh-TW.md) |
| 5 | 💻 **Coding Agent 與程式碼生成** | 程式碼是「能創造新工具的工具」，生產級 Coding Agent 全景 | [讀](../../book-zhtw/chapter5.zhtw.md) | [13](../../chapter5/README.zh-TW.md) |
| 6 | 🎯 **Agent 的評估** | 把表現變成可比較訊號：評估環境、指標、統計顯著性、評估驅動選型 | [讀](../../book-zhtw/chapter6.zhtw.md) | [12](../../chapter6/README.zh-TW.md) |
| 7 | 🧠 **模型後訓練** | 預訓練/SFT/RL 三階段：何時選 SFT、何時選 RL，工具呼叫內化、樣本效率 | [讀](../../book-zhtw/chapter7.zhtw.md) | [16](../../chapter7/README.zh-TW.md) |
| 8 | 🔄 **Agent 的自我進化** | 不改權重也能成長：經驗學習、從工具使用者到創造者 | [讀](../../book-zhtw/chapter8.zhtw.md) | [7](../../chapter8/README.zh-TW.md) |
| 9 | 🎙️ **多模態與即時互動** | 從文字擴充套件到語音、GUI、物理世界：語音三典範、Computer Use、機器人 | [讀](../../book-zhtw/chapter9.zhtw.md) | [7](../../chapter9/README.zh-TW.md) |
| 10 | 🤝 **多 Agent 協作** | 群體智慧高於個體：協作框架、上下文共享/隔離、湧現的「Agent 社會」 | [讀](../../book-zhtw/chapter10.zhtw.md) | [7](../../chapter10/README.zh-TW.md) |

> 💡 **讀** = 在 GitHub 網頁直接讀章節正文（markdown）；**N** = 該章配套專案數，點選檢視程式碼。專案型別說明（✅ 可執行 / 📖 復現 / 🚧 設計）見各章 README。
>
> 📚 如何高效閱讀本書？詳見 **[學習建議](LEARNING.md)**（核心理念、學習路徑、難度分級、實踐建議）。

## 💻 執行配套實驗

專案統一支援 **Python 3.10+**。請在倉庫根目錄按章節安裝依賴；將 `ch1` 替換為 `ch2` ~ `ch10` 即可安裝對應章節：

```bash
# 推薦：使用提交到倉庫的 uv.lock，取得可重現的章節環境
uv sync --locked --extra ch1

# 未安裝 uv 時：使用 pip 從 pyproject.toml 重新解析
python -m pip install -e ".[ch1]"
```

執行會呼叫模型的實驗前，請依該實驗 README 設定憑證：支援根目錄設定的實驗可複製 `.env.example` 為 `.env` 並填入至少一個 provider key；有些實驗要求在自身目錄放 `.env` 或直接匯出環境變數。只有在實驗 README 或 CLI 明確列出 `ollama` 時，才可啟動本機 Ollama 並加入 `--provider ollama`。

安裝後可從倉庫根目錄執行實驗，例如：

```bash
uv run python chapter1/context/main.py
# 使用 pip 安裝時也可直接執行：python chapter1/context/main.py
```

- `uv` 安裝方法見[官方文件](https://docs.astral.sh/uv/getting-started/installation/)；`pip` 仍受支援，但不會使用鎖定檔。
- 各實驗現有的 `requirements.txt` 在遷移期間繼續有效，適合只執行單一專案或需要特殊版本約束的情況。
- `all` 是不含本機訓練堆疊的 CPU 友好組合，並不代表每個實驗；`uv sync` 每次都會精確同步目前選擇，使用特殊 extra 時請合併到同一條指令，例如 `uv sync --locked --extra ch2 --extra vllm` 或 `uv sync --locked --extra ch7 --extra unsloth`；pip 對應為 `python -m pip install -e ".[ch2,vllm]"`。
- 瀏覽器、CUDA、FFmpeg、Ollama、Playwright 瀏覽器及外部倉庫等系統依賴，請繼續參考各實驗 README。部分瀏覽器和記憶實驗需要 Python 3.11+，第 8 章部分內建第三方元件需要 Python 3.12+。

## 🔑 API 金鑰

建議申請下面幾個平台的 API Key 方便學習。模型選型可參考 [這篇指南](https://01.me/2025/07/llm-api-setup/)。

| 平台 | 連結 | 特色 | 訪問節點 |
| --- | --- | --- | --- |
| **Kimi**（月之暗面） | <https://platform.moonshot.cn/> | Kimi 系列，Coding、Agent 能力強 | 中國大陸 |
| **智譜 GLM** | <https://open.bigmodel.cn/> | GLM-5.2 等，Coding、Agent 能力強 | 中國大陸 |
| **Siliconflow** | <https://siliconflow.cn/> | 各種開源模型（DeepSeek、Qwen 等），中國大陸訪問速度快 | 中國大陸 |
| **DeepSeek** | <https://platform.deepseek.com/> | DeepSeek 官方 API | 全球 + 中國大陸 |
| **Krill AI** | [www.krill-ai.net](https://www.krill-ai.net/register?invite=Q8D3L35725) | 一站式訪問全球及國內主流模型（OpenAI、Claude、Gemini、Grok、Kimi、GLM、DeepSeek、Qwen、Minimax） | 全球 + 中國大陸 |
| **OpenRouter** | <https://openrouter.ai/> | 一站式訪問全球及國內主流模型（GPT、Claude、Gemini、Kimi、GLM、DeepSeek、Qwen 等） | 全球 |

## 💎 贊助商

感謝 **Krill AI** 贊助本專案！Krill 提供 GPT / Claude / Gemini / 多款國產模型的官方穩定極速 API 中轉服務，支援企業級客製、報銷開票、7×16h 專屬技術支援，更有獨家適配的 WebSocket 連線方式，暢享極速首字速度。

Krill 為本書讀者提供特別優惠：使用[此連結](https://www.krill-ai.net/register?invite=Q8D3L35725)註冊並在儲值時填寫優惠碼「ai-agent-book」，首次購買 Codex 套餐可享 77 折優惠！

> 🧪 配套實驗的執行狀態、證據與尚未完成的驗收門檻，另行記錄於 [`EXPERIMENT_STATUS.md`](../EXPERIMENT_STATUS.md)；克隆或安裝原始碼不代表實驗已完成。

## 📦 附錄 · 外部倉庫獲取

第 6、7、9、10 章的評測基準、訓練框架、機器人平台等 23 個外部倉庫**未內建**（出於體積與版權），需要自行克隆到對應目錄。

### 一鍵克隆指令碼

<details>
<summary><b>🔧 展開克隆命令</b>（共 23 個外部倉庫）</summary>

```bash
# 第 6 章 · 評測基準
git clone https://github.com/google-research/android_world.git         chapter6/android_world
git clone https://huggingface.co/datasets/gaia-benchmark/GAIA          chapter6/GAIA
git clone https://github.com/xlang-ai/OSWorld.git                      chapter6/OSWorld
git clone https://github.com/SWE-bench/SWE-bench.git                   chapter6/SWE-bench
git clone https://github.com/sierra-research/tau2-bench.git            chapter6/tau2-bench
git clone https://github.com/laude-institute/terminal-bench.git        chapter6/terminal-bench

# 第 7 章 · 訓練框架（bojieli/* 為本書適配的分支）
git clone https://github.com/bojieli/minimind.git                      chapter7/MiniMind-pretrain/minimind      # 實驗 7-3 從零訓 LLM
git clone https://github.com/bojieli/minimind-v.git                    chapter7/MiniMind-pretrain/minimind-v    # 實驗 7-4 從零訓 VLM（投影層）
git clone https://github.com/bojieli/AdaptThink.git                    chapter7/AdaptThink-original
git clone https://github.com/bojieli/AWorld.git                        chapter7/AWorld
git clone https://github.com/bojieli/SFTvsRL.git                       chapter7/SFTvsRL
git clone https://github.com/bojieli/verl.git                          chapter7/verl
git clone https://github.com/bojieli/SandboxFusion.git chapter7/SandboxFusion && git -C chapter7/SandboxFusion fetch origin 4a0d573ebd64c98234c190a9d1d49e4276199a0c && git -C chapter7/SandboxFusion checkout --detach 4a0d573ebd64c98234c190a9d1d49e4276199a0c && test "$(git -C chapter7/SandboxFusion rev-parse HEAD)" = "4a0d573ebd64c98234c190a9d1d49e4276199a0c"  # Exp 7-15 code sandbox
git clone https://github.com/thinking-machines-lab/tinker-cookbook.git chapter7/tinker-cookbook
git clone https://github.com/19PINE-AI/rlvp.git                        chapter7/RLVP/rlvp                       # 實驗 7-14 RLVP 論文程式碼
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git                 chapter7/SimpleVLA-RL/SimpleVLA-RL       # 實驗 7-13 視覺-語言-動作 RL

# 第 9 章 · 瀏覽器自動化與 Claude 示例
git clone https://github.com/browser-use/browser-use.git               chapter9/browser-use
git clone https://github.com/anthropics/claude-quickstarts.git         chapter9/claude-quickstarts
git clone https://github.com/Vector-Wangel/XLeRobot.git chapter9/XLeRobot && git -C chapter9/XLeRobot fetch origin 3d14695e40c9c68229c0aacffca6053c75cd3eb6 && git -C chapter9/XLeRobot checkout --detach 3d14695e40c9c68229c0aacffca6053c75cd3eb6 && test "$(git -C chapter9/XLeRobot rev-parse HEAD)" = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"  # Exp 9-8/9-9 shared
git clone https://github.com/Grigorij-Dudnik/RoboCrew.git chapter9/RoboCrew && git -C chapter9/RoboCrew fetch origin c749148f29bd14e61347f9fc3530c343fff0d994 && git -C chapter9/RoboCrew checkout --detach c749148f29bd14e61347f9fc3530c343fff0d994 && test "$(git -C chapter9/RoboCrew rev-parse HEAD)" = "c749148f29bd14e61347f9fc3530c343fff0d994"  # Exp 9-9; RoboCrew v0.3.1
git clone https://github.com/StoneT2000/lerobot-sim2real.git chapter9/lerobot-sim2real && git -C chapter9/lerobot-sim2real fetch origin 87d6c1d969f6e0ca4dc5697940804e231118a63a && git -C chapter9/lerobot-sim2real checkout --detach 87d6c1d969f6e0ca4dc5697940804e231118a63a && test "$(git -C chapter9/lerobot-sim2real rev-parse HEAD)" = "87d6c1d969f6e0ca4dc5697940804e231118a63a"  # Exp 9-10

# 第 10 章 · 雙 Agent 架構（已獨立為 TalkAct 專案）+ 斯坦福 AI 小鎮
git clone https://github.com/19PINE-AI/TalkAct.git                     chapter10/use-computer-while-calling
git clone https://github.com/joonspk-research/generative_agents.git    chapter10/generative_agents             # 實驗 10-7 斯坦福 AI 小鎮
```

> 各專案 README 如標註了特定 commit，請按說明 `git checkout` 到對應版本以保證復現一致。第 10 章 `use-computer-while-calling` 已發展為獨立維護的 [19PINE-AI/TalkAct](https://github.com/19PINE-AI/TalkAct)，本倉庫不內建該目錄，用上面的克隆命令獲取。

</details>

## 🤝 貢獻

本書與配套程式碼全部開源，非常歡迎社群透過 Pull Request 參與共建：

| 型別 | 說明 |
| --- | --- |
| 📝 **書籍內容改進** | 勘誤、補充、更清晰的表述，或新增前沿進展（正文見 `book/chapter*.md`） |
| 🐛 **程式碼改進與 Bug 修復** | 讓配套專案更健壯、更易用、更貼近生產實踐 |
| 🧪 **新的實踐專案** | 為某個實驗補充/替換更好的實現，或貢獻全新的示例專案 |
| 🎨 **配圖設計改進** | 直接改進 `book/images/` 中已簽入的 SVG 圖表，讓它們更清晰美觀 |
| 🌐 **新語言翻譯** | 歡迎翻譯成更多語言，可參考英文（`book-en/`）、阿拉伯語（`book-ar/`）、繁體中文（台灣）版（`book-zhtw/`）、俄語（`book-ru/`）、泰米爾語（`book-ta/`）、越南語（`book-vi/`）、日語（`book-ja/`）、土耳其語（`book-tr/`）、韓語（`book-ko/`）的組織方式 |

提交前建議先把相關實驗親手跑一遍、確認可復現；也歡迎先提 issue 討論想法。

## 📄 許可證

本專案採用 [Apache License 2.0](../../LICENSE) 開源許可證，詳見 [`LICENSE`](../../LICENSE) 檔案。部分子專案可能包含各自的許可證資訊，請以子專案中的說明為準。

## ⭐ Star History

<a href="https://star-history.com/#bojieli/ai-agent-book&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../../assets/star-history-dark.png" />
    <source media="(prefers-color-scheme: light)" srcset="../../assets/star-history-light.png" />
    <img alt="Star History Chart" src="../../assets/star-history-light.png" width="100%" />
  </picture>
</a>

<sub>由 [`scripts/gen_star_history.py`](../../scripts/gen_star_history.py) 生成，[GitHub Actions](../../.github/workflows/star-history.yml) 每日自動更新 · 點選圖片檢視即時資料</sub>
