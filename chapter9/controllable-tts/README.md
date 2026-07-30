# 实验 9-5：Fish Audio S1 控制标记 TTS

本项目实际调用 Fish Audio S1，不再使用 OpenAI TTS、固定 `alloy` voice 或拟声词替代。执行层把主 LLM 的控制标记映射到真实的 24 条参考语音，并通过 S1 的零样本 `ReferenceAudio` voice cloning 合成同一说话人、不同情绪/语速/风格的语音。

参考库是严格的笛卡尔积：

- 情绪：neutral / happy / frustrated / thinking；
- 语速：normal / fast / slow；
- 风格：formal / casual；
- 总计：4 × 3 × 2 = 24 条。

## 1. 构建真实参考语音库

```bash
cd chapter9/controllable-tts
pip install -r requirements.txt
cp env.example .env
python build_reference_library.py
```

配置 `FISH_API_KEY` 与一个你拥有或获准克隆的 `FISH_BASE_REFERENCE_ID`。builder 使用同一 source timbre 和 Fish S1 原生情感标记，合成 24 条约 5 秒的参考音；`reference_audio/manifest.json` 保存每条音频的情绪、语速、风格、transcript、时长和 SHA-256。运行时会验证数量与 hash，缺任何一条都拒绝合成。

## 2. 三配置对照

```bash
# From the repository root: use the shared Chapter 9 core environment
uv sync --locked --python 3.12 --extra ch9

# Activate it before changing directories:
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

# pip fallback when uv is not installed:
# python -m pip install -e ".[ch9]"

cd chapter9/controllable-tts

# Install this experiment's Fish SDK runtime dependencies.
python -m pip install -r requirements.txt

# Requires ffmpeg/ffprobe installed on the system
cp env.example .env                       # Fill in FISH_API_KEY and reference settings
python demo.py                            # Generates output/*.mp3
```

同一文本生成：

- A `A_no_control_markers.mp3`：删除标记，直接使用 source `reference_id`；
- B `B_single_reference.mp3`：全程仅用 neutral/normal/formal 一条参考音做零样本克隆；
- C `C_24_reference_library.mp3`：逐段解析标记并在 24 条参考音中切换。

`[THINKING]` 产生 1.2s 思考停顿和 S1 `(uncertain)嗯……`；`[SIGH]`、`[LAUGH:small]`、`[BREATH]` 分别发送 S1 原生 `(sighing)`、`(chuckling)`、`(gasping)`，不再用“唉/哈哈”等文字冒充非语言音。所有 Fish 请求显式指定 `backend="s1"`。

## 实际验证

2026-07-29 使用真实 Fish API 构建了 24 条参考音并运行 A/B/C 三组：

## Validation

The regression tests are offline: they validate marker parsing and empty-segment handling without calling TTS APIs or ffmpeg concat.

```bash
# From the repository root, include dev tools for pytest
uv sync --locked --python 3.12 --extra ch9 --extra dev

# Activate it before changing directories:
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

cd chapter9/controllable-tts
python -m pytest -q
```

| 配置 | ffprobe 时长 |
| --- | ---: |
| A 无控制标记 | 5.355s |
| B 单一参考音克隆 | 5.904s |
| C 24 条参考库 | 8.305s |

脱敏证据在 `validation/latest.json`，包含 provider=`Fish Audio`、backend=`s1`、24 条库维度、解析轨迹、每段采用的 reference SHA-256 和输出 ffprobe 信息。生成音频在 `output/`，API key 与用户标识不会写入证据。

`python evaluate_audio_quality.py` 会把 A/B/C 隐去配置名称，以三种轮换顺序交给真实音频理解模型直接聆听；支持 Gemini、OpenRouter 音频路由、DashScope Omni 和 Mistral Voxtral，并保存实际成功的 provider/model 及失败的前置尝试。每次都按自然度、情绪匹配、思考停顿、音色一致性和真人客服感五维评分，理由必须引用可听见证据；三次位置平衡用于降低顺序偏差。结果写入 `validation/audio_quality_study.json`。这是多模态模型听测，不冒充真人 MOS 面板。

`python validate_artifacts.py` 会重新核对 24 条参考音的 hash/时长、A/B/C 输出媒体、正文示例的三次路由，以及听测的三种排列、逐项证据、音频 hash 和重算聚合结果，不会再次调用 API。严格审计写入 `validation/acceptance.json`。本次构建与 A/B/C 运行估计产生 30 次 Fish 请求（24+1+1+4）；SDK 未返回逐请求美元费用。验收把“实验已经完整执行”和“正文主观排序是否复现”分开报告，因此真实负结果也不会被伪装成未运行。

2026-07-30 的真实听测使用 Mistral `voxtral-small-latest`。三次轮换位置后，多参考 C 组总均分 4.60、真人客服感 4.67，均为三组最高，支持“多参考更接近真人客服”；但完整的 `C > B > A` 排序没有复现：无标记 A 为 3.93，单参考 B 为 3.20。正式结论因此是“C 的主要优势复现，B 优于 A 未复现”，而不是把部分正结果改写为全部成功。逐次匿名映射、原始理由和聚合结果见 `validation/audio_quality_study.json`。

```bash
pytest -q
```

---

## English

This is real Fish Audio S1 zero-shot voice cloning. A builder renders a same-speaker 4×3×2 reference library, hashes all 24 clips, and the runtime selects those real clips through inline `ReferenceAudio`. Native S1 `(sighing)`, `(chuckling)`, `(gasping)`, and `(uncertain)` controls replace the former OpenAI/onomatopoeia approximation. `demo.py` produces and records the required no-marker, single-reference, and 24-reference comparison.
