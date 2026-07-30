# 实验 9-4：Step-Audio R1 四配置外部复现轨道（未完成）

正文实验的验收对象不是“任意端到端语音请求”，而是表 9-1 的四行：不思考直接回答、MPS Speak-First、MPS Think-First、完整 TBS；并且必须分别在完整 Spoken-MQA 与 URO-Bench 上用对应评测器复算。当前目录是**外部复现轨道**，尚无可验收的真实结果。论文分数不会被复制成“本机结果”，单路径 API 演示也不会冒充四配置实验。

Step-Audio R1 是音频编码器 + adapter + Qwen2.5 32B 解码器，需要 Linux 和多张 NVIDIA GPU。客户端严格采用上游 `stepfun-ai/Step-Audio-R1` 的 customized-vLLM 协议：WAV 被编码为 `input_audio`，assistant 以 `<think>\n` 开始，使用 `continue_final_message`、`stop_token_ids=[151665]`，并从流式 `content` / `tts_content.tts_text` / `tts_content.tts_audio` 读取结果和首 token 延迟。

## 部署

```bash
hf download stepfun-ai/Step-Audio-R1 --local-dir /models/Step-Audio-R1
cd chapter9/end-to-end-speech
export STEP_AUDIO_MODEL_DIR=/models/Step-Audio-R1
./deploy_step_audio_r1.sh
```

脚本使用上游镜像 `stepfun2025/vllm:step-audio-2-v20250909`、4-way tensor parallel、仓库内的上游等价 chat template，并在 `localhost:9999` 暴露 OpenAI-compatible endpoint。上游报告测试配置为 4×L40S/H100/H800/H20。

## 精确验收矩阵

| 配置 | Spoken-MQA | URO-Bench | 当前公开可复算 |
| --- | --- | --- | --- |
| 不思考直接回答 | 完整数据集+官方评分 | 完整数据集+官方评分 | 否 |
| MPS Speak-First | `spkfirst` checkpoint/serving mode+评分 | 同左 | 否 |
| MPS Think-First | `thkfirst` checkpoint/serving mode+评分 | 同左 | 否 |
| 完整 TBS | 无延迟约束 TBS+评分 | 正文表中无该分数 | 否 |

2026-07-29 审计的官方 GitHub tree 为 `c73a43cd1f64f07b5d68ef4a41a0b2e4125ae6f8`；Hugging Face `Step-Audio-R1` 为 `60a56dbe86918b0a85b07ec29f2c8983025e7073`，`R1.1` 为 `8abb296c09123345b09de57dbc2830b6a12134b1`。公开树含 MPS 论文和一条 `spoken_mqa_test.wav`，但没有四种可参数切换的 serving/evaluation modes、完整 Spoken-MQA 评测器或 URO-Bench 评测资产。可重复审计：

```bash
python validate_upstream.py
```

脱敏结果在 `validation/upstream_audit.json`。

## 公开单路径诊断（不计作实验验收）

若另行提供真实 customized-vLLM endpoint，可用一条口述数学题与一条中文对话 WAV 检查公开 R1 请求协议：

```bash
cp env.example .env
python demo.py \
  --endpoint http://localhost:9999 \
  --audio spoken_mqa.wav --task spoken-mqa \
  --instruction 'Solve the spoken math problem step by step.' \
  --audio uro_dialogue.wav --task uro-bench \
  --instruction 'Respond naturally and appropriately to the spoken user.'
```

`demo.py` 先验证 `/v1/models` 确实提供 `Step-Audio-R1`，随后运行：

- Step-Audio R1：直接基于音频 latent 做推理，记录完整 response、TTFT、总延迟及 audio token 数；
- 级联对照：`whisper-1 → gpt-4o-mini`，记录被 ASR 压平后的 transcript 与总延迟。

证据写入 `validation/latest.json`。这只能证明公开单路径可调用；`--skip-cascade` 只用于服务调试。两者都不能使表 9-1 验收通过。

## 当前精确阻塞

本机没有 `STEP_AUDIO_ENDPOINT`、NVIDIA/CUDA 或四卡 GPU。即使另有单个 R1 endpoint，缺失的四模式与完整评测资产仍会阻止正文实验验收。只有上游提供这些精确资产，或获得作者内部复现环境后，才能继续；不得用 GPT Audio、普通 R1 单路径或 Whisper→LLM 替代。

```bash
pytest -q
```

---

## English

This is an incomplete external reproduction track. Acceptance requires the exact four Table 9-1 configurations and the full Spoken-MQA/URO-Bench evaluators. The public single-path R1 client is diagnostic only. No substitute model or copied paper score counts.
