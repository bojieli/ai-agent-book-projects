# 实验 8-6：评估 Agent 是否在持续进化

本实验把评估对象从“单次任务是否成功”扩展到一条长期任务流。任务不会简单重复，而是依次经历四个阶段：学习阶段暴露可共享规律，迁移阶段更换表述和环境，规则变化阶段要求修订旧能力，保持阶段重新测试未变化能力与当前有效规则。

```bash
python demo.py
python demo.py --profile evolving
python demo.py --output output/report.json
python -m unittest -v test_longitudinal.py
```

实验完全离线，不需要 API Key。`dataset.json` 包含退款、身份核验和行李政策三个任务族。行李规则在第三阶段从 20kg 改为 23kg，因此只会追加知识、不会淘汰旧规则的 Agent 会在变化阶段和保持阶段持续失败。

上述命令使用可控参考 Agent 来校验评估框架。要让真实 LLM 逐题决策并经历同一条外部记忆更新流：

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=your_api_key_here
python demo.py --profile llm --model gpt-5.6 --output output/llm-report.json
```

该路径会对 14 个顺序任务真实调用 OpenAI Responses API，产生 API 费用。环境在每个带反馈的任务后更新版本化规则，但不会把 `expected_action` 泄露给当前调用；最终仍由 Harness 计算迁移、适应、保持、安全、负迁移与实际 Token/延迟。参考 Agent 与真实 LLM 应在同一数据流上分别运行，前者验证指标实现，后者才构成模型实验。

`demo.py` 提供三个可控参考 Agent：

- `evolving` 能保存经验，也能用更高版本替换旧规则；
- `append_only` 能学习第一版规则，却不能更新或淘汰它；
- `static` 不持久化任何生产反馈。
- `llm_evolving` 由真实 LLM 选择动作，并读取同一份版本化外部记忆。

它们不是被宣称为真实模型，而是用于检查评估框架是否能区分三种长期行为。你可以用自己的 Agent 替换 `ReferenceAgent`，只需实现 `act(task)`、`observe(task)`、`profile` 和 `storage_bytes`。

## 报告指标

`LongitudinalEvaluator` 输出每阶段准确率、学习曲线、迁移准确率、规则变化后的恢复速度、保持率、负迁移率、安全 Rubric 通过率，以及 Token、时间和存储成本。逐任务记录还保留实际动作、使用的知识版本和本轮是否发生更新。

其中“规则变化后的恢复速度”以收到第一条新规则信号后，还需要多少个任务恢复正确为准；“负迁移”统计 Agent 调用了已有经验却因此答错的情况；保持率只按最后阶段的当前有效规则计算，避免把继续执行已经废止的旧政策误当成记忆良好。

这个实验刻意避免把全部指标压成一个总分。一个 Agent 可能迁移很好，却无法更新旧知识；也可能保持率高，却靠违反规则的捷径完成任务。持续进化只有在适应性、保持性、效率和安全性同时可见时才有可解释的意义。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `dataset.json` | 四阶段顺序任务流与环境反馈 |
| `agent.py` | evolving、append-only、static 三种参考行为 |
| `harness.py` | 长期运行、分阶段统计、成本与安全评估 |
| `demo.py` | 命令行对照实验 |
| `test_longitudinal.py` | 迁移、规则更新、保持和四阶段完整性测试 |

旧版“发现、创造并复用工具”的四层评估已不再作为本章主实验；这类工具创造仍可作为持续进化闭环中的一个更新载体，但不能单独证明 Agent 能在长期运行中适应变化并避免遗忘。
