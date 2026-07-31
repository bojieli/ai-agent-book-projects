#!/usr/bin/env python3
"""
Test script for DeepSeek model integration.
Tests deepseek-v4-flash (default) with conversation and tool calling.
"""

import os
import sys

from _bootstrap import add_project_root

add_project_root()

from dotenv import load_dotenv
from agent import ContextAwareAgent, ContextMode
from config import Config

# Load environment variables
load_dotenv()


def test_basic_conversation():
    """Test basic conversation capabilities"""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Conversation")
    print("=" * 60)

    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("❌ ERROR: DEEPSEEK_API_KEY not set in environment")
            print("Please set it in your .env file or as environment variable")
            return False

        agent = ContextAwareAgent(
            api_key=api_key,
            provider="deepseek",
            context_mode=ContextMode.FULL,
            verbose=False,
        )

        query = "What is 25 * 4 + 10? Reply with FINAL ANSWER: and the number."
        print(f"\n📝 Query: {query}")

        response = agent.process(query)
        print(f"\n🤖 Response: {response}")

        if "110" in response:
            print("\n✅ Basic conversation test passed!")
            return True
        else:
            print("\n❌ Test failed - incorrect answer")
            return False

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        return False


def test_tool_usage():
    """Test tool calling capabilities"""
    print("\n" + "=" * 60)
    print("TEST 2: Tool Usage (Calculator)")
    print("=" * 60)

    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("❌ ERROR: DEEPSEEK_API_KEY not set")
            return False

        agent = ContextAwareAgent(
            api_key=api_key,
            provider="deepseek",
            context_mode=ContextMode.FULL,
            verbose=False,
        )

        query = (
            "Calculate: (123.45 * 67.89) / 12.34 + sqrt(144) - 2^8. "
            "Use the calculate tool. End with FINAL ANSWER:"
        )
        print(f"\n📝 Query: {query}")

        response = agent.process(query)
        print(f"\n🤖 Response: {response}")

        if agent.trajectory.tool_calls:
            print(f"\n🔧 Tools used: {len(agent.trajectory.tool_calls)}")
            for call in agent.trajectory.tool_calls:
                print(f"  - {call.tool_name}: {call.arguments}")
            print("\n✅ Tool usage test passed!")
            return True
        else:
            print("\n⚠️  No tools were used")
            return False

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        return False


def test_currency_conversion():
    """Test currency conversion tool"""
    print("\n" + "=" * 60)
    print("TEST 3: Currency Conversion")
    print("=" * 60)

    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("❌ ERROR: DEEPSEEK_API_KEY not set")
            return False

        agent = ContextAwareAgent(
            api_key=api_key,
            provider="deepseek",
            context_mode=ContextMode.FULL,
            verbose=False,
        )

        query = "Convert 100 USD to EUR and JPY. Use convert_currency. FINAL ANSWER: the amounts."
        print(f"\n📝 Query: {query}")

        response = agent.process(query)
        print(f"\n🤖 Response: {response}")

        tool_names = [call.tool_name for call in agent.trajectory.tool_calls]
        if "convert_currency" in tool_names:
            print("\n🔧 Currency converter was used")
            print("\n✅ Currency conversion test passed!")
            return True
        else:
            print("\n⚠️  Currency converter was not used")
            return False

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        return False


def test_model_info():
    """Test and display model information"""
    print("\n" + "=" * 60)
    print("TEST 4: Model Information")
    print("=" * 60)

    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("❌ ERROR: DEEPSEEK_API_KEY not set")
            return False

        agent = ContextAwareAgent(
            api_key=api_key,
            provider="deepseek",
            context_mode=ContextMode.FULL,
            verbose=False,
        )

        expected = Config.get_default_model("deepseek")
        print("\n📊 Model Configuration:")
        print(f"  Provider: {agent.provider}")
        print(f"  Model: {agent.model}")
        print(f"  Expected default: {expected}")
        print(f"  Base URL: {agent.client.base_url}")
        print(f"  Context Mode: {agent.context_mode.value}")

        if agent.provider != "deepseek" or agent.model != expected:
            print("\n❌ Model config mismatch")
            return False

        print("\n✅ Model info test completed!")
        return True

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("DEEPSEEK MODEL INTEGRATION TEST SUITE")
    print("=" * 60)
    print("\nModel: deepseek-v4-flash (default)")
    print("Provider: DeepSeek")
    print("API: https://api.deepseek.com")

    if not os.getenv("DEEPSEEK_API_KEY"):
        print("\n❌ ERROR: DEEPSEEK_API_KEY not found in environment")
        print("\nPlease set up your .env file with:")
        print("  DEEPSEEK_API_KEY=your_api_key_here")
        print("\nYou can get an API key from: https://platform.deepseek.com/api_keys")
        sys.exit(1)

    results = []
    results.append(("Model Information", test_model_info()))
    results.append(("Basic Conversation", test_basic_conversation()))
    results.append(("Tool Usage", test_tool_usage()))
    results.append(("Currency Conversion", test_currency_conversion()))

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! DeepSeek integration is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
