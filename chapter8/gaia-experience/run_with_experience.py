"""
Modified GAIA Runner with Learning from Experience
This script extends the original GAIA runner with experience learning capabilities.
"""

import argparse
import json
import logging
import os
import re
import traceback
from pathlib import Path
from typing import Any, Dict, List
from dotenv import load_dotenv

from llm_env import resolve_llm, DEFAULT_MODEL

# The heavy runtime dependencies (AWorld framework + local experience
# components, which pull in sentence-transformers / faiss) are imported lazily
# via _load_runtime() so that `--help` and argument parsing work even when the
# full stack is not installed. The names below are populated on first run.
AgentConfig = TaskConfig = Task = None
system_prompt = None
add_file_path = load_dataset_meta = question_scorer = report_results = None
ExperienceAgent = KnowledgeBase = TrajectorySummarizer = None


def _load_runtime():
    """Import AWorld and experience components lazily (see note above)."""
    global AgentConfig, TaskConfig, Task, system_prompt
    global add_file_path, load_dataset_meta, question_scorer, report_results
    global ExperienceAgent, KnowledgeBase, TrajectorySummarizer

    from AWorld.aworld.config.conf import AgentConfig as _AgentConfig
    from AWorld.aworld.config.conf import TaskConfig as _TaskConfig
    from AWorld.aworld.core.task import Task as _Task
    from AWorld.examples.gaia.prompt import system_prompt as _system_prompt
    from AWorld.examples.gaia.utils import (
        add_file_path as _add_file_path,
        load_dataset_meta as _load_dataset_meta,
        question_scorer as _question_scorer,
        report_results as _report_results,
    )
    from experience_agent import ExperienceAgent as _ExperienceAgent
    from knowledge_base import KnowledgeBase as _KnowledgeBase
    from trajectory_summarizer import TrajectorySummarizer as _TrajectorySummarizer

    AgentConfig, TaskConfig, Task = _AgentConfig, _TaskConfig, _Task
    system_prompt = _system_prompt
    add_file_path, load_dataset_meta = _add_file_path, _load_dataset_meta
    question_scorer, report_results = _question_scorer, _report_results
    ExperienceAgent = _ExperienceAgent
    KnowledgeBase = _KnowledgeBase
    TrajectorySummarizer = _TrajectorySummarizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """解析命令行参数（Parse command line arguments）。"""
    parser = argparse.ArgumentParser(
        prog="run_with_experience.py",
        description=(
            "在 GAIA 基准上运行带“从经验中学习”能力的 Agent（实验 8-2：经验知识文档）。\n"
            "支持两种模式：学习模式（learning-mode）在任务成功后把轨迹提炼成经验并入库；\n"
            "应用模式（apply-experience）在解题前检索最相似的历史经验注入系统提示词。\n"
            "使用 --compare 可自动做 A/B 对照，直观展示“复用经验是否提升 GAIA 成绩”。"
        ),
        epilog=(
            "示例（Examples）：\n"
            "  # 1) 仅解析参数、查看帮助（无需 API/数据集）\n"
            "  python run_with_experience.py --help\n\n"
            "  # 2) 学习模式：从前 10 道题的成功轨迹中沉淀经验\n"
            "  python run_with_experience.py --learning-mode --start 0 --end 10\n\n"
            "  # 3) 应用模式：用已学到的经验解 10~20 题\n"
            "  python run_with_experience.py --apply-experience --start 10 --end 20\n\n"
            "  # 4) A/B 对照：同一批题分别在“无经验/有经验”下各跑一次并对比准确率\n"
            "  #    （先用 learning-mode 在其它题上积累经验，再在未见过的题上对照，避免数据泄漏）\n"
            "  python run_with_experience.py --compare --start 10 --end 20 \\\n"
            "      --experience-db ./learned_experiences.json\n\n"
            "  # 5) 指定主 Agent 模型与结果输出路径\n"
            "  python run_with_experience.py --apply-experience --model gpt-5.6-luna \\\n"
            "      --output ./results/exp_run.json --start 0 --end 5\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ---- 任务集选择（Task set selection）----
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="数据集起始下标（默认：0）",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=20,
        help="数据集结束下标（不含，默认：20）",
    )
    parser.add_argument(
        "--q",
        type=str,
        help="指定单个题目下标或 task_id；优先级最高，会覆盖 --start/--end",
    )
    parser.add_argument(
        "--skip",
        action="store_true",
        help="若题目此前已处理过则跳过",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="validation",
        help="数据集划分，如 validation、test（默认：validation）",
    )
    parser.add_argument(
        "--blacklist_file_path",
        type=str,
        nargs="?",
        help="黑名单文件路径，如 blacklist.txt（其中的 task_id 会被跳过）",
    )

    # ---- 模型与输出（Model & output）----
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="主 Agent 使用的模型名；缺省时读取环境变量 LLM_MODEL_NAME（默认 gpt-5.6-luna）",
    )
    parser.add_argument(
        "--summary-model",
        type=str,
        default=DEFAULT_MODEL,
        help="用于轨迹总结（经验提炼）的模型（默认：gpt-5.6-luna）",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="用于语义检索的 sentence-transformers 模型（默认：all-MiniLM-L6-v2）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="结果 JSON 输出路径；缺省写入 $AWORLD_WORKSPACE/experience_results.json",
    )

    # ---- 经验学习开关（Experience learning）----
    parser.add_argument(
        "--learning-mode",
        action="store_true",
        help="启用学习模式：捕获成功轨迹并总结为可复用经验",
    )
    parser.add_argument(
        "--apply-experience",
        action="store_true",
        help="启用应用模式：为新任务检索并注入相关历史经验",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="A/B 对照模式：同一批题分别在“无经验/有经验”下各跑一次并对比准确率",
    )
    parser.add_argument(
        "--preload-kb",
        action="store_true",
        help="从 gaia-validation.jsonl 预加载知识库（注意：勿在评测同一批题上预加载，以免泄漏答案）",
    )
    parser.add_argument(
        "--kb-path",
        type=str,
        default="./kb_index",
        help="知识库索引存储路径（默认：./kb_index）",
    )
    parser.add_argument(
        "--experience-db",
        type=str,
        default="./learned_experiences.json",
        help="已学习经验的存储路径（默认：./learned_experiences.json）",
    )
    parser.add_argument(
        "--validation-file",
        type=str,
        default="gaia-validation.jsonl",
        help="用于预加载的 gaia-validation.jsonl 路径",
    )

    return parser.parse_args()


def setup_logging(args):
    """Setup logging configuration."""
    workspace = os.getenv("AWORLD_WORKSPACE", ".")
    os.makedirs(workspace, exist_ok=True)
    
    log_file_name = f"experience_agent_{args.q}.log" if args.q else f"experience_agent_{args.start}_{args.end}.log"
    file_handler = logging.FileHandler(
        os.path.join(workspace, log_file_name),
        mode="a",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    
    logging.getLogger().addHandler(file_handler)


def load_mcp_config(config_path: Path) -> Dict[str, Any]:
    """Load MCP configuration."""
    mcp_config = {}
    available_servers = []
    
    try:
        if config_path.exists():
            with open(config_path, mode="r", encoding="utf-8") as f:
                mcp_config = json.loads(f.read())
                available_servers = list(mcp_config.get("mcpServers", {}).keys())
                logger.info(f"🔧 MCP Available Servers: {available_servers}")
    except json.JSONDecodeError as e:
        logger.error(f"Error loading mcp_collections.json: {e}")
    
    return mcp_config, available_servers


async def run_with_experience(args):
    """Main execution function with experience learning."""
    _load_runtime()

    # Load dataset
    gaia_dataset_path = os.getenv("GAIA_DATASET_PATH", "./gaia_dataset")
    full_dataset = load_dataset_meta(gaia_dataset_path, split=args.split)
    logger.info(f"Total questions: {len(full_dataset)}")
    
    # Load MCP configuration
    mcp_config_path = Path(__file__).parent / "AWorld" / "examples" / "gaia" / "mcp.json"
    mcp_config, available_servers = load_mcp_config(mcp_config_path)
    
    # Setup agent configuration. The main agent model can be overridden via the
    # --model CLI flag; otherwise it falls back to the LLM_MODEL_NAME env var.
    # OpenAI 直连优先，缺 Key 时自动走 OpenRouter 兜底（见 llm_env.resolve_llm）。
    agent_config = AgentConfig(
        **resolve_llm(model_override=args.model),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.0"))
    )
    
    # Initialize knowledge base
    knowledge_base = None
    if args.apply_experience or args.preload_kb:
        logger.info("Initializing knowledge base...")
        knowledge_base = KnowledgeBase(
            index_path=args.kb_path,
            model_name=args.embedding_model
        )
        
        # Preload validation data if requested
        if args.preload_kb and os.path.exists(args.validation_file):
            logger.info(f"Preloading knowledge base from {args.validation_file}")
            knowledge_base.index_gaia_validation(args.validation_file)
            stats = knowledge_base.get_statistics()
            logger.info(f"Knowledge base statistics: {stats}")
    
    # Initialize trajectory summarizer
    summarizer = None
    if args.learning_mode:
        logger.info("Initializing trajectory summarizer...")
        summarizer = TrajectorySummarizer(
            llm_config=agent_config,
            model_name=resolve_llm(model_override=args.summary_model)["llm_model_name"]
        )
    
    # Create experience agent
    experience_agent = ExperienceAgent(
        conf=agent_config,
        name="gaia_experience_agent",
        system_prompt=system_prompt,
        learning_mode=args.learning_mode,
        apply_experience=args.apply_experience,
        experience_db_path=args.experience_db,
        knowledge_base=knowledge_base,
        summarizer=summarizer,
        mcp_config=mcp_config,
        mcp_servers=available_servers,
    )
    
    logger.info(f"Experience Agent initialized:")
    logger.info(f"  - Learning mode: {args.learning_mode}")
    logger.info(f"  - Apply experience: {args.apply_experience}")
    logger.info(f"  - Knowledge base: {'Yes' if knowledge_base else 'No'}")
    logger.info(f"  - Summarizer: {'Yes' if summarizer else 'No'}")
    
    # Load existing results (path overridable via --output)
    results_file = args.output or os.path.join(
        os.getenv("AWORLD_WORKSPACE", "."), "experience_results.json"
    )
    results_dir = os.path.dirname(results_file)
    if results_dir:
        os.makedirs(results_dir, exist_ok=True)
    if os.path.exists(results_file):
        with open(results_file, "r", encoding="utf-8") as f:
            results = json.load(f)
    else:
        results = []
    
    # Load blacklist
    blacklist = set()
    if args.blacklist_file_path and os.path.exists(args.blacklist_file_path):
        with open(args.blacklist_file_path, "r", encoding="utf-8") as f:
            blacklist = set(f.read().splitlines())
    
    try:
        # Determine dataset slice
        if args.q:
            dataset_slice = [
                record for record in full_dataset 
                if record["task_id"] == args.q
            ]
        else:
            dataset_slice = full_dataset[args.start:args.end]
        
        # Process each question
        for i, dataset_i in enumerate(dataset_slice):
            # Check if should skip
            if not args.q:
                if dataset_i["task_id"] in blacklist:
                    logger.info(f"Skipping blacklisted task: {dataset_i['task_id']}")
                    continue
                
                if args.skip and any(
                    result["task_id"] == dataset_i["task_id"]
                    for result in results
                ):
                    logger.info(f"Skipping already processed task: {dataset_i['task_id']}")
                    continue
            
            try:
                # Log task details
                logger.info(f"{'='*60}")
                logger.info(f"Processing task {i+1}/{len(dataset_slice)}: {dataset_i['task_id']}")
                logger.info(f"Question: {dataset_i['Question']}")
                logger.info(f"Level: {dataset_i['Level']}")
                logger.info(f"Tools: {dataset_i['Annotator Metadata']['Tools']}")
                
                # Prepare question with file paths
                question_data = add_file_path(dataset_i, file_path=gaia_dataset_path, split=args.split)
                question = question_data["Question"]
                
                # Create and execute task
                task = Task(
                    input=question,
                    agent=experience_agent,
                    conf=TaskConfig()
                )
                
                # Execute with experience learning/application
                task_response = await experience_agent.execute_task(task)
                
                # Extract answer
                answer = None
                if task_response and task_response.answer:
                    match = re.search(r"<answer>(.*?)</answer>", task_response.answer)
                    if match:
                        answer = match.group(1)
                
                # Evaluate result
                is_correct = False
                if answer:
                    logger.info(f"Agent answer: {answer}")
                    logger.info(f"Correct answer: {dataset_i['Final answer']}")
                    is_correct = question_scorer(answer, dataset_i["Final answer"])
                    
                    if is_correct:
                        logger.info(f"✓ Question {i} Correct!")
                    else:
                        logger.info(f"✗ Incorrect!")
                else:
                    logger.warning("No answer extracted from response")
                
                # Record result
                new_result = {
                    "task_id": dataset_i["task_id"],
                    "level": dataset_i["Level"],
                    "question": question,
                    "answer": dataset_i["Final answer"],
                    "response": answer or "",
                    "is_correct": is_correct,
                    "learning_mode": args.learning_mode,
                    "applied_experience": args.apply_experience
                }
                
                # Update or append result
                existing_index = next(
                    (idx for idx, result in enumerate(results) 
                     if result["task_id"] == dataset_i["task_id"]),
                    None
                )
                
                if existing_index is not None:
                    results[existing_index] = new_result
                else:
                    results.append(new_result)
                
                # Save intermediate results
                with open(results_file, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=4, ensure_ascii=False)
                
            except Exception as e:
                logger.error(f"Error processing task {dataset_i['task_id']}: {e}")
                logger.error(traceback.format_exc())
                continue
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    
    finally:
        # Report final results
        report_results(results)
        
        # Save final results
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        
        # Log experience learning statistics if enabled
        if args.learning_mode:
            num_experiences = len(experience_agent.experiences)
            logger.info(f"\nLearning Statistics:")
            logger.info(f"  - Total experiences learned: {num_experiences}")
            logger.info(f"  - Experience database: {args.experience_db}")
        
        if args.apply_experience and knowledge_base:
            stats = knowledge_base.get_statistics()
            logger.info(f"\nKnowledge Base Statistics:")
            logger.info(f"  - Total indexed documents: {stats['total_documents']}")
            logger.info(f"  - Sources: {stats['sources']}")


async def _evaluate_slice(experience_agent, dataset_slice, gaia_dataset_path, args, pass_label):
    """
    Run one evaluation pass over a dataset slice and return per-task results.

    The agent's ``apply_experience`` flag is read as currently set on the
    ``experience_agent`` instance, which lets the caller toggle experience reuse
    on/off between passes for an apples-to-apples A/B comparison. Correctness is
    computed with GAIA's own ``question_scorer`` — no numbers are fabricated.

    Args:
        experience_agent: The (already constructed) ExperienceAgent.
        dataset_slice: The list of dataset records to evaluate.
        gaia_dataset_path: Root path of the GAIA dataset (for attached files).
        args: Parsed CLI arguments.
        pass_label: Human-readable label for logging (e.g. "baseline").

    Returns:
        A list of per-task result dicts including an ``is_correct`` flag.
    """
    results = []
    for i, dataset_i in enumerate(dataset_slice):
        try:
            logger.info(f"[{pass_label}] Task {i + 1}/{len(dataset_slice)}: {dataset_i['task_id']}")
            question_data = add_file_path(dataset_i, file_path=gaia_dataset_path, split=args.split)
            question = question_data["Question"]

            task = Task(input=question, agent=experience_agent, conf=TaskConfig())
            task_response = await experience_agent.execute_task(task)

            answer = None
            if task_response and task_response.answer:
                match = re.search(r"<answer>(.*?)</answer>", task_response.answer)
                if match:
                    answer = match.group(1)

            is_correct = bool(answer) and question_scorer(answer, dataset_i["Final answer"])
            results.append({
                "task_id": dataset_i["task_id"],
                "level": dataset_i["Level"],
                "question": question,
                "answer": dataset_i["Final answer"],
                "response": answer or "",
                "is_correct": is_correct,
            })
        except Exception as e:
            logger.error(f"[{pass_label}] Error on {dataset_i['task_id']}: {e}")
            results.append({
                "task_id": dataset_i["task_id"],
                "level": dataset_i["Level"],
                "is_correct": False,
                "error": str(e),
            })
    return results


def _accuracy(results):
    """Compute accuracy (correct / total) from a list of result dicts."""
    total = len(results)
    correct = sum(1 for r in results if r.get("is_correct"))
    return correct, total, (correct / total if total else 0.0)


async def run_comparison(args):
    """
    A/B comparison: evaluate the same task slice twice — once WITHOUT experience
    reuse (baseline) and once WITH it — then report the accuracy delta.

    This directly demonstrates the experiment's thesis: reusing accumulated
    experience improves GAIA performance. All reported numbers are computed from
    the actual runs; none are hard-coded.
    """
    _load_runtime()

    gaia_dataset_path = os.getenv("GAIA_DATASET_PATH", "./gaia_dataset")
    full_dataset = load_dataset_meta(gaia_dataset_path, split=args.split)

    mcp_config_path = Path(__file__).parent / "AWorld" / "examples" / "gaia" / "mcp.json"
    mcp_config, available_servers = load_mcp_config(mcp_config_path)

    agent_config = AgentConfig(
        **resolve_llm(model_override=args.model),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
    )

    # Build the experience knowledge base for the "with experience" pass.
    knowledge_base = KnowledgeBase(index_path=args.kb_path, model_name=args.embedding_model)
    if args.preload_kb and os.path.exists(args.validation_file):
        logger.warning(
            "--preload-kb indexes gaia-validation.jsonl; if the evaluated tasks are in "
            "that file this leaks their reference solutions. For a fair comparison, "
            "accumulate experiences from OTHER tasks (via --learning-mode) instead."
        )
        knowledge_base.index_gaia_validation(args.validation_file)

    experience_agent = ExperienceAgent(
        conf=agent_config,
        name="gaia_experience_agent",
        system_prompt=system_prompt,
        learning_mode=False,          # keep both passes clean; learn separately
        apply_experience=False,
        experience_db_path=args.experience_db,
        knowledge_base=knowledge_base,
        summarizer=None,
        mcp_config=mcp_config,
        mcp_servers=available_servers,
    )

    num_learned = len(experience_agent.experiences)
    kb_docs = knowledge_base.get_statistics()["total_documents"]
    logger.info(
        f"Comparison ready: {num_learned} learned experiences, {kb_docs} KB documents available."
    )
    if num_learned == 0 and kb_docs == 0:
        logger.warning(
            "No experiences available to reuse. Run --learning-mode first (or pass "
            "--preload-kb) so the 'with experience' pass has something to retrieve."
        )

    dataset_slice = full_dataset[args.start:args.end]

    # Pass 1: baseline (no experience reuse)
    experience_agent.apply_experience = False
    baseline = await _evaluate_slice(experience_agent, dataset_slice, gaia_dataset_path, args, "baseline")

    # Pass 2: with experience reuse
    experience_agent.apply_experience = True
    with_exp = await _evaluate_slice(experience_agent, dataset_slice, gaia_dataset_path, args, "with-experience")

    b_correct, b_total, b_acc = _accuracy(baseline)
    e_correct, e_total, e_acc = _accuracy(with_exp)

    report = {
        "split": args.split,
        "range": [args.start, args.end],
        "num_learned_experiences": num_learned,
        "kb_documents": kb_docs,
        "baseline": {"correct": b_correct, "total": b_total, "accuracy": b_acc, "results": baseline},
        "with_experience": {"correct": e_correct, "total": e_total, "accuracy": e_acc, "results": with_exp},
        "delta_accuracy": e_acc - b_acc,
    }

    out = args.output or os.path.join(os.getenv("AWORLD_WORKSPACE", "."), "comparison_results.json")
    out_dir = os.path.dirname(out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Console summary (computed from real runs)
    print("\n" + "=" * 60)
    print("A/B COMPARISON: experience reuse vs. baseline")
    print("=" * 60)
    print(f"  Tasks evaluated       : {b_total}  (split={args.split}, range=[{args.start}, {args.end}))")
    print(f"  Reusable experiences  : {num_learned} learned, {kb_docs} preloaded")
    print(f"  Baseline accuracy     : {b_correct}/{b_total} = {b_acc:.1%}")
    print(f"  With-experience acc.  : {e_correct}/{e_total} = {e_acc:.1%}")
    print(f"  Delta (with - base)   : {e_acc - b_acc:+.1%}")
    print(f"  Full report written to: {out}")
    print("=" * 60)


def main():
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()

    # Load environment
    load_dotenv()

    # Setup logging
    setup_logging(args)

    # Log configuration
    logger.info("Starting GAIA with Experience Learning")
    logger.info(f"Configuration:")
    logger.info(f"  - Learning mode: {args.learning_mode}")
    logger.info(f"  - Apply experience: {args.apply_experience}")
    logger.info(f"  - Preload KB: {args.preload_kb}")
    logger.info(f"  - Compare mode: {args.compare}")

    # Run async main
    import asyncio
    if args.compare:
        asyncio.run(run_comparison(args))
    else:
        asyncio.run(run_with_experience(args))


if __name__ == "__main__":
    main()
