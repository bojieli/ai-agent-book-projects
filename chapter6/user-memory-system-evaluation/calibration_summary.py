#!/usr/bin/env python3
"""Summarize calibration output: per-case calls/tokens/cost, projected to 60 cases."""

import json
import sys
from collections import defaultdict

path = sys.argv[1]
data = json.load(open(path))
records = data["records"]
ok = [r for r in records if r["status"] == "ok"]
err = [r for r in records if r["status"] == "error"]
print(f"records={len(records)} ok={len(ok)} error={len(err)}")

tokens_by_cell_component = defaultdict(int)
chat_in = defaultdict(int)
chat_out = defaultdict(int)
costs = defaultdict(float)
unpriced_tokens = 0
unpriced_requests = 0
latencies = []

for r in ok:
    latencies.append(r["latency_ms"])
    unpriced_tokens += r["unpriced_tokens"] + r["fixed_query_unpriced_tokens"]
    unpriced_requests += r["unpriced_requests"] + r["fixed_query_unpriced_requests"]
    for cur, amt in r.get("cost_by_currency", {}).items():
        costs[cur] += amt
    for cur, amt in r.get("fixed_query_retrieval_cost_by_currency", {}).items():
        costs[cur] += amt
    # main+reranker+judge tokens are merged in input/output tokens;
    # fixed-query tokens are separate.
    chat_in[r["main_model"]] += r["input_tokens"]
    chat_out[r["main_model"]] += r["output_tokens"]

print("\nPer-case totals (one case = 24 cells + 12 fixed-query benchmarks):")
print(f"  primary input tokens by main model: {dict(chat_in)}")
print(f"  primary output tokens by main model: {dict(chat_out)}")
print(f"  fixed-query tokens: {sum(r['fixed_query_input_tokens'] + r['fixed_query_output_tokens'] for r in ok)}")
print(f"  cost by currency: {dict(costs)}")
print(f"  unpriced tokens: {unpriced_tokens}, unpriced requests: {unpriced_requests}")
print(f"  latency_ms sum over records: {sum(latencies):.0f} "
      f"(serial per-cell latency; per-case wall clock differs)")

print("\nProjected x60 cases:")
for cur, amt in costs.items():
    print(f"  {cur}: {amt * 60:.2f}")
print(f"  primary input tokens: {sum(chat_in.values()) * 60:,}")
print(f"  primary output tokens: {sum(chat_out.values()) * 60:,}")

# steps/tool calls distribution
import statistics
steps = [r["steps"] for r in ok]
tools = [r["tool_calls"] for r in ok]
print(f"\nsteps: mean={statistics.fmean(steps):.2f} max={max(steps)}; "
      f"tool_calls: mean={statistics.fmean(tools):.2f} max={max(tools)}")
by_rr = defaultdict(list)
for r in ok:
    by_rr[(r["reranker"], r["main_model"])].append(r["latency_ms"])
for k, v in sorted(by_rr.items(), key=str):
    print(f"  {k}: n={len(v)} mean latency {statistics.fmean(v)/1000:.1f}s")
