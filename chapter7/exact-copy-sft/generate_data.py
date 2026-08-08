from __future__ import annotations
import hashlib, json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789_-+=:@"
LANGUAGES = ["Python", "JavaScript", "Java", "Go", "Rust", "SQL", "Shell", "JSON", "Markdown", "纯文本"]
ARTICLE_TYPES = ["代码审查", "补丁说明", "故障复盘", "API 文档", "部署手册", "测试报告", "变更公告", "设计文档"]

def make_string(rng, n):
    return "".join(rng.choice(ALPHABET) for _ in range(n))

def make(split, n, seed):
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        s = make_string(rng, 18 + (i % 7) * 7)
        if i % 5 == 0:
            s = s[:8] + " " + s[8:] + "\n" + s[-3:]
        elif i % 5 == 1:
            s = s[:5] + "\\n" + s[5:] + "\\tEND"
        elif i % 5 == 2:
            s = "ID=" + s + "; sha256=" + make_string(rng, 16)
        elif i % 5 == 3:
            s = s[:4] + "é" + s[4:] + "\u200b"
        else:
            s = "中" + s + "e\u0301"
        candidates = [make_string(rng, len(s)), make_string(rng, len(s)), s]
        language = LANGUAGES[(i + seed) % len(LANGUAGES)]
        article_type = ARTICLE_TYPES[(i * 3 + seed) % len(ARTICLE_TYPES)]
        if i % 3 == 0:
            prompt = (f"这是{article_type}中的 {language} 文件。\n从下面的工具观察中找到 path=/tmp/job.txt 的 old_string。\n"
                      "只输出 JSON，不要解释：\n" + json.dumps(
                          {"path": "/tmp/job.txt", "old_string": s, "other": ""}, ensure_ascii=False))
            target = json.dumps({"old_string": s}, ensure_ascii=False, separators=(",", ":"))
            kind = "tool_json"
        elif i % 3 == 1:
            prompt = (f"这是{article_type}中的 {language} 片段。\n请逐字复述唯一被标记为 TARGET 的字符串，只输出字符串本身。\n" +
                      "\n".join(f"{('TARGET' if j == 2 else 'DECOY')}={x}" for j, x in enumerate(candidates)))
            target, kind = s, "decoy_copy"
        else:
            prompt = (f"这是{article_type}中的 {language} 片段。\n请把 SOURCE 中的内容逐字复制到 ANSWER，不得修正大小写、空格、反斜杠或换行，只输出 ANSWER。\nSOURCE:\n" + s)
            target, kind = s, "verbatim"
        rows.append({"id": f"{split}-{i:03d}", "kind": kind, "language": language,
                     "article_type": article_type, "source": s, "prompt": prompt, "target": target})
    return rows

def write(name, rows):
    p = DATA / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")
    return hashlib.sha256(p.read_bytes()).hexdigest()

if __name__ == "__main__":
    print(json.dumps({
        "train": write("train.jsonl", make("train", 1024, 719)),
        "eval": write("eval.jsonl", make("eval", 256, 1729)),
        "boundary": write("boundary.jsonl", make("boundary", 256, 2718)),
    }, indent=2))
