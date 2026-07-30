#!/usr/bin/env python3
"""
Main script for Log Sanitization using Local LLM
"""

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

from config import OUTPUT_DIR, OLLAMA_MODEL
import regex_sanitizer
from samples import SAMPLES


def main(test_id: Optional[str] = None, limit: Optional[int] = None,
         model: str = OLLAMA_MODEL):
    """
    Main function to run log sanitization
    
    Args:
        test_id: Specific test case ID to process (optional)
        limit: Maximum number of test cases to process (optional)
    """
    print("🚀 Starting Log Sanitization with Local LLM")
    print("=" * 60)

    # Initialize components
    try:
        from agent import LogSanitizationAgent
        from test_loader import TestCaseLoader

        print("📦 Loading test cases from user-memory-evaluation...")
        loader = TestCaseLoader()

        print(f"🤖 Initializing Ollama agent (model: {model})...")
        agent = LogSanitizationAgent(model=model)

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return 1
    
    # Get test cases to process
    if test_id:
        # Process specific test case
        print(f"\n📋 Processing specific test case: {test_id}")
        conversations = loader.get_test_case_conversations(test_id)
        
        if not conversations:
            print(f"❌ Test case {test_id} not found or has no conversations")
            return 1
        
        agent.process_test_case(test_id, conversations)
        
    else:
        # Process Layer 3 test cases (most complex, likely to have PII)
        print("\n📋 Getting Layer 3 test cases...")
        test_cases = loader.get_layer3_test_cases()
        
        if not test_cases:
            print("❌ No Layer 3 test cases found")
            return 1
        
        print(f"Found {len(test_cases)} Layer 3 test cases")
        
        # Apply limit if specified
        if limit:
            test_cases = test_cases[:limit]
            print(f"Processing first {limit} test cases")
        
        # Process each test case
        for i, tc in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] Test Case: {tc['test_id']}")
            print(f"   Title: {tc['title']}")
            print(f"   Conversations: {tc['num_conversations']}")
            
            # Get conversation histories
            conversations = loader.get_test_case_conversations(tc['test_id'])
            
            if conversations:
                agent.process_test_case(tc['test_id'], conversations)
            else:
                print(f"   ⚠️  No conversations found for {tc['test_id']}")
    
    print("\n" + "=" * 60)
    print("✅ Log Sanitization Complete!")
    print(f"📁 Results saved to: {OUTPUT_DIR}")
    
    return 0


def demo_regex_mode():
    """离线规则脱敏演示：对多个代表性样本展示 before/after 与类别汇总"""
    print("🎯 离线规则脱敏演示 (regex 模式，无需 Ollama)")
    print("=" * 60)
    print(f"共 {len(SAMPLES)} 个代表性样本，覆盖密钥 / 令牌 / 私钥 / PII 等类别\n")

    total = Counter()
    total_hits = 0
    for name, text in SAMPLES:
        redacted, findings = regex_sanitizer.sanitize(text)
        regex_sanitizer.print_report(name, text, redacted, findings)
        total.update(regex_sanitizer.summarize(findings))
        total_hits += len(findings)

    print(f"\n{'=' * 64}")
    print("脱敏类别汇总 (across all samples)")
    print("=" * 64)
    for category, count in total.most_common():
        label = regex_sanitizer.CATEGORY_LABELS.get(category, category)
        print(f"   {label:<16} {count} 处")
    print(f"\n   合计脱敏 {total_hits} 处敏感信息，覆盖 {len(total)} 个类别")
    return 0


def sanitize_file(input_path: str, output_path: Optional[str] = None,
                  mode: str = "regex", model: str = OLLAMA_MODEL):
    """对任意日志文件执行脱敏，结果写入输出文件"""
    in_file = Path(input_path)
    if not in_file.exists():
        print(f"❌ 输入文件不存在: {input_path}")
        return 1

    text = in_file.read_text(encoding="utf-8", errors="replace")
    out_file = Path(output_path) if output_path else in_file.with_suffix(in_file.suffix + ".sanitized")

    if mode == "regex":
        print(f"🔍 使用离线规则引擎脱敏: {input_path}")
        redacted, findings = regex_sanitizer.sanitize(text)
        counts = regex_sanitizer.summarize(findings)
    else:
        print(f"🔍 使用本地 LLM ({model}) 脱敏: {input_path}")
        try:
            from agent import LogSanitizationAgent
        except Exception as e:
            print(f"❌ 加载 LLM 引擎失败: {e}")
            return 1
        agent = LogSanitizationAgent(model=model)
        pii_values, _ = agent.detect_pii(text)
        redacted, _ = agent.sanitize_text(text, pii_values)
        counts = Counter({"pii": len(pii_values)})
        findings = pii_values

    out_file.write_text(redacted, encoding="utf-8")

    print(f"\n✅ 已写入脱敏结果: {out_file}")
    print(f"   共脱敏 {sum(counts.values())} 处敏感信息")
    for category, count in counts.most_common():
        label = regex_sanitizer.CATEGORY_LABELS.get(category, category)
        print(f"   - {label}: {count} 处")
    return 0


def demo_mode(model: str = OLLAMA_MODEL):
    """Run a quick demo with sample PII-containing text (本地 LLM 模式)"""
    print("🎯 Running Demo Mode (LLM)")
    print("=" * 60)

    # Create a sample conversation with Level 3 PII
    sample_conversation = {
        'conversation_id': 'demo_001',
        'timestamp': '2024-01-01 10:00:00',
        'messages': [
            {
                'role': 'user',
                'content': 'I need to update my information. My SSN is 123-45-6789.'
            },
            {
                'role': 'assistant',
                'content': 'I can help you update your information. Can you confirm your credit card?'
            },
            {
                'role': 'user',
                'content': 'Yes, it\'s 4532 1234 5678 9012. Also, my medical record number is MRN-789456.'
            },
            {
                'role': 'assistant',
                'content': 'Thank you. I\'ve noted your SSN ending in 6789 and card ending in 9012.'
            },
            {
                'role': 'user',
                'content': 'Great. My driver\'s license is DL-123456789 and passport is P987654321.'
            }
        ]
    }
    
    try:
        from agent import LogSanitizationAgent
        agent = LogSanitizationAgent(model=model)
        print("\n📝 Sample conversation created with Level 3 PII")
        print("🔍 Detecting and sanitizing PII...\n")
        
        result = agent.sanitize_conversation(sample_conversation, 'demo')
        
        print("\n" + "=" * 60)
        print("DEMO RESULTS")
        print("=" * 60)
        print(f"PII Items Found: {len(result['pii_found'])}")
        for pii in result['pii_found']:
            print(f"  - {pii}")
        
        print(f"\nReplacements Made: {result['replacements_made']}")
        print("\n--- SANITIZED TEXT ---")
        print(result['sanitized_text'])
        
        # Save demo results
        agent.save_sanitized_log('demo', [result])
        agent.metrics_collector.save_metrics()
        agent.metrics_collector.print_summary()
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="日志脱敏实验：从 Agent 日志 / 工具输出中检测并脱敏敏感信息"
                    "（API 密钥、令牌、私钥、信用卡、身份证、手机号、邮箱等）。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
两种脱敏引擎：
  regex  离线规则引擎（默认），基于正则 + 校验算法，无需 Ollama，结果确定、速度快
  llm    本地 LLM 引擎，通过 Ollama 调用小模型（默认 qwen3:0.6b）语义识别 Level 3 PII

常用示例：
  python main.py --demo                     # 离线跑内置样本，展示 before/after 与脱敏汇总
  python main.py --demo --mode llm          # 用本地 LLM 跑演示样本
  python main.py --input app.log            # 离线脱敏一个日志文件
  python main.py --input app.log -o out.log # 指定输出文件
  python main.py --input app.log --mode llm # 用本地 LLM 脱敏文件
  python main.py                            # (LLM) 批量处理 chapter3 评测框架中的 Layer 3 用例
  python main.py --test-id layer3_01_travel_coordination
  python main.py --limit 3 --model qwen3:1.7b
""",
    )

    parser.add_argument(
        '--mode',
        choices=['regex', 'llm'],
        default='regex',
        help='脱敏引擎：regex=离线规则(默认)，llm=本地 Ollama 模型。'
             '（注意：不带 --demo/--input 的批量评测路径始终使用 LLM）'
    )

    parser.add_argument(
        '-i', '--input',
        type=str,
        metavar='FILE',
        help='待脱敏的日志文件路径（配合 --mode 选择引擎）'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        metavar='FILE',
        help='脱敏结果输出文件路径（仅 --input 模式生效，默认写到 <输入>.sanitized）'
    )

    parser.add_argument(
        '--model',
        type=str,
        default=OLLAMA_MODEL,
        help=f'Ollama 模型名（默认 {OLLAMA_MODEL}），仅 llm 模式生效'
    )

    parser.add_argument(
        '--test-id',
        type=str,
        help='仅处理指定 ID 的评测用例（LLM 批量路径）'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='最多处理多少个评测用例（LLM 批量路径）'
    )

    parser.add_argument(
        '--demo',
        action='store_true',
        help='运行演示：默认离线规则引擎跑内置代表性样本；加 --mode llm 则用本地 LLM'
    )

    args = parser.parse_args()

    if args.input:
        exit_code = sanitize_file(args.input, args.output, mode=args.mode, model=args.model)
    elif args.demo:
        if args.mode == 'llm':
            exit_code = demo_mode(model=args.model)
        else:
            exit_code = demo_regex_mode()
    else:
        exit_code = main(test_id=args.test_id, limit=args.limit, model=args.model)

    sys.exit(exit_code)
