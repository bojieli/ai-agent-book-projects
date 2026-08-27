#!/usr/bin/env bash
# 在 τ²-bench telecom 迁移集（114 条，与提炼集不相交）上跑三个对照臂。
# 通过替换 main_policy.md 切换策略；每次运行前后记录 sha256，结束后恢复原文件。
set -euo pipefail
TAU=/Users/boj/book/ai-agent-book/chapter7/tau2-bench
EXP=/Users/boj/book/ai-agent-book/chapter9/tau2-escalation-experience
POLICY=$TAU/data/tau2/domains/telecom/main_policy.md
BACKUP=$(mktemp)
cp "$POLICY" "$BACKUP"
restore(){ cp "$BACKUP" "$POLICY"; echo "[$(date +%T)] 已恢复原始策略"; }
trap restore EXIT

AGENT=volcengine/doubao-seed-1-6-flash-250615
USER=volcengine/doubao-seed-1-6-250615

run_arm(){  # $1=臂名  $2=策略文件
  cp "$2" "$POLICY"
  echo "[$(date +%T)] === $1 === 策略 sha256=$(shasum -a 256 "$POLICY" | cut -c1-16) 字符数=$(wc -c <"$POLICY")"
  cd "$TAU"
  .venv/bin/tau2 run --domain telecom \
    --agent-llm "$AGENT" --user-llm "$USER" \
    --num-trials 1 --max-concurrency 10 \
    --task-set-name telecom --save-to "$1" --log-level WARNING </dev/null >/dev/null 2>&1 || true
  echo "[$(date +%T)] $1 完成，落盘 $(python3 -c "
import json;print(len(json.load(open('$TAU/data/simulations/$1.json'))['simulations']))" 2>/dev/null || echo '?') 条"
}

run_arm armA-baseline    "$EXP/policies/baseline_main_policy.md"
run_arm armB-evolved-v1  "$EXP/validation/runs/exp9-2-tau2-escalation-v1/evolved_main_policy.md"
run_arm armC-evolved-v2  "$EXP/validation/runs/exp9-2-tau2-escalation-v2/evolved_main_policy.md"
echo "[$(date +%T)] 三臂全部完成"
