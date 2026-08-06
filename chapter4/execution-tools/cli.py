#!/usr/bin/env python3
"""执行工具统一命令行入口（实验 4-3：执行工具 MCP 服务器）。

本文件提供一个 argparse 命令行界面，用于列出、单独调用每个执行工具，并运行
一个端到端的离线演示。它复用 server.py 背后的同一批工具实现，因此命令行的
行为与 MCP 服务器完全一致。

工具清单（与 server.py 一致）：
  file_write        写文件（写入前自动做语法/linter 校验）
  file_edit         按“搜索-替换”编辑文件（带 diff 预览与校验）
  code_interpreter  多语言沙盒代码执行（危险操作审批、长输出截断持久化）
  virtual_terminal  Shell 命令执行（危险命令检测、长输出截断持久化）
  google_calendar_add  创建 Google 日历事件（需要凭据）
  github_create_pr     创建 GitHub Pull Request（需要 token）

安全机制（与书中“执行工具”一节对应）：
  - LLM 事前审批：不可逆/危险操作在执行前交由独立 LLM 审查
  - 自动验证：Python 语法通过 compile() 本地校验，其他语言由 LLM 兜底
  - 长输出截断与持久化：超过阈值时仅保留头尾若干行，完整输出落盘到临时文件

用法示例：
  python cli.py list
  python cli.py demo
  python cli.py code --language python --code "print(2 ** 10)"
  python cli.py shell "python3 --version"
  python cli.py write --path notes.txt --content "hello" --overwrite
  python cli.py --no-approval --no-summarize shell "ls -la"

不需要 API key 的命令：list、demo（离线路径）、以及关闭了审批/总结/非 Python
校验的 code/shell/write/edit。需要 API key 的场景：LLM 审批、长输出 LLM 总结、
非 Python 语法校验。calendar 与 pr 还额外需要相应的外部凭据。
"""

import argparse
import asyncio
import json
import os
import sys
import tempfile
import textwrap


# ---------------------------------------------------------------------------
# 工具元数据（供 `list` 子命令展示）
# ---------------------------------------------------------------------------
TOOL_CATALOG = [
    ("file_write", "文件系统", "写文件，写入前自动做语法/linter 校验"),
    ("file_edit", "文件系统", "按搜索-替换编辑文件，附带 diff 预览与校验"),
    ("code_interpreter", "通用执行", "多语言沙盒代码执行（Python/JS/Go/Java/C++/Rust/PHP/Bash）"),
    ("virtual_terminal", "通用执行", "Shell 命令执行，含危险命令检测与长输出截断"),
    ("google_calendar_add", "外部系统", "创建 Google 日历事件（需要 credentials.json）"),
    ("github_create_pr", "外部系统", "创建 GitHub Pull Request（需要 GITHUB_TOKEN）"),
]


def _apply_global_env(args: argparse.Namespace) -> None:
    """把全局开关写入环境变量，供 config.py 在导入时读取。

    config.Config 在模块导入时读取环境变量，因此所有涉及配置的模块都必须在此
    函数执行之后才导入（本文件中的工具模块均为函数内延迟导入）。
    """
    if args.provider:
        os.environ["PROVIDER"] = args.provider
    if args.workspace:
        os.environ["WORKSPACE_DIR"] = os.path.abspath(args.workspace)
    if args.no_approval:
        os.environ["REQUIRE_APPROVAL_FOR_DANGEROUS_OPS"] = "false"
    if args.no_verify:
        os.environ["AUTO_VERIFY_CODE"] = "false"
    if args.no_summarize:
        os.environ["AUTO_SUMMARIZE_COMPLEX_OUTPUT"] = "false"


def _build_tools():
    """构造共享的工具实例（延迟导入，确保环境变量已就绪）。"""
    from llm_helper import LLMHelper
    from file_tools import FileTools
    from execution_tools import ExecutionTools
    from external_tools import ExternalTools

    llm_helper = LLMHelper()  # 客户端惰性创建，离线时不需要 API key
    return {
        "llm": llm_helper,
        "file": FileTools(llm_helper),
        "exec": ExecutionTools(llm_helper),
        "external": ExternalTools(llm_helper),
    }


def _print_result(result: dict) -> None:
    """统一以 JSON 打印工具返回结果。"""
    print(json.dumps(result, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# 子命令实现
# ---------------------------------------------------------------------------
def cmd_list(args: argparse.Namespace) -> int:
    print("可用执行工具：\n")
    print(f"  {'工具名':<20} {'类别':<8} 说明")
    print(f"  {'-' * 20} {'-' * 8} {'-' * 40}")
    for name, category, desc in TOOL_CATALOG:
        print(f"  {name:<20} {category:<8} {desc}")
    print("\n用 `python cli.py <子命令> --help` 查看每个工具的参数。")
    print("用 `python cli.py demo` 运行端到端离线演示。")
    return 0


def cmd_code(args: argparse.Namespace) -> int:
    code = args.code
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            code = f.read()
    if not code:
        print("错误：请通过 --code 或 --file 提供要执行的代码。", file=sys.stderr)
        return 2

    tools = _build_tools()
    result = asyncio.run(tools["exec"].code_interpreter(
        code=code,
        language=args.language,
        timeout=args.timeout,
        stdin=args.stdin,
    ))
    _print_result(result)
    return 0 if result.get("success") else 1


def cmd_shell(args: argparse.Namespace) -> int:
    tools = _build_tools()
    result = asyncio.run(tools["exec"].virtual_terminal(
        command=args.command,
        timeout=args.timeout,
    ))
    _print_result(result)
    return 0 if result.get("success") else 1


def cmd_write(args: argparse.Namespace) -> int:
    content = args.content
    if args.content_file:
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read()
    if content is None:
        print("错误：请通过 --content 或 --content-file 提供文件内容。", file=sys.stderr)
        return 2

    tools = _build_tools()
    result = asyncio.run(tools["file"].write_file(
        path=args.path,
        content=content,
        overwrite=args.overwrite,
    ))
    _print_result(result)
    return 0 if result.get("success") else 1


def cmd_edit(args: argparse.Namespace) -> int:
    tools = _build_tools()
    result = asyncio.run(tools["file"].edit_file(
        path=args.path,
        search=args.search,
        replace=args.replace,
    ))
    _print_result(result)
    return 0 if result.get("success") else 1


def cmd_calendar(args: argparse.Namespace) -> int:
    tools = _build_tools()
    result = asyncio.run(tools["external"].google_calendar_add(
        summary=args.summary,
        start_time=args.start,
        end_time=args.end,
        description=args.description,
        location=args.location,
    ))
    _print_result(result)
    return 0 if result.get("success") else 1


def cmd_pr(args: argparse.Namespace) -> int:
    tools = _build_tools()
    result = asyncio.run(tools["external"].github_create_pr(
        repo_name=args.repo,
        title=args.title,
        body=args.body,
        head_branch=args.head,
        base_branch=args.base,
    ))
    _print_result(result)
    return 0 if result.get("success") else 1


def cmd_demo(args: argparse.Namespace) -> int:
    """端到端离线演示：模拟一个 Agent 用执行工具完成一个真实小任务。

    场景：Agent 需要写一个词频统计脚本、生成样本数据、运行统计、再用 shell
    校验结果。演示同时覆盖四个安全机制：linter 校验、危险命令 fail-safe 审批、
    长输出截断与持久化。整个流程默认离线运行（关闭 LLM 总结）。
    """
    # 演示放在独立临时工作区，避免污染当前目录。
    workspace = tempfile.mkdtemp(prefix="exec_tools_demo_")
    os.environ["WORKSPACE_DIR"] = workspace
    # 离线运行：关闭需要 LLM 的输出总结（截断持久化不依赖 LLM）。
    if "AUTO_SUMMARIZE_COMPLEX_OUTPUT" not in os.environ:
        os.environ["AUTO_SUMMARIZE_COMPLEX_OUTPUT"] = "false"

    tools = _build_tools()
    file_tools = tools["file"]
    exec_tools = tools["exec"]

    def section(title: str) -> None:
        print("\n" + "=" * 64)
        print(title)
        print("=" * 64)

    print(f"演示工作区：{workspace}")
    print("（离线路径，无需 API key；如已配置 key，审批/总结将走真实 LLM）")

    async def run() -> None:
        # 1. 写文件 + 自动 linter 校验（合法代码）
        section("1. file_write：写入词频统计脚本（自动语法校验）")
        script = textwrap.dedent('''\
            """统计文本文件中的词频。"""
            import sys
            from collections import Counter

            def word_count(path):
                with open(path, encoding="utf-8") as f:
                    words = f.read().split()
                return Counter(words)

            if __name__ == "__main__":
                for word, freq in word_count(sys.argv[1]).most_common(5):
                    print(f"{word}\\t{freq}")
            ''')
        r = await file_tools.write_file("wordcount.py", script, overwrite=True)
        print(f"结果：success={r['success']}, verification={r.get('verification')}")
        print(f"写入：{r.get('path')}")

        # 2. linter 拦截语法错误的代码
        section("2. file_write：写入含语法错误的代码（linter 应拦截）")
        broken = "def broken(:\n    return 1\n"
        r = await file_tools.write_file("broken.py", broken, overwrite=True)
        print(f"结果：success={r['success']}")
        print(f"校验反馈：{r.get('error')}")

        # 3. 生成样本数据
        section("3. file_write：生成样本数据文件")
        sample = "apple banana apple cherry banana apple date cherry banana apple\n"
        r = await file_tools.write_file("data.txt", sample, overwrite=True)
        print(f"结果：success={r['success']}，写入 {r.get('bytes_written')} 字节")

        # 4. code_interpreter：运行统计脚本
        section("4. code_interpreter：运行统计逻辑（Python 沙盒）")
        analysis = textwrap.dedent('''\
            from collections import Counter
            text = "apple banana apple cherry banana apple date cherry banana apple"
            for word, freq in Counter(text.split()).most_common(3):
                print(f"{word}: {freq}")
            ''')
        r = await exec_tools.code_interpreter(code=analysis, language="python")
        print(f"结果：success={r['success']}, returncode={r.get('returncode')}")
        print("stdout:")
        print(textwrap.indent(r.get("stdout", ""), "  "))

        # 5. virtual_terminal：用 shell 校验数据文件
        section("5. virtual_terminal：用 shell 校验数据文件")
        r = await exec_tools.virtual_terminal(
            command=f"wc -w {workspace}/data.txt && echo '--- 词数统计完成 ---'"
        )
        print(f"结果：success={r['success']}, returncode={r.get('returncode')}")
        print("stdout:")
        print(textwrap.indent(r.get("stdout", ""), "  "))

        # 6. 长输出截断与持久化（离线，不需 LLM）
        section("6. code_interpreter：长输出自动截断并落盘")
        long_code = "for i in range(1000):\n    print(f'line {i}: ' + 'x' * 20)\n"
        r = await exec_tools.code_interpreter(code=long_code, language="python")
        stdout = r.get("stdout", "")
        print(f"上下文中保留的输出行数：{len(stdout.splitlines())}（原始 1000 行）")
        print(f"完整输出落盘文件：{r.get('stdout_file')}")
        print("上下文中输出的尾部片段：")
        print(textwrap.indent("\n".join(stdout.splitlines()[-4:]), "  "))

        # 7. 危险命令的审批（离线 fail-safe / 在线交由真实 LLM 判断）
        section("7. virtual_terminal：危险命令触发审批")
        os.environ["REQUIRE_APPROVAL_FOR_DANGEROUS_OPS"] = "true"
        # 目标是不存在的临时路径，即便被执行也无副作用。
        danger = await exec_tools.virtual_terminal(
            command="rm -rf /tmp/exec_tools_demo_nonexistent_path_xyz"
        )
        print(f"结果：success={danger['success']}")
        if danger.get("error"):
            print(f"说明：{danger.get('error')}")
            print("（审批未通过：危险命令被拦截、未执行。离线无 LLM 时按 fail-safe 拒绝，"
                  "在线时也可能被真实 LLM 判定为高风险而拒绝。）")
        else:
            print("（审批通过：已配置 API key，真实 LLM 判定该命令针对不存在路径、无副作用而放行。）")

        section("演示完成")
        print("覆盖的安全机制：自动 linter 校验、危险命令审批、长输出截断持久化。")
        print(f"演示产物位于：{workspace}")

    asyncio.run(run())
    return 0


# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="执行工具统一命令行入口（实验 4-3：执行工具 MCP 服务器）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            示例：
              python cli.py list                     列出所有执行工具
              python cli.py demo                     运行端到端离线演示
              python cli.py code --code "print(6*7)"  执行 Python 代码
              python cli.py shell "ls -la"            执行 shell 命令
              python cli.py write --path a.txt --content hi --overwrite
              python cli.py --no-approval shell "echo hello"

            关闭 --no-approval / --no-summarize / --no-verify 后，
            code/shell/write/edit 等命令可完全离线运行，无需 API key。
        """),
    )

    # 全局开关
    parser.add_argument("--provider", help="LLM 提供商（覆盖 PROVIDER，如 kimi/doubao/siliconflow/openrouter）")
    parser.add_argument("--workspace", help="工作目录（覆盖 WORKSPACE_DIR，文件操作被限制在此目录内）")
    parser.add_argument("--no-approval", action="store_true", help="关闭危险操作的 LLM 事前审批")
    parser.add_argument("--no-verify", action="store_true", help="关闭写文件/代码的自动语法校验")
    parser.add_argument("--no-summarize", action="store_true", help="关闭长输出的 LLM 总结（仍会截断持久化）")

    sub = parser.add_subparsers(dest="command", metavar="<子命令>")

    p = sub.add_parser("list", help="列出所有可用的执行工具")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("demo", help="运行端到端离线演示（推荐先看这个）")
    p.set_defaults(func=cmd_demo)

    p = sub.add_parser("code", help="调用 code_interpreter 执行代码")
    p.add_argument("--code", help="要执行的代码字符串")
    p.add_argument("--file", help="从文件读取要执行的代码")
    p.add_argument("--language", default="python",
                   help="编程语言（python/javascript/typescript/go/java/cpp/rust/php/bash，默认 python）")
    p.add_argument("--timeout", type=float, default=30.0, help="执行超时秒数（默认 30）")
    p.add_argument("--stdin", help="可选的标准输入")
    p.set_defaults(func=cmd_code)

    p = sub.add_parser("shell", help="调用 virtual_terminal 执行 shell 命令")
    p.add_argument("command", help="要执行的 shell 命令")
    p.add_argument("--timeout", type=int, default=30, help="超时秒数（默认 30）")
    p.set_defaults(func=cmd_shell)

    p = sub.add_parser("write", help="调用 file_write 写文件")
    p.add_argument("--path", required=True, help="文件路径（相对工作目录或绝对路径）")
    p.add_argument("--content", help="文件内容")
    p.add_argument("--content-file", help="从文件读取要写入的内容")
    p.add_argument("--overwrite", action="store_true", help="允许覆盖已存在文件")
    p.set_defaults(func=cmd_write)

    p = sub.add_parser("edit", help="调用 file_edit 按搜索-替换编辑文件")
    p.add_argument("--path", required=True, help="文件路径")
    p.add_argument("--search", required=True, help="要搜索的文本")
    p.add_argument("--replace", required=True, help="替换文本")
    p.set_defaults(func=cmd_edit)

    p = sub.add_parser("calendar", help="调用 google_calendar_add 创建日历事件（需要凭据）")
    p.add_argument("--summary", required=True, help="事件标题")
    p.add_argument("--start", required=True, help="开始时间（ISO 8601，如 2025-10-01T10:00:00）")
    p.add_argument("--end", required=True, help="结束时间（ISO 8601）")
    p.add_argument("--description", help="事件描述")
    p.add_argument("--location", help="事件地点")
    p.set_defaults(func=cmd_calendar)

    p = sub.add_parser("pr", help="调用 github_create_pr 创建 Pull Request（需要 token）")
    p.add_argument("--repo", required=True, help="仓库名（owner/repo 格式）")
    p.add_argument("--title", required=True, help="PR 标题")
    p.add_argument("--body", required=True, help="PR 描述")
    p.add_argument("--head", required=True, help="源分支")
    p.add_argument("--base", default="main", help="目标分支（默认 main）")
    p.set_defaults(func=cmd_pr)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    _apply_global_env(args)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n已中断。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
