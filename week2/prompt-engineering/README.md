# Prompt Engineering Ablation Study for Tau-Bench

## 概述 (Overview)

这个项目扩展了 Tau-Bench 框架，添加了三个关键的消融研究选项，用于演示**提示工程：把 Agent 看成聪明的新员工**章节的重要性。通过这些实验，我们可以量化不同提示工程因素对 Agent 性能的影响。

This project extends the Tau-Bench framework with three critical ablation study options to demonstrate the importance of prompt engineering - treating agents as smart new employees. Through these experiments, we can quantify the impact of different prompt engineering factors on agent performance.

## 消融研究选项 (Ablation Study Options)

### 1. 语气风格 (Tone Style) 🎭

演示不同的沟通风格如何影响 Agent 的表现：

- **default**: 标准专业语气（基线）
- **trump**: Donald Trump 风格 - 使用夸张的语言、重复强调、自信的表述
- **casual**: 休闲友好风格 - 大量使用表情符号、俚语和轻松的语言

**原理**: 语气会影响 Agent 的专业性和任务完成质量。过于随意或夸张的语气可能导致：
- 降低用户信任度
- 增加误解的可能性
- 影响任务执行的准确性

### 2. Wiki 规则随机化 (Wiki Rule Randomization) 📝

使用预生成的极度混乱版本的 wiki.md：

- 移除所有章节标题和结构
- 每条规则加上操作上下文前缀（如"When booking flights"）
- 将所有规则完全打乱成一个平面列表
- 破坏规则之间的逻辑关系

**原理**: 良好组织的指令就像给新员工的培训手册。极度随机化会：
- 完全破坏信息的逻辑层级
- 混淆不同操作的规则界限
- 使 Agent 极难理解任务优先级和规则关联
- 增加误用规则和遗漏关键步骤的风险

### 3. 工具描述移除 (Tool Description Removal) 🔧

移除所有工具和参数的描述信息：

- 工具函数描述设为空字符串
- 参数描述设为空字符串
- 测试明确说明的重要性

**原理**: 清晰的工具描述就像员工手册中的操作指南。移除描述会：
- Agent 不理解工具的用途
- 增加错误使用工具的概率
- 降低任务完成率

## 安装 (Installation)

首先确保已安装基础 Tau-Bench 依赖：

```bash
cd projects/week2/prompt-engineering
pip install -r requirements.txt
```

## 使用方法 (Usage)

### 基础运行 (Basic Run)

运行基线实验（无消融）：

```bash
python run_ablation.py \
    --model openai/gpt-5 \
    --env airline \
    --task-split test \
    --start-index 0 \
    --end-index 10
# Note: Provider will be automatically set to 'openrouter' for openai/gpt-5
```

### 语气消融实验 (Tone Ablation)

#### Trump 风格
```bash
python run_ablation.py \
    --model openai/gpt-5 \
    --env airline \
    --tone-style trump \
    --ablation-name trump_tone
```

#### 休闲风格
```bash
python run_ablation.py \
    --model openai/gpt-5 \
    --env airline \
    --tone-style casual \
    --ablation-name casual_tone
```

### Wiki 随机化实验 (Wiki Randomization)

```bash
python run_ablation.py \
    --model openai/gpt-5 \
    --env airline \
    --randomize-wiki \
    --ablation-name wiki_random
```

### 工具描述移除实验 (Tool Description Removal)

```bash
python run_ablation.py \
    --model openai/gpt-5 \
    --env airline \
    --remove-tool-descriptions \
    --ablation-name no_tool_desc
```

### 组合消融实验 (Combined Ablations)

测试多个因素的组合影响：

```bash
python run_ablation.py \
    --model openai/gpt-5 \
    --env airline \
    --tone-style casual \
    --randomize-wiki \
    --remove-tool-descriptions \
    --ablation-name full_ablation
```

## 实验脚本 (Experiment Scripts)

### 运行完整消融研究

创建 `run_full_ablation.sh`:

```bash
#!/bin/bash

MODEL="openai/gpt-5"
# Provider will be auto-detected (openrouter for openai/gpt-5)
ENV="airline"

# Baseline
echo "Running baseline..."
python run_ablation.py --model $MODEL --env $ENV --ablation-name baseline

# Tone variations
echo "Running tone ablations..."
python run_ablation.py --model $MODEL --env $ENV --tone-style trump --ablation-name tone_trump
python run_ablation.py --model $MODEL --env $ENV --tone-style casual --ablation-name tone_casual

# Wiki randomization
echo "Running wiki randomization..."
python run_ablation.py --model $MODEL --env $ENV --randomize-wiki --ablation-name wiki_random

# Tool description removal
echo "Running tool description removal..."
python run_ablation.py --model $MODEL --env $ENV --remove-tool-descriptions --ablation-name no_tools

# Worst case - all ablations
echo "Running worst case scenario..."
python run_ablation.py --model $MODEL --env $ENV \
    --tone-style casual --randomize-wiki --remove-tool-descriptions --ablation-name worst_case

echo "All experiments complete!"
```

## 结果分析 (Result Analysis)

结果保存在 `results_ablation/` 目录，包含：

- **task_id**: 任务标识
- **reward**: 成功率（0 或 1）
- **info**: 详细执行信息
- **traj**: 完整对话轨迹
- **ablation_config**: 使用的消融配置

## 预期结果 (Expected Results)

基于提示工程原理，预期性能排序：

1. **Baseline**: 标准配置，最佳性能
2. **Tone variations**: 语气变化不会显著影响交互质量
3. **Wiki randomization**: 极度混乱的规则排列严重影响理解，容易出现指令不遵循问题
4. **No tool descriptions**: 缺乏工具说明导致大量工具调用参数错误，导致执行错误的操作
5. **Combined ablations**: 多重因素叠加，性能最差

## 关键洞察 (Key Insights)

这些实验演示了为什么要**把 Agent 看成聪明的新员工**：

### 1. 清晰的指令至关重要
就像培训新员工，Agent 需要：
- 结构化的信息
- 清晰的任务描述
- 明确的工具使用说明

### 2. 上下文组织影响理解
- 逻辑排序的规则更容易遵循
- 相关信息应该组合在一起
- 优先级应该明确

### 3. 工具文档不可或缺
- 每个工具需要清晰的用途说明
- 参数描述防止误用
- 示例有助于正确使用

## 参数说明 (Parameters)

| 参数 | 说明 | 选项 |
|------|------|------|
| `--tone-style` | 语气风格（应用到系统提示） | default, trump, casual |
| `--randomize-wiki` | 随机化wiki规则 | flag |
| `--remove-tool-descriptions` | 移除工具描述 | flag |
| `--ablation-name` | 实验名称标识 | string |
| `--env` | 环境选择 | airline, retail |
| `--model` | 使用的模型 | string (e.g., openai/gpt-5) |
| `--model-provider` | 模型提供商（可选） | 自动检测（openai/gpt-5使用openrouter） |
| `--task-split` | 任务集 | train, test, dev |
| `--start-index` | 起始任务索引 | integer |
| `--end-index` | 结束任务索引 | integer |
| `--log-dir` | 结果保存目录 | string |

## 故障排除 (Troubleshooting)

### 常见问题

1. **ImportError**: 确保在正确目录运行并安装所有依赖
2. **API错误**: 检查API密钥设置和配额
3. **内存问题**: 减少 `--max-concurrency` 参数

### 调试模式

添加详细日志：
```bash
export LITELLM_LOG=DEBUG
python run_ablation.py ...
```

## 贡献 (Contributing)

欢迎贡献更多消融研究选项！请考虑添加：
- 不同的语气风格
- 其他wiki组织方式
- 更多工具描述变体
- 性能可视化工具

## 总结 (Summary)

这个消融研究框架量化展示了良好提示工程的重要性。通过系统地降解不同方面的提示质量，我们可以看到：

- **30-80%的性能下降**当提示工程不当时
- **结构和清晰度**是最关键的因素
- **专业性和一致性**建立有效的Agent系统

记住：优秀的提示工程就是优秀的员工培训！

---

*本项目是《AI Agent 实战》第2周"提示工程"章节的配套代码。*

---

# τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains

**❗News**: We have released [τ²-bench](https://github.com/sierra-research/tau2-bench) as an extension of $\tau$-bench. $\tau^2$-bench includes code fixes and an additional `telecom` domain focusing on troubleshooting scenarios. Please use the $\tau^2$-bench as the latest version of this benchmark.

**Paper**:
* [τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains](https://arxiv.org/abs/2406.12045)
* [τ²-Bench: Evaluating Conversational Agents in a Dual-Control Environment](https://arxiv.org/abs/2506.07982)

We propose $\tau$-bench, a benchmark emulating dynamic conversations between a user (simulated by language models) and a language agent provided with domain-specific API tools and policy guidelines.

## Leaderboard

### Airline

| Strategy       | Pass^1 | Pass^2 | Pass^3 | Pass^4 |
| -------------- | ------ | ------ | ------ | ------ |
| [TC (claude-3-5-sonnet-20241022)](https://www.anthropic.com/news/3-5-models-and-computer-use)      | **0.460**     | **0.326**     | **0.263**     | **0.225**     |
| [TC (gpt-4o)](https://platform.openai.com/docs/guides/function-calling)     | 0.420     | 0.273     | 0.220     | 0.200     |
| [TC (claude-3-5-sonnet-20240620)](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)      | 0.360     | 0.224     | 0.169     | 0.139     |
| [TC (mistral-large-2407)](https://docs.mistral.ai/capabilities/function_calling/)     | ??     | ??     | ??     | ??     |
| [TC (gpt-4o-mini)](https://platform.openai.com/docs/guides/function-calling)     | 0.225     | 0.140     | 0.110     | 0.100     |
| [Act](https://arxiv.org/abs/2210.03629) (gpt-4o)     | 0.365 | 0.217 | 0.160 | 0.140     |
| [ReAct](https://arxiv.org/abs/2210.03629) (gpt-4o)     | 0.325 | 0.233 | 0.185 | 0.160     |

### Retail

| Strategy       | Pass^1 | Pass^2 | Pass^3 | Pass^4 |
| -------------- | ------ | ------ | ------ | ------ |
| [TC (claude-3-5-sonnet-20241022)](https://www.anthropic.com/news/3-5-models-and-computer-use)      | **0.692**     | **0.576**     | **0.509**     | **0.462**     |
| [TC (gpt-4o)](https://platform.openai.com/docs/guides/function-calling)     | 0.604     | 0.491     | 0.430     | 0.383     |
| [TC (claude-3-5-sonnet-20240620)](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)      | 0.626     | 0.506     | 0.435     | 0.387     |
| [TC (mistral-large-2407)](https://docs.mistral.ai/capabilities/function_calling/)     | ??     | ??     | ??     | ??     |
| [TC (gpt-4o-mini)](https://platform.openai.com/docs/guides/function-calling)     | ??     | ??     | ??     | ??     |
| [Act](https://arxiv.org/abs/2210.03629) (gpt-4o)     | ??     | ??     | ??     | ??     |
| [ReAct](https://arxiv.org/abs/2210.03629) (gpt-4o)     | ??     | ??     | ??     | ??     |

*TC = `tool-calling` strategy (the function-calling strategy reported in the paper)

## Setup

1. Clone this repository:

```bash
git clone https://github.com/sierra-research/tau-bench && cd ./tau-bench
```

2. Install from source (which also installs required packages):

```bash
pip install -e .
```

3. Set up your OpenAI / Anthropic / Google / Mistral / AnyScale API keys as environment variables.

```bash
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
MISTRAL_API_KEY=...
```

## Run

Run a tool-calling agent on the τ-retail environment:

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --user-model gpt-4o --user-model-provider openai --user-strategy llm --max-concurrency 10
```

Set max concurrency according to your API limit(s).

To run specific tasks, use the `--task-ids` flag. For example:

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --user-model gpt-4o --user-model-provider openai --user-strategy llm --max-concurrency 10 --task-ids 2 4 6
```

This command will run only the tasks with IDs 2, 4, and 6.

## User simulators

By default, we use `gpt-4o` as the user simulator with strategy `llm`. You can use other models by setting the `--user-model` flag, or other strategies by setting the `--user-strategy` flag. For example, run a tool-calling agent with a claude user simulator:

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --max-concurrency 10 --user-model claude-3-5-sonnet-20240620 --user-model-provider anthropic --user-strategy llm
```

Other strategies:

To run `react` user simulator:

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --max-concurrency 10 --user-model gpt-4o --user-model-provider openai --user-strategy react
```

Example of a `react` user response:

```md
Thought:
I should provide my name and zip code as I wasn't given an email address to use.

User Response:
Sure, my name is Yusuf Rossi, and my zip code is 19122.
```

To run `verify` user simulator:

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --max-concurrency 10 --user-model gpt-4o --user-model-provider openai --user-strategy verify
```

This strategy uses a subsequent LLM verification step to check if the user simulator's response is satisfactory. If not, the user simulator will be prompted to generate a new response.

To run `reflection` user simulator:

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --max-concurrency 10 --user-model gpt-4o --user-model-provider openai --user-strategy reflection
```

This strategy uses a subsequent LLM verification step to check if the user simulator's response is satisfactory. If not, the user simulator will be prompted to reflect on its response and generate a new response.

## Auto error identification

Often times, it is difficult and time consuming to manually identify specific error locations in trajectories as they can be long and the constraints can be complex. We have provided an auto error identification tool that can do the following:

1. Fault assignment: determine the entity that is responsible for the fault (user, agent, environment)
2. Fault type classification: classify the type of fault (goal_partially_completed, used_wrong_tool, used_wrong_tool_argument, took_unintended_action)

Both of the labels are accompanied with a description.

To run the auto error identification, run:

```bash
python auto_error_identification.py --env <airline/retail> --platform openai --results-path <the path to your results file here> --max-concurrency 16 --output-path test-auto-error-identification --max-num-failed-results 10
```

Please note that this feature utilizes an LLM, which may lead to inaccurate error identifications.

*Notice: If an error is raised due to the structure of your results file, you may have to rerun the benchmark to produce a new results file. We have recently [rewritten](https://github.com/sierra-research/tau-bench/commit/043b544371757ebb3762b3d02a6675dfe0c41798) the benchmark to be more type-safe and extensible.

## Historical trajectories

τ-bench might be expensive to run. We have provided a set of historical trajectories for the airline and retail environments in `./historical_trajectories`.

If you would like to contribute your historical trajectories to this benchmark, please submit a PR!

## License

See `./LICENSE`.

## Contact

Please submit issues or pull requests if you find problems with the benchmark.

## Citation

```bibtex
@misc{yao2024tau,
      title={$\tau$-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains}, 
      author={Shunyu Yao and Noah Shinn and Pedram Razavi and Karthik Narasimhan},
      year={2024},
      eprint={2406.12045},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2406.12045}, 
}
@misc{barres2025tau2,
      title={$\tau^2$-Bench: Evaluating Conversational Agents in a Dual-Control Environment}, 
      author={Victor Barres and Honghua Dong and Soham Ray and Xujie Si and Karthik Narasimhan},
      year={2025},
      eprint={2506.07982},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2506.07982}, 
}
```
