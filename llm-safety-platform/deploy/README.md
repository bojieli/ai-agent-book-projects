# 部署说明（金融行内私有化）

## docker compose（默认 mock 审核）

```bash
docker compose -f deploy/docker-compose.yml up --build -d
```

| 服务 | 端口 | 说明 |
|------|------|------|
| gateway | 8080 | FastAPI Safety Gateway + /console |
| moderation | 8091 | LLM-as-Judge `/v1/classify`（默认 `MODERATION_MOCK=1`） |
| postgres | 5432 | 策略/VK/审计/审批 |
| redis | 6379 | 限流 / 可选 session store |

## On-prem 配置档（私有 GPU / vLLM）

```bash
# 准备 deploy/.env.moderation 或导出：
#   MODERATION_UPSTREAM_URL=http://host.docker.internal:8000/v1
#   MODERATION_MODEL=qwen2.5-7b-instruct
# 无 GPU 时可：MODERATION_ONPREM_MOCK=1（规则模拟私有端点）

docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.onprem.yml --env-file deploy/.env.moderation up -d
```

Gateway：`SAFETY_SCANNER_MODE=remote` + `SAFETY_CLASSIFIER_URL=http://moderation:8091/v1/classify`。  
亦可把 `SAFETY_CLASSIFIER_URL` 直接指到行内私有 classify 服务。

## Helm

```bash
# 开发/shim
helm upgrade --install llm-safety ./deploy/helm/llm-safety-platform -n llm-safety --create-namespace

# 行内 on-prem（OIDC fail-closed + remote moderation + SIEM/KMS knobs）
helm upgrade --install llm-safety ./deploy/helm/llm-safety-platform \
  -f ./deploy/helm/llm-safety-platform/values.yaml \
  -f ./deploy/helm/llm-safety-platform/values-onprem.yaml \
  -n llm-safety --create-namespace
```

### 关键环境变量（生产）

| 变量 | 说明 |
|------|------|
| `SAFETY_OIDC_DISABLED=0` + `OIDC_REQUIRED=1` | JWT/JWKS 校验，失败拒绝对管理面 |
| `SAFETY_OIDC_JWKS_URL` / `SAFETY_OIDC_ISSUER` / `SAFETY_OIDC_AUDIENCE` | IdP |
| `SAFETY_KMS_PROVIDER` | `env\|file\|aws_kms_stub\|http_kms` |
| `SAFETY_SIEM_SINK` | `log\|http\|file` + `SAFETY_SIEM_WEBHOOK_URL` |
| `SAFETY_CLASSIFIER_URL` / `MODERATION_UPSTREAM_*` | 私有审核链路 |
| `SAFETY_DUAL_LLM=1` | Dual-LLM opt-in MVP |
| `REDTEAM_EXTERNAL=1` | 进程外 garak/agentic 真跑（需 study 克隆） |

## 业务 VK 冒烟

```bash
# gateway 已启动后
./scripts/smoke_business_vk.sh
```

创建 `t_bank_retail` / `wealth_assistant` VK → chat → audit → HITL。

## 外部红队

```bash
# CI 默认（无重依赖）
python -c "from app.redteam.external_runners import run_multiturn_shim; print(run_multiturn_shim()['passed'])"

# 真跑（需 ../llm-safety-study/<suite> 存在）
REDTEAM_EXTERNAL=1 REDTEAM_EXTERNAL_TIMEOUT=120 \
  python -c "from app.redteam.external_runners import spawn_external; print(spawn_external('garak'))"
```

## 上线清单

1. 轮换 `SAFETY_MASTER_KEY` / 切换 `SAFETY_KMS_PROVIDER=http_kms`  
2. `OIDC_REQUIRED=1` + 行内 JWKS  
3. `SAFETY_MODEL_UPSTREAM_*` + `MODERATION_UPSTREAM_*` 指私有端点  
4. `SAFETY_SIEM_SINK=http` + webhook  
5. `python -m app.eval.run_all`（shim）全绿；周度 `REDTEAM_EXTERNAL=1` Job  
6. critical 应用双人发布；wealth_assistant 高风险 fail-closed
