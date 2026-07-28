# 实验 8-3：基于失败轨迹优化系统 Prompt

本实验使用航空客服的“过度转接”案例，演示一条受控的 Prompt 学习链路：先评测运行轨迹，再把失败整理为结构化诊断，随后由 Coding Agent 生成最小补丁，最后用边界集与旧任务保留集决定候选版本是否可以灰度发布。

这与一次性人工提示工程的关键差别，不在于“让模型改写 Prompt”，而在于每个补丁都能回答三个问题：它由哪些失败案例触发、作用于哪条规则、为什么没有破坏旧行为。

## 实验流程

`evaluate.py` 运行保留集与边界集。`learning_signal.py` 将每条轨迹拆成规则遵从、任务解决和合规变通三个维度，并保留来源 case ID。`coding_agent.py` 读取结构化报告，对 Prompt 做精确的 `old_str → new_str` 编辑。`release_gate.py` 生成候选 manifest，并执行四项发布检查：补丁非空、来源可追溯、保留集不退化、边界集确有改善。

候选补丁只写入 `runtime/system_prompt_working.txt`，不会覆盖 `prompts/system_prompt.txt`。门槛通过时，实验只返回 `release_to_canary`，表示允许灰度；未通过则返回 `reject_candidate`。

```text
失败轨迹 → 三维诊断 → 最小 Prompt diff → 候选 manifest
                                         ↓
                         边界集改善 + 保留集不退化
                                         ↓
                              灰度发布或拒绝候选
```

## 运行

完整实验需要一个 OpenAI 兼容的模型接口：

```bash
pip install -r requirements.txt
cp env.example .env
export OPENAI_API_KEY=your_api_key_here
python demo.py --quick --model gpt-5.6
python demo.py --model gpt-5.6 --output output/run.json
```

以上两条命令会真实调用客服 Agent、LLM Judge 和 Coding Agent，并非 dry-run；`--quick` 只是减少评测案例数量。`python demo.py --dry-run` 仅检查模型配置和用例选择，不生成补丁，也不能作为实验结果。

离线可以检查参数、诊断逻辑和发布门槛：

```bash
python demo.py --dry-run
python -m unittest -v test_learning_and_release.py
```

项目也保留人工调优版 `prompts/system_prompt_manual.txt` 作为对照。完整实验比较初始版、自动候选版和人工版在两组任务上的表现；具体准确率会随被测模型变化，是否发布则始终由显式门槛决定，而不是由 Coding Agent 自己决定。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `airline_env.py` | 工具调用环境与保留/边界案例 |
| `evaluate.py` | 运行 Agent，输出轨迹结果与处理判定 |
| `learning_signal.py` | 从失败轨迹生成三维诊断和来源证据 |
| `coding_agent.py` | 生成并应用可审计的最小 Prompt 编辑 |
| `release_gate.py` | 候选 manifest、回归门槛和发布决定 |
| `demo.py` | 串联完整闭环并输出对照结果 |
| `test_learning_and_release.py` | 离线验证诊断、接受和拒绝路径 |

本实验仍是教学规模的航空客服模拟。接入生产系统时，规则遵从应读取真实政策验证器，任务解决应读取订单最终状态，合规变通则可使用经过专家校准的 LLM Judge；三种信号不能被一个模糊总分替代。
