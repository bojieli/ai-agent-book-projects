"""
Custom Agent for Ablation Study
Extends ToolCallingAgent to support tone modifications
"""

import json
import os
from litellm import completion
from typing import List, Optional, Dict, Any

from tau_bench.agents.base import Agent
from tau_bench.agents.tool_calling_agent import message_to_action
from tau_bench.envs.base import Env
from tau_bench.types import SolveResult, Action, RESPOND_ACTION_NAME


class AblationAgent(Agent):
    """
    Agent that supports tone modifications for ablation studies
    """
    
    def __init__(
        self,
        tools_info: List[Dict[str, Any]],
        wiki: str,
        model: str,
        provider: str,
        temperature: float = 0.0,
        verbose: bool = True
    ):
        """
        Initialize the ablation agent
        
        Args:
            tools_info: Information about available tools
            wiki: Wiki/system prompt text (may have tone modifications already applied)
            model: Model name
            provider: Model provider
            temperature: Sampling temperature
            verbose: Whether to show detailed output (default: True)
        """
        self.tools_info = tools_info
        self.wiki = wiki
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.verbose = verbose
    
    def solve(
        self, env: Env, task_index: Optional[int] = None, max_num_steps: int = 30
    ) -> SolveResult:
        """
        Solve a task with potential tone modifications
        
        Args:
            env: The environment
            task_index: Optional task index
            max_num_steps: Maximum number of steps
        
        Returns:
            SolveResult with the outcome
        """
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"🎯 STARTING TASK {task_index if task_index is not None else 'N/A'}")
            print(f"{'='*80}")
            print(f"\n📜 SYSTEM PROMPT (Wiki) - {len(self.wiki)} characters:")
            print("─"*40)
            # Show first 500 chars of wiki to see tone modifications
            if len(self.wiki) > 500:
                print(self.wiki[:500])
                print(f"... [{len(self.wiki) - 500} more characters]")
            else:
                print(self.wiki)
            print("─"*40)
        
        total_cost = 0.0
        env_reset_res = env.reset(task_index=task_index)
        obs = env_reset_res.observation
        info = env_reset_res.info.model_dump()
        reward = 0.0
        
        if self.verbose:
            print(f"\n📝 Initial User Message:")
            print(f"{'─'*40}")
            print(obs)
            print(f"{'─'*40}")
        
        # Initialize messages
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.wiki},
            {"role": "user", "content": obs},
        ]
        
        for step in range(max_num_steps):
            if self.verbose:
                print(f"\n{'━'*80}")
                print(f"📍 STEP {step + 1}/{max_num_steps}")
                print(f"{'━'*80}")
            
            # Debug: Print request details
            if self.verbose:  # Show full API request details when verbose
                print(f"\n{'='*60}")
                print(f"🚀 API CALL #{step + 1} to {self.provider} / {self.model}")
                print(f"{'='*60}")
                print(f"📤 SENDING {len(messages)} messages:")
                print("\n" + "─"*50)
                for i, msg in enumerate(messages):  # Show ALL messages
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    print(f"\n📨 Message [{i+1}] - Role: {role.upper()}")
                    print("─"*50)
                    if content:
                        print(content)
                    if 'tool_calls' in msg and msg['tool_calls']:
                        print(f"\n🔧 Tool Calls:")
                        for tc in msg['tool_calls']:
                            if isinstance(tc, dict):
                                print(f"  - Function: {tc.get('function', {}).get('name', 'unknown')}")
                                print(f"    Args: {tc.get('function', {}).get('arguments', 'none')}")
                    if 'tool_call_id' in msg:
                        print(f"\n🔧 Tool Response ID: {msg['tool_call_id']}")
                    print("─"*50)
                print("\n" + "="*60)
                print(f"🔧 Temperature: {self.temperature}")
                print(f"🛠️  Tools: {len(self.tools_info) if self.tools_info else 0} tools available")
                if self.tools_info:
                    print("\n📋 COMPLETE TOOL DEFINITIONS (JSON):")
                    print("─"*50)
                    import json
                    for i, tool in enumerate(self.tools_info, 1):
                        print(f"\n[Tool {i}] {tool.get('function', {}).get('name', 'unknown')}:")
                        print(json.dumps(tool, indent=2))
                    print("─"*50)
                print("="*60)
            
            # Get completion from model
            try:
                # Prepare completion kwargs
                completion_kwargs = {
                    "messages": messages,
                    "model": self.model,
                    "custom_llm_provider": self.provider,
                    "tools": self.tools_info,
                    "temperature": self.temperature,
                }
                
                # Add reasoning_effort for gpt-5 to minimize thinking tokens
                if "gpt-5" in self.model:
                    completion_kwargs["extra_body"] = {"reasoning_effort": "low"}
                    if self.verbose:
                        print("💭 Using reasoning_effort='low' to minimize thinking tokens")
                
                res = completion(**completion_kwargs)
                
                # Debug: Print response
                if self.verbose:  # Show full API response details when verbose
                    print(f"\n📥 RESPONSE received:")
                    print("─"*50)
                    if res.choices[0].message.content:
                        print("📝 Response Content:")
                        print("─"*50)
                        print(res.choices[0].message.content)  # Show FULL content
                        print("─"*50)
                    if hasattr(res.choices[0].message, 'tool_calls') and res.choices[0].message.tool_calls:
                        print(f"\n🔧 Tool calls: {len(res.choices[0].message.tool_calls)} tool(s) called")
                        for idx, tc in enumerate(res.choices[0].message.tool_calls):  # Show ALL tool calls
                            print(f"\n  Tool Call [{idx+1}]:")
                            print(f"    - Function: {tc.function.name}")
                            print(f"    - Arguments (FULL):")
                            print(f"      {tc.function.arguments}")  # Show FULL arguments
                    print(f"{'='*60}\n")
            except Exception as e:
                print(f"\n❌ ERROR calling API:")
                print(f"  Provider: {self.provider}")
                print(f"  Model: {self.model}")
                print(f"  Error: {str(e)}")
                print(f"  Error type: {type(e).__name__}")
                import traceback
                print(f"  Traceback:\n{traceback.format_exc()}")
                raise
            
            next_message = res.choices[0].message.model_dump()
            cost = res._hidden_params.get("response_cost", 0)
            if cost is not None:
                total_cost += cost
            
            # Show assistant response if verbose
            if self.verbose:
                print(f"\n🤖 Assistant Response:")
                print(f"{'─'*40}")
                if next_message.get("content"):
                    print(f"💬 Message: {next_message['content']}")
                if next_message.get("tool_calls"):
                    print(f"\n🔧 Tool Calls ({len(next_message['tool_calls'])} tool(s)):")
                    for i, tc in enumerate(next_message["tool_calls"], 1):
                        func_name = tc.get('function', {}).get('name', 'unknown')
                        func_args = tc.get('function', {}).get('arguments', '')
                        print(f"  [{i}] {func_name}")
                        try:
                            import json
                            args_dict = json.loads(func_args) if isinstance(func_args, str) else func_args
                            for key, value in args_dict.items():
                                value_str = str(value)
                                print(f"      • {key}: {value_str}")
                        except:
                            print(f"      Args: {func_args}")
                print(f"{'─'*40}")
            
            
            # Convert message to action
            action = message_to_action(next_message)
            
            # Step in environment
            env_response = env.step(action)
            reward = env_response.reward
            info = {**info, **env_response.info.model_dump()}
            
            # Show environment response if verbose
            if self.verbose:
                print(f"\n🌍 Environment Response:")
                print(f"{'─'*40}")
                print(f"  Action: {action.name}")
                if env_response.observation:
                    obs_str = env_response.observation
                    if action.name != RESPOND_ACTION_NAME:
                        print(f"  Tool Output: {obs_str}")
                    else:
                        print(f"  User Reply: {obs_str}")
                print(f"  Reward: {reward}")
                print(f"  Done: {env_response.done}")
                print(f"{'─'*40}")
            
            # Update messages based on action type
            if action.name != RESPOND_ACTION_NAME:
                # Tool call - limit to first tool call
                next_message["tool_calls"] = next_message["tool_calls"][:1]
                messages.extend(
                    [
                        next_message,
                        {
                            "role": "tool",
                            "tool_call_id": next_message["tool_calls"][0]["id"],
                            "name": next_message["tool_calls"][0]["function"]["name"],
                            "content": env_response.observation,
                        },
                    ]
                )
            else:
                # Response to user
                messages.extend(
                    [
                        next_message,
                        {"role": "user", "content": env_response.observation},
                    ]
                )
            
            # Check if done
            if env_response.done:
                if self.verbose:
                    if reward == 1:
                        print(f"\n✅ Task completed successfully! (Reward = {reward})")
                    else:
                        print(f"\n🏁 Task ended (Reward = {reward})")
                break
        
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"📊 TASK SUMMARY")
            print(f"{'='*80}")
            print(f"  Final Reward: {reward}")
            print(f"  Total Steps: {step + 1}")
            print(f"  Total Cost: ${total_cost:.4f}")
            print(f"  Messages Exchanged: {len(messages)}")
            print(f"{'='*80}\n")
        
        return SolveResult(
            reward=reward,
            info=info,
            messages=messages,
            total_cost=total_cost,
        )
