# Experiment 7-16 reproduction anchor

The book-owned guide is this directory; executable code belongs in `chapter7/RLVP/rlvp` and comes from [`19PINE-AI/rlvp`](https://github.com/19PINE-AI/rlvp). The current workspace has no such checkout. A read-only upstream audit fixed revision `1ad30bc7e338911fb733739393d92c420f4d8bee` and verified the entrypoints below; no RLVP training or evaluation was run.

```bash
git clone https://github.com/19PINE-AI/rlvp.git chapter7/RLVP/rlvp
git -C chapter7/RLVP/rlvp fetch origin 1ad30bc7e338911fb733739393d92c420f4d8bee
git -C chapter7/RLVP/rlvp checkout --detach 1ad30bc7e338911fb733739393d92c420f4d8bee
git -C chapter7/RLVP/rlvp rev-parse HEAD
test "$(git -C chapter7/RLVP/rlvp rev-parse HEAD)" = "1ad30bc7e338911fb733739393d92c420f4d8bee"
```

At this revision, the audited sequence is `python3 tests/test_rules.py && python3 tests/test_credit.py`, `python3 scripts/phase0_baseline.py`, `bash scripts/run_all.sh`, and `python3 scripts/eval_checkpoint.py results/run_c3/final c3_norules`. The full campaign requires CUDA. The chapter's reported paper results are not a current-workspace execution claim.

## English

# Experiment 7-16: RLVP —— Reward the Outcome, Penalize the Path

> 📖 **The complete training/evaluation code corresponding to this experiment is in the standalone paper repository: [`github.com/19PINE-AI/rlvp`](https://github.com/19PINE-AI/rlvp)**
>
> RLVP (Reward the Outcome, Penalize the Path) is a post-training study by the author team. All results reported in Chapter 7, Experiment 7-16 of the book (violation rate, miniF2F, full-loss group proportion, etc.) come from experiments in that repository. Since training depends on GPU clusters and the code is continuously updated alongside the paper, the main book repository no longer duplicates it. Please go directly to the upstream repository for the latest code, configuration, and reproduction instructions:

```bash
# Use the pinned clone/fetch/detached-checkout/SHA-verification block above.
```

## Relationship with Other Training Experiments in This Chapter

This directory, like `chapter7/AdaptThink`, `chapter7/retool`, and `chapter7/AWorld-train`, belongs to the **reproduction guide (KEEP-EXT)**: the core training code resides in an external repository; simply follow its README to reproduce. For an explanation of the method and conclusions, see the corresponding section on "Model Post-Training" in Chapter 7 of the book.

---

## 中文

# 实验 7-16：RLVP —— 奖励结果、惩罚路径

> 📖 **本实验对应的完整训练/评估代码在独立论文仓库：[`github.com/19PINE-AI/rlvp`](https://github.com/19PINE-AI/rlvp)**
>
> RLVP（Reward the outcome, Penalize the path）是作者团队的一项后训练研究。书中第 7 章
> 实验 7-16 报告的各项结果（违规率、miniF2F、全败组占比等）均来自该仓库的实验。由于训练
> 依赖 GPU 集群、且代码随论文持续更新，本书主仓库不再重复内置，请直接前往上游仓库获取最新
> 代码、配置与复现说明：

```bash
# 请使用本 README 顶部固定版本的 clone/fetch/detached-checkout/SHA 校验命令。
```

## 与本章其它训练类实验的关系

本目录与 `chapter7/AdaptThink`、`chapter7/retool`、`chapter7/AWorld-train` 等一样，属于
**复现指南（KEEP-EXT）**：核心训练代码在外部仓库，按其 README 复现即可。书中对方法与结论的
讲解见正文第 7 章「模型后训练」相应小节。
