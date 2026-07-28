# Elo Rating Leaderboard from Pairwise Comparisons

## English

**Experiment 6-6**: Building Model Leaderboard from Pairwise Comparison Data

This project implements an Elo rating system from scratch to analyze model performance using Chatbot Arena's public voting data. The implementation demonstrates how the Bradley-Terry model extracts relative model capabilities from millions of pairwise comparison votes.

## Overview

The Elo rating system is a method for calculating the relative skill levels of players (or in this case, AI models) in zero-sum games. Originally developed for chess, it has been adapted to rank AI language models based on head-to-head comparisons from user votes.

### Key Features

- **High-performance implementation**: NumPy + Numba JIT + parallel processing for optimal speed
- **Real voting data analysis**: Uses actual Chatbot Arena voting data with millions of pairwise comparisons
- **Win rate prediction**: Calculates expected win probabilities between any two models
- **Historical tracking**: Builds time-series snapshots showing ranking evolution
- **Interactive visualizations**: Multiple visualization types including animated bar chart races
- **Scalable**: Efficiently handles 2GB datasets with hundreds of thousands of matches

## Mathematical Foundation

The Elo system is based on the Bradley-Terry model, which models the probability that model A beats model B as:

```
P(A beats B) = 1 / (1 + 10^((R_B - R_A) / 400))
```

After each match, ratings are updated using:

```
R_A_new = R_A + K * (S_A - E_A)
```

Where:
- `R_A` is the current rating of model A
- `K` is the learning rate (K-factor)
- `S_A` is the actual score (1 for win, 0 for loss, 0.5 for tie)
- `E_A` is the expected score (predicted win probability)

## Requirements

- **Disk Space**: At least 3GB free (2GB for data file, 1GB for processing)
- **RAM**: 4GB+ recommended for full dataset analysis
- **Internet**: Stable connection for ~2GB download
- **Python**: 3.8+

## Installation

```bash
cd chapter6/elo-leaderboard
pip install -r requirements.txt
```

## 命令行工具 / Command-Line Interface (`cli.py`)

`cli.py` 是本实验统一的 argparse 命令行入口（中文 `--help`），把整条流水线拆成子命令：
**对战 (battle) -> 计算评分 (elo) -> 展示排行榜 (leaderboard)**，并提供 `pipeline` 一步到位。

```bash
python cli.py --help              # 查看全部子命令
python cli.py battle --help       # 查看某个子命令的参数

# 默认离线端到端演示：模拟对战 -> 在线 Elo -> 最终排行榜表格（无需任何数据/API）
python cli.py                     # 等价于 python cli.py pipeline
```

### 子命令

| 子命令 | 作用 | 关键参数 |
|--------|------|----------|
| `battle` | 生成两两对战结果 | `--source {simulate,arena,llm}`、`--num-battles`、`--tie-prob`、`--seed`、`--sample`、`--output` |
| `elo` | 从对战结果计算评分 | `--method {online-elo,bradley-terry}`、`--k`、`--bootstrap`、`--input`、`--output` |
| `leaderboard` | 渲染最终排行榜表格 | `--input`（对战或评分文件）、`--method`、`--bootstrap`、`--top-n` |
| `pipeline` | 一步跑完 对战 -> Elo -> 排行榜 | 上述参数的并集 |

### 三种对战来源（`--source`）

- **`simulate`（默认，纯离线）**：从已知的潜在实力分模拟对战。因为真值已知，可用来**校验**恢复出的排行榜排序是否正确；`--tie-prob` 控制平局比例，用于演练平局处理。
- **`arena`（离线）**：加载真实 Chatbot Arena 投票数据（默认 `arena_data.json`，约 2GB），可用 `--sample N` 抽样。
- **`llm`（需 API）**：用 LLM 做配对评判，并内置**位置偏差消除**——每对交换顺序各评一次，两次判决一致才计胜负、否则记为平局（对应书中 6.4 位置偏差讨论）。仅此来源需要 LLM API Key。

  **两种评判后端（`--judge-backend {anthropic,openrouter,auto}`，默认 `auto`）**：
  - `anthropic`：官方 `anthropic` SDK，用 `ANTHROPIC_API_KEY`。
  - `openrouter`：OpenAI 兼容 SDK 指向 `https://openrouter.ai/api/v1`，用 `OPENROUTER_API_KEY`。内部 Claude 名字会自动映射为 OpenRouter id（`claude-opus-4-8` → `anthropic/claude-opus-4.8`，`claude-haiku-4-5` → `anthropic/claude-haiku-4.5`）；已含 `/` 的 id（如 `openai/gpt-5.6-luna`）原样透传。当直连 Anthropic key 缺失或失效时用它兜底。
  - `auto`（默认）：有 `ANTHROPIC_API_KEY` 走 anthropic，否则回退 openrouter。注意 `auto` 只看 key 是否存在、不校验有效性；若 `ANTHROPIC_API_KEY` 存在但已失效，请显式 `--judge-backend openrouter`。

  位置偏差消除与 A/B/tie 解析逻辑与后端无关，两条路径完全一致。

### 分步示例

```bash
# 1) 模拟 5000 场对战（含 10% 平局）
python cli.py battle --source simulate --num-battles 5000 --output battles.json

# 2) 用官方 Bradley-Terry MLE + 100 轮 bootstrap 置信区间计算评分
python cli.py elo --input battles.json --method bradley-terry --bootstrap 100

# 3) 展示前 20 名排行榜（也可直接读评分文件）
python cli.py leaderboard --input battles.json --top-n 20

# 用真实 Arena 数据抽样跑（离线）
python cli.py pipeline --source arena --arena-file arena_data.json --sample 50000 --method bradley-terry --bootstrap 100

# LLM 评判对战（需要 API Key）——官方 Anthropic
export ANTHROPIC_API_KEY=sk-...
python cli.py battle --source llm --candidate-models claude-opus-4-8 claude-haiku-4-5

# LLM 评判对战——通过 OpenRouter 兜底（直连 Anthropic key 缺失/失效时）
export OPENROUTER_API_KEY=sk-or-...
python cli.py battle --source llm --judge-backend openrouter \
  --judge-model claude-opus-4-8 \
  --candidate-models anthropic/claude-haiku-4.5 openai/gpt-5.6-luna
```

模拟来源会同时打印真值潜在实力，方便和恢复出的排行榜对照；在线 Elo 与 Bradley-Terry 两种方法都应恢复出与真值一致的排名（分值不必精确对齐，见下文说明）。

## Quick Start

The project implements **two ranking methods** following official Chatbot Arena:

### 1. Bradley-Terry Model (Default - Recommended)

```bash
python main.py
# or explicitly:
python main.py bradley-terry
```

**Use this for**: Official leaderboard, stable rankings, production use

**Key features**:
- ✅ Official Chatbot Arena method
- ✅ Uses sklearn LogisticRegression for Maximum Likelihood Estimation
- ✅ Order-independent (processes all matches simultaneously)
- ✅ Includes 95% confidence intervals via bootstrap (100 samples)
- ✅ More stable and reliable rankings

**Processing time**: ~2-3 minutes (including bootstrap)

### 2. Online Elo (K=4)

```bash
python main.py online-elo
```

**Use this for**: Understanding Elo mechanics, educational purposes, faster computation

**Key features**:
- ✅ K-factor = 4 (official value used by Chatbot Arena)
- ✅ Simple sequential rating updates
- ✅ Order-dependent (processes matches chronologically)
- ✅ Faster computation (~30 seconds)
- ⚠️ Less stable, can vary based on match order

### Method Comparison

| Feature | Bradley-Terry | Online Elo |
|---------|--------------|------------|
| **Stability** | High (MLE fit) | Medium (sequential) |
| **Order dependence** | None | High |
| **Confidence intervals** | Yes (bootstrap) | No |
| **Speed** | Slower (~3 min) | Faster (~30 sec) |
| **Official method** | ✅ Yes | For comparison only |
| **Recommended** | ✅ Production | Educational |

### What Both Methods Do

1. Download Chatbot Arena voting data (~2GB, 5-15 minutes depending on connection)
2. Apply official filters:
   - Anonymous votes only (blind evaluation)
   - Deduplication (removes top 0.1% redundant prompts)
3. Compute model ratings using selected method
4. Calculate predicted win rates between all model pairs
5. Generate visualizations:
   - `leaderboard.png` - Top 20 models ranked by rating
   - `rating_distribution.png` - Rating histogram and statistics
   - `win_rate_matrix.png` - Predicted win rates (top 30 models)

**Note**: The initial data download is ~2GB and may take several minutes. A progress bar shows download status.

### Quick Demo (Synthetic Data)

To quickly understand Elo mechanics without downloading 2GB:

```bash
python quickstart.py
```

This runs a small demo with synthetic matchups between GPT-4, Claude, Llama, and Gemini.

### Benchmark

To compare both methods:

```bash
python benchmark.py
```

This shows performance and accuracy differences between online Elo and Bradley-Terry approaches.

## Project Structure

```
elo-leaderboard/
├── cli.py                      # Unified argparse CLI (battle / elo / leaderboard / pipeline)
├── battle_simulator.py         # Offline synthetic pairwise-battle generator
├── llm_judge.py                # LLM-as-judge battles with position-bias mitigation (needs API)
├── main.py                     # Main analysis script
├── optimized_elo.py            # NumPy + Numba Elo rating system
├── parallel_processing.py      # Multi-core parallel processing utilities
├── data_loader.py              # Data download and preprocessing
├── leaderboard.py              # Leaderboard calculation and analysis
├── visualization.py            # Static and interactive visualizations
├── animation.py                # Animated bar chart race generator
├── benchmark.py                # Performance benchmark tool
├── quickstart.py               # Quick demo with synthetic data
├── elo_rating.py               # Reference implementation (for comparison)
├── test_elo.py                 # Unit tests
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Usage Examples

### Building Elo Leaderboard

```python
from optimized_elo import build_leaderboard_optimized

# Build Elo leaderboard from DataFrame
elo = build_leaderboard_optimized(
    df,  # DataFrame with columns: model_a, model_b, winner
    initial_rating=1000.0,
    k_factor=32.0,
    show_progress=True
)

# Get leaderboard
leaderboard = elo.get_leaderboard()
for rank, (model, rating, matches, wins) in enumerate(leaderboard[:10], 1):
    win_rate = wins / matches * 100 if matches > 0 else 0
    print(f"{rank}. {model}: {rating:.1f} ({matches} matches, {win_rate:.1f}% win rate)")
```

### Loading and Filtering Data

```python
from data_loader import load_arena_data, filter_data

# Load data
df = load_arena_data("arena_data.json")

# Filter for blind votes only (reduces bias)
df_filtered = filter_data(
    df,
    anony_only=True,      # Only anonymous votes
    language="English",    # Specific language
    min_turn=1            # Minimum conversation turn
)
```

### Building Historical Leaderboards

```python
from data_loader import get_time_slices
from leaderboard import build_historical_leaderboards, get_rating_history

# Create weekly time slices
time_slices = get_time_slices(df, interval='W')

# Build leaderboard for each time point
historical_leaderboards = build_historical_leaderboards(
    df, time_slices, initial_rating=1000.0, k_factor=32.0
)

# Get rating history DataFrame
history_df = get_rating_history(historical_leaderboards)
```

### Creating Visualizations

```python
from visualization import (
    plot_leaderboard,
    plot_win_rate_matrix,
    plot_rating_history,
    create_interactive_leaderboard
)

# Static leaderboard chart
plot_leaderboard(leaderboard, top_n=20, save_path="leaderboard.png")

# Win rate heatmap
win_rate_df = calculate_win_rate_matrix_from_data(df)
plot_win_rate_matrix(win_rate_df, top_n=15, save_path="matrix.png")

# Rating evolution
plot_rating_history(history_df, models=["gpt-4", "claude-v1"], 
                   save_path="history.png")

# Interactive chart
fig = create_interactive_leaderboard(history_df, top_n=15)
fig.write_html("interactive.html")
```

### Creating Animated Bar Chart Race

```python
from animation import create_simple_animation

# Generate animated HTML
animation_file = create_simple_animation(
    history_df,
    output_path="animation.html",
    top_n=15
)

# Open animation.html in browser to view
```

## Output Files

After running `main.py`, the following files are generated:

### Static Images (PNG)
- `leaderboard.png` - Current top 20 models ranked by Elo rating
- `rating_distribution.png` - Histogram and box plot of rating distribution
- `win_rate_matrix.png` - Heatmap showing pairwise win rates
- `rating_history.png` - Line chart showing rating evolution over time

### Interactive Visualizations (HTML)
- `interactive_rating_evolution.html` - Interactive chart with zoom/pan
- `interactive_rank_evolution.html` - Interactive rank tracking
- `leaderboard_animation.html` - **Animated bar chart race** showing ranking evolution

## Key Parameters

### Elo System Parameters (Online Elo Method)

- **initial_rating** (default: 1000.0): Starting rating for all models
- **k_factor** (default: 4.0): Learning rate controlling update magnitude
  - Official Chatbot Arena uses K=4 for stability
  - Higher K-factor (e.g., 32): More volatile, faster adaptation to new data
  - Lower K-factor (e.g., 4): More stable, less influenced by recent matches

### Bradley-Terry Parameters

- **SCALE** (400): Elo scale parameter - determines rating point interpretation
- **BASE** (10): Base for logistic function - standard for Elo calculations  
- **INIT_RATING** (1000): Initial rating for all models
- **bootstrap_rounds** (100): Number of bootstrap samples for confidence intervals

### Time Slice Intervals

For historical analysis, you can adjust the time granularity:
- `'D'` - Daily snapshots
- `'W'` - Weekly snapshots (recommended)
- `'M'` - Monthly snapshots

### Visualization Parameters

- **top_n**: Number of top models to display (10-20 recommended)
- **Animation speed**: Adjustable in the HTML interface (1x to 10x)

## Data Format

The Chatbot Arena data includes the following fields:

- `model_a`: Identifier for first model
- `model_b`: Identifier for second model
- `winner`: Match outcome ('model_a', 'model_b', or 'tie')
- `tstamp`: Unix timestamp of the vote
- `judge`: User who made the vote
- `turn`: Conversation turn number
- `anony`: Whether vote was anonymous/blind
- `language`: Language of the conversation

## Validation

The implementation validates the Elo predictions against empirical win rates:

```python
from leaderboard import compare_win_rates

# Compare predicted vs actual win rates
comparison = compare_win_rates(elo_system, empirical_win_rates)
mean_error = comparison['error'].mean()
print(f"Mean Absolute Error: {mean_error:.4f}")
```

A low MAE (< 0.05) indicates the Elo model fits the data well.

## Analysis Insights

The project helps identify:

1. **Current Rankings**: Which models are currently strongest
2. **Rating Trends**: How model performance evolves over time
3. **Breakthrough Moments**: When new models enter or shake up rankings
4. **Competitive Dynamics**: Which models are closely matched
5. **Long-term Trajectories**: Models in ascent vs. decline
6. **Rating Stability**: Volatility in model performance

## Performance Architecture

The implementation is designed for high performance on large datasets (2GB+).

### Core Optimizations

#### 1. **NumPy + Numba JIT Compilation**

Uses NumPy arrays and Numba's just-in-time compilation:
- **NumPy arrays** for O(1) integer indexing (vs O(n) dictionary lookups)
- **Numba JIT** compiles hot loops to machine code (50-100x speedup)
- **Pre-allocated arrays** eliminate dynamic memory allocation overhead
- **Integer indices** instead of string model names for cache-friendly access

#### 2. **Multi-Core Parallel Processing**

Parallelizes independent operations across all CPU cores:
- **Historical analysis**: Each time slice processed independently
- **Win rate matrices**: Model pairs computed in parallel chunks
- **Data filtering**: DataFrame operations distributed across cores

```python
from parallel_processing import build_historical_leaderboards_parallel

# Automatically uses all available CPU cores
historical_lb = build_historical_leaderboards_parallel(
    df, time_slices, n_jobs=-1
)
```

#### 3. **Memory Optimization**

Reduces memory footprint through intelligent data types:
- Downcasts numeric types (int64 → int32, float64 → float32)
- Converts repetitive strings to categorical types
- Achieves 30-50% memory reduction

```python
from parallel_processing import optimize_dataframe

df = optimize_dataframe(df)  # Automatic memory optimization
```

### Performance Characteristics

On typical hardware (4-8 core CPU) with the full 2GB dataset:

| Component | Technique | Impact |
|---|---|---|
| Elo Computation | NumPy + Numba JIT | 50-100x faster |
| Historical Analysis | Multi-core parallel | 4-8x faster |
| Win Rate Matrix | Parallel processing | 4-8x faster |
| Memory Usage | Type optimization | 30-50% reduction |
| **Overall** | **Combined** | **~10-15x speedup** |

**Processing time**: 1-2 minutes for full dataset (hundreds of thousands of matches)

## Advanced Usage

### Custom Analysis

The modular design allows for flexible customization:

### Focused Analysis

```python
from optimized_elo import build_leaderboard_optimized
from data_loader import load_arena_data, filter_data

df = load_arena_data("arena_data.json")

# Analyze only recent data
df_recent = filter_data(df, min_date="2024-01-01")
elo_recent = build_leaderboard_optimized(df_recent)

# Analyze specific model family
gpt_models = [m for m in df['model_a'].unique() if 'gpt' in m.lower()]
df_gpt = df[df['model_a'].isin(gpt_models) & df['model_b'].isin(gpt_models)]
elo_gpt = build_leaderboard_optimized(df_gpt)
```

### Export Results

```python
import pandas as pd

# Export leaderboard to CSV
lb_df = pd.DataFrame(leaderboard, columns=['model', 'rating', 'matches', 'wins'])
lb_df.to_csv('leaderboard.csv', index=False)

# Export rating history
history_df.to_csv('rating_history.csv', index=False)
```

## Troubleshooting

### Data Download Issues

If automatic download fails:
1. Manually download from: https://storage.googleapis.com/arena_external_data/public/clean_battle_20240814_public.json
2. Save as `arena_data.json` in the project directory
3. Run `python main.py` again

### Memory Issues

The dataset is large (~2GB, hundreds of thousands of battles). If you encounter memory issues on systems with limited RAM:

```python
from data_loader import load_arena_data, filter_data, get_time_slices
from optimized_elo import build_leaderboard_optimized

# Load and immediately filter to reduce memory usage
df = load_arena_data("arena_data.json")

# Filter to recent data only
df_filtered = filter_data(df, min_date="2024-01-01", anony_only=True)

# Use monthly instead of weekly intervals for historical analysis
time_slices = get_time_slices(df_filtered, interval='M')  # vs 'W' for weekly

# Analyze with smaller top_n for visualizations
elo = build_leaderboard_optimized(df_filtered)
```

The built-in memory optimization reduces footprint by 30-50%, but very large analyses may still require 4GB+ RAM.

### Visualization Issues

- Ensure matplotlib, seaborn, and plotly are installed: `pip install -r requirements.txt`
- For HTML animations, use a modern web browser (Chrome, Firefox, Safari, Edge)
- If plots don't display in Jupyter, use `%matplotlib inline` or save to file

## References

- **Chatbot Arena**: https://chat.lmsys.org/
- **Elo Rating System**: https://en.wikipedia.org/wiki/Elo_rating_system
- **Bradley-Terry Model**: https://en.wikipedia.org/wiki/Bradley–Terry_model
- **LMSYS Paper**: "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"

## Learning Objectives

This experiment demonstrates:

1. **Statistical Modeling**: How pairwise comparisons reveal relative abilities
2. **Online Learning**: Incremental rating updates as new data arrives
3. **Probabilistic Prediction**: Converting rating differences to win probabilities
4. **Data Visualization**: Effective techniques for showing temporal dynamics
5. **Model Evaluation**: Alternative to traditional benchmark approaches

## Technical Details

### Why Elo Computation is Hard to Parallelize

Elo rating computation is **inherently sequential** because each match's rating update depends on the current ratings, which were modified by all previous matches. This is why we can't simply split matches into chunks and process them independently.

However, we can still achieve significant speedups through:

1. **Algorithmic optimization**: NumPy arrays + Numba JIT
2. **Parallelizing independent operations**: Historical analysis, win rate matrices
3. **Memory efficiency**: Better cache utilization
4. **Data structure optimization**: Integer indexing, pre-allocation

### Numba JIT Compilation

The core Elo update loop is compiled to machine code using Numba:

```python
@jit(nopython=True)
def process_elo_updates_vectorized(ratings, model_a_indices, model_b_indices, 
                                   outcomes, k_factor, match_counts, win_counts):
    for i in range(len(model_a_indices)):
        # This loop runs at C speed, not Python speed
        # Typical speedup: 50-100x over pure Python
        ...
```

### Memory Layout

Using NumPy arrays with proper data types:
- `ratings`: float64 array (8 bytes per model)
- `match_counts`: int32 array (4 bytes per model)
- `model_indices`: int32 array (4 bytes per match)

For 500 models and 500K matches: ~10 MB vs ~500 MB for dictionaries.

## Extensions

Potential enhancements:

- Implement Glicko or Glicko-2 rating systems (account for rating uncertainty)
- Add confidence intervals for rating estimates
- Analyze rating by language or task type
- Compare with other ranking methods (e.g., TrueSkill, PageRank)
- Implement time-decay for older matches
- Add statistical significance testing
- Build prediction model for future rankings
- GPU acceleration using CuPy for even larger datasets
- Distributed processing using Dask for multi-machine scaling

## License

This project is part of the AI Agent practical training course materials.

## Contact

For questions or issues, please refer to the course materials or discussion forums.

---

## 中文

该项目围绕**配对比较（pairwise）数据**构建 Elo/Bradley-Terry 排名流程，目标是用公开的模型对战投票数据（重点是 Chatbot Arena）形成可复现的模型排行榜与可视化分析。

### 实验导向背景

Elo 本质上用于“成对对局中的胜率”学习相对能力，最初用于棋类，现被广泛用于语言模型两两对比的排序。

### 关键特性

- 高性能实现：NumPy + Numba JIT + 并行处理。
- 真实数据分析：接入大规模公开投票数据。
- 胜率推断：可预测任意两个模型的胜率。
- 历史追踪：可输出时间序列排行快照。
- 交互可视化：支持静态图与动态动画。
- 可扩展：可承接较大规模比赛集合。

### 数学原理

与 AndroidWorld 风格一致，评分来自 Bradley-Terry：

```
P(A 胜过 B) = 1 / (1 + 10^((R_B - R_A) / 400))
```

单步更新：

```
R_A_new = R_A + K * (S_A - E_A)
```

### 安装与运行

```bash
cd chapter6/elo-leaderboard
pip install -r requirements.txt
```

### 命令行（`cli.py`）

`cli.py` 是统一入口：
- `battle`：生成/采集两两对战
- `elo`：计算评级
- `leaderboard`：出榜
- `pipeline`：端到端一条龙

```bash
python cli.py --help
python cli.py battle --help
python cli.py   # 等价于 python cli.py pipeline
```

### 三类对战源

- `simulate`：合成对战（有真值），用于验证是否恢复出正确排序。
- `arena`：离线加载 `arena_data.json`（约 2GB）；可用 `--sample` 抽样。
- `llm`：调用 LLM 判断对战，带位置偏差消除；支持 `anthropic`、`openrouter` 和 `auto`。

`auto` 会优先使用 Anthropic key，失败时回退 OpenRouter；位置消偏策略与 A/B/tie 判定和后端无关。

### 两种核心评分方法

- Bradley-Terry（推荐）：更稳定，适合正式排行。
- Online Elo：更贴近课程里的机制讲解，速度快但对顺序敏感。

### 项目结构

同上方英文学段落中的文件列表。

### 使用示例

核心示例同上英文学：
- `python cli.py battle ...`
- `python cli.py elo ...`
- `python cli.py leaderboard ...`
- `python demo.py` / `python benchmark.py`

### 注意

- `--sample`、`--pipeline`、`--top-n` 等参数见命令行帮助。
- 建议先看 CLI 输出再对照 `leaderboard` 与可视化文件确认理解。
