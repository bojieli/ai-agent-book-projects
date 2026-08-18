# AI 写作风格 Skill：开放式提炼 + LLM-as-a-judge

本项目把用户对「AI 味」的 before/after 纠正持续提炼为写作规则。提炼代码不再包含
`PATTERN_LIBRARY` 或 detector 白名单：模型可以从反馈中发现词表之外的语义、句法、
语气和篇章问题。所有候选规则统一交给 LLM judge，并且只有通过独立人工金标校准后
才能进入最终 Skill。

默认模型是 OpenAI `gpt-5.6-sol`，OpenAI 直连使用 Responses API 的 JSON 输出。

```bash
# 从仓库根目录开始
uv sync --locked --python 3.12 --extra ch8
source .venv/bin/activate
source ~/.zshrc                  # 载入本机 OPENAI_API_KEY

cd chapter9/ai-style-skill
python -m pytest -q test_pipeline.py
python run_ai_style_skill.py     # 默认 --provider openai --model gpt-5.6-sol
```

单元测试用假的批量 judge，因而无需 API key；完整验收必须调用真实模型。原始请求、响应、
Token 用量、延迟和哈希写入 `validation/<run>/evidence.json`，凭据值不会落盘。

## 完整循环

1. **收集**（`data/feedback_pairs.json`）：26 条用户纠正，除了原有案例，还加入长句信息堆叠、重复「值得注意的是」和连续被动语态等库外问题。
2. **开放式提炼**（`extract_rules.py`）：模型一次比较完整反馈语料，在同一次语义判断中归并重复现象、分开不同问题。这样不会因批次顺序把一个概念拆成多个 id，或把两个相似表面形式误并。代码验证 source id 和正反例确实来自输入，并把 detector 固定为 `{"type": "llm"}`。
3. **合并**（`skill_manager.py`）：模型输出必须使用唯一规则 id；管理器只做机械的 id 去重与来源合并，不再按预置 detector 指纹过滤。模型仍只能提出候选，不能自行激活规则。
4. **校准**（`judge.py`、`data/golden_set.json`）：每条规则用与其反馈来源关联的独立人工正反例校准；一致率低于 0.8 或没有金标覆盖时拒绝上线。
5. **评估**（`evaluate.py`、`data/eval_texts.json`）：人工标注使用反馈来源而不是写死模型生成的规则 id。这样规则名称可动态变化，同时库外保留样本仍能揭示漏检。
6. **改写**（`rewrite_demo.py`）：只把通过校准的 active 规则交给模型改写，不再提供预置换写模式。

judge 会在一次请求里评判一段文本与全部 active 规则，避免为每条规则分别调用 API；
校准时也会批量评判一条规则的全部金标样本。解析失败或缺失 verdict 一律按校准不一致处理。

## 防止新的自洽闭环

- 提炼输入只有用户纠正和当前已提炼规则，没有八类模式清单。
- 候选不会因为无法映射到已有 detector 而回退或丢弃。
- 金标集和 boundary/retention 集是独立人工文本，不复用提炼用的 before/after。
- 评估集明确保留三类原模式库之外的问题，并为相似但合理的写法提供 retention 反例。
- 激活、阈值门槛、证据校验和 API 回执仍由模型外部代码控制。

第三方 OpenAI 兼容端点仍可通过 `--provider ark` 或 `--provider openrouter` 使用；本项目的
OpenAI 默认路径和验收基线使用 `gpt-5.6-sol`。

## 真实验收结果（2026-08-18）

使用 `--provider openrouter --model openai/gpt-5.6-sol` 完成真实运行，证据见
`validation/real_20260818T130450Z/evidence.json`，`validation/latest.json` 为同一份结果：

- 完整语料开放式提炼出 11 条唯一规则，11 条全部通过独立金标校准，一致率均为 1.0。
- boundary 检出 10/11，超过 0.85 门槛；retention 误伤 0/11。
- 长句信息堆叠、重复强调套话和连续被动语态三类库外保留样本全部命中对应新规则。
- 35 次真实 API 调用均保留回执，共使用 86,002 tokens；证据文件不记录凭据值。
