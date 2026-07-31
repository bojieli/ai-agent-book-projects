# 实验 8-4：从浏览器轨迹生成可验证工作流

本项目展示“把经验写成程序”的第一种形式：Agent 首次探索网页任务后，把动作轨迹参数化为工作流；但首次成功只产生 `candidate`，不能直接进入能力库。候选工作流必须在重置后的环境中完整重放，并通过每一步的状态谓词与最终状态谓词，才会成为 `validated`。页面变化导致谓词失败时，旧版本转为 `invalid`，系统退回完整 Agent 重新探索。

## 离线机制预检

```bash
python workflow_validation_demo.py
python -m unittest -v test_state_predicates.py
```

该命令只用于预检生命周期代码，不能作为正文的真实浏览器验收。它演示：

```text
首次轨迹 → candidate → 重置环境 → 完整回放通过 → validated → 能力库
                                                        │
                                               页面或接口发生变化
                                                        ↓
                                      谓词失败 → invalid → 完整 Agent 重学
```

`WorkflowStep` 现在包含 `preconditions` 与 `postconditions`，`Workflow` 包含 `final_predicates`。内置谓词覆盖 URL 包含、元素可见、元素文本包含和页面状态值相等。`WorkflowReplayer` 在动作前后检查真实 Playwright 页面；任一谓词失败都会立即中止，返回明确原因与 `fallback_required=True`，不会把“动作执行过”误报为任务成功。

`KnowledgeBase` 将候选区与正式能力库分开。`save_workflow` 拒绝未验证对象；`publish_validated` 只接收完整回放通过的版本；`invalidate_workflow` 会把失效版本移出检索，同时保留审计文件。

## 正文验收：真实模型、HTTP 站点与 Chromium

`run_experiment_8_4.py` 启动一个仅监听 `127.0.0.1` 的可重置消息站。页面通过真实 HTTP/JavaScript 写入服务端状态；真实模型在四个观察—决策—动作回合中选择控件，Playwright Chromium 执行动作。所有收件人和消息均为虚构数据，运行不会发送电子邮件或产生站外副作用。

```bash
pip install -r requirements.txt
playwright install chromium
python run_experiment_8_4.py \
  --provider ark \
  --model doubao-seed-1-6-flash-250615 \
  --seed 8401
```

正式运行严格覆盖正文四阶段：

1. Agent 向 `test@example.com` 发送主题“测试邮件”的首条消息，逐步保存参数、URL、XPath、CSS、`id`、`name`、`role`、`aria-label`、`data-testid` 和页面状态，只生成 `candidate`。
2. 通过独立 HTTP `validation_reset` 清空服务端状态，再完整检查动作前、动作后和最终 `sent-list`；通过后才发布为 `validated`。无 reset 的负对照始终不可检索。
3. 对收件人、主题、正文均不同的任务匹配正式工作流并参数化回放，回放阶段不调用 LLM，也不复用首轮字面量。
4. 页面把 `#send` 改为 `#deliver-v2` 后，前置谓词在产生发送请求之前中止工作流；版本转为 `invalid`、移出检索，并返回 `fallback_required=True`。

同一工作流还在“正文为空”和“服务端接受但不持久化”两种故障下运行两遍：只数动作的基线报告 2/2 假成功，带状态验证的实验组报告 0/2 假成功。

2026-07-30 的证据为 `validation/real_20260729T171233Z/evidence.json`，SHA-256 为
`a673c657c670482c7d4bedc0dd340ee51586f3e8d6feb440bb7cc216edca426c`。
同目录还保存探索完成截图、候选快照、无 reset 候选和失效版本；`validation/latest.json` 保存同一证据。全部 13 项执行门槛和 5 项结果声明通过。

本次结果：探索 5.313 秒、4 次 LLM 调用；不同参数回放 4.447 秒、0 次 LLM 调用，实测加速 1.195 倍；匹配率、回放成功率、页面变化检出率均为 100%，回退重学计数为 1。该结果证明本次运行有加速，但没有声称复现 PreAct 论文的 8.5–13 倍。ARK 共返回 3,999 Token，未返回货币费用字段，故美元成本保持 `null`。

## 通用 browser-use 封装

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

`learning_agent/agent.py` 保留对 browser-use 的通用封装。上游 `browser-use/` 副本保持不变，本实验的生命周期与验证逻辑全部位于封装层。
真实浏览器演示仍可使用 `demo_email.py` 和 `demo_weather.py`，需要安装根目录 `ch8` 依赖、Chromium 与模型 API。

真实 LLM + 浏览器的最小冒烟测试如下；`--quick` 在这里不是 dry-run，它会实际调用模型并控制 Chromium：

```bash
# 从仓库根目录开始：使用共享的第 8 章环境
uv sync --locked --python 3.12 --extra ch8
# Apple Silicon macOS 需要 macOS 14+（锁文件中的 bitsandbytes wheel 要求）；
# 更早的 macOS 请使用下方单项目兼容路径。

# 切换目录前先激活环境：
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

# 未安装 uv 时可用 pip 兜底：
# python -m pip install -e ".[ch8]"

cd chapter8/browser-use-rpa

# 迁移期间仍支持单项目兼容路径（playwright-stealth 等历史可选依赖）：
# python -m pip install -r requirements.txt

playwright install chromium
export OPENAI_API_KEY=your_api_key_here
python demo_email.py --quick --headless --model gpt-5.6
```

对于其他目标站点，调用者仍必须自行提供安全的 `validation_reset`。没有可重置环境时，真实 LLM 轨迹只能形成候选，不应为了“验证”而在生产账号中重复发送邮件或提交订单。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `learning_agent/workflow.py` | 状态谓词、工作流结构与 candidate/validated/invalid 生命周期 |
| `learning_agent/replay.py` | 基于 Playwright 的动作执行和前置/后置/最终验证 |
| `learning_agent/knowledge_base.py` | 候选审计、验证后发布、失效隔离 |
| `learning_agent/agent.py` | 首次探索、参数化、重置回放与失败回退 |
| `workflow_validation_demo.py` | 纯标准库的确定性状态机演示 |
| `test_state_predicates.py` | 生命周期、页面变化和序列化测试 |
| `local_mail_sandbox.py` | 可重置的本地 HTTP/JavaScript 消息站和服务端环境真值 |
| `run_experiment_8_4.py` | 正文四阶段真实模型 + Chromium 验收与原始证据保存 |
| `test_real_playwright_campaign.py` | 对真实 Chromium 的 reset、参数化、假成功与失效测试 |

该项目检验的是“轨迹能否编译成经过验证的可执行能力”，而不只是回放速度。真实系统还应为高风险动作加入权限检查、幂等键、沙盒账号和人工批准。
