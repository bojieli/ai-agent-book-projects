"""
阶段化系统提示词附加项目 演示入口：一条命令跑通“需求澄清 -> 代码实现 -> 代码审查”三阶段。

    python demo.py                 # 默认任务、默认模型、最多 3 次审查回退
    python demo.py --list-stages   # 离线查看三阶段配置（无需 API Key）
    python demo.py --help          # 查看全部可选参数

演示任务：用户想要“写一个整理下载文件夹的 Python 脚本”。
需求本身模糊，因此需求澄清阶段的 Agent 会主动提问，由模拟用户自动回答；
之后进入实现阶段写代码、审查阶段严格把关（可能回退重写）。
"""

import argparse

from agent import StagedAgent, stage_overview
from config import Config


USER_TASK = "帮我写一个整理下载文件夹的 Python 脚本。"
DEFAULT_MAX_REVISIONS = 3


def parse_args() -> argparse.Namespace:
    """解析命令行参数。不传任何参数时，行为与原始固定脚本完全一致。"""
    parser = argparse.ArgumentParser(
        prog="demo.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "阶段化系统提示词附加项目：阶段化系统提示词（需求澄清 -> 代码实现 -> 代码审查）演示。\n"
            "同一个 Agent 在三个阶段切换系统提示词与工具集，扮演不同角色，\n"
            "而对话历史与任务状态跨阶段连续共享。不加参数运行即为默认演示。"
        ),
        epilog=(
            "示例：\n"
            "  python demo.py                        默认任务，跑通三阶段\n"
            "  python demo.py --list-stages          离线查看三阶段配置（无需 API Key）\n"
            "  python demo.py --start-stage implementation   跳过需求澄清，从实现阶段起步\n"
            "  python demo.py --interactive          需求澄清阶段由你本人回答提问\n"
            "  python demo.py --model gpt-5.6-luna --task '写一个批量重命名图片的脚本'"
        ),
    )
    parser.add_argument(
        "--task",
        default=USER_TASK,
        help=f"交给 Agent 的用户任务（默认：{USER_TASK!r}）",
    )
    parser.add_argument(
        "--start-stage",
        choices=["requirements", "implementation"],
        default="requirements",
        help=(
            "从哪个阶段开始（默认：requirements）。选 implementation 会预置一份"
            "等价于需求澄清产物的已确认需求、直接从实现阶段起步，便于单独调试后两个阶段。"
            "（review 阶段依赖实现阶段产出的代码，无法作为起点。）"
        ),
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="需求澄清阶段改由真人从标准输入回答 Agent 的提问（默认用模拟用户自动回答）。",
    )
    parser.add_argument(
        "--max-revisions",
        type=int,
        default=DEFAULT_MAX_REVISIONS,
        help=f"审查阶段允许的最大回退次数，超过则强制结束演示（默认：{DEFAULT_MAX_REVISIONS}）",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"覆盖 OPENAI_MODEL 环境变量指定的模型名（默认：使用环境变量，当前为 {Config.MODEL!r}）",
    )
    parser.add_argument(
        "--list-stages",
        action="store_true",
        help="离线打印三阶段（角色/系统提示词/工具集/转换信号）后退出，不调用任何 API。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 离线路径：只展示三阶段配置，不需要 API Key，也不发起任何请求。
    if args.list_stages:
        print(stage_overview())
        return

    if args.model:
        Config.MODEL = args.model

    # 先解析 provider（含 OpenRouter 回退），确保打印出的模型/端点是最终生效值。
    Config.validate()
    print("模型：%s  | base_url：%s" % (Config.MODEL, Config.BASE_URL))
    agent = StagedAgent(
        max_revisions=args.max_revisions,
        verbose=True,
        interactive=args.interactive,
    )
    agent.run(args.task, start_stage=args.start_stage)
    agent.print_summary()

    # 打印最终产出的主文件，方便肉眼确认实现阶段真的写了代码
    if agent.workspace.files:
        print("\n" + "=" * 70)
        print("最终产出文件内容：")
        print("=" * 70)
        for path, content in agent.workspace.files.items():
            print(f"\n--- {path} ---\n{content}")


if __name__ == "__main__":
    main()
