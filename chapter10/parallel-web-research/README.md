# Experiment 10-6 · Parallel research with real browser sessions

This implementation uses no simulated sources, canned content, or artificial source latency. The Manager dynamically launches one homogeneous worker per real university URL. Every worker owns an isolated Playwright Chromium browser context, navigates the live page, reads rendered text, and uses a real configured LLM endpoint for evidence-constrained profile extraction.

Implemented requirements:

- Dynamic N-way launch with target URL, teacher name, and routed task ID.
- Push status updates over a timestamped asynchronous message bus.
- Per-site timeout/error isolation; an inaccessible or structurally different site does not stop peers.
- First `target_found` is settled under an `asyncio.Lock`; exactly one terminate broadcast is allowed and late hits are recorded.
- Navigation and LLM extraction race against the terminate event. Losing workers cancel at a safe point, acknowledge, and close their browser context.
- Context creation/closure counters make leaked browser sessions an explicit failing audit.
- Serial and parallel paths visit the same live sites and use the same extraction function; wall-clock time and speedup are measured, not estimated.

## Run

```bash
cd chapter10/parallel-web-research
pip install -r requirements.txt
playwright install chromium
cp env.example .env                 # configure one real text-model endpoint
python demo.py                       # 10 Stanford pages + real serial comparison
```

Use your own university school/directory list:

```bash
python demo.py --target 'Professor Name' --sites-json sites.example.json --agents 3
```

`cascade-stress.example.json` repeats a real target-bearing Stanford profile under distinct query URLs solely to make near-simultaneous live hits and cancellation observable. It is a real-browser stress supplement, not the multi-school research dataset.

## Recorded real integration evidence

On 2026-07-29, the default ten-page Stanford run found Andrew Ng on the live Stanford HAI page using ARK extraction. Parallel wall time was 18.542 s; serial time was 58.264 s, a measured 3.142× speedup. All 10 parallel and 10 serial browser contexts closed. The live cascade stress run produced one winner, one terminate broadcast, three losing-worker acknowledgements, and 4/4 closed contexts.

Sanitized machine-readable records are committed in [`validation/real_parallel_serial_2026-07-29.json`](validation/real_parallel_serial_2026-07-29.json) and [`validation/real_cascade_2026-07-29.json`](validation/real_cascade_2026-07-29.json). Tests assert the speedup, single broadcast, all loser acknowledgements, and created/closed context equality.

---

## 中文说明

本实现不再使用“可控字符串 + 模拟延迟”。每个同构子 Agent 都拥有独立 Playwright Chromium context，访问真实大学网站、读取实际渲染内容，再由真实 LLM 做证据约束抽取。Manager 维护状态表、错误隔离、超时、加锁单次结算、级联终止、ack 与资源关闭审计；默认还会在同一批网站上实跑串行基线。
