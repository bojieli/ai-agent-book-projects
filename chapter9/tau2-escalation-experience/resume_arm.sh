#!/usr/bin/env bash
# tau2 的 executor.map 遇到任一任务异常就整体中止；它支持断点续跑，
# 这里反复续跑直到 114 条全部完成或连续两轮无进展。
set -uo pipefail
TAU=/Users/boj/book/ai-agent-book/chapter7/tau2-bench
EXP=/Users/boj/book/ai-agent-book/chapter9/tau2-escalation-experience
POLICY=$TAU/data/tau2/domains/telecom/main_policy.md
ARM=$1; POLICY_FILE=$2; TARGET=${3:-114}
cp "$POLICY_FILE" "$POLICY"
echo "[$(date +%T)] $ARM 策略 sha256=$(shasum -a 256 "$POLICY"|cut -c1-16)"
cd "$TAU"
prev=-1
for i in $(seq 1 25); do
  n=$(python3 -c "
import json,os
p='data/simulations/$ARM.json'
print(len(json.load(open(p))['simulations']) if os.path.exists(p) else 0)" 2>/dev/null || echo 0)
  echo "[$(date +%T)] $ARM 第 $i 轮前已完成 $n/$TARGET"
  [ "$n" -ge "$TARGET" ] && break
  [ "$n" -eq "$prev" ] && [ $i -gt 2 ] && { echo "连续无进展，停止"; break; }
  prev=$n
  yes y | .venv/bin/tau2 run --domain telecom \
    --agent-llm volcengine/doubao-seed-1-6-flash-250615 \
    --user-llm volcengine/doubao-seed-1-6-250615 \
    --num-trials 1 --max-concurrency 6 \
    --task-set-name telecom --save-to "$ARM" --log-level WARNING >/dev/null 2>&1
done
n=$(python3 -c "import json;print(len(json.load(open('data/simulations/$ARM.json'))['simulations']))")
echo "[$(date +%T)] $ARM 最终 $n/$TARGET"
