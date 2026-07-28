# 实验 8-4：从浏览器轨迹生成可验证工作流

本项目展示“把经验写成程序”的第一种形式：Agent 首次探索网页任务后，把动作轨迹参数化为工作流；但首次成功只产生 `candidate`，不能直接进入能力库。候选工作流必须在重置后的环境中完整重放，并通过每一步的状态谓词与最终状态谓词，才会成为 `validated`。页面变化导致谓词失败时，旧版本转为 `invalid`，系统退回完整 Agent 重新探索。

## 可离线复现的主实验

```bash
python workflow_validation_demo.py
python -m unittest -v test_state_predicates.py
```

模拟页面演示了完整生命周期：

```text
首次轨迹 → candidate → 重置环境 → 完整回放通过 → validated → 能力库
                                                        │
                                               页面或接口发生变化
                                                        ↓
                                      谓词失败 → invalid → 完整 Agent 重学
```

`WorkflowStep` 现在包含 `preconditions` 与 `postconditions`，`Workflow` 包含 `final_predicates`。内置谓词覆盖 URL 包含、元素可见、元素文本包含和页面状态值相等。`WorkflowReplayer` 在动作前后检查真实 Playwright 页面；任一谓词失败都会立即中止，返回明确原因与 `fallback_required=True`，不会把“动作执行过”误报为任务成功。

`KnowledgeBase` 将候选区与正式能力库分开。`save_workflow` 拒绝未验证对象；`publish_validated` 只接收完整回放通过的版本；`invalidate_workflow` 会把失效版本移出检索，同时保留审计文件。

## 接入真实浏览器 Agent

`learning_agent/agent.py` 是对 browser-use 的封装。首次运行会捕获动作、提取参数和保守状态谓词，然后保存候选版本。调用者还必须提供一个 `validation_reset` 回调，用于把测试站点、账号或沙盒恢复到独立初始状态；没有回调时，候选只保留供审计，不会自动发布，以免通过重复发送邮件、重复下单等有副作用的方式“验证”。

```python
agent = LearningAgent(
    task=task,
    llm=llm,
    knowledge_base_path="./knowledge_base",
    validation_reset=reset_test_account,
)
result = agent.run_sync(max_steps=20)
```

真实浏览器演示仍可使用 `demo_email.py` 和 `demo_weather.py`，需要安装 `requirements.txt`、Chromium 与模型 API。上游 `browser-use/` 副本保持不变，本实验的生命周期与验证逻辑全部位于封装层。

真实 LLM + 浏览器的最小冒烟测试如下；`--quick` 在这里不是 dry-run，它会实际调用模型并控制 Chromium：

```bash
pip install -r requirements.txt
playwright install chromium
export OPENAI_API_KEY=your_api_key_here
python demo_email.py --quick --headless --model gpt-5.6
```

完整的候选发布测试还需为目标测试站点实现 `validation_reset`，并使用沙盒账号，随后运行不带 `--quick` 的学习—重放流程。没有可重置环境时，真实 LLM 轨迹只能形成候选，不应为了“验证”而在生产账号中重复发送邮件或提交订单。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `learning_agent/workflow.py` | 状态谓词、工作流结构与 candidate/validated/invalid 生命周期 |
| `learning_agent/replay.py` | 基于 Playwright 的动作执行和前置/后置/最终验证 |
| `learning_agent/knowledge_base.py` | 候选审计、验证后发布、失效隔离 |
| `learning_agent/agent.py` | 首次探索、参数化、重置回放与失败回退 |
| `workflow_validation_demo.py` | 纯标准库的确定性状态机演示 |
| `test_state_predicates.py` | 生命周期、页面变化和序列化测试 |

该项目检验的是“轨迹能否编译成经过验证的可执行能力”，而不只是回放速度。真实系统还应为高风险动作加入权限检查、幂等键、沙盒账号和人工批准。
