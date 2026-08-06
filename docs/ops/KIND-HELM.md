# Compose 验收后的 kind + Helm 最小路径

前置：本地 Compose Core 已通过 `scripts/verify_local_stack.py`。

## 1. 创建 kind 集群

```bash
kind create cluster --name meeting-assistant
```

## 2. 安装安全平台 Helm（仓库已有 Chart）

```bash
helm upgrade --install llm-safety \
  llm-safety-platform/deploy/helm/llm-safety-platform \
  -f llm-safety-platform/deploy/helm/llm-safety-platform/values.yaml \
  --namespace meeting-assistant --create-namespace
```

私有化样例：

```bash
helm upgrade --install llm-safety \
  llm-safety-platform/deploy/helm/llm-safety-platform \
  -f llm-safety-platform/deploy/helm/llm-safety-platform/values-onprem.yaml \
  --namespace meeting-assistant
```

## 3. 验收

```bash
kubectl -n meeting-assistant get pods
kubectl -n meeting-assistant port-forward svc/llm-safety 8080:8080
curl -s http://127.0.0.1:8080/healthz
```

## 4. 清理

```bash
helm uninstall llm-safety -n meeting-assistant || true
kind delete cluster --name meeting-assistant
```

## 边界

- 纪要君当前以 Compose/进程内演示为主，未提供独立 Helm Chart。
- kind 路径用于验证安全平台打包与健康探针，不替代 Compose 脱敏回归。
- 不在 CI 默认跑 kind（需本机/容器特权）。
