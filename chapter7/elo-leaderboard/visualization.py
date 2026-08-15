"""
Visualization tools for Elo leaderboard analysis
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Tuple, Optional
import plotly.graph_objects as go
import plotly.express as px


def plot_leaderboard(leaderboard_data: list, top_n: int = 20, save_path: Optional[str] = None):
    """
    Plot static leaderboard bar chart.
    
    Args:
        leaderboard_data: List of (model, rating, matches, wins) tuples
        top_n: Number of top models to display
        save_path: If provided, save figure to this path
    """
    # Convert to DataFrame and get top N
    df = pd.DataFrame(leaderboard_data, columns=['model', 'rating', 'matches', 'wins'])
    df = df.head(top_n)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create horizontal bar chart
    bars = ax.barh(range(len(df)), df['rating'], color=plt.cm.viridis(np.linspace(0, 1, len(df))))
    
    # Customize
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df['model'])
    ax.set_xlabel('Elo Rating', fontsize=12)
    ax.set_title(f'Model Leaderboard - Top {top_n} Models', fontsize=14, fontweight='bold')
    ax.invert_yaxis()  # Highest rating at top
    
    # Add value labels on bars
    for i, (rating, matches) in enumerate(zip(df['rating'], df['matches'])):
        ax.text(rating + 10, i, f'{rating:.0f} ({matches} matches)', 
                va='center', fontsize=9)
    
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved leaderboard to {save_path}")
    
    plt.show()


def plot_win_rate_matrix(win_rate_df: pd.DataFrame, 
                         top_n: int = 15,
                         save_path: Optional[str] = None):
    """
    Plot heatmap of win rate matrix.
    
    Args:
        win_rate_df: DataFrame with win rates (rows beat columns)
        top_n: Number of models to include
        save_path: If provided, save figure to this path
    """
    # Get top N models by average win rate
    avg_win_rates = win_rate_df.mean(axis=1).sort_values(ascending=False)
    top_models = avg_win_rates.head(top_n).index.tolist()
    
    # Subset matrix
    subset = win_rate_df.loc[top_models, top_models]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # Plot heatmap
    sns.heatmap(subset, annot=True, fmt='.2f', cmap='RdYlGn', center=0.5,
                vmin=0, vmax=1, square=True, linewidths=0.5,
                cbar_kws={'label': 'Win Rate'}, ax=ax)
    
    ax.set_title(f'Win Rate Matrix - Top {top_n} Models\n(Row vs Column)', 
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Opponent (Column)', fontsize=12)
    ax.set_ylabel('Model (Row)', fontsize=12)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved win rate matrix to {save_path}")
    
    plt.show()


def plot_rating_history(history_df: pd.DataFrame, 
                        models: Optional[List[str]] = None,
                        top_n: int = 10,
                        save_path: Optional[str] = None):
    """
    Plot rating evolution over time for selected models.
    
    Args:
        history_df: DataFrame with columns: date, model, rating
        models: List of specific models to plot (if None, plot top N)
        top_n: If models not specified, plot top N models by final rating
        save_path: If provided, save figure to this path
    """
    if models is None:
        # Get top N models by final rating
        final_date = history_df['date'].max()
        final_ratings = history_df[history_df['date'] == final_date].nlargest(top_n, 'rating')
        models = final_ratings['model'].tolist()
    
    # Filter data
    plot_data = history_df[history_df['model'].isin(models)].copy()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot each model
    for model in models:
        model_data = plot_data[plot_data['model'] == model].sort_values('date')
        ax.plot(model_data['date'], model_data['rating'], marker='o', 
                label=model, linewidth=2, markersize=4)
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Elo Rating', fontsize=12)
    ax.set_title('Model Rating Evolution Over Time', fontsize=14, fontweight='bold')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax.grid(alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved rating history to {save_path}")
    
    plt.show()


def plot_rating_distribution(leaderboard_data: list, save_path: Optional[str] = None):
    """
    Plot distribution of ratings across all models.
    
    Args:
        leaderboard_data: List of (model, rating, matches, wins) tuples
        save_path: If provided, save figure to this path
    """
    df = pd.DataFrame(leaderboard_data, columns=['model', 'rating', 'matches', 'wins'])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Histogram
    ax1.hist(df['rating'], bins=30, color='steelblue', edgecolor='black', alpha=0.7)
    ax1.axvline(df['rating'].mean(), color='red', linestyle='--', 
                linewidth=2, label=f'Mean: {df["rating"].mean():.1f}')
    ax1.axvline(df['rating'].median(), color='green', linestyle='--', 
                linewidth=2, label=f'Median: {df["rating"].median():.1f}')
    ax1.set_xlabel('Elo Rating', fontsize=12)
    ax1.set_ylabel('Count', fontsize=12)
    ax1.set_title('Rating Distribution', fontsize=13, fontweight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # Box plot
    ax2.boxplot(df['rating'], vert=True)
    ax2.set_ylabel('Elo Rating', fontsize=12)
    ax2.set_title('Rating Box Plot', fontsize=13, fontweight='bold')
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Saved rating distribution to {save_path}")
    
    plt.show()


def create_interactive_leaderboard(history_df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """
    Create interactive Plotly visualization of ranking evolution.
    
    Args:
        history_df: DataFrame with columns: date, model, rating, rank
        top_n: Number of top models to include
        
    Returns:
        Plotly Figure object
    """
    # Get top N models by final rating
    final_date = history_df['date'].max()
    final_ratings = history_df[history_df['date'] == final_date].nlargest(top_n, 'rating')
    top_models = final_ratings['model'].tolist()
    
    # Filter data
    plot_data = history_df[history_df['model'].isin(top_models)].copy()
    
    # Create figure
    fig = go.Figure()
    
    for model in top_models:
        model_data = plot_data[plot_data['model'] == model].sort_values('date')
        
        fig.add_trace(go.Scatter(
            x=model_data['date'],
            y=model_data['rating'],
            mode='lines+markers',
            name=model,
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Date: %{x}<br>' +
                         'Rating: %{y:.0f}<br>' +
                         '<extra></extra>'
        ))
    
    fig.update_layout(
        title='Interactive Model Rating Evolution',
        xaxis_title='Date',
        yaxis_title='Elo Rating',
        hovermode='closest',
        height=600,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    return fig


def create_rank_evolution_chart(history_df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """
    Create interactive rank evolution chart (lower rank number is better).
    
    Args:
        history_df: DataFrame with columns: date, model, rating, rank
        top_n: Number of models to track
        
    Returns:
        Plotly Figure object
    """
    # Get models that were ever in top N
    models_in_top = history_df[history_df['rank'] <= top_n]['model'].unique()
    
    # Filter data
    plot_data = history_df[history_df['model'].isin(models_in_top)].copy()
    
    # Create figure
    fig = go.Figure()
    
    for model in models_in_top:
        model_data = plot_data[plot_data['model'] == model].sort_values('date')
        
        fig.add_trace(go.Scatter(
            x=model_data['date'],
            y=model_data['rank'],
            mode='lines+markers',
            name=model,
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Date: %{x}<br>' +
                         'Rank: #%{y}<br>' +
                         '<extra></extra>'
        ))
    
    fig.update_layout(
        title=f'Model Rank Evolution (Top {top_n})',
        xaxis_title='Date',
        yaxis_title='Rank',
        yaxis=dict(autorange='reversed'),  # Lower rank at top
        hovermode='closest',
        height=600,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )
    
    return fig

