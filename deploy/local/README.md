# 本地 Core 环境

本目录提供两个项目共享的本地基础设施。Core 默认包含 PostgreSQL、Redis、SeaweedFS（S3-compatible）和 Qdrant；不会启动商业模型调用，也不包含真实企业凭据。

## 为什么不是 MinIO

MinIO 社区仓库已于 2026 年 4 月归档。本项目采用仍在维护、Apache 2.0、支持 ARM64 的 SeaweedFS，并只依赖标准 S3 契约，后续可替换为其他 S3-compatible 服务。

## 启动

1. 启动 Docker Desktop 或其他 Docker daemon。
2. 复制本地配置：

```bash
cp deploy/local/.env.example deploy/local/.env
```

3. 校验并启动：

```bash
docker compose \
  --env-file deploy/local/.env \
  -f deploy/local/docker-compose.yml \
  config

docker compose \
  --env-file deploy/local/.env \
  -f deploy/local/docker-compose.yml \
  up -d
```

4. 验证：

```bash
python3 scripts/verify_local_stack.py
```

验证脚本输出 JSON。Docker daemon 未运行、任一服务未启动或健康端点失败时，脚本返回非零退出码并标出具体服务。

## 本地端口

- PostgreSQL：`55432`
- Redis：`56379`
- SeaweedFS Master：`59333`
- SeaweedFS Filer：`58888`
- SeaweedFS S3：`58333`
- SeaweedFS Admin：`53646`
- Qdrant HTTP：`56333`
- Qdrant gRPC：`56334`

端口均可在 `.env` 中覆盖。

## 数据隔离

PostgreSQL 实例仅为本地节省资源而共享；`jiyaojun` 与 `safety` 使用两个数据库。Redis 分别使用 DB 1 和 DB 0。SeaweedFS bucket 与 Qdrant collection 由纪要君独立配置。

纪要君 Celery broker 使用 **Redis DB 2**（`JIYAOJUN_CELERY_BROKER_URL=redis://127.0.0.1:56379/2`），避免与安全平台 DB0、纪要君缓存 DB1 冲突。

## Celery Worker（可选）

Core 栈启动后，可在宿主机运行纪要君 Worker：

```bash
cd jiyaojun
export JIYAOJUN_SCHEDULER_BACKEND=celery
export JIYAOJUN_CELERY_BROKER_URL=redis://127.0.0.1:56379/2
export JIYAOJUN_REDIS_URL=redis://127.0.0.1:56379/1
celery -A app.scheduler.celery_app.celery_app worker -l info
```

或使用 Compose profile：

```bash
docker compose --profile worker -f deploy/local/docker-compose.yml up -d celery-worker
```

## 停止

```bash
docker compose \
  --env-file deploy/local/.env \
  -f deploy/local/docker-compose.yml \
  down
```

如需删除本地脱敏数据，再显式追加 `--volumes`。不要在日常停止命令中默认删除数据卷。

## 可选 Profile（M5）

默认 `up -d` **不**启动以下服务，保证 Core 轻量；需要时显式加 profile：

| Profile | 服务 | 端口（默认） | 用途 |
|---------|------|--------------|------|
| `identity` | Keycloak | `58080` | OIDC 演示身份源 |
| `secrets` | OpenBao（dev） | `58200` | 凭据外置演示 |
| `observability` | OTel Collector / Prometheus / Grafana / Tempo | `54318` / `59090` / `53000` / `53200` | Trace + 指标看板 |
| `worker` | Celery Worker | — | 纪要君长任务 |

```bash
docker compose --env-file deploy/local/.env \
  --profile identity --profile secrets --profile observability \
  -f deploy/local/docker-compose.yml up -d

# Grafana: http://127.0.0.1:53000 （匿名只读已开；admin/admin-dev-only）
# 离线故障矩阵（不依赖上述容器）：
cd jiyaojun && python -m app.eval.fault_matrix
```

配置样例见 `.env.example` 中 `JIYAOJUN_OTEL_ENDPOINT`、`PLATFORM_KEYCLOAK_PORT` 等。OpenBao root token 仅本地开发，禁止提交真实凭据。
