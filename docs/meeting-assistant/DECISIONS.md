# 架构决策记录（ADR）

> 锁定契约决策。变更须新 ADR + 改 03/06/07/08，禁止 silently 改口径。

---

## ADR-001 · 绿场重建，preview 仅参考

- **状态**：Accepted  
- **背景**：`jiyaojun-preview` 双栈与「只写纪要」失败模式不符企业工作单元目标。  
- **决策**：全新 `app/` 树；preview 只借算法与反例。  
- **后果**：不迁 Flask 第二脑；Phase 0 从契约+mock 起。

---

## ADR-002 · orchestration_mode：sop vs playbook

- **状态**：Accepted（v7.4）  
- **背景**：强行每场景 invent SOP 导致空壳合规。  
- **决策**：有真实行内步骤 → `sop` + `steps.yaml` + validate Hooks；否则 `playbook` 走平台 Default Playbook。禁止捏造 SOP。  
- **后果**：L3 近生产须 sop；playbook 默认更严 HITL、禁生产自动生效。

---

## ADR-003 · 单一 embed_gate

- **状态**：Accepted（v7.5）  
- **决策**：仅 `allow | confirm_only | block`；场景 `default_embed_gate` + 运行时取 `max_strict`。废弃并行 `auto_embed_policy`（仅别名）。  
- **后果**：Policy / Envelope / 表字段统一。

---

## ADR-004 · production_effect_cap ≠ work_object.production_effect

- **状态**：Accepted  
- **决策**：cap 是本场允许上限（policy_binding）；实际写回等级在 work_object。  
- **后果**：K1/B5/K5 可 `draft_only` cap，仍禁止 production 工具 discover。

---

## ADR-005 · policy_binding 版本化

- **状态**：Accepted  
- **决策**：initial / ambiguity_changed / understanding_changed / pre_embed；禁止改写旧版。  
- **后果**：DDL 多行；meeting 指针指向当前版。

---

## ADR-006 · Continuum write_class 与索引写入解耦投递

- **状态**：Accepted（v7.7）  
- **决策**：`wide|domain|sealed|none`；critical 默认 sealed；索引写入决策独立于邮件投递。  
- **后果**：H2/H5 sealed + block + 禁群发负例。

---

## ADR-007 · Render 先 acl_view

- **状态**：Accepted（v7.6）  
- **决策**：Artifact → 物化 acl_view → 再 email/charts/HTML；critical 无 allowlist → skip render（不落长文）。  
- **后果**：先渲全量再过滤 = 缺陷；`render.skipped` 事件必记。

---

## ADR-008 · Phase 0 实现语言与目录边界

- **状态**：Accepted（本轮）  
- **背景**：文档未钉死语言；需可跑冒烟与 eval runner；**不得改动**仓库内原始 `jiyaojun-preview/`。  
- **决策**：绿场代码全部落在仓库根目录 **`jiyaojun/`**（内含 `app/` 树，对齐 03 §6）；契约真相仍在 `docs/meeting-assistant/samples/`；`jiyaojun/app/skills` 只读引用 samples（symlink）。DDL 用 PostgreSQL 方言，放 `jiyaojun/migrations/`。  
- **理由**：与 preview 物理隔离；03 §5 eval 已示意 `.py`；避免双栈。  
- **后果**：禁止向 `jiyaojun-preview/**` 提交功能改动；MCP 暴露后挂。

---

## ADR-009 · V1 Skill Pack 目录约定

- **状态**：Accepted  
- **决策**：`samples/skills/{org_domain}/{StoryId}_{slug}/`；sop 必有 `sop/steps.yaml`；playbook **不得**有假 `sop/`。platform `general` 放 `samples/skills/platform/general/`。  
- **后果**：CI 可扫 mode vs 目录一致性。

---

## ADR-011 · Embedding 默认选型 BGE-M3（Hybrid Dense+Sparse）

- **状态**：Accepted  
- **背景**：03 §2.4 / §2.19 要求 Knowledge Plane 为 RAG 主路径，且 Hybrid Dense+Sparse **必做**；需在「可私有化、中文金融、双通道」约束下钉死默认 embedding，并允许 CI shim。  
- **决策**：默认 embedding = **BGE-M3（BAAI/bge-m3）**；通过 `EmbeddingProvider` 同时产出 dense 向量与 sparse lexical weights。生产 `JIYAOJUN_EMBEDDING=bge-m3`；CI/无权重 = `bge-m3-shim`（同接口，禁止当生产模型宣传）。  
- **理由**：  
  1. 原生 dense+sparse，对齐 Hybrid 契约，避免假 Hybrid。  
  2. 中文与专名友好，适合制度文号/策略 ID/会议短 query。  
  3. 开源可私有化，会议与制度默认不出公有云。  
  4. 否决绑死 OpenAI embedding（出域+无内置 sparse）与「仅 dense 中文小模型」作为默认。  
- **后果**：RAG 管线只依赖 Provider 接口；换行内模型不改 Orchestrator；详见 [09_RAG与Embedding选型.md](./09_RAG与Embedding选型.md)。

---

## ADR-010 · Phase 0 冒烟路径钉死

- **状态**：Accepted  
- **决策**：完成定义跑：`eng × tech_review`（映射 R1 需求澄清 playbook）→ 理解 → Envelope → mock 缺陷/任务单 → work_link → acl_view → email_html，并写 trace/usage。  
- **备注**：R1 故事是需求澄清；冒烟用「任务/缺陷草稿」演示嵌入，与 R1 成功标准一致（行动项→任务）。
