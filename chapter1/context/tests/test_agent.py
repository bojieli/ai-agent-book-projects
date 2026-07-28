#!/usr/bin/env python3
"""
Test script for Context-Aware Agent
Validates installation and basic functionality
"""

import sys
import json
from agent import ContextAwareAgent, ContextMode, ToolRegistry
import unittest
from unittest.mock import MagicMock, patch


class TestToolRegistry(unittest.TestCase):
    """Test the tool registry functions"""
    
    def test_calculator(self):
        """Test calculator tool"""
        tools = ToolRegistry()
        
        # Basic arithmetic
        result = tools.calculate("2 + 2")
        self.assertEqual(result["result"], 4)
        
        # Complex expression
        result = tools.calculate("(10 * 5) + (20 / 4)")
        self.assertEqual(result["result"], 55.0)
        
        # With math functions
        result = tools.calculate("sqrt(16) + abs(-5)")
        self.assertEqual(result["result"], 9.0)
        
    def test_currency_converter(self):
        """Test currency conversion tool"""
        tools = ToolRegistry()
        
        # USD to EUR
        result = tools.convert_currency(100, "USD", "EUR")
        self.assertIn("converted_amount", result)
        self.assertIn("exchange_rate", result)
        self.assertGreater(result["converted_amount"], 0)
        
        # Invalid currency
        result = tools.convert_currency(100, "XXX", "YYY")
        self.assertIn("error", result)
    
    def test_pdf_parser_structure(self):
        """Test PDF parser structure (without actual PDF)"""
        tools = ToolRegistry()
        
        # Test with invalid URL (should handle gracefully)
        result = tools.parse_pdf("http://invalid-url-for-testing.com/test.pdf")
        self.assertIn("error", result)


class TestContextModes(unittest.TestCase):
    """Test different context modes"""
    
    @patch.dict('os.environ', {'SILICONFLOW_API_KEY': 'test_key'})
    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_key"
    
    def test_context_mode_initialization(self):
        """Test agent initialization with different context modes"""
        for mode in ContextMode:
            agent = ContextAwareAgent(self.api_key, mode)
            self.assertEqual(agent.context_mode, mode)
            self.assertEqual(agent.trajectory.context_mode, mode)
    
    def test_context_building(self):
        """Test context building for different modes"""
        # Full context mode
        agent = ContextAwareAgent(self.api_key, ContextMode.FULL)
        agent.trajectory.reasoning_steps = ["Step 1", "Step 2"]
        agent.trajectory.tool_calls.append(
            MagicMock(tool_name="test", arguments={}, result={"test": "result"})
        )
        
        context = agent._build_context()
        self.assertIn("Previous Reasoning Steps", context)
        self.assertIn("Tool Call History", context)
        
        # No reasoning mode
        agent_no_reasoning = ContextAwareAgent(self.api_key, ContextMode.NO_REASONING)
        agent_no_reasoning.trajectory.reasoning_steps = ["Step 1"]
        context = agent_no_reasoning._build_context()
        self.assertNotIn("Previous Reasoning Steps", context)
        
        # No history mode
        agent_no_history = ContextAwareAgent(self.api_key, ContextMode.NO_HISTORY)
        agent_no_history.trajectory.tool_calls.append(
            MagicMock(tool_name="test", arguments={}, result={"test": "result"})
        )
        context = agent_no_history._build_context()
        self.assertEqual(context, "")


class TestAblationScenarios(unittest.TestCase):
    """Test ablation scenarios"""
    
    def test_tool_execution(self):
        """Test tool execution"""
        agent = ContextAwareAgent("test_key", ContextMode.FULL)
        
        # Test calculator execution
        result = agent._execute_tool("calculate", {"expression": "2 + 2"})
        self.assertEqual(result["result"], 4)
        
        # Test unknown tool
        result = agent._execute_tool("unknown_tool", {})
        self.assertIn("error", result)
    
    def test_trajectory_reset(self):
        """Test trajectory reset"""
        agent = ContextAwareAgent("test_key", ContextMode.FULL)
        
        # Add some data to trajectory
        agent.trajectory.reasoning_steps.append("Test step")
        agent.trajectory.tool_calls.append(
            MagicMock(tool_name="test", arguments={})
        )
        
        # Reset
        agent.reset()
        
        # Check if cleared
        self.assertEqual(len(agent.trajectory.reasoning_steps), 0)
        self.assertEqual(len(agent.trajectory.tool_calls), 0)
        self.assertEqual(agent.trajectory.context_mode, ContextMode.FULL)


def run_integration_test():
    """Run a simple integration test"""
    print("\n" + "="*60)
    print("INTEGRATION TEST")
    print("="*60)
    
    # Check if API key is available
    import os
    api_key = os.getenv("SILICONFLOW_API_KEY")
    
    if not api_key:
        print("⚠️ Skipping integration test (no API key found)")
        print("Set SILICONFLOW_API_KEY to run integration tests")
        return False
    
    print("✅ API key found, running integration test...")
    
    try:
        # Create agent
        agent = ContextAwareAgent(api_key, ContextMode.FULL)
        
        # Simple task that doesn't require external PDFs
        simple_task = "Calculate: What is 15% of $2500? Then convert the result to EUR."
        
        print(f"\nTest task: {simple_task}")
        print("Running...")
        
        # Execute with timeout
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Integration test timed out")
        
        # Set 30 second timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        try:
            result = agent.execute_task(simple_task, max_iterations=3)
            signal.alarm(0)  # Cancel alarm
            
            print(f"\n✅ Integration test completed!")
            print(f"Success: {result.get('success', False)}")
            print(f"Tool calls: {len(result['trajectory'].tool_calls)}")
            
            if result.get('final_answer'):
                print(f"Answer preview: {result['final_answer'][:100]}...")
            
            return True
            
        except TimeoutError:
            print("❌ Integration test timed out")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        return False


def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("CONTEXT-AWARE AGENT TEST SUITE")
    print("="*60)
    
    # Run unit tests
    print("\n📋 Running unit tests...")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestToolRegistry))
    suite.addTests(loader.loadTestsFromTestCase(TestContextModes))
    suite.addTests(loader.loadTestsFromTestCase(TestAblationScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("UNIT TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("✅ All unit tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)
    
    # Run integration test if possible
    print("\n" + "="*60)
    integration_success = run_integration_test()
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL TEST SUMMARY")
    print("="*60)
    
    if result.wasSuccessful():
        print("✅ Unit tests: PASSED")
    else:
        print("❌ Unit tests: FAILED")
    
    if integration_success:
        print("✅ Integration test: PASSED")
    else:
        print("⚠️ Integration test: SKIPPED or FAILED")
    
    print("\n🎉 Testing complete!")
    print("="*60 + "\n")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
