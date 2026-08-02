# 实验 8-6：把这本书交给 Hermes：它能升级自己吗？

如果 Agent 读到一本讲“Agent 如何进化”的书，它能不能回头看看自己，并真的学会一项新本领？
我们没有让 Hermes 只写一份读后感，而是把整本书和它自己的源码一起交给它，让它边读边改自己。

## 我们做了什么

一位读者给了我们四条线索：消融实验、系统状态栏、带遗忘机制的记忆，以及负责把关的
Proposal Reviewer。我们让 [Hermes](https://github.com/NousResearch/hermes-agent) 读完本书，
再回到自己的代码里逐项比较。线索只是起点；Hermes 仍要自己判断哪些能力已经存在、哪些真的缺失，
以及哪项改进最值得现在动手。

整个过程可以记成一句话：

> **阅读 → 对照 → 修改 → 审查 → 学习 → 再修改**

## Hermes 真的做了什么

Hermes 没有贪多。它发现有些线索在现有系统里已经部分实现，有些则需要更大的实验才能证明价值，
于是选择先补上一个清楚、可验证的改进：让模型在工作时也能看到自己的剩余预算和当前待办事项。

关键是，它不只是提出建议。Hermes 亲手修改了自己的源码、运行检查，并留下了一份可应用的补丁。
这让“读书后获得启发”变成了“读书后改变自己”。

## Reviewer 如何推动它继续改

第一版没有过关。独立 Reviewer 在真实使用场景中发现问题后，我们把反馈原样交还给同一个 Hermes
会话。Hermes 阅读反馈、重新检查自己的实现，再次修改代码。新的 Reviewer 随后从头验收；如果仍有
问题，就继续下一轮。

前五次最终验收都被退回，Hermes 也因此连续修正了缓存、工具调用、重启恢复和重复请求等场景中的
缺陷。第六位全新 Reviewer 最终接受了候选版本。也就是说，Reviewer 的拒绝不是实验的终点，而是
Hermes 下一轮学习的输入。

## 这个实验证明了什么

这次运行完成了一个真实的自我更新闭环：Hermes 读了书，检查了自己，选择并实现了一项改进，
又根据独立审查反复纠错，直到通过验收。最终候选也通过了相关的新旧测试。

不过，“成功更新自己”和“所有任务表现都变强”是两回事。要证明后者，还需要在相同任务和模型下，
分别开关新能力做消融实验。本实验诚实地停在前一个结论：**Hermes 已经学会根据书和反馈修改自己，
但这项修改对下游任务的收益仍要另行测量。**

下面保留完整证据，方便核对或复现。Canonical 运行固定在 Hermes commit
`85c8956ec7f2b4607509980794995e1c5e21e292`，使用 `openai/gpt-5.6-luna`，补丁尚未合入上游。

- [Evidence manifest](validation/exp8-6-hermes-gpt56luna-20260802-v1/manifest.json)
- [Hermes 自述报告](validation/exp8-6-hermes-gpt56luna-20260802-v1/BOOK_SELF_EVOLUTION_REPORT.md)
- [最终候选补丁](validation/exp8-6-hermes-gpt56luna-20260802-v1/hermes-self-evolution.patch)
- 原始主运行、八轮 proposer 修正与六次 fresh acceptance review transcript 位于
  [`raw/`](validation/exp8-6-hermes-gpt56luna-20260802-v1/raw/)

证据边界：这次运行证明了 Agent 能阅读、审计、生成候选代码并根据外部审查纠错；它**没有**
证明状态栏提升了下游任务成功率。Hermes 在报告中设计了固定任务、固定模型、逐项关闭功能的
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
去凭据的证据写到 `validation/<run-id>/`。Canonical 八轮审查 Prompt 保存在
`review_task.md` 至 `review_task_8.md`。若新候选出现相同缺陷，可按需把对应反馈交回 proposer：

```bash
python run_review_pass.py --run-id your-run-id --task review_task.md --output review-1.txt
python run_review_pass.py --run-id your-run-id --task review_task_2.md --output review-2.txt
python run_review_pass.py --run-id your-run-id --task review_task_3.md --output review-3.txt
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
its own code? We gave Hermes this entire book, four clues from a reader, and access to
its own source. Hermes compared the ideas with what it already had, chose one useful
improvement, and implemented it itself.

The first version was not accepted. Each independent Reviewer rejection became the
next lesson: Hermes read the feedback, changed its code again, and sent a new version
for a fresh review. Five final reviews found more work; the sixth accepted the result,
and the relevant tests passed. The experiment completes a simple but real loop:
**read → compare → change → review → learn → change again**. It shows that Hermes can
update itself from a book and external feedback. Whether the new feature improves
downstream task performance remains a separate question for an ablation experiment.
