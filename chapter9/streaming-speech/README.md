# 实验 9-3：Qwen2-Audio 递增前缀模拟流式感知

本项目实际运行 `Qwen/Qwen2-Audio-7B-Instruct`：每收到一个新块，就把 `[0:t]` 的完整累积音频再次送入 Qwen2-Audio，输出当前 transcript 和声学事件。它不是 Whisper 替代实现，也不会把这种全量重编码称作真流式。

对照组是传统 600ms 端点 VAD + 开源 Whisper。三类场景均被测量：正常对话、含 900ms 中途停顿的长句、混入粉红背景噪声的对话。证据记录每个前缀的模型原始输出、单块延迟、最终 CER、事件 token，以及 VAD 分段点、Whisper 推理时长和 CER。

## 安装

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

cd chapter9/streaming-speech

# Install this experiment's local audio/model runtime dependencies.
python -m pip install -r requirements.txt
```

NVIDIA 路径使用原始 BF16 权重：

```bash
python demo.py --model Qwen/Qwen2-Audio-7B-Instruct --device cuda ...
```

Apple Silicon 可运行同一 Qwen2-Audio 架构的 4-bit MLX 量化权重（LLM 量化，音频编码器和 projector 保持 BF16）：

```bash
python prepare_scenarios.py audio/sentence.wav validation/scenarios

python demo.py \
  --model mlx-community/Qwen2-Audio-7B-Instruct-4bit --device mlx \
  --chunk-seconds 2 --whisper-model tiny \
  --audio validation/scenarios/normal.wav --scenario normal \
  --reference '麻烦你帮我把明天下午的会议改到两点半，地点还是在三号会议室，别忘了通知大家。' \
  --audio validation/scenarios/long_pause.wav --scenario pause \
  --reference '麻烦你帮我把明天下午的会议改到两点半，地点还是在三号会议室，别忘了通知大家。' \
  --audio validation/scenarios/background_noise.wav --scenario noise \
  --reference '麻烦你帮我把明天下午的会议改到两点半，地点还是在三号会议室，别忘了通知大家。'
```

结果写入 `validation/latest.json`。`--skip-whisper` 只用于单独调试 Qwen，不能完成书中的对照验收。原始 BF16 模型约 16.8GB；MLX 量化权重约 6.6GB。

保持上述科学设计不变并生成完整验收 manifest：

```bash
python run_official_experiment.py --run-id exp9-3-qwen2audio-whisper-provenance-YYYYMMDD-vN
```

官方 runner 在运行前后核对源码 hash，并绑定三类测试音频、原始源音频、Whisper
checkpoint、Qwen2-Audio snapshot 的每个文件（包括 6.56GB 权重）、13 个原始前缀
输出、运行日志和独立 acceptance 文件。

## 已验证结果

当前 canonical 记录是 [`validation/runs/exp9-3-qwen2audio-whisper-provenance-20260730-v3/manifest.json`](validation/runs/exp9-3-qwen2audio-whisper-provenance-20260730-v3/manifest.json)。
2026-07-30 在 Apple Silicon 上严格复跑 `mlx-community/Qwen2-Audio-7B-Instruct-4bit`；8/8
执行与溯源门禁通过，但正文结果只复现 2/6。13 次前缀推理实测 8.4–11.3s，不能据此声称
100–200ms；传统路径也未在三类输入上全部落入 800–1100ms。900ms 停顿被 VAD 分为两段，
但 Qwen 漏报 `<|silence|>`；强噪声样本检出 `<|noise|>`，同时误报 `<|cough|>` 与
`<|laughter|>`。这些负结果与所有原始响应都保留在验收记录中。2026-07-29 的 `latest.json`
和 `latest_v2.json` 作为历史运行保留，不再承担 canonical 选择职责。

```bash
pytest -q
```

---

## English

This is actual Qwen2-Audio growing-prefix inference, not a Whisper substitute. Every `[0:t]` prefix is fully re-encoded and compared with a real 600ms-VAD + open-source Whisper pipeline on normal, long-pause, and noisy speech. CUDA uses the original model; Apple Silicon can use the published 4-bit MLX conversion of the same Qwen2-Audio architecture. The canonical v3 manifest binds raw responses, sources, audio, the Whisper checkpoint, and every Qwen snapshot file. Execution passed while the manuscript result bundle did not: only 2/6 claims reproduced, with 8.4–11.3s prefix inference and retained acoustic-event errors.
