# -*- coding: utf-8 -*-
"""
Evaluation script for Korean Mistral continued-pretrained models
Loads saved LoRA adapters and evaluates on Korean and English tasks
"""

import os
import argparse

# 说明：unsloth / torch / transformers 等重型依赖在函数内按需导入，
# 这样 `python evaluate_model.py --help` 无需 GPU 环境即可查看参数。

# ANSI color codes for colored output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_section(title, color=Colors.CYAN):
    """Print a colored section header"""
    print(f"\n{color}{Colors.BOLD}{'='*70}")
    print(f"{title}")
    print(f"{'='*70}{Colors.ENDC}\n")

def load_model(model_path, max_seq_length=2048, dtype=None, load_in_4bit=True):
    """Load the saved LoRA model"""
    from unsloth import FastLanguageModel
    print_section(f"📥 LOADING MODEL FROM: {model_path}", Colors.BLUE)

    print(f"{Colors.YELLOW}Loading model and tokenizer...{Colors.ENDC}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = model_path,
        max_seq_length = max_seq_length,
        dtype = dtype,
        load_in_4bit = load_in_4bit,
    )
    
    FastLanguageModel.for_inference(model)  # Enable native 2x faster inference
    print(f"{Colors.GREEN}✓ Model loaded successfully!{Colors.ENDC}")
    
    return model, tokenizer

def run_evaluation(model, tokenizer, max_new_tokens=150, 
                   temperature=0.7, top_p=0.9, use_sampling=False):
    """Run all evaluation tests"""
    from transformers import TextStreamer

    print_section("🧪 RUNNING EVALUATION TESTS", Colors.CYAN)
    print(f"{Colors.YELLOW}Generation Parameters:{Colors.ENDC}")
    print(f"  • max_new_tokens: {max_new_tokens}")
    if use_sampling:
        print(f"  • temperature: {temperature}")
        print(f"  • top_p: {top_p}")
        print(f"  • Sampling: Enabled")
    else:
        print(f"  • Sampling: Disabled (greedy decoding)")
    
    text_streamer = TextStreamer(tokenizer, skip_special_tokens=True)
    
    # Define prompts
    wikipedia_prompt_korean = """위키피디아 기사
### 제목: {}

### 기사:
{}"""

    wikipedia_prompt_english = """Wikipedia Article
### Title: {}

### Article:
{}"""

    alpaca_prompt_korean = """다음은 작업을 설명하는 명령입니다. 요청을 적절하게 완료하는 응답을 작성하세요.

### 지침:
{}

### 응답:
{}"""

    alpaca_prompt_english = """Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
{}

### Response:
{}"""

    # Prepare generation kwargs
    gen_kwargs = {
        "max_new_tokens": max_new_tokens,
        "use_cache": True,
    }
    
    if use_sampling:
        gen_kwargs.update({
            "do_sample": True,
            "temperature": temperature,
            "top_p": top_p,
        })
    
    # Test 1: Korean Wikipedia Article
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"Test 1: Korean Wikipedia Article - Artificial Intelligence (인공지능)")
    print(f"{'='*70}{Colors.ENDC}")
    print(f"{Colors.CYAN}Prompt (Translation): Wikipedia Article / Title: Artificial Intelligence / Article:{Colors.ENDC}\n")
    
    test_prompt = wikipedia_prompt_korean.format("인공지능", "")
    inputs = tokenizer([test_prompt], return_tensors="pt").to("cuda")
    print(f"{Colors.GREEN}[KOREAN OUTPUT]{Colors.ENDC}")
    _ = model.generate(**inputs, streamer=text_streamer, **gen_kwargs)
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    # Test 2: English Wikipedia Article
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"Test 2: English Wikipedia Article - Artificial Intelligence")
    print(f"{'='*70}{Colors.ENDC}\n")
    
    test_prompt = wikipedia_prompt_english.format("Artificial Intelligence", "")
    inputs = tokenizer([test_prompt], return_tensors="pt").to("cuda")
    print(f"{Colors.GREEN}[ENGLISH OUTPUT]{Colors.ENDC}")
    _ = model.generate(**inputs, streamer=text_streamer, **gen_kwargs)
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    # Test 3: Korean Instruction (Kimchi)
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"Test 3: Korean Instruction - Explain about Kimchi")
    print(f"{'='*70}{Colors.ENDC}")
    print(f"{Colors.CYAN}Prompt (Translation): Instruction: Explain about kimchi, a traditional Korean food. / Response:{Colors.ENDC}\n")
    
    test_prompt = alpaca_prompt_korean.format("한국의 전통 음식인 김치에 대해 설명하세요.", "")
    inputs = tokenizer([test_prompt], return_tensors="pt").to("cuda")
    print(f"{Colors.GREEN}[KOREAN OUTPUT]{Colors.ENDC}")
    _ = model.generate(**inputs, streamer=text_streamer, **gen_kwargs)
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    # Test 4: English Instruction (Thanksgiving)
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"Test 4: English Instruction - Explain about Thanksgiving Turkey")
    print(f"{'='*70}{Colors.ENDC}\n")
    
    test_prompt = alpaca_prompt_english.format("Explain about Thanksgiving turkey, a traditional American food.", "")
    inputs = tokenizer([test_prompt], return_tensors="pt").to("cuda")
    print(f"{Colors.GREEN}[ENGLISH OUTPUT]{Colors.ENDC}")
    _ = model.generate(**inputs, streamer=text_streamer, **gen_kwargs)
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    # Additional Korean tests
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"Test 5: Korean Instruction - Explain about Seoul")
    print(f"{'='*70}{Colors.ENDC}")
    print(f"{Colors.CYAN}Prompt (Translation): Instruction: Briefly introduce Seoul, the capital of South Korea. / Response:{Colors.ENDC}\n")
    
    test_prompt = alpaca_prompt_korean.format("대한민국의 수도인 서울에 대해 간단히 소개해주세요.", "")
    inputs = tokenizer([test_prompt], return_tensors="pt").to("cuda")
    print(f"{Colors.GREEN}[KOREAN OUTPUT]{Colors.ENDC}")
    _ = model.generate(**inputs, streamer=text_streamer, **gen_kwargs)
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    # Test 6: Korean Instruction (K-pop)
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"Test 6: Korean Instruction - Explain about K-pop")
    print(f"{'='*70}{Colors.ENDC}")
    print(f"{Colors.CYAN}Prompt (Translation): Instruction: Explain what K-pop is. / Response:{Colors.ENDC}\n")
    
    test_prompt = alpaca_prompt_korean.format("K-pop이 무엇인지 설명해주세요.", "")
    inputs = tokenizer([test_prompt], return_tensors="pt").to("cuda")
    print(f"{Colors.GREEN}[KOREAN OUTPUT]{Colors.ENDC}")
    _ = model.generate(**inputs, streamer=text_streamer, **gen_kwargs)
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    print_section("✅ EVALUATION COMPLETE", Colors.GREEN)

def main():
    parser = argparse.ArgumentParser(description="Evaluate Korean Mistral LoRA models")
    parser.add_argument(
        "--model_path",
        type=str,
        default="lora_model",
        help="Path to the saved LoRA model (default: lora_model)"
    )
    parser.add_argument(
        "--pretrained",
        action="store_true",
        help="Load the pretrained model (before SFT) instead of final model"
    )
    parser.add_argument(
        "--max_seq_length",
        type=int,
        default=2048,
        help="Maximum sequence length (default: 2048)"
    )
    parser.add_argument(
        "--load_in_4bit",
        action="store_true",
        default=True,
        help="Load model in 4-bit quantization (default: True)"
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=150,
        help="Maximum number of tokens to generate (default: 150)"
    )
    parser.add_argument(
        "--use_sampling",
        action="store_true",
        help="Use sampling instead of greedy decoding"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7, only used with --use_sampling)"
    )
    parser.add_argument(
        "--top_p",
        type=float,
        default=0.9,
        help="Top-p sampling parameter (default: 0.9, only used with --use_sampling)"
    )
    
    args = parser.parse_args()
    
    # Determine model path
    if args.pretrained:
        model_path = "lora_model_pretrained"
        print(f"{Colors.YELLOW}Loading PRETRAINED model (before instruction finetuning){Colors.ENDC}")
    else:
        model_path = args.model_path
        print(f"{Colors.YELLOW}Loading FINETUNED model (after instruction finetuning){Colors.ENDC}")
    
    # Check if model exists
    if not os.path.exists(model_path):
        print(f"{Colors.RED}Error: Model path '{model_path}' does not exist!{Colors.ENDC}")
        print(f"{Colors.YELLOW}Make sure you've run the training script first.{Colors.ENDC}")
        return
    
    print_section("🚀 KOREAN MISTRAL MODEL EVALUATION", Colors.HEADER)
    
    # Load model
    model, tokenizer = load_model(
        model_path=model_path,
        max_seq_length=args.max_seq_length,
        load_in_4bit=args.load_in_4bit
    )
    
    # Display GPU info
    import torch
    print_section("💾 GPU MEMORY STATS", Colors.YELLOW)
    gpu_stats = torch.cuda.get_device_properties(0)
    reserved_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
    max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
    print(f"GPU: {gpu_stats.name}")
    print(f"Max memory: {max_memory} GB")
    print(f"Reserved memory: {reserved_memory} GB")
    
    # Run evaluation
    run_evaluation(
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_p=args.top_p,
        use_sampling=args.use_sampling
    )
    
    print(f"\n{Colors.CYAN}{'='*70}")
    print(f"💡 Tips:")
    print(f"{'='*70}{Colors.ENDC}")
    print(f"• Compare pretrained vs finetuned: Run with --pretrained flag")
    print(f"• Adjust generation: Use --max_new_tokens")
    print(f"• Enable sampling: Use --use_sampling --temperature 0.7 --top_p 0.9")
    print(f"• Example: python evaluate_model.py --pretrained --max_new_tokens 300")
    print()

if __name__ == "__main__":
    main()

