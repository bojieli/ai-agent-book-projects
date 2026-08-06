# 最终证据报告模板（M6）

> 在新环境跑完一键演示后填写，用于求职/二次接入展示。勿粘贴真实凭据。

## 环境

| 项 | 值 |
|----|-----|
| 日期 | |
| 机器 | |
| Docker | |
| 分支 / commit | |

## 门禁结果

| 门禁 | 命令 | 结果 |
|------|------|------|
| Core 健康 | `python3 scripts/verify_local_stack.py` | ☐ ok |
| R1 演示 | `python -m app.demo.r1_flagship_loop` | ☐ ok |
| 故障矩阵 | `python -m app.eval.fault_matrix` | ☐ 7/7 |
| M6 质量 | `python -m app.eval.m6_quality_gates` | ☐ ok |
| 纪要君 run_all | `python -m app.eval.run_all` | ☐ ok |
| 安全 run_all | `python -m app.eval.run_all` | ☐ ok |

## 规模指标（摘自 m6_quality_report.json）

| 指标 | 最低要求 | 实测 |
|------|----------|------|
| RAG 黄金集 | ≥60 | |
| Agent 故事 | ≥30 | |
| ACL/密封/跨域负例 | ≥20 | |
| 安全规则 P99 | ≤80ms | |
| RAG P95 | ≤500ms | |
| 流水线 P95 | ≤120s | |

## 故障矩阵摘要

| 场景 | 终态 | 通过 |
|------|------|------|
| model_timeout | | ☐ |
| qdrant_pause | | ☐ |
| worker_restart | | ☐ |
| duplicate_webhook | | ☐ |
| postgres_unavailable | | ☐ |
| safety_block | | ☐ |
| budget_exhausted | | ☐ |

## 边界声明

- 本仓库为**生产架构脱敏重建**，不宣称企业生产就绪。
- 默认离线不依赖商业模型额度。
- shim / mock / OfflineSafetyGateway 结果不得表述为生产零事故。
