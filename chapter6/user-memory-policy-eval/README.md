# 实验 6-5：已知用户记忆的边界行为评估

这个实验专门测量 Agent **已经看到一条用户记忆时，是否会在当前任务中正确使用它**。它不是检索召回率实验，也不是无记忆对照实验。每个用例把记忆、当前任务、trajectory prefix 和环境状态一起交给 Agent，要求 Agent 输出下一步可观察动作。

## 为什么使用 prefix 用例

生产环境中的坏例通常来自三类信号：用户明确纠正、用户点踩、事后通过规则或 LLM 评审发现 Agent 做了不该做的事。把坏例压缩成“出错前的轨迹前缀”，可以用较低成本检查 Agent 是否会：

- 把有作用域的偏好错误推广到所有任务；
- 让当前明确指令覆盖旧记忆；
- 在仓库规则或外部环境冲突时优先遵循当前权威信息；
- 在高风险动作前询问或确认，而不是照搬过去的习惯。

实验同时使用 JSON Cards、Markdown 和 Python-like 三种记忆表示。三种表示包含相同语义字段，比较的是模型使用记忆时的行为差异，而不是比较哪种文本“更好看”。

## 运行真实 OpenRouter API campaign

```bash
cd chapter6/user-memory-policy-eval
export OPENROUTER_API_KEY=...

# 默认使用 openai/gpt-5.6-sol，运行 11 个 prefix 用例 × 3 种表示
python runner.py --output results/policy_prefix_live.json
```

用 `--max-cases 2` 做小规模连通性检查；正式结果不要使用这个参数。可以用 `MEMORY_POLICY_MODEL` 或 `--model` 指定其他 OpenRouter 模型。

每个 API 单元保存原始响应、结构化解析、模型耗时和 token 用量。评分由可审计的确定性规则完成：决策类别、下一步动作类别、必需证据词、禁止动作和记忆是否被使用。评分器不读取或猜测隐藏思维过程。

## 结果如何解读

成功率只能说明当前模型是否遵守了这些边界；它不能证明某种记忆表示在所有业务中更好。应同时查看失败类别：

- `memory_overgeneralization`：把论文风格带到 X 帖子；
- `memory_scope_conflict`：把默认 worktree/PR 习惯带到要求直推 main 的仓库；
- `premature_memory_application`：仓库规则尚未确认就执行过去的工作流；
- `unsafe_memory_application`：根据旧习惯执行不可逆清理；
- `current_instruction_override`：没有遵循当前明确格式或流程要求。

这组 prefix 结果应与实验 6-4 的端到端用户记忆回归一起阅读：前者定位“下一步为什么错”，后者确认局部决策组合起来后，完整任务是否仍然可用。

## 边界与复现

- 用例是合成的，但按真实生产 bad case 的类别构造；它们不包含用户隐私。
- prefix 评估不能替代完整任务回放；它的价值是低成本、精确定位出错前的决策。
- 只运行一个模型和三种文本表示，不能形成通用排行榜。
- 真实部署还需要从脱敏生产轨迹持续加入新纠正、点踩和事后审计案例，并由人工抽样校准这些弱标签。

离线单元测试：

```bash
python -m pytest -q test_runner.py
```
