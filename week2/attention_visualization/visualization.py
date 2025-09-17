"""
Attention Visualization Utilities
Creates visual representations of attention patterns
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import seaborn as sns
from typing import List, Dict, Any, Optional, Tuple
import json
from pathlib import Path


def create_attention_heatmap(
    attention_weights: List[List[float]],
    input_tokens: List[str],
    output_tokens: List[str],
    context_boundary: int,
    title: str = "Attention Heatmap",
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (14, 10),
    cmap: str = 'viridis'
) -> plt.Figure:
    """
    Create a heatmap visualization of attention weights
    
    Args:
        attention_weights: 2D list of attention weights [output_len x total_len]
        input_tokens: List of input tokens
        output_tokens: List of generated tokens
        context_boundary: Position where input ends and output begins
        title: Title for the plot
        save_path: Optional path to save the figure
        figsize: Figure size
        cmap: Colormap to use
        
    Returns:
        matplotlib Figure object
    """
    # Handle variable-length attention weights (triangular pattern)
    # Each step i has context_boundary + i + 1 attention weights
    max_len = context_boundary + len(output_tokens)
    attention_matrix = np.zeros((len(attention_weights), max_len))
    
    for i, weights in enumerate(attention_weights):
        # Handle both list and nested list formats
        if weights and isinstance(weights[0], list):
            # Average across heads if multi-head attention
            weights = np.array(weights).mean(axis=0).tolist()
        # Fill in the weights we have
        attention_matrix[i, :len(weights)] = weights[:max_len]
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create the heatmap
    im = ax.imshow(attention_matrix, cmap=cmap, aspect='auto', vmin=0, vmax=1)
    
    # Set ticks and labels
    all_tokens = input_tokens + output_tokens
    
    # X-axis (what is being attended to)
    ax.set_xticks(np.arange(len(all_tokens)))
    ax.set_xticklabels(all_tokens, rotation=45, ha='right', fontsize=8)
    
    # Y-axis (generated tokens)
    ax.set_yticks(np.arange(len(output_tokens)))
    ax.set_yticklabels(output_tokens, fontsize=10)
    
    # Add boundary line between input and output
    ax.axvline(x=context_boundary - 0.5, color='red', linewidth=2, linestyle='--', label='Input/Output Boundary')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Attention Weight', rotation=270, labelpad=20)
    
    # Add grid
    ax.set_xticks(np.arange(len(all_tokens) + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(len(output_tokens) + 1) - 0.5, minor=True)
    ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.5, alpha=0.3)
    
    # Labels and title
    ax.set_xlabel('Token Position (Input → Output)', fontsize=12)
    ax.set_ylabel('Generated Tokens', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add legend
    ax.legend(loc='upper right')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
    return fig


def create_attention_flow_diagram(
    attention_steps: List[Dict],
    input_tokens: List[str],
    context_length: int,
    max_steps: int = 10,
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (16, 10)
) -> plt.Figure:
    """
    Create a flow diagram showing attention evolution over generation steps
    
    Args:
        attention_steps: List of attention step dictionaries
        input_tokens: List of input tokens
        context_length: Length of input context
        max_steps: Maximum number of steps to visualize
        save_path: Optional path to save the figure
        figsize: Figure size
        
    Returns:
        matplotlib Figure object
    """
    # Limit steps if needed
    steps_to_show = min(len(attention_steps), max_steps)
    
    # Create subplots
    fig, axes = plt.subplots(1, steps_to_show, figsize=figsize, sharey=True)
    
    if steps_to_show == 1:
        axes = [axes]
    
    for idx, step in enumerate(attention_steps[:steps_to_show]):
        ax = axes[idx]
        
        # Get attention weights for this step
        attention = np.array(step['attention_weights'])
        
        # Handle both 1D and 2D attention
        if attention.ndim == 2:
            # Average across heads if needed
            attention = attention.mean(axis=0)
        
        # Ensure attention is normalized
        if attention.sum() > 0:
            attention = attention / attention.sum()
        
        # Create bar plot
        positions = np.arange(len(attention))
        colors = ['blue' if i < context_length else 'red' for i in positions]
        
        bars = ax.bar(positions, attention, color=colors, alpha=0.7)
        
        # Highlight top attention positions
        top_k = min(3, len(attention))
        top_indices = np.argsort(attention)[-top_k:]
        for i in top_indices:
            bars[i].set_alpha(1.0)
            bars[i].set_edgecolor('black')
            bars[i].set_linewidth(2)
        
        # Labels
        ax.set_title(f"Step {step['step']}\nToken: '{step['token']}'", fontsize=10)
        ax.set_xlabel('Position', fontsize=8)
        if idx == 0:
            ax.set_ylabel('Attention Weight', fontsize=10)
        
        # Add context boundary line
        ax.axvline(x=context_length - 0.5, color='green', linestyle='--', alpha=0.5)
        
        # Limit y-axis for better visibility
        ax.set_ylim(0, min(1.0, attention.max() * 1.2))
        
    # Overall title
    fig.suptitle('Attention Flow During Generation', fontsize=14, fontweight='bold')
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='blue', alpha=0.7, label='Input Context'),
        Patch(facecolor='red', alpha=0.7, label='Generated'),
        Patch(facecolor='green', alpha=0.5, label='Context Boundary')
    ]
    fig.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
    return fig


def create_token_attention_summary(
    result: Dict,
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (14, 8)
) -> plt.Figure:
    """
    Create a summary visualization showing tokens and their attention patterns
    
    Args:
        result: Generation result dictionary
        save_path: Optional path to save the figure
        figsize: Figure size
        
    Returns:
        matplotlib Figure object
    """
    fig = plt.figure(figsize=figsize)
    
    # Create grid for subplots
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 2, 2], width_ratios=[1, 1])
    
    # 1. Token sequences display
    ax_tokens = fig.add_subplot(gs[0, :])
    ax_tokens.axis('off')
    
    # Display input tokens
    input_text = "Input: " + "".join(result['input_tokens'][:50])  # Limit display
    ax_tokens.text(0.05, 0.7, input_text, fontsize=10, color='blue', 
                   wrap=True, transform=ax_tokens.transAxes)
    
    # Display output tokens
    output_text = "Output: " + "".join(result['output_tokens'][:50])
    ax_tokens.text(0.05, 0.3, output_text, fontsize=10, color='red',
                   wrap=True, transform=ax_tokens.transAxes)
    
    # 2. Attention statistics
    ax_stats = fig.add_subplot(gs[1, 0])
    
    if result['attention_steps']:
        # Calculate statistics
        avg_attentions = []
        max_attentions = []
        
        for step in result['attention_steps']:
            weights = np.array(step['attention_weights'])
            if weights.ndim == 2:
                weights = weights.mean(axis=0)
            avg_attentions.append(weights.mean())
            max_attentions.append(weights.max())
        
        steps = np.arange(len(avg_attentions))
        
        ax_stats.plot(steps, avg_attentions, 'b-', label='Average', linewidth=2)
        ax_stats.plot(steps, max_attentions, 'r-', label='Maximum', linewidth=2)
        ax_stats.fill_between(steps, avg_attentions, alpha=0.3)
        
        ax_stats.set_xlabel('Generation Step')
        ax_stats.set_ylabel('Attention Weight')
        ax_stats.set_title('Attention Statistics Over Time')
        ax_stats.legend()
        ax_stats.grid(True, alpha=0.3)
    
    # 3. Attention distribution histogram
    ax_hist = fig.add_subplot(gs[1, 1])
    
    if result['attention_steps']:
        all_weights = []
        for step in result['attention_steps']:
            weights = np.array(step['attention_weights'])
            if weights.ndim == 2:
                weights = weights.mean(axis=0)
            all_weights.extend(weights.tolist())
        
        ax_hist.hist(all_weights, bins=50, alpha=0.7, color='green', edgecolor='black')
        ax_hist.set_xlabel('Attention Weight')
        ax_hist.set_ylabel('Frequency')
        ax_hist.set_title('Attention Weight Distribution')
        ax_hist.axvline(np.mean(all_weights), color='red', linestyle='--', 
                       label=f'Mean: {np.mean(all_weights):.3f}')
        ax_hist.legend()
    
    # 4. Top attended positions
    ax_top = fig.add_subplot(gs[2, :])
    
    if result['attention_steps']:
        # Aggregate attention across all steps
        context_len = result['context_length']
        total_len = context_len + len(result['output_tokens'])
        aggregated_attention = np.zeros(total_len)
        
        for step in result['attention_steps']:
            weights = np.array(step['attention_weights'])
            if weights.ndim == 2:
                weights = weights.mean(axis=0)
            aggregated_attention[:len(weights)] += weights
        
        # Normalize
        aggregated_attention /= len(result['attention_steps'])
        
        # Create bar plot
        positions = np.arange(len(aggregated_attention))
        colors = ['blue' if i < context_len else 'red' for i in positions]
        
        ax_top.bar(positions, aggregated_attention, color=colors, alpha=0.7)
        ax_top.axvline(x=context_len - 0.5, color='green', linestyle='--', 
                      label='Context Boundary')
        
        # Highlight top positions
        top_k = min(5, len(aggregated_attention))
        top_indices = np.argsort(aggregated_attention)[-top_k:]
        for idx in top_indices:
            ax_top.annotate(f'{idx}', xy=(idx, aggregated_attention[idx]),
                           xytext=(idx, aggregated_attention[idx] + 0.01),
                           ha='center', fontsize=8)
        
        ax_top.set_xlabel('Token Position')
        ax_top.set_ylabel('Average Attention')
        ax_top.set_title('Aggregated Attention Across All Generation Steps')
        ax_top.legend()
    
    plt.suptitle('Attention Analysis Summary', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
    return fig


def visualize_results(
    results_path: str,
    output_dir: str = "visualizations",
    formats: List[str] = ['heatmap', 'flow', 'summary']
):
    """
    Generate visualizations from saved results
    
    Args:
        results_path: Path to JSON results file
        output_dir: Directory to save visualizations
        formats: Which visualization formats to generate
    """
    # Load results
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Process each result
    for idx, result in enumerate(results):
        print(f"Generating visualizations for result {idx + 1}...")
        
        # Extract data
        input_tokens = result['input_tokens']
        output_tokens = result['output_tokens']
        attention_steps = result['attention_steps']
        context_length = result['context_length']
        
        # Create attention matrix for heatmap
        if 'heatmap' in formats and attention_steps:
            attention_matrix = []
            for step in attention_steps:
                weights = step['attention_weights']
                if isinstance(weights[0], list):  # 2D
                    weights = np.array(weights).mean(axis=0).tolist()
                attention_matrix.append(weights)
            
            fig = create_attention_heatmap(
                attention_matrix,
                input_tokens,
                output_tokens,
                context_length,
                title=f"Attention Heatmap - Example {idx + 1}",
                save_path=output_path / f"heatmap_{idx + 1}.png"
            )
            plt.close(fig)
        
        # Create flow diagram
        if 'flow' in formats and attention_steps:
            fig = create_attention_flow_diagram(
                attention_steps,
                input_tokens,
                context_length,
                save_path=output_path / f"flow_{idx + 1}.png"
            )
            plt.close(fig)
        
        # Create summary
        if 'summary' in formats:
            fig = create_token_attention_summary(
                result,
                save_path=output_path / f"summary_{idx + 1}.png"
            )
            plt.close(fig)
    
    print(f"Visualizations saved to {output_path}")


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        results_file = sys.argv[1]
    else:
        results_file = "attention_results.json"
    
    if Path(results_file).exists():
        visualize_results(results_file)
    else:
        print(f"Results file {results_file} not found. Run agent.py first.")
