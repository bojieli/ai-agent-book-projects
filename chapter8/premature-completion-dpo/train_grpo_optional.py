"""可选 RL 分支：GRPO + 隐藏验收测试作为奖励（实验 7-17 可选路径，主线是 DPO）。

奖励函数 = 隐藏验收测试：对每个端到端任务，模型输出若宣称完成，则在隔离的
临时目录里还原工作区并运行该任务附带的隐藏检查脚本：
- 宣称完成且隐藏测试通过：+1
- 宣称完成但测试不过：-1
- 未宣称完成但执行了验证动作：+0.3
- 其它：0

隐藏测试定义在 data/hidden_tests.json。脚本真实可运行，但属于可选分支：
正文以 DPO 为主线，GRPO 路径需要 GPU 且训练成本更高。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from evaluate import has_completion_claim, has_verification_action

ROOT = Path(__file__).resolve().parent
HIDDEN_TESTS_PATH = ROOT / "data" / "hidden_tests.json"

REWARD_CLAIM_PASS = 1.0
REWARD_CLAIM_FAIL = -1.0
REWARD_VERIFY = 0.3


def load_hidden_tasks(path: Path = HIDDEN_TESTS_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_hidden_check(task: dict[str, Any], workdir: Path) -> bool:
    """在临时目录里还原工作区并运行隐藏检查脚本，返回是否通过。"""
    for rel_path, content in task["workspace_files"].items():
        target = workdir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    try:
        result = subprocess.run(
            task["hidden_check"], shell=True, cwd=workdir,
            capture_output=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return False
    return result.returncode == 0


def hidden_test_reward(completion: str, task: dict[str, Any]) -> float:
    """单条补全的奖励：宣称完成要看隐藏测试结果，验证动作给小额奖励。"""
    claimed = has_completion_claim(completion)
    if not claimed:
        return REWARD_VERIFY if has_verification_action(completion) else 0.0
    with tempfile.TemporaryDirectory(prefix="grpo-hidden-") as tmp:
        passed = run_hidden_check(task, Path(tmp))
    return REWARD_CLAIM_PASS if passed else REWARD_CLAIM_FAIL


def build_dataset(tasks: list[dict[str, Any]]):
    """GRPO 数据集：prompt 列给模型，task 列透传给奖励函数。"""
    from datasets import Dataset

    rows = [{
        "prompt": f"任务：{t['task']}\n\n请完成该任务，并在最后说明你的结论。",
        "task_id": t["id"],
    } for t in tasks]
    return Dataset.from_list(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--output-dir", default=str(ROOT / "output" / "grpo_adapter"))
    parser.add_argument("--seed", type=int, default=717)
    parser.add_argument("--num-generations", type=int, default=8, help="每个 prompt 的采样数")
    args = parser.parse_args()

    tasks = load_hidden_tasks()
    task_by_id = {t["id"]: t for t in tasks}

    def reward_func(completions, task_id, **kwargs):
        """TRL GRPO 奖励回调：dataset 的 task_id 列会作为关键字参数透传进来。"""
        return [hidden_test_reward(c, task_by_id[tid]) for c, tid in zip(completions, task_id)]

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig
    from trl import GRPOConfig, GRPOTrainer

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto"
    )
    model.config.use_cache = False

    peft_config = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM")
    config = GRPOConfig(
        output_dir=args.output_dir,
        learning_rate=1e-6,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,
        num_generations=args.num_generations,
        max_completion_length=512,
        bf16=True,
        gradient_checkpointing=True,
        num_train_epochs=1,
        logging_steps=1,
        save_strategy="no",
        report_to=[],
        seed=args.seed,
    )
    trainer = GRPOTrainer(
        model=model,
        reward_funcs=reward_func,
        args=config,
        train_dataset=build_dataset(tasks),
        processing_class=tokenizer,
        peft_config=peft_config,
    )
    trainer.train()
    trainer.save_model(args.output_dir)
    print(f"GRPO adapter 已保存到 {args.output_dir}（可选分支产物）")


if __name__ == "__main__":
    main()
