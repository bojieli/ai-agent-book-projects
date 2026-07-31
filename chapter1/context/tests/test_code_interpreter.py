#!/usr/bin/env python3
"""
Test the code_interpreter tool with the agent
"""

import os
from agent import ContextAwareAgent, ContextMode

def test_code_interpreter():
    """Test code interpreter integration"""
    
    print("\n" + "="*60)
    print("🧪 CODE INTERPRETER TEST")
    print("="*60)
    
    # Check API key
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("⚠️ No API key set, using mock test")
        # Test just the tool directly
        from agent import ToolRegistry
        tools = ToolRegistry()
        
        code = """
# Calculate total expenses
expenses_usd = {
    'US Office': 2500000,
    'UK Office (converted)': 2278481.01,
    'Japan Office (converted)': 2541806.02,
    'EU Office (converted)': 2282608.70,
    'Singapore Office (converted)': 2388059.70
}

# Calculate total
total = sum(expenses_usd.values())

# Calculate percentages
for office, amount in expenses_usd.items():
    percentage = (amount / total) * 100
    print(f"{office}: ${amount:,.2f} ({percentage:.2f}%)")

print(f"\\nTotal Expenses: ${total:,.2f}")

# Calculate after 12% reduction
reduced_total = total * 0.88
savings = total - reduced_total
print(f"After 12% reduction: ${reduced_total:,.2f}")
print(f"Savings: ${savings:,.2f}")

result = {
    'total': total,
    'reduced': reduced_total,
    'savings': savings
}
"""
        
        result = tools.code_interpreter(code)
        if result['success']:
            print("✅ Code interpreter executed successfully!")
            print("\nOutput:")
            print(result['output'])
            print(f"\nResult dictionary: {result['result']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        return
    
    # Test with full agent
    agent = ContextAwareAgent(api_key, ContextMode.FULL)
    
    task = """
    Calculate the following:
    
    Given these expenses:
    - US: $2,500,000
    - UK: $2,278,481
    - Japan: $2,541,806
    - EU: $2,282,609
    - Singapore: $2,388,060
    
    Use the code_interpreter tool to:
    1. Calculate the total expenses
    2. Calculate what percentage each office represents
    3. Calculate the new totals if we apply a 12% cost reduction
    
    FINAL ANSWER: Provide the total, the percentage breakdown, and the reduced total.
    """
    
    print("Running task with agent...")
    print("Task: Calculate totals and percentages using code_interpreter")
    print("-"*40)
    
    result = agent.execute_task(task, max_iterations=3)
    
    print(f"\nSuccess: {result.get('success', False)}")
    print(f"Tool calls made: {len(result['trajectory'].tool_calls)}")
    
    # Check if code_interpreter was used
    code_interpreter_used = any(
        tc.tool_name == 'code_interpreter' 
        for tc in result['trajectory'].tool_calls
    )
    
    if code_interpreter_used:
        print("✅ Code interpreter was used!")
        # Show the code that was executed
        for tc in result['trajectory'].tool_calls:
            if tc.tool_name == 'code_interpreter':
                print("\nExecuted code:")
                print("-"*40)
                print(tc.arguments.get('code', 'N/A'))
                print("-"*40)
                if tc.result and tc.result.get('output'):
                    print("\nOutput:")
                    print(tc.result['output'])
    else:
        print("⚠️ Code interpreter was not used")
    
    if result.get('final_answer'):
        print("\n📝 Final Answer:")
        print(result['final_answer'])


if __name__ == "__main__":
    test_code_interpreter()
