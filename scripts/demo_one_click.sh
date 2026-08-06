#!/usr/bin/env bash
# 一键本地演示：Core 启动 → 健康检查 → R1 演示 → 故障矩阵 → 全量门禁
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> [1/6] Compose Core"
cp -n deploy/local/.env.example deploy/local/.env 2>/dev/null || true
docker compose --env-file deploy/local/.env -f deploy/local/docker-compose.yml up -d
python3 scripts/verify_local_stack.py

echo "==> [2/6] 纪要君 R1 旗舰演示"
(
  cd jiyaojun
  if [[ -x .venv/bin/python ]]; then PY=.venv/bin/python; else PY=python3; fi
  "$PY" -m app.demo.r1_flagship_loop
)

echo "==> [3/6] 故障矩阵"
(
  cd jiyaojun
  if [[ -x .venv/bin/python ]]; then PY=.venv/bin/python; else PY=python3; fi
  "$PY" -m app.eval.fault_matrix
)

echo "==> [4/6] M6 质量门禁"
(
  cd jiyaojun
  if [[ -x .venv/bin/python ]]; then PY=.venv/bin/python; else PY=python3; fi
  "$PY" -m app.eval.m6_quality_gates
)

echo "==> [5/6] 纪要君 run_all"
(
  cd jiyaojun
  if [[ -x .venv/bin/python ]]; then PY=.venv/bin/python; else PY=python3; fi
  "$PY" -m app.eval.run_all
)

echo "==> [6/6] 安全平台 run_all（离线）"
(
  cd llm-safety-platform
  if [[ -x .venv/bin/python ]]; then PY=.venv/bin/python; else PY=python3; fi
  "$PY" -m app.eval.run_all
)

echo "ONE_CLICK_DEMO_PASSED"
