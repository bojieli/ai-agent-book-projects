#!/usr/bin/env python3
"""
用户记忆离线命令行工具 (memory_cli)

这是一个**离线**的记忆运维 CLI，直接操作 memory_manager 的持久化存储，
无需任何大模型 API，即可演示用户记忆系统的完整生命周期：
提取（手动写入）→ 存储 → 更新 → 去重 / 版本化冲突消解 → 跨会话回忆。

与 main.py 的分工：
  * main.py  —— 完整的对话 / 后台记忆处理 / 评测流程，需要 LLM API。
  * memory_cli.py —— 单条记忆的增删查改与整理逻辑，纯本地可运行，
    便于在没有 API Key 的情况下检验存储、去重与冲突消解的行为。

子命令：
  add          写入一条记忆（模拟从某次会话中提取到的事实）
  query        按关键词检索记忆（跨会话回忆）
  update       按 ID 更新一条已有记忆
  consolidate  对记忆做去重与版本化冲突消解（无需 API）
  show         打印某个用户当前的全部记忆
  demo         运行一个多会话离线示例，展示记忆在后续会话中被复用
  extract      从一段对话中自动提取记忆（需要 LLM API）

示例：
  python memory_cli.py demo
  python memory_cli.py add --user alice --session s1 \
      --content "喜欢靠窗座位" --tags seat_preference
  python memory_cli.py query --user alice --query 座位
  python memory_cli.py consolidate --user alice
"""

import argparse
import sys

from config import Config, MemoryMode
from memory_manager import create_memory_manager


# 记忆模式字符串 -> 枚举，供各子命令共用
MODE_MAP = {
    "notes": MemoryMode.NOTES,
    "enhanced_notes": MemoryMode.ENHANCED_NOTES,
    "json_cards": MemoryMode.JSON_CARDS,
    "advanced_json_cards": MemoryMode.ADVANCED_JSON_CARDS,
}


def _apply_store_path(store_path):
    """若指定了 --store-path，则重定向记忆存储目录（不影响默认数据）。"""
    if store_path:
        Config.MEMORY_STORAGE_DIR = store_path
    Config.create_directories()


def _build_manager(args):
    """按命令行参数构造对应的记忆管理器（先设置存储目录再实例化）。"""
    _apply_store_path(getattr(args, "store_path", None))
    mode = MODE_MAP[args.memory_mode] if getattr(args, "memory_mode", None) else Config.MEMORY_MODE
    manager = create_memory_manager(args.user, mode)
    manager.verbose = True
    return manager, mode


def cmd_add(args):
    """写入一条记忆。仅 notes / enhanced_notes 模式支持自由文本写入。"""
    manager, mode = _build_manager(args)
    if mode not in (MemoryMode.NOTES, MemoryMode.ENHANCED_NOTES):
        print("❌ add 子命令仅支持 notes / enhanced_notes 模式（JSON 卡片请用 main.py 的对话流程生成）")
        return 1
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
    note_id = manager.add_memory(args.content, args.session, tags=tags)
    print(f"✅ 已写入记忆，ID={note_id}")
    return 0


def cmd_query(args):
    """按关键词检索记忆——用于演示“在后续会话中回忆起用户信息”。"""
    manager, _ = _build_manager(args)
    results = manager.search_memories(args.query)
    if not results:
        print(f"🔍 未检索到与“{args.query}”相关的记忆")
        return 0
    print(f"🔍 检索到 {len(results)} 条与“{args.query}”相关的记忆：")
    for item in results:
        if hasattr(item, "content"):  # MemoryNote
            tags = f" [tags: {', '.join(item.tags)}]" if item.tags else ""
            print(f"  - ({item.note_id[:8]}) {item.content}{tags}")
        else:  # (memory_path, data) tuple from JSON managers
            path, data = item
            print(f"  - {path}: {data}")
    return 0


def cmd_update(args):
    """按 ID 更新一条已有记忆（模拟用户提供了更新后的信息）。"""
    manager, _ = _build_manager(args)
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else None
    ok = manager.update_memory(args.id, args.content, args.session, tags=tags)
    print("✅ 更新成功" if ok else "⚠️  未找到对应 ID 的记忆，更新失败")
    return 0 if ok else 1


def cmd_consolidate(args):
    """去重 + 版本化冲突消解（纯离线，无需 API）。"""
    manager, _ = _build_manager(args)
    if not hasattr(manager, "consolidate_memories"):
        print("ℹ️  当前记忆模式的整理由写入时的键覆盖自动完成，无需显式 consolidate。")
        return 0
    report = manager.consolidate_memories(resolve_conflicts=not args.no_conflict)
    print("\n===== 记忆整理报告 =====")
    print(f"整理前条数: {report['initial_count']}")
    print(f"删除重复项: {report['duplicates_removed']}")
    print(f"消解冲突数: {len(report['conflicts_resolved'])}")
    for c in report["conflicts_resolved"]:
        print(f"  ⚔️  属性“{c['attribute']}”: 保留「{c['kept']}」，"
              f"废弃 {c['superseded']}")
    print(f"整理后条数: {report['final_count']}")
    return 0


def cmd_show(args):
    """打印某用户当前的全部记忆（即注入模型上下文的字符串）。"""
    manager, mode = _build_manager(args)
    print(f"\n===== 用户 {args.user} 的记忆（模式: {mode.value}）=====")
    print(manager.get_context_string())
    return 0


def cmd_demo(args):
    """多会话离线示例：写入 → 冲突/重复 → 整理 → 后续会话回忆。

    使用独立的 user_id 和临时存储目录，绝不触碰 data/ 下的真实用户数据。
    """
    import tempfile

    Config.MEMORY_STORAGE_DIR = args.store_path or tempfile.mkdtemp(prefix="memcli_demo_")
    Config.create_directories()
    user_id = "demo_user"
    mgr = create_memory_manager(user_id, MemoryMode.NOTES)
    mgr.verbose = False
    # 从干净状态开始，避免重复运行 demo 时叠加旧数据
    if hasattr(mgr, "clear_all_memories"):
        mgr.notes = []

    print("\n" + "=" * 62)
    print("  用户记忆多会话演示（离线，无需 API）")
    print(f"  存储目录: {Config.MEMORY_STORAGE_DIR}")
    print("=" * 62)

    # ---- 会话 1（较早）：首次了解用户偏好 ----
    print("\n[会话 1 · 2024-03-01] 用户初次交流，Agent 提取到以下事实：")
    mgr.add_memory("用户偏好靠窗座位", "session_2024_03", tags=["seat_preference"])
    mgr.add_memory("用户家住北京朝阳区", "session_2024_03", tags=["home_address"])
    mgr.add_memory("用户喜欢川菜", "session_2024_03", tags=["food_preference"])
    for n in mgr.notes:
        print(f"    + {n.content}  [{n.tags[0]}]")

    # ---- 会话 2（较晚）：用户搬家（冲突）并重复提到座位偏好（重复）----
    print("\n[会话 2 · 2024-09-15] 用户提供了更新后的信息：")
    mgr.add_memory("用户已搬到上海浦东", "session_2024_09", tags=["home_address"])
    mgr.add_memory("用户偏好靠窗座位", "session_2024_09", tags=["seat_preference"])  # 重复
    print("    + 用户已搬到上海浦东  [home_address]  (与会话1的北京住址冲突)")
    print("    + 用户偏好靠窗座位  [seat_preference]  (与会话1重复)")
    print(f"\n  整理前共有 {len(mgr.notes)} 条记忆（含 1 条重复、1 处冲突）")

    # ---- 记忆整理：去重 + 版本化冲突消解 ----
    print("\n[后台整理] 运行 consolidate_memories()：去重 + 按更新时间消解冲突")
    report = mgr.consolidate_memories(resolve_conflicts=True)
    print(f"    删除重复: {report['duplicates_removed']} 条")
    for c in report["conflicts_resolved"]:
        print(f"    冲突消解: 属性“{c['attribute']}”保留「{c['kept']}」，废弃 {c['superseded']}")
    print(f"    整理后共有 {report['final_count']} 条记忆")

    # ---- 会话 3（更晚）：后续会话中回忆用户信息 ----
    print("\n[会话 3 · 2025-01-20] 用户问：“帮我订张机票，你还记得我住哪吗？”")
    hits = mgr.search_memories("home_address")
    recalled = hits[0].content if hits else "（无相关记忆）"
    print(f"    Agent 检索记忆(home_address) → 回忆到：{recalled}")
    print(f"    ✅ Agent 回复：已按您在上海浦东的地址为您推荐航班。")
    print("       （注意：这里回忆到的是消解冲突后的最新住址，而非会话1的旧址）")

    print("\n最终记忆快照：")
    print(mgr.get_context_string())
    return 0


def cmd_extract(args):
    """从一段对话中自动提取记忆——需要 LLM API（在线）。

    此子命令的参数解析与校验可离线验证；实际提取会调用后台记忆处理器，
    需要配置对应 provider 的 API Key。
    """
    provider = args.provider or Config.PROVIDER
    if not Config.get_api_key(provider):
        print(f"⚠️  extract 需要 LLM API：未检测到 provider '{provider}' 的 API Key。")
        print("    请在 .env 中配置对应的 *_API_KEY 后重试（参数解析已通过）。")
        return 2

    # 读取对话文本：--conversation 可为文件路径或直接的文本
    import os
    text = args.conversation
    if text and os.path.isfile(text):
        with open(text, "r", encoding="utf-8") as f:
            text = f.read()
    if not text:
        print("❌ 请通过 --conversation 提供对话文本或文件路径")
        return 1

    _apply_store_path(args.store_path)
    mode = MODE_MAP[args.memory_mode] if args.memory_mode else Config.MEMORY_MODE

    from background_memory_processor import BackgroundMemoryProcessor
    processor = BackgroundMemoryProcessor(
        user_id=args.user, provider=provider, model=args.model, memory_mode=mode, verbose=True
    )
    # 将纯文本对话拆成 user/assistant 轮次交给处理器分析
    lines = [ln for ln in text.splitlines() if ln.strip()]
    conversation = [{"role": "user" if i % 2 == 0 else "assistant", "content": ln}
                    for i, ln in enumerate(lines)]
    processor.analyze_conversation(conversation)
    print("\n✅ 提取完成，当前记忆：")
    print(processor.memory_manager.get_context_string())
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="memory_cli.py",
        description="用户记忆离线命令行工具：增/查/改/整理记忆，演示跨会话记忆的存储与冲突消解（无需 API）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", metavar="子命令")

    def add_common(p, need_mode=True):
        p.add_argument("--user", default="default_user", help="用户 ID（默认: default_user）")
        p.add_argument("--store-path", default=None,
                       help="记忆存储目录（默认: data/memories，可指定其它路径以免影响真实数据）")
        if need_mode:
            p.add_argument("--memory-mode", choices=list(MODE_MAP.keys()), default=None,
                           help="记忆存储格式（默认取环境变量 MEMORY_MODE）")

    p_add = sub.add_parser("add", help="写入一条记忆（模拟从会话中提取到的事实）")
    add_common(p_add)
    p_add.add_argument("--session", default="cli_session", help="来源会话 ID（默认: cli_session）")
    p_add.add_argument("--content", required=True, help="记忆内容文本")
    p_add.add_argument("--tags", default=None, help="标签，逗号分隔；第一个标签作为冲突消解的属性键")
    p_add.set_defaults(func=cmd_add)

    p_query = sub.add_parser("query", help="按关键词检索记忆（跨会话回忆）")
    add_common(p_query)
    p_query.add_argument("--query", required=True, help="检索关键词")
    p_query.set_defaults(func=cmd_query)

    p_update = sub.add_parser("update", help="按 ID 更新一条已有记忆")
    add_common(p_update)
    p_update.add_argument("--id", required=True, help="要更新的记忆 ID")
    p_update.add_argument("--session", default="cli_session", help="本次更新的会话 ID")
    p_update.add_argument("--content", required=True, help="更新后的记忆内容")
    p_update.add_argument("--tags", default=None, help="更新后的标签，逗号分隔")
    p_update.set_defaults(func=cmd_update)

    p_cons = sub.add_parser("consolidate", help="去重 + 版本化冲突消解（纯离线）")
    add_common(p_cons)
    p_cons.add_argument("--no-conflict", action="store_true",
                        help="只做去重，不做冲突消解")
    p_cons.set_defaults(func=cmd_consolidate)

    p_show = sub.add_parser("show", help="打印某用户当前的全部记忆")
    add_common(p_show)
    p_show.set_defaults(func=cmd_show)

    p_demo = sub.add_parser("demo", help="多会话离线示例：写入→冲突/重复→整理→后续会话回忆")
    p_demo.add_argument("--store-path", default=None,
                        help="演示数据的存储目录（默认: 临时目录，不触碰 data/）")
    p_demo.set_defaults(func=cmd_demo)

    p_ext = sub.add_parser("extract", help="从对话中自动提取记忆（需要 LLM API）")
    add_common(p_ext)
    p_ext.add_argument("--conversation", required=True, help="对话文本或对话文件路径")
    p_ext.add_argument("--provider", default=None,
                       choices=["dashscope", "qwen", "bailian", "siliconflow", "doubao", "kimi", "moonshot", "openrouter"],
                       help="LLM 提供商（默认取环境变量 PROVIDER）")
    p_ext.add_argument("--model", default=None, help="模型名称（默认使用提供商默认模型）")
    p_ext.set_defaults(func=cmd_extract)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
