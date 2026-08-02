# 实验 8-6：把这本书交给 Hermes：它能升级自己吗？

如果 Agent 读到一本讲“Agent 如何进化”的书，它能不能回头看看自己，并真的学会一项新本领？
我们没有让 Hermes 只写一份读后感，而是把整本书和它自己的源码一起交给它，让它边读边改自己。

## 我们做了什么

这个实验思路由读者 Grace 贡献。核心做法不是给 Hermes 一张问题清单，而是让
[Hermes](https://github.com/NousResearch/hermes-agent) 读完本书十章，再回到自己的代码里寻找
值得改进的地方。实验 Prompt 明确不提供候选能力或预设缺口；选什么、为什么选、怎样实现，都由
Hermes 根据书和源码自行判断。

整个过程可以记成一句话：

> **阅读 → 对照 → 选题 → 修改 → 审查 → 学习 → 再修改**

## Hermes 真的做了什么

Hermes 读完十章并检查自身实现后，主动发现：虽然系统会保存运行轨迹，但这些记录缺少可直接供后续
学习使用的结构化证据。它决定从真实工具结果中提取保守的学习信号，让离线评价与后续改进不必只依赖
最终文本或主观总结。

关键是，它不只提出建议。Hermes 亲手修改了自己的轨迹处理与保存路径、补充测试、运行验证，并留下
一份可应用的补丁。这让“读书后获得启发”变成了“读书后改变自己”。

## Reviewer 如何推动它继续改

第一版没有过关。独立 Reviewer 发现它的测试数据与真实轨迹格式不一致；修正后，新的 Reviewer 又
发现部分保存路径没有采用同一证据契约；第三轮继续发现重复计数和遗漏路径。每次反馈都交还给同一个
Hermes 会话，由它重新读代码、修正并再试。第四位全新 Reviewer 最终接受候选。Reviewer 的拒绝不是
实验终点，而是 Hermes 下一轮学习的输入。

## 这个实验证明了什么

这次运行完成了一个真实的自我更新闭环：Hermes 在没有候选清单的情况下读书、检查自己、自主选题并
实现改进，又根据独立审查反复纠错，直到通过验收。最终候选通过 6 个新增行为测试和 38 个相关回归测试。

不过，“成功更新自己”和“所有任务表现都变强”是两回事。要证明后者，还需要在相同任务和模型下，
分别开关新能力做消融实验。本实验诚实地停在前一个结论：**Hermes 已经学会根据书和反馈修改自己，
但这项修改对下游任务的收益仍要另行测量。**

下面保留完整证据，方便核对或复现。Canonical 开放式运行固定在 Hermes commit
`85c8956ec7f2b4607509980794995e1c5e21e292`，使用 `openai/gpt-5.6-luna`，补丁尚未合入上游。

- [Evidence manifest](validation/exp8-6-hermes-gpt56luna-autonomous-20260802-v2/manifest.json)
- [Hermes 自述报告](validation/exp8-6-hermes-gpt56luna-autonomous-20260802-v2/BOOK_SELF_EVOLUTION_REPORT.md)
- [最终候选补丁](validation/exp8-6-hermes-gpt56luna-autonomous-20260802-v2/hermes-self-evolution.patch)
- 原始主运行、三轮 proposer 修正与四次 fresh acceptance review transcript 位于
  [`raw/`](validation/exp8-6-hermes-gpt56luna-autonomous-20260802-v2/raw/)

证据边界：这次运行证明了 Agent 能阅读、审计、生成候选代码并根据外部审查纠错；它**没有**
证明新的轨迹学习信号提升了下游任务成功率。Hermes 在报告中设计了固定任务、固定模型、逐项关闭功能的
消融 campaign，但本次没有执行，因此不能把“完成自我更新闭环”写成“下游任务已经变强”。

## 复现

要求：Git、`uv`、Python 3.12，以及 `OPENROUTER_API_KEY`。Hermes 使用自己的隔离环境，
不依赖根项目的 Chapter 8 extra。

```bash
cd chapter8/hermes-self-evolution
cp env.example .env
# 把真实 OPENROUTER_API_KEY 放入当前 shell 或未跟踪的 .env；不要提交。
set -a && source .env && set +a

python run_experiment_8_6.py --run-id your-run-id
```

主运行会把 clone 放在忽略的 `worktree/`，把 Hermes 状态放在忽略的 `.hermes-home/`，并把
去凭据的证据写到 `validation/<run-id>/`。每次开放式运行可能选择不同改进，因此必须先独立审查实际
候选，再把具体反馈写成新的 review task 交回 proposer。Canonical 运行的三轮反馈保存在
`review_task_autonomous_1.md` 至 `review_task_autonomous_3.md`：

```bash
python run_review_pass.py --run-id your-run-id --task your-review-task.md --output review-1.txt
python run_acceptance_review.py --run-id your-run-id --round 1
```

审查 Prompt 针对 canonical 候选的具体缺陷；如果新运行生成了不同实现，应先独立检查再编写
对应反馈，而不是机械套用。`acceptance_review.md` 与 `run_acceptance_review.py` 提供 fresh
terminal gate；被拒后应把具体问题作为新的 review task 返回 proposer，再用新的 reviewer
home 重跑。`finalize_evidence.py` 用于 canonical 证据收口，包括终局 `ACCEPT` 检查、测试、
补丁可应用性和凭据形状扫描。

普通离线预检不需要 API key：

```bash
python -m py_compile run_experiment_8_6.py run_review_pass.py run_acceptance_review.py finalize_evidence.py
python run_experiment_8_6.py --help
```

## English summary

What happens when an agent reads a book about agent evolution and then looks back at
its own code? Reader Grace contributed the experiment idea. We gave Hermes this entire
book and access to its own source, but no candidate improvement or alleged gap. Hermes
read the chapters, inspected itself, chose one useful improvement, and implemented it.

Hermes independently chose to add evidence-backed learning signals to saved execution
trajectories. The first version was not accepted. Each independent Reviewer rejection
became the next lesson: Hermes read the feedback, changed its code again, and sent a new
version for fresh review. Three reviews found more work; the fourth accepted the result,
and 44 focused tests passed. The experiment completes a real loop: **read → compare →
choose → change → review → learn → change again**. Whether the new feature improves
downstream performance remains a separate question for an ablation experiment.
