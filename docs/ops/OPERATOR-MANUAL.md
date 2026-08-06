# 操作手册（脱敏重建本地环境）

本文面向新环境独立完成：**启动 → 正常演示 → 故障演示 → 全量门禁**。

## 1. 前置

- Docker Desktop（或兼容 daemon）
- Python 3.11+
- 不需要商业模型 API Key（默认离线全绿）

## 2. 一键启动与演示

```bash
chmod +x scripts/demo_one_click.sh scripts/demo_faults.sh
./scripts/demo_one_click.sh
```

仅 Core 基础设施：

```bash
cp deploy/local/.env.example deploy/local/.env
docker compose --env-file deploy/local/.env -f deploy/local/docker-compose.yml up -d
python3 scripts/verify_local_stack.py
```

可选 profile（身份 / 密钥 / 观测）：

```bash
docker compose --env-file deploy/local/.env \
  --profile identity --profile secrets --profile observability \
  -f deploy/local/docker-compose.yml up -d
```

## 3. 正常演示（R1）

```bash
cd jiyaojun
python -m app.demo.r1_flagship_loop
```

期望：技术评审 → HITL → 建缺陷 → 企微 msgid → webhook 关闭 → 下场 briefing 不含已关闭项。

## 4. 故障演示

```bash
./scripts/demo_faults.sh
# 或
cd jiyaojun && python -m app.eval.fault_matrix
```

| 场景 | 终态 | 恢复要点 |
|------|------|----------|
| 模型/网关超时 | failed | 恢复上游或切 Offline；禁止写回 |
| Qdrant 暂停 | degraded | unpause 后重试检索 |
| Worker 重启 | orphaned | needs_resume；幂等键防重复 |
| 重复 webhook | succeeded | item_id 幂等忽略 |
| PG 不可用 | failed | 恢复健康检查；可用 memory 离线 |
| 安全阻断 | failed | 调整分级/人工；不得扩权 |
| 预算耗尽 | failed | 日切或管理员提配额 |

## 5. 全量门禁

```bash
cd jiyaojun && python -m app.eval.run_all
cd llm-safety-platform && python -m app.eval.run_all
cd jiyaojun && python -m app.eval.m6_quality_gates
```

## 6. 商业 Judge（opt-in）

```bash
# 每周抽样 100；发布前 300（需 SAFETY_CLASSIFIER_URL）
cd llm-safety-platform
SAFETY_JUDGE_SAMPLE_LIMIT=100 python -m app.eval.remote_judge_compare
SAFETY_JUDGE_SAMPLE_LIMIT=300 python -m app.eval.remote_judge_compare
```

无分类器 URL 时 **skip**，不假装通过。

## 7. kind + Helm（Compose 验收后）

见 [`KIND-HELM.md`](KIND-HELM.md)。

## 8. 证据报告

跑完后收集：

- `jiyaojun/fixtures/eval/m6_quality_report.json`
- `jiyaojun/fixtures/eval/story_gates_report.json`
- `fault_matrix` stdout JSON
- `scripts/verify_local_stack.py` JSON

模板见 [`EVIDENCE-REPORT.md`](EVIDENCE-REPORT.md)。
