"""Safe refusal templates — never echo blocked harmful/sensitive content."""

from __future__ import annotations

REFUSALS: dict[str, str] = {
    "content_sexual": "抱歉，该请求涉及不当性内容，系统已拦截，无法继续回答。",
    "content_violence": "抱歉，该请求涉及暴力或危险活动指导，系统已拦截，无法提供相关信息。",
    "content_political": "抱歉，该请求触及政策不允许讨论的敏感内容，系统已拦截。",
    "content_self_harm": "很关心你的处境。我无法提供自我伤害相关建议；如需帮助请联系当地紧急救助或心理援助热线。",
    "content_harassment": "抱歉，该请求涉及歧视或骚扰内容，系统已拦截。",
    "content_fraud": "抱歉，该请求涉及欺诈或违法牟利指导，系统已拦截。",
    "content_privacy": "抱歉，该请求涉及侵犯隐私的行为指导，系统已拦截。",
    "content_disinformation": "抱歉，该请求涉及蓄意虚假信息传播，系统已拦截。",
    "content_expert_advice": "抱歉，无法提供个性化医疗或具体投资建议，请咨询持牌专业人士。",
    "content_jailbreak": "检测到不安全的指令操纵尝试，请求已被拦截。",
    "ban_topic": "抱歉，该话题不在本业务助手的服务范围内，请换一个与业务相关的问题。",    "injection_heuristic": "检测到不安全的指令操纵尝试，请求已被拦截。",
    "secret_pattern": "检测到疑似密钥或凭据，请求已被拦截，请勿在对话中粘贴密钥。",
    "sensitive_in_output": "模型输出含敏感信息，已拦截展示；请调整提问或联系管理员。",
    "pii_redacted": "已对敏感个人信息做脱敏处理。",
    "token_limit": "输入过长，已被系统拒绝，请缩短后重试。",
    "system_prompt_exfil_attempt": "检测到试图套取系统提示的行为，请求已被拦截。",
    "system_prompt_echo": "输出疑似泄露系统提示，已拦截。",
    "system_prompt_hash_mismatch": "系统提示完整性校验失败，请求已被拦截。",
    "rag_indirect_injection": "检索内容含不安全指令，已拦截。",
    "rag_acl_mismatch": "检索内容租户不匹配，已拦截。",
    "ungrounded_advice": "回答缺乏可核验证据，按政策已拦截。",
    "grounding_overlap": "回答与知识库证据关联不足，已拦截。",
    "tool_result_unsafe": "工具返回内容未通过安全扫描，已拦截。",
    "model_digest_mismatch": "模型制品摘要与策略钉死版本不符，已拦截。",
    "default": "该请求因安全策略无法回答。如有业务问题，请换一种方式描述。",
}


def refusal_for_reasons(reasons: list[str]) -> str:
    if not reasons:
        return REFUSALS["default"]
    joined = ";".join(reasons)
    for key, msg in REFUSALS.items():
        if key == "default":
            continue
        if key in joined or any(key in r or r.startswith(key) for r in reasons):
            # ban_topic:xxx
            if key == "ban_topic" and any(r.startswith("ban_topic") for r in reasons):
                return msg
            if key in joined or any(r == key or r.startswith(key + ":") or r.startswith(key + "_") or key in r for r in reasons):
                return msg
    # category content_*
    for r in reasons:
        if r.startswith("content_"):
            return REFUSALS.get(r, REFUSALS["default"])
        if r.startswith("ban_topic"):
            return REFUSALS["ban_topic"]
    return REFUSALS["default"]
