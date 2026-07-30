"""
主程序 - Web Search Agent 使用示例

演示第一章的 ReAct 循环（Reasoning + Acting）：模型先思考，再调用 web_search
行动，观察搜索结果后继续思考，直到综合出最终答案。运行时会逐步打印 ReAct 轨迹。
"""

import os
import sys
import json
import argparse
import logging
from typing import Optional
from agent import WebSearchAgent, run_offline_demo
from config import Config

# 设置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)


def _save_output(path: str, payload: dict):
    """把问题、ReAct 轨迹和答案保存为 JSON 文件"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\n💾 结果已保存到: {path}")


def run_interactive_mode(agent: WebSearchAgent, output: Optional[str] = None):
    """
    交互式模式 - 持续与 Agent 对话

    Args:
        agent: WebSearchAgent 实例
        output: 可选，保存每次问答轨迹的 JSON 文件路径
    """
    print("\n" + "="*60)
    print("🤖 Kimi Web Search Agent - 交互模式")
    print("="*60)
    print("输入您的问题，Agent 将自动搜索并回答")
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'clear' 清空对话历史")
    print("="*60 + "\n")

    while True:
        try:
            # 获取用户输入
            user_input = input("您的问题: ").strip()

            # 检查退出命令
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 再见！")
                break

            # 检查清空命令
            if user_input.lower() == 'clear':
                agent.clear_history()
                print("✅ 对话历史已清空\n")
                continue

            # 检查空输入
            if not user_input:
                print("❌ 请输入一个问题\n")
                continue

            # 显示思考中
            print("\n🔍 Agent 正在搜索和思考（ReAct 轨迹如下）...\n")

            # 获取答案（verbose=True 时轨迹已在 agent 内实时打印）
            answer = agent.search_and_answer(user_input, max_iterations=Config.MAX_SEARCH_ITERATIONS)

            # 显示答案
            print("\n" + "="*60)
            print("📝 Agent 回答:")
            print("-"*60)
            print(answer)
            print("="*60 + "\n")

            if output:
                _save_output(output, {"question": user_input,
                                      "trace": agent.get_trace(),
                                      "answer": answer,
                                      "api_turns": agent.get_api_turns(),
                                      "provider": "openrouter" if agent.using_openrouter else "moonshot",
                                      "model": agent.model,
                                      "base_url": agent.base_url})

        except KeyboardInterrupt:
            print("\n\n👋 检测到中断，退出程序")
            break
        except Exception as e:
            logger.error(f"处理问题时出错: {str(e)}")
            print(f"\n❌ 出错了: {str(e)}\n")


def run_single_question(agent: WebSearchAgent, question: str,
                        max_iterations: int, output: Optional[str] = None):
    """
    单个问题模式 - 回答一个问题后退出

    Args:
        agent: WebSearchAgent 实例
        question: 要回答的问题
        max_iterations: 最大 ReAct 迭代次数
        output: 可选，保存轨迹的 JSON 文件路径
    """
    print("\n" + "="*60)
    print("🤖 Kimi Web Search Agent")
    print("="*60)
    print(f"问题: {question}")
    print("-"*60)
    print("🔍 ReAct 轨迹（想 → 做 → 看）:\n")

    try:
        answer = agent.search_and_answer(question, max_iterations=max_iterations)
        print("\n📝 答案:")
        print("-"*60)
        print(answer)
        print("="*60 + "\n")

        if output:
            _save_output(output, {"question": question,
                                  "trace": agent.get_trace(),
                                  "answer": answer,
                                  "api_turns": agent.get_api_turns(),
                                  "provider": "openrouter" if agent.using_openrouter else "moonshot",
                                  "model": agent.model,
                                  "base_url": agent.base_url})
    except Exception as e:
        logger.error(f"处理问题时出错: {str(e)}")
        print(f"\n❌ 出错了: {str(e)}\n")


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器（中文帮助）"""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Kimi Web Search Agent —— 演示 ReAct 循环（思考→行动→观察）的搜索 Agent。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  python main.py                                  # 进入交互模式
  python main.py "2024 诺贝尔物理学奖得主是谁？"    # 单次问答，打印 ReAct 轨迹
  python main.py --provider offline-demo          # 离线演示 ReAct 循环（无需 API Key）
  python main.py "比特币现价" --max-steps 3 --output result.json
""",
    )
    parser.add_argument("query", nargs="*",
                        help="要提问的问题；省略则进入交互模式")
    parser.add_argument("--provider", choices=["kimi", "offline-demo"], default="kimi",
                        help="搜索后端：kimi=调用 Kimi Formula web_search（需 API Key）；"
                             "offline-demo=离线回放示例轨迹（默认 kimi）")
    parser.add_argument("--model", default=Config.DEFAULT_MODEL,
                        help=f"使用的模型名称（默认 {Config.DEFAULT_MODEL}）")
    parser.add_argument("--max-steps", type=int, default=Config.MAX_SEARCH_ITERATIONS,
                        help=f"最大 ReAct 迭代次数（默认 {Config.MAX_SEARCH_ITERATIONS}）")
    parser.add_argument("--base-url", default=Config.KIMI_BASE_URL,
                        help=f"API 基础 URL（默认 {Config.KIMI_BASE_URL}）")
    parser.add_argument("--api-key", default=None,
                        help="Kimi API Key（默认从 MOONSHOT_API_KEY / KIMI_API_KEY 环境变量读取）")
    parser.add_argument("--output", "-o", default=None,
                        help="将问题、ReAct 轨迹和答案保存到指定 JSON 文件")
    parser.add_argument("--quiet", action="store_true",
                        help="不实时打印 ReAct 轨迹（默认打印）")
    return parser


def main(argv: Optional[list] = None):
    """主函数：解析命令行参数并分发到相应模式"""
    parser = build_parser()
    args = parser.parse_args(argv)
    question = " ".join(args.query).strip()

    # 离线演示模式：无需 API Key，回放示例轨迹展示 ReAct 循环
    if args.provider == "offline-demo":
        demo_question = question or "Moonshot AI 的 Context Caching 是什么技术？"
        print("\n" + "="*60)
        print("🧪 离线演示模式（示例轨迹，非真实搜索结果）")
        print("="*60)
        print(f"问题: {demo_question}")
        print("-"*60)
        print("🔍 ReAct 轨迹（想 → 做 → 看）:\n")
        result = run_offline_demo(demo_question, verbose=not args.quiet)
        print("\n📝 答案:")
        print("-"*60)
        print(result["answer"])
        print("="*60 + "\n")
        if args.output:
            _save_output(args.output, result)
        return

    # 在线模式：需要 API Key
    api_key = Config.get_api_key(args.api_key)
    if not api_key and not os.getenv("OPENROUTER_API_KEY"):
        Config.validate()
        print("提示：也可设置 OPENROUTER_API_KEY 作为通用兜底。")
        sys.exit(1)

    # 创建 Agent
    try:
        agent = WebSearchAgent(
            api_key=api_key,
            base_url=args.base_url,
            model=args.model,
            verbose=not args.quiet,
        )
        logger.info("Agent 初始化成功")
    except Exception as e:
        logger.error(f"Agent 初始化失败: {str(e)}")
        sys.exit(1)

    # 有问题则单次问答，否则进入交互模式
    if question:
        run_single_question(agent, question, args.max_steps, args.output)
    else:
        run_interactive_mode(agent, args.output)


if __name__ == "__main__":
    main()
