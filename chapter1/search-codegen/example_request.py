#!/usr/bin/env python3
"""
Example showing the exact OpenRouter GPT-5 request format matching the Go implementation
"""

import json
import requests
import os
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def make_gpt5_openrouter_request(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    reasoning_effort: str = "low"
) -> Dict[str, Any]:
    """
    Make a GPT-5 request using the exact format from the Go implementation
    
    This matches the GPT5OpenRouterRequest structure from the Go code
    """
    
    # Build messages (matching Go implementation)
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user", 
            "content": user_prompt
        }
    ]
    
    # Build web search tool configuration (matching Go GPT5OpenRouterWebSearchTool)
    web_search_tool = {
        "type": "web_search",
        "search_context_size": "medium",
        "user_location": {
            "type": "approximate",
            "country": "US"
        }
    }
    
    # Build request with OpenRouter-specific parameters (matching Go GPT5OpenRouterRequest)
    request_body = {
        "model": "openai/gpt-5.6-sol",  # Default from Go code
        "messages": messages,
        "tools": [web_search_tool],
        "tool_choice": "auto",
        "parallel_tool_calls": True,
        "reasoning": {
            "effort": reasoning_effort,
            "generate_summary": False
        },
        "background": False,
        "stream": False  # Can be set to True for streaming
    }
    
    print("="*60)
    print("GPT-5 OpenRouter Request (matching Go implementation):")
    print("="*60)
    print(json.dumps(request_body, indent=2))
    print("="*60)
    
    # Set headers (matching Go implementation)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Make the request
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=request_body,
            timeout=600  # Match Go timeout
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            # Log usage (matching Go logging)
            if "usage" in response_data:
                usage = response_data["usage"]
                input_tokens = usage.get(
                    "prompt_tokens", usage.get("input_tokens", 0)
                )
                output_tokens = usage.get(
                    "completion_tokens", usage.get("output_tokens", 0)
                )
                input_details = usage.get(
                    "prompt_tokens_details", usage.get("input_tokens_details")
                )
                output_details = usage.get(
                    "completion_tokens_details", usage.get("output_tokens_details")
                )
                print("\nGPT-5 OpenRouter Usage:")
                print(f"  Input: {input_tokens} tokens", end="")
                if isinstance(input_details, dict):
                    print(f" (cached: {input_details.get('cached_tokens', 0)})")
                else:
                    print()
                    
                print(f"  Output: {output_tokens} tokens", end="")
                if isinstance(output_details, dict):
                    print(f" (reasoning: {output_details.get('reasoning_tokens', 0)})")
                else:
                    print()
                    
                print(f"  Total: {usage.get('total_tokens', 0)}")
            
            return response_data
        else:
            print(f"\nError: {response.text}")
            return {"error": response.text, "status_code": response.status_code}
            
    except Exception as e:
        print(f"\nException: {str(e)}")
        return {"error": str(e)}


def demonstrate_streaming_response():
    """
    Demonstrate how streaming would work (matching Go handleStreamingResponse)
    """
    print("\n" + "="*60)
    print("Streaming Response Handler (pseudo-code matching Go):")
    print("="*60)
    
    streaming_code = '''
def handle_streaming_response(response):
    """
    Handle streaming responses from GPT-5 OpenRouter API
    Matches Go handleStreamingResponse function
    """
    content_builder = []
    reasoning_builder = []
    reasoning_token_count = 0
    
    for line in response.iter_lines():
        if not line:
            continue
            
        line_str = line.decode('utf-8')
        
        if not line_str.startswith("data: "):
            continue
            
        data = line_str[6:]  # Remove "data: " prefix
        
        if data == "[DONE]":
            break
            
        try:
            chunk = json.loads(data)
            
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {})
                
                # Check for reasoning content
                if "reasoning_content" in delta:
                    reasoning = delta["reasoning_content"]
                    reasoning_builder.append(reasoning)
                    reasoning_token_count += 1
                    print(f"🧠 [GPT-5 THINKING] {reasoning}")
                
                # Check for regular content
                if "content" in delta:
                    content = delta["content"]
                    content_builder.append(content)
                    
        except json.JSONDecodeError:
            continue
    
    final_content = "".join(content_builder)
    return final_content
'''
    print(streaming_code)


def main():
    """
    Main demonstration
    """
    print("\n" + "="*60)
    print("   GPT-5 OpenRouter Request Format Demo")
    print("   Exact match with Go implementation")
    print("="*60)
    
    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        print("\n❌ Error: OPENROUTER_API_KEY not found in environment")
        print("Please set: export OPENROUTER_API_KEY=your-openrouter-api-key")
        return
    
    # Example prompts
    system_prompt = "You are a helpful AI assistant with web search capabilities."
    user_prompt = "What are the latest developments in artificial intelligence?"
    
    print("\n1. Making request with LOW reasoning effort:")
    print("-"*60)
    result_low = make_gpt5_openrouter_request(
        api_key=api_key,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        reasoning_effort="low"
    )
    
    if "choices" in result_low:
        content = result_low["choices"][0]["message"]["content"]
        print(f"\nResponse preview: {content[:200]}...")
    
    print("\n2. Making request with HIGH reasoning effort:")
    print("-"*60)
    result_high = make_gpt5_openrouter_request(
        api_key=api_key,
        system_prompt=system_prompt,
        user_prompt="Explain the implications of quantum computing on cryptography",
        reasoning_effort="high"
    )
    
    if "choices" in result_high:
        content = result_high["choices"][0]["message"]["content"]
        print(f"\nResponse preview: {content[:200]}...")
    
    # Show streaming handler
    demonstrate_streaming_response()
    
    print("\n" + "="*60)
    print("Demo complete! This shows the exact request format from Go.")
    print("="*60)


if __name__ == "__main__":
    main()
