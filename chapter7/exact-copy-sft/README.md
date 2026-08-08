# 实验 7-19：特殊字符串的精确复述 SFT

本实验从 Coding Agent 的 `old_string` 匹配失败出发，区分模型复制错误与 tokenizer、序列化、Harness 和工具层错误，然后用未见过的随机字符串和工具参数任务训练 Qwen3-8B 的 LoRA 适配器。训练目标是 byte-exact 复制，而不是语义相似或“看起来一样”。

## 运行

```bash
cd chapter7/exact-copy-sft
python generate_data.py
python train_sft.py --model Qwen/Qwen3-8B
python evaluate.py --model Qwen/Qwen3-8B --adapter output/adapter
python tokenizer_audit.py
```

训练和评估必须使用本机 CUDA GPU 与开源 Hugging Face 模型。数据按随机种子、字符串长度、token 组合和上下文包装隔离；`validation/` 保存训练回执和独立回归报告。

扩容后先对三类任务、10 种语言上下文和 8 种文章体裁做分层人工抽查，记录见 [`validation/manual_audit.md`](validation/manual_audit.md)；再运行 tokenizer 审计，避免把 tokenizer/序列化损坏误判为模型能力问题。

如果模型在直接复述探针中正确、但工具调用仍失败，应修复 Harness 或工具协议，不应把系统层损坏误报为后训练收益。

本机 RTX PRO 6000 实测：1024 条训练样本、256 条留出样本、256 条边界样本，训练 2 个 epoch、Qwen3-8B bf16 LoRA。留出集 byte-exact accuracy 从基座 37.5% 提升到 78.9%，独立边界集为 80.1%；平均首次字节分歧位置分别为 54.0 和 54.2。另用 512 条留出/边界探针审计 3 个开源 tokenizer：Qwen3 与 Qwen2.5 round-trip 均为 80.1%，Mistral 为 100%，说明 tokenizer 层也必须单独设回归门禁。结果文件见 `validation/eval_base_eval.json`、`validation/eval_adapted_eval.json`、`validation/eval_adapted_boundary.json` 和 `validation/tokenizer_audit.json`。
