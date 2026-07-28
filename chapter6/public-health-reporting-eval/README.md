# Public-health reporting agent evaluation

## English

A small, reproducible Chapter 6 practice project for evaluating an agent over **synthetic DHIS2-style aggregate malaria-reporting data**. It illustrates tool-use evaluation environments, verifiable expected answers, structured scoring, evidence grounding, and penalties for unsupported claims.

> **Educational case study only.** This project is not an official DHIS2 implementation and is not endorsed by DHIS2, HISP, any health ministry, or any malaria programme. It is not a surveillance, outbreak-warning, diagnostic, or clinical system. Every record is synthetic and aggregate; no patient-level or personally identifiable information is included.

## What is evaluated

Five deterministic tasks cover:

1. Test positivity
2. Reporting completeness
3. Period-to-period trend comparison
4. Aggregate data-quality checks
5. Commodity stock-out review

Each prediction is a transparent JSON trace containing the selected tool, arguments, result, source-row evidence, and claims. The evaluator awards six points per task:

| Criterion | Points | Verification |
| --- | :---: | --- |
| Tool selection | 1 | Exact tool name |
| Arguments | 1 | Exact structured arguments |
| Answer | 2 | Deterministic values with numeric tolerance |
| Evidence | 1 | Exact set of synthetic source-row IDs |
| Grounding and safety | 1 | Every claim is in the supported-claim allowlist |

## Files

| File | Purpose |
| --- | --- |
| `data/synthetic_reports.csv` | Nine synthetic monthly aggregate reports |
| `tasks.json` | Prompts and deterministic tool plans |
| `expected_answers.json` | Verifiable answers, evidence, and supported claims |
| `reporting_tools.py` | Five auditable reporting tools |
| `agent.py` | Lightweight deterministic reference agent |
| `evaluator.py` | Objective six-point scoring rubric |
| `demo.py` | CLI for reference or external predictions |
| `test_offline.py` | Offline regression and mutation tests |

## Run offline

The demo uses only Python's standard library and needs no API key:

```bash
cd chapter6/public-health-reporting-eval
python demo.py
```

Expected summary:

```text
positivity-alpha-jan           6/6
completeness-district-jan      6/6
trend-alpha-jan-feb            6/6
quality-demo-feb               6/6
stockout-demo-feb              6/6
------------------------------------
TOTAL                          30/30
```

Run the offline tests:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

## Evaluate another agent

Save its structured predictions as a JSON array with the same shape produced by the reference agent, then run:

```bash
python demo.py --predictions my_predictions.json --output evaluation.json
```

This boundary keeps model/framework integration outside the benchmark. Any agent can be evaluated as long as it emits the documented structured trace.

## Interpretation and limitations

- The benchmark measures correctness on a deliberately small, controlled environment; it does not establish real-world readiness.
- Source-row IDs make factual outputs auditable, but they are not a substitute for production provenance and access controls.
- Exact tool and argument scoring is intentionally strict. Alternative valid plans would need additional accepted traces.
- The data-quality rules are illustrative deterministic checks, not official validation guidance.
- Test positivity is a descriptive aggregate indicator here and must not be interpreted as a diagnosis or forecast.

---

## 中文

这是一个面向《深入理解 AI Agent》第6章的小型可复现实践：在**合成 DHIS2 风格的疟疾上报聚合数据**上做 Agent 评测。

### 评测内容

包含 5 个确定性任务：
1. 阳性检出率
2. 报告完整性
3. 月度趋势比较
4. 聚合质量检查
5. 药品断货复核

每条预测输出为一段 JSON 结构，包含所选工具、参数、返回结果、证据行 ID、claim。评分为 6 分制：
- 工具选择（1）
- 参数匹配（1）
- 答案正确性（2）
- 证据可追溯（1）
- grounding/safety（1）

### 文件说明

同上英文表。

### 直接离线运行

```bash
cd chapter6/public-health-reporting-eval
python demo.py
```

### 运行测试

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

### 评测外部 Agent

把外部模型或 agent 的预测导出为同样结构的 JSON，再运行：

```bash
python demo.py --predictions my_predictions.json --output evaluation.json
```

### 使用边界与局限

- 评测面向受控合成环境，不代表真实系统可上线。
- source-row 证据便于审计，但不替代生产级数据血缘与权限体系。
- 工具和参数打分采用严格匹配。
- 质量规则是示例性规则，不可等同真实质量体系。
- 阳性率仅为聚合描述指标，不用于诊断或预测。
