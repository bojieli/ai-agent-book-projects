"""
Main entry point for GPT-5 Native Tools Agent
Interactive CLI for using web_search and code_interpreter tools
"""

import sys
import json
import logging
from typing import Optional
from agent import GPT5NativeAgent, GPT5AgentChain
from config import Config
import argparse

# Set up logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)


class InteractiveCLI:
    """Interactive command-line interface for GPT-5 Agent"""
    
    def __init__(self, backend: str = None, model: str = None):
        """Initialize the CLI"""
        if not Config.validate(backend):
            raise ValueError("Invalid configuration. Please check your .env file")
        api_key, base_url, resolved_model = Config.resolve(backend, model)
        self.agent = GPT5NativeAgent(
            api_key=api_key,
            base_url=base_url,
            model=resolved_model,
        )
        self.backend = backend or Config.BACKEND
        
        self.commands = {
            "/help": self.show_help,
            "/clear": self.clear_history,
            "/history": self.show_history,
            "/tools": self.toggle_tools,
            "/search": self.search_mode,
            "/code": self.code_mode,
            "/analyze": self.analyze_mode,
            "/config": self.show_config,
            "/reasoning": self.set_reasoning_effort,
            "/exit": self.exit_cli,
            "/quit": self.exit_cli,
        }
        
        self.use_tools = True
        self.tool_choice = "auto"
        self.reasoning_effort = "low"  # Default reasoning effort
    
    def show_help(self):
        """Display help information"""
        help_text = """
Commands:                                              
  /help     - Show this help message                    
  /clear    - Clear conversation history                
  /history  - Show conversation history                 
  /tools    - Toggle tools on/off                       
  /search   - Enter web search mode                     
  /code     - Enter code interpreter mode               
  /analyze  - Combined search + analysis mode           
  /config   - Show current configuration                
  /reasoning - Set reasoning effort (low/medium/high)   
  /exit     - Exit the application                      
                                                        
Native Tools:                                           
  • web_search - Search the internet for real-time info 
  • code_interpreter - Execute Python code and analyze  
                                                        
Usage:                                                  
  Simply type your request and the agent will use       
  appropriate tools automatically.                      
                                                        
Examples:                                               
  "东盟 10 国首都之间，距离最近的两个首都是？给出你的详细分析推理过程。"
  "搜索最近一年比特币的价格，计算收益率、最大回撤、年化波动等重要指标"
        """
        print(help_text)
    
    def clear_history(self):
        """Clear conversation history"""
        self.agent.clear_history()
        print("✅ Conversation history cleared")
    
    def show_history(self):
        """Display conversation history"""
        history = self.agent.get_history()
        if not history:
            print("📭 No conversation history")
            return
        
        print("\n" + "="*60)
        print("CONVERSATION HISTORY")
        print("="*60)
        
        for i, msg in enumerate(history, 1):
            role = msg["role"].upper()
            content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
            print(f"\n[{i}] {role}:\n{content}")
        
        print("="*60)
    
    def toggle_tools(self):
        """Toggle tool usage on/off"""
        self.use_tools = not self.use_tools
        status = "enabled" if self.use_tools else "disabled"
        print(f"🔧 Tools {status}")
    
    def search_mode(self):
        """Enter web search mode"""
        print("\n🔍 Web Search Mode")
        print("Enter your search query (or 'back' to return):")
        
        query = input("> ").strip()
        if query.lower() == "back":
            return
        
        request = f"Search the web for: {query}"
        self._process_request(request, force_tools=True)
    
    def code_mode(self):
        """Enter code interpreter mode"""
        print("\n💻 Code Interpreter Mode")
        print("Enter your code or computational request (or 'back' to return):")
        
        request = input("> ").strip()
        if request.lower() == "back":
            return
        
        enhanced_request = f"Use the code interpreter to: {request}"
        self._process_request(enhanced_request, force_tools=True)
    
    def analyze_mode(self):
        """Combined search and analysis mode"""
        print("\n🔬 Search & Analyze Mode")
        print("Enter topic to research and analyze (or 'back' to return):")
        
        topic = input("> ").strip()
        if topic.lower() == "back":
            return
        
        print("\nOptional: Enter Python code for analysis (press Enter to skip):")
        code = input("> ").strip()
        
        if code:
            result = self.agent.search_and_analyze(topic, code)
        else:
            result = self.agent.search_and_analyze(topic)
        
        self._display_result(result)
    
    def show_config(self):
        """Display current configuration"""
        Config.display()
        print(f"\nCurrent Settings:")
        print(f"  Tools Enabled: {self.use_tools}")
        print(f"  Tool Choice: {self.tool_choice}")
        print(f"  Reasoning Effort: {self.reasoning_effort}")
    
    def set_reasoning_effort(self):
        """Set the reasoning effort level"""
        print("\n🧠 Set Reasoning Effort")
        print("Options: low, medium, high")
        print(f"Current: {self.reasoning_effort}")
        
        effort = input("Enter new effort level: ").strip().lower()
        if effort in ["low", "medium", "high"]:
            self.reasoning_effort = effort
            print(f"✅ Reasoning effort set to: {effort}")
        else:
            print(f"❌ Invalid effort level. Must be low, medium, or high")
    
    def exit_cli(self):
        """Exit the application"""
        print("\n👋 Goodbye!")
        sys.exit(0)
    
    def _process_request(self, request: str, force_tools: bool = False):
        """
        Process a user request
        
        Args:
            request: User request
            force_tools: Force tool usage regardless of settings
        """
        use_tools = force_tools or self.use_tools
        
        result = self.agent.process_request(
            request,
            use_tools=use_tools,
            tool_choice=self.tool_choice if use_tools else "none",
            temperature=Config.DEFAULT_TEMPERATURE,
            max_tokens=Config.DEFAULT_MAX_TOKENS,
            reasoning_effort=self.reasoning_effort
        )
        
        self._display_result(result)
    
    def _display_result(self, result: dict):
        """
        Display the result of a request
        
        Args:
            result: Result dictionary from agent
        """
        print("\n" + "="*60)
        
        if result["success"]:
            # Display tool usage
            if result["tool_calls"]:
                print("🔧 Tools Used:")
                for tool in result["tool_calls"]:
                    print(f"  • {tool.get('type', 'unknown_tool')}")
                print()
            
            # Display response
            print("📝 Response:")
            print("-"*60)
            print(result["response"])
            print("-"*60)
            
            # Display token usage
            if result.get("usage"):
                usage = result["usage"]
                total = usage.get("total_tokens", 0)
                if total:
                    print(f"\n📊 Tokens used: {total}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        print("="*60)
    
    def run(self):
        """Run the interactive CLI"""
        print("\n" + "="*60)
        print("     🤖 GPT-5 Native Tools Agent")
        print(f"     Responses API backend: {self.backend}")
        print("="*60)
        
        self.show_help()
        
        while True:
            try:
                print("\n💬 Enter your request (or /help for commands):")
                user_input = input("> ").strip()
                
                if not user_input:
                    continue
                
                # Check for commands
                if user_input.startswith("/"):
                    command = user_input.split()[0].lower()
                    if command in self.commands:
                        self.commands[command]()
                    else:
                        print(f"❌ Unknown command: {command}")
                        print("Type /help for available commands")
                else:
                    # Process as regular request
                    self._process_request(user_input)
                    
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted. Type /exit to quit or continue chatting.")
            except Exception as e:
                logger.error(f"Error: {str(e)}")
                print(f"❌ An error occurred: {str(e)}")


def _run_single(args):
    """执行单次请求（single / dry-run 模式），打印可读轨迹并按需保存结果。"""
    # dry-run 只组装请求体、不联网，因此无需真实 API Key
    api_key, base_url, model = Config.resolve(args.backend, args.model)
    api_key = api_key or ("DRYRUN-PLACEHOLDER" if args.dry_run else "")

    agent = GPT5NativeAgent(
        api_key=api_key,
        base_url=base_url,
        model=model,
    )

    result = agent.process_request(
        args.request,
        use_tools=not args.no_tools,
        temperature=Config.DEFAULT_TEMPERATURE,
        max_tokens=Config.DEFAULT_MAX_TOKENS,
        reasoning_effort=args.reasoning,
        verbosity=args.verbosity,
        dry_run=args.dry_run
    )

    # dry-run：打印将要发送给模型的完整请求体（原生工具定义 + 参数）
    if result.get("dry_run"):
        print("\n" + "=" * 60)
        print("🧪 Dry-run：以下是发送给 GPT-5 的请求体（未联网）")
        print("=" * 60)
        print(f"Model: {result['model']}")
        print(f"任务: {args.request}")
        print("-" * 60)
        print(json.dumps(result["request"], indent=2, ensure_ascii=False))
        print("=" * 60)
    elif result["success"]:
        print("\n" + "=" * 60)
        print("📝 Response:")
        print("-" * 60)
        print(result["response"])
        print("-" * 60)
        usage = result.get("usage") or {}
        if usage:
            print(
                f"📊 Tokens - Input: {usage.get('input_tokens', 'N/A')}, "
                f"Output: {usage.get('output_tokens', 'N/A')}, "
                f"Reasoning: {usage.get('output_tokens_details', {}).get('reasoning_tokens', 0)}, "
                f"Total: {usage.get('total_tokens', 'N/A')}"
            )
        print("=" * 60)
    else:
        print(f"❌ Error: {result.get('error')}")

    # 按需将完整结果（含轨迹/请求体）保存为 JSON，便于复盘
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 结果已保存到: {args.output}")

    if not result["success"]:
        sys.exit(1)


def main():
    """主入口：解析命令行参数并分派到交互 / 单次 / 测试模式。"""
    parser = argparse.ArgumentParser(
        description="GPT-5 原生工具 Agent —— 演示实验 1.3：网络搜索 + 代码解释器的原生 Deep Research 能力",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例：
  python main.py                                    # 交互模式（默认）
  python main.py --mode single --request "东盟 10 国首都之间距离最近的两个首都是？"
  python main.py --mode single --request "分析比特币近一月走势" --reasoning high --verbosity high
  python main.py --mode single --request "..." --output result.json
  python main.py --dry-run --request "..."          # 离线查看请求体（原生工具定义），无需 API Key
  python main.py --mode test --test basic           # 运行指定联网手动用例
""",
    )

    parser.add_argument(
        "--mode",
        choices=["interactive", "single", "test"],
        default="interactive",
        help="运行模式：interactive 交互对话（默认）/ single 单次请求 / test 联网手动用例",
    )
    parser.add_argument(
        "--request",
        type=str,
        help="single / dry-run 模式下的任务或查询内容",
    )
    parser.add_argument(
        "--backend",
        choices=["openai", "openrouter", "dashscope"],
        default=Config.BACKEND,
        help="Responses API backend; openai is the exact canonical path, dashscope is the eligible equivalent-provider path",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help=f"覆盖模型名称（默认取配置 {Config.MODEL_NAME}）",
    )
    parser.add_argument(
        "--reasoning",
        choices=["none", "low", "medium", "high", "xhigh", "max"],
        default="low",
        help="推理力度 Reasoning Effort（low/medium/high，默认 low）",
    )
    parser.add_argument(
        "--verbosity",
        choices=["low", "medium", "high"],
        default=None,
        help="输出详略程度 Verbosity（low/medium/high，默认跟随模型）",
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="禁用原生工具（web_search / code_interpreter）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="将完整结果（含轨迹 / 请求体）保存为 JSON 文件的路径",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="离线组装并打印请求体（含原生工具定义），不调用 API、无需 API Key",
    )
    parser.add_argument(
        "--test",
        type=str,
        help="test 模式下运行指定联网手动用例（basic/analysis/complex/code/reasoning/search_analyze/chain）",
    )

    args = parser.parse_args()

    # dry-run：离线路径，跳过 API Key 校验
    if args.dry_run:
        if not args.request:
            print("❌ --dry-run 需要配合 --request 使用")
            sys.exit(1)
        _run_single(args)
        return

    # 其余模式需要有效配置
    if not Config.validate(args.backend):
        print("❌ 配置错误！")
        print("请配置所选 backend 对应的 OPENAI_API_KEY / OPENROUTER_API_KEY / DASHSCOPE_API_KEY")
        print("\n示例 .env：")
        print("DASHSCOPE_API_KEY=your-dashscope-api-key")
        sys.exit(1)

    if args.mode == "interactive":
        cli = InteractiveCLI(args.backend, args.model)
        cli.run()

    elif args.mode == "single":
        if not args.request:
            print("❌ single 模式需要 --request 参数")
            sys.exit(1)
        _run_single(args)

    elif args.mode == "test":
        from tests.manual.agent_cases import TestGPT5Agent, run_single_test

        if args.test:
            run_single_test(args.test)
        else:
            tester = TestGPT5Agent()
            tester.run_all_tests()


if __name__ == "__main__":
    main()
