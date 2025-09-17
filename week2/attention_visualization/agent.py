"""
Attention Visualization Agent
Integrates Qwen3 0.5B model with attention tracking and visualization
"""

import json
import logging
import torch
import numpy as np
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    LogitsProcessorList,
    LogitsProcessor,
    GenerationConfig
)
import warnings
warnings.filterwarnings("ignore")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AttentionStep:
    """Records attention information for a single generation step"""
    step: int
    token_id: int
    token: str
    position: int
    attention_weights: List[List[float]]  # [num_heads x seq_len] or averaged [seq_len]
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'step': self.step,
            'token_id': self.token_id, 
            'token': self.token,
            'position': self.position,
            'attention_weights': self.attention_weights
        }


@dataclass  
class GenerationResult:
    """Complete result from a generation with attention tracking"""
    input_text: str
    output_text: str
    input_tokens: List[str]
    output_tokens: List[str]
    attention_steps: List[AttentionStep]
    context_length: int
    response: str = ""  # For compatibility
    tokens: List[str] = field(default_factory=list)  # For compatibility
    attention_weights: Dict = field(default_factory=dict)  # For compatibility
    
    def __post_init__(self):
        if not self.tokens:
            self.tokens = self.input_tokens + self.output_tokens
        if not self.response:
            self.response = self.output_text
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'input_text': self.input_text,
            'output_text': self.output_text,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'attention_steps': [step.to_dict() for step in self.attention_steps],
            'context_length': self.context_length,
            'response': self.response,
            'tokens': self.tokens
        }


class AttentionTracker(LogitsProcessor):
    """
    LogitsProcessor that tracks attention weights during generation
    """
    
    def __init__(self, tokenizer, context_length: int, verbose: bool = False):
        self.tokenizer = tokenizer
        self.context_length = context_length
        self.verbose = verbose
        self.attention_cache = {}
        self.generation_step = 0
        self.generated_tokens = []
        self.output_only = True  # Only track attention from output tokens
        
    def reset(self):
        """Reset tracker for new generation"""
        self.attention_cache = {}
        self.generation_step = 0
        self.generated_tokens = []
        
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        """Called during generation to track tokens"""
        self.generation_step += 1
        
        # Track generated token
        if input_ids.shape[1] > self.context_length:
            last_token_id = input_ids[0, -1].item()
            last_token = self.tokenizer.decode([last_token_id])
            current_position = input_ids.shape[1] - 1
            
            self.generated_tokens.append({
                'step': self.generation_step,
                'token_id': last_token_id,
                'token': last_token,
                'position': current_position
            })
            
            if self.verbose:
                print(f"  Step {self.generation_step}: Generated '{last_token}' at position {current_position}")
                
        return scores
    
    def update_attention(self, position: int, attention_weights):
        """Store attention weights for a position (only for output tokens)"""
        # Only store attention for output tokens (positions >= context_length)
        if self.output_only and position < self.context_length:
            return  # Skip input token attention
        self.attention_cache[position] = attention_weights
        
    def get_attention_steps(self) -> List[AttentionStep]:
        """Convert cached data into AttentionStep objects"""
        steps = []
        for token_info in self.generated_tokens:
            position = token_info['position']
            if position in self.attention_cache:
                attention = self.attention_cache[position]
                if isinstance(attention, torch.Tensor):
                    attention = attention.cpu().numpy().tolist()
                elif isinstance(attention, np.ndarray):
                    attention = attention.tolist()
                    
                steps.append(AttentionStep(
                    step=token_info['step'],
                    token_id=token_info['token_id'],
                    token=token_info['token'],
                    position=position,
                    attention_weights=attention
                ))
        return steps


class AttentionVisualizationAgent:
    """
    Agent that generates text using Qwen3 0.6B while tracking attention weights
    """
    
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-0.6B",
        device: Optional[str] = None,
        attention_layer_index: int = -1,
        verbose: bool = True
    ):
        """
        Initialize the agent with Qwen3 model
        
        Args:
            model_name: Hugging Face model name
            device: Device to run on (cuda/mps/cpu)
            attention_layer_index: Which layer's attention to track (-1 for last)
            verbose: Whether to print debug info
        """
        self.model_name = model_name
        self.attention_layer_index = attention_layer_index
        self.verbose = verbose
        
        # Detect device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else \
                         "mps" if torch.backends.mps.is_available() else "cpu"
        else:
            self.device = device
            
        logger.info(f"Initializing {model_name} on {self.device}")
        
        # Load model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
            trust_remote_code=True,
            attn_implementation="eager"  # Enable attention output
        ).to(self.device)
        
        # Determine number of layers
        self.num_layers = self._get_num_layers()
        if self.num_layers:
            logger.info(f"Model has {self.num_layers} layers")
            
        # Initialize attention tracker
        self.tracker = None
        self.conversation_history = []
        
    def _get_num_layers(self) -> Optional[int]:
        """Get the number of transformer layers in the model"""
        if hasattr(self.model, 'config'):
            for attr in ['num_hidden_layers', 'n_layer', 'num_layers']:
                if hasattr(self.model.config, attr):
                    return getattr(self.model.config, attr)
        return None
    
    def _capture_attention_hook(self, module, input, output):
        """Hook to capture attention weights from model layers"""
        if self.tracker is None:
            return
            
        try:
            attention_weights = None
            
            # Try different ways to extract attention
            if hasattr(output, 'attentions') and output.attentions is not None:
                attention_weights = output.attentions
            elif isinstance(output, tuple) and len(output) > 1:
                for item in output:
                    if isinstance(item, torch.Tensor) and len(item.shape) == 4:
                        attention_weights = item
                        break
                        
            if attention_weights is not None:
                # Handle multiple layers
                if isinstance(attention_weights, (list, tuple)):
                    layer_idx = self.attention_layer_index
                    if layer_idx >= 0 and layer_idx < len(attention_weights):
                        attention_weights = attention_weights[layer_idx]
                    else:
                        attention_weights = attention_weights[-1]  # Default to last
                        
                # Extract attention for last token
                if isinstance(attention_weights, torch.Tensor) and attention_weights.dim() >= 3:
                    if attention_weights.dim() == 4:
                        # Average across heads: [batch, heads, seq, seq] -> [seq]
                        avg_attention = attention_weights[0, :, -1, :].mean(dim=0)
                    else:
                        avg_attention = attention_weights[0, -1, :]
                        
                    current_pos = avg_attention.shape[0] - 1
                    
                    # Only track attention for output tokens
                    if current_pos >= self.tracker.context_length:
                        self.tracker.update_attention(current_pos, avg_attention)
                    
        except Exception as e:
            if self.verbose:
                logger.warning(f"Error in attention hook: {e}")
    
    def save_trajectory(self, result: GenerationResult, query: str = None, category: str = "General") -> str:
        """Save a trajectory to frontend/public/ with unique filename"""
        # Create output directory
        output_dir = Path("frontend/public/trajectories")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = output_dir / f"trajectory_{timestamp}.json"
        
        # Extract attention data for visualization (output tokens only)
        attention_matrix = []
        if result.attention_steps:
            for step in result.attention_steps:
                if step.attention_weights:
                    attention_matrix.append(step.attention_weights)
        
        # Prepare data in the format expected by frontend
        trajectory_data = {
            "id": timestamp,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_case": {
                "category": category,
                "query": query or result.input_text,
                "description": f"Agent trajectory from {time.strftime('%Y-%m-%d %H:%M:%S')}"
            },
            "response": result.output_text,
            "tokens": result.tokens,
            "attention_data": {
                "tokens": result.tokens,
                "attention_matrix": attention_matrix,
                "num_layers": 1,  # Simplified for now
                "num_heads": len(attention_matrix[0]) if attention_matrix and attention_matrix[0] else 0,
                "output_only": True,  # Flag to indicate output-only attention
                "context_length": result.context_length  # Where output tokens start
            },
            "metadata": {
                "model": self.model_name,
                "temperature": temperature,
                "max_tokens": max_new_tokens,
                "device": str(self.device),
                "attention_type": "output_only"  # Clarify attention type
            }
        }
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(trajectory_data, f, indent=2, default=str)
        
        # Update manifest file
        manifest_file = output_dir / "manifest.json"
        manifest = []
        if manifest_file.exists():
            try:
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
            except:
                manifest = []
        
        # Add new trajectory to manifest
        manifest.append({
            "filename": f"trajectory_{timestamp}.json",
            "id": timestamp,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "query": query or result.input_text
        })
        
        # Keep only last 50 trajectories in manifest
        manifest = manifest[-50:]
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Trajectory saved to {filename}")
        return str(filename)
    
    def generate_with_attention(
        self,
        prompt: str,
        max_new_tokens: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True,
        save_trajectory: bool = True,
        category: str = "General",
        store_full_tokens: bool = True
    ) -> GenerationResult:
        """
        Generate text while tracking attention weights
        
        Args:
            prompt: Input prompt text
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            do_sample: Whether to use sampling
            store_full_tokens: Whether to store all input tokens (not truncated)
            
        Returns:
            GenerationResult with tokens and attention information
        """
        # Tokenize input without truncation to preserve all tokens
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=False)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        context_length = inputs['input_ids'].shape[1]
        
        # Decode input tokens - store full sequence
        input_token_ids = inputs['input_ids'][0].tolist()
        input_tokens = [self.tokenizer.decode([tid], skip_special_tokens=False) for tid in input_token_ids]
        
        logger.info(f"Input: {len(input_tokens)} tokens")
        
        # Initialize tracker
        self.tracker = AttentionTracker(self.tokenizer, context_length, self.verbose)
        
        # Set up generation config
        generation_config = GenerationConfig(
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=do_sample,
            top_p=top_p,
            repetition_penalty=1.1
        )
        
        # Register attention hooks
        hooks = []
        hook_modules = []
        
        # Find attention modules
        for name, module in self.model.named_modules():
            if any(pattern in name.lower() for pattern in ['attn', 'attention', 'self_attn']):
                if hasattr(module, 'forward'):
                    hook = module.register_forward_hook(self._capture_attention_hook)
                    hooks.append(hook)
                    hook_modules.append(name)
                    
        if self.verbose:
            logger.info(f"Registered {len(hooks)} attention hooks")
            
        try:
            # Generate with attention tracking
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    generation_config=generation_config,
                    logits_processor=LogitsProcessorList([self.tracker]),
                    output_attentions=True,
                    output_scores=True,
                    return_dict_in_generate=True
                )
                
            # Process attention from generate output if available
            if hasattr(outputs, 'attentions') and outputs.attentions is not None:
                self._process_generation_attentions(outputs.attentions, context_length)
                
        finally:
            # Remove hooks
            for hook in hooks:
                hook.remove()
                
        # Decode output
        generated_ids = outputs.sequences[0][context_length:]
        output_text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        # Keep special tokens in token list for accurate representation
        output_tokens = [self.tokenizer.decode([tid], skip_special_tokens=False) for tid in generated_ids.tolist()]
        
        # Get attention steps
        attention_steps = self.tracker.get_attention_steps()
        
        logger.info(f"Generated {len(output_tokens)} tokens with {len(attention_steps)} attention steps")
        
        # Store all tokens (input + output) for complete sequence
        all_token_ids = outputs.sequences[0].tolist()
        all_tokens = [self.tokenizer.decode([tid], skip_special_tokens=False) for tid in all_token_ids]
        
        result = GenerationResult(
            input_text=prompt,
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tokens=all_tokens,  # Complete token sequence
            attention_steps=attention_steps,
            context_length=context_length
        )
        
        # Save trajectory if requested
        if save_trajectory:
            self.save_trajectory(result, query=prompt, category=category)
        
        return result
    
    def _process_generation_attentions(self, attentions, context_length):
        """Process attention weights from generation output"""
        if not attentions or not self.tracker:
            return
            
        try:
            for step_idx, step_attentions in enumerate(attentions):
                if step_attentions is None or len(step_attentions) == 0:
                    continue
                    
                # Select layer
                layer_index = self.attention_layer_index
                if layer_index >= 0 and layer_index < len(step_attentions):
                    selected_attention = step_attentions[layer_index]
                elif layer_index < 0 and abs(layer_index) <= len(step_attentions):
                    selected_attention = step_attentions[layer_index]
                else:
                    selected_attention = step_attentions[-1]
                    
                if isinstance(selected_attention, torch.Tensor):
                    # Get attention for last position
                    current_seq_len = selected_attention.shape[2]
                    last_pos = current_seq_len - 1
                    
                    # Average across heads
                    avg_attention = selected_attention[0, :, last_pos, :].mean(dim=0)
                    
                    # Store in tracker
                    seq_pos = context_length + step_idx
                    self.tracker.update_attention(seq_pos, avg_attention)
                    
        except Exception as e:
            if self.verbose:
                logger.warning(f"Error processing generation attentions: {e}")
    
    def chat(self, message: str, **kwargs) -> GenerationResult:
        """
        Chat interface that maintains conversation history
        
        Args:
            message: User message
            **kwargs: Generation parameters
            
        Returns:
            GenerationResult with attention tracking
        """
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Build full prompt with history
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]
        messages.extend(self.conversation_history)
        
        # Apply chat template
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Generate response
        result = self.generate_with_attention(prompt, **kwargs)
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": result.output_text
        })
        
        return result
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        logger.info("Conversation history reset")


def demonstrate_attention_tracking():
    """Demonstrate the attention tracking functionality"""
    print("=" * 60)
    print("Attention Visualization Demo")
    print("=" * 60)
    
    # Initialize agent
    agent = AttentionVisualizationAgent(verbose=True)
    
    # Test prompts with categories
    test_prompts = [
        ("What is the capital of France?", "Knowledge"),
        ("Calculate 25 * 4 + 10", "Math"),
        ("Write a haiku about spring", "Creative"),
        ("If all cats are animals, and some animals are pets, can we conclude that all cats are pets?", "Reasoning"),
        ("Write a Python function to calculate factorial", "Code")
    ]
    
    results = []
    saved_files = []
    
    for i, (prompt, category) in enumerate(test_prompts, 1):
        print(f"\n--- Test {i}: {category} ---")
        print(f"Prompt: {prompt}")
        
        # Generate with attention tracking and save trajectory
        result = agent.generate_with_attention(
            prompt,
            max_new_tokens=100,
            temperature=0.7,
            save_trajectory=True,
            category=category
        )
        
        print(f"Response: {result.output_text}")
        print(f"Input tokens: {len(result.input_tokens)}")
        print(f"Output tokens: {len(result.output_tokens)}")
        print(f"Attention steps tracked: {len(result.attention_steps)}")
        
        results.append(result)
        time.sleep(1)  # Ensure unique timestamps
        
    return results


if __name__ == "__main__":
    results = demonstrate_attention_tracking()
    
    print("\n" + "=" * 60)
    print("✨ Demo Complete!")
    print("\n🌐 To view the visualizations:")
    print("   1. cd frontend")
    print("   2. npm install (if not already done)")
    print("   3. npm run dev")
    print("   4. Open http://localhost:3000")
    print("\n💾 Trajectories saved to frontend/public/trajectories/")
    print("=" * 60)
