# Chapter 5 experiment ledger

This ledger distinguishes a complete experiment from a supported hypothesis.
`official_complete` means every execution/evidence gate in the Chinese
manuscript has substantive evidence; a statistically negative result remains
a complete experiment and is reported as such.

| Experiment | Canonical evidence | Status | `official_complete` | Hypothesis | Evidence SHA-256 |
| --- | --- | --- | --- | --- | --- |
| 5-1 | `code-for-math/validation/runs/exp5-1-ark-doubao-flash-aime2024-20260730-v1/manifest.json` | passed | true | not supported | `3f4508457ae620efdb8864ed52ef150d3e584da128f2249ca18553904d6f571a` |
| 5-2 | `code-for-logic/validation/real_ark_doubao_flash_hf84_20260730.json` | passed | true | contradicted | `ac602aebf67e9b2ee508f3472f4348fd7c30edd05098fed8cbc6ebef15d2df28` |
| 5-3 | `small-model-codified-rules/validation/real_ollama_qwen3_4b_60x2_20260730.json` | passed | true | not supported | `003c8e0593623b700a173b463199ae080a6c7bcbcedce1f5568d579515da66ab` |
| 5-4 | `paper-to-ppt/validation/runs/exp5-4-real-pdf-both-20260730-v9/comparison_summary.json` | passed | true | context advantage supported; quality tied | `bfd913d311ab4d6ad5a8cae93b61ce54ce6d19f9d2d10ee2afdef06becd1e09f` |
| 5-5 | `paper-to-video/validation/runs/exp5-5-kimi-fish-qwen-20260730-v1/manifest.json` | passed | true | supported | `93bb69a916a76d12de56270928971f6e39f47755214f7a135817d7effd8b3f09` |
| 5-6 | `video-edit/validation/runs/exp5-6-real-blender-20260730-055102/manifest.json` | passed | true | supported | `fd044738e812faa832863f4c112880a9583c268afb7d08f388c00623498ab7a8` |
| 5-7 | `adaptive-log-parser/validation/runs/20260729T212342Z-5_7-live/manifest.json` | passed | true | supported | `00851a7b15fba8bad94422b7870b9eda1a9f3b12f3e509b2d768db244edc2507` |
| 5-8 | `log-diagnosis/validation/runs/exp5-8-live-http-mcp-20260730-053403/manifest.json` | passed | true | supported | `68e09e7c8b4fc100e0612a6f81978079c393a822025bfa794b6dda85134a5813` |
| 5-9 | `dynamic-form/validation/runs/20260729T212542Z-5_9-live-browser/manifest.json` | passed | true | supported | `6e6b2cc9c31071c880f2c66a7f172d4933a1ee2f51ac7206b89a1cd89dca08a7` |
| 5-10 | `erp-agent/validation/runs/20260729T210334Z-5_10-postgresql/manifest.json` | passed | true | supported | `5b167f34d18cca867b6fa5fe2d61cd1bf4324f618d6e21221fe9131e56aaed16` |
| 5-11 | `conversational-ui/validation/runs/20260729T212933Z-5_11-hmr/manifest.json` | passed | true | supported | `34d6d8f325ac598b8e55a8a93763dda2bdb019020aa0cf67aa421e861be9279c` |
| 5-12 | `permission-embedded-data-objects/README.md` and `demo.py` | available | false | data-layer authorization and integrity remain enforceable under dynamic application code | — |
| 5-13 | `agent-creator/runs/exp5-12-kimi-k3-20260730-v1/comparison.json` | passed | true | strict joint advantage not observed | `dee9c74c6b89d2563cd78752b75e96293a33159439d87133add220f7d80782ed` |

## Contract observations

- **5-1:** all 30 unique AIME 2024 problems completed in both arms with zero
  provider errors, and every code trajectory called the real sandbox. Code was
  53.3% versus CoT 36.7%, but exact paired p=0.125.
- **5-2:** the pinned K&K revision supplied 84 stratified paired tasks; every
  code trajectory used `python-constraint`. Code was 39.3% versus pure
  reasoning 75.0% (p=2.27e-7 in the opposite direction), so neither >90% nor
  significant improvement is claimed.
- **5-3:** local Ollama `qwen3:4b` completed all 60 frozen cases in both arms
  with database/server-clock truth and full messages/tool receipts. Codified
  rules were 91.7% versus control 95.0% (p=0.6875).
- **5-4:** both arms produced twenty-page Slidev decks from the hash-pinned
  real PDF and all three provenance-tracked original figure crops. Real
  rendering, iterative Vision review and the same independent judge all ran;
  both final decks scored 95 and passed with no high/medium defect. Quality
  tied, while peak context was 24,186 tokens for the split design versus
  92,601 for single-agent self-review (3.83×), and total tokens were 73,227
  versus 298,259.
- **5-5:** twelve real Experiment 5-4 pages received live Kimi K3 narration,
  independent Qwen-VL-Max pixel review, and Fish Audio S1 speech. The H.264/AAC
  result is 513.010 seconds (8.55 minutes); summed page audio is 512.913
  seconds and maximum page drift is 0.024 seconds.
- **5-6:** a real source video was localized coarse-to-fine, Blender executed
  generated scripts, the Vision reviewer rejected the negative control and
  triggered correction/refinement, and the accepted boundary error stayed
  within the manuscript's three-second tolerance.
- **5-7:** two live log producers emitted initially unsupported formats; real
  model-generated parsers compiled, passed tests, hot-loaded, parsed the live
  streams, and produced a browser-rendered visualization.
- **5-8:** real local HTTP trajectories drove model diagnosis and executable
  regression tests; every test failed on the buggy service and passed after
  the fix. The official `github/github-mcp-server` created
  `https://github.com/bojieli/ai-agent-book/issues/502`.
- **5-9:** a real model generated the Beijing-flight cascading form; Chromium
  verified one submission containing departure city/date, one-way/round-trip,
  and conditionally visible return date.
- **5-10:** PostgreSQL held both required tables, the real model generated SQL
  artifacts for all ten manuscript questions, and the database results were
  independently checked and browser-rendered without asking the model to copy
  result rows.
- **5-11:** three real-model customization turns changed color, typography,
  layout and component placement in a React/FastAPI app; Vite HMR was observed
  in-browser after every source mutation and a production build passed.
- **5-12:** the copied PEDO implementation includes a deterministic PostgreSQL
  demo and core/scenario tests. A live Agent-generated-code campaign remains an
  optional reader run rather than completed evidence.
- **5-13:** both generated Agents passed structure, compilation, tests,
  standard tool protocol, real Kimi K3 tasks and multi-turn state gates. The
  template arm tied deterministic quality (39/39 each) while using 1,181
  creator tokens versus 381,814 and 24.7 seconds versus 5,412.8 seconds; it was
  more efficient but not strictly higher quality.

The retained 5-13 comparison directory is named `exp5-12-...` because that
campaign ran before the manuscript renumbered the Agent-creator experiment.
The protocol, source code, chapter text, and current index all identify it as
Experiment 5-13; the historical directory name is intentionally preserved so
the evidence hash and provenance remain stable.
