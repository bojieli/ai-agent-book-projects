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


def _configure_cjk_font():
    """
    Best-effort: pick a CJK-capable font so Chinese token labels (e.g. the
    '北京 的 天气 怎么样' example from Chapter 2) render as glyphs instead of
    tofu boxes. Silently no-ops if none is installed.
    """
    from matplotlib import font_manager
    candidates = [
        "Arial Unicode MS", "PingFang SC", "Hiragino Sans GB", "Heiti SC",
        "Songti SC", "STHeiti", "Noto Sans CJK SC", "Noto Sans CJK JP",
        "Microsoft YaHei", "WenQuanYi Zen Hei", "SimHei",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name] + list(
                plt.rcParams.get("font.sans-serif", [])
            )
            plt.rcParams["axes.unicode_minus"] = False
            return name
    return None


_configure_cjk_font()


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


def clean_token_labels(tokens: List[str], max_len: int = 14) -> List[str]:
    """
    Make raw tokenizer tokens readable as axis labels.

    Replaces whitespace with visible glyphs and truncates very long
    special tokens so the heatmap axes stay legible.
    """
    cleaned = []
    for tok in tokens:
        label = tok.replace("\n", "\\n").replace("\t", "\\t")
        # Qwen byte-level space marker and plain spaces -> visible middle dot
        label = label.replace("Ġ", " ").replace("▁", " ")
        if label.strip() == "":
            label = "␣"
        if len(label) > max_len:
            label = label[:max_len - 1] + "…"
        cleaned.append(label)
    return cleaned


def attention_sink_stats(attention_matrix: np.ndarray, sink_index: int = 0) -> Dict[str, float]:
    """
    Compute how much attention lands on a single "sink" column.

    Averages, over every query row that can see the sink column, the
    attention weight assigned to ``sink_index``. This quantifies the
    "attention sink" phenomenon described in Chapter 2 without inventing
    any numbers - it is measured directly from the model's own weights.

    Returns a dict with the mean and max sink share (0..1).
    """
    matrix = np.asarray(attention_matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0:
        return {"mean_sink_share": 0.0, "max_sink_share": 0.0}

    shares = []
    for row_idx in range(matrix.shape[0]):
        # A causal row only attends to positions <= row_idx.
        if row_idx < sink_index:
            continue
        row = matrix[row_idx, : row_idx + 1]
        total = row.sum()
        if total > 0:
            shares.append(float(matrix[row_idx, sink_index] / total))

    if not shares:
        return {"mean_sink_share": 0.0, "max_sink_share": 0.0}
    return {
        "mean_sink_share": float(np.mean(shares)),
        "max_sink_share": float(np.max(shares)),
    }


def create_layer_attention_heatmap(
    attention_matrix: np.ndarray,
    tokens: List[str],
    title: str = "Attention Heatmap",
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 10),
    cmap: str = "viridis",
    context_boundary: Optional[int] = None,
    annotate_sink: bool = True,
) -> plt.Figure:
    """
    Plot a full [seq x seq] self-attention matrix for one layer/head.

    Rows are Query positions (the token doing the attending) and columns
    are Key positions (the token being attended to). Because generation is
    causal, the matrix is lower-triangular - each token only sees itself
    and the tokens before it, producing the triangular pattern discussed
    in Chapter 2.

    Args:
        attention_matrix: 2D array [seq, seq]. Upper triangle is masked out.
        tokens: Token strings for both axes (length seq).
        title: Plot title.
        save_path: Optional path to save the PNG.
        figsize: Figure size.
        cmap: Matplotlib colormap.
        context_boundary: If given, draws a line where the prompt ends and
            generated tokens begin.
        annotate_sink: If True, annotate the measured attention-sink share.

    Returns:
        matplotlib Figure object.
    """
    matrix = np.asarray(attention_matrix, dtype=float)
    seq_len = matrix.shape[0]

    # Mask the (structurally zero) upper triangle so it renders blank
    # instead of dark, making the causal triangle obvious.
    masked = np.ma.array(matrix, mask=np.triu(np.ones_like(matrix, dtype=bool), k=1))

    fig, ax = plt.subplots(figsize=figsize)
    cmap_obj = plt.get_cmap(cmap).copy()
    cmap_obj.set_bad(color="#f0f0f0")
    im = ax.imshow(masked, cmap=cmap_obj, aspect="auto")

    labels = clean_token_labels(tokens)
    # Avoid an unreadable wall of labels for long sequences.
    if seq_len <= 80:
        ticks = np.arange(seq_len)
    else:
        step = int(np.ceil(seq_len / 80))
        ticks = np.arange(0, seq_len, step)
    tick_labels = [labels[i] for i in ticks]

    ax.set_xticks(ticks)
    ax.set_xticklabels(tick_labels, rotation=90, fontsize=6)
    ax.set_yticks(ticks)
    ax.set_yticklabels(tick_labels, fontsize=6)

    if context_boundary is not None and 0 < context_boundary < seq_len:
        ax.axvline(x=context_boundary - 0.5, color="red", linewidth=1.2,
                   linestyle="--", label="Prompt / Generated boundary")
        ax.axhline(y=context_boundary - 0.5, color="red", linewidth=1.2,
                   linestyle="--")
        ax.legend(loc="lower left", fontsize=8)

    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Attention Weight", rotation=270, labelpad=15)

    ax.set_xlabel("Key position (attended to)", fontsize=11)
    ax.set_ylabel("Query position (attending from)", fontsize=11)

    if annotate_sink:
        stats = attention_sink_stats(matrix, sink_index=0)
        title = (f"{title}\nAttention sink (token 0): "
                 f"mean {stats['mean_sink_share'] * 100:.1f}% / "
                 f"max {stats['max_sink_share'] * 100:.1f}% of each row")

    ax.set_title(title, fontsize=12, fontweight="bold")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def create_attention_comparison(
    matrices: List[np.ndarray],
    tokens_list: List[List[str]],
    titles: List[str],
    save_path: Optional[str] = None,
    figsize: Optional[Tuple[int, int]] = None,
    cmap: str = "viridis",
    suptitle: str = "Attention Pattern Comparison",
) -> plt.Figure:
    """
    Plot several [seq x seq] attention matrices side by side for comparison.

    Used to contrast attention patterns - e.g. two different layers, two
    prompts, or with-tools vs without-tools - as described in Chapter 2.
    """
    n = len(matrices)
    if figsize is None:
        figsize = (7 * n, 6)
    fig, axes = plt.subplots(1, n, figsize=figsize)
    if n == 1:
        axes = [axes]

    cmap_obj = plt.get_cmap(cmap).copy()
    cmap_obj.set_bad(color="#f0f0f0")

    for ax, matrix, tokens, title in zip(axes, matrices, tokens_list, titles):
        matrix = np.asarray(matrix, dtype=float)
        masked = np.ma.array(matrix, mask=np.triu(np.ones_like(matrix, dtype=bool), k=1))
        im = ax.imshow(masked, cmap=cmap_obj, aspect="auto")

        seq_len = matrix.shape[0]
        labels = clean_token_labels(tokens)
        if seq_len <= 40:
            ticks = np.arange(seq_len)
        else:
            step = int(np.ceil(seq_len / 40))
            ticks = np.arange(0, seq_len, step)
        ax.set_xticks(ticks)
        ax.set_xticklabels([labels[i] for i in ticks], rotation=90, fontsize=5)
        ax.set_yticks(ticks)
        ax.set_yticklabels([labels[i] for i in ticks], fontsize=5)

        stats = attention_sink_stats(matrix, sink_index=0)
        ax.set_title(f"{title}\nsink mean {stats['mean_sink_share'] * 100:.1f}%",
                     fontsize=10, fontweight="bold")
        ax.set_xlabel("Key position", fontsize=9)
        ax.set_ylabel("Query position", fontsize=9)
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    fig.suptitle(suptitle, fontsize=13, fontweight="bold")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


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
