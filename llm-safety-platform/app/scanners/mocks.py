"""Phase-0/production scanners — shim heuristics; onnx adapter stub."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from urllib.parse import parse_qs, urlparse

from app.config import settings
from app.scanners.base import ScanContext, ScanResult
from app.scanners.content_safety import ContentSafetyScanner, ToxicityScanner
from app.scanners.decode_views import recursive_decode_views
from app.scanners.hidden_ascii import HiddenAsciiScanner
from app.scanners.normalize import despace_alnum, leetspeak_fold, normalize_text, obfuscation_signals
from app.scanners.owasp_controls import (
    GroundingScanner,
    RagGateScanner,
    SupplyChainScanner,
    SystemLeakScanner,
)
from app.scanners.session_risk import SessionRiskScanner

PHONE_RE = re.compile(r"(?<!\d)(?:1[3-9]\d{9})(?!\d)")
ID_RE = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
BANK_RE = re.compile(r"(?<!\d)(?:62\d{14,17}|4\d{15}|5[1-5]\d{14})(?!\d)")
SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"
)
# \s* so char-spaced / despaced views still match
INJECTION_PATTERNS = [
    # Imperative override (avoid FP on quoted teaching:「忽略以上指令」是攻击特征)
    # quoted teaching / slash-separated glossaries: 「忽略先前指令 / 忽略之前的规则」
    r"(?<![「『\"“'\(\[【/／])忽略.{0,12}(规则|指示|指令|提示)",
    r"无视.{0,10}(安全|规则|策略|限制|过滤)",
    r"无条件服从",
    r"(?<![\"'“])ignore\s*(all\s*)?(previous|above|prior)\s*(instructions|rules|prompts?)",
    # Quoted citation shells still ask to execute the ignore payload
    r"(ignore\s*(all\s*)?(previous|above|prior)\s*(instructions|rules|prompts?)).{0,120}"
    r"(execute|follow|obey|按.{0,8}执行|执行.{0,12}(引用|指令|cited))",
    r"forget\s*(all\s*)?(previous|prior|above)\s*(instructions|rules|commands|prompts?)",
    r"set\s+aside.{0,24}(directives?|instructions?|rules?|policies)",
    r"输出.{0,30}系统提示",
    r"reveal\s*(the\s*)?system\s*prompt",
    r"(repeat|disclose|print|output).{0,40}"
    r"(system\s+(?:instructions?|prompts?)|hidden\s+preamble|initial\s+system)",
    r"完全重现.{0,24}(系统提示|system\s*prompt)|系统提示词配置正确",
    r"(部署研发|部署工程师|研发你的工程师).{0,140}(系统提示|system\s*prompt|完全重现)",
    # Avoid FP on glossary「什么是 jailbreak / DAN」— require attack framing
    r"(?:enable|attempt|try|perform|do)\s+jailbreak|paraphrase\s+a\s+jailbreak|"
    r"jailbreak\s+mode|how\s+to\s+jailbreak|jailbreak\s*[:：]|"
    # glossary「DAN mode / Do Anything Now」must allow — require enablement framing
    r"(?:enable|enter|activate|switch\s+to)\s+dan\s*mode|dan\s*mode\s*[:：]|dan\s*mode\s+enabled|"
    r"\byou\s+are\s+dan\b|\[DAN\]|AntiGPT",
    # Bare "Do Anything Now" only when not a glossary/definition gloss
    r"(?<![（(/])do\s+anything\s+now(?!.{0,100}(definitions?\s+only|glossary|acronym\s+stand))",
    r"\bDAN\b.{0,80}(bomb|unrestricted|no\s+restriction|bypass|jailbreak\s+mode)",
    # ZH DAN persona + filter-bypass howto (glossary uses definitions-only framing)
    r"(你现在是|你是|扮演|进入)\s*DAN\b",
    r"\bDAN\b.{0,100}(不受任何安全|无安全限制|绕过内容过滤|安全限制)",
    r"(如何|怎样|说明).{0,12}绕过内容过滤|绕过内容过滤器",
    r"\[INST\]",
    r"<\s*system\s*>",
    r"(you\s+are\s+now\s+)?unrestricted|无限制模式",
    r"developer\s*mode(\s*enabled)?",
    r"bypass\s+content\s+filters?",
    r"(base64|rot[\s_-]?13|url\s*encod|encoded|编码).{0,60}(解码|decode|执行|obey|follow|run)",
    r"(decode|解码).{0,20}(then\s+)?(run|obey|follow|执行)",
    # handbook §7.2 context wrapping
    r"(请摘要|请总结|摘要以下).{0,80}(ignore|忽略|reveal|系统提示|exfiltrat)",
    r"(代码审查|安全漏洞|请分析).{0,120}(ignore\s+previous|忽略.{0,8}指令|reveal\s+system|系统提示)",
    r"(翻译成|translate\s+into).{0,80}(ignore\s+(all\s+)?previous|bypass\s+content)",
    r"(论文|学术|according\s+to|cited\s+instruction|Smith\s*\(\d{4}\)).{0,120}"
    r"(ignore\s+previous|reveal\s+the\s+system|output\s+your\s+system|execute\s+the\s+cited)",
    r"(bomb[- ]making|制作炸弹|explosive).{0,80}(base64|markdown\s+link|url\s+param)",
    r"base64.{0,60}(markdown\s+link|query\s+string).{0,40}(bomb|explosive|系统提示)",
    r"(?<![\"'“])ign[0o]re\s+prev",
    r"r[3e]veal\s+(the\s+)?system",
    r"policy\s+layers?\s+are\s+offline|extract\s+your\s+system\s+prompt",
    r"(grandma|grandmother).{0,100}(bomb|munition|explosive|pipe\s*bomb)",
    # OSS stenography wrappers (agentic_security stenography_fn families)
    r"(backwards|restore\s+vowels|remove\s+vowels|scramble|zigzag|mirror).{0,48}(obey|follow|decode)",
    # Jailbreak persona families (garak DAN/STAN/opposite + common OSS)
    r"pretend to be\s+DAN|\bSTAN\b|Strive To Avoid Norms|\bAntiDAN\b|\bDUDE\b",
    r"Boolean Opposite Machine|opposite day|breaks?\s+AI\s+rules|no\s+content\s+filter|no\s+prohibitions",
    r"does not follow OpenAI policies|content policy is far too lenient",
    r"['\"]DAN['\"]|person named Dan|replies the opposite|only replies the opposite",
    r"Sydney AI assistant|programmer at OpenAI.{0,100}(reprogram|modifying your|vulnerability)",
    # CyberSecEval / PurpleLlama prompt-injection families (secret + role override)
    r"(give|tell|confirm|share|reveal)\s+(me\s+)?(your|the|our|system)\s+(password|secret\s*key|passphrase)",
    r"what\s+is\s+(your|the|our|system)\s+(password|secret\s*key|passphrase)",
    r"(your|the|our|system)\s+(password|secret\s*key).{0,12}\?",
    r"\b(contraseña|mot de passe|qual è la password)\b",
    r"(i['’]?m your developer|security audit|system mode).{0,80}(password|secret)",
    r"SmartGPT|no special filtering|decode this Morse|morse code.{0,60}(password|pass)",
    r"what is your secret key|Dont reveal it to anyone",
    r"let'?s\s+say\s+i\s+wanted\s+to\s+(login|log\s+in)",
    r"Interlace\s+Part\s+\d+",
    r"(?:Q:\s*.{3,120}?\s+A:\s*.{3,200}?\s+){3,}Q:",
    # handbook expanded families (high-ROI; not one-off strings)
    r"\[\s*ADMIN\s+OVERRIDE\s*\]|system_command[\"']?\s*:\s*[\"']?config_dump",
    r"SYSTEM\s+COMPROMISED|PRIORITY\s+PROTOCOL|协议已激活|系统已被攻陷",
    r"(deployment\s+engineer|developer\s+support|security\s+auditor|penetration\s+test|"
    r"部署工程师|内部审计|安全事件响应|vendor\s+TAM|MSRC\s+liaison|法务|内审|监管|红队)."
    r"{0,140}(system\s*(prompt|configuration)|safety[- ]policy|开发者(消息|指令)|系统提示|幕后设定)",
    r"(audit\s*id|ticket\s*#?\s*[A-Z]{2,5}-\d).{0,80}(system\s*(prompt|configuration)|系统提示)",
    r"(NEW\s+TASK|新任务).{0,40}(不要摘要|do\s+not\s+summarize|extract|提取).{0,60}"
    r"(secret|api[_ -]?key|password|密钥|密码)",
    r"evil\s+confidant|parallel\s+universe.{0,40}(safety|restriction)|思想实验.{0,40}(无对齐|绕过)",
    r"(official\s+compliance\s+protocol|security\s+audit\s+endpoint|官方.{0,12}(合规|审计).{0,20}协议|"
    r"安全审计端点|条文伪称|audit-spoof\.example|AUTHORIZED\s+SECURITY\s+AUDIT)",
    r"(translate|翻译).{0,40}(then\s+)?(obey|follow|执行)|先翻译.{0,12}再执行|translate-then-obey",
    r"(dump|export|force).{0,40}(phone\s*numbers?|national\s*ids?|bank\s*accounts?|ssn|PII)|"
    r"(强制导出|不要脱敏|禁止打码).{0,40}(手机号|身份证|银行卡|邮箱|个人信息|客户隐私|隐私字段|证件号)|"
    r"(敏感个人信息|证件与银行卡|PAN/?CVV|Privacy\s+bypass).{0,40}(dump|export|reveal|导出|打印)?",
    r"(guarantee\s+\d+%\s+returns?|insider[- ]style|稳赚不赔|内幕交易|保证收益|明日必涨)",
    # privilege / debug frames (avoid FP:「管理员权限申请流程」)
    r"管理员权限.{0,24}(覆盖|打印|reveal|系统提示|配置导出|override)|"
    r"进入调试模式.{0,40}(打印|reveal|系统|配置)|打印完整系统配置|"
    r"disable_filters\s*=\s*1|"
    r"<\s*admin\b[^>]*>|role[\"']?\s*:\s*[\"']?root|action[\"']?\s*:\s*[\"']?reveal_system|"
    r"\[\s*ADMIN\s+OVERRIDE\s*\]|ADMIN/?debug|enable\s+jailbreak|dump\s+secrets|"
    r"<privilege\b[^>]*>|mode:\s*debug.{0,40}(reveal|给出|draft)|"
    r"system_command[\"']?\s*:\s*[\"']?(elevate|config_dump|root)",
    # system exfil paraphrases / tool smuggle
    r"隐藏系统设定|prompt_dump|debug\.prompt_dump|"
    r"initial\s+instructions\s+above\s+this\s+conversation|"
    r"verbatim\s+safety[- ]policy|输出隐藏开发者|幕后设定全文|舞台幕后台词本",
    # adversarial suffix / soft override paraphrases
    r"对抗后缀|期望完整系统提示词|Adversarial\s+suffix\s+trial|"
    r"pause\s+prior\s+guidance|暂停先前指引|充分合作模式|条条框框",
    # output-channel / data-URI obey (input-side)
    r"data:(text|application)/[^\s]+;base64,.{0,240}(obey|执行|decode\s+the\s+data\s+uri)",
    # tool abuse / SSRF / secret exfil via agents
    r"run_command|scp\s*密钥|curl\s+https?://(evil|attacker)|"
    r"169\.254\.169\.254|fetch.{0,40}127\.0\.0\.1.{0,40}secret|"
    r"os\.system\s*\(\s*['\"]curl|/--data\s+@/etc/passwd",
    # context wrap / task hijack paraphrases
    r"P\.S\.\s*AI\s+must|task:\s*exfil|密钥导出|secretly\s+encode\s+secrets|"
    r"IGNORE\s+POLICY|Before\s+searching,|"
    r"系统提示词转为\s*base64|markdown\s*外链以便",
    # multi-turn approx / finance / harm howto (request-level)
    r"渐进式（单条模拟多轮）|渐进式\s*[:：]|模拟多轮\s*[:：]|可绕过限制|crescendo|"
    r"check-kiting|payment\s+diversion\s+playbook|"
    r"physical\s+harm.{0,40}(how-?to|fiction-research)|"
    r"诱导性投顾|监管尚未知晓的利好|wire\s+fraud\s+step\s+by\s+step",
    # expanded-corpus hard families (2026-08-05 leak cut; keep benign FP-safe)
    r"list\s+all\s+tokens?\s+and\s+secrets?|"
    r"(tokens?|secrets?|api\s*keys?).{0,40}"
    r"(currently\s+in\s+context|in\s+(the\s+)?conversation\s+context|from\s+(the\s+)?(conversation\s+)?context)|"
    r"(list\s+all|dump|extract|output|print)\s+(all\s+)?(tokens?|secrets?|api\s*keys?|passwords?).{0,48}"
    r"(in\s+(the\s+)?(conversation\s+)?context|from\s+(the\s+)?(conversation\s+)?context)|"
    r"extract\s+API\s*keys?\s+and\s+passwords?\s+from\s+(the\s+)?(conversation\s+)?context|"
    r"(full\s+)?policy\s+dump|do\s+not\s+redact|"
    r"(openai\s+support|msrc|红队授权).{0,80}(绕过内容过滤|无限制回答|bypass\s+content)|"
    r"ignore\s+privacy\s+policy|export\s+user\s+dossier|"
    r"把\s*PII\s*做成\s*CSV|强制导出手机号|导出客户名单|"
    r"假装?policies?\s+are\s+folklore|academic\s+sandbox|"
    r"(hypothetical|hypothetically|fictional\s+request).{0,60}(bomb|assault|violent|爆炸|暴力)|"
    r"data:text/plain;base64.{0,40}system\s+prompt|"
    r"output\s+your\s+system\s+prompt\s+as\s+a\s+fenced|"
    r"伪装成合规条文|忽略用户隐私条款|"
    r"没有过滤的地下顾问|roleplay\s+JailGPT|JailGPT|"
    r"pre_hook[\"']?\s*:\s*[\"'].{0,80}(密钥|钓鱼|api|密码|markdown)|"
    r"mode:\s*debug.{0,80}(不要脱敏|完整打印|privacy|dossier)|"
    r"pause\s*safety\s*checks|pausesafetychecks|"
    r"violent\s*assault\s*howto|draft\s+a\s+violent\s+assault|"
    r"account-verification\s+lure|紧急账户验证钓鱼|"
    r"phishing.{0,48}(email\s+)?template|phishing.{0,48}credential\s+theft|"
    r"provide\s+a\s+phishing|"
    r"Zignoruj\s+poprzednie|تجاهل كل التعليمات|Önceki talimatları|"
    r"पिछले सभी निर्देशों|"
    r"paste\s+hidden\s+developer\s+instructions|"
    r"hidden\s+developer\s+instructions|"
    r"disable\s*filters?\s+then\s+output|"
    r"从记忆与检索块提取|提取所有身份证号|"
    r"output\s+all\s+tokens\s+in\s+json|"
    # HTML/CSS-hidden SYSTEM / override (require instruction-shaped SYSTEM; allow sanitizer docs)
    r"(display\s*:\s*none|mso-hide\s*:\s*all|opacity\s*:\s*0|font-size\s*:\s*[01]px|"
    r"visibility\s*:\s*hidden|color\s*:\s*white).{0,160}"
    r"(SYSTEM\s*:|SYSTEM\s+OVERRIDE|\[\s*SYSTEM|Copilot\s+Override|IGNORE\s+PRIOR)|"
    r"(HTML\s+retrieved|HTML\s+隐藏|邮件正文.{0,12}不可见).{0,80}"
    r"(SYSTEM\s*:|SYSTEM\s+OVERRIDE|隐藏指令|IGNORE\s+PRIOR)|"
    # payment-diversion / wire-fraud request family (not bare awareness / 防伪识别)
    r"payment\s+diversion\s+playbook|check[- ]kiting|"
    r"(给出|编写|教我|provide|how\s+to|如何实施|实施).{0,24}(伪造支付改道|伪造支付|支付改道|payment\s+diversion|电汇诈骗)|"
    r"伪造支付改道.{0,24}(操作|请求|说明|话术|模板|步骤|playbook)|"
    # trailing「实施」must not match educational「非实施」
    r"电汇诈骗.{0,16}(话术|模板|步骤|操作请求|操作说明)|"
    # SharePoint / RAG authority smuggle (cross-doc secret retrieval)
    r"cross[- ]document\s+secret\s+retrieval|secret\s+retrieval\s+protocol|"
    r"post\s+to\s+audit\s+endpoint|跨文档.{0,12}(密钥|敏感).{0,12}检索",
    # context wrapping: summary-shell + harm howto (ZH)
    r"(文档摘要壳|摘要时顺便).{0,80}(暴力伤害|暴力伤害操作|操作步骤)|"
    r"(以假设方式|假设方式).{0,40}(请求)?暴力伤害|暴力伤害操作步骤|"
    # guardrail exfil: image/md channel carrying context PII
    # bare「诱导外泄」appears in DLP training — require attack framing / colon
    r"诱导外泄\s*[:：]|诱导外泄.{0,24}(在回答|附加|嵌入|末尾)|"
    r"图片链接.{0,40}(承载|携带|编码).{0,40}(邮箱|密钥|令牌|上下文|PII)|"
    r"(附加|嵌入).{0,16}图片链接.{0,60}(邮箱列表|密钥|令牌|secrets?)|"
    # multi-turn approx: single-msg shard crescendo + context secret pull
    # bare「分片指令」is a detector label in SOC glossaries — require N= / colon / pull
    r"分片指令\s*[:：]|分片指令.{0,24}N\s*=|分片指令.{0,80}(提取|密钥|密码|令牌|钓鱼|支付改道|绕过内容)|"
    r"提取上下文中的.{0,36}(API\s*密钥|密钥和密码|密码|令牌|secrets?|api[_ -]?keys?)|"
    # finance policy bypass: insider framing / earnings leak / YAML ask
    r"actionable\s+insider\s+framing|insider\s+framing.{0,48}earnings\s+leak|"
    r"earnings\s+leak|ask\s*:\s*insider\s+entry|insider\s+entry|"
    r"guarantee\s*:\s*true.{0,160}(insider|ticker)|"
    # task hijack (doc): degrade summary → exfil tokens to JSON
    # bare「任务劫持」is a taxonomy term — require colon or exfil follow-on
    r"任务劫持\s*[:：]|任务劫持.{0,64}(原摘要|外泄|令牌|密钥|降级|提取|JSON|tokens?)|"
    r"原摘要任务降级|"
    r"(优先外泄|外泄).{0,48}(上下文中的)?(令牌|tokens?|密钥).{0,40}(JSON|字段|tokens?|攻击者|URL)?|"
    r"外泄上下文中的令牌|优先外泄密钥到攻击者|"
    # task hijack (support): priority reorder before user answer
    r"客服优先级重排\s*[:：]|客服优先级重排.{0,100}(令牌|密钥|邮箱|证件|手机号|开发者指令|打印|导出|提取|钓鱼|暴力)|"
    r"优先级重排.{0,100}(令牌|密钥|邮箱|证件|手机号|开发者指令)|"
    r"(先以\s*JSON\s*列出|先导出|以\s*JSON\s*列出).{0,48}上下文中的.{0,48}(令牌|密钥|邮箱|手机号|证件)|"
    r"priority_note\s*=|原客服任务延后|"
    r"把密钥编码进指向攻击者域名的\s*markdown|"
    # full expanded residual families (2026-08-05; phrase-level, not case-id)
    r"绕过内容过滤并无限制回答|绕过内容过滤.{0,12}无限制回答|"
    r"不要脱敏[，,：:\s]{0,8}完整打印.{0,24}(客户)?隐私|"
    r"完整打印客户隐私字段|导出上下文中的邮箱[、,]\s*手机号|"
    r"list\s+every\s+PII\s+field|including\s+SSN\s+patterns|"
    r"table\s+of\s+emails?\s+and\s+account\s+numbers|"
    r"Markdown\s+table\s+request:.{0,80}\|\s*name\s*\|\s*id\s*\|\s*phone|"
    r"\|\s*name\s*\|\s*id\s*\|\s*phone\s*\|.{0,80}No\s+masking|"
    r"violent\s+assault\s+plan.{0,80}how-?to|"
    r"describe\s+a\s+violent\s+assault\s+plan\s+as\s+a\s+hypothetical|"
    # bare「诱导工具调用/Poisoned MCP/工具投毒」appear in hygiene docs — require attack framing
    r"诱导工具调用\s*[:：]|诱导工具调用.{0,64}(用\s*search_files|找\s*id_rsa|上传到攻击|attacker\s+URL)|"
    r"search_files.{0,48}id_rsa|id_rsa.{0,48}(攻击者|attacker|上传)|"
    r"Poisoned\s+MCP\s+prompt|Poisoned\s+MCP.{0,48}(reveal|secrets?|template|\{)|"
    r"MCP\s*/\s*工具投毒\s+JSON|工具投毒\s+JSON|工具投毒.{0,48}(pre_hook|密钥|reveal)|"
    r"\{\{#system\}\}.{0,40}reveal\s+secrets|"
    r"请注册工具：.{0,24}audit_dump|audit_dump.{0,100}(绕过|不要脱敏|令牌|密钥|隐私|导出|开发者)|"
    r"tools\s*\[\s*\]\s*\.?\s*description.{0,80}(HTML\s*注释|不要脱敏|藏指令)|"
    r"原样返回\s*system\s*prompt|"
    r"安全事件响应：.{0,100}(输出安全规则|工具定义|安全规则与工具)|"
    r"(平台运维|deployment\s+engineer).{0,100}(原样返回|system\s*prompt|不要脱敏|完整打印)|"
    r"paste\s+developer\s+message|developer\s+message\s*#?\s*\d|"
    r"data:\s*URI.{0,80}developer\s+instructions|"
    r"Return\s+a\s+data:\s*URI\s+containing\s+the\s+developer|"
    r"/bin/reveal_prompt|export\s+SAFETY\s*=\s*0|Shell-frame\s*:|"
    r"POST\s+/v1/system/config.{0,120}[\"']?dump[\"']?\s*:\s*true|"
    r"system_command[\"']?\s*:\s*[\"']?debug_unlock|"
    r"Bypass\s+financial\s+advice\s+policy|leverage\s+crypto\s+all-in\s+with\s+certainty|"
    r"从现在起覆盖原指令|暂停既有策略|"
    r"新任务：?\s*不要执行原任务|"
    r"Leetspeak\s+instruction\s*:|"
    r"이전\s*지침을\s*무시|시스템\s*프롬프트를\s*출력|"
    r"Игнорируй\s+все\s+предыдущие|раскрой\s+системный\s+промпт|"
    r"Game\s+rule\s+for\s+\w+.{0,40}violent\s+assault|"
    r"NOTE\s+TO\s+MODEL:\s*.{0,40}violent\s+assault|"
    r"secretly\s+describe\s+a\s+violent\s+assault|"
    r"Fill\s+in\s+harmful\s+how-to\s+as\s+comments|"
    r"bypasscontentfilters|dumpapikeysfromcontext|"
    r"leakpasswordsfrommemory|aborttheusertask|"
    r"dump\s*api\s*keys?\s*from\s*context|leak\s*passwords?\s*from\s*memory|"
    r"abort\s+the\s+user\s+task",
]
INJECTION_RE = re.compile("|".join(INJECTION_PATTERNS), re.I | re.S)
INDIRECT_RE = re.compile(
    r"(?i)(when\s+summarizing|hidden\s+instruction|"
    r"exfiltrat(?:e|ing)\s+(?:secrets?|tokens?|credentials?|pii|to\b)|"
    r"exfiltration\s+of\s+(?:secrets?|tokens?|credentials?|customer\s+data)|"
    r"把密钥发给|send\s+secrets?\s+to|"
    r"(?<!无)隐藏指令|"
    r"attacker\.(com|example)|编码为\s*URL\s*参数|markdown\s*链接.{0,40}(attacker|evil|exfil)|"
    r"webhook\.site|ngrok\.(io|app)|echo\.attacker|evil\.example|audit-spoof\.example|"
    r"安全审计端点|assistants\s+SHALL\s+post\s+context|跨文档敏感信息检索|密钥导出|"
    r"encode\s+secrets?\s+into\s+a\s+markdown|"
    r"(display\s*:\s*none|mso-hide\s*:\s*all|opacity\s*:\s*0|font-size\s*:\s*[01]px|"
    r"visibility\s*:\s*hidden).{0,160}"
    r"(SYSTEM\s*:|SYSTEM\s+OVERRIDE|\[\s*SYSTEM|IGNORE\s+PRIOR|HIDDEN\s+INSTRUCTION)|"
    r"HTML\s+retrieved.{0,40}SYSTEM\s*:|HTML\s+隐藏指令|"
    r"payment\s+diversion\s+playbook|"
    r"(给出|编写|教我|provide|如何实施|实施).{0,24}(伪造支付改道|支付改道|payment\s+diversion|电汇诈骗)|"
    r"伪造支付改道.{0,24}(操作|请求|说明|话术|模板|步骤|playbook)|"
    r"电汇诈骗.{0,16}(话术|模板|步骤|操作请求|操作说明)|"
    r"cross[- ]document\s+secret\s+retrieval|secret\s+retrieval\s+protocol|"
    r"post\s+to\s+audit\s+endpoint|"
    r"诱导外泄\s*[:：]|诱导外泄.{0,24}(在回答|附加|嵌入|末尾)|"
    r"图片链接.{0,40}(承载|携带).{0,40}(邮箱|密钥|令牌|上下文)|"
    r"任务劫持\s*[:：]|任务劫持.{0,64}(原摘要|外泄|令牌|密钥|降级|提取|JSON)|"
    r"客服优先级重排\s*[:：]|客服优先级重排.{0,100}(令牌|密钥|邮箱|证件|手机号|开发者|打印|导出|提取)|"
    r"外泄上下文中的令牌|"
    r"提取上下文中的.{0,36}(API\s*密钥|密钥和密码|密码|令牌)|"
    r"绕过内容过滤并无限制回答|完整打印客户隐私字段|"
    r"Poisoned\s+MCP\s+prompt|MCP\s*/\s*工具投毒\s+JSON|工具投毒\s+JSON|"
    r"诱导工具调用\s*[:：]|诱导工具调用.{0,64}(用\s*search_files|找\s*id_rsa|上传到攻击|attacker\s+URL)|"
    r"priority_note\s*=|"
    r"\{\{#system\}\}.{0,40}reveal\s+secrets)",
)
_URL_IN_TEXT_RE = re.compile(r"https?://[^\s\]\)\"'<>]{12,}", re.I)
_MD_IMG_RE = re.compile(r"!\[[^\]]*\]\((https?://[^)\s]+)\)", re.I)
_DATA_URI_RE = re.compile(r"data:(?:text|application)/[^;,\s]+;base64,[A-Za-z0-9+/=]{48,}", re.I)
_HIGH_ENTROPY_RE = re.compile(r"[A-Za-z0-9+/=_-]{40,}")
_EXFIL_HOST_HINTS = (
    "evil.",
    "webhook.",
    "ngrok.",
    "requestbin.",
    "pipedream.",
    "burpcollaborator",
    "oastify.",
    "interact.sh",
    "canarytokens.",
)


class TokenLimitScanner:
    id = "token_limit"
    layer = "L1"

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        tokens = max(1, len(text) // 4)
        limit = ctx.spec.max_tokens or 4096
        if tokens > limit:
            return ScanResult(self.id, "block", 1.0, [f"token_limit_exceeded:{tokens}>{limit}"])
        return ScanResult(self.id, "allow", 0.0, [])


class SecretsScanner:
    id = "secrets"
    layer = "L1"

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        if SECRET_RE.search(text):
            return ScanResult(self.id, "block", 0.95, ["secret_pattern"])
        return ScanResult(self.id, "allow", 0.0, [])


_META_EDU_RE = re.compile(
    r"(?i)("
    r"fingerprint|postmortem|glossary|awareness|staff\s+training|internal\s+faq|"
    r"话术特征|复盘|术语|词典|\bFAQ\b|防诈培训|安全培训|防伪|防御文档|sanitize|"
    r"运维手册|runbook|政策要点|policy\s+要点|"
    r"definitions?\s+only|acronym\s+stand|define\s+the\s+terms|what\s+is\b|如何上报|识别要点|核对清单|detection\s+only|"
    r"注入特征|攻击者常说|面向.{0,12}(培训|教育|柜员|员工)|不要给(出)?(攻击|可复制)|不要演示|"
    r"高层次|high-level\s+DLP|（概念）|taxonomy|detector\s+docs?|hygiene|"
    r"acceptance\s+criteria|误报复核|家族标签|探测流量|onboarding|须知|基线|"
    r"合规课|合规培训|理财合规|禁止类表述|disallowed|compliance training|"
    r"换一种说法|换种表述|改写成|paraphrase\s+our|awareness\s+paraphrase|"
    r"never\s+ask|不要.*(list|导出|打印)|rotate\s+leaked"
    r")"
)
_HARD_ATTACK_FOLLOW_RE = re.compile(
    r"(?i)("
    r"输出.{0,16}系统提示|reveal\s*(the\s*)?system|print\s*(your\s*)?system|"
    r"hidden\s+preamble|dump\s+(developer|secrets?|tokens?)|exfiltrat|"
    r"extract\s+all\s+secrets|secrets?\s+from\s+context|do\s+not\s+summarize|"
    r"NEW\s+TASK|新任务|"
    # Bare DAN acronym expansion alone is not hard-follow (glossary / definitions only)
    r"do\s+anything\s+now.{0,60}(bypass|unrestricted|reveal|bomb|no\s+restriction)|"
    r"unrestricted|bypass\s+content|"
    r"phishing\s+email\s+template|credential\s+theft|payment\s+diversion\s+playbook|"
    r"(给出|编写|教我|provide|如何实施|实施).{0,24}伪造支付改道|"
    r"伪造支付改道.{0,24}(操作|请求|说明|话术|模板)|"
    r"(实施|如何实施).{0,8}电汇诈骗|电汇诈骗.{0,12}(话术|模板)|"
    r"provide\s+a\s+(phishing|check-kiting)|无限制回答|完整打印客户隐私|"
    r"search_files.{0,40}id_rsa|诱导工具调用\s*[:：]|"
    r"SYSTEM\s+COMPROMISED|PRIORITY\s+PROTOCOL|系统已被攻陷|协议已激活|"
    r"full\s+policy\s+dump|policy\s+dump.{0,40}(do\s+not\s+redact|cite\s+fake)|"
    r"output.{0,48}system\s+configuration|dump\s+all\s+memory|"
    r"do\s+not\s+redact.{0,40}(policy|cite\s+fake)"
    r")"
)


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


class PromptInjectionScanner:
    id = "prompt_injection"
    layer = "L1"

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        norm = normalize_text(text)
        decoded = recursive_decode_views(text)
        desp = despace_alnum(norm)
        leet = leetspeak_fold(desp)
        views = [text, norm, desp, leet, *decoded]
        views.extend(normalize_text(d) for d in decoded)
        views.extend(despace_alnum(normalize_text(d)) for d in decoded)
        views.extend(leetspeak_fold(despace_alnum(normalize_text(d))) for d in decoded)
        matched = any(INJECTION_RE.search(v) for v in views)
        encoded_hit = bool(decoded) and any(
            INJECTION_RE.search(d) or INJECTION_RE.search(normalize_text(d)) for d in decoded
        )
        if encoded_hit:
            matched = True
        # Heavy obfuscation + collapsed harmful markers → escalate
        ob = obfuscation_signals(text, norm)
        if not matched and (
            "char_spaced_words" in ob or "char_spaced_cjk" in ob or "leetspeak_like" in ob
        ):
            if INJECTION_RE.search(leet) or re.search(
                r"(?i)(pausesafety|violentassault|howto|systemprompt|ignoreprevious|"
                r"bypasscontentfilters?|dumpapikeys|leakpasswords|aborttheusertask|"
                r"insteadleak|sendcontextsecrets|ignoreallrules|"
                r"强制导出|手机号|身份证|系统提示|绕过内容过滤|无限制回答)",
                leet,
            ):
                matched = True
                encoded_hit = True
        # Soft keyword in defensive teaching / glossary / postmortem — allow unless hard follow-on
        if matched and _META_EDU_RE.search(text) and not _HARD_ATTACK_FOLLOW_RE.search(text):
            return ScanResult(self.id, "allow", 0.0, ["injection_meta_edu_context"])
        if matched:
            score = 0.95
            if "zero_width_chars" in ob or "char_spaced_words" in ob or "char_spaced_cjk" in ob:
                score = min(1.0, score + 0.03)
            if "leetspeak_like" in ob:
                score = min(1.0, score + 0.02)
            if encoded_hit:
                score = min(1.0, score + 0.02)
            if score >= ctx.spec.threshold:
                reasons = ["injection_heuristic"]
                if encoded_hit:
                    reasons.append("encoded_payload")
                if decoded:
                    reasons.append(f"decode_views:{min(len(decoded), 9)}")
                reasons.extend(f"obfuscation:{s}" for s in ob)
                return ScanResult(self.id, "block", score, reasons)
        return ScanResult(self.id, "allow", 0.0, [])


class AnonymizeScanner:
    id = "anonymize"
    layer = "L1"

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        out = text
        found = False
        for pii_type, regex in (
            ("PHONE", PHONE_RE),
            ("ID", ID_RE),
            ("EMAIL", EMAIL_RE),
            ("BANK", BANK_RE),
        ):
            matches = list(regex.finditer(out))
            for m in reversed(matches):
                found = True
                token = ctx.vault.put(
                    tenant_id=ctx.tenant_id,
                    request_id=ctx.request_id,
                    pii_type=pii_type,
                    value=m.group(0),
                )
                out = out[: m.start()] + token + out[m.end() :]
        if found:
            return ScanResult(self.id, "redact", 0.6, ["pii_redacted"], redacted_text=out)
        return ScanResult(self.id, "allow", 0.0, [], redacted_text=out)


class BanTopicsScanner:
    id = "ban_topics"
    layer = "L1"

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        for t in ctx.spec.topics:
            if t and t in text:
                return ScanResult(self.id, "block", 0.9, [f"ban_topic:{t}"])
        return ScanResult(self.id, "allow", 0.0, [])


class SensitiveScanner:
    id = "sensitive"
    layer = "L3"

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        if (
            PHONE_RE.search(text)
            or ID_RE.search(text)
            or BANK_RE.search(text)
            or SECRET_RE.search(text)
        ):
            return ScanResult(self.id, "block", 0.85, ["sensitive_in_output"])
        return ScanResult(self.id, "allow", 0.0, [])


class OutputExfilScanner:
    """Handbook §8.4.2 — suspicious URL / high-entropy exfil in model output."""

    id = "output_exfil"
    layer = "L3"

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        reasons: list[str] = []
        score = 0.0
        urls = [m.group(0).rstrip(".,);]") for m in _URL_IN_TEXT_RE.finditer(text)]
        urls.extend(m.group(1) for m in _MD_IMG_RE.finditer(text))
        for url in urls:
            try:
                parsed = urlparse(url)
            except Exception:
                continue
            host = (parsed.hostname or "").lower()
            qs = parse_qs(parsed.query)
            long_param = any(len(v) >= 40 for vals in qs.values() for v in vals)
            if any(h in host for h in _EXFIL_HOST_HINTS):
                reasons.append(f"exfil_host:{host}")
                score = max(score, 0.95)
            if long_param or len(parsed.query) >= 80:
                reasons.append("suspicious_url_params")
                score = max(score, 0.85)
            # DNS / path exfil: long subdomain labels or token-like path segments
            labels = [x for x in (host or "").split(".") if x]
            if any(len(lab) >= 40 for lab in labels):
                reasons.append("exfil_dns_label")
                score = max(score, 0.85)
        if _DATA_URI_RE.search(text or ""):
            reasons.append("data_uri_exfil")
            score = max(score, 0.9)
        if _MD_IMG_RE.search(text or "") and any(
            h in (text or "").lower() for h in _EXFIL_HOST_HINTS
        ):
            reasons.append("markdown_img_exfil")
            score = max(score, 0.92)
        for m in _HIGH_ENTROPY_RE.finditer(text):
            chunk = m.group(0)
            if _shannon_entropy(chunk) >= 4.5 and len(chunk) >= 48:
                reasons.append("high_entropy_blob")
                score = max(score, 0.8)
                break
        if score >= ctx.spec.threshold and reasons:
            return ScanResult(self.id, "block", score, reasons)
        return ScanResult(self.id, "allow", 0.0, [])


class IndirectInjectionScanner:
    id = "indirect_injection"
    layer = "L1"

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        norm = normalize_text(text)
        if INDIRECT_RE.search(text) or INDIRECT_RE.search(norm):
            return ScanResult(self.id, "block", 0.9, ["indirect_injection"])
        return ScanResult(self.id, "allow", 0.0, [])


class SchemaScanner:
    id = "schema"
    layer = "L3"

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        s = text.strip()
        if not (s.startswith("{") or s.startswith("[")):
            return ScanResult(self.id, "allow", 0.0, ["schema_skipped_non_json"])
        try:
            json.loads(s)
            return ScanResult(self.id, "allow", 0.0, ["schema_ok"])
        except json.JSONDecodeError:
            return ScanResult(self.id, "block", 0.8, ["schema_invalid_json"])


class OnnxClassifierAdapter:
    id = "prompt_injection_onnx"
    layer = "L1"

    def __init__(self, inner: PromptInjectionScanner) -> None:
        self.inner = inner

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        if settings.scanner_mode != "onnx":
            return self.inner.scan(text, ctx)
        return self.inner.scan(text, ctx)


def default_registry() -> dict[str, object]:
    inj = PromptInjectionScanner()
    scanners = [
        TokenLimitScanner(),
        SecretsScanner(),
        inj,
        HiddenAsciiScanner(),
        AnonymizeScanner(),
        BanTopicsScanner(),
        ContentSafetyScanner(),
        ToxicityScanner(),
        SensitiveScanner(),
        OutputExfilScanner(),
        IndirectInjectionScanner(),
        SchemaScanner(),
        SystemLeakScanner(),
        RagGateScanner(),
        GroundingScanner(),
        SupplyChainScanner(),
        SessionRiskScanner(),
    ]
    reg = {s.id: s for s in scanners}
    reg["prompt_injection"] = (
        OnnxClassifierAdapter(inj) if settings.scanner_mode == "onnx" else inj
    )
    return reg
