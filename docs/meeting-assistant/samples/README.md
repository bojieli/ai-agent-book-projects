# Samples（Phase 0 可执行样例）

> 契约真相源。运行时代码在仓库根 **`jiyaojun/`**（不修改 `jiyaojun-preview/`）。

| 路径 | 说明 |
|------|------|
| [playbooks/default.yaml](./playbooks/default.yaml) | 平台 Default Playbook |
| [schemas/artifact_envelope.json](./schemas/artifact_envelope.json) | Artifact 公共信封 JSON Schema |
| [render/default/](./render/default/) | 默认邮件模板与图表绑定 |
| [skills/eng/R1_req_sync/](./skills/eng/R1_req_sync/) | L2/playbook｜需求同步 |
| [skills/eng/R4_release_review/](./skills/eng/R4_release_review/) | L3/sop｜发布评审 |
| [skills/eng/R5_delivery_sync/](./skills/eng/R5_delivery_sync/) | L2/playbook｜交付周会 |
| [skills/business/B4_business_review/](./skills/business/B4_business_review/) | L2/playbook｜经营复盘 |
| [skills/business/B5_limit_pricing/](./skills/business/B5_limit_pricing/) | L3/sop｜额度定价 |
| [skills/hr/H2_perf_calibration/](./skills/hr/H2_perf_calibration/) | L2/playbook｜绩效校准 critical |
| [skills/hr/H5_org_change/](./skills/hr/H5_org_change/) | L2/playbook｜减员分析 critical |
| [skills/risk/K1_policy_review/](./skills/risk/K1_policy_review/) | L3/sop｜策略评审 |
| [skills/risk/K5_model_monitor/](./skills/risk/K5_model_monitor/) | L3/sop｜模型监控 |
| [skills/compliance/C2_remediation/](./skills/compliance/C2_remediation/) | L3/sop｜整改推进 |
| [skills/cross/X1_gray_ambiguity/](./skills/cross/X1_gray_ambiguity/) | L2/playbook｜灰度消歧 |
| [skills/platform/general/](./skills/platform/general/) | L0/playbook｜未知降级 |
| `skills/**` 其余 `backlog: true` 包 | 06 §3 后续故事 **Stub**（draft/playbook，无假 SOP） |

> 外部系统模拟：`jiyaojun/app` 内 Mock ASR / Hybrid 向量 / Jira / 企微 / LLM Evaluator。

契约文档：

- [06_优先故事成熟度表](../06_优先故事成熟度表.md)
- [07_Artifact公共信封](../07_Artifact公共信封.md)
- [08_Domain_Event目录](../08_Domain_Event目录.md)
- [DECISIONS](../DECISIONS.md) · [WORKLOG](../WORKLOG.md)
