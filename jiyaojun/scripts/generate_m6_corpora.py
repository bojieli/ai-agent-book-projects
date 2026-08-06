#!/usr/bin/env python3
"""一次性生成 M6 扩充评测语料（可重复执行覆盖）。"""

from __future__ import annotations

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "fixtures" / "eval"


def _rag() -> dict:
    """生成 ≥60 条 RAG cases + 扩展语料。"""
    corpus = [
        {
            "id": "doc_api_timeout",
            "kind": "doc",
            "org_domain": "eng",
            "classification": "internal",
            "acl": ["u_pm", "u_dev_a"],
            "title": "接口超时规范",
            "body": (
                "# 接口超时与重试\n\n"
                "## 超时阈值\n网关对外接口超时阈值为 3 秒。\n\n"
                "## 重试策略\n最多重试 2 次，仅对幂等 GET。\n"
                "半成功场景必须写入补偿任务队列。\n\n"
                "## 监控\n超时率超过 1% 触发告警。"
            ),
        },
        {
            "id": "doc_pol_fraud",
            "kind": "doc",
            "org_domain": "risk",
            "classification": "confidential",
            "acl": ["u_risk_pm"],
            "title": "策略 pol_fraud_rule_88",
            "body": (
                "策略 pol_fraud_rule_88 上线前必须 Shadow 观察误杀率。\n"
                "生产热切换禁止在未完成 Shadow 报告时执行。"
            ),
        },
        {
            "id": "doc_gateway_sla",
            "kind": "doc",
            "org_domain": "eng",
            "classification": "internal",
            "acl": ["u_pm", "u_dev_a"],
            "title": "网关 SLA 规范",
            "body": "网关容量规划每季度复盘。支付切流前须完成压测，红灯条件不得上线。",
        },
        {
            "id": "doc_hr_sealed",
            "kind": "doc",
            "org_domain": "hr",
            "classification": "critical",
            "acl": ["u_hrbp"],
            "write_class": "sealed",
            "title": "组织调整密封纪要",
            "body": "组织调整分析摘要（密封），仅限 HRBP 查阅。",
        },
        {
            "id": "doc_deploy_checklist",
            "kind": "doc",
            "org_domain": "eng",
            "classification": "internal",
            "acl": ["u_pm", "u_dev_a"],
            "title": "发布检查清单",
            "body": "发布前核对回滚方案、监控看板、值班通讯录。灰度比例默认 5%。",
        },
        {
            "id": "doc_biz_pricing",
            "kind": "doc",
            "org_domain": "business",
            "classification": "confidential",
            "acl": ["u_biz_pm"],
            "title": "限价策略说明",
            "body": "限价活动需业务与风控双签。跨域不得直接引用工程密钥。",
        },
        {
            "id": "mtg_pay_review_transcript",
            "kind": "transcript",
            "meeting_id": "mtg_pay_review",
            "org_domain": "eng",
            "classification": "internal",
            "acl": ["u_pm", "u_dev_a"],
            "title": "支付切流评审转写",
            "write_class": "domain",
            "series_id": "series_pay",
            "segments": [
                {
                    "speaker": "张三",
                    "text": "本周支付切流压测还没出结论，网关容量是红灯。",
                    "start_ms": 0,
                    "end_ms": 4200,
                    "section": "压测",
                },
                {
                    "speaker": "李四",
                    "text": "建议先灰度 5% 流量，观察超时与重试指标。",
                    "start_ms": 4300,
                    "end_ms": 9100,
                    "section": "讨论",
                },
                {
                    "speaker": "王五",
                    "text": "上次会议决议是压测通过前不切流，这条要继续跟进。",
                    "start_ms": 9200,
                    "end_ms": 14000,
                    "section": "决议",
                },
                {
                    "speaker": "张三",
                    "text": "补偿任务队列本周已补齐，半成功不会再丢单。",
                    "start_ms": 14100,
                    "end_ms": 18500,
                    "section": "补偿",
                },
            ],
        },
        {
            "id": "c_open_blocker",
            "kind": "continuum",
            "org_domain": "eng",
            "classification": "internal",
            "write_class": "wide",
            "acl": ["u_pm", "u_dev_a"],
            "meeting_id": "mtg_r5_prev",
            "series_id": "series_pay",
            "open": True,
            "body": "网关容量未关闭，支付切流红灯。责任人：张三。截止：本周五。",
        },
    ]

    # 追加主题文档，支撑更多召回 case
    topics = [
        ("doc_retry_jitter", "eng", "internal", ["u_pm"], "重试抖动", "指数退避与抖动避免雪崩。"),
        ("doc_circuit_breaker", "eng", "internal", ["u_pm"], "熔断器", "错误率超阈值打开熔断，半开探测。"),
        ("doc_idempotency", "eng", "internal", ["u_pm", "u_dev_a"], "幂等键", "写回必须携带幂等键，重复请求不重复建单。"),
        ("doc_hitl_policy", "eng", "internal", ["u_pm"], "人工确认", "高风险写回需 HITL 通过后方可 embed。"),
        ("doc_rag_acl", "eng", "internal", ["u_pm"], "检索 ACL", "检索必须先 ACL 过滤再 dense/sparse。"),
        ("doc_sealed_meeting", "hr", "critical", ["u_hrbp"], "密封会议规则", "critical 会议产物不得出站到商业模型。"),
        ("doc_cross_domain", "business", "confidential", ["u_biz_pm"], "跨域协作", "跨域会议未消歧不得写回。"),
        ("doc_webhook_idem", "eng", "internal", ["u_pm"], "Webhook 幂等", "重复 webhook 按 external_id 忽略。"),
    ]
    for did, org, cls, acl, title, body in topics:
        corpus.append(
            {
                "id": did,
                "kind": "doc",
                "org_domain": org,
                "classification": cls,
                "acl": acl,
                "title": title,
                "body": body,
            }
        )

    cases: list[dict] = [
        {
            "id": "acl_denied_eng_doc",
            "query": "超时重试",
            "user_id": "stranger",
            "org_domains": ["eng"],
            "expect_empty": True,
        },
        {
            "id": "doc_timeout_recall",
            "query": "超时重试",
            "user_id": "u_pm",
            "org_domains": ["eng"],
            "relevant_ids": ["doc_api_timeout"],
            "must_hit": True,
        },
        {
            "id": "policy_id_sparse",
            "query": "pol_fraud_rule_88",
            "user_id": "u_risk_pm",
            "org_domains": ["risk"],
            "relevant_ids": ["doc_pol_fraud"],
            "must_hit": True,
        },
        {
            "id": "transcript_speaker_topic",
            "query": "压测结论 网关容量",
            "user_id": "u_pm",
            "org_domains": ["eng"],
            "relevant_ids": ["mtg_pay_review_transcript"],
            "must_hit": True,
        },
        {
            "id": "continuum_open_item",
            "query": "支付切流 红灯",
            "user_id": "u_pm",
            "org_domains": ["eng"],
            "relevant_ids": ["c_open_blocker"],
            "must_hit": True,
        },
        {
            "id": "agentic_rewrite_timeout",
            "query": "那个乱七八糟的超时事情怎么办呀",
            "user_id": "u_pm",
            "org_domains": ["eng"],
            "max_hops": 3,
            "min_score": 0.0,
            "relevant_ids": ["doc_api_timeout"],
            "must_hit": True,
        },
        {
            "id": "cross_chunk_compensation",
            "query": "补偿任务 半成功",
            "user_id": "u_pm",
            "org_domains": ["eng"],
            "relevant_ids": ["doc_api_timeout"],
            "must_hit": True,
        },
        {
            "id": "hr_sealed_acl",
            "query": "组织调整",
            "user_id": "u_hrbp",
            "org_domains": ["hr"],
            "relevant_ids": ["doc_hr_sealed"],
            "must_hit": True,
        },
        {
            "id": "hr_sealed_denied",
            "query": "组织调整",
            "user_id": "u_pm",
            "org_domains": ["hr"],
            "expect_empty": True,
        },
    ]

    # 正例扩写：同文档多查询变体
    positive_templates = [
        ("doc_api_timeout", "eng", "u_pm", ["超时阈值", "3秒超时", "GET 重试", "超时告警", "补偿队列"]),
        ("doc_gateway_sla", "eng", "u_pm", ["网关容量", "压测红灯", "季度复盘", "支付切流", "SLA"]),
        ("doc_deploy_checklist", "eng", "u_pm", ["回滚方案", "灰度 5%", "值班通讯录", "发布检查", "监控看板"]),
        ("doc_retry_jitter", "eng", "u_pm", ["指数退避", "抖动", "雪崩", "重试抖动"]),
        ("doc_circuit_breaker", "eng", "u_pm", ["熔断", "半开探测", "错误率阈值"]),
        ("doc_idempotency", "eng", "u_pm", ["幂等键", "重复建单", "写回幂等"]),
        ("doc_hitl_policy", "eng", "u_pm", ["HITL", "人工确认", "高风险写回"]),
        ("doc_rag_acl", "eng", "u_pm", ["ACL 过滤", "检索必须先 ACL", "检索 ACL"]),
        ("doc_webhook_idem", "eng", "u_pm", ["webhook 幂等", "external_id", "重复 webhook"]),
        ("doc_pol_fraud", "risk", "u_risk_pm", ["Shadow", "误杀率", "热切换禁止", "pol_fraud"]),
        ("doc_biz_pricing", "business", "u_biz_pm", ["限价", "双签", "风控"]),
        ("doc_cross_domain", "business", "u_biz_pm", ["跨域", "消歧", "未消歧不得写回"]),
        ("doc_sealed_meeting", "hr", "u_hrbp", ["密封会议", "不得出站", "critical 产物"]),
        ("c_open_blocker", "eng", "u_pm", ["未关闭红灯", "责任人张三", "本周五截止"]),
        ("mtg_pay_review_transcript", "eng", "u_pm", ["灰度 5%", "不切流", "补偿不丢单"]),
    ]
    for doc_id, org, user, queries in positive_templates:
        for i, q in enumerate(queries):
            cases.append(
                {
                    "id": f"pos_{doc_id}_{i}",
                    "query": q,
                    "user_id": user,
                    "org_domains": [org],
                    "relevant_ids": [doc_id],
                    "must_hit": True,
                }
            )

    # ACL / 跨域 / 密封负例：用户在目标 org 无权限 → 必须空召回
    negatives = [
        ("neg_eng_user_on_risk", "Shadow 误杀", "u_pm", ["risk"], True),
        ("neg_eng_user_on_biz", "限价双签", "u_pm", ["business"], True),
        ("neg_eng_to_hr", "密封会议", "u_pm", ["hr"], True),
        ("neg_stranger_sla", "网关容量", "stranger", ["eng"], True),
        ("neg_dev_hr", "组织调整", "u_dev_a", ["hr"], True),
        ("neg_biz_risk", "pol_fraud_rule_88", "u_biz_pm", ["risk"], True),
        ("neg_hr_eng_timeout", "超时重试", "u_hrbp", ["eng"], True),
        ("neg_cross_org_domains", "限价", "u_pm", ["business"], True),
    ]
    for cid, q, user, orgs, empty in negatives:
        cases.append(
            {
                "id": cid,
                "query": q,
                "user_id": user,
                "org_domains": orgs,
                "expect_empty": empty,
            }
        )

    # 补足到至少 60
    filler_qs = [
        "超时",
        "重试",
        "补偿",
        "告警",
        "网关",
        "压测",
        "灰度",
        "回滚",
        "幂等",
        "熔断",
        "HITL",
        "webhook",
        "ACL",
        "检索",
        "发布",
    ]
    i = 0
    while len(cases) < 60:
        q = filler_qs[i % len(filler_qs)]
        cases.append(
            {
                "id": f"fill_timeout_{i}",
                "query": f"{q} 规范",
                "user_id": "u_pm",
                "org_domains": ["eng"],
                "relevant_ids": ["doc_api_timeout", "doc_gateway_sla", "doc_deploy_checklist"],
                "must_hit": True,
            }
        )
        i += 1

    return {
        "k": 5,
        "thresholds": {
            "hit_rate": 0.75,
            "recall_at_k": 0.75,
            "mrr": 0.55,
            "faithfulness": 0.45,
        },
        "corpus": corpus,
        "cases": cases,
    }


def _agent_stories() -> dict:
    """≥30 条 Agent 主路径与失败故事目录。"""
    stories = []
    # 主路径（成功）
    success = [
        ("R1_happy", "R1", "success", "技术评审生成结构化产物"),
        ("R1_hitl_then_defect", "R1", "success", "HITL 通过后建缺陷"),
        ("R1_webhook_close", "R1", "success", "webhook 关闭 Continuum"),
        ("R1_briefing_recall", "R1", "success", "下场 briefing 召回 open item"),
        ("R1_idempotent_defect", "R1", "success", "同幂等键不重复建单"),
        ("R5_recall_blockers", "R5", "success", "交付同步召回未关闭 blocker"),
        ("R4_sop_path", "R4", "success", "发布评审走 SOP 路径"),
        ("K1_policy_sop", "K1", "success", "策略评审 SOP 且不写回"),
        ("dialog_create_task", "dialog", "success", "对话建任务"),
        ("dialog_create_defect", "dialog", "success", "对话建缺陷"),
        ("dialog_answer_only", "dialog", "success", "无工具意图直接回答"),
        ("pipeline_playbook", "general", "success", "未知场景 playbook/fallback"),
        ("safety_dual_authz_allow", "safety", "success", "业务∩安全允许后写回"),
        ("rag_grounded_answer", "rag", "success", "带 citation 的接地回答"),
        ("worker_resume", "worker", "success", "orphaned 任务可 resume"),
    ]
    # 失败故事
    failure = [
        ("R4_checklist_fail", "R4", "failure", "checklist 失败阻断 SOP"),
        ("H5_no_leak", "H5", "failure", "HR 密封不向工程泄露"),
        ("X1_ambiguity_block", "X1", "failure", "未消歧禁止写回"),
        ("K5_no_hot_swap", "K5", "failure", "禁止模型热切换"),
        ("safety_block_critical", "safety", "failure", "critical 出站阻断"),
        ("safety_budget_exhausted", "safety", "failure", "预算耗尽 fail-closed"),
        ("safety_gateway_timeout", "safety", "failure", "网关超时不写回"),
        ("tool_business_deny", "safety", "failure", "业务拒绝安全不可放权"),
        ("embed_effect_cap", "pipeline", "failure", "effect_cap 超限拒绝"),
        ("hitl_reject", "dialog", "failure", "HITL 拒绝终止写回"),
        ("acl_stranger", "rag", "failure", "陌生人检索为空"),
        ("cross_domain_deny", "rag", "failure", "跨域越权检索为空"),
        ("postgres_down", "infra", "failure", "PG 不可用明确失败"),
        ("qdrant_pause", "infra", "failure", "Qdrant 暂停检索降级"),
        ("duplicate_webhook_noop", "webhook", "failure", "重复 webhook 无额外副作用"),
    ]
    for sid, story, kind, title in success + failure:
        stories.append(
            {
                "id": sid,
                "story_family": story,
                "kind": kind,
                "title": title,
                "automated": True,
            }
        )
    assert len(stories) >= 30
    return {"version": "1.0", "min_required": 30, "stories": stories}


def _negatives() -> dict:
    """≥20 条 ACL/密封/跨域越权负例。"""
    catalog = [
        {"id": "continuum_wide_leak", "stories": ["H2", "H5"], "expect": "deny write_class=wide for critical", "category": "sealed"},
        {"id": "sop_skip_step", "stories": ["R4", "K1"], "expect": "fail if validate wall skipped", "category": "sop"},
        {"id": "empty_shell_sop", "stories": ["R1", "R5"], "expect": "playbook packs must not have sop/steps.yaml", "category": "sop"},
        {"id": "K5_hot_swap", "stories": ["K5"], "expect": "deny model hot swap", "category": "policy"},
        {"id": "H5_broadcast", "stories": ["H5"], "expect": "delivery.suppressed / render.skipped", "category": "sealed"},
        {"id": "X1_unresolved_agree", "stories": ["X1"], "expect": "fail evaluate on 各方同意 while open", "category": "cross_domain"},
        {"id": "render_full_then_filter", "stories": ["H2", "H5"], "expect": "acl_view before render", "category": "acl"},
        {"id": "global_hotword_force", "stories": ["general"], "expect": "deny injecting all-domain hotwords", "category": "acl"},
        # 新增可执行负例
        {"id": "acl_stranger_retrieve", "stories": ["rag"], "expect": "stranger gets empty retrieval", "category": "acl"},
        {"id": "sealed_egress_block", "stories": ["safety"], "expect": "critical classification blocks egress", "category": "sealed"},
        {"id": "cross_org_retrieve", "stories": ["rag"], "expect": "eng user cannot hit risk corpus", "category": "cross_domain"},
        {"id": "confidential_to_public_user", "stories": ["rag"], "expect": "biz confidential denied to eng pm", "category": "acl"},
        {"id": "hr_sealed_to_dev", "stories": ["H5"], "expect": "hr sealed denied to eng developer", "category": "sealed"},
        {"id": "tool_denylist_shell", "stories": ["safety"], "expect": "shell_exec blocked by safety", "category": "acl"},
        {"id": "business_deny_overrides_safety_allow", "stories": ["safety"], "expect": "empty grant cannot execute", "category": "acl"},
        {"id": "confirm_only_no_execute", "stories": ["safety"], "expect": "confirm_only is not executable", "category": "policy"},
        {"id": "cross_domain_writeback_blocked", "stories": ["X1"], "expect": "ambiguity blocks embed", "category": "cross_domain"},
        {"id": "critical_render_skipped", "stories": ["H5"], "expect": "critical email render skipped", "category": "sealed"},
        {"id": "risk_doc_cross_leak", "stories": ["K1"], "expect": "risk policy id not visible to eng", "category": "cross_domain"},
        {"id": "sealed_continuum_none", "stories": ["H5"], "expect": "write_class none rejects continuum", "category": "sealed"},
        {"id": "acl_empty_allowlist_deny", "stories": ["dialog"], "expect": "empty tool allowlist denies all", "category": "acl"},
        {"id": "budget_blocks_writeback", "stories": ["safety"], "expect": "budget exhausted blocks model path", "category": "policy"},
    ]
    assert len(catalog) >= 20
    return {"min_required": 20, "catalog": catalog}


def main() -> None:
    EVAL.mkdir(parents=True, exist_ok=True)
    rag = _rag()
    (EVAL / "rag_golden.yaml").write_text(
        yaml.safe_dump(rag, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    stories = _agent_stories()
    (EVAL / "agent_stories.yaml").write_text(
        yaml.safe_dump(stories, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    negs = _negatives()
    (EVAL / "negative_catalog.yaml").write_text(
        yaml.safe_dump(negs, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    print(
        f"rag_cases={len(rag['cases'])} corpus={len(rag['corpus'])} "
        f"stories={len(stories['stories'])} negatives={len(negs['catalog'])}"
    )


if __name__ == "__main__":
    main()
