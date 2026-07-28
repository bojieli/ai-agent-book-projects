"""
基于规则（正则）的离线日志脱敏引擎

与 agent.py 中依赖本地 LLM 的方案互补：本模块不需要任何模型或网络，
纯靠正则表达式 + 校验算法（Luhn、身份证校验码）识别日志 / 工具输出中的
敏感信息，速度快、结果确定，适合作为 Agent 日志落盘前的第一道防线。

覆盖的敏感信息类别（按匹配优先级从高到低）：
  - 私钥 / 证书（PEM 块）
  - JWT
  - 云厂商与第三方密钥（AWS AKIA、GitHub、Slack、Google、OpenAI 风格 sk-）
  - HTTP Authorization: Bearer / Basic 令牌
  - 配置中的口令 / 密钥赋值（password=..., token: ... 等）
  - 邮箱地址
  - 信用卡号（Luhn 校验）
  - IBAN 国际银行账号
  - 美国社会安全号（SSN）
  - 中国大陆身份证号（校验码验证）
  - 中国大陆手机号
  - IPv4 地址

每一类都会被替换为带类别标签的占位符（如 [REDACTED_API_KEY]），
既隐去了原值，又保留了“这里原本是什么”的可读性，方便排障。
"""

import re
from collections import Counter
from typing import Dict, List, Tuple


def _luhn_ok(number: str) -> bool:
    """Luhn 校验，用于降低信用卡号的误报率"""
    digits = [int(c) for c in number if c.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _cn_id_ok(value: str) -> bool:
    """中国大陆二代身份证号（18 位）校验码验证"""
    s = value.upper()
    if len(s) != 18 or not s[:17].isdigit():
        return False
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_codes = "10X98765432"
    total = sum(int(s[i]) * weights[i] for i in range(17))
    return check_codes[total % 11] == s[17]


# 每条规则：(类别, 占位符, 编译后的正则, 用于取值的分组号, 可选校验函数)
# 分组号为 0 表示整段命中都要脱敏；为 N 表示只脱敏第 N 个捕获组（保留键名等上下文）。
_RULES = [
    (
        "private_key", "[REDACTED_PRIVATE_KEY]",
        # Truncated PEM (BEGIN without END) must still redact through EOF.
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"
            r"[\s\S]*?(?:-----END (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----|(?=\Z))"
        ),
        0, None,
    ),
    (
        "jwt", "[REDACTED_JWT]",
        re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
        0, None,
    ),
    (
        # 连接串中的口令，如 postgres://user:PASSWORD@host:5432/db
        "url_credential", "[REDACTED_URL_CRED]",
        re.compile(r"://[^\s:/@]*:([^\s@]+)@"),
        1, None,
    ),
    (
        "aws_access_key", "[REDACTED_AWS_KEY]",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        0, None,
    ),
    (
        "github_token", "[REDACTED_GITHUB_TOKEN]",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,})\b"),
        0, None,
    ),
    (
        "slack_token", "[REDACTED_SLACK_TOKEN]",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
        0, None,
    ),
    (
        "google_api_key", "[REDACTED_GOOGLE_API_KEY]",
        re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
        0, None,
    ),
    (
        "api_key", "[REDACTED_API_KEY]",
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
        0, None,
    ),
    (
        "bearer_token", "[REDACTED_BEARER_TOKEN]",
        re.compile(r"(?i)\bBearer\s+([A-Za-z0-9._~+/=-]{10,})"),
        1, None,
    ),
    (
        "basic_auth", "[REDACTED_BASIC_AUTH]",
        # Require Authorization: so English "Basic knowledge …" is not redacted.
        re.compile(r"(?i)\bAuthorization\s*:\s*Basic\s+([A-Za-z0-9+/=]{4,})"),
        1, None,
    ),
    (
        "secret_assignment", "[REDACTED_SECRET]",
        re.compile(
            r"(?i)(?:password|passwd|pwd|secret|token|api[_-]?key|"
            r"access[_-]?key|auth|credential)[\"']?\s*[=:]\s*"
            r"(?:\"([^\"]{4,})\"|'([^']{4,})'|([^\s\"',}]{4,}))"
        ),
        (1, 2, 3), None,
    ),
    (
        "email", "[REDACTED_EMAIL]",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        0, None,
    ),
    (
        "credit_card", "[REDACTED_CREDIT_CARD]",
        re.compile(r"\b(?:\d[ -]?){13,19}\b"),
        0, _luhn_ok,
    ),
    (
        "iban", "[REDACTED_IBAN]",
        re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
        0, None,
    ),
    (
        "us_ssn", "[REDACTED_SSN]",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        0, None,
    ),
    (
        "cn_id_card", "[REDACTED_ID_CARD]",
        re.compile(r"\b\d{17}[\dXx]\b"),
        0, _cn_id_ok,
    ),
    (
        "cn_phone", "[REDACTED_PHONE]",
        re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
        0, None,
    ),
    (
        "ip_address", "[REDACTED_IP]",
        re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
        0, None,
    ),
]

# 人类可读的类别中文名，用于打印汇总
CATEGORY_LABELS = {
    "private_key": "私钥 / 证书",
    "jwt": "JWT 令牌",
    "url_credential": "连接串凭据",
    "aws_access_key": "AWS 访问密钥",
    "github_token": "GitHub 令牌",
    "slack_token": "Slack 令牌",
    "google_api_key": "Google API Key",
    "api_key": "API Key (sk-)",
    "bearer_token": "Bearer 令牌",
    "basic_auth": "Basic 认证",
    "secret_assignment": "口令 / 密钥赋值",
    "email": "邮箱地址",
    "credit_card": "信用卡号",
    "iban": "IBAN 银行账号",
    "us_ssn": "美国社保号(SSN)",
    "cn_id_card": "身份证号",
    "cn_phone": "手机号",
    "ip_address": "IP 地址",
}


def sanitize(text: str) -> Tuple[str, List[Dict]]:
    """
    对文本执行离线规则脱敏。

    Returns:
        - 脱敏后的文本
        - 命中列表，每项为 {category, value, placeholder, start, end}
    """
    candidates: List[Dict] = []
    for priority, (category, placeholder, pattern, group, validator) in enumerate(_RULES):
        groups = group if isinstance(group, tuple) else (group,)
        for m in pattern.finditer(text):
            start = end = -1
            for g in groups:
                start, end = m.span(g)
                if start >= 0:
                    break
            if start < 0:  # 该捕获组未参与本次匹配
                continue
            value = text[start:end]
            if validator and not validator(value):
                continue
            candidates.append({
                "category": category,
                "placeholder": placeholder,
                "value": value,
                "start": start,
                "end": end,
                "priority": priority,
            })

    # 处理重叠：优先级高（数字小）的规则胜出，避免同一段被重复/错误脱敏
    candidates.sort(key=lambda c: (c["priority"], c["start"]))
    accepted: List[Dict] = []
    for c in candidates:
        if any(not (c["end"] <= a["start"] or c["start"] >= a["end"]) for a in accepted):
            continue
        accepted.append(c)

    # 按位置顺序重建脱敏文本
    accepted.sort(key=lambda c: c["start"])
    parts: List[str] = []
    last = 0
    for c in accepted:
        parts.append(text[last:c["start"]])
        parts.append(c["placeholder"])
        last = c["end"]
    parts.append(text[last:])

    findings = [
        {k: c[k] for k in ("category", "value", "placeholder", "start", "end")}
        for c in accepted
    ]
    return "".join(parts), findings


def summarize(findings: List[Dict]) -> Counter:
    """统计各类别命中次数"""
    return Counter(f["category"] for f in findings)


def print_report(name: str, original: str, redacted: str, findings: List[Dict]) -> None:
    """打印单条样本的 before/after 与命中明细"""
    print(f"\n{'=' * 64}")
    print(f"样本: {name}  （命中 {len(findings)} 处敏感信息）")
    print("=" * 64)
    print("--- 脱敏前 (BEFORE) ---")
    print(original.rstrip())
    print("\n--- 脱敏后 (AFTER) ---")
    print(redacted.rstrip())
    if findings:
        print("\n--- 命中明细 ---")
        for f in findings:
            label = CATEGORY_LABELS.get(f["category"], f["category"])
            print(f"   [{label}] {f['value']}  ->  {f['placeholder']}")


if __name__ == "__main__":
    # 直接运行本模块时，对内置样本做一次快速演示
    from samples import SAMPLES

    total = Counter()
    for name, text in SAMPLES:
        redacted, findings = sanitize(text)
        print_report(name, text, redacted, findings)
        total.update(summarize(findings))

    print(f"\n{'=' * 64}")
    print("脱敏类别汇总")
    print("=" * 64)
    for category, count in total.most_common():
        label = CATEGORY_LABELS.get(category, category)
        print(f"   {label:<16} {count} 处")
    print(f"\n   合计脱敏 {sum(total.values())} 处敏感信息")
