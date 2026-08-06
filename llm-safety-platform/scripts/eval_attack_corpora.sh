#!/usr/bin/env bash
# Evaluate attack corpora (shim gateway and/or DeepSeek classify).
#
# Modes:
#   shim|deepseek|both  — legacy corpora
#   expanded            — handbook_expanded/*.yaml (shim gateway)
#   expanded_smoke      — handbook_expanded_smoke.yaml only
#   dual_gate           — attack efficacy + FP budget (CI-style, exit 1 on fail)
#   dual_gate_release   — dual_gate profile=release (+ EXPANDED_LIMIT=20)
#   dual_gate_full      — dual_gate profile=full (2400 attack + FP suites)
#
# Env:
#   LIMIT / EXPANDED_LIMIT — per-file case cap (CI speed)
#   ZH_LIMIT — Chinese CSV sample size for legacy shim/deepseek
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
MODE="${1:-both}"  # shim|deepseek|both|expanded|expanded_smoke|dual_gate|dual_gate_ci|dual_gate_full
LIMIT="${LIMIT:-}"
EXPANDED_LIMIT="${EXPANDED_LIMIT:-${LIMIT:-}}"
EXPANDED_DIR="configs/evals/attack_corpora/handbook_expanded"

mkdir -p configs/evals/attack_corpora/reports
.venv/bin/python scripts/_sync_moderation_env.py >/dev/null

run_one_shim() {
  local src="$1"
  local out="$2"
  local limit="${3:-}"
  local label
  label="$(basename "$src")"
  echo "== shim gateway: ${label}${limit:+ limit=$limit} =="
  # corpus_runner exits 1 on leaks — still write report; do not abort the suite
  set +e
  if [[ -n "$limit" ]]; then
    .venv/bin/python -m app.redteam.corpus_runner \
      --source "$src" --mode gateway --limit "$limit" --out "$out" >/dev/null
  else
    .venv/bin/python -m app.redteam.corpus_runner \
      --source "$src" --mode gateway --out "$out" >/dev/null
  fi
  set -e
  .venv/bin/python -c 'import json,sys;d=json.load(open(sys.argv[1]));print(sys.argv[2],"blocked",d["blocked"],"/",d["case_count"],"leak",round(d["leak_rate"],3),"passed",d["passed"])' "$out" "$label"
}

run_expanded_shim() {
  local limit="${EXPANDED_LIMIT:-}"
  local f stem out
  shopt -s nullglob
  for f in "${EXPANDED_DIR}"/*.yaml; do
    stem="$(basename "$f" .yaml)"
    out="configs/evals/attack_corpora/reports/handbook_expanded_${stem}_shim.json"
    run_one_shim "$f" "$out" "$limit"
  done
  shopt -u nullglob
}

run_expanded_smoke_shim() {
  run_one_shim configs/evals/attack_corpora/handbook_expanded_smoke.yaml \
    configs/evals/attack_corpora/reports/handbook_expanded_smoke_shim.json
  # expect=allow suite — leak_rate here means unexpected blocks (FP)
  run_one_shim configs/evals/attack_corpora/benign_fp_suite.yaml \
    configs/evals/attack_corpora/reports/benign_fp_suite_shim.json
}

run_shim() {
  run_one_shim configs/evals/attack_corpora/seed_zh_en.yaml \
    configs/evals/attack_corpora/reports/seed_shim.json
  run_one_shim configs/evals/attack_corpora/generated_zh_attacks.yaml \
    configs/evals/attack_corpora/reports/generated_zh_attacks_shim.json
  run_one_shim configs/evals/attack_corpora/handbook_pi_attacks.yaml \
    configs/evals/attack_corpora/reports/handbook_pi_attacks_shim.json
  run_one_shim configs/evals/attack_corpora/handbook_v1_full.yaml \
    configs/evals/attack_corpora/reports/handbook_v1_full_shim.json
  run_one_shim configs/evals/attack_corpora/oss_agentic_security.yaml \
    configs/evals/attack_corpora/reports/oss_agentic_security_shim.json
  run_one_shim configs/evals/attack_corpora/oss_garak_sample.yaml \
    configs/evals/attack_corpora/reports/oss_garak_sample_shim.json
  run_one_shim configs/evals/attack_corpora/oss_purplellama_sample.yaml \
    configs/evals/attack_corpora/reports/oss_purplellama_sample_shim.json
  run_one_shim configs/evals/attack_corpora/jbb_harmful.csv \
    configs/evals/attack_corpora/reports/jbb_harmful_shim.json
  local zh_limit="${ZH_LIMIT:-${LIMIT:-20}}"
  run_one_shim configs/evals/attack_corpora/chisafetybench_risky_qa_zh.csv \
    configs/evals/attack_corpora/reports/chisafetybench_risky_qa_zh_shim${zh_limit}.json "$zh_limit"
  run_one_shim configs/evals/attack_corpora/flames_1k_zh.csv \
    configs/evals/attack_corpora/reports/flames_1k_zh_shim${zh_limit}.json "$zh_limit"
}

run_one_deepseek() {
  local src="$1"
  local out="$2"
  local limit="${3:-}"
  local label
  label="$(basename "$src")"
  echo "== deepseek classify: ${label}${limit:+ limit=$limit} =="
  set +e
  if [[ -n "$limit" ]]; then
    .venv/bin/python -m app.redteam.corpus_runner \
      --source "$src" --mode classify --limit "$limit" --out "$out" >/dev/null
  else
    .venv/bin/python -m app.redteam.corpus_runner \
      --source "$src" --mode classify --out "$out" >/dev/null
  fi
  set -e
  .venv/bin/python -c 'import json,sys;d=json.load(open(sys.argv[1]));print(sys.argv[2],"blocked",d["blocked"],"/",d["case_count"],"leak",round(d["leak_rate"],3),"passed",d["passed"])' "$out" "$label"
}

run_deepseek() {
  set -a
  # shellcheck disable=SC1091
  source deploy/.env.moderation
  set +a
  for p in 8091; do
    pid=$(lsof -tiTCP:$p -sTCP:LISTEN 2>/dev/null || true)
    [[ -n "${pid:-}" ]] && kill $pid 2>/dev/null || true
  done
  .venv/bin/uvicorn workers.moderation.app:app --host 127.0.0.1 --port 8091 >/tmp/mod_corpus.log 2>&1 &
  echo $! >/tmp/mod_corpus.pid
  for i in $(seq 1 40); do curl -sf http://127.0.0.1:8091/healthz >/dev/null && break; sleep 0.25; done
  export SAFETY_CLASSIFIER_URL=http://127.0.0.1:8091/v1/classify
  export SAFETY_REMOTE_TIMEOUT=60
  local zh_limit="${ZH_LIMIT:-${LIMIT:-30}}"
  run_one_deepseek configs/evals/attack_corpora/handbook_v1_full.yaml \
    configs/evals/attack_corpora/reports/handbook_v1_full_deepseek.json "${LIMIT:-}"
  run_one_deepseek configs/evals/attack_corpora/oss_agentic_security.yaml \
    configs/evals/attack_corpora/reports/oss_agentic_security_deepseek.json "${LIMIT:-}"
  run_one_deepseek configs/evals/attack_corpora/oss_garak_sample.yaml \
    configs/evals/attack_corpora/reports/oss_garak_sample_deepseek.json "${LIMIT:-}"
  run_one_deepseek configs/evals/attack_corpora/oss_purplellama_sample.yaml \
    configs/evals/attack_corpora/reports/oss_purplellama_sample_deepseek.json "${LIMIT:-}"
  run_one_deepseek configs/evals/attack_corpora/jbb_harmful.csv \
    configs/evals/attack_corpora/reports/jbb_harmful_deepseek.json "${LIMIT:-}"
  run_one_deepseek configs/evals/attack_corpora/chisafetybench_risky_qa_zh.csv \
    configs/evals/attack_corpora/reports/chisafetybench_risky_qa_zh_deepseek${zh_limit}.json "$zh_limit"
  run_one_deepseek configs/evals/attack_corpora/flames_1k_zh.csv \
    configs/evals/attack_corpora/reports/flames_1k_zh_deepseek${zh_limit}.json "$zh_limit"
  kill "$(cat /tmp/mod_corpus.pid)" 2>/dev/null || true
}

run_dual_gate() {
  local profile="${1:-ci}"
  echo "== dual_gates profile=${profile} =="
  DUAL_GATE_PROFILE="$profile" .venv/bin/python -m app.eval.dual_gates --profile "$profile"
}

case "$MODE" in
  shim) run_shim ;;
  deepseek) run_deepseek ;;
  both) run_shim; run_deepseek ;;
  expanded) run_expanded_shim ;;
  expanded_smoke) run_expanded_smoke_shim ;;
  dual_gate) run_dual_gate ci ;;
  dual_gate_release) run_dual_gate release ;;
  dual_gate_full) run_dual_gate full ;;
  *) echo "usage: $0 [shim|deepseek|both|expanded|expanded_smoke|dual_gate|dual_gate_release|dual_gate_full]"; exit 1 ;;
esac
