"""
Live manual cases for GPT-5 Native Tools Agent.

These cases demonstrate web_search with the OpenRouter format and require
OPENROUTER_API_KEY.
"""

import json
import logging
import sys
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent import GPT5NativeAgent, GPT5AgentChain
from config import Config

# Set up logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)


class TestGPT5Agent:
    """Live manual case suite for GPT-5 Native Tools Agent"""
    
    def __init__(self):
        """Initialize manual case suite"""
        if not Config.validate():
            raise ValueError("Invalid configuration. Please check your .env file")
        
        self.agent = GPT5NativeAgent(
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL,
            model=Config.MODEL_NAME
        )
        self.results = []
    
    def test_web_search_basic(self) -> Dict[str, Any]:
        """
        Test Case 1: Basic web search
        """
        print("\n" + "="*60)
        print("TEST 1: Basic Web Search")
        print("="*60)
        
        request = """Search for the latest information about GPT-5 capabilities and features."""
        
        result = self.agent.process_request(
            request,
            use_tools=True,
            reasoning_effort="low"
        )
        
        self._print_result(result)
        return result
    
    def test_web_search_with_analysis(self) -> Dict[str, Any]:
        """
        Test Case 2: Web search with analysis request
        """
        print("\n" + "="*60)
        print("TEST 2: Web Search with Analysis")
        print("="*60)
        
        request = """Search for current cryptocurrency market trends and Bitcoin price. 
        Then analyze the data to identify patterns and provide insights."""
        
        result = self.agent.process_request(
            request,
            use_tools=True,
            reasoning_effort="medium"
        )
        
        self._print_result(result)
        return result
    
    def test_complex_research(self) -> Dict[str, Any]:
        """
        Test Case 3: Complex research task
        """
        print("\n" + "="*60)
        print("TEST 3: Complex Research Task")
        print("="*60)
        
        request = """Research the current state of renewable energy adoption globally.
        Find statistics on solar, wind, and hydroelectric capacity.
        Analyze growth trends and project future adoption rates.
        Provide a comprehensive summary with data-driven insights."""
        
        result = self.agent.process_request(
            request,
            use_tools=True,
            reasoning_effort="high"
        )
        
        self._print_result(result)
        return result
    
    def test_search_and_code(self) -> Dict[str, Any]:
        """
        Test Case 4: Search and code generation
        """
        print("\n" + "="*60)
        print("TEST 4: Search and Code Generation")
        print("="*60)
        
        request = """Search for the latest Python web frameworks in 2025.
        Then create a simple comparison table and sample code for the top 3 frameworks."""
        
        result = self.agent.process_request(
            request,
            use_tools=True,
            reasoning_effort="medium"
        )
        
        self._print_result(result)
        return result
    
    def test_reasoning_efforts(self) -> List[Dict[str, Any]]:
        """
        Test Case 5: Compare different reasoning efforts
        """
        print("\n" + "="*60)
        print("TEST 5: Reasoning Effort Comparison")
        print("="*60)
        
        request = "What are the implications of quantum computing on current encryption methods?"
        
        results = []
        for effort in ["low", "medium", "high"]:
            print(f"\n--- Testing with {effort} reasoning effort ---")
            result = self.agent.process_request(
                request,
                use_tools=True,
                reasoning_effort=effort
            )
            self._print_result(result)
            results.append({
                "effort": effort,
                "result": result
            })
        
        return results
    
    def test_search_and_analyze_method(self) -> Dict[str, Any]:
        """
        Test Case 6: Using the search_and_analyze convenience method
        """
        print("\n" + "="*60)
        print("TEST 6: Search and Analyze Method")
        print("="*60)
        
        analysis_code = """
# Analyze stock market data
import statistics

# Sample data processing
prices = [100, 102, 98, 105, 103, 107, 104]
returns = [(prices[i] - prices[i-1])/prices[i-1] * 100 for i in range(1, len(prices))]

avg_return = statistics.mean(returns)
volatility = statistics.stdev(returns)

print(f"Average Return: {avg_return:.2f}%")
print(f"Volatility: {volatility:.2f}%")
"""
        
        result = self.agent.search_and_analyze(
            topic="Current S&P 500 performance and market outlook for 2025",
            analysis_code=analysis_code
        )
        
        self._print_result(result)
        return result
    
    def test_agent_chain(self) -> List[Dict[str, Any]]:
        """
        Test Case 7: Chain multiple requests
        """
        print("\n" + "="*60)
        print("TEST 7: Agent Chain")
        print("="*60)
        
        chain = GPT5AgentChain(self.agent)
        
        # Step 1: Research
        chain.add_step(
            "Search for information about the latest AI developments in 2025",
            use_tools=True,
            reasoning_effort="low"
        )
        
        # Step 2: Deep dive
        chain.add_step(
            "Based on the previous findings, search for more details about the most promising AI breakthrough",
            use_tools=True,
            reasoning_effort="medium"
        )
        
        # Step 3: Analysis
        chain.add_step(
            "Analyze the impact of these AI developments on various industries",
            use_tools=True,
            reasoning_effort="high"
        )
        
        results = chain.execute()
        
        for i, step_result in enumerate(results, 1):
            print(f"\n--- Chain Step {i} ---")
            self._print_result(step_result["result"])
        
        return results
    
    def _print_result(self, result: Dict[str, Any]):
        """
        Pretty print test result
        
        Args:
            result: Test result dictionary
        """
        if result["success"]:
            print(f"\n✅ Test Passed")
            print(f"\nResponse Preview:")
            print("-"*60)
            response = result["response"]
            if len(response) > 500:
                print(response[:500] + "...")
            else:
                print(response)
            print("-"*60)
            
            if result.get("usage"):
                usage = result["usage"]
                print(f"\n📊 Token Usage:")
                print(f"  - Input: {usage.get('input_tokens', 'N/A')}")
                print(f"  - Output: {usage.get('output_tokens', 'N/A')}")
                print(f"  - Total: {usage.get('total_tokens', 'N/A')}")
                if usage.get("input_tokens_details"):
                    print(f"  - Cached: {usage['input_tokens_details'].get('cached_tokens', 0)}")
                if usage.get("output_tokens_details"):
                    print(f"  - Reasoning: {usage['output_tokens_details'].get('reasoning_tokens', 0)}")
        else:
            print(f"\n❌ Test Failed")
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    def run_all_tests(self):
        """Run all live manual cases"""
        print("\n" + "="*60)
        print("RUNNING GPT-5 NATIVE TOOLS MANUAL CASES")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Model: {Config.MODEL_NAME}")
        print("="*60)
        
        case_methods = [
            ("Basic Web Search", self.test_web_search_basic),
            ("Web Search with Analysis", self.test_web_search_with_analysis),
            ("Complex Research", self.test_complex_research),
            ("Search and Code", self.test_search_and_code),
            ("Reasoning Efforts", self.test_reasoning_efforts),
            ("Search and Analyze Method", self.test_search_and_analyze_method),
            ("Agent Chain", self.test_agent_chain)
        ]
        
        results_summary = []
        
        for case_name, case_method in case_methods:
            try:
                print(f"\n🧪 Running: {case_name}")
                result = case_method()
                
                # Handle different result types
                if isinstance(result, list):
                    # For tests that return multiple results
                    if all(isinstance(r, dict) and "result" in r for r in result):
                        success = all(r["result"]["success"] for r in result)
                    else:
                        success = all(r.get("success", False) for r in result if isinstance(r, dict))
                else:
                    success = result.get("success", False)
                
                results_summary.append({
                    "case": case_name,
                    "success": success,
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"Manual case {case_name} failed with exception: {str(e)}")
                results_summary.append({
                    "case": case_name,
                    "success": False,
                    "error": str(e)
                })
        
        # Print summary
        print("\n" + "="*60)
        print("MANUAL CASE SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in results_summary if r["success"])
        total = len(results_summary)
        
        for result in results_summary:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{result['case']}: {status}")
        
        print(f"\nTotal: {passed}/{total} manual cases passed")
        print("="*60)
        
        return results_summary


def run_single_test(test_name: str = "basic"):
    """
    Run a single live manual case
    
    Args:
        test_name: Name of manual case to run
    """
    tester = TestGPT5Agent()
    
    test_map = {
        "basic": tester.test_web_search_basic,
        "analysis": tester.test_web_search_with_analysis,
        "complex": tester.test_complex_research,
        "code": tester.test_search_and_code,
        "reasoning": tester.test_reasoning_efforts,
        "search_analyze": tester.test_search_and_analyze_method,
        "chain": tester.test_agent_chain
    }
    
    if test_name in test_map:
        test_map[test_name]()
    else:
        print(f"Unknown test: {test_name}")
        print(f"Available tests: {', '.join(test_map.keys())}")


if __name__ == "__main__":
    # Check configuration first
    Config.display()
    
    if not Config.validate():
        print("\n❌ Configuration validation failed!")
        print("Please set up your .env file with OPENROUTER_API_KEY")
        sys.exit(1)
    
    # Run manual cases
    if len(sys.argv) > 1:
        # Run specific test
        run_single_test(sys.argv[1])
    else:
        # Run all tests
        tester = TestGPT5Agent()
        tester.run_all_tests()
