from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

VERSIONS = ["v2", "v2.1", "v3", "v4-beta", "2026.08", "release-候选"]
ACTIONS = ["先运行测试", "先备份数据", "检查权限", "重新读取文件", "核对验收条件", "查看变更记录"]
STATUSES = ["ok", "ready", "pending", "degraded", "accepted", "retry"]
WORDS = ["当前状态", "请求编号", "缓存策略", "错误原因", "目标路径", "发布说明"]
LITERALS = ["DELETE", "PATCH", "ROLLBACK", "dry_run", "API_KEY", "status"]
ENGLISH = [
    "Please restart the service before retrying.",
    "The file was not changed.",
    "Run the migration only once.",
    "This value must remain unchanged.",
    "Do not remove the assertion.",
]

ARTICLE_TYPES = [
    "新闻报道", "API 参考", "故障复盘", "发布说明", "操作手册",
    "FAQ", "设计文档", "教程", "变更公告", "安全通告",
]

TEMPLATES = {
    "zh": (
        "请把下面的中文段落按项目文档规范修订，只输出修订后的文本。\n\n他说：\"今天发布 {version}\"，随后补充：\"{action}\"。",
        "他说：“今天发布 {version}”，随后补充：“{action}”。",
    ),
    "mixed": (
        "请修订下面的混合技术说明，只输出结果。\n\n调用 `{method}()` 后，服务返回 {{\"status\": \"{status}\"}}。说明文字中写着：\"{action}\"。",
        "调用 `{method}()` 后，服务返回 {{\"status\": \"{status}\"}}。说明文字中写着：“{action}”。",
    ),
    "english": (
        "请修订下面的文章，只输出结果。\n\n原文引用如下：\"{english}\" 这段英文必须保持原样。",
        "原文引用如下：\"{english}\" 这段英文必须保持原样。",
    ),
    "python": (
        "请修订下面的 Markdown 文档，只输出结果。\n\n```python\n# 中文注释：显示 \"{word}\"\nname = \"{literal}\"\nprint(name)\n```\n代码不能被改坏。",
        "```python\n# 中文注释：显示 “{word}”\nname = \"{literal}\"\nprint(name)\n```\n代码不能被改坏。",
    ),
    "javascript": (
        "请修订下面的 JavaScript 示例，只输出结果。\n\n```javascript\n// 中文注释：显示 \"{word}\"\nconst name = \"{literal}\";\nconsole.log(name);\n```\n代码不能被改坏。",
        "```javascript\n// 中文注释：显示 “{word}”\nconst name = \"{literal}\";\nconsole.log(name);\n```\n代码不能被改坏。",
    ),
    "java": (
        "请修订下面的 Java 示例，只输出结果。\n\n```java\n// 中文注释：显示 \"{word}\"\nString name = \"{literal}\";\nSystem.out.println(name);\n```\n代码不能被改坏。",
        "```java\n// 中文注释：显示 “{word}”\nString name = \"{literal}\";\nSystem.out.println(name);\n```\n代码不能被改坏。",
    ),
    "go": (
        "请修订下面的 Go 示例，只输出结果。\n\n```go\n// 中文注释：显示 \"{word}\"\nname := \"{literal}\"\nfmt.Println(name)\n```\n代码不能被改坏。",
        "```go\n// 中文注释：显示 “{word}”\nname := \"{literal}\"\nfmt.Println(name)\n```\n代码不能被改坏。",
    ),
    "rust": (
        "请修订下面的 Rust 示例，只输出结果。\n\n```rust\n// 中文注释：显示 \"{word}\"\nlet name = \"{literal}\";\nprintln!(\"{{}}\", name);\n```\n代码不能被改坏。",
        "```rust\n// 中文注释：显示 “{word}”\nlet name = \"{literal}\";\nprintln!(\"{{}}\", name);\n```\n代码不能被改坏。",
    ),
    "sql": (
        "请修订下面的 SQL 示例，只输出结果。\n\n```sql\n-- 中文注释：显示 \"{word}\"\nSELECT \"{literal}\" AS status;\n```\n代码不能被改坏。",
        "```sql\n-- 中文注释：显示 “{word}”\nSELECT \"{literal}\" AS status;\n```\n代码不能被改坏。",
    ),
    "shell": (
        "请修订下面的 Shell 示例，只输出结果。\n\n```bash\n# 中文注释：显示 \"{word}\"\nname=\"{literal}\"\nprintf '%s\\n' \"$name\"\n```\n代码不能被改坏。",
        "```bash\n# 中文注释：显示 “{word}”\nname=\"{literal}\"\nprintf '%s\\n' \"$name\"\n```\n代码不能被改坏。",
    ),
    "yaml": (
        "请修订下面的 YAML 配置，只输出结果。\n\n```yaml\n# 中文注释：显示 \"{word}\"\nname: \"{literal}\"\n```\n代码不能被改坏。",
        "```yaml\n# 中文注释：显示 “{word}”\nname: \"{literal}\"\n```\n代码不能被改坏。",
    ),
    "markdown": (
        "请修订下面的 Markdown 教程，只输出结果。\n\n说明文字写着：\"{action}\"；命令 `run-{method}` 必须保持。",
        "说明文字写着：“{action}”；命令 `run-{method}` 必须保持。",
    ),
    "nested": (
        "请修订下面的中文段落，只输出结果。\n\n她说：\"他说“{action}”，然后才修改。\"",
        "她说：“他说‘{action}’，然后才修改。”",
    ),
    "comment": (
        "请修订下面的说明，只输出结果。\n\n代码注释里的自然语言引用是：\"{action}\"；Python 字符串 `{quote_literal}` 的语法必须保持。",
        "代码注释里的自然语言引用是：“{action}”；Python 字符串 `{quote_literal}` 的语法必须保持。",
    ),
    "quote": (
        "请修订下面的中文报道，只输出结果。\n\n报告引用用户原话：\"{action}\"。英文原句 \"{english}\" 也要原样保留。",
        "报告引用用户原话：“{action}”。英文原句 \"{english}\" 也要原样保留。",
    ),
    "json": (
        "请修订下面的接口文档，只输出结果。\n\n中文说明：\"{word}必须存在\"。请求体示例：{{\"message\": \"{status}\"}}。",
        "中文说明：“{word}必须存在”。请求体示例：{{\"message\": \"{status}\"}}。",
    ),
}
KINDS = list(TEMPLATES)
CODE_LANGUAGES = {
    "python": "Python", "javascript": "JavaScript", "java": "Java",
    "go": "Go", "rust": "Rust", "sql": "SQL", "shell": "Shell",
    "yaml": "YAML", "markdown": "Markdown",
}
CODE_KINDS = set(CODE_LANGUAGES) | {"comment"}
SCOPE_RULE = (
    "作用域规则：只把代码注释中的中文自然语言直引号改成中文弯引号；"
    "字符串/字符字面量、格式化占位符、标识符、JSON 和 SQL 语法中的 ASCII 引号必须逐字保留。"
    "示例：# 中文注释：显示 \"状态\" → # 中文注释：显示“状态”；name = \"status\" 不变。"
)


def make(split: str, n: int):
    rows = []
    split_offset = {"train": 0, "eval": 17, "boundary": 31}[split]
    for i in range(n):
        kind = KINDS[(i + split_offset) % len(KINDS)]
        values = {
            "version": VERSIONS[(i + split_offset) % len(VERSIONS)],
            "action": ACTIONS[(i * 3 + split_offset) % len(ACTIONS)],
            "status": STATUSES[(i * 5 + split_offset) % len(STATUSES)],
            "word": WORDS[(i * 7 + split_offset) % len(WORDS)],
            "literal": LITERALS[(i * 11 + split_offset) % len(LITERALS)],
            "quote_literal": LITERALS[(i * 13 + split_offset) % len(LITERALS)],
            "english": ENGLISH[(i * 2 + split_offset) % len(ENGLISH)],
            "method": ["reset", "validate", "rebuild", "deploy", "rollback", "inspect"][(i + split_offset) % 6],
        }
        prompt, target = (x.format(**values) for x in TEMPLATES[kind])
        if kind in CODE_KINDS:
            prompt = SCOPE_RULE + "\n\n" + prompt
        article_type = ARTICLE_TYPES[(i * 5 + split_offset) % len(ARTICLE_TYPES)]
        language = CODE_LANGUAGES.get(kind, "中文/英文自然语言")
        suffix = f"（案例编号 {split}-{i:03d}；体裁={article_type}；语言={language}；请保持事实和代码不变。）"
        rows.append({"id": f"{split}-{i:04d}", "kind": kind, "article_type": article_type,
                     "language": language, "prompt": prompt + "\n" + suffix,
                     "target": target + "\n" + suffix})
    return rows


def write(name: str, rows):
    path = DATA / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    hashes = {
        "train": write("train.jsonl", make("train", 1024)),
        "eval": write("eval.jsonl", make("eval", 256)),
        "boundary": write("boundary.jsonl", make("boundary", 256)),
    }
    print(json.dumps(hashes, indent=2))
