#!/usr/bin/env bash
# 故障演示：跑强制故障矩阵并打印恢复说明摘要
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/jiyaojun"
if [[ -x .venv/bin/python ]]; then PY=.venv/bin/python; else PY=python3; fi
"$PY" -m app.eval.fault_matrix
echo "详见 docs/ops/OPERATOR-MANUAL.md §故障演示"
