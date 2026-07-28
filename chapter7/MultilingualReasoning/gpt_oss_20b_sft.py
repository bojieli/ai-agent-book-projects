"""
多语言推理模型微调脚本

本脚本展示如何使用 Hugging Face 的 TRL 库对 OpenAI 的 gpt-oss-20b 模型进行微调，
使其能够在多种语言中进行有效推理。

基于 OpenAI Cookbook 教程：
https://cookbook.openai.com/articles/gpt-oss/fine-tune-transfomers

作者: Edward Beeching, Quentin Gallouédec, Lewis Tunstall
修改: 适配为完整的 Python 脚本

⚠️  硬件要求（重要！）:
- GPU: H100（80GB 显存）或更高配置
- 训练时间: H100 上约 18 分钟
- 使用 Mxfp4Config 量化和 LoRA 进行内存高效训练

功能特性:
- 使用 Mxfp4Config（针对 OpenAI 模型优化的 4-bit 浮点格式）
- 使用 LoRA 进行内存高效的微调（包括 MoE 专家层）
- 支持多语言推理（英语、西班牙语、法语、德语、意大利语等）
- 可以混合语言（用一种语言提问，用另一种语言推理）
- 所有超参数与 OpenAI Cookbook 教程完全一致
"""

import os
import argparse
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Mxfp4Config,
)
from peft import LoraConfig, PeftModel, get_peft_model
from trl import SFTTrainer, SFTConfig


# ============================================================================
# 第一部分：数据集准备
# ============================================================================

def load_and_prepare_dataset():
    """
    加载并准备多语言推理数据集
    
    使用 HuggingFaceH4/Multilingual-Thinking 数据集，该数据集包含：
    - 多种语言的推理链（思维链）
    - 支持英语、西班牙语、法语、德语、意大利语等
    
    Returns:
        Dataset: 格式化后的训练数据集
    """
    print("=" * 80)
    print("步骤 1: 加载数据集")
    print("=" * 80)
    
    # 从 Hugging Face Hub 加载数据集
    dataset = load_dataset("HuggingFaceH4/Multilingual-Thinking")
    
    print(f"数据集加载完成！")
    print(f"训练样本数: {len(dataset['train'])}")
    print(f"数据集列: {dataset['train'].column_names}")
    print(f"\n示例数据:")
    print(dataset['train'][0])
    
    return dataset['train']


def format_chat_template(example, tokenizer):
    """
    格式化对话模板
    
    将数据集中的消息格式化为模型可以理解的对话格式
    
    Args:
        example: 数据集中的一个样本
        tokenizer: 分词器
        
    Returns:
        dict: 格式化后的样本
    """
    # 应用聊天模板
    example["text"] = tokenizer.apply_chat_template(
        example["messages"],
        tokenize=False,
    )
    return example


# ============================================================================
# 第二部分：模型准备
# ============================================================================

def load_base_model(model_name="openai/gpt-oss-20b"):
    """
    加载基础模型和分词器
    
    使用 Mxfp4Config 进行量化，这是专门为 OpenAI 模型优化的 4-bit 浮点格式。
    
    Args:
        model_name: 模型名称或路径
        
    Returns:
        tuple: (model, tokenizer)
    """
    print("\n" + "=" * 80)
    print("步骤 2: 加载基础模型")
    print("=" * 80)
    
    # 加载分词器
    print(f"加载分词器: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # 设置 pad token（如果不存在）
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # 配置 Mxfp4 量化（针对 OpenAI 模型优化）
    print("使用 Mxfp4Config 量化...")
    quantization_config = Mxfp4Config(dequantize=True)
    
    # 配置模型加载参数
    model_kwargs = {
        "attn_implementation": "eager",      # 注意力实现方式
        "torch_dtype": torch.bfloat16,       # 使用 bfloat16 提高效率
        "quantization_config": quantization_config,  # Mxfp4 量化配置
        "use_cache": False,                   # 训练时禁用 KV 缓存
        "device_map": "auto",                 # 自动分配设备
    }
    
    # 加载模型
    print(f"加载模型: {model_name}")
    print("这可能需要几分钟时间...")
    model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
    
    print(f"模型加载完成！")
    print(f"模型参数量: {model.num_parameters() / 1e9:.2f}B")
    
    return model, tokenizer


def prepare_model_for_lora(model, lora_rank=8, lora_alpha=16):
    """
    配置 LoRA（低秩适应）进行高效微调
    
    LoRA 只训练少量参数，大大减少内存使用和训练时间。
    针对 openai/gpt-oss-20b 的 MoE（混合专家）架构，除了注意力层外，
    还需要特别指定 MLP 专家层进行训练。
    
    Args:
        model: 基础模型
        lora_rank: LoRA 秩（默认 8，与官方教程一致）
        lora_alpha: LoRA 缩放参数（默认 16）
        
    Returns:
        PeftModel: 配置了 LoRA 的模型
    """
    print("\n" + "=" * 80)
    print("步骤 3: 配置 LoRA")
    print("=" * 80)
    
    # LoRA 配置（与 OpenAI Cookbook 一致）
    peft_config = LoraConfig(
        r=lora_rank,                     # LoRA 秩
        lora_alpha=lora_alpha,           # LoRA 缩放参数
        target_modules="all-linear",     # 目标所有线性层
        target_parameters=[              # MoE 专家层的特定参数
            "7.mlp.experts.gate_up_proj",
            "7.mlp.experts.down_proj",
            "15.mlp.experts.gate_up_proj",
            "15.mlp.experts.down_proj",
            "23.mlp.experts.gate_up_proj",
            "23.mlp.experts.down_proj",
        ],
    )
    
    print("LoRA 配置:")
    print(f"  - Rank: {lora_rank}")
    print(f"  - Alpha: {lora_alpha}")
    print(f"  - 目标模块: {peft_config.target_modules}")
    print(f"  - MoE 专家层参数: {len(peft_config.target_parameters)} 个")
    
    # 应用 LoRA
    model = get_peft_model(model, peft_config)
    
    # 打印可训练参数统计
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_percent = 100 * trainable_params / total_params
    
    print(f"\n可训练参数统计:")
    print(f"  - 可训练参数: {trainable_params:,} ({trainable_percent:.2f}%)")
    print(f"  - 总参数: {total_params:,}")
    
    return model


# ============================================================================
# 第三部分：训练
# ============================================================================

def train_model(model, tokenizer, dataset, output_dir="./gpt-oss-20b-multilingual-reasoner", 
                batch_size=4, num_epochs=1, learning_rate=2e-4, max_seq_length=2048):
    """
    使用 SFTTrainer 训练模型
    
    Args:
        model: 配置了 LoRA 的模型
        tokenizer: 分词器
        dataset: 训练数据集
        output_dir: 输出目录
        batch_size: 批次大小（根据 GPU 显存调整，默认 4）
        num_epochs: 训练轮数（默认 1）
        learning_rate: 学习率（默认 2e-4）
        max_seq_length: 最大序列长度
        
    Returns:
        SFTTrainer: 训练好的 trainer 对象
    """
    print("\n" + "=" * 80)
    print("步骤 4: 开始训练")
    print("=" * 80)
    
    # 训练参数配置（与 OpenAI Cookbook 完全一致）
    training_args = SFTConfig(
        learning_rate=learning_rate,
        gradient_checkpointing=True,
        num_train_epochs=num_epochs,
        logging_steps=1,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4,
        max_length=max_seq_length,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine_with_min_lr",
        lr_scheduler_kwargs={"min_lr_rate": 0.1},
        output_dir=output_dir,
        report_to="trackio",  # 设为 "trackio" 以启用实验跟踪
        push_to_hub=False,  # 设为 True 以自动推送到 Hub
    )
    
    print("训练配置:")
    print(f"  - 批次大小: {batch_size}")
    print(f"  - 梯度累积步数: {training_args.gradient_accumulation_steps}")
    print(f"  - 有效批次大小: {batch_size * training_args.gradient_accumulation_steps}")
    print(f"  - 训练轮数: {num_epochs}")
    print(f"  - 学习率: {learning_rate}")
    print(f"  - 学习率调度: {training_args.lr_scheduler_type}")
    print(f"  - 最大序列长度: {max_seq_length}")
    print(f"  - 输出目录: {output_dir}")
    
    # 初始化 SFTTrainer
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )
    
    # 开始训练
    print("\n开始训练...")
    print("⚠️  在 H100 GPU 上训练约需 18 分钟")
    print("-" * 80)
    
    trainer.train()
    
    print("\n" + "=" * 80)
    print("训练完成！")
    print("=" * 80)
    
    return trainer


# ============================================================================
# 第四部分：保存和推送模型
# ============================================================================

def save_and_push_model(trainer, output_dir, push_to_hub=False, hub_model_id=None):
    """
    保存模型并可选择推送到 Hugging Face Hub
    
    Args:
        trainer: 训练好的 trainer 对象
        output_dir: 输出目录
        push_to_hub: 是否推送到 Hub
        hub_model_id: Hub 上的模型 ID
    """
    print("\n" + "=" * 80)
    print("步骤 5: 保存模型")
    print("=" * 80)
    
    # 保存模型到本地
    print(f"保存模型到: {output_dir}")
    trainer.save_model(output_dir)
    print("模型保存完成！")
    
    # 可选：推送到 Hugging Face Hub
    if push_to_hub:
        if hub_model_id is None:
            raise ValueError("需要提供 hub_model_id 才能推送到 Hub")

        print(f"\n推送模型到 Hugging Face Hub: {hub_model_id}")
        # Trainer.push_to_hub 从 args.hub_model_id 取仓库名；不设置的话会
        # 忽略用户传入的 --hub_model_id，推到 output_dir 同名的默认仓库。
        trainer.args.hub_model_id = hub_model_id
        trainer.push_to_hub(
            dataset_name="HuggingFaceH4/Multilingual-Thinking",
        )
        print("模型已成功推送到 Hub！")


# ============================================================================
# 第五部分：推理
# ============================================================================

def load_trained_model(base_model_name, peft_model_path):
    """
    加载训练好的模型进行推理
    
    Args:
        base_model_name: 基础模型名称
        peft_model_path: LoRA 权重路径
        
    Returns:
        tuple: (model, tokenizer)
    """
    print("\n" + "=" * 80)
    print("加载训练好的模型进行推理")
    print("=" * 80)
    
    # 加载分词器
    print(f"加载分词器: {base_model_name}")
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    
    # 加载基础模型
    print(f"加载基础模型: {base_model_name}")
    model_kwargs = {
        "attn_implementation": "eager",
        "torch_dtype": "auto",
        "use_cache": True,  # 推理时启用 KV 缓存
        "device_map": "auto",
    }
    base_model = AutoModelForCausalLM.from_pretrained(base_model_name, **model_kwargs)
    
    # 加载并合并 LoRA 权重
    print(f"加载 LoRA 权重: {peft_model_path}")
    model = PeftModel.from_pretrained(base_model, peft_model_path)
    
    print("合并 LoRA 权重与基础模型...")
    model = model.merge_and_unload()
    
    print("模型加载完成！")
    
    return model, tokenizer


def generate_response(model, tokenizer, reasoning_language, user_prompt, 
                     max_new_tokens=512, temperature=0.6, format_output=True):
    """
    生成多语言推理响应
    
    Args:
        model: 训练好的模型
        tokenizer: 分词器
        reasoning_language: 推理使用的语言
        user_prompt: 用户提问
        max_new_tokens: 最大生成 token 数
        temperature: 采样温度（越高越随机）
        format_output: 是否格式化输出（使用明显的标记）
        
    Returns:
        str: 生成的完整响应
    """
    # 构建消息
    system_prompt = f"reasoning language: {reasoning_language}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    # 应用聊天模板
    input_ids = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(model.device)
    
    # 生成配置
    gen_kwargs = {
        "max_new_tokens": max_new_tokens,
        "do_sample": True,
        "temperature": temperature,
        "top_p": None,
        "top_k": None,
    }
    
    # 生成响应
    print(f"\n生成响应...")
    print(f"推理语言: {reasoning_language}")
    print(f"用户提问: {user_prompt}")
    
    with torch.no_grad():
        output_ids = model.generate(input_ids, **gen_kwargs)
    
    # 解码输出 - 保留特殊标记以便解析
    response_with_tokens = tokenizer.batch_decode(output_ids, skip_special_tokens=False)[0]
    print("-" * 80)
    print(response_with_tokens)
    print("-" * 80)


def run_inference_examples(model, tokenizer):
    """
    运行多个推理示例
    
    Args:
        model: 训练好的模型
        tokenizer: 分词器
    """
    print("\n" + "=" * 80)
    print("推理示例")
    print("=" * 80)
    
    # 示例 1: 西班牙语提问，德语推理
    print("\n[示例 1: 西班牙语提问 + 德语推理]")
    generate_response(
        model, tokenizer,
        reasoning_language="German",
        user_prompt="¿Cuál es el capital de Australia?",  # 澳大利亚的首都是什么？
        format_output=True,
    )
    
    # 示例 2: 英语提问，中文推理
    print("\n\n[示例 2: 英语提问 + 中文推理]")
    generate_response(
        model, tokenizer,
        reasoning_language="Chinese",
        user_prompt="What is the national symbol of Canada?",
        format_output=True,
    )
    
    # 示例 3: 中文提问，中文推理
    print("\n\n[示例 3: 中文提问 + 中文推理]")
    generate_response(
        model, tokenizer,
        reasoning_language="Chinese",
        user_prompt="求解 x^2 - 2x + 1 = 0 的根",
        format_output=True,
    )


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数：完整的训练流程"""
    
    parser = argparse.ArgumentParser(description="多语言推理模型微调")
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["train", "inference", "full"],
        default="full",
        help="运行模式: train（仅训练）, inference（仅推理）, full（完整流程）"
    )
    parser.add_argument("--model_name", type=str, default="openai/gpt-oss-20b", help="基础模型名称")
    parser.add_argument("--output_dir", type=str, default="./gpt-oss-20b-multilingual-reasoner", help="输出目录")
    parser.add_argument("--batch_size", type=int, default=4, help="训练批次大小（默认 4，与官方教程一致）")
    parser.add_argument("--num_epochs", type=int, default=1, help="训练轮数（默认 1，与官方教程一致）")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="学习率（默认 2e-4，与官方教程一致）")
    parser.add_argument("--max_seq_length", type=int, default=2048, help="最大序列长度")
    parser.add_argument("--lora_rank", type=int, default=8, help="LoRA 秩（默认 8，与官方教程一致）")
    parser.add_argument("--lora_alpha", type=int, default=16, help="LoRA alpha")
    parser.add_argument("--push_to_hub", action="store_true", default=False, help="推送模型到 Hugging Face Hub")
    parser.add_argument("--hub_model_id", type=str, default=None, help="Hub 模型 ID")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("多语言推理模型微调")
    print("=" * 80)
    print(f"模式: {args.mode}")
    print(f"基础模型: {args.model_name}")
    print(f"输出目录: {args.output_dir}")
    
    # 训练模式
    if args.mode in ["train", "full"]:
        # 1. 加载数据集
        dataset = load_and_prepare_dataset()
        
        # 2. 加载基础模型（使用 Mxfp4Config 量化）
        model, tokenizer = load_base_model(args.model_name)
        
        # 3. 配置 LoRA
        model = prepare_model_for_lora(model, args.lora_rank, args.lora_alpha)
        
        # 4. 训练模型
        trainer = train_model(
            model, 
            tokenizer, 
            dataset,
            output_dir=args.output_dir,
            batch_size=args.batch_size,
            num_epochs=args.num_epochs,
            learning_rate=args.learning_rate,
            max_seq_length=args.max_seq_length,
        )
        
        # 5. 保存模型
        save_and_push_model(
            trainer, 
            args.output_dir,
            push_to_hub=args.push_to_hub,
            hub_model_id=args.hub_model_id,
        )
        
        if args.mode == "full":
            # full 模式继续跑推理：先释放训练占用的显存，
            # 再按推理路径从 output_dir 重新加载已保存的模型。
            del trainer
            del model
            torch.cuda.empty_cache()
            print("\n训练完成！已释放训练显存，继续运行推理示例。")
        else:
            print("\n训练完成！建议重启内核以释放 GPU 显存后再进行推理。")

    # 推理模式（inference 单独运行；full 在训练后接着运行）
    if args.mode in ["inference", "full"]:
        if not os.path.exists(args.output_dir):
            print(f"错误: 未找到模型目录 {args.output_dir}")
            print("请先运行训练或指定正确的模型路径")
            return
        
        # 加载训练好的模型
        model, tokenizer = load_trained_model(args.model_name, args.output_dir)
        
        # 运行推理示例
        run_inference_examples(model, tokenizer)
    
    print("\n" + "=" * 80)
    print("完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()

