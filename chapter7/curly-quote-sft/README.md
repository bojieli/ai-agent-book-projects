# 实验 7-18：中文弯引号的作用域敏感 SFT

本实验从生产反馈“中文文章使用了 ASCII 直引号”出发，先把反馈提炼成可审计的文档 Skill，再用结构化合成数据训练 Qwen3-8B 的 LoRA 适配器。重点不是全局字符替换，而是判断符号所在的作用域：中文自然语言中的引用可以改为 `“”`，英文原文、代码、JSON、路径和标识符必须保持其语法需要的引号。

可读规范保存在 [`SKILL.md`](SKILL.md)；它同时是合成数据的标签依据、训练后的回归规范和规则变更时的重训输入。

## 运行

```bash
cd chapter7/curly-quote-sft
python generate_data.py
python quality_audit.py
python train_sft.py --model Qwen/Qwen3-8B
python evaluate.py --model Qwen/Qwen3-8B --adapter output/adapter
```

训练使用本机 CUDA GPU、bf16 和 LoRA；模型必须是开源 Hugging Face checkpoint。默认数据、模型和评估结果都写入本目录，训练回执位于 `validation/`。

## 验证口径

评估集按作用域逐项计算：中文自然语言引用的转换率、英文原文和代码保护率、非目标文本修改率，以及 Python/JSON/Markdown 的语法完整性。训练集与边界集按模板和组合方式隔离；边界集包含代码注释、嵌套引号、大段英文原文和混合 Markdown。

生产系统仍应保留 Markdown/代码解析和语法检查；参数化模型负责在复杂上下文中学会选择作用域，不能成为唯一的语法安全边界。

本机 RTX PRO 6000 实测：1024 条训练样本、256 条留出样本、256 条边界样本，训练 2 个 epoch、Qwen3-8B bf16 LoRA（256 次更新）。基座留出集 exact 为 0%；加入人工审计后的显式正反规则再训练后，留出集 exact 为 96.9%，边界集为 97.7%，两者动态保护区域保持率均为 100%。Python、JavaScript、Java、Go、Rust、SQL、Shell、YAML、Markdown 等代码类别均达到 100%；JSON 为 68.8%，中文报道引用为 81.3%/93.8%。数据门禁和人工抽查记录见 `validation/quality_audit.json` 与 `validation/manual_audit.md`，结果文件见 `validation/eval_base_eval.json`、`validation/eval_adapted_eval.json` 和 `validation/eval_adapted_boundary.json`。
