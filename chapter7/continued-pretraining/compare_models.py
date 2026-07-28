# -*- coding: utf-8 -*-
"""
Compare baseline → pretrained → finetuned Korean Mistral models (3-way comparison)
Shows progression from original model to final Korean-capable model
"""

import argparse

# 说明：unsloth / torch 等重型依赖在函数内按需导入，
# 这样 `python compare_models.py --help` 无需 GPU 环境即可查看参数。

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
    print(f"\n{color}{Colors.BOLD}{'='*80}")
    print(f"{title}")
    print(f"{'='*80}{Colors.ENDC}\n")

def load_baseline_model(base_model="unsloth/mistral-7b-v0.3", max_seq_length=2048):
    """Load the original Mistral model (before any training)"""
    from unsloth import FastLanguageModel
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)
    return model, tokenizer

def load_model(model_path, max_seq_length=2048):
    """Load a trained LoRA model"""
    from unsloth import FastLanguageModel
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_path,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)
    return model, tokenizer

def generate_text(model, tokenizer, prompt, max_new_tokens=150, temperature=0.3):
    """Generate text without streaming"""
    inputs = tokenizer([prompt], return_tensors="pt").to("cuda")
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        use_cache=True,
        do_sample=True,
        temperature=temperature,
        pad_token_id=tokenizer.eos_token_id,
    )
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Remove the prompt from the output
    response = generated_text[len(prompt):].strip()
    return response

def compare_on_prompt(baseline_model, baseline_tokenizer,
                     pretrained_model, pretrained_tokenizer, 
                     finetuned_model, finetuned_tokenizer,
                     prompt, test_name, prompt_translation=None,
                     max_new_tokens=150, temperature=0.3):
    """Compare three models on the same prompt"""
    
    print(f"\n{Colors.BOLD}{'='*80}")
    print(f"{test_name}")
    print(f"{'='*80}{Colors.ENDC}")
    
    if prompt_translation:
        print(f"{Colors.CYAN}Prompt (Translation): {prompt_translation}{Colors.ENDC}\n")
    
    print(f"{Colors.YELLOW}Generating from BASELINE model (original Mistral)...{Colors.ENDC}")
    baseline_output = generate_text(
        baseline_model, baseline_tokenizer, prompt, 
        max_new_tokens, temperature
    )
    
    print(f"{Colors.YELLOW}Generating from PRETRAINED model (after Korean training)...{Colors.ENDC}")
    pretrained_output = generate_text(
        pretrained_model, pretrained_tokenizer, prompt, 
        max_new_tokens, temperature
    )
    
    print(f"{Colors.YELLOW}Generating from FINETUNED model (after instruction tuning)...{Colors.ENDC}")
    finetuned_output = generate_text(
        finetuned_model, finetuned_tokenizer, prompt,
        max_new_tokens, temperature
    )
    
    # Display all three outputs
    print(f"\n{Colors.RED}┌─ BASELINE MODEL (Original Mistral) ───────────────────────────────┐{Colors.ENDC}")
    print(f"{Colors.RED}│{Colors.ENDC}")
    for line in baseline_output.split('\n'):
        print(f"{Colors.RED}│{Colors.ENDC} {line}")
    print(f"{Colors.RED}│{Colors.ENDC}")
    print(f"{Colors.RED}└────────────────────────────────────────────────────────────────────┘{Colors.ENDC}\n")
    
    print(f"{Colors.GREEN}┌─ PRETRAINED MODEL (After Korean Wikipedia) ───────────────────────┐{Colors.ENDC}")
    print(f"{Colors.GREEN}│{Colors.ENDC}")
    for line in pretrained_output.split('\n'):
        print(f"{Colors.GREEN}│{Colors.ENDC} {line}")
    print(f"{Colors.GREEN}│{Colors.ENDC}")
    print(f"{Colors.GREEN}└────────────────────────────────────────────────────────────────────┘{Colors.ENDC}\n")
    
    print(f"{Colors.CYAN}┌─ FINETUNED MODEL (After Instruction Tuning) ──────────────────────┐{Colors.ENDC}")
    print(f"{Colors.CYAN}│{Colors.ENDC}")
    for line in finetuned_output.split('\n'):
        print(f"{Colors.CYAN}│{Colors.ENDC} {line}")
    print(f"{Colors.CYAN}│{Colors.ENDC}")
    print(f"{Colors.CYAN}└────────────────────────────────────────────────────────────────────┘{Colors.ENDC}\n")

def parse_args():
    parser = argparse.ArgumentParser(
        description="对比韩语 Mistral 的三个阶段模型：基础模型 → 继续预训练 → 指令微调。"
                    "在同一批中韩英提示上并排生成，直观展示韩语能力的提升与英语能力的保留。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--base_model", type=str, default="unsloth/mistral-7b-v0.3",
                        help="基础（未训练）模型名称")
    parser.add_argument("--pretrained_path", type=str, default="lora_model_pretrained",
                        help="继续预训练后保存的 LoRA 模型目录")
    parser.add_argument("--finetuned_path", type=str, default="lora_model",
                        help="指令微调后保存的最终 LoRA 模型目录")
    parser.add_argument("--max_seq_length", type=int, default=2048,
                        help="最大序列长度")
    parser.add_argument("--max_new_tokens", type=int, default=150,
                        help="每次生成的最大 token 数")
    parser.add_argument("--temperature", type=float, default=0.3,
                        help="采样温度（越低越确定）")
    return parser.parse_args()


def main():
    args = parse_args()

    print_section("🔬 KOREAN MISTRAL 3-WAY MODEL COMPARISON", Colors.HEADER)
    print(f"{Colors.YELLOW}This script compares three model stages:{Colors.ENDC}")
    print(f"  1. {Colors.RED}Baseline{Colors.ENDC} - Original Mistral (no Korean training)")
    print(f"  2. {Colors.GREEN}Pretrained{Colors.ENDC} - After Korean Wikipedia training")
    print(f"  3. {Colors.CYAN}Finetuned{Colors.ENDC} - After instruction tuning")
    print(f"\n{Colors.CYAN}Generation settings: temperature={args.temperature}, do_sample=True (no repetition_penalty){Colors.ENDC}\n")
    
    # Load all three models
    print_section("📥 LOADING MODELS", Colors.BLUE)
    
    print(f"{Colors.YELLOW}Loading baseline model (original Mistral v0.3)...{Colors.ENDC}")
    baseline_model, baseline_tokenizer = load_baseline_model(args.base_model, args.max_seq_length)
    print(f"{Colors.GREEN}✓ Baseline model loaded{Colors.ENDC}")
    
    print(f"\n{Colors.YELLOW}Loading pretrained model (after Korean pretraining)...{Colors.ENDC}")
    pretrained_model, pretrained_tokenizer = load_model(args.pretrained_path, args.max_seq_length)
    print(f"{Colors.GREEN}✓ Pretrained model loaded{Colors.ENDC}")
    
    print(f"\n{Colors.YELLOW}Loading finetuned model (after instruction tuning)...{Colors.ENDC}")
    finetuned_model, finetuned_tokenizer = load_model(args.finetuned_path, args.max_seq_length)
    print(f"{Colors.GREEN}✓ Finetuned model loaded{Colors.ENDC}")
    
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
    
    print_section("🧪 RUNNING 3-WAY COMPARISONS", Colors.CYAN)
    
    # Test 1: Korean Wikipedia
    compare_on_prompt(
        baseline_model, baseline_tokenizer,
        pretrained_model, pretrained_tokenizer,
        finetuned_model, finetuned_tokenizer,
        wikipedia_prompt_korean.format("인공지능", ""),
        "Test 1: Korean Wikipedia - Artificial Intelligence (인공지능)",
        "Wikipedia Article / Title: Artificial Intelligence / Article:",
        max_new_tokens=args.max_new_tokens, temperature=args.temperature
    )
    
    # Test 2: English Wikipedia - Preservation Check
    compare_on_prompt(
        baseline_model, baseline_tokenizer,
        pretrained_model, pretrained_tokenizer,
        finetuned_model, finetuned_tokenizer,
        wikipedia_prompt_english.format("Artificial Intelligence", ""),
        "Test 2: English Wikipedia - Artificial Intelligence (Preservation Check)",
        None,
        max_new_tokens=args.max_new_tokens, temperature=args.temperature
    )
    
    # Test 3: Korean Instruction - Kimchi
    compare_on_prompt(
        baseline_model, baseline_tokenizer,
        pretrained_model, pretrained_tokenizer,
        finetuned_model, finetuned_tokenizer,
        alpaca_prompt_korean.format("한국의 전통 음식인 김치에 대해 설명하세요.", ""),
        "Test 3: Korean Instruction - Explain Kimchi",
        "Instruction: Explain about kimchi, a traditional Korean food. / Response:",
        max_new_tokens=args.max_new_tokens, temperature=args.temperature
    )
    
    # Test 4: Korean Instruction - Seoul
    compare_on_prompt(
        baseline_model, baseline_tokenizer,
        pretrained_model, pretrained_tokenizer,
        finetuned_model, finetuned_tokenizer,
        alpaca_prompt_korean.format("대한민국의 수도인 서울에 대해 간단히 소개해주세요.", ""),
        "Test 4: Korean Instruction - Introduce Seoul",
        "Instruction: Briefly introduce Seoul, the capital of South Korea. / Response:",
        max_new_tokens=args.max_new_tokens, temperature=args.temperature
    )
    
    # Test 5: English Instruction - Preservation Check
    compare_on_prompt(
        baseline_model, baseline_tokenizer,
        pretrained_model, pretrained_tokenizer,
        finetuned_model, finetuned_tokenizer,
        alpaca_prompt_english.format("Explain about Thanksgiving turkey, a traditional American food.", ""),
        "Test 5: English Instruction - Thanksgiving Turkey (Preservation Check)",
        None,
        max_new_tokens=args.max_new_tokens, temperature=args.temperature
    )
    
    print_section("📊 COMPARISON COMPLETE", Colors.GREEN)
    
    print(f"{Colors.CYAN}{'='*80}")
    print(f"💡 What to Look For:")
    print(f"{'='*80}{Colors.ENDC}")
    
    print(f"\n{Colors.RED}Baseline Model (Red boxes - Original Mistral):{Colors.ENDC}")
    print(f"  • Korean: Should be POOR - repetitive, nonsensical")
    print(f"  • English: Should be GOOD - this is the starting point")
    print(f"  • Shows what model knows BEFORE any Korean training")
    
    print(f"\n{Colors.GREEN}Pretrained Model (Green boxes - After Korean Wikipedia):{Colors.ENDC}")
    print(f"  • Korean: Should show IMPROVED fluency and vocabulary")
    print(f"  • Better Korean sentence structure")
    print(f"  • Weak instruction-following (only learned language, not how to follow instructions)")
    print(f"  • English: Should REMAIN strong (no catastrophic forgetting)")
    
    print(f"\n{Colors.CYAN}Finetuned Model (Cyan boxes - After Instruction Tuning):{Colors.ENDC}")
    print(f"  • Korean: Should be FLUENT with GOOD instruction-following")
    print(f"  • More structured and complete responses")
    print(f"  • Directly answers questions")
    print(f"  • English: Should REMAIN strong")
    
    print(f"\n{Colors.YELLOW}Key Progression to Observe:{Colors.ENDC}")
    print(f"  📊 Korean Quality:    {Colors.RED}Poor{Colors.ENDC} → {Colors.GREEN}Better{Colors.ENDC} → {Colors.CYAN}Best{Colors.ENDC}")
    print(f"  📊 Instruction:       {Colors.RED}Weak{Colors.ENDC} → {Colors.GREEN}Weak{Colors.ENDC} → {Colors.CYAN}Strong{Colors.ENDC}")
    print(f"  📊 English Quality:   {Colors.RED}Good{Colors.ENDC} → {Colors.GREEN}Good{Colors.ENDC} → {Colors.CYAN}Good{Colors.ENDC}")
    print(f"  📊 Repetition:        {Colors.RED}High{Colors.ENDC} → {Colors.GREEN}Medium{Colors.ENDC} → {Colors.CYAN}Low{Colors.ENDC}")
    
    print(f"\n{Colors.YELLOW}This demonstrates:{Colors.ENDC}")
    print(f"  ✓ Continued pretraining successfully teaches new language (Korean)")
    print(f"  ✓ Instruction tuning teaches how to follow instructions in the new language")
    print(f"  ✓ English capability is preserved throughout (no catastrophic forgetting)")
    print(f"  ✓ Both Wikipedia and Instruction tasks show English preservation")
    print(f"  ✓ Two-stage approach is necessary: language first, then instruction-following")
    print(f"\n{Colors.CYAN}💡 Note: Compare the English tests (Tests 2 & 5) across all three models.")
    print(f"All three should perform similarly well, proving no English degradation.{Colors.ENDC}")
    print()

if __name__ == "__main__":
    main()
