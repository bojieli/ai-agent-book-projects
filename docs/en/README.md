# AI Agents in Depth: Design Principles and Engineering Practice

[![PDF](https://img.shields.io/badge/PDF-download-success.svg)](#-e-book) [![Read online](https://img.shields.io/badge/🌐_Read_online-bojieli.github.io-success?style=flat-square)](https://bojieli.github.io/ai-agent-book/) [![Stars](https://img.shields.io/github/stars/bojieli/ai-agent-book?style=social)](https://github.com/bojieli/ai-agent-book) [![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](../../LICENSE) [![Languages](https://img.shields.io/badge/translations-13%20languages-informational.svg)](#-e-book)
[![Trending GitHub Project of the Day](https://img.shields.io/badge/GitHub%20Trending-Project%20of%20the%20Day-orange?logo=github)](https://github.com/trending)

**[中文](../../README.md) · English ← current · [Español](../es/README.md) · [Bahasa Indonesia](../id/README.md) · [العربية](../ar/README.md) · [繁體中文（台灣）](../zh-TW/README.md) · [Русский](../ru/README.md) · [Tiếng Việt](../vi/README.md) · [தமிழ்](../ta/README.md) · [日本語](../ja/README.md) · [Türkçe](../tr/README.md) · [한국어](../ko/README.md) · [Magyar](../hu/README.md)**

> 📥 **[Download PDF / EPUB](#-e-book)** (recommended) — the PDF / EPUB editions offer the best reading experience; you can also [read online](https://bojieli.github.io/ai-agent-book/) (multi-language switcher, collapsible chapter tree, full-text search, auto-rebuilt on every push to main).

**Agent = LLM + Context + Tools** — This book builds on this core formula across 10 chapters, taking AI Agents from principles to engineering practice. The full text, illustrations, and **93 accompanying experiments** are all open source. You are welcome to run the experiments yourself.

| 📚 **10 chapters** of text, from basics to production | 📂 **93** companion projects (70+ standalone) | 🌐 **13 languages**: CN / EN / ES / ID / AR / zh-TW / RU / TA / VI / JA / TR / KO / HU |
| :---: | :---: | :---: |

## 📖 E-Book

> 📥 **Download** (recommended; full text, free and open source). These links always point to the latest build of the `main` branch; fixed editions are on the [Releases](https://github.com/bojieli/ai-agent-book/releases) page:
> - **Chinese (original)**: [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-CN.epub)
> - **English** (community translation, by [@nsdevaraj](https://github.com/nsdevaraj) and [@whanyu1212](https://github.com/whanyu1212)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-en.epub)
> - **Spanish** (community translation, by [@santhreal](https://github.com/santhreal)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-es.epub)
> - **Traditional Chinese (Taiwan)** (community translation, by [@tigercosmos](https://github.com/tigercosmos)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-zh-TW.epub)
> - **Russian** (community translation, by [@ui99ru](https://github.com/ui99ru)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ru.epub)
> - **Tamil** (community translation, by [@nsdevaraj](https://github.com/nsdevaraj)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ta.epub)
> - **Vietnamese** (community translation, by [@toanalien](https://github.com/toanalien)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-vi.epub)
> - **Japanese** (community translation, by [@eltociear](https://github.com/eltociear)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ja.epub)
> - **Arabic** (community translation, by [@TheSyBuilder](https://github.com/TheSyBuilder)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ar.epub)
> - **Turkish** (community translation, by [@memisemre](https://github.com/memisemre)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-tr.epub)
> - **Korean** (community translation, by [@JeongJaeSoon](https://github.com/JeongJaeSoon)): [PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.pdf) · [EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.epub)
>
> 🌐 You can also [read online](https://bojieli.github.io/ai-agent-book/) — multi-language switcher, collapsible chapter tree, full-text search, and direct links to companion experiments. Auto-rebuilt on every push to main.

Chinese text source is in [`book/`](../../book/); English/Spanish/Arabic/Traditional Chinese (Taiwan)/Russian/Tamil/Vietnamese/Japanese/Turkish/Korean versions are community contributions (may lag behind the Chinese original), located in [`book-en/`](../../book-en/), [`book-es/`](../../book-es/), [`book-ar/`](../../book-ar/), [`book-zhtw/`](../../book-zhtw/), [`book-ru/`](../../book-ru/), [`book-ta/`](../../book-ta/), [`book-vi/`](../../book-vi/), [`book-ja/`](../../book-ja/), [`book-tr/`](../../book-tr/), [`book-ko/`](../../book-ko/) respectively.

<details>
<summary><b>🔧 Build PDF / EPUB yourself?</b> (PDF requires pandoc / xelatex / ElegantBook)</summary>

- **EPUB**: Use the shared builder; see the [EPUB build instructions](../../EPUB.md)
- **Text source**: `book/introduction.md` (intro), `book/chapter1.md` ~ `book/chapter10.md` (Chapters 1–10), `book/afterword.md` (afterword)
- **Build**: Install pandoc, xelatex, ElegantBook document class and required fonts, then run

  ```bash
  cd book && bash build_pdf.sh
  ```

  Figures are stored as SVG files in `book/images/` and used directly by the build; see `book/preamble.tex` and `book/*.lua` for typography details.

</details>

## 📑 Content Overview (Chapters 1–10)

The book revolves around the core formula **Agent = LLM + Context + Tools**, with ten chapters building progressively:

| Ch | Topic | One-line Summary | Text | Code |
| :--: | --- | --- | :--: | :--: |
| 1 | 🚀 **Agent Fundamentals** | **Agent = LLM + Context + Tools**; Harness engineering is the real competitive edge | [Read](../../book-en/chapter1.md) | [4](../../chapter1/README.en.md) |
| 2 | 🎯 **Context Engineering** | Context caps Agent ability: KV Cache, prompt engineering, Agent Skills, context compression | [Read](../../book-en/chapter2.md) | [9](../../chapter2/README.en.md) |
| 3 | 📚 **User Memory & Knowledge Bases** | Cross-session user memory + external knowledge: user memory, RAG, structured indexes, knowledge graphs | [Read](../../book-en/chapter3.md) | [12](../../chapter3/README.en.md) |
| 4 | 🛠️ **Tools** | Tools are the Agent's hands: MCP protocol, perception/execution/collaboration tools, event-driven async Agents, proactive tool discovery | [Read](../../book-en/chapter4.md) | [8](../../chapter4/README.en.md) |
| 5 | 💻 **Coding Agent & Code Generation** | Code is a "tool that creates new tools"; production-grade Coding Agent in full | [Read](../../book-en/chapter5.md) | [13](../../chapter5/README.en.md) |
| 6 | 🎯 **Agent Evaluation** | Turn performance into comparable signals: environments, metrics, statistical significance, evaluation-driven selection | [Read](../../book-en/chapter6.md) | [12](../../chapter6/README.en.md) |
| 7 | 🧠 **Model Post-Training** | Pre-training/SFT/RL three stages: when to choose SFT vs. RL, internalizing tool calls, sample efficiency | [Read](../../book-en/chapter7.md) | [16](../../chapter7/README.en.md) |
| 8 | 🔄 **Agent Self-Evolution** | Growth without changing weights: learning from experience, from tool user to tool creator | [Read](../../book-en/chapter8.md) | [7](../../chapter8/README.en.md) |
| 9 | 🎙️ **Multimodal & Real-Time Interaction** | Extending from text to voice, GUI, physical world: three voice paradigms, Computer Use, robotics | [Read](../../book-en/chapter9.md) | [7](../../chapter9/README.en.md) |
| 10 | 🤝 **Multi-Agent Collaboration** | Collective intelligence > individual: collaboration frameworks, context sharing/isolation, emergent "Agent Society" | [Read](../../book-en/chapter10.md) | [7](../../chapter10/README.en.md) |

> 💡 **Read** = read the chapter text on GitHub (markdown); **N** = number of companion projects, click for code. Project types (✅ Standalone / 📖 Reproduction / 🚧 Design) are explained in each chapter's README.
>
> 📚 How to read this book efficiently? See **[Learning Suggestions](LEARNING.md)** (core ideas, learning path, difficulty levels, practice tips).

## 💻 Run the Companion Experiments

The shared baseline is **Python 3.10+**. Install dependencies by chapter from the repository root; replace `ch1` with `ch2` through `ch10` for another chapter:

```bash
# Recommended: use the committed uv.lock for a reproducible chapter environment
uv sync --locked --extra ch1

# Without uv: resolve from pyproject.toml with pip
python -m pip install -e ".[ch1]"
```

Before running an experiment that calls a model, follow that experiment's README for credentials. Experiments that support root-level configuration can use `.env.example` copied to `.env` with at least one provider key; some experiments instead require an adjacent `.env` or exported environment variables. Use local Ollama with `--provider ollama` only when that experiment's README or CLI lists it.

Then run an experiment from the repository root, for example:

```bash
uv run python chapter1/context/main.py
# After a pip install, you can also run: python chapter1/context/main.py
```

- See the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/). `pip` remains supported but resolves fresh instead of using the lockfile.
- Existing experiment-level `requirements.txt` files remain supported during migration, especially for isolated projects or special version constraints.
- `all` is broad and CPU-friendly, not literally every experiment. `uv sync` exactly syncs the current selection each time, so combine special extras in one command, such as `uv sync --locked --extra ch2 --extra vllm` or `uv sync --locked --extra ch7 --extra unsloth`; the pip equivalent is `python -m pip install -e ".[ch2,vllm]"`.
- Follow each experiment's README for system dependencies such as browsers, CUDA, FFmpeg, Ollama, Playwright browsers, and external repositories. Some browser and memory experiments require Python 3.11+, while some vendored Chapter 8 components require Python 3.12+.

## 🔑 API Keys

It is recommended to apply for API keys from several platforms for convenient learning. See [this guide](https://01.me/2025/07/llm-api-setup/) for model selection.

| Platform | Link | Notes | Access endpoints |
| --- | --- | --- | --- |
| **Kimi** (Moonshot) | <https://platform.moonshot.cn/> | Kimi series, strong in long context and Agent capabilities | Mainland China |
| **Zhipu GLM** | <https://open.bigmodel.cn/> | GLM-4.6 etc., strong Chinese ability, cost-effective | Mainland China |
| **Siliconflow** | <https://siliconflow.cn/> | Various open-source models (DeepSeek, Qwen, etc.), fast access from mainland China | Mainland China |
| **DeepSeek** | <https://platform.deepseek.com/> | Official DeepSeek API | Global + Mainland China |
| **Krill AI** | [www.krill-ai.net](https://www.krill-ai.net/register?invite=Q8D3L35725) | One-stop access to major global and China-domestic models (OpenAI, Claude, Gemini, Grok, Kimi, GLM, DeepSeek, Qwen, Minimax) | Global + Mainland China |
| **OpenRouter** | <https://openrouter.ai/> | One-stop access to major global and China-domestic models (GPT, Claude, Gemini, Kimi, GLM, DeepSeek, Qwen, etc.) | Global |

## 💎 Sponsors

Thanks to **Krill AI** for sponsoring this project! Krill provides an official, stable, and ultra-fast API relay for GPT / Claude / Gemini and many Chinese models, with enterprise-grade customization, invoicing, and 7×16h dedicated technical support, plus an exclusively adapted WebSocket connection for blazing-fast time to first token.

Krill offers a special deal for readers of this book: register via [this link](https://www.krill-ai.net/register?invite=Q8D3L35725) and enter the promo code "ai-agent-book" when topping up to get 23% off your first Codex plan!

> 🧪 Experiment execution status, evidence, and outstanding gates are tracked separately in [`EXPERIMENT_STATUS.md`](../EXPERIMENT_STATUS.md); cloning or installing source code does not establish completion.

## 📦 Appendix · Obtaining External Repositories

The 23 external repos for benchmarks, training frameworks, and robot platforms in Chapters 6, 7, 9, 10 are **not bundled** (due to size and licensing) and must be cloned into the corresponding directories.

### One-shot Clone Script

<details>
<summary><b>🔧 Expand clone commands</b> (23 external repos)</summary>

```bash
# Chapter 6 · Evaluation Benchmarks
git clone https://github.com/google-research/android_world.git         chapter6/android_world
git clone https://huggingface.co/datasets/gaia-benchmark/GAIA          chapter6/GAIA
git clone https://github.com/xlang-ai/OSWorld.git                      chapter6/OSWorld
git clone https://github.com/SWE-bench/SWE-bench.git                   chapter6/SWE-bench
git clone https://github.com/sierra-research/tau2-bench.git            chapter6/tau2-bench
git clone https://github.com/laude-institute/terminal-bench.git        chapter6/terminal-bench

# Chapter 7 · Training Frameworks (bojieli/* are book-adapted forks)
git clone https://github.com/bojieli/minimind.git                      chapter7/MiniMind-pretrain/minimind      # Exp 7-3 train LLM from scratch
git clone https://github.com/bojieli/minimind-v.git                    chapter7/MiniMind-pretrain/minimind-v    # Exp 7-4 train VLM from scratch (projection layer)
git clone https://github.com/bojieli/AdaptThink.git                    chapter7/AdaptThink-original
git clone https://github.com/bojieli/AWorld.git                        chapter7/AWorld
git clone https://github.com/bojieli/SFTvsRL.git                       chapter7/SFTvsRL
git clone https://github.com/bojieli/verl.git                          chapter7/verl
git clone https://github.com/bojieli/SandboxFusion.git chapter7/SandboxFusion && git -C chapter7/SandboxFusion fetch origin 4a0d573ebd64c98234c190a9d1d49e4276199a0c && git -C chapter7/SandboxFusion checkout --detach 4a0d573ebd64c98234c190a9d1d49e4276199a0c && test "$(git -C chapter7/SandboxFusion rev-parse HEAD)" = "4a0d573ebd64c98234c190a9d1d49e4276199a0c"  # Exp 7-15 code sandbox
git clone https://github.com/thinking-machines-lab/tinker-cookbook.git chapter7/tinker-cookbook
git clone https://github.com/19PINE-AI/rlvp.git                        chapter7/RLVP/rlvp                       # Exp 7-14 RLVP paper code
git clone https://github.com/PRIME-RL/SimpleVLA-RL.git                 chapter7/SimpleVLA-RL/SimpleVLA-RL       # Exp 7-13 vision-language-action RL

# Chapter 9 · Browser Automation & Claude Examples
git clone https://github.com/browser-use/browser-use.git               chapter9/browser-use
git clone https://github.com/anthropics/claude-quickstarts.git         chapter9/claude-quickstarts
git clone https://github.com/Vector-Wangel/XLeRobot.git chapter9/XLeRobot && git -C chapter9/XLeRobot fetch origin 3d14695e40c9c68229c0aacffca6053c75cd3eb6 && git -C chapter9/XLeRobot checkout --detach 3d14695e40c9c68229c0aacffca6053c75cd3eb6 && test "$(git -C chapter9/XLeRobot rev-parse HEAD)" = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"  # Exp 9-8/9-9 shared
git clone https://github.com/Grigorij-Dudnik/RoboCrew.git chapter9/RoboCrew && git -C chapter9/RoboCrew fetch origin c749148f29bd14e61347f9fc3530c343fff0d994 && git -C chapter9/RoboCrew checkout --detach c749148f29bd14e61347f9fc3530c343fff0d994 && test "$(git -C chapter9/RoboCrew rev-parse HEAD)" = "c749148f29bd14e61347f9fc3530c343fff0d994"  # Exp 9-9; RoboCrew v0.3.1
git clone https://github.com/StoneT2000/lerobot-sim2real.git chapter9/lerobot-sim2real && git -C chapter9/lerobot-sim2real fetch origin 87d6c1d969f6e0ca4dc5697940804e231118a63a && git -C chapter9/lerobot-sim2real checkout --detach 87d6c1d969f6e0ca4dc5697940804e231118a63a && test "$(git -C chapter9/lerobot-sim2real rev-parse HEAD)" = "87d6c1d969f6e0ca4dc5697940804e231118a63a"  # Exp 9-10

# Chapter 10 · Dual-Agent Architecture (now independent TalkAct project) + Stanford AI Town
git clone https://github.com/19PINE-AI/TalkAct.git                     chapter10/use-computer-while-calling
git clone https://github.com/joonspk-research/generative_agents.git    chapter10/generative_agents             # Exp 10-7 Stanford AI Town
```

> If a project README specifies a particular commit, `git checkout` to that version for reproducibility. Chapter 10's `use-computer-while-calling` has evolved into the independently maintained [19PINE-AI/TalkAct](https://github.com/19PINE-AI/TalkAct); this repo does not bundle that directory — use the clone command above to fetch it.

</details>

## 🤝 Contributing

The book and accompanying code are fully open source. Pull Requests are very welcome:

| Type | Notes |
| --- | --- |
| 📝 **Book content** | Errata, additions, clearer wording, or new developments (text in `book/chapter*.md`) |
| 🐛 **Code improvements & bug fixes** | Make companion projects more robust, usable, and production-ready |
| 🧪 **New practice projects** | Add/replace better implementations for experiments, or contribute new examples |
| 🎨 **Figure design** | Directly improve the checked-in SVG charts under `book/images/` |
| 🌐 **New translations** | Translations into more languages are welcome; see English (`book-en/`), Arabic (`book-ar/`), Traditional Chinese/Taiwan (`book-zhtw/`), Russian (`book-ru/`), Tamil (`book-ta/`), Vietnamese (`book-vi/`), Japanese (`book-ja/`), Turkish (`book-tr/`), and Korean (`book-ko/`) for reference |

Before submitting, please run the relevant experiments to confirm reproducibility; feel free to open an issue to discuss ideas first.

## 📄 License

This project is licensed under [Apache License 2.0](../../LICENSE). See the [`LICENSE`](../../LICENSE) file for details. Some sub-projects may include their own license information; refer to the sub-project for specifics.

## ⭐ Star History

<a href="https://star-history.com/#bojieli/ai-agent-book&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../../assets/star-history-dark.png" />
    <source media="(prefers-color-scheme: light)" srcset="../../assets/star-history-light.png" />
    <img alt="Star History Chart" src="../../assets/star-history-light.png" width="100%" />
  </picture>
</a>

<sub>Generated by [`scripts/gen_star_history.py`](../../scripts/gen_star_history.py), updated daily by [GitHub Actions](../../.github/workflows/star-history.yml) · Click image for live data</sub>
