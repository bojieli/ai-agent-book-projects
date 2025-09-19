#!/usr/bin/env python3
"""
Ablation Study Runner for Tau-Bench Framework
Demonstrates the importance of prompt engineering by testing different variations:
1. Tone variations (Trump style, Casual style, Default style)
2. Wiki rule randomization
3. Tool description removal
"""

import argparse
import random
import os
import json
from datetime import datetime
from tau_bench.types import RunConfig
# from litellm import provider_list  # This returns enums, not strings
# Define provider choices as strings
provider_list = ["openai", "anthropic", "azure", "bedrock", "cohere", "gemini", "groq", "mistral", "ollama", "openrouter", "replicate", "together_ai", "vertex_ai", "huggingface"]
from tau_bench.envs.user import UserStrategy

# Import custom modules for ablation
from ablation_utils import (
    apply_tone_modification,
    load_randomized_wiki, 
    remove_tool_descriptions,
    ToneStyle
)


def parse_args():
    parser = argparse.ArgumentParser(description="Run Tau-Bench with ablation study options")
    
    # Original arguments
    parser.add_argument("--num-trials", type=int, default=1)
    parser.add_argument(
        "--env", type=str, choices=["retail", "airline"], default="airline",
        help="Environment to run (default: airline for demonstration)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="openai/gpt-5",
        help="The model to use for the agent (default: openai/gpt-5)",
    )
    parser.add_argument(
        "--model-provider",
        type=str,
        choices=provider_list,
        default=None,  # Will be set based on model
        help="The model provider for the agent (default: openrouter for openai/gpt-5)",
    )
    parser.add_argument(
        "--user-model",
        type=str,
        default="openai/gpt-5",
        help="The model to use for the user simulator (default: openai/gpt-5)",
    )
    parser.add_argument(
        "--user-model-provider",
        type=str,
        choices=provider_list,
        default=None,  # Will be set based on model
        help="The model provider for the user simulator (default: openrouter for openai/gpt-5)",
    )
    parser.add_argument(
        "--agent-strategy",
        type=str,
        default="tool-calling",
        choices=["tool-calling", "act", "react", "few-shot"],
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help="The sampling temperature for the action model (default: 1.0 for gpt-5 compatibility)",
    )
    parser.add_argument(
        "--task-split",
        type=str,
        default="test",
        choices=["train", "test", "dev"],
    )
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int, default=-1)
    parser.add_argument("--task-ids", type=int, nargs="+")
    parser.add_argument("--log-dir", type=str, default="results_ablation")
    parser.add_argument("--max-concurrency", type=int, default=1)
    parser.add_argument("--seed", type=int, default=10)
    parser.add_argument("--shuffle", type=int, default=0)
    parser.add_argument(
        "--user-strategy", 
        type=str, 
        default="llm", 
        choices=[item.value for item in UserStrategy]
    )
    parser.add_argument("--few-shot-displays-path", type=str)
    
    # New ablation study arguments
    parser.add_argument(
        "--tone-style",
        type=str,
        choices=["default", "trump", "casual"],
        default="default",
        help="Tone style for the agent: default (neutral), trump (Donald Trump style), or casual (fun with emojis)"
    )
    
    parser.add_argument(
        "--randomize-wiki",
        action="store_true",
        help="Randomize the order of rules in wiki.md"
    )
    
    parser.add_argument(
        "--remove-tool-descriptions",
        action="store_true",
        help="Remove all tool and parameter descriptions"
    )
    
    parser.add_argument(
        "--ablation-name",
        type=str,
        default="",
        help="Custom name for this ablation experiment"
    )
    
    parser.add_argument(
        "--no-verbose",
        action="store_true",
        help="Disable verbose output (default: verbose is enabled)"
    )
    
    args = parser.parse_args()
    
    # Set verbose flag (defaults to True unless --no-verbose is used)
    args.verbose = not args.no_verbose
    
    # Set default provider based on model if not specified
    if args.model_provider is None:
        if args.model == "openai/gpt-5":
            args.model_provider = "openrouter"
        else:
            args.model_provider = "openai"
    
    # Set default user model provider based on user model if not specified
    if args.user_model_provider is None:
        if args.user_model == "openai/gpt-5":
            args.user_model_provider = "openrouter"
        else:
            args.user_model_provider = "openai"
    
    return args


def run_with_ablation(args):
    """Run tau-bench with ablation modifications"""
    
    # Import the original run module
    from tau_bench.run import run, agent_factory, display_metrics
    from tau_bench.envs import get_env
    import multiprocessing
    from concurrent.futures import ThreadPoolExecutor
    from typing import List
    from tau_bench.types import EnvRunResult
    
    # Create configuration
    config = RunConfig(
        model_provider=args.model_provider,
        user_model_provider=args.user_model_provider,
        model=args.model,
        user_model=args.user_model,
        num_trials=args.num_trials,
        env=args.env,
        agent_strategy=args.agent_strategy,
        temperature=args.temperature,
        task_split=args.task_split,
        start_index=args.start_index,
        end_index=args.end_index,
        task_ids=args.task_ids,
        log_dir=args.log_dir,
        max_concurrency=args.max_concurrency,
        seed=args.seed,
        shuffle=args.shuffle,
        user_strategy=args.user_strategy,
        few_shot_displays_path=args.few_shot_displays_path,
    )
    
    random.seed(config.seed)
    
    # Create descriptive log filename
    ablation_suffix = []
    if args.tone_style != "default":
        ablation_suffix.append(f"tone_{args.tone_style}")
    if args.randomize_wiki:
        ablation_suffix.append("wiki_random")
    if args.remove_tool_descriptions:
        ablation_suffix.append("no_tool_desc")
    if args.ablation_name:
        ablation_suffix.append(args.ablation_name)
    
    ablation_str = "_".join(ablation_suffix) if ablation_suffix else "baseline"
    
    time_str = datetime.now().strftime("%m%d%H%M%S")
    ckpt_path = f"{config.log_dir}/{config.agent_strategy}-{config.model.split('/')[-1]}-{ablation_str}_{time_str}.json"
    
    if not os.path.exists(config.log_dir):
        os.makedirs(config.log_dir)
    
    print(f"🔬 Running Ablation Study: {ablation_str}")
    print(f"  - Tone Style: {args.tone_style}")
    print(f"  - Randomize Wiki: {args.randomize_wiki}")
    print(f"  - Remove Tool Descriptions: {args.remove_tool_descriptions}")
    print(f"  - Checkpoint: {ckpt_path}")
    print()
    
    # Load environment
    env = get_env(
        config.env,
        user_strategy=config.user_strategy,
        user_model=config.user_model,
        user_provider=config.user_model_provider,
        task_split=config.task_split,
    )
    
    # Apply ablation modifications
    modified_wiki = env.wiki
    modified_tools_info = env.tools_info
    
    # 1. Apply wiki randomization if requested
    if args.randomize_wiki:
        print("📝 Using pre-randomized wiki rules...")
        modified_wiki = load_randomized_wiki(config.env)
    
    # 2. Apply tone modification if requested
    if args.tone_style != "default":
        print(f"🎭 Applying {args.tone_style} tone style to system prompt...")
        tone_style = ToneStyle[args.tone_style.upper()]
        modified_wiki = apply_tone_modification(modified_wiki, tone_style)
    
    # 3. Remove tool descriptions if requested
    if args.remove_tool_descriptions:
        print("🔧 Removing tool descriptions...")
        modified_tools_info = remove_tool_descriptions(modified_tools_info)
    
    # Create agent with modifications
    from ablation_agent import AblationAgent
    
    agent = AblationAgent(
        tools_info=modified_tools_info,
        wiki=modified_wiki,
        model=config.model,
        provider=config.model_provider,
        temperature=config.temperature,
        verbose=args.verbose
    )
    
    # Run tasks
    end_index = (
        len(env.tasks) if config.end_index == -1 else min(config.end_index, len(env.tasks))
    )
    results: List[EnvRunResult] = []
    lock = multiprocessing.Lock()
    
    if config.task_ids and len(config.task_ids) > 0:
        print(f"Running tasks {config.task_ids}")
    else:
        print(f"Running tasks {config.start_index} to {end_index}")
    
    for i in range(config.num_trials):
        if config.task_ids and len(config.task_ids) > 0:
            idxs = config.task_ids
        else:
            idxs = list(range(config.start_index, end_index))
        if config.shuffle:
            random.shuffle(idxs)
        
        def _run(idx: int) -> EnvRunResult:
            isolated_env = get_env(
                config.env,
                user_strategy=config.user_strategy,
                user_model=config.user_model,
                task_split=config.task_split,
                user_provider=config.user_model_provider,
                task_index=idx,
            )
            
            # Apply same modifications to isolated env
            if args.randomize_wiki:
                isolated_env.wiki = load_randomized_wiki(config.env)
            if args.tone_style != "default":
                isolated_env.wiki = apply_tone_modification(
                    isolated_env.wiki, 
                    ToneStyle[args.tone_style.upper()]
                )
            if args.remove_tool_descriptions:
                isolated_env.tools_info = remove_tool_descriptions(isolated_env.tools_info)
            
            print(f"Running task {idx}")
            try:
                res = agent.solve(
                    env=isolated_env,
                    task_index=idx,
                )
                result = EnvRunResult(
                    task_id=idx,
                    reward=res.reward,
                    info=res.info,
                    traj=res.messages,
                    trial=i,
                )
            except Exception as e:
                import traceback
                result = EnvRunResult(
                    task_id=idx,
                    reward=0.0,
                    info={"error": str(e), "traceback": traceback.format_exc()},
                    traj=[],
                    trial=i,
                )
            
            print(
                "✅" if result.reward == 1 else "❌",
                f"task_id={idx}",
                result.info,
            )
            print("-----")
            
            with lock:
                data = []
                if os.path.exists(ckpt_path):
                    with open(ckpt_path, "r") as f:
                        data = json.load(f)
                with open(ckpt_path, "w") as f:
                    json.dump(data + [result.model_dump()], f, indent=2)
            return result
        
        with ThreadPoolExecutor(max_workers=config.max_concurrency) as executor:
            res = list(executor.map(_run, idxs))
            results.extend(res)
    
    display_metrics(results)
    
    # Save final results with ablation metadata
    final_results = {
        "ablation_config": {
            "tone_style": args.tone_style,
            "randomize_wiki": args.randomize_wiki,
            "remove_tool_descriptions": args.remove_tool_descriptions,
        },
        "results": [result.model_dump() for result in results]
    }
    
    with open(ckpt_path, "w") as f:
        json.dump(final_results, f, indent=2)
        print(f"\n📄 Results saved to {ckpt_path}\n")
    
    return results


def main():
    args = parse_args()
    run_with_ablation(args)


if __name__ == "__main__":
    main()
