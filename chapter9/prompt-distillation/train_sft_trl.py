"""
Prompt Distillation Training using Hugging Face TRL

This script trains a student model using the TRL SFTTrainer instead of verl.
TRL is more widely used, better documented, and easier to work with.

Based on the same prompt distillation methodology but using standard HF tools.
"""

import argparse
import json
import os
from pathlib import Path

import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model

# 注意：trl 的 SFTTrainer / SFTConfig 在 train_model() 内部按需导入，
# 这样即便未安装 trl（如离线查看 --help 时）也能正常展示命令行帮助。


def load_jsonl_dataset(file_path: str) -> Dataset:
    """
    Load training data from JSONL file.
    
    Args:
        file_path: Path to JSONL file with messages format
        
    Returns:
        Dataset: Hugging Face Dataset object
    """
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    
    if local_rank == 0:
        print(f"Loading dataset from: {file_path}")
    
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    if local_rank == 0:
        print(f"Loaded {len(data)} training examples")
        
        # Show sample
        if data:
            print(f"\nSample data:")
            print(f"  Messages: {data[0]['messages']}")
    
    # Convert to HF Dataset
    dataset = Dataset.from_list(data)
    
    return dataset


def prepare_model_and_tokenizer(model_name: str, use_lora: bool = True, 
                                lora_rank: int = 32, lora_alpha: int = 16):
    """
    Load model and tokenizer, optionally with LoRA.
    
    Args:
        model_name: Model name or path
        use_lora: Whether to use LoRA for efficient training
        lora_rank: LoRA rank
        lora_alpha: LoRA alpha parameter
        
    Returns:
        tuple: (model, tokenizer, peft_config or None)
    """
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    
    if local_rank == 0:
        print(f"\n{'='*80}")
        print(f"Loading Model and Tokenizer")
        print(f"{'='*80}")
        print(f"Model: {model_name}")
        print(f"LoRA: {'Enabled' if use_lora else 'Disabled'}")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    
    # Set pad token if not exists
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id
    
    if local_rank == 0:
        print(f"Tokenizer loaded: vocab_size={len(tokenizer)}")
    
    # Load model
    # Note: Don't use device_map='auto' in distributed training - let DDP/FSDP handle device placement
    model_kwargs = {
        "torch_dtype": torch.bfloat16,
        "trust_remote_code": True,
        "use_cache": False,  # Disable for training
    }
    
    # Only use device_map for single GPU (non-distributed)
    if local_rank == -1 or int(os.environ.get("WORLD_SIZE", "1")) == 1:
        model_kwargs["device_map"] = "auto"
    
    if local_rank == 0:
        print(f"Loading model (this may take a few minutes)...")
    model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
    
    if local_rank == 0:
        print(f"Model loaded successfully!")
        print(f"  Parameters: {model.num_parameters() / 1e9:.2f}B")
    
    # Configure LoRA if enabled
    peft_config = None
    if use_lora:
        if local_rank == 0:
            print(f"\nConfiguring LoRA:")
            print(f"  Rank: {lora_rank}")
            print(f"  Alpha: {lora_alpha}")
        
        peft_config = LoraConfig(
            r=lora_rank,
            lora_alpha=lora_alpha,
            target_modules="all-linear",
            lora_dropout=0.0,
            bias="none",
            task_type="CAUSAL_LM",
        )
        
        model = get_peft_model(model, peft_config)
        
        # Print trainable parameters
        if local_rank == 0:
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            total_params = sum(p.numel() for p in model.parameters())
            trainable_percent = 100 * trainable_params / total_params
            
            print(f"\nTrainable Parameters:")
            print(f"  Trainable: {trainable_params:,} ({trainable_percent:.2f}%)")
            print(f"  Total: {total_params:,}")
    
    return model, tokenizer, peft_config


def train_model(
    model,
    tokenizer,
    train_dataset,
    output_dir: str,
    num_train_epochs: int = 1,
    per_device_train_batch_size: int = 4,
    gradient_accumulation_steps: int = 4,
    learning_rate: float = 2e-4,
    max_length: int = 2048,
    warmup_ratio: float = 0.03,
    logging_steps: int = 1,
    save_strategy: str = "epoch",
    lr_scheduler_type: str = "cosine_with_min_lr",
    report_to: str = "wandb",
    run_name: str = None,
):
    """
    Train the model using TRL SFTTrainer.
    
    Hyperparameters are based on the OpenAI Cookbook gpt-oss-20b example,
    which provides good defaults for efficient fine-tuning.
    
    Args:
        model: The model to train
        tokenizer: The tokenizer
        train_dataset: Training dataset
        output_dir: Output directory for checkpoints
        num_train_epochs: Number of training epochs (default: 1, matching OpenAI)
        per_device_train_batch_size: Batch size per device (default: 4, matching OpenAI)
        gradient_accumulation_steps: Gradient accumulation steps (default: 4, matching OpenAI)
        learning_rate: Learning rate (default: 2e-4, matching OpenAI)
        max_length: Maximum sequence length (default: 2048, matching OpenAI)
        warmup_ratio: Warmup ratio (default: 0.03, matching OpenAI)
        logging_steps: Steps between logging (default: 1, matching OpenAI)
        save_strategy: When to save checkpoints
        lr_scheduler_type: Learning rate scheduler type (default: cosine_with_min_lr, matching OpenAI)
        report_to: Where to report metrics (default: wandb)
        run_name: Custom run name for logging (default: auto-generated)
        
    Returns:
        SFTTrainer: The trained trainer object
    """
    from trl import SFTTrainer, SFTConfig

    local_rank = int(os.environ.get("LOCAL_RANK", 0))

    if local_rank == 0:
        print(f"\n{'='*80}")
        print(f"Training Configuration")
        print(f"{'='*80}")
    
    # Calculate effective batch size
    world_size = torch.cuda.device_count() if torch.cuda.is_available() else 1
    effective_batch_size = per_device_train_batch_size * gradient_accumulation_steps * world_size
    
    # Detect distributed mode
    distributed_mode = "Single GPU"
    if int(os.environ.get("WORLD_SIZE", "1")) > 1:
        if os.environ.get("ACCELERATE_USE_FSDP", "false").lower() == "true":
            distributed_mode = "FSDP (Fully Sharded Data Parallel)"
        else:
            distributed_mode = "DDP (Distributed Data Parallel)"
    
    if local_rank == 0:
        print(f"Training Parameters:")
        print(f"  Output directory: {output_dir}")
        print(f"  Distributed mode: {distributed_mode}")
        print(f"  Epochs: {num_train_epochs}")
        print(f"  Per-device batch size: {per_device_train_batch_size}")
        print(f"  Gradient accumulation steps: {gradient_accumulation_steps}")
        print(f"  Number of GPUs: {world_size}")
        print(f"  Effective batch size: {effective_batch_size}")
        print(f"  Learning rate: {learning_rate}")
        print(f"  LR scheduler: {lr_scheduler_type}")
        print(f"  Warmup ratio: {warmup_ratio}")
        print(f"  Max length: {max_length}")
        print(f"  Logging steps: {logging_steps}")
        print(f"  Save strategy: {save_strategy}")
        
        # Show memory advantage for FSDP
        if "FSDP" in distributed_mode:
            print(f"\n  💡 FSDP Mode: Each GPU holds ~{100/world_size:.1f}% of the model")
    
    # Training configuration (matching OpenAI Cookbook gpt-oss-20b example)
    training_args = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=num_train_epochs,
        per_device_train_batch_size=per_device_train_batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        max_length=max_length,  # Note: Use max_length, not max_seq_length
        warmup_ratio=warmup_ratio,
        lr_scheduler_type=lr_scheduler_type,
        lr_scheduler_kwargs={"min_lr_rate": 0.1} if lr_scheduler_type == "cosine_with_min_lr" else {},
        logging_steps=logging_steps,
        save_strategy=save_strategy,
        save_total_limit=2,  # Keep only last 2 checkpoints
        gradient_checkpointing=True,  # Save memory (matching OpenAI)
        bf16=torch.cuda.is_available(),  # Use bfloat16 if available
        logging_first_step=True,
        report_to=report_to,  # wandb, tensorboard, or none
        run_name=run_name or f"prompt-distillation-{num_train_epochs}epoch",
        remove_unused_columns=False,
        dataset_text_field="",  # We'll use formatting function
        dataset_kwargs={
            "skip_prepare_dataset": False,
        },
    )
    
    if local_rank == 0:
        if report_to == "wandb":
            print(f"\n  📊 Logging to Weights & Biases (wandb)")
            print(f"     Run name: {run_name or f'prompt-distillation-{num_train_epochs}epoch'}")
            print(f"     View at: https://wandb.ai")
        elif report_to == "tensorboard":
            print(f"\n  📊 Logging to TensorBoard")
            print(f"     View with: tensorboard --logdir {output_dir}")
        else:
            print(f"\n  📊 Logging disabled (report_to=none)")
    
    # Initialize trainer
    if local_rank == 0:
        print(f"\n{'='*80}")
        print(f"Initializing SFTTrainer")
        print(f"{'='*80}")
    
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        processing_class=tokenizer,
        formatting_func=lambda x: tokenizer.apply_chat_template(
            x["messages"],
            tokenize=False,
            add_generation_prompt=False,
        ),
    )
    
    # Start training
    if local_rank == 0:
        print(f"\n{'='*80}")
        print(f"Starting Training")
        print(f"{'='*80}")

    trainer.train()
    
    if local_rank == 0:
        print(f"\n{'='*80}")
        print(f"Training Complete!")
        print(f"{'='*80}")
    
    return trainer


def main():
    parser = argparse.ArgumentParser(
        description="用 Hugging Face TRL 训练 Prompt 蒸馏学生模型（无提示直接作答）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Data arguments
    parser.add_argument(
        "--train_file",
        type=str,
        default="./data/prompt_distillation_lang.jsonl",
        help="训练数据路径（JSONL 格式）",
    )

    # Model arguments
    parser.add_argument(
        "--model_name",
        type=str,
        default="Qwen/Qwen3-30B-A3B-Instruct-2507",
        help="学生基座模型名称或路径（用于蒸馏的非思考型模型）",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./models/prompt_distillation_trl",
        help="模型 checkpoint 的输出目录",
    )

    # LoRA arguments
    parser.add_argument(
        "--use_lora",
        action="store_true",
        default=True,
        help="使用 LoRA 做参数高效微调",
    )
    parser.add_argument(
        "--lora_rank",
        type=int,
        default=32,
        help="LoRA rank（默认 32，与 tinker 一致）",
    )
    parser.add_argument(
        "--lora_alpha",
        type=int,
        default=16,
        help="LoRA alpha 参数（默认 16）",
    )

    # Training arguments
    parser.add_argument(
        "--num_train_epochs",
        type=int,
        default=1,
        help="训练轮数（默认 1，与 OpenAI 教程一致）",
    )
    parser.add_argument(
        "--per_device_train_batch_size",
        type=int,
        default=4,
        help="每张 GPU 的批次大小（默认 4，与 OpenAI 教程一致）",
    )
    parser.add_argument(
        "--gradient_accumulation_steps",
        type=int,
        default=4,
        help="梯度累积步数（默认 4，与 OpenAI 教程一致）",
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=2e-4,
        help="学习率（默认 2e-4，与 OpenAI 教程一致）",
    )
    parser.add_argument(
        "--max_length",
        type=int,
        default=2048,
        help="最大序列长度（默认 2048，与 OpenAI 教程一致）",
    )
    parser.add_argument(
        "--warmup_ratio",
        type=float,
        default=0.03,
        help="warmup 比例（默认 0.03，与 OpenAI 教程一致）",
    )
    parser.add_argument(
        "--lr_scheduler_type",
        type=str,
        default="cosine_with_min_lr",
        help="学习率调度器类型（默认 cosine_with_min_lr，与 OpenAI 教程一致）",
    )

    # Logging arguments
    parser.add_argument(
        "--report_to",
        type=str,
        default="wandb",
        choices=["wandb", "tensorboard", "none"],
        help="训练指标上报目标（默认 wandb）",
    )
    parser.add_argument(
        "--run_name",
        type=str,
        default=None,
        help="wandb 运行名称（未提供则自动生成）",
    )
    
    args = parser.parse_args()
    
    # Print configuration
    print(f"{'='*80}")
    print(f"Prompt Distillation Training with TRL")
    print(f"{'='*80}")
    print(f"Configuration:")
    print(f"  Train file: {args.train_file}")
    print(f"  Model: {args.model_name}")
    print(f"  Output dir: {args.output_dir}")
    print(f"  LoRA: {args.use_lora}")
    if args.use_lora:
        print(f"    - Rank: {args.lora_rank}")
        print(f"    - Alpha: {args.lora_alpha}")
    print(f"  Epochs: {args.num_train_epochs}")
    print(f"  Batch size: {args.per_device_train_batch_size}")
    print(f"  Gradient accumulation: {args.gradient_accumulation_steps}")
    print(f"  Learning rate: {args.learning_rate}")
    print(f"  Max length: {args.max_length}")
    print(f"  LR scheduler: {args.lr_scheduler_type}")
    print(f"  Warmup ratio: {args.warmup_ratio}")
    print(f"{'='*80}\n")
    
    # Check if training file exists
    if not os.path.exists(args.train_file):
        raise FileNotFoundError(f"Training file not found: {args.train_file}")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load dataset
    train_dataset = load_jsonl_dataset(args.train_file)
    
    # Load model and tokenizer
    model, tokenizer, peft_config = prepare_model_and_tokenizer(
        args.model_name,
        use_lora=args.use_lora,
        lora_rank=args.lora_rank,
        lora_alpha=args.lora_alpha,
    )
    
    # Train model
    trainer = train_model(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        output_dir=args.output_dir,
        num_train_epochs=args.num_train_epochs,
        per_device_train_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        max_length=args.max_length,
        warmup_ratio=args.warmup_ratio,
        lr_scheduler_type=args.lr_scheduler_type,
        report_to=args.report_to,
        run_name=args.run_name,
    )
    
    # Save final model (only main process)
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    
    if local_rank == 0:
        print(f"\nSaving final model to: {args.output_dir}")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    if local_rank == 0:
        print(f"\n{'='*80}")
        print(f"Training Complete!")
        print(f"{'='*80}")
        print(f"Model saved to: {args.output_dir}")
        print(f"\nTo use the model:")
        print(f"  from transformers import AutoModelForCausalLM, AutoTokenizer")
        print(f"  from peft import PeftModel")
        print(f"  ")
        print(f"  tokenizer = AutoTokenizer.from_pretrained('{args.output_dir}')")
        print(f"  model = AutoModelForCausalLM.from_pretrained('{args.model_name}')")
        print(f"  model = PeftModel.from_pretrained(model, '{args.output_dir}')")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    main()

