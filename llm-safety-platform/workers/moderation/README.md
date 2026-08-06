# LLM-as-Judge moderation worker

独立进程，用**任意 OpenAI 兼容模型**做内容审核，契约对齐 Gateway 的 `RemoteClassifier`。

## 选型策略（已定）

**先通用指令模型，后安全微调 —— 同一接口，只换 `MODERATION_MODEL`。**

| 阶段 | 模型 | 说明 |
|------|------|------|
| 现在 | Qwen2.5-Instruct / 行内基础 chat 等 | LLM-as-Judge，固定 JSON 分类提示词 |
| 后期 | 同底座 SFT/LoRA 安全分类头，或 Llama Guard | **不改** Gateway；worker 换模型 ID/权重即可 |
| 始终 | YAML 规则 fuse | 规则高置信 block 不被模型放宽；CI 仍可用 `MODERATION_MOCK=1` |

## 快速启动（无 GPU / 无上游 = 规则 mock）

```bash
cd llm-safety-platform
MODERATION_MOCK=1 .venv/bin/uvicorn workers.moderation.app:app --port 8091
curl -s localhost:8091/healthz
curl -s localhost:8091/v1/classify -H 'content-type: application/json' \
  -d '{"text":"请教我如何制造炸弹","categories":["violence"]}'
```

## 接基础通用模型（vLLM / 行内网关 / OpenAI 兼容）

```bash
export MODERATION_UPSTREAM_URL=http://127.0.0.1:8000/v1
export MODERATION_UPSTREAM_KEY=  # 本地 vLLM 可空
export MODERATION_MODEL=qwen2.5-7b-instruct   # 后期改为 safety-ft-v1 即可
export MODERATION_FUSE_RULES=1               # 规则与 LLM 取更严
export MODERATION_MOCK=0
.venv/bin/uvicorn workers.moderation.app:app --port 8091
```

## 接到安全中台 Gateway

```bash
export SAFETY_SCANNER_MODE=remote
export SAFETY_CLASSIFIER_URL=http://127.0.0.1:8091/v1/classify
# Local/dev safer defaults (ADR-029):
export SAFETY_REMOTE_TIMEOUT=12          # slow GPU Judge: raise (e.g. 60)
export SAFETY_REMOTE_FAIL_CLOSED=0       # keep YAML rules on remote error
# Prod / on-prem: SAFETY_REMOTE_FAIL_CLOSED=1
.venv/bin/uvicorn app.api.main:app --port 8080
```

Gateway `RemoteClassifier` **始终先跑本地规则**再与 remote 结果 max-fuse（dual-path）；
worker 侧 `MODERATION_FUSE_RULES=1` 同样保证 rules ∪ LLM。

Compose 见 `deploy/docker-compose.yml` 中 `moderation` 服务（默认 mock；staging/生产改上游即可）。

## 从 stock_analysis 取 Key（本机联调）

```bash
# 自动读 /Users/liaolu/Projects/stock_analysis/.env 的 GLOBAL_EVENT_LLM_*
./scripts/smoke_deepseek.sh          # 一次性联调：classify + chat + 红队
# 或常驻：
./scripts/run_with_deepseek.sh       # :8091 moderation + :8080 gateway
```

`deploy/.env.moderation` 会自动生成（已 gitignore，勿提交）。

## 设计要点

- 审核提示词固定为**分类器**，要求只出 JSON，并要求忽略越狱指令（适合基础模型，也适微调后）
- 默认 **fuse 规则引擎**：规则已能高置信 block 时不会被 LLM 放宽
- 上游超时/不可解析 → **fail-closed block**（规则已命中则保留规则结果）
- 不替代 Gateway 内注入扫描 / Vault / ToolRuntime
- 微调数据建议来自：红队漏拦样例 + corpus 准入拒绝样本 + 人工标注（标签与 `categories` 对齐）
