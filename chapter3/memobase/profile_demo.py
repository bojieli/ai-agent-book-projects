"""
Memobase 用户画像（Profile）+ 事件记忆（Event Memory）演示

对应《深入理解 AI Agent》第 3 章"记忆框架案例"中对 Memobase 的介绍：
Memobase（开源项目 memodb-io/memobase）把用户记忆组织为两部分——
  * 用户画像（Profile）：按"主题—子主题"两级组织的稳定用户属性
    （如 basic_info→姓名、interest→游戏偏好、work→职位），从对话中提取；
  * 事件记忆（Event Memory）：按时间线记录用户经历的事件，
    用于回答"我们上次讨论预算是什么时候"这类与时间有关的问题。
工程上 Memobase 采用"缓冲批处理"：对话先 insert 进缓冲区累积，
flush 时才统一触发一次 LLM 记忆提取，查询侧（profile/event/context）
只读取已整理好的结果，保证低延迟。

本脚本用真实的 memobase Python SDK 演示这条链路：
    insert（写入对话缓冲）→ flush（触发提取）→ profile / event / context（召回）

运行前提：Memobase 需要一个正在运行的服务端 + 用于提取记忆的 LLM。
  * 自托管：见 https://github.com/memodb-io/memobase （docker compose 启动，
    默认服务地址 http://localhost:8019，默认 token 为 secret）；
  * 云服务：在 https://www.memobase.ai 申请 project_url 与 api_key。
无服务端时可用 --dry-run 查看示例对话与将要执行的操作（不联网、不伪造结果）。
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 示例多轮对话：内容刻意覆盖三个画像主题，便于观察 Profile 的两级结构
SAMPLE_CONVERSATION = [
    {"role": "user", "content": "你好，我叫李明，今年 28 岁，住在上海。"},
    {"role": "assistant", "content": "你好李明，很高兴认识你！有什么可以帮你的吗？"},
    {"role": "user", "content": "我在一家游戏公司做后端工程师，主要用 Go 语言。"},
    {"role": "assistant", "content": "后端工程师很酷，Go 在高并发服务里很常用。"},
    {"role": "user", "content": "平时最喜欢玩《塞尔达传说》和《艾尔登法环》这类开放世界游戏。"},
    {"role": "assistant", "content": "开放世界游戏的探索感确实很棒。"},
    {"role": "user", "content": "对了，上周我们把新项目的预算定在了 50 万。"},
    {"role": "assistant", "content": "好的，我记住了新项目预算是 50 万。"},
]

# 期望被提取出的画像主题（仅用于 --dry-run 的结构说明，非真实结果）
EXPECTED_TOPICS = {
    "basic_info": ["姓名", "年龄", "城市"],
    "work": ["职位", "公司", "技术栈"],
    "interest": ["游戏偏好"],
}

DEFAULT_PROJECT_URL = os.getenv("MEMOBASE_PROJECT_URL", "http://localhost:8019")
DEFAULT_API_KEY = os.getenv("MEMOBASE_API_KEY", "secret")


def load_conversation(input_path: str | None) -> list[dict]:
    """从 --input 指定的 JSON 文件读取对话，缺省则用内置示例对话。

    文件格式：[{"role": "user"|"assistant", "content": "..."}, ...]
    """
    if not input_path:
        return SAMPLE_CONVERSATION
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(
        isinstance(m, dict) and "role" in m and "content" in m for m in data
    ):
        raise ValueError("对话文件应为 [{'role':..., 'content':...}, ...] 形式的 JSON")
    return data


def print_conversation(conversation: list[dict]) -> None:
    print("\n💬 对话内容：")
    for m in conversation:
        who = "👤 用户" if m["role"] == "user" else "🤖 助手"
        print(f"  {who}: {m['content']}")


def build_client(args):
    """构造并连通 Memobase 客户端（联网）。失败时给出可操作的提示。"""
    try:
        from memobase import MemoBaseClient
    except ImportError:
        print("❌ 未安装 memobase SDK，请先运行：pip install -r requirements.txt")
        sys.exit(1)

    client = MemoBaseClient(project_url=args.project_url, api_key=args.api_key)
    try:
        reachable = client.ping()
    except Exception as exc:  # 连接被拒绝、超时、DNS 失败等
        reachable = False
        print(f"❌ 连接 Memobase 服务端时出错：{exc}")
    if not reachable:
        print("❌ 无法连接 Memobase 服务端：", args.project_url)
        print("   请确认服务已启动（自托管见 memodb-io/memobase 的 docker compose），")
        print("   或用 --project-url / --api-key 指定云服务地址与密钥。")
        print("   仅想查看示例与流程（不联网）可加 --dry-run。")
        sys.exit(1)
    return client


def render_profiles(profiles) -> list[dict]:
    """把 SDK 返回的 UserProfile 列表整理成 主题→子主题→内容 的结构。"""
    rows = []
    for p in profiles:
        rows.append({"topic": p.topic, "sub_topic": p.sub_topic, "content": p.content})
    return rows


def render_events(events) -> list[dict]:
    """把 SDK 返回的 UserEventData 列表整理成可读的时间线。"""
    rows = []
    for e in events:
        tip = None
        tags = None
        if e.event_data is not None:
            tip = e.event_data.event_tip
            if e.event_data.event_tags:
                tags = {t.tag: t.value for t in e.event_data.event_tags}
        rows.append(
            {
                "created_at": str(e.created_at),
                "event_tip": tip,
                "event_tags": tags,
            }
        )
    return rows


def op_insert(user, conversation) -> None:
    from memobase import ChatBlob

    print_conversation(conversation)
    bid = user.insert(ChatBlob(messages=conversation))
    print(f"\n✅ 已写入对话缓冲区（blob id: {bid}）")
    print("   提示：写入只进缓冲区，尚未提取记忆；执行 flush 才会触发一次提取。")


def op_flush(user) -> None:
    print("\n🧠 正在 flush 缓冲区，触发记忆提取（由服务端 LLM 完成，可能需要数秒）...")
    ok = user.flush(sync=True)
    print("✅ 记忆提取完成" if ok else "⚠️ flush 返回 False，请检查服务端日志")


def op_profile(user) -> list[dict]:
    profiles = render_profiles(user.profile())
    print("\n📇 用户画像（Profile，主题 → 子主题 → 内容）：")
    if not profiles:
        print("  （暂无画像，请先 insert 对话并 flush 提取）")
    for r in profiles:
        print(f"  • [{r['topic']}] {r['sub_topic']}: {r['content']}")
    return profiles


def op_event(user) -> list[dict]:
    events = render_events(user.event())
    print("\n🗓️  事件记忆（Event Memory，按时间线）：")
    if not events:
        print("  （暂无事件）")
    for r in events:
        print(f"  • {r['created_at']}  {r['event_tip'] or ''}")
        if r["event_tags"]:
            print(f"      标签: {r['event_tags']}")
    return events


def op_context(user) -> str:
    ctx = user.context()
    print("\n🧩 组装好的记忆上下文（context，可直接拼进 LLM 提示词）：")
    print(ctx if ctx else "  （空）")
    return ctx


def run_demo(user, conversation, output_path):
    """端到端演示：从对话构建画像，再召回画像 / 事件 / 上下文。"""
    print("=" * 64)
    print("Memobase 用户画像 + 事件记忆 端到端演示")
    print("=" * 64)
    op_insert(user, conversation)
    op_flush(user)
    profiles = op_profile(user)
    events = op_event(user)
    ctx = op_context(user)
    result = {"profiles": profiles, "events": events, "context": ctx}
    if output_path:
        Path(output_path).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\n💾 结果已写入：{output_path}")
    return result


def run_dry_run(conversation):
    """离线路径：不联网，展示示例对话、缓冲批处理流程与期望画像结构。"""
    print("=" * 64)
    print("Memobase 演示（--dry-run 离线预览，不连接服务端、不伪造结果）")
    print("=" * 64)
    print_conversation(conversation)
    print("\n🔀 将要执行的操作（缓冲批处理流水线）：")
    print("  1) insert  —— 把上述对话写入用户缓冲区（不触发提取）")
    print("  2) flush   —— 统一触发一次 LLM 记忆提取（摊薄调用成本）")
    print("  3) profile —— 读取提取出的结构化用户画像")
    print("  4) event   —— 读取按时间线组织的事件记忆")
    print("  5) context —— 读取组装好的记忆上下文")
    print("\n🧬 期望被提取的画像结构（主题 → 子主题，示意，非真实结果）：")
    for topic, subs in EXPECTED_TOPICS.items():
        print(f"  • {topic}: {', '.join(subs)}")
    print("\n▶️  接入真实服务后，去掉 --dry-run 即可执行上述完整链路。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Memobase 用户画像（Profile）+ 事件记忆（Event Memory）演示",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python profile_demo.py                      # 端到端演示（内置示例对话）\n"
            "  python profile_demo.py --dry-run            # 离线预览流程，不连接服务端\n"
            "  python profile_demo.py --op profile         # 只召回已提取的用户画像\n"
            "  python profile_demo.py --op event           # 只查看事件记忆时间线\n"
            "  python profile_demo.py --input chat.json --output result.json\n"
        ),
    )
    parser.add_argument(
        "--op",
        choices=["demo", "insert", "flush", "profile", "event", "context", "reset"],
        default="demo",
        help="记忆操作：demo=端到端演示(默认)；insert=写入对话缓冲；"
        "flush=触发提取；profile=召回画像；event=事件记忆；"
        "context=记忆上下文；reset=删除该用户重置",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="对话输入文件（JSON：[{'role','content'}, ...]），缺省用内置示例对话",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default="demo_user_liming",
        help="用户 ID（默认 demo_user_liming）",
    )
    parser.add_argument(
        "--project-url",
        type=str,
        default=DEFAULT_PROJECT_URL,
        help=f"Memobase 服务地址（默认 {DEFAULT_PROJECT_URL}，可用环境变量 MEMOBASE_PROJECT_URL）",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=DEFAULT_API_KEY,
        help="Memobase 访问密钥（默认取环境变量 MEMOBASE_API_KEY，自托管默认 secret）",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="记忆提取所用 LLM（仅作说明：Memobase 由服务端配置提取模型，"
        "客户端不直接指定；如需更换请改服务端 .env）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="将画像/事件/上下文结果写入指定 JSON 文件",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="离线预览：仅展示示例对话与操作流程，不连接服务端、不伪造结果",
    )
    return parser


def main():
    args = build_parser().parse_args()
    try:
        conversation = load_conversation(args.input)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"❌ 读取对话文件失败（{args.input}）：{exc}")
        sys.exit(1)

    if args.dry_run:
        run_dry_run(conversation)
        return

    if args.model:
        print(f"ℹ️  --model={args.model}：Memobase 的提取模型由服务端配置，此处仅作记录。")

    client = build_client(args)
    user = client.get_or_create_user(args.user_id)

    if args.op == "demo":
        run_demo(user, conversation, args.output)
        return

    result = None
    if args.op == "insert":
        op_insert(user, conversation)
    elif args.op == "flush":
        op_flush(user)
    elif args.op == "profile":
        result = {"profiles": op_profile(user)}
    elif args.op == "event":
        result = {"events": op_event(user)}
    elif args.op == "context":
        result = {"context": op_context(user)}
    elif args.op == "reset":
        client.delete_user(args.user_id)
        print(f"🧹 已删除用户 {args.user_id}，画像与事件已清空。")

    if result and args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\n💾 结果已写入：{args.output}")


if __name__ == "__main__":
    main()
