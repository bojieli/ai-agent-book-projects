"""
Demo: Email sending with learning capability

This demo shows how the agent learns to send emails and reuses the learned workflow.
Uses Ethereal Email (ethereal.email) as a test email service.
"""

import argparse
import asyncio
import json
import logging
import time
from dotenv import load_dotenv

from browser_use import ChatOpenAI, ChatGoogle
from learning_agent import LearningAgent
from llm_factory import make_llm, DEFAULT_MODEL


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()


# Default two-phase tasks. Phase 1 teaches the workflow from scratch (expensive,
# multimodal LLM loop); Phase 2 replays it with different parameters (cheap, no LLM).
DEFAULT_LEARNING_TASK = """
Go to https://ethereal.email and send a test email with:
- To: test@example.com
- Subject: Hello from Learning Agent
- Message: This is a test email sent by the learning agent. The workflow will be captured for future reuse.
"""

DEFAULT_REPLAY_TASK = """
Send an email to another@example.com with subject "Workflow Test"
and message "This email is sent using a learned workflow. No LLM calls needed!"
"""


class EmailDemo:
    """Demo for email sending with learning capability."""
    
    def __init__(self, llm_model=DEFAULT_MODEL, knowledge_base_path="./email_knowledge",
                 headless=False, max_steps=20, learning_task=None, replay_task=None,
                 output_path=None):
        self.llm_model = llm_model
        self.knowledge_base_path = knowledge_base_path
        self.headless = headless
        self.max_steps = max_steps
        self.learning_task = learning_task or DEFAULT_LEARNING_TASK
        self.replay_task = replay_task or DEFAULT_REPLAY_TASK
        self.output_path = output_path

    async def run_full_demo(self):
        """Run complete email demo with learning and replay phases."""
        
        print("=" * 80)
        print("EMAIL SENDING DEMO - LEARNING AGENT")
        print("=" * 80)
        print("\nThis demo uses Ethereal Email (ethereal.email) for testing.")
        print("Note: This is a test service - emails won't actually be delivered.")
        print("=" * 80)
        
        # Phase 1: Learning
        await self.phase1_learning()
        
        # Wait before Phase 2
        print("\n⏳ Waiting 5 seconds before replay phase...")
        await asyncio.sleep(5)
        
        # Phase 2: Replay
        await self.phase2_replay()
        
        # Phase 3: Statistics
        self.show_statistics()

        # Optionally persist the before/after comparison for later analysis
        if self.output_path:
            self.save_results()

    async def phase1_learning(self):
        """Phase 1: Learn how to send an email."""
        
        print("\n" + "📚 PHASE 1: LEARNING - First Email Task ".ljust(70, "="))
        print("\nThe agent will learn how to send an email from scratch.")
        print("This requires multiple LLM calls to explore and understand the interface.")
        print("-" * 70)
        
        # Task with specific details
        task = self.learning_task

        print(f"Task: {task.strip()}")
        print("Expected behavior:")
        print("  1. Navigate to Ethereal Email")
        print("  2. Create a test account (if needed)")
        print("  3. Compose and send the email")
        print("  4. Capture workflow for future reuse")
        
        # Create learning agent
        agent = LearningAgent(
            task=task,
            llm=self._get_llm(),
            knowledge_base_path=self.knowledge_base_path,
            headless=self.headless
        )

        print("\n🚀 Starting learning phase...")
        start_time = time.time()
        
        try:
            result = await agent.run(max_steps=self.max_steps)

            elapsed = time.time() - start_time

            print("\n✅ Learning phase completed!")
            print(f"  📊 Results:")
            print(f"     - Success: {'✓' if result['success'] else '✗'}")
            print(f"     - Execution time: {elapsed:.2f} seconds")
            print(f"     - LLM calls made: {result['llm_calls']}")
            print(f"     - Workflow captured: {'Yes' if result['success'] else 'No'}")
            
            if result['success']:
                print("\n  💡 Workflow successfully learned and saved!")
                print("     The agent can now repeat similar tasks without LLM calls.")
            
            # Store metrics for comparison
            self.learning_metrics = {
                'time': elapsed,
                'llm_calls': result['llm_calls'],
                'success': result['success']
            }
            
        except Exception as e:
            print(f"\n❌ Learning phase failed: {e}")
            self.learning_metrics = {'time': 0, 'llm_calls': 0, 'success': False}
    
    async def phase2_replay(self):
        """Phase 2: Replay learned workflow with different parameters."""
        
        print("\n" + "🚀 PHASE 2: REPLAY - Second Email Task ".ljust(70, "="))
        print("\nThe agent will reuse the learned workflow with different parameters.")
        print("This should be much faster and require NO LLM calls.")
        print("-" * 70)
        
        # Different email parameters
        task = self.replay_task

        print(f"Task: {task.strip()}")
        print("Expected behavior:")
        print("  1. Match task to learned workflow")
        print("  2. Extract new parameters (recipient, subject, message)")
        print("  3. Replay workflow with new parameters")
        print("  4. Complete task without any LLM calls")
        
        # Create agent for replay
        agent = LearningAgent(
            task=task,
            llm=self._get_llm(),
            knowledge_base_path=self.knowledge_base_path,
            headless=self.headless
        )

        print("\n🔄 Starting replay phase...")
        start_time = time.time()
        
        try:
            result = await agent.run(max_steps=self.max_steps)

            elapsed = time.time() - start_time

            print("\n✅ Replay phase completed!")
            print(f"  📊 Results:")
            print(f"     - Success: {'✓' if result['success'] else '✗'}")
            print(f"     - Execution time: {elapsed:.2f} seconds")
            print(f"     - Workflow reused: {'Yes' if result['replay_used'] else 'No'}")
            
            if result['replay_used']:
                # Calculate improvements
                if hasattr(self, 'learning_metrics') and self.learning_metrics['success']:
                    speedup = self.learning_metrics['time'] / elapsed
                    calls_saved = self.learning_metrics['llm_calls']
                    
                    print(f"\n  🎯 Performance Improvements:")
                    print(f"     - Speed: {speedup:.1f}x faster")
                    print(f"     - LLM calls saved: {calls_saved}")
                    print(f"     - Time saved: {self.learning_metrics['time'] - elapsed:.1f} seconds")
            else:
                print(f"     - LLM calls made: {result.get('llm_calls', 0)}")
                print("\n  ⚠️ Workflow was not reused. Task may be too different.")
            
            # Store replay metrics
            self.replay_metrics = {
                'time': elapsed,
                'replay_used': result['replay_used'],
                'success': result['success']
            }
            
        except Exception as e:
            print(f"\n❌ Replay phase failed: {e}")
            self.replay_metrics = {'time': 0, 'replay_used': False, 'success': False}
    
    def show_statistics(self):
        """Show knowledge base statistics."""
        
        print("\n" + "📊 KNOWLEDGE BASE STATISTICS ".ljust(70, "="))
        
        from learning_agent import KnowledgeBase
        kb = KnowledgeBase(self.knowledge_base_path)
        stats = kb.get_statistics()
        
        print("\n  Current Knowledge Base Status:")
        for key, value in stats.items():
            formatted_key = key.replace('_', ' ').title()
            print(f"     - {formatted_key}: {value}")
        
        # Show comparison if both phases completed
        if hasattr(self, 'learning_metrics') and hasattr(self, 'replay_metrics'):
            if self.learning_metrics['success'] and self.replay_metrics['replay_used']:
                print("\n  📈 Performance Comparison:")
                print(f"     Phase 1 (Learning):")
                print(f"        - Time: {self.learning_metrics['time']:.2f}s")
                print(f"        - LLM Calls: {self.learning_metrics['llm_calls']}")
                print(f"     Phase 2 (Replay):")
                print(f"        - Time: {self.replay_metrics['time']:.2f}s")
                print(f"        - LLM Calls: 0")
                
                improvement = (1 - self.replay_metrics['time'] / self.learning_metrics['time']) * 100
                print(f"\n     🚀 Overall Improvement: {improvement:.0f}% faster with replay!")
        
        print("\n" + "=" * 70)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 70)
    
    def save_results(self):
        """Persist learning/replay metrics and KB stats to a JSON file."""
        from learning_agent import KnowledgeBase

        kb = KnowledgeBase(self.knowledge_base_path)
        payload = {
            'model': self.llm_model,
            'knowledge_base_path': self.knowledge_base_path,
            'headless': self.headless,
            'max_steps': self.max_steps,
            'learning_task': self.learning_task.strip(),
            'replay_task': self.replay_task.strip(),
            'learning_metrics': getattr(self, 'learning_metrics', None),
            'replay_metrics': getattr(self, 'replay_metrics', None),
            'knowledge_base_stats': kb.get_statistics(),
        }

        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Results saved to: {self.output_path}")

    def _get_llm(self):
        """Get LLM instance based on configuration (OpenAI 直连，缺 Key 时 OpenRouter 兜底)。"""
        return make_llm(self.llm_model)


async def quick_test(model=DEFAULT_MODEL, headless=False, max_steps=15,
                     knowledge_base_path="./test_knowledge", task=None):
    """Quick test with a single simple task (no replay comparison)."""
    print("\n🧪 QUICK TEST - Simple Email Task")
    print("-" * 40)

    task = task or "Go to ethereal.email and send a test email to demo@test.com"

    llm = make_llm(model)
    agent = LearningAgent(
        task=task,
        llm=llm,
        knowledge_base_path=knowledge_base_path,
        headless=headless
    )

    print(f"Task: {task}")
    result = await agent.run(max_steps=max_steps)

    print(f"\nResult: {'Success' if result['success'] else 'Failed'}")
    print(f"Time: {result['execution_time']:.2f}s")
    print(f"LLM calls: {result.get('llm_calls', 0)}")


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器（RPA 邮件学习/回放演示）。"""
    parser = argparse.ArgumentParser(
        prog="demo_email.py",
        description=(
            "browser-use RPA 演示：学习一次「发送邮件」工作流，之后用不同参数高速回放。\n"
            "第一阶段（学习）通过多模态大模型逐步探索并录制工作流；\n"
            "第二阶段（回放）直接复用工作流、无需再调用大模型，对比耗时与调用次数。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python demo_email.py                       # 运行完整的「学习→回放」对比演示\n"
            "  python demo_email.py --quick               # 只跑一次简单任务，快速冒烟测试\n"
            "  python demo_email.py --model gemini-2.0-flash-exp --headless\n"
            "  python demo_email.py --task '给 a@b.com 发主题为\"报告\"的邮件' \\\n"
            "                       --replay-task '给 c@d.com 发主题为\"周报\"的邮件' \\\n"
            "                       --output results.json\n"
        ),
    )
    parser.add_argument(
        "--task", default=None,
        help="学习阶段的任务描述（默认：向 test@example.com 发送测试邮件）",
    )
    parser.add_argument(
        "--replay-task", default=None,
        help="回放阶段的任务描述，参数不同但流程相同（默认：向 another@example.com 发送邮件）",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help="使用的大模型，gpt-* 走 OpenAI（缺 Key 时走 OpenRouter 兜底），"
             "gemini-* 走 Google（默认：gpt-5.6-luna）",
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="以无界面（headless）模式运行浏览器（默认：显示浏览器窗口）",
    )
    parser.add_argument(
        "--knowledge-base", default="./email_knowledge", metavar="PATH",
        help="工作流知识库的存储目录（默认：./email_knowledge）",
    )
    parser.add_argument(
        "--max-steps", type=int, default=20, metavar="N",
        help="学习阶段允许的最大操作步数（默认：20）",
    )
    parser.add_argument(
        "--output", default=None, metavar="PATH",
        help="将学习/回放的指标对比与知识库统计写入指定 JSON 文件",
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="快速冒烟测试：只运行一次简单任务，不做学习/回放对比",
    )
    return parser


def main():
    """Main entry point."""
    args = build_parser().parse_args()

    if args.quick:
        # Run quick test (single task, no replay comparison)
        asyncio.run(quick_test(
            model=args.model,
            headless=args.headless,
            max_steps=args.max_steps,
            knowledge_base_path=args.knowledge_base,
            task=args.task,
        ))
    else:
        # Run full learning + replay demo
        demo = EmailDemo(
            llm_model=args.model,
            knowledge_base_path=args.knowledge_base,
            headless=args.headless,
            max_steps=args.max_steps,
            learning_task=args.task,
            replay_task=args.replay_task,
            output_path=args.output,
        )
        asyncio.run(demo.run_full_demo())


if __name__ == "__main__":
    main()
