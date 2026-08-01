# 实验 9-4：本地运行 MiniCPM-o 4.5 端到端全模态语音

本实验属于正文的“**范式二 · 端到端全模态模型（Omni）**”，不属于后文的“边想边说”方案。它用同一个开放权重模型 MiniCPM-o 4.5 比较两条路径：

- **端到端路径**：WAV 直接进入模型的音频编码器与隐空间，模型直接回答；
- **自级联路径**：同一模型先把 WAV 转成纯文字，再只依据文字回答，主动丢弃语速等副语言信息。

另加一条 audio-to-audio 检查，确认模型不仅能听，还能在本地生成 24kHz 语音。实验关闭 `enable_thinking`，因此结果不能用来声称复现 Step-Audio R1 的 MPS、Speak-First、Think-First 或“边想边说”。

## 实验设计

`fixtures/cases.json` 固定四条小型合成语音：两道只依赖语义的口述算术题，以及文字完全相同、语速分别为快和慢的两条副语言题。每条都运行端到端与自级联两臂。小样本只用于验证机制与本地可运行性，不是模型排行榜；合成音也不能替代真人、多口音与噪声数据集。

| 维度 | 端到端臂 | 自级联臂 |
| --- | --- | --- |
| 输入 | 单声道 WAV（读取时重采样为模型要求的 16kHz） | MiniCPM-o 生成的纯文字转录 |
| 回答模型 | MiniCPM-o 4.5 | 同一个 MiniCPM-o 4.5 |
| 是否保留语速 | 是 | 否（转录提示明确只保留说出的文字） |
| 采样 | 关闭 | 关闭 |
| 思考模式 | 关闭 | 关闭 |

固定模型为 `openbmb/MiniCPM-o-4_5@1f761131fa83f5ed3cd6f2f22b225c4501d154fa`。官方实现由 SigLip2、Whisper-medium、CosyVoice2 与 Qwen3-8B 组成，总计约 9B 参数；本实验只初始化音频与 TTS 分支，不初始化视觉分支。

## 安装

上游明确测试 Python 3.10、`transformers==4.51.0`、PyTorch 2.3–2.8。该组合与仓库共享环境里的其他实验可能冲突，因此这里有意使用独立虚拟环境：

```bash
cd chapter9/end-to-end-speech
uv venv .venv --python 3.10
uv pip install --python .venv/bin/python -r requirements.txt
source .venv/bin/activate

hf download openbmb/MiniCPM-o-4_5 \
  --revision 1f761131fa83f5ed3cd6f2f22b225c4501d154fa
```

需要 Linux、NVIDIA CUDA GPU 和约 21GB 可用显存。只有扩展到视频输入/输出时才需要 FFmpeg；本次 WAV→文本/语音 campaign 不调用 FFmpeg。模型权重与上游 Python 自定义代码会被下载到 Hugging Face cache，运行前应按自己的供应链策略审查并固定 revision。

## 运行

```bash
python demo.py \
  --local-files-only \
  --evidence validation/runs/exp9-4-minicpmo45-20260801-v1/evidence.json \
  --output-dir validation/runs/exp9-4-minicpmo45-20260801-v1/outputs

python validate_evidence.py \
  validation/runs/exp9-4-minicpmo45-20260801-v1/evidence.json
```

`demo.py` 一次加载模型，随后保存每条输入的 SHA-256、两臂原始回复、模型自产转录、分阶段延迟、模型 revision、软件版本、GPU 信息，以及语音输出的 SHA-256/采样率/时长。验收只要求真实本地路径完整且证据闭环，**不要求假设必须为正**。

没有 GPU 时可运行离线单元测试，但不能据此宣称完成真实实验：

```bash
python -m pytest -q tests
python demo.py --help
```

合成输入可用 `python prepare_fixtures.py` 重建（需要 `espeak`）；正式证据以仓库中 WAV 的 hash 为准。

## 本地结果

2026-08-01 的[本地 canonical run](validation/runs/exp9-4-minicpmo45-20260801-v1/evidence.json)已通过[全部 11 项验收](validation/runs/exp9-4-minicpmo45-20260801-v1/acceptance.json)。硬件是单张 96GB RTX PRO 6000 Blackwell，PyTorch 2.8.0+cu128、Transformers 4.51.0、BF16/SDPA；模型加载 6.154 秒，峰值分配显存 20.269GiB。

| 任务 | 端到端 | 自级联 |
| --- | ---: | ---: |
| 语义算术（2 条） | 1/2 | 2/2 |
| 副语言语速（2 条） | 2/2 | 1/2 |
| 合计 | 3/4 | 3/4 |

总分相同但错误互补。端到端在第一题把 “twelve boxes” 感知成 8，算出 47；自级联先正确转录出 12，再算出 79。相反，快/慢两条音频在自级联中都被压成完全相同的 `Please send the report before lunch.`，于是它把 fast 样本也猜成 slow；端到端保留了速度信息，两条都正确。

加载完成后的平均整次调用为端到端 0.686 秒、自级联 0.551 秒。由于端到端固定先跑、回复长度不同且只有四条，这不是可推广的延迟排名。audio-to-audio 臂另生成了[11.56 秒、24kHz 单声道 WAV](validation/runs/exp9-4-minicpmo45-20260801-v1/outputs/spoken-math-boxes-response.wav)，但它继承了第一题的感知错误。这是有价值的负结果：路径真实跑通不等于答案正确。

---

## English

Experiment 9-4 now belongs to Paradigm 2, end-to-end omni models. It runs the pinned MiniCPM-o 4.5 checkpoint locally and compares native audio-to-answer inference against a self-cascade that first flattens the same audio to text. A separate audio-output arm retains a real 24kHz waveform. Thinking is deliberately disabled; this experiment makes no MPS or “thinking while speaking” claim.
