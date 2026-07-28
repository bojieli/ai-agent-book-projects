"""
Main script to demonstrate KV cache importance
Runs the ReAct agent with different implementations and compares performance
"""

import os
import sys
import glob
import json
import argparse
import logging
from typing import Dict, List, Any
from datetime import datetime
from dataclasses import asdict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from agent import KVCacheAgent, KVCacheMode, AgentMetrics, compare_implementations

# Default model (Moonshot / Kimi). The whole current Kimi family (k2.5/k2.6/
# k2.7/k3) reports cached_tokens for automatic prefix caching AND reasons, so it
# only accepts temperature=1 (agent.py handles that automatically). kimi-k2.6 has
# the lightest reasoning footprint of the cache-reporting models, giving the
# cleanest TTFT while still exposing the prefix-cache hit metric this demo needs.
# (The non-reasoning moonshot-v1-* models do NOT report cached_tokens, so they
# cannot demonstrate the cache effect.)
DEFAULT_MODEL = "kimi-k2.6"
DEFAULT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kv_cache_demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Metrics helpers (shared by live comparison and offline report)
# ---------------------------------------------------------------------------

def _coerce_metrics(metrics: Any) -> Dict[str, Any]:
    """Normalize a stored metrics value into a plain dict.

    Handles both formats found in result files:
      - dict: produced by --compare (asdict) and by the fixed --mode path
      - str : legacy single-mode files that stored repr(AgentMetrics(...))
              because json.dump used default=str
    """
    if isinstance(metrics, dict):
        return metrics
    if isinstance(metrics, str) and metrics.startswith("AgentMetrics("):
        # Safe eval: only AgentMetrics is exposed, no builtins.
        try:
            obj = eval(metrics, {"__builtins__": {}}, {"AgentMetrics": AgentMetrics})
            return asdict(obj)
        except Exception as e:  # pragma: no cover - defensive
            logger.warning(f"Could not parse legacy metrics string: {e}")
    return {}


def _avg_ttft(m: Dict[str, Any]) -> float:
    """Average TTFT across iterations, falling back to first-iteration TTFT."""
    lst = m.get("ttft_per_iteration") or []
    return sum(lst) / len(lst) if lst else float(m.get("ttft", 0.0) or 0.0)


def _hit_rate(m: Dict[str, Any]) -> float:
    total = (m.get("cache_hits", 0) or 0) + (m.get("cache_misses", 0) or 0)
    return (m.get("cache_hits", 0) or 0) / total * 100 if total else 0.0


def _billable_tokens(m: Dict[str, Any], cache_price_ratio: float) -> float:
    """Illustrative billable prompt tokens under a prompt-cache discount.

    cached tokens are charged at cache_price_ratio of the normal price; the
    rest at full price. This is a transparent function of the *measured*
    token counts and a user-supplied ratio - it is not a fabricated
    provider-specific price.
    """
    prompt = m.get("prompt_tokens", 0) or 0
    cached = m.get("cached_tokens", 0) or 0
    cached = min(cached, prompt)
    return (prompt - cached) + cached * cache_price_ratio


def print_comparison_table(results: Dict[str, Any], cache_price_ratio: float = 0.1) -> None:
    """Render the cross-strategy comparison table (latency / cache / cost)."""
    print(f"\n{'Mode':<16} {'Iters':<6} {'1st TTFT':<10} {'Avg TTFT':<10} "
          f"{'Total(s)':<10} {'Prompt':<9} {'Cached':<9} {'Hit%':<7} "
          f"{'Cache%':<8} {'Bill.Tok':<10} {'Save%':<7}")
    print("-" * 112)

    for mode, data in results.items():
        m = _coerce_metrics(data.get("metrics", {}))
        prompt = m.get("prompt_tokens", 0) or 0
        cached = m.get("cached_tokens", 0) or 0
        iters = data.get("iterations", m.get("iterations", 0)) or 0
        cache_pct = cached / prompt * 100 if prompt else 0.0
        billable = _billable_tokens(m, cache_price_ratio)
        save_pct = (prompt - billable) / prompt * 100 if prompt else 0.0

        print(f"{mode:<16} {iters:<6} {float(m.get('ttft', 0.0) or 0.0):<10.3f} "
              f"{_avg_ttft(m):<10.3f} {float(m.get('total_time', 0.0) or 0.0):<10.3f} "
              f"{prompt:<9,} {cached:<9,} {_hit_rate(m):<7.1f} "
              f"{cache_pct:<8.1f} {billable:<10,.0f} {save_pct:<7.1f}")

    print("-" * 112)
    print(f"注：Bill.Tok / Save% 假设缓存 token 按正常价的 {cache_price_ratio:.0%} 计费"
          f"（可用 --cache-price-ratio 调整），仅为成本示意，非某家服务商实际报价。")


def load_result_files(paths: List[str]) -> Dict[str, Any]:
    """Load result_*.json files into a {mode: {...}} dict for offline reporting."""
    results: Dict[str, Any] = {}
    for path in sorted(paths):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            logger.warning(f"Skipping {path}: {e}")
            continue

        # A comparison_*.json holds many modes; a result_*.json holds one.
        if "mode" not in data and all(isinstance(v, dict) and "metrics" in v
                                      for v in data.values()):
            for mode, entry in data.items():
                results[mode] = {"metrics": _coerce_metrics(entry.get("metrics", {})),
                                 "iterations": entry.get("iterations"),
                                 "_source": path}
        else:
            mode = data.get("mode", os.path.splitext(os.path.basename(path))[0])
            results[mode] = {"metrics": _coerce_metrics(data.get("metrics", {})),
                             "iterations": data.get("iterations"),
                             "_source": path}
    return results


def run_report(inputs: List[str] = None, cache_price_ratio: float = 0.1) -> None:
    """Offline: build the comparison table from existing result_*.json files.

    No API key required - reads previously saved runs so the final result is
    legible in one command without re-hitting the model.
    """
    if not inputs:
        inputs = ["result_*.json", "comparison_*.json"]

    paths: List[str] = []
    for item in inputs:
        if os.path.isdir(item):
            paths.extend(glob.glob(os.path.join(item, "result_*.json")))
            paths.extend(glob.glob(os.path.join(item, "comparison_*.json")))
        else:
            paths.extend(glob.glob(item))

    paths = sorted(set(paths))
    if not paths:
        logger.error("未找到任何 result_*.json / comparison_*.json 结果文件。"
                     "请先运行 --mode 或 --compare 生成结果，或用 --input 指定路径。")
        sys.exit(1)

    results = load_result_files(paths)

    print("\n" + "=" * 112)
    print("KV CACHE 离线对比报告（基于已保存的实测结果）")
    print("=" * 112)
    print(f"数据来源（{len(paths)} 个文件）:")
    for mode, data in results.items():
        print(f"  • {mode:<16} ← {os.path.basename(data.get('_source', '?'))}")

    print_comparison_table(results, cache_price_ratio)

    print("\n📝 说明：不同结果文件可能来自不同任务/时间，绝对数值仅供同一次运行内横向对比；"
          "如需严格对照，请用 --compare 在同一任务下一次性生成全部模式的数据。")


def create_summary_task() -> str:
    """Create a task that requires reading multiple files"""
    return """Please analyze and summarize all the projects in the chapter1 and chapter2 directories.
For each project:
1. Find all Python files
2. Read the main files and understand the functionality
3. Identify the key features and purpose
4. Provide a comprehensive summary

Start with chapter1 projects, then move to chapter2. Be thorough in your analysis."""


def run_single_mode(api_key: str, mode: str, task: str = None, root_dir: str = DEFAULT_ROOT_DIR,
                    model: str = DEFAULT_MODEL, output: str = None):
    """
    Run agent in a single mode

    Args:
        api_key: API key for Kimi
        mode: KV cache mode to use
        task: Custom task (optional)
        root_dir: Root directory for file operations (default: "../.." = repository root)
        model: Model to use
        output: Output path for the result JSON (optional; auto-named if omitted)
    """
    # Parse mode
    mode_map = {
        "correct": KVCacheMode.CORRECT,
        "dynamic_system": KVCacheMode.DYNAMIC_SYSTEM,
        "shuffled_tools": KVCacheMode.SHUFFLED_TOOLS,
        "dynamic_profile": KVCacheMode.DYNAMIC_PROFILE,
        "sliding_window": KVCacheMode.SLIDING_WINDOW,
        "text_format": KVCacheMode.TEXT_FORMAT
    }
    
    if mode not in mode_map:
        logger.error(f"Invalid mode: {mode}")
        logger.info(f"Valid modes: {', '.join(mode_map.keys())}")
        return
    
    # Use default task if not provided
    if not task:
        task = create_summary_task()
    
    logger.info(f"Running in mode: {mode}")
    logger.info(f"Task: {task}")
    logger.info("="*80)
    
    # Create agent and execute task
    agent = KVCacheAgent(
        api_key=api_key,
        mode=mode_map[mode],
        model=model,
        root_dir=root_dir,
        verbose=True
    )
    
    result = agent.execute_task(task, max_iterations=30)
    
    # Print results
    print("\n" + "="*80)
    print(f"EXECUTION RESULTS - Mode: {mode}")
    print("="*80)
    
    metrics = result["metrics"]
    print(f"\n📊 Performance Metrics:")
    print(f"  • Time to First Token (TTFT): {metrics.ttft:.3f} seconds")
    
    # Show TTFT progression
    if metrics.ttft_per_iteration:
        print(f"  • TTFT per iteration:")
        for i, ttft in enumerate(metrics.ttft_per_iteration, 1):
            print(f"      Iteration {i}: {ttft:.3f}s")

        # Show improvement
        if len(metrics.ttft_per_iteration) > 1:
            first_ttft = metrics.ttft_per_iteration[0]
            last_ttft = metrics.ttft_per_iteration[-1]
            avg_after_first = sum(metrics.ttft_per_iteration[1:]) / len(metrics.ttft_per_iteration[1:])
            print(f"  • TTFT Analysis:")
            print(f"      First iteration: {first_ttft:.3f}s")
            print(f"      Last iteration: {last_ttft:.3f}s")
            print(f"      Average (after first): {avg_after_first:.3f}s")
            improvement = (first_ttft - last_ttft) / first_ttft * 100
            print(f"      Improvement: {improvement:.1f}%")
    
    print(f"  • Total Execution Time: {metrics.total_time:.3f} seconds")
    print(f"  • Iterations: {result['iterations']}")
    print(f"  • Tool Calls: {len(result['tool_calls'])}")
    
    print(f"\n🔄 Cache Statistics:")
    print(f"  • Cached Tokens: {metrics.cached_tokens:,}")
    print(f"  • Cache Hits: {metrics.cache_hits}")
    print(f"  • Cache Misses: {metrics.cache_misses}")
    if metrics.cache_hits + metrics.cache_misses > 0:
        hit_rate = metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses) * 100
        print(f"  • Cache Hit Rate: {hit_rate:.1f}%")
    
    print(f"\n💰 Token Usage:")
    print(f"  • Prompt Tokens: {metrics.prompt_tokens:,}")
    print(f"  • Completion Tokens: {metrics.completion_tokens:,}")
    print(f"  • Total Tokens: {metrics.prompt_tokens + metrics.completion_tokens:,}")
    if metrics.prompt_tokens > 0:
        cache_ratio = metrics.cached_tokens / metrics.prompt_tokens * 100
        print(f"  • Cache Ratio: {cache_ratio:.1f}% of prompt tokens cached")
    
    # Show tool calls summary
    if result["tool_calls"]:
        print(f"\n🔧 Tool Calls Summary:")
        tool_counts = {}
        for tc in result["tool_calls"]:
            tool_counts[tc.name] = tool_counts.get(tc.name, 0) + 1
        for tool_name, count in tool_counts.items():
            print(f"  • {tool_name}: {count} calls")
    
    # Save detailed results
    output_file = output or f"result_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        # Convert to serializable format. Store metrics as a dict (via asdict)
        # so the file can be re-loaded later by --report; tool calls likewise.
        result_copy = result.copy()
        result_copy["metrics"] = asdict(result["metrics"])
        result_copy["tool_calls"] = [
            {
                "name": tc.name,
                "arguments": tc.arguments,
                "timestamp": tc.timestamp
            }
            for tc in result["tool_calls"]
        ]
        json.dump(result_copy, f, indent=2, default=str)

    print(f"\n💾 Detailed results saved to: {output_file}")


def select_mode_interactive():
    """
    Interactive mode selection menu
    
    Returns:
        Selected mode string or None for all modes
    """
    modes = [
        ("correct", "✅ Correct Implementation - Optimal KV cache usage"),
        ("dynamic_system", "❌ Dynamic System Prompt - Adds timestamps"),
        ("shuffled_tools", "❌ Shuffled Tools - Randomizes tool order"),
        ("dynamic_profile", "❌ Dynamic Profile - Updates user credits"),
        ("sliding_window", "❌ Sliding Window - Keeps only recent messages"),
        ("text_format", "❌ Text Format - Plain text instead of structured"),
        ("compare", "📊 Compare All - Run all modes and compare"),
    ]
    
    print("\n" + "="*60)
    print("KV CACHE DEMONSTRATION - MODE SELECTION")
    print("="*60)
    print("\nSelect a mode to run:\n")
    
    for i, (mode, description) in enumerate(modes, 1):
        print(f"  {i}. {description}")
    
    print("\n  0. Exit")
    print("-"*60)
    
    while True:
        try:
            choice = input("\nEnter your choice (0-7): ").strip()
            choice_num = int(choice)
            
            if choice_num == 0:
                print("Exiting...")
                sys.exit(0)
            elif 1 <= choice_num <= 6:
                selected = modes[choice_num - 1][0]
                print(f"\n✓ Selected: {modes[choice_num - 1][1]}")
                return selected
            elif choice_num == 7:
                print("\n✓ Selected: Compare all modes")
                return "compare"
            else:
                print("Invalid choice. Please enter a number between 0 and 7.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)

def run_comparison(api_key: str, task: str = None, root_dir: str = DEFAULT_ROOT_DIR,
                   model: str = DEFAULT_MODEL, output: str = None,
                   cache_price_ratio: float = 0.1):
    """
    Run comparison across all modes

    Args:
        api_key: API key for Kimi
        task: Custom task (optional)
        root_dir: Root directory for file operations (default: "../.." = repository root)
        model: Model to use for all modes
        output: Output path for the comparison JSON (optional; auto-named if omitted)
        cache_price_ratio: Assumed price of a cached token vs a normal token (cost column)
    """
    # Use default task if not provided
    if not task:
        task = create_summary_task()

    logger.info("Starting KV Cache Comparison Study")
    logger.info(f"Task: {task[:200]}...")
    logger.info("="*80)

    # Run comparison
    results = compare_implementations(api_key, task, root_dir, model=model)

    # Print comparison table
    print("\n" + "="*112)
    print("KV CACHE COMPARISON RESULTS")
    print("="*112)

    print_comparison_table(results, cache_price_ratio)

    # Analyze results
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    # Find best and worst performers
    correct_metrics = results["correct"]["metrics"]
    
    print("\n🏆 Performance Impact (compared to correct implementation):")
    for mode, data in results.items():
        if mode == "correct":
            continue
        
        metrics = data["metrics"]
        ttft_diff = ((metrics["ttft"] - correct_metrics["ttft"]) / correct_metrics["ttft"]) * 100
        total_diff = ((metrics["total_time"] - correct_metrics["total_time"]) / correct_metrics["total_time"]) * 100
        cache_diff = correct_metrics["cached_tokens"] - metrics["cached_tokens"]
        
        print(f"\n{mode}:")
        print(f"  • TTFT: {'+' if ttft_diff > 0 else ''}{ttft_diff:.1f}% "
              f"({'slower' if ttft_diff > 0 else 'faster'})")
        print(f"  • Total Time: {'+' if total_diff > 0 else ''}{total_diff:.1f}% "
              f"({'slower' if total_diff > 0 else 'faster'})")
        print(f"  • Lost Cached Tokens: {cache_diff:,}")
    
    # Show TTFT progression comparison
    print("\n📈 TTFT Progression (first 5 iterations):")
    for mode, data in results.items():
        metrics = data["metrics"]
        ttft_list = metrics.get("ttft_per_iteration", [])[:5]
        if ttft_list:
            ttft_str = " → ".join([f"{t:.2f}s" for t in ttft_list])
            print(f"  {mode:<20}: {ttft_str}")
    
    # Key insights
    print("\n📝 Key Insights:")
    print("  1. The correct implementation maintains stable context for optimal KV cache usage")
    print("  2. TTFT improves dramatically after first iteration when cache is utilized")
    print("  3. Dynamic system prompts invalidate the entire cache on each request")
    print("  4. Shuffling tools breaks cache even though the functionality is identical")
    print("  5. Dynamic user profiles add unnecessary context changes")
    print("  6. Sliding windows may seem to reduce context but actually harm cache efficiency")
    print("  7. Text formatting breaks the structured message format that enables caching")
    
    # Save comparison results
    output_file = output or f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Comparison results saved to: {output_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="KV Cache 实验：用 ReAct Agent 对比不同上下文构造策略对前缀缓存"
                    "（KV Cache / Prompt Cache）命中率、TTFT 延迟与成本的影响。",
        epilog="示例：\n"
               "  python main.py --mode correct                  # 运行单个策略\n"
               "  python main.py --compare                       # 一次跑完所有策略并打印对比表\n"
               "  python main.py --report                        # 离线：读取已有 result_*.json 打印对比表（无需 API Key）\n"
               "  python main.py --mode sliding_window --model kimi-k2.6 --output run.json\n"
               "\n可选策略（--mode）：correct, dynamic_system, shuffled_tools,\n"
               "                      dynamic_profile, sliding_window, text_format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--api-key", type=str,
                        help="Moonshot/Kimi API Key（也可用环境变量 MOONSHOT_API_KEY）")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL,
                        help=f"使用的模型名（默认：{DEFAULT_MODEL}）")
    parser.add_argument("--mode", type=str,
                        help="运行单个策略：correct / dynamic_system / shuffled_tools / "
                             "dynamic_profile / sliding_window / text_format")
    parser.add_argument("--compare", action="store_true",
                        help="依次运行全部策略并打印横向对比表（需要 API Key）")
    parser.add_argument("--report", action="store_true",
                        help="离线模式：从已保存的 result_*.json / comparison_*.json 生成对比表（无需 API Key）")
    parser.add_argument("--input", type=str, nargs="*", default=None,
                        help="配合 --report：指定结果文件、通配符或目录（默认：当前目录下的 result_*.json 与 comparison_*.json）")
    parser.add_argument("--output", type=str,
                        help="结果 JSON 的输出路径（默认按模式和时间戳自动命名）")
    parser.add_argument("--cache-price-ratio", type=float, default=0.1,
                        help="成本估算中缓存 token 相对正常 token 的计费比例（默认：0.1，即缓存读取按一折计），仅作示意")
    parser.add_argument("--task", type=str, help="自定义任务描述（默认：分析并总结项目代码）")
    parser.add_argument("--root-dir", type=str, default=DEFAULT_ROOT_DIR,
                        help="文件工具的根目录（默认：仓库根目录，供 Agent 读取代码）")
    parser.add_argument("--interactive", action="store_true", default=True,
                        help="交互式菜单选择策略（默认开启）")
    parser.add_argument("--no-interactive", dest="interactive", action="store_false",
                        help="关闭交互式菜单")

    args = parser.parse_args()

    # Offline report needs no API key - handle it first.
    if args.report:
        run_report(args.input, args.cache_price_ratio)
        return

    # Get API key. 优先 Moonshot/Kimi 官方 key；缺失时回退到 OPENROUTER_API_KEY
    # （KVCacheAgent 会据此自动切换到 OpenRouter 端点并映射模型名）。
    api_key = (args.api_key or os.getenv("MOONSHOT_API_KEY")
               or os.getenv("KIMI_API_KEY") or os.getenv("OPENROUTER_API_KEY"))
    if not api_key:
        logger.error("请通过 --api-key 或环境变量 MOONSHOT_API_KEY / KIMI_API_KEY / "
                     "OPENROUTER_API_KEY 提供 API Key；"
                     "若只想查看已有结果，可使用 --report（无需 API Key）。")
        sys.exit(1)

    # Run based on mode
    if args.compare:
        # Explicit --compare flag overrides interactive mode
        run_comparison(api_key, args.task, args.root_dir, args.model, args.output,
                       args.cache_price_ratio)
    elif args.mode:
        # Explicit --mode flag overrides interactive mode
        run_single_mode(api_key, args.mode, args.task, args.root_dir, args.model, args.output)
    elif args.interactive and not args.task:
        # Interactive mode selection (default)
        selected_mode = select_mode_interactive()
        if selected_mode == "compare":
            run_comparison(api_key, args.task, args.root_dir, args.model, args.output,
                           args.cache_price_ratio)
        else:
            run_single_mode(api_key, selected_mode, args.task, args.root_dir, args.model, args.output)
    else:
        # If task is provided without mode, ask which mode to use
        if args.task:
            print(f"\n📝 Custom task provided: {args.task}")
            selected_mode = select_mode_interactive()
            if selected_mode == "compare":
                run_comparison(api_key, args.task, args.root_dir, args.model, args.output,
                               args.cache_price_ratio)
            else:
                run_single_mode(api_key, selected_mode, args.task, args.root_dir, args.model, args.output)
        else:
            # Fallback to interactive mode
            selected_mode = select_mode_interactive()
            if selected_mode == "compare":
                run_comparison(api_key, args.task, args.root_dir, args.model, args.output,
                               args.cache_price_ratio)
            else:
                run_single_mode(api_key, selected_mode, args.task, args.root_dir, args.model, args.output)


if __name__ == "__main__":
    main()
