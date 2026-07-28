"""
Data generation script for prompt distillation using vLLM.

This script generates training data for prompt distillation by using a teacher model
to generate language classification labels with a detailed prompt, which will then be
used to train a student model that internalizes the prompt.

Based on the tinker cookbook prompt distillation recipe.
"""

import argparse
import asyncio
import json
import os
import re
from pathlib import Path
from typing import Optional

from tqdm.asyncio import tqdm_asyncio

# 注意：vllm / SamplingParams 在 generate_distillation_data() 内部按需导入，
# 这样即便未安装 vllm（如离线查看 --help 时）也能正常展示命令行帮助。

LANGUAGE_CLASSIFICATION_PROMPT = """You are a precise language classifier.

Goal: Classify the language of the provided text into exactly one of these labels:
ar (Arabic), de (German), el (Greek), en (English), es (Spanish), fr (French),
hi (Hindi), ru (Russian), tr (Turkish), ur (Urdu), vi (Vietnamese),
zh (Chinese - Simplified), ot (Other/Unknown).

Instructions:
1) Preprocess carefully (without changing the intended meaning):
   - Trim whitespace.
   - Ignore URLs, emails, file paths, hashtags, user handles, and emojis.
   - Ignore numbers, math expressions, and standalone punctuation.
   - If there is code, IGNORE code syntax (keywords, operators, braces) and focus ONLY on human language in comments and string literals.
   - Preserve letters and diacritics; do NOT strip accents.
   - If after ignoring the above there are no alphabetic letters left, output 'ot'.

2) Script-based rules (highest priority):
   - Devanagari script → hi.
   - Greek script → el.
   - Cyrillic script → ru.
   - Han characters (中文) → zh. (Treat Traditional as zh too.)
   - Arabic script → ar vs ur:
       • If Urdu-only letters appear (e.g., ے, ڑ, ں, ھ, ٹ, ڈ, کھ, گ, چ with Urdu forms), or clear Urdu words, choose ur.
       • Otherwise choose ar.
   (If multiple scripts appear, pick the script that contributes the majority of alphabetic characters. If tied, go to step 5.)

3) Latin-script heuristics (use when text is mainly Latin letters):
   - vi: presence of Vietnamese-specific letters/diacritics (ă â ê ô ơ ư đ, plus dense diacritics across many words).
   - tr: presence of Turkish-specific letters (ı İ ğ Ğ ş Ş ç Ç ö Ö ü Ü) and common function words (ve, bir, için, değil, ama, çok).
   - de: presence of umlauts (ä ö ü) or ß and common function words (und, der, die, das, nicht, ist).
   - es: presence of ñ, ¿, ¡ and common words (y, de, la, el, es, no, por, para, con, gracias, hola).
   - fr: frequent French diacritics (é è ê à ç ô â î û ù) and common words (et, le, la, les, des, une, est, avec, pour, merci, bonjour).
   - en: default among Latin languages if strong evidence for others is absent, but ONLY if English function words are present (the, and, is, are, to, of, in, for, on, with). If evidence is insufficient for any Latin language, prefer 'ot' over guessing.

4) Named entities & loanwords:
   - Do NOT decide based on a single proper noun, brand, or place name.
   - Require at least two function words or repeated language-specific signals (diacritics/letters) before assigning a Latin-language label.

5) Mixed-language text:
   - Determine the dominant language by counting indicative tokens (language-specific letters/diacritics/function words) AFTER preprocessing.
   - If two or more languages are equally dominant or the text is a deliberate multi-language mix, return 'ot'.

6) Very short or noisy inputs:
   - If the text is ≤2 meaningful words or too short to be confident, return 'ot' unless there is a very strong language-specific signal (e.g., "bonjour" → fr, "hola" → es).

7) Transliteration/romanization:
   - If Hindi/Urdu/Arabic/Chinese/Russian/Greek is written purely in Latin letters (romanized) without clear, repeated language-specific cue words, return 'ot'. (Only classify as hi/ur/ar/zh/ru/el when native scripts or highly distinctive romanized patterns are clearly present.)

8) Code-heavy inputs:
   - If the text is mostly code with minimal or no natural-language comments/strings, return 'ot'.
   - If comments/strings clearly indicate a language per rules above, use that label.

9) Ambiguity & confidence:
   - When in doubt, choose 'ot' rather than guessing.

Text to classify:
{text}

Output format:
- Respond with EXACTLY one line: "Final Answer: xx"
- Where xx ∈ {{ar, de, el, en, es, fr, hi, ru, tr, ur, vi, zh, ot}} and nothing else.
"""


def parse_final_answer(response: str, debug: bool = False) -> Optional[str]:
    """
    Parse the final answer from the model response.
    For Thinking models, extract from <think>...</think> tags or after them.
    """
    # For Thinking models, the response may have <think></think> tags
    # Remove thinking content and focus on the final answer
    response_stripped = response.strip()
    
    # Remove <think>...</think> content if present
    response_cleaned = re.sub(r'<think>.*?</think>', '', response_stripped, flags=re.DOTALL)
    response_cleaned = response_cleaned.strip()
    
    # Also try the original response
    candidates = [response_cleaned, response_stripped]
    
    valid_labels = {'ar', 'de', 'el', 'en', 'es', 'fr', 'hi', 'ru', 'tr', 'ur', 'vi', 'zh', 'ot'}
    
    # Try multiple patterns to extract language label
    patterns = [
        r"Final Answer:\s*(\w{2})",  # Standard format
        r"Final Answer:\s*([a-z]{2})",  # Lowercase only
        r"Answer:\s*(\w{2})",  # Without "Final"
        r"Language:\s*(\w{2})",  # "Language: xx"
        r"^([a-z]{2})$",  # Just the label alone
        r"\b([a-z]{2})\b\s*$",  # Label at the end with word boundary
        r"is:\s*(\w{2})",  # "is: xx"
        r"→\s*(\w{2})",  # "→ xx"
    ]
    
    for candidate in candidates:
        candidate_lower = candidate.lower()
        
        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, candidate_lower, re.MULTILINE)
            if match:
                label = match.group(1)
                if label in valid_labels:
                    if debug:
                        print(f"    [DEBUG] Matched pattern '{pattern}' -> '{label}'")
                    return label
        
        # Special case: check if the entire response is just a language code
        if len(candidate) <= 3 and candidate_lower in valid_labels:
            if debug:
                print(f"    [DEBUG] Matched entire response as label -> '{candidate_lower}'")
            return candidate_lower
    
    if debug:
        print(f"    [DEBUG] No pattern matched.")
        print(f"    [DEBUG] Response length: {len(response_stripped)}")
        print(f"    [DEBUG] Cleaned response: '{response_cleaned[:300]}'")
        print(f"    [DEBUG] Original response: '{response_stripped[:300]}'")
    
    return None


async def generate_distillation_data(
    input_file: str,
    output_file: str,
    model_name: str = "Qwen/Qwen3-30B-A3B-Thinking-2507",
    temperature: float = 0.15,
    max_tokens: int = 4096,
    tensor_parallel_size: int = 1,
    max_retries: int = 3,
):
    """
    Generate prompt distillation training data.
    
    Args:
        input_file: Path to file containing sentences to classify (one per line)
        output_file: Path to save the generated training data (JSONL format)
        model_name: Teacher model to use for generating labels
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        tensor_parallel_size: Number of GPUs to use for tensor parallelism
    """
    print(f"Loading input sentences from {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        sentences = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(sentences)} sentences")
    if not sentences:
        print("Input file has no sentences to process, skipping data generation.")
        return

    from vllm import LLM, SamplingParams

    # Initialize vLLM model
    print(f"Initializing teacher model: {model_name}")
    print(f"Using tensor parallelism across {tensor_parallel_size} GPU(s)")
    
    # Get tokenizer to use proper chat template
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    
    llm = LLM(
        model=model_name,
        tensor_parallel_size=tensor_parallel_size,
        trust_remote_code=True,
        gpu_memory_utilization=0.90,  # Use 90% of GPU memory for better throughput
        max_model_len=32768,  # Match training max length
        enable_prefix_caching=True,  # Cache the system prompt
    )
    
    # Set sampling parameters - use Qwen3 recommended settings
    # For Thinking models, we need to allow enough tokens for reasoning
    sampling_params = SamplingParams(
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=0.8,
        top_k=20,
        # Don't use custom stop sequences - let model finish naturally
        skip_special_tokens=False,  # Keep special tokens for thinking models
    )
    
    # Initial generation
    print("Generating labels with teacher model...")
    results = {}  # sentence -> (response, final_answer)
    failed_indices = []
    failed_examples = []  # Store examples for debugging
    
    # Format prompts using proper chat template
    print("Formatting prompts with Qwen3 chat template...")
    formatted_prompts = []
    for sentence in sentences:
        messages = [
            {
                "role": "user",
                "content": LANGUAGE_CLASSIFICATION_PROMPT.format(text=sentence)
            }
        ]
        # Use tokenizer's chat template
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        formatted_prompts.append(prompt_text)
    
    print(f"Sample formatted prompt:")
    print(formatted_prompts[0])
    
    outputs = llm.generate(formatted_prompts, sampling_params)
    
    for idx, (sentence, output) in enumerate(zip(sentences, outputs)):
        response = output.outputs[0].text
        # Enable debug mode for first few failures
        debug_mode = len(failed_examples) < 3
        final_answer = parse_final_answer(response, debug=debug_mode)
        
        if final_answer:
            results[sentence] = (response, final_answer)
        else:
            failed_indices.append(idx)
            # Store first 10 failed examples for debugging
            if len(failed_examples) < 10:
                failed_examples.append({
                    'sentence': sentence,
                    'response': response,
                })
    
    # results is keyed by sentence text, so len(results) counts UNIQUE
    # sentences; the JSONL below writes one row per sentence occurrence. Count
    # rows actually labeled so the reported rate matches the output when the
    # corpus contains duplicate lines (common in language-ID data).
    num_labeled = sum(1 for s in sentences if s in results)
    print(f"\nInitial generation: {num_labeled}/{len(sentences)} successful ({num_labeled/len(sentences)*100:.2f}%)")
    
    # Show debugging info for failed samples
    if failed_examples:
        print(f"\n{'='*60}")
        print("DEBUGGING: Examples of FAILED responses")
        print(f"{'='*60}")
        for i, example in enumerate(failed_examples, 1):
            print(f"\nFailed Example {i}:")
            print(f"  Input: {example['sentence']}")
            print(f"  Response: {example['response']}")
            print(f"  Parsed result: None")
    
    # Show examples of successful responses
    if results:
        print(f"\n{'='*60}")
        print("DEBUGGING: Examples of SUCCESSFUL responses")
        print(f"{'='*60}")
        success_examples = list(results.items())[:3]
        for i, (sentence, (response, label)) in enumerate(success_examples, 1):
            print(f"\nSuccess Example {i}:")
            print(f"  Input: {sentence}")
            print(f"  Response: {response}")
            print(f"  Parsed label: {label}")
    
    # Retry failed generations up to max_retries times
    for retry in range(1, max_retries + 1):
        if not failed_indices:
            break
            
        print(f"\nRetry {retry}/{max_retries}: Regenerating {len(failed_indices)} failed samples...")
        
        # Prepare prompts for failed sentences
        retry_sentences = [sentences[idx] for idx in failed_indices]
        retry_formatted_prompts = []
        for s in retry_sentences:
            messages = [
                {
                    "role": "user",
                    "content": LANGUAGE_CLASSIFICATION_PROMPT.format(text=s)
                }
            ]
            prompt_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            retry_formatted_prompts.append(prompt_text)
        
        # Generate with slightly higher temperature to encourage different outputs
        retry_params = SamplingParams(
            temperature=min(temperature * (1 + retry * 0.1), 0.5),  # Gradually increase temp
            max_tokens=max_tokens,
            top_p=0.8,
            top_k=20,
            skip_special_tokens=False,
        )
        
        retry_outputs = llm.generate(retry_formatted_prompts, retry_params)
        
        # Track newly successful and still-failed indices
        new_failed_indices = []
        for idx, sentence, output in zip(failed_indices, retry_sentences, retry_outputs):
            response = output.outputs[0].text
            final_answer = parse_final_answer(response)
            
            if final_answer:
                results[sentence] = (response, final_answer)
            else:
                new_failed_indices.append(idx)
        
        newly_successful = len(failed_indices) - len(new_failed_indices)
        print(f"  ✓ {newly_successful} more samples successful")
        num_labeled = sum(1 for s in sentences if s in results)
        print(f"  Total successful: {num_labeled}/{len(sentences)} ({num_labeled/len(sentences)*100:.2f}%)")
        
        failed_indices = new_failed_indices
    
    # Save results
    print(f"\nSaving results to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        for sentence in sentences:
            if sentence in results:
                _, final_answer = results[sentence]
                data = {
                    "messages": [
                        {
                            "role": "user",
                            "content": sentence,
                        },
                        {
                            "role": "assistant",
                            "content": final_answer,
                        },
                    ]
                }
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
    
    # Final report
    print(f"\n{'='*60}")
    print("DATA GENERATION COMPLETE")
    print(f"{'='*60}")
    num_labeled = sum(1 for s in sentences if s in results)
    print(f"Total sentences: {len(sentences)}")
    print(f"Valid labels generated: {num_labeled}")
    print(f"Failed after {max_retries} retries: {len(failed_indices)}")
    print(f"Final success rate: {num_labeled/len(sentences)*100:.2f}%")
    print(f"Saved to: {output_file}")
    
    if failed_indices:
        print(f"\n⚠️  Warning: {len(failed_indices)} sentences failed to generate valid labels")
        print("Consider inspecting these samples or adjusting the prompt/temperature")


def main():
    parser = argparse.ArgumentParser(
        description="用教师模型（长提示 + 思考）生成 Prompt 蒸馏训练数据",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default="./example-data/multilingual.txt",
        help="输入文本文件路径（每行一句待分类文本）",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="./data/prompt_distillation_lang.jsonl",
        help="生成的训练数据保存路径（JSONL 格式）",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="Qwen/Qwen3-30B-A3B-Thinking-2507",
        help="教师模型名称（用思考型模型以获得更高准确率）",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.15,
        help="采样温度（与 tinker 保持一致，取 0.15）",
    )
    parser.add_argument(
        "--max_tokens",
        type=int,
        default=4096,
        help="单条生成的最大 token 数",
    )
    parser.add_argument(
        "--tensor_parallel_size",
        type=int,
        default=1,
        help="张量并行使用的 GPU 数（30B 模型在 H100 上建议 2-4）",
    )
    parser.add_argument(
        "--max_retries",
        type=int,
        default=3,
        help="失败样本的最大重试次数",
    )
    
    args = parser.parse_args()
    
    # Create output directory if needed
    output_dir = os.path.dirname(args.output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        raise FileNotFoundError(f"Input file not found: {args.input_file}")
    
    # Generate data
    asyncio.run(
        generate_distillation_data(
            input_file=args.input_file,
            output_file=args.output_file,
            model_name=args.model_name,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            tensor_parallel_size=args.tensor_parallel_size,
            max_retries=args.max_retries,
        )
    )


if __name__ == "__main__":
    main()

