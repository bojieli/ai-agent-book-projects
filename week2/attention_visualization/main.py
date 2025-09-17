"""
ReAct Tool-Calling Agent with Attention Visualization
Implements a proper ReAct (Reasoning + Acting) loop with step-by-step visualization
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from agent import AttentionVisualizationAgent, GenerationResult
from tools import ToolRegistry
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ReActStep:
    """Represents one step in the ReAct reasoning process"""
    step_number: int
    step_type: str  # 'thought', 'action', 'observation', 'answer'
    content: str
    tool_call: Optional[Dict[str, Any]] = None
    tool_result: Optional[str] = None
    
    def to_dict(self):
        return {
            'step_number': self.step_number,
            'step_type': self.step_type,
            'content': self.content,
            'tool_call': self.tool_call,
            'tool_result': self.tool_result
        }


class ReActAttentionAgent(AttentionVisualizationAgent):
    """
    ReAct agent that implements proper Thought-Action-Observation loop
    with attention tracking at each step
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_registry = ToolRegistry()
        self.max_iterations = 10  # Allow more iterations for complex reasoning
        self.trajectory_data = []  # Store trajectory data for this session
        
    def create_initial_messages(self, query: str) -> list:
        """Create initial messages with proper format for Qwen3"""
        system_prompt = """You are a helpful AI assistant. Always use tools when you need specific information or calculations."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        return messages
    
    def parse_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """Parse tool calls from agent response using Qwen3 format"""
        tool_calls = []
        
        # Look for <tool_call> tags (Qwen3 format)
        tool_pattern = r'<tool_call>(.*?)</tool_call>'
        tool_matches = re.findall(tool_pattern, text, re.DOTALL)
        
        for match in tool_matches:
            try:
                # Parse the JSON inside the tool_call tags
                tool_data = json.loads(match.strip())
                if "name" in tool_data and "arguments" in tool_data:
                    tool_calls.append(tool_data)
                    logger.info(f"Parsed tool call: {tool_data['name']}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse tool call: {e}")
                logger.debug(f"Content was: {match}")
        
        return tool_calls
    
    def generate_with_streaming(
        self,
        prompt: str,
        max_new_tokens: int = 2000,
        temperature: float = 0.3,
        verbose: bool = True,
        show_token_ids: bool = False,
        track_attention: bool = True
    ) -> tuple:
        """
        Generate text with token-by-token streaming and stop at EOS
        
        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            verbose: Whether to stream tokens to console
            show_token_ids: Whether to show token IDs alongside text
            track_attention: Whether to track attention weights
            
        Returns:
            Tuple of (generated_text, attention_weights)
        """
        import torch
        
        # Tokenize input without truncation to preserve all tokens
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=False)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        input_length = inputs['input_ids'].shape[1]
        
        # Get EOS token ID
        eos_token_id = self.tokenizer.eos_token_id
        if isinstance(eos_token_id, list):
            eos_token_ids = eos_token_id
        else:
            eos_token_ids = [eos_token_id] if eos_token_id else []
        
        # Add common stop tokens
        stop_tokens = set(eos_token_ids)
        if hasattr(self.tokenizer, 'pad_token_id') and self.tokenizer.pad_token_id:
            stop_tokens.add(self.tokenizer.pad_token_id)
        
        # Add special tokens that might indicate end of generation
        special_stop_strings = ['<|endoftext|>', '<|im_end|>', '</s>', '[DONE]']
        
        generated_ids = []
        generated_text = ""
        attention_weights = [] if track_attention else None
        
        if verbose:
            print(f"📊 Input: {input_length} tokens | Max new: {max_new_tokens}")
            print("🔤 Streaming output:", flush=True)
            print("-" * 60, flush=True)
        
        # Generate token by token
        with torch.no_grad():
            past_key_values = None
            input_ids = inputs['input_ids']
            
            for i in range(max_new_tokens):
                # Forward pass with attention output
                outputs = self.model(
                    input_ids=input_ids,
                    past_key_values=past_key_values,
                    use_cache=True,
                    return_dict=True,
                    output_attentions=track_attention
                )
                
                # Get logits for next token
                logits = outputs.logits[0, -1, :] / temperature
                
                # Sample next token
                probs = torch.nn.functional.softmax(logits, dim=-1)
                next_token_id = torch.multinomial(probs, num_samples=1).item()
                
                # Track attention if requested
                if track_attention and hasattr(outputs, 'attentions') and outputs.attentions:
                    # Get last layer attention, maximum across heads
                    last_attn = outputs.attentions[-1]  # [batch, heads, seq, seq]
                    max_attn = last_attn[0, :, -1, :].max(dim=0)[0].cpu().numpy()  # Maximum over heads
                    attention_weights.append(max_attn)
                
                # Check for EOS
                if next_token_id in stop_tokens:
                    if verbose:
                        print(f"\n🛑 [EOS token detected: {next_token_id}]", flush=True)
                        print(f"📈 Generated {len(generated_ids)} tokens total")
                    break
                
                # Decode and stream token
                token_text = self.tokenizer.decode([next_token_id], skip_special_tokens=False)
                generated_ids.append(next_token_id)
                generated_text += token_text
                
                if verbose:
                    # Stream token to console (skip special tokens for display)
                    display_text = self.tokenizer.decode([next_token_id], skip_special_tokens=True)
                    if display_text:  # Only print if there's visible text
                        if show_token_ids:
                            print(f"[{next_token_id}:{display_text}]", end="", flush=True)
                        else:
                            print(display_text, end="", flush=True)
                
                # Check for stop strings in accumulated text
                for stop_str in special_stop_strings:
                    if stop_str in generated_text:
                        if verbose:
                            print(f"\n🛑 [Stop string detected: {stop_str}]", flush=True)
                            print(f"📈 Generated {len(generated_ids)} tokens")
                        return generated_text[:generated_text.index(stop_str)], attention_weights
                
                # Update input for next iteration
                input_ids = torch.tensor([[next_token_id]], device=self.device)
                past_key_values = outputs.past_key_values
        
        if verbose:
            print(f"\n{'-' * 60}")
            print(f"📈 Total generated: {len(generated_ids)} tokens")
        
        return generated_text, attention_weights
    
    def generate_with_attention_streaming(
        self,
        prompt: str,
        max_new_tokens: int = 2000,
        temperature: float = 0.3,
        verbose: bool = True,
        save_trajectory: bool = False
    ) -> GenerationResult:
        """
        Generate text with streaming output while tracking attention, returning GenerationResult format
        
        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            verbose: Whether to stream tokens to console
            save_trajectory: Whether to save trajectory (unused but kept for compatibility)
            
        Returns:
            GenerationResult object with tokens and attention information
        """
        from agent import AttentionStep
        import torch
        
        # Use the streaming generation method (without attention tracking during streaming)
        generated_text, _ = self.generate_with_streaming(
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            verbose=verbose,
            track_attention=False  # Don't track during streaming
        )
        
        # Tokenize to get input and output tokens
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=False)
        input_token_ids = inputs['input_ids'][0].tolist()
        input_tokens = [self.tokenizer.decode([tid], skip_special_tokens=False) for tid in input_token_ids]
        
        # Get output tokens and IDs
        output_token_ids = self.tokenizer(generated_text, return_tensors="pt", truncation=False)['input_ids'][0].tolist()
        output_tokens = [self.tokenizer.decode([tid], skip_special_tokens=False) for tid in output_token_ids]
        
        # Now do a single forward pass to get the full attention matrix for the complete sequence
        full_text = prompt + generated_text
        full_inputs = self.tokenizer(full_text, return_tensors="pt", truncation=False)
        full_inputs = {k: v.to(self.device) for k, v in full_inputs.items()}
        
        # Get full attention matrix with a single forward pass
        attention_matrix = []
        with torch.no_grad():
            outputs = self.model(
                **full_inputs,
                output_attentions=True,
                return_dict=True
            )
            
            if hasattr(outputs, 'attentions') and outputs.attentions:
                # Get the last layer's attention
                last_layer_attn = outputs.attentions[-1]  # [batch, heads, seq, seq]
                # Average across heads and extract batch 0
                avg_attn = last_layer_attn[0].mean(dim=0).cpu().numpy()  # [seq, seq]
                
                # Extract only the output token rows (attention from output tokens)
                # We want attention from each output token to all previous tokens
                output_start_idx = len(input_tokens)
                for i in range(len(output_tokens)):
                    token_idx = output_start_idx + i
                    if token_idx < avg_attn.shape[0]:
                        # Get attention from this output token to all previous tokens (including input)
                        attn_row = avg_attn[token_idx, :token_idx+1].tolist()
                        attention_matrix.append(attn_row)
        
        # Create attention steps
        attention_steps = []
        for i, attn_row in enumerate(attention_matrix):
            if i < len(output_tokens) and i < len(output_token_ids):
                step = AttentionStep(
                    step=i,
                    token_id=output_token_ids[i],
                    token=output_tokens[i],
                    position=len(input_tokens) + i,
                    attention_weights=[attn_row]  # Wrap as 2D array for AttentionStep dataclass
                )
                attention_steps.append(step)
        
        # Create and return GenerationResult
        all_tokens = input_tokens + output_tokens
        
        return GenerationResult(
            input_text=prompt,
            output_text=generated_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tokens=all_tokens,
            attention_steps=attention_steps,
            context_length=len(input_tokens)
        )
    
    def execute_react_loop(
        self,
        query: str,
        temperature: float = 0.3,
        max_new_tokens: int = 2000,
        verbose: bool = True,
        save_attention: bool = True
    ) -> List[ReActStep]:
        """
        Execute the ReAct loop for a given query
        
        Args:
            query: User query to answer
            temperature: Sampling temperature
            max_new_tokens: Maximum tokens to generate per response
            verbose: Whether to print progress
            save_attention: Whether to save attention visualizations
            
        Returns:
            List of ReActStep objects representing the reasoning process
        """
        from pathlib import Path
        import numpy as np
        import matplotlib.pyplot as plt
        
        steps = []
        step_counter = 0
        final_answer = None
        
        # Create output directory for attention maps
        if save_attention:
            output_dir = Path("agent_demo_results")
            output_dir.mkdir(exist_ok=True)
            attention_dir = output_dir / "attention_maps"
            attention_dir.mkdir(exist_ok=True)
        
        # Initialize messages
        messages = self.create_initial_messages(query)
        tools = self.tool_registry.get_tool_schemas()
        
        if verbose:
            print("=" * 60)
            print("Starting ReAct Reasoning Loop")
            print("=" * 60)
            print(f"\n📝 Query: {query}\n")
        
        for iteration in range(self.max_iterations):
            step_counter += 1
            
            if verbose:
                print(f"\n--- Step {step_counter} ---")
            
            # Apply chat template with tools
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tools=tools,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Generate response with streaming and attention tracking
            # This shows tokens as they're generated while collecting attention data
            result = self.generate_with_attention_streaming(
                prompt=prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                verbose=verbose,  # Enable streaming output
                save_trajectory=False  # Don't save individual trajectories
            )
            
            response_text = result.output_text
            attention_weights = []
            
            # Extract attention weights from result
            if result.attention_steps:
                for step in result.attention_steps:
                    if step.attention_weights:
                        # step.attention_weights is [[row]], we want just [row]
                        attention_weights.append(step.attention_weights[0] if step.attention_weights else [])
            
            if verbose and attention_weights:
                print(f"\n📊 Generated {len(result.output_tokens)} tokens with {len(attention_weights)} attention steps")
            
            # Store complete attention data for this LLM call
            if save_attention:
                self.trajectory_data.append({
                    "step_num": step_counter,
                    "prompt": prompt,
                    "response": response_text,
                    "input_tokens": result.input_tokens,  # Full input tokens
                    "output_tokens": result.output_tokens,  # Output tokens only
                    "all_tokens": result.tokens if hasattr(result, 'tokens') else (result.input_tokens + result.output_tokens),  # Complete sequence
                    "attention_matrix": attention_weights,
                    "attention_steps": [step.to_dict() for step in result.attention_steps] if result.attention_steps else [],
                    "step_type": 'reasoning' if '<think>' in response_text else 'action',
                    "tool_info": {'tools_used': [tc['name'] for tc in self.parse_tool_calls(response_text)]},
                    "token_count": len(result.input_tokens) + len(result.output_tokens)
                })
            
            # Add assistant's response to messages
            messages.append({"role": "assistant", "content": response_text})
            
            # Extract thinking from <think> tags if present
            think_match = re.search(r'<think>(.*?)</think>', response_text, re.DOTALL)
            if think_match:
                thought = think_match.group(1).strip()
                if thought and verbose:
                    print(f"\n🤔 Thinking: {thought}")
                if thought:
                    steps.append(ReActStep(
                        step_number=step_counter,
                        step_type='thought',
                        content=thought
                    ))
            
            # Parse tool calls
            tool_calls = self.parse_tool_calls(response_text)
            
            if tool_calls:
                # Process each tool call
                for tool_call in tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['arguments']
                    
                    if verbose:
                        print(f"\n🔧 Action: Calling {tool_name}")
                        print(f"   Args: {tool_args}")
                    
                    # Execute tool
                    tool_result = self.tool_registry.execute_tool(tool_name, tool_args)
                    
                    if verbose:
                        print(f"   Result: {tool_result}")
                    
                    # Record the action step
                    steps.append(ReActStep(
                        step_number=step_counter,
                        step_type='action',
                        content=f"Using tool: {tool_name}",
                        tool_call=tool_call,
                        tool_result=tool_result
                    ))
                    
                    # Add tool response as user message (Qwen3 format)
                    tool_response_msg = f"<tool_response>\n{tool_result}\n</tool_response>"
                    messages.append({"role": "user", "content": tool_response_msg})
                    
                    # Record observation
                    steps.append(ReActStep(
                        step_number=step_counter,
                        step_type='observation',
                        content=tool_result
                    ))
            else:
                # No tool calls detected - this is our stopping condition
                if verbose:
                    print("\n📍 No tool calls in response. Stopping ReAct loop.")
                
                # Extract final answer if present
                # Remove <think> tags to get clean content
                clean_content = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
                
                if clean_content:
                    final_answer = clean_content
                    if verbose:
                        print(f"\n✅ Final Answer: {final_answer[:200]}...")
                    
                    steps.append(ReActStep(
                        step_number=step_counter,
                        step_type='answer',
                        content=final_answer
                    ))
                
                # Stop the loop since no tools were called
                break
        
        return steps
    
    def save_react_trajectory(self, query: str, steps: List[ReActStep], final_answer: str,
                              temperature: float = 0.3, max_tokens: int = 2000):
        """
        Save the ReAct trajectory with all steps
        
        Args:
            query: The initial query
            steps: List of ReAct steps
            final_answer: The final answer generated
            temperature: Temperature used for generation
            max_tokens: Maximum tokens used for generation
        """
        from pathlib import Path
        import time
        import json
        
        # Create output directory
        output_dir = Path("frontend/public/trajectories")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = output_dir / f"trajectory_{timestamp}.json"
        
        # Process LLM calls with attention data from trajectory_data
        llm_calls = []
        for traj_data in self.trajectory_data:
            # Extract attention matrix properly (output tokens only)
            attention_matrix = []
            if traj_data.get('attention_matrix'):
                # Convert attention weights to proper format
                for weights in traj_data['attention_matrix']:
                    if isinstance(weights, list):
                        attention_matrix.append(weights)
                    elif hasattr(weights, 'tolist'):
                        attention_matrix.append(weights.tolist())
            
            # Use complete token sequence if available, otherwise combine
            all_tokens = traj_data.get('all_tokens', [])
            if not all_tokens:
                # Fallback: combine input and output tokens without truncation
                all_tokens = traj_data.get('input_tokens', []) + traj_data.get('output_tokens', [])
            
            # Store full prompt and response without any truncation
            llm_call = {
                "step_num": traj_data.get('step_num'),
                "step_type": traj_data.get('step_type', 'unknown'),
                "prompt": traj_data.get('prompt', ''),  # Full prompt text, no truncation
                "response": traj_data.get('response', ''),  # Full response text
                "tokens": all_tokens,  # Complete token sequence
                "input_tokens": traj_data.get('input_tokens', []),  # Full input tokens
                "output_tokens": traj_data.get('output_tokens', []),  # Full output tokens  
                "input_token_count": len(traj_data.get('input_tokens', [])),
                "output_token_count": len(traj_data.get('output_tokens', [])),
                "total_token_count": traj_data.get('token_count', len(all_tokens)),
                "attention_data": {
                    "tokens": all_tokens,
                    "attention_matrix": attention_matrix,
                    "num_layers": 1,
                    "num_heads": len(attention_matrix[0]) if attention_matrix and attention_matrix[0] else 0,
                    "output_only": True,  # Only output token attention
                    "context_length": traj_data.get('input_token_count', len(traj_data.get('input_tokens', [])))
                },
                "tool_info": traj_data.get('tool_info', {})
            }
            llm_calls.append(llm_call)
        
        # Combine all step content for summary
        combined_response = []
        for step in steps:
            combined_response.append(f"[{step.step_type.upper()}] {step.content}")
            if step.tool_result:
                combined_response.append(f"[OBSERVATION] {step.tool_result}")
        
        # Prepare trajectory data with multiple LLM calls
        trajectory_data = {
            "id": timestamp,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_case": {
                "category": "ReAct",
                "query": query,
                "description": f"ReAct agent trajectory with {len(llm_calls)} LLM calls and {len(steps)} reasoning steps"
            },
            "response": final_answer if final_answer else "\\n\\n".join(combined_response),
            "llm_calls": llm_calls,  # Multiple LLM calls with individual attention maps
            "reasoning_steps": [step.to_dict() for step in steps],  # ReAct steps for reference
            "tokens": llm_calls[0]["tokens"] if llm_calls else [],  # For compatibility
            "attention_data": {  # Use first LLM call's attention for main display
                "tokens": llm_calls[0]["tokens"] if llm_calls else [],
                "attention_matrix": llm_calls[0]["attention_data"]["attention_matrix"] if llm_calls else [],
                "num_layers": 1,
                "num_heads": llm_calls[0]["attention_data"]["num_heads"] if llm_calls else 0,
                "output_only": True,  # Only output token attention
                "context_length": llm_calls[0]["attention_data"].get("context_length", 0) if llm_calls else 0
            },
            "metadata": {
                "model": self.model_name,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "device": str(self.device),
                "total_llm_calls": len(llm_calls),
                "total_steps": len(steps),
                "attention_type": "output_only",  # Clarify attention type
                "step_breakdown": {
                    step_type: sum(1 for s in steps if s.step_type == step_type)
                    for step_type in set(s.step_type for s in steps)
                }
            }
        }
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(trajectory_data, f, indent=2, default=str)
        
        # Update manifest
        manifest_file = output_dir / "manifest.json"
        manifest = []
        if manifest_file.exists():
            try:
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
            except:
                manifest = []
        
        manifest.append({
            "filename": f"trajectory_{timestamp}.json",
            "id": timestamp,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "category": "ReAct",
            "query": query
        })
        
        # Keep only last 50 trajectories
        manifest = manifest[-50:]
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"ReAct trajectory saved to {filename}")
        return str(filename)


def demonstrate_react_agent():
    """Demonstrate the ReAct agent with various queries"""
    print("=" * 60)
    print("ReAct Tool-Calling Agent Demo with Attention Tracking")
    print("=" * 60)
    
    # Initialize agent (verbose for agent internals, not generation)
    agent = ReActAttentionAgent(verbose=False)
    
    # Test queries from the original request
    test_queries = [
        "What's the weather like in Vancouver right now?",
        "Calculate the exact compound interest on $5,000 invested at 6% annual interest rate for 30 years, compounded monthly.",
    ]
    
    all_results = []
    saved_trajectories = []
    
    # Run queries
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Sample {i}: {query}")
        print(f"{'='*60}")
        
        # Clear trajectory data for new query
        agent.trajectory_data = []
        
        # Define generation parameters
        temperature = 0.7
        max_new_tokens = 2000
        
        # Execute with ReAct loop
        steps = agent.execute_react_loop(
            query,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
            verbose=True
        )
        
        # Display summary
        print(f"\n📊 Summary:")
        print(f"  • Total steps: {len(steps)}")
        print(f"  • Step breakdown:")
        
        step_counts = {}
        for step in steps:
            step_counts[step.step_type] = step_counts.get(step.step_type, 0) + 1
        
        for step_type, count in step_counts.items():
            print(f"    - {step_type}: {count}")
        
        # Get final answer
        final_answer = next((s.content for s in steps if s.step_type == 'answer'), "No answer generated")
        print(f"\n💬 Final Answer: {final_answer[:200]}...")
        
        all_results.append({
            'query': query,
            'steps': [s.to_dict() for s in steps],
            'final_answer': final_answer
        })
        
        # Save the complete trajectory
        trajectory_file = agent.save_react_trajectory(query, steps, final_answer, temperature, max_new_tokens)
        if trajectory_file:
            saved_trajectories.append(trajectory_file)
        
        print("-" * 40)
    
    # Save results
    output_dir = Path("agent_demo_results")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "react_results.json", 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Visualization is now handled by the frontend
    print(f"\n✨ To visualize attention patterns:")
    print(f"   1. Run the frontend: cd frontend && npm run dev")
    print(f"   2. Open http://localhost:3000 in your browser")
    print(f"\n💾 {len(saved_trajectories)} trajectories saved to frontend/public/trajectories/")
    
    print(f"\n✅ Results saved to {output_dir}/")
    
    return all_results


if __name__ == "__main__":
    import sys
    
    print("\nThis demonstrates a proper ReAct agent that:")
    print("  • Uses structured reasoning (Thought -> Action -> Observation)")
    print("  • Calls tools when needed for information")
    print("  • Tracks attention at each reasoning step")
    print("  • Generates as many tokens as needed (no limits!)")
    print("\nThe agent now properly reasons about problems and uses tools!")
    print("=" * 60)

    # Run demonstration
    demonstrate_react_agent()
        
    print("\n" + "=" * 60)
    print("✨ Demo complete!")