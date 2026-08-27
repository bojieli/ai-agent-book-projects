#!/usr/bin/env bash
set -uo pipefail
EXP=/Users/boj/book/ai-agent-book/chapter9/tau2-escalation-experience
TAU=/Users/boj/book/ai-agent-book/chapter7/tau2-bench
while pgrep -f 'run_arms.sh' >/dev/null; do sleep 10; done
echo "[$(date +%T)] 首轮已结束，开始补齐"
cd "$EXP"
./resume_arm.sh armA-baseline   "$EXP/policies/baseline_main_policy.md"
./resume_arm.sh armB-evolved-v1 "$EXP/validation/runs/exp9-2-tau2-escalation-v1/evolved_main_policy.md"
./resume_arm.sh armC-evolved-v2 "$EXP/validation/runs/exp9-2-tau2-escalation-v2/evolved_main_policy.md"
cp "$EXP/policies/baseline_main_policy.md" "$TAU/data/tau2/domains/telecom/main_policy.md"
echo "[$(date +%T)] 全部完成，策略已恢复原状"
