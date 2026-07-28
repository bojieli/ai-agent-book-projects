"""
Evaluation script for the distilled prompt model.

This script evaluates the student model's performance on language classification
without providing the detailed prompt.

The student model (Qwen3-30B-A3B-Instruct) has been distilled from the teacher
(Qwen3-30B-A3B-Thinking) which used a 2000+ token prompt. After distillation,
the student responds directly without needing the prompt or thinking process.
"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from tqdm import tqdm


def load_model(model_path: str, base_model: str = "Qwen/Qwen3-30B-A3B-Instruct-2507"):
    """Load the fine-tuned model with LoRA adapters."""
    print(f"Loading base model: {base_model}")
    print(f"This may take a few minutes for the 30B model...")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        dtype=torch.bfloat16,  # Use 'dtype' instead of deprecated 'torch_dtype'
        device_map="auto",
        trust_remote_code=True,
    )
    
    print(f"Loading LoRA adapters from: {model_path}")
    model = PeftModel.from_pretrained(model, model_path)
    model.eval()
    
    return model, tokenizer

def compute_parse_rate(predicted: int, total: int) -> float:
    """Parseable prediction rate; empty total is 0.0 (not ZeroDivisionError)."""
    return predicted / total if total > 0 else 0.0


def format_pred_label(pred_label: Optional[str]) -> str:
    """Display token for progress lines when the model reply is unparseable."""
    return pred_label or "??"

def parse_language_label(response: str) -> Optional[str]:
    """Extract the language label from model response."""
    # Try to match common patterns
    patterns = [
        r"^([a-z]{2})$",  # Just "en", "fr", etc.
        r"^([a-z]{2})\s*$",  # With trailing whitespace
        r"Final Answer:\s*([a-z]{2})",  # With "Final Answer:" prefix
        r"Language:\s*([a-z]{2})",  # With "Language:" prefix
    ]
    
    response = response.strip().lower()
    for pattern in patterns:
        # response is lower-cased above, so the mixed-case "Final Answer:" /
        # "Language:" patterns only match case-insensitively — without this
        # they are unreachable and such answers score as unparseable.
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # If response is short and looks like a language code
    if len(response) == 2 and response.isalpha():
        return response
    
    return None

def evaluate_model(
    model,
    tokenizer,
    test_sentences: List[str],
    ground_truth_labels: Optional[List[str]] = None,
    max_new_tokens: int = 10,
    temperature: float = 0.0,
) -> Dict:
    """Evaluate the distilled model on test sentences."""
    
    predictions = []
    correct = 0
    total = 0
    
    print("\nEvaluating model...")
    print("="*80)
    
    for idx, sentence in enumerate(test_sentences):
        # Format as user message (no system prompt!)
        messages = [
            {"role": "user", "content": sentence}
        ]
        
        # Apply chat template
        input_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        
        # Tokenize
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature if temperature > 0 else None,
                do_sample=temperature > 0,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )
        
        # Decode
        response = tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:],
            skip_special_tokens=True,
        )
        
        # Parse prediction
        pred_label = parse_language_label(response)
        predictions.append(pred_label)
        
        # Check correctness and show real-time progress. Rows without ground
        # truth (teacher never labeled the sentence) are excluded from the
        # accuracy denominator — counting them as wrong deflated the reported
        # fidelity by exactly the unmatched fraction.
        if ground_truth_labels and idx < len(ground_truth_labels) and ground_truth_labels[idx] is not None:
            gt_label = ground_truth_labels[idx]
            is_correct = pred_label == gt_label
            if is_correct:
                correct += 1
            total += 1
            
            # Show every sample in real-time
            status = "✓" if is_correct else "✗"
            status_color = "✓" if is_correct else "✗"
            
            # Truncate sentence for display
            display_sentence = sentence if len(sentence) <= 60 else sentence[:57] + "..."
            
            print(f"{status_color} [{idx+1:4d}/{len(test_sentences)}] "
                  f"Pred: {format_pred_label(pred_label):>2s} | GT: {gt_label:>2s} | "
                  f"Acc: {correct}/{total} ({correct/total*100:5.1f}%) | "
                  f"{display_sentence}")
        else:
            # No ground truth - just show prediction
            display_sentence = sentence if len(sentence) <= 60 else sentence[:57] + "..."
            print(f"  [{idx+1:4d}/{len(test_sentences)}] "
                  f"Pred: {format_pred_label(pred_label):>2s} | "
                  f"{display_sentence}")
    
    print("="*80)
    print(f"Evaluation completed: {len(test_sentences)} samples processed")
    
    # Calculate metrics
    results = {
        "predictions": predictions,
        "total": len(test_sentences),
        "predicted": sum(1 for p in predictions if p is not None),
        "unparseable": sum(1 for p in predictions if p is None),
    }
    
    if ground_truth_labels:
        results["accuracy"] = correct / total if total > 0 else 0.0
        results["correct"] = correct
        results["evaluated"] = total
        
        # Build confusion matrix
        results["confusion_matrix"] = build_confusion_matrix(
            predictions, ground_truth_labels, test_sentences
        )
    
    return results

def build_confusion_matrix(predictions: List[str], ground_truth: List[str], 
                           sentences: List[str]) -> Dict:
    """
    Build confusion matrix and identify problematic languages.
    
    Returns:
        Dict with confusion matrix, per-language stats, and error examples
    """
    # Get all unique labels (rows without ground truth are excluded).
    # Pair each prediction with its ground truth, then surface unparseable
    # predictions (pred is None, counted as the "None" column below) as an
    # explicit label. Otherwise confusion_matrix_2d drops that column and a
    # true-label row's cells no longer sum to that language's total.
    labeled = [(p, g) for p, g in zip(predictions, ground_truth) if g is not None]
    all_labels = sorted(set(g for _, g in labeled) | set(p for p, _ in labeled if p))
    if any(p is None for p, _ in labeled):
        all_labels = all_labels + ["None"]

    # Initialize confusion matrix
    confusion = defaultdict(lambda: defaultdict(int))
    per_language_stats = defaultdict(lambda: {"correct": 0, "total": 0, "errors": []})

    # Build matrix
    for idx, (pred, gt, sentence) in enumerate(zip(predictions, ground_truth, sentences)):
        if gt is None:
            continue
        if pred is None:
            pred = "None"

        confusion[gt][pred] += 1
        per_language_stats[gt]["total"] += 1
        
        if pred == gt:
            per_language_stats[gt]["correct"] += 1
        else:
            # Store error examples
            if len(per_language_stats[gt]["errors"]) < 5:  # Keep first 5 errors per language
                per_language_stats[gt]["errors"].append({
                    "sentence": sentence,
                    "predicted": pred,
                    "ground_truth": gt,
                    "index": idx,
                })
    
    # Calculate per-language accuracy
    language_accuracy = {}
    for lang in all_labels:
        stats = per_language_stats[lang]
        if stats["total"] > 0:
            accuracy = stats["correct"] / stats["total"]
            language_accuracy[lang] = {
                "accuracy": accuracy,
                "correct": stats["correct"],
                "total": stats["total"],
                "errors": stats["errors"],
            }
    
    # Sort languages by accuracy (worst first)
    sorted_languages = sorted(
        language_accuracy.items(),
        key=lambda x: x[1]["accuracy"]
    )
    
    # Create 2D confusion matrix as a proper array
    confusion_matrix_2d = []
    for true_label in all_labels:
        row = []
        for pred_label in all_labels:
            count = confusion.get(true_label, {}).get(pred_label, 0)
            row.append(count)
        confusion_matrix_2d.append(row)
    
    return {
        "confusion_matrix": {gt: dict(preds) for gt, preds in confusion.items()},  # Dict format
        "confusion_matrix_2d": confusion_matrix_2d,  # 2D array format
        "all_labels": all_labels,
        "per_language_accuracy": language_accuracy,
        "worst_performing_languages": sorted_languages[:5],  # Top 5 worst
        "all_languages_sorted": sorted_languages,  # All languages sorted by accuracy
    }

def print_confusion_matrix(confusion_data: Dict):
    """Pretty print confusion matrix and analysis."""
    print("\n" + "="*80)
    print("CONFUSION MATRIX")
    print("="*80)
    
    # Get labels and matrix
    labels = confusion_data["all_labels"]
    confusion = confusion_data["confusion_matrix"]
    
    # Print matrix header - use shorter labels for display
    print("\n     ", end="")
    for label in labels:
        # Truncate long labels for display
        display_label = label if len(label) <= 3 else label[:3]
        print(f"{display_label:>4s}", end="")
    print("  | Total")
    print("  " + "-" * (len(labels) * 4 + 10))
    
    # Print matrix rows
    for true_label in labels:
        # Truncate long labels for display
        display_label = true_label if len(true_label) <= 2 else true_label[:2]
        print(f"{display_label:>2s} | ", end="")
        row_total = sum(confusion.get(true_label, {}).values())
        
        for pred_label in labels:
            count = confusion.get(true_label, {}).get(pred_label, 0)
            if count > 0:
                if true_label == pred_label:
                    print(f"\033[92m{count:4d}\033[0m", end="")  # Green for diagonal
                else:
                    print(f"\033[91m{count:4d}\033[0m", end="")  # Red for errors
            else:
                print(f"   .", end="")
        print(f"  | {row_total:4d}")
    
    # Print per-language accuracy
    print(f"\n{'='*80}")
    print("PER-LANGUAGE ACCURACY")
    print("="*80)
    
    lang_acc = confusion_data["per_language_accuracy"]
    sorted_langs = sorted(lang_acc.items(), key=lambda x: x[1]["accuracy"])
    
    for lang, stats in sorted_langs:
        acc = stats["accuracy"] * 100
        symbol = "✓" if acc >= 90 else "⚠️" if acc >= 70 else "✗"
        print(f"{symbol} {lang:>2s}: {acc:5.1f}% ({stats['correct']:4d}/{stats['total']:4d})")
    
    # Identify problematic languages
    print(f"\n{'='*80}")
    print("MOST PROBLEMATIC LANGUAGES (Top 5)")
    print("="*80)
    
    worst_languages = confusion_data["worst_performing_languages"]
    for idx, (lang, stats) in enumerate(worst_languages, 1):
        acc = stats["accuracy"] * 100
        print(f"\n{idx}. Language: {lang} - Accuracy: {acc:.1f}% ({stats['correct']}/{stats['total']})")
        
        if stats["errors"]:
            print(f"   Error examples:")
            for err in stats["errors"][:3]:  # Show first 3 errors
                pred_lang = err['predicted']
                sentence_preview = err['sentence'][:50] + "..." if len(err['sentence']) > 50 else err['sentence']
                print(f"     - Predicted {pred_lang} (should be {lang}): {sentence_preview}")
    
    print("\n" + "="*80)

def main():
    parser = argparse.ArgumentParser(
        description="评估蒸馏后的学生模型（无提示、直接作答）在语言分类上的表现",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default="./models/prompt_distillation_trl",
        help="训练得到的 LoRA adapter 路径",
    )
    parser.add_argument(
        "--base_model",
        type=str,
        default="Qwen/Qwen3-30B-A3B-Instruct-2507",
        help="学生基座模型名称（非思考型）",
    )
    parser.add_argument(
        "--test_file",
        type=str,
        default="./example-data/multilingual.txt",
        help="测试文本文件（每行一句）",
    )
    parser.add_argument(
        "--ground_truth_file",
        type=str,
        default=None,
        help="标准答案标签文件（可选，每行一个）。未提供时会尝试从训练数据中读取",
    )
    parser.add_argument(
        "--train_data_file",
        type=str,
        default="./data/prompt_distillation_lang.jsonl",
        help="训练数据文件，未提供 ground_truth_file 时从中提取教师标签作为基准",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="./evaluation_results.json",
        help="评估结果的保存路径",
    )
    parser.add_argument(
        "--max_samples",
        type=int,
        default=None,
        help="最多评估的样本数（用于快速测试）",
    )
    
    args = parser.parse_args()
    
    # Load model
    model, tokenizer = load_model(args.model_path, args.base_model)
    
    # Load test data
    print(f"\nLoading test sentences from: {args.test_file}")
    with open(args.test_file, "r", encoding="utf-8") as f:
        test_sentences = [line.strip() for line in f if line.strip()]
    
    # Load ground truth
    ground_truth = None
    if args.ground_truth_file:
        print(f"Loading ground truth from: {args.ground_truth_file}")
        with open(args.ground_truth_file, "r", encoding="utf-8") as f:
            ground_truth = [line.strip() for line in f if line.strip()]
    elif args.train_data_file and Path(args.train_data_file).exists():
        # Try to extract ground truth from training data
        print(f"Loading ground truth from training data: {args.train_data_file}")
        ground_truth = []
        sentence_to_label = {}
        
        with open(args.train_data_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    messages = data.get("messages", [])
                    if len(messages) >= 2:
                        user_content = messages[0].get("content", "")
                        assistant_content = messages[1].get("content", "")
                        sentence_to_label[user_content] = assistant_content
        
        # Match test sentences to ground truth labels. None = no ground truth
        # for this sentence; such rows are skipped in accuracy and the
        # confusion matrix instead of being scored as wrong under a phantom
        # "?" language.
        for sentence in test_sentences:
            ground_truth.append(sentence_to_label.get(sentence))

        matched = sum(1 for gt in ground_truth if gt is not None)
        print(f"Matched {matched}/{len(test_sentences)} test sentences to training data")
        
        if matched == 0:
            print("⚠️  Warning: No ground truth matched. Results will not show accuracy.")
            ground_truth = None
    
    # Limit samples if requested
    if args.max_samples:
        test_sentences = test_sentences[:args.max_samples]
        if ground_truth:
            ground_truth = ground_truth[:args.max_samples]
        print(f"Limiting evaluation to {args.max_samples} samples")
    
    print(f"Total test sentences: {len(test_sentences)}")
    
    # Evaluate
    results = evaluate_model(
        model=model,
        tokenizer=tokenizer,
        test_sentences=test_sentences,
        ground_truth_labels=ground_truth,
    )
    
    # Print confusion matrix analysis
    if "confusion_matrix" in results:
        print_confusion_matrix(results["confusion_matrix"])
    
    # Print summary
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"Model: {args.base_model}")
    print(f"Adapter: {args.model_path}")
    print(f"\nPerformance:")
    print(f"  Total samples: {results['total']}")
    print(f"  Successfully predicted: {results['predicted']}")
    print(f"  Unparseable responses: {results['unparseable']}")
    rate = compute_parse_rate(results["predicted"], results["total"])
    print(f"  Parse rate: {rate * 100:.2f}%")
    
    if "accuracy" in results:
        print(f"\n  Overall Accuracy: {results['accuracy']*100:.2f}%")
        print(f"  Correct: {results['correct']}/{results['evaluated']}")
        print(f"\n💡 The model responds directly without the 2000+ token prompt!")
    
    # Save comprehensive results to JSON
    output = {
        "model_path": args.model_path,
        "base_model": args.base_model,
        "test_file": args.test_file,
        "train_data_file": args.train_data_file,
        "timestamp": str(Path(args.model_path).stat().st_mtime) if Path(args.model_path).exists() else None,
        "summary": {
            "total_samples": results["total"],
            "predicted": results["predicted"],
            "unparseable": results["unparseable"],
            "parse_rate": compute_parse_rate(results["predicted"], results["total"]),
        },
        "predictions": results["predictions"],
    }
    
    # Add accuracy metrics if available
    if "accuracy" in results:
        output["summary"]["accuracy"] = results["accuracy"]
        output["summary"]["correct"] = results["correct"]
        output["summary"]["evaluated"] = results["evaluated"]
    
    # Add confusion matrix and language analysis
    if "confusion_matrix" in results:
        cm_data = results["confusion_matrix"]
        output["confusion_matrix"] = {
            "matrix_dict": cm_data["confusion_matrix"],  # Dict format for readability
            "matrix_2d": cm_data["confusion_matrix_2d"],  # 2D array for analysis
            "labels": cm_data["all_labels"],  # Label order for the 2D matrix
        }
        
        # Save ALL languages with their full statistics
        output["all_languages_accuracy"] = {
            lang: {
                "accuracy": stats["accuracy"],
                "correct": stats["correct"],
                "total": stats["total"],
                "error_examples": stats["errors"],
            }
            for lang, stats in cm_data["all_languages_sorted"]
        }
        
        # Also save per-language accuracy (same data, different format)
        output["per_language_accuracy"] = {
            lang: {
                "accuracy": stats["accuracy"],
                "correct": stats["correct"],
                "total": stats["total"],
                "error_examples": stats["errors"],
            }
            for lang, stats in cm_data["per_language_accuracy"].items()
        }
        
        # Save top 5 worst for quick reference
        output["worst_performing_languages"] = [
            {
                "language": lang,
                "accuracy": stats["accuracy"],
                "correct": stats["correct"],
                "total": stats["total"],
                "error_examples": stats["errors"],
            }
            for lang, stats in cm_data["worst_performing_languages"]
        ]
    
    # Save to file
    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n📁 Complete results saved to: {args.output_file}")
    print(f"   Includes: predictions, confusion matrix, per-language stats, error examples")

if __name__ == "__main__":
    main()

