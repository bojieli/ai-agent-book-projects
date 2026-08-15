"""
Prompt 蒸馏「蒸馏前 vs 蒸馏后」量化对比脚本。

本脚本回答实验 7-8 的核心问题：把「长提示 + 思考型教师」蒸馏成「无提示 + 直接
回答的学生」之后，到底省了多少、质量掉了多少？它在 **不加载任何大模型、不联网** 的
前提下，用真实数据算出一张 before/after 对比表：

  1. 输入成本（token）：教师每次调用都要带上完整的语言分类提示（约上千 token），
     学生只需要原始待分类文本。二者的 token 差就是每次调用省下的输入开销。
  2. 任务质量：直接读取 evaluate.py 产出的 evaluation_results.json，得到学生在
     相同输入上「与教师标注的一致率」（即蒸馏保真度）。
  3. 逐条案例：抽取若干条真实样本，并排展示 教师 token / 学生 token / 教师标签 /
     学生预测 / 是否一致，让「多个案例上的 before/after」一目了然。

设计原则：所有数字都来自真实数据与真实分词器，不臆造。延迟（秒级响应时间）需要
在 GPU 上实测，本脚本不做估算，只报告可离线复现的 token 成本与质量。
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


VALID_LABELS = ["ar", "de", "el", "en", "es", "fr", "hi", "ru", "tr", "ur", "vi", "zh", "ot"]


def load_prompt_template(source_file: str) -> str:
    """从 create_data.py 中提取教师使用的语言分类提示模板（避免 import vllm）。"""
    src = Path(source_file).read_text(encoding="utf-8")
    match = re.search(
        r'LANGUAGE_CLASSIFICATION_PROMPT\s*=\s*"""(.*?)"""',
        src,
        re.DOTALL,
    )
    if not match:
        raise ValueError(
            f"无法在 {source_file} 中找到 LANGUAGE_CLASSIFICATION_PROMPT 模板，"
            f"请用 --prompt_source 指定包含该常量的文件。"
        )
    return match.group(1)


def build_token_counter(tokenizer_name: Optional[str]) -> Tuple[Callable[[str], int], str]:
    """
    构造一个 token 计数函数，按优先级回退，保证离线可用。

    返回 (counter, method_description)：
      1) 若指定 --tokenizer，用 HuggingFace 分词器精确计数（GPU 机器上可得到 Qwen 的真实 token 数）。
      2) 否则用 tiktoken 的 o200k_base（GPT-4o/o1 分词器）作近似，可离线复现。
      3) 再退化为「字符数 / 4」的粗略启发式，并明确标注为估算。
    每种方法都会在输出里注明，绝不把近似值当成精确值。
    """
    if tokenizer_name:
        try:
            from transformers import AutoTokenizer

            tok = AutoTokenizer.from_pretrained(tokenizer_name, trust_remote_code=True)
            return (lambda s: len(tok.encode(s))), f"HuggingFace 分词器（精确）: {tokenizer_name}"
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] 无法加载分词器 {tokenizer_name}（{exc}），回退到 tiktoken。", file=sys.stderr)

    try:
        import tiktoken

        enc = tiktoken.get_encoding("o200k_base")
        return (lambda s: len(enc.encode(s))), "tiktoken o200k_base（近似，可离线复现）"
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] tiktoken 不可用（{exc}），回退到字符启发式。", file=sys.stderr)

    return (lambda s: max(1, len(s) // 4)), "字符数/4（粗略估算）"


def load_texts(test_file: str) -> List[str]:
    with open(test_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_teacher_labels(train_data_file: str) -> Dict[str, str]:
    """从蒸馏训练数据（教师标注）中读取 文本 -> 教师标签 的映射。"""
    mapping: Dict[str, str] = {}
    if not Path(train_data_file).exists():
        return mapping
    with open(train_data_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            msgs = data.get("messages", [])
            if len(msgs) >= 2:
                mapping[msgs[0].get("content", "")] = msgs[1].get("content", "")
    return mapping


def load_eval_results(eval_file: str) -> Optional[Dict]:
    if not Path(eval_file).exists():
        return None
    with open(eval_file, "r", encoding="utf-8") as f:
        return json.load(f)


def truncate(text: str, width: int = 42) -> str:
    text = text.replace("\n", " ")
    return text if len(text) <= width else text[: width - 1] + "…"


def compare(
    prompt_template: str,
    texts: List[str],
    teacher_labels: Dict[str, str],
    eval_results: Optional[Dict],
    count_tokens: Callable[[str], int],
    token_method: str,
    num_examples: int,
) -> Dict:
    n = len(texts)

    # 固定提示开销（模板本身，不含待分类文本）
    fixed_overhead = count_tokens(prompt_template.format(text=""))

    teacher_input_total = 0
    student_input_total = 0
    per_text_tokens: List[Tuple[int, int]] = []  # (teacher_tokens, student_tokens)
    for text in texts:
        teacher_prompt = prompt_template.format(text=text)
        t_tok = count_tokens(teacher_prompt)
        s_tok = count_tokens(text)
        teacher_input_total += t_tok
        student_input_total += s_tok
        per_text_tokens.append((t_tok, s_tok))

    if n == 0:
        teacher_avg = student_avg = reduction_pct = 0.0
        ratio = float("inf")
    else:
        teacher_avg = teacher_input_total / n
        student_avg = student_input_total / n
        reduction_pct = (
            100.0 * (1 - student_input_total / teacher_input_total)
            if teacher_input_total
            else 0.0
        )
        ratio = (
            teacher_input_total / student_input_total
            if student_input_total
            else float("inf")
        )

    # 学生预测（与 test_file 逐行对齐）
    student_preds: Optional[List[Optional[str]]] = None
    accuracy = None
    correct = evaluated = None
    if eval_results:
        student_preds = eval_results.get("predictions")
        summary = eval_results.get("summary", {})
        accuracy = summary.get("accuracy")
        correct = summary.get("correct")
        evaluated = summary.get("evaluated")

    # 逐条案例：优先覆盖不同语言，并尽量各带上一致/不一致的例子
    examples: List[Dict] = []
    seen_labels = set()
    for idx, text in enumerate(texts):
        teacher_label = teacher_labels.get(text, "?")
        student_pred = (
            student_preds[idx] if student_preds and idx < len(student_preds) else None
        )
        key = teacher_label
        if key in seen_labels and len(examples) >= num_examples:
            continue
        if len(examples) >= num_examples:
            break
        if key in seen_labels:
            continue
        seen_labels.add(key)
        t_tok, s_tok = per_text_tokens[idx]
        examples.append(
            {
                "text": text,
                "teacher_tokens": t_tok,
                "student_tokens": s_tok,
                "teacher_label": teacher_label,
                "student_pred": student_pred,
                "match": (student_pred == teacher_label) if student_pred else None,
            }
        )

    return {
        "num_cases": n,
        "token_method": token_method,
        "fixed_prompt_overhead": fixed_overhead,
        "teacher_input_total": teacher_input_total,
        "teacher_input_avg": teacher_avg,
        "student_input_total": student_input_total,
        "student_input_avg": student_avg,
        "input_token_reduction_pct": reduction_pct,
        "teacher_student_ratio": ratio,
        "student_accuracy": accuracy,
        "student_correct": correct,
        "student_evaluated": evaluated,
        "examples": examples,
    }


def print_report(r: Dict) -> None:
    line = "=" * 78
    print("\n" + line)
    print("Prompt 蒸馏：蒸馏前 vs 蒸馏后 量化对比")
    print(line)
    print(f"样本数            : {r['num_cases']}")
    print(f"Token 计数方式    : {r['token_method']}")
    print(f"固定提示开销      : {r['fixed_prompt_overhead']} tokens（模板本身，每次调用都要重复付费）")

    print("\n" + "-" * 78)
    print("一、输入成本（每次调用的输入 token）")
    print("-" * 78)
    print(f"{'维度':<24}{'教师(长提示+思考)':>20}{'学生(无提示)':>18}")
    print(f"{'单条平均输入 token':<24}{r['teacher_input_avg']:>20.1f}{r['student_input_avg']:>18.1f}")
    print(f"{'全量总输入 token':<24}{r['teacher_input_total']:>20,}{r['student_input_total']:>18,}")
    print(
        f"\n→ 输入 token 降低 {r['input_token_reduction_pct']:.1f}%"
        f"（教师是学生的 {r['teacher_student_ratio']:.1f} 倍）。"
    )
    print("  按输入 token 计费的 API 上，这一项直接等比例降低费用；教师端还有未计入的")
    print("  思考（CoT）输出 token，实际差距只会更大。延迟需在 GPU 上实测，此处不估算。")

    print("\n" + "-" * 78)
    print("二、任务质量（学生在相同输入上与教师标注的一致率 = 蒸馏保真度）")
    print("-" * 78)
    if r["student_accuracy"] is not None:
        print(
            f"教师(基准) : 100.00%   学生(蒸馏后) : {r['student_accuracy'] * 100:.2f}%"
            f"  ({r['student_correct']}/{r['student_evaluated']})"
        )
        print(
            f"→ 无提示、无思考的学生保留了教师约 {r['student_accuracy'] * 100:.1f}% 的判断，"
            f"质量损失约 {(1 - r['student_accuracy']) * 100:.1f} 个百分点。"
        )
    else:
        print("未找到 evaluation_results.json（学生尚未评估）。先运行 evaluate.py 生成，")
        print("再回来看这一栏。本栏缺失不影响上面的输入成本对比。")

    print("\n" + "-" * 78)
    print(f"三、逐条案例（{len(r['examples'])} 例）")
    print("-" * 78)
    print(f"{'待分类文本':<44}{'教师tok':>8}{'学生tok':>8}{'教师':>6}{'学生':>6}{'一致':>6}")
    for ex in r["examples"]:
        if ex["match"] is None:
            mark = "—"
        else:
            mark = "✓" if ex["match"] else "✗"
        pred = ex["student_pred"] if ex["student_pred"] else "—"
        print(
            f"{truncate(ex['text']):<44}"
            f"{ex['teacher_tokens']:>8}{ex['student_tokens']:>8}"
            f"{ex['teacher_label']:>6}{pred:>6}{mark:>6}"
        )
    print(line + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Prompt 蒸馏「蒸馏前 vs 蒸馏后」量化对比：离线算出输入成本、任务质量与逐条案例",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--test_file",
        type=str,
        default="./example-data/multilingual.txt",
        help="待分类文本文件（每行一句），作为对比的输入集合",
    )
    parser.add_argument(
        "--train_data_file",
        type=str,
        default="./data/prompt_distillation_lang.jsonl",
        help="蒸馏训练数据（教师标注），用于取教师标签作为质量基准",
    )
    parser.add_argument(
        "--eval_results",
        type=str,
        default="./evaluation_results.json",
        help="evaluate.py 产出的评估结果，用于读取学生的一致率（可选）",
    )
    parser.add_argument(
        "--prompt_source",
        type=str,
        default="./create_data.py",
        help="包含教师提示模板 LANGUAGE_CLASSIFICATION_PROMPT 的源文件",
    )
    parser.add_argument(
        "--tokenizer",
        type=str,
        default=None,
        help="可选：HuggingFace 分词器名/路径（如 Qwen/Qwen3-30B-A3B-Instruct-2507）。"
        "指定后用它精确计数；不指定则用 tiktoken 近似，保证离线可跑",
    )
    parser.add_argument(
        "--num_examples",
        type=int,
        default=10,
        help="逐条案例展示的条数（尽量覆盖不同语言）",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default=None,
        help="可选：把对比结果（含逐条案例）保存为 JSON 的路径",
    )
    args = parser.parse_args()

    if not os.path.exists(args.test_file):
        raise FileNotFoundError(f"待分类文本文件不存在: {args.test_file}")
    if not os.path.exists(args.prompt_source):
        raise FileNotFoundError(f"提示模板源文件不存在: {args.prompt_source}")

    prompt_template = load_prompt_template(args.prompt_source)
    texts = load_texts(args.test_file)
    teacher_labels = load_teacher_labels(args.train_data_file)
    eval_results = load_eval_results(args.eval_results)
    count_tokens, token_method = build_token_counter(args.tokenizer)

    if not teacher_labels:
        print(
            f"[warn] 未从 {args.train_data_file} 读到教师标注，逐条案例的教师标签将显示为 '?'。",
            file=sys.stderr,
        )
    if eval_results is None:
        print(
            f"[warn] 未找到 {args.eval_results}，将只给出输入成本对比，跳过质量一栏。",
            file=sys.stderr,
        )

    report = compare(
        prompt_template=prompt_template,
        texts=texts,
        teacher_labels=teacher_labels,
        eval_results=eval_results,
        count_tokens=count_tokens,
        token_method=token_method,
        num_examples=args.num_examples,
    )

    print_report(report)

    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"📁 对比结果已保存到: {args.output_file}")


if __name__ == "__main__":
    main()
