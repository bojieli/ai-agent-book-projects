# 实验 9-3：Qwen2-Audio 递增前缀模拟流式感知

本项目实际运行 `Qwen/Qwen2-Audio-7B-Instruct`：每收到一个新块，就把 `[0:t]` 的完整累积音频再次送入 Qwen2-Audio，输出当前 transcript 和声学事件。它不是 Whisper 替代实现，也不会把这种全量重编码称作真流式。

对照组是传统 600ms 端点 VAD + 开源 Whisper。三类场景均被测量：正常对话、含 900ms 中途停顿的长句、混入粉红背景噪声的对话。证据记录每个前缀的模型原始输出、单块延迟、最终 CER、事件 token，以及 VAD 分段点、Whisper 推理时长和 CER。

## 安装

```bash
cd chapter9/streaming-speech
pip install -r requirements.txt
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

## 已验证结果

2026-07-29 在 Apple Silicon 上真实运行 `mlx-community/Qwen2-Audio-7B-Instruct-4bit`。正常、停顿、噪声三种输入的最终 transcript 都收敛到参考句，Qwen 每次都重新编码更长的前缀；实测单前缀约 2.7–5.7s，因此本机结果并不伪称书中 GPU 的 100–200ms。强噪声样本确实产生 `<|noise|>`，但同一回答也出现 laughter/cough 假阳性；原始输出完整保存在证据中，便于审计模型的事件检测误差。

```bash
pytest -q
```

---

## English

This is actual Qwen2-Audio growing-prefix inference, not a Whisper substitute. Every `[0:t]` prefix is fully re-encoded and compared with a real 600ms-VAD + open-source Whisper pipeline on normal, long-pause, and noisy speech. CUDA uses the original model; Apple Silicon can use the published 4-bit MLX conversion of the same Qwen2-Audio architecture. Raw responses and measured results are saved under `validation/`.
