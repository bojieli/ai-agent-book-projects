#!/usr/bin/env python3
"""
Test script to verify PDF parsing and currency conversion
"""

import os
import sys

from _bootstrap import add_project_root

add_project_root()

from agent import ContextAwareAgent, ContextMode

def test_pdf_with_currencies():
    """Test PDF parsing with currency conversion"""
    
    print("\n" + "="*60)
    print("🧪 PDF PARSING & CURRENCY CONVERSION TEST")
    print("="*60)
    
    # Check API key
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("❌ No API key found. Set SILICONFLOW_API_KEY environment variable.")
        return False
    
    # Create agent
    agent = ContextAwareAgent(api_key, ContextMode.FULL)
    
    # Test task
    task = """
    Analyze the expense report at fixtures/pdfs/simple_expense_report.pdf
    
    Extract the following expenses mentioned in the document:
    - US Office: $2,500,000 USD
    - UK Office: £1,800,000 GBP
    - Japan Office: ¥380,000,000 JPY
    - EU Office: €2,100,000 EUR
    - Singapore Office: S$3,200,000 SGD
    
    Convert all amounts to USD and calculate the total.
    
    FINAL ANSWER: Provide the total expenses in USD.
    """
    
    print("📋 Task: Parse PDF and convert multiple currencies to USD")
    print("-"*40)
    
    try:
        # Execute task
        result = agent.execute_task(task, max_iterations=5)
        
        print("\n" + "="*40)
        print("RESULTS:")
        print("="*40)
        print(f"Success: {result.get('success', False)}")
        print(f"Iterations: {result.get('iterations', 0)}")
        print(f"Tool Calls: {len(result['trajectory'].tool_calls)}")
        
        # Show tool calls made
        print("\n📊 Tool Calls Made:")
        for i, tc in enumerate(result['trajectory'].tool_calls, 1):
            print(f"{i}. {tc.tool_name}")
            if tc.tool_name == "parse_pdf":
                print(f"   - PDF: {tc.arguments.get('url', 'N/A')}")
                if tc.result and 'num_pages' in tc.result:
                    print(f"   - Pages: {tc.result['num_pages']}")
            elif tc.tool_name == "convert_currency":
                print(f"   - {tc.arguments.get('amount', 0)} {tc.arguments.get('from_currency', '')} → {tc.arguments.get('to_currency', '')}")
                if tc.result and 'converted_amount' in tc.result:
                    print(f"   - Result: {tc.result['converted_amount']}")
            elif tc.tool_name == "calculate":
                print(f"   - Expression: {tc.arguments.get('expression', '')}")
                if tc.result and 'result' in tc.result:
                    print(f"   - Result: {tc.result['result']}")
        
        if result.get('final_answer'):
            print("\n✅ Final Answer:")
            print("-"*40)
            print(result['final_answer'])
        
        if result.get('error'):
            print(f"\n❌ Error: {result['error']}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"\n❌ Exception: {str(e)}")
        return False


if __name__ == "__main__":
    # Ensure PDFs exist
    if not os.path.exists("fixtures/pdfs/simple_expense_report.pdf"):
        print("⚠️ Creating sample PDFs...")
        os.system("python create_sample_pdf.py")
    
    # Run test
    success = test_pdf_with_currencies()
    sys.exit(0 if success else 1)
