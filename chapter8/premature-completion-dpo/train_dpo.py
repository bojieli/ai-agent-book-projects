"""DPO 训练脚本（实验 7-17 主线，需要单卡 GPU）。

默认配置面向单卡：bf16、gradient checkpointing、LoRA r=16 alpha=32、
per_device_batch_size=1、gradient_accumulation 2、learning_rate 3e-5、
beta 0.1、4 epochs。小数据集使用较小的累积步数，确保确实有足够的更新步；可用
`--epochs`、`--gradient-accumulation` 和 `--learning-rate` 覆盖。训练产物：output/adapter/（仅 LoRA adapter），
训练回执 validation/<run>/training_receipt.json（配置、数据哈希、时间戳）。

--smoke 模式只做数据加载、tokenizer、模型前向的一次性检查，不训练，
用于无 GPU 环境验证脚本完整性（仍需能下载一个小模型，见 --smoke-model）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "output" / "preference_pairs.jsonl"
ADAPTER_DIR = ROOT / "output" / "adapter"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_pairs(path: Path):
    """加载 DPO 偏好对为 datasets.Dataset（prompt/chosen/rejected 三列）。"""
    from datasets import Dataset

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise SystemExit(f"偏好对为空：{path}；请先运行 python build_preference_data.py")
    return Dataset.from_list([{k: r[k] for k in ("prompt", "chosen", "rejected")} for r in rows])


def smoke(args) -> None:
    """一次性完整性检查：数据加载 + tokenizer + 模型前向，不做训练。"""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    dataset = load_pairs(Path(args.data))
    print(f"数据加载 OK：{len(dataset)} 条偏好对，列 = {dataset.column_names}")

    tokenizer = AutoTokenizer.from_pretrained(args.smoke_model)
    text = dataset[0]["prompt"] + dataset[0]["chosen"]
    inputs = tokenizer(text, return_tensors="pt")
    print(f"tokenizer OK：首条样本 {inputs['input_ids'].shape[-1]} tokens")

    model = AutoModelForCausalLM.from_pretrained(args.smoke_model)
    model.eval()
    with torch.no_grad():
        outputs = model(**inputs)
    print(f"前向 OK：logits shape = {tuple(outputs.logits.shape)}")
    print("smoke 检查通过（未训练）。")


def train(args) -> None:
    import torch
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import DPOConfig, DPOTrainer

    data_path = Path(args.data)
    dataset = load_pairs(data_path)
    started = datetime.now(timezone.utc)

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto"
    )
    model.config.use_cache = False

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    training_args = DPOConfig(
        output_dir=str(args.output_dir),
        beta=0.1,
        learning_rate=args.learning_rate,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=args.gradient_accumulation,
        gradient_checkpointing=True,
        bf16=True,
        logging_steps=1,
        save_strategy="no",
        report_to=[],
        max_length=1536,
        seed=args.seed,
    )
    trainer = DPOTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=peft_config,
    )
    trainer.train()

    adapter_dir = Path(args.output_dir)
    adapter_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(adapter_dir))
    finished = datetime.now(timezone.utc)

    run = started.strftime("train_%Y%m%dT%H%M%SZ")
    receipt_dir = ROOT / "validation" / run
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt = {
        "experiment": "7-17 premature-completion-dpo",
        "run": run,
        "model": args.model,
        "data": str(data_path.relative_to(ROOT)),
        "data_sha256": sha256_file(data_path),
        "pair_count": len(dataset),
        "config": {
            "beta": 0.1, "learning_rate": args.learning_rate, "epochs": args.epochs,
            "lora_r": 16, "lora_alpha": 32,
            "per_device_batch_size": 1, "gradient_accumulation": args.gradient_accumulation,
            "bf16": True, "gradient_checkpointing": True, "seed": args.seed,
        },
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "adapter_dir": str(adapter_dir.relative_to(ROOT)),
        "training_loss": next(
            (entry.get("loss") for entry in reversed(trainer.state.log_history)
             if entry.get("loss") is not None),
            None,
        ),
    }
    (receipt_dir / "training_receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (ROOT / "validation" / "latest.json").write_text(
        json.dumps({"run": run, "training_receipt": f"validation/{run}/training_receipt.json"},
                   ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"adapter 已保存到 {adapter_dir}；训练回执 -> {receipt_dir / 'training_receipt.json'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct", help="基座模型（可用 --model 覆盖）")
    parser.add_argument("--data", default=str(DATA_PATH), help="preference_pairs.jsonl 路径")
    parser.add_argument("--output-dir", default=str(ADAPTER_DIR), help="adapter 输出目录")
    parser.add_argument("--seed", type=int, default=717)
    parser.add_argument("--epochs", type=float, default=4,
                        help="训练轮数；小数据演示默认 4 轮，避免只有一两个更新步")
    parser.add_argument("--gradient-accumulation", type=int, default=2,
                        help="梯度累积步数；24 条演示数据默认设为 2")
    parser.add_argument("--learning-rate", type=float, default=3e-5,
                        help="LoRA 学习率；小数据演示默认 3e-5")
    parser.add_argument("--smoke", action="store_true", help="只做数据/tokenizer/前向检查，不训练")
    parser.add_argument("--smoke-model", default="Qwen/Qwen2.5-0.5B-Instruct",
                        help="smoke 模式用的小模型（CPU 可前向）")
    args = parser.parse_args()

    if args.smoke:
        smoke(args)
    else:
        train(args)


if __name__ == "__main__":
    main()
