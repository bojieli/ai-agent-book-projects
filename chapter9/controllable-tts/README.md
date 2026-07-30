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
python demo.py
```

同一文本生成：

- A `A_no_control_markers.mp3`：删除标记，直接使用 source `reference_id`；
- B `B_single_reference.mp3`：全程仅用 neutral/normal/formal 一条参考音做零样本克隆；
- C `C_24_reference_library.mp3`：逐段解析标记并在 24 条参考音中切换。

`[THINKING]` 产生 1.2s 思考停顿和 S1 `(uncertain)嗯……`；`[SIGH]`、`[LAUGH:small]`、`[BREATH]` 分别发送 S1 原生 `(sighing)`、`(chuckling)`、`(gasping)`，不再用“唉/哈哈”等文字冒充非语言音。所有 Fish 请求显式指定 `backend="s1"`。

## 实际验证

2026-07-29 使用真实 Fish API 构建了 24 条参考音并运行 A/B/C 三组：

| 配置 | ffprobe 时长 |
| --- | ---: |
| A 无控制标记 | 5.355s |
| B 单一参考音克隆 | 5.904s |
| C 24 条参考库 | 8.305s |

脱敏证据在 `validation/latest.json`，包含 provider=`Fish Audio`、backend=`s1`、24 条库维度、解析轨迹、每段采用的 reference SHA-256 和输出 ffprobe 信息。生成音频在 `output/`，API key 与用户标识不会写入证据。

`python validate_artifacts.py` 会重新核对 24 条参考音的 hash/时长、A/B/C 输出媒体和正文示例的三次路由，不会再次调用 API。严格审计写入 `validation/acceptance.json`。本次构建与 A/B/C 运行估计产生 30 次 Fish 请求（24+1+1+4）；SDK 未返回逐请求美元费用。

结构与真实媒体验收已通过；但正文“无标记机械、单参考情感单调、多参考接近真人客服”是主观听感排序，目前没有盲听、MOS 或客观韵律评测，因此不能标为完整结果复现。

```bash
pytest -q
```

---

## English

This is real Fish Audio S1 zero-shot voice cloning. A builder renders a same-speaker 4×3×2 reference library, hashes all 24 clips, and the runtime selects those real clips through inline `ReferenceAudio`. Native S1 `(sighing)`, `(chuckling)`, `(gasping)`, and `(uncertain)` controls replace the former OpenAI/onomatopoeia approximation. `demo.py` produces and records the required no-marker, single-reference, and 24-reference comparison.
