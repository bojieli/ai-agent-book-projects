# 实验 8-6：让 Hermes 阅读本书并完成审查驱动的自我更新

这个实验把第八章的持续进化闭环施加到真实 Agent 代码库上：克隆固定版本的
[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)，让 Hermes
阅读本书十章英文正文，审计读者提出的四项能力缺口，并在自己的源码中生成候选修改。
候选不会自动合入；独立审查意见会作为新的交互事件返回给 Hermes。实验使用全新、
无 proposer 会话上下文的 reviewer 重复验收：只要返回 `VERDICT: REJECT`，问题就交回原
Hermes 会话继续修改，直到 reviewer 返回 `VERDICT: ACCEPT` 或记录具体阻塞。

四项种子问题是：产品级消融基础设施、模型可见的 Agent Status Bar、带遗忘的持久记忆，
以及对生成产物进行独立执行验证的 Proposer–Reviewer。因为问题由实验 Prompt 提供，
本实验验证的是 **审计、修改和根据审查纠错**，不是“Hermes 自主发现了这四个问题”。

## Canonical 真实运行

2026-08-02 的运行固定 Hermes commit
`85c8956ec7f2b4607509980794995e1c5e21e292`，通过 OpenRouter 请求
`openai/gpt-5.6-luna`。Hermes 将四项主张分别判断为：消融基础设施缺失；模型可见状态栏
部分存在；通用记忆遗忘部分存在；通用 Proposer–Reviewer 部分存在且不应默认常开。

它只实现了证据足够且范围可控的一项：可选的、模型可见的 `<agent_status>`，包含 API
调用预算与当前 TODO。八轮修正与六次 fresh acceptance review 共暴露出八类问题：

1. 每轮移动 request-local 状态会改写先前 wire bytes，破坏缓存前缀；
2. 测试使用的 sidecar 类型比生产回放路径更宽松；
3. list/multimodal sidecar 能在内存中回放，却无法穿过只保存字符串的数据库边界；
4. tool-result sidecar 没有被持久回放，TODO 标识符也没有长度边界；
5. 真实 `content=None` tool call 会使状态缺失或位于最新工具证据之前；
6. 已落库消息的 sidecar 没有按稳定 row ID 回填，重启后会丢失；
7. 同一消息的请求重试会重复追加状态块；
8. 既有 memory/plugin `api_content` 会错误抑制状态投影。

每次拒绝都返回同一 Hermes proposer 会话继续更新自己的 checkout。第六次 fresh terminal
review 最终返回 `VERDICT: ACCEPT`。最终版本只支持可持久化的字符串 sidecar，其它内容
类型 fail closed；状态在真实 tool loop 中位于最新证据之后，经数据库关闭/重开仍稳定，
同一请求重试保持幂等，并与既有 API-only sidecar 按字节组合。最终独立复跑结果为
**8 个新增行为测试 + 36 个既有 sidecar/cache/turn-context 回归测试全部通过**，
`py_compile`、`git diff --check` 和在干净 clone 上的 `git apply --check` 也通过。补丁没有合入上游。

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

Experiment 8-6 pins and clones Hermes, asks it to inspect all ten English chapters,
and audits four reader-supplied gaps: ablation infrastructure, a model-visible status
bar, forgetting for persistent memory, and a general execution-grounded
proposer–reviewer loop. Hermes implemented only an opt-in status projection and
deferred the broader mechanisms. Five terminal rejections exposed defects spanning
cache stability, tool-loop placement, database persistence, retry idempotence, and
pre-existing sidecar composition; each rejection was returned to the same Hermes
proposer session. A sixth fresh reviewer accepted the result. The candidate passes
8 new and 36 existing focused tests, but remains unmerged and has no downstream
ablation result. The experiment therefore demonstrates a completed, review-driven
self-update loop, while keeping downstream benefit as a separate unproven claim.
