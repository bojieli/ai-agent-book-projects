# IMO Super Agent with Guard Agent

This folder contains the Super Agent and Guard Agent dialogue system migrated from the GAIA project, specifically designed for solving IMO (International Mathematical Olympiad) problems.

## Quick Start

1. **Setup Environment**:
   ```bash
   cd AWorld/examples/imo
   ./setup_env.sh
   ```

2. **Configure Environment Variables**:
   ```bash
   cp .env_template .env
   # Edit .env file with your API keys
   ```

3. **Run the Program**:
   ```bash
   conda activate aworld_imo_env
   python run.py --q imo4
   ```

## File Structure

```
imo/
├── run.py                        # Main execution file
├── guard_tool_caller.py          # Guard tool caller
├── prompt.py                     # System prompts
├── utils.py                      # Utility functions
├── metadata.jsonl                # IMO problem dataset
├── requirements.txt              # Python dependencies
├── setup_env.sh                  # Environment setup script
├── README.md                     # Documentation
└── .env                          # Environment variables configuration file
```

## Environment Setup

### Method 1: Automatic Setup (Recommended)

```bash
# Navigate to the imo directory
cd AWorld/examples/imo

# Run the automatic setup script
./setup_env.sh
```

This script will automatically:
1. Create a new conda environment named `aworld_imo_env`
2. Install all necessary dependencies
3. Install the AWorld framework
4. Provide usage instructions

### Method 2: Manual Setup

If you prefer manual setup, follow these steps:

```bash
# 1. Create a new conda environment
conda create -n aworld_imo_env python=3.11 -y

# 2. Activate the environment
conda activate aworld_imo_env

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install AWorld framework
cd ../../../
pip install -e .
cd AWorld/examples/imo
```

## Environment Configuration

Before running the program, you need to set up your environment variables:

1. **Copy the template file**:
   ```bash
   cp .env_template .env
   ```

2. **Edit the `.env` file** with your actual API keys and configurations:
   ```bash
   # LLM Configuration
   LLM_MODEL_NAME="your_model_name"          # e.g., "google/gemini-2.5-pro-preview"
   LLM_API_KEY="your_api_key"                # Your API key from OpenAI, OpenRouter, etc.
   LLM_BASE_URL="your_base_url"              # e.g., "https://openrouter.ai/api/v1"
   LLM_TEMPERATURE=0.1

   # Path Configurations (use relative paths)
   IMO_DATASET_PATH="."                      # Current directory
   AWORLD_WORKSPACE="Record"                 # Record directory

   # IMO Server (same as LLM configuration for most cases)
   IMO_LLM_API_KEY="your_imo_api_key"        # Same as LLM_API_KEY
   IMO_LLM_BASE_URL="your_imo_base_url"      # Same as LLM_BASE_URL
   IMO_LLM_MODEL_NAME="your_imo_model_name"  # Same as LLM_MODEL_NAME
   ```

**Important Notes**:
- The `.env_template` file contains a template with empty values. You need to fill in your actual API keys and configurations in the `.env` file.
- For most users, the IMO Server configuration can be the same as the LLM configuration.
- You can obtain API keys from services like OpenAI, OpenRouter, or other LLM providers.
- The path configurations use relative paths (`.`) which means the current directory.

## Using the Environment

After setup, use the IMO project:

```bash
# 1. Activate the environment
conda activate aworld_imo_env

# 2. Navigate to the project directory
cd AWorld/examples/imo

# 3. Run the program
python run.py --q imo4
```

## Dataset Description

The IMO dataset is contained in the `metadata.jsonl` file, including the following IMO problems:
- imo1: Plane geometry problem
- imo2: Circle and triangle problem
- imo3: Function problem
- imo4: Sequence problem
- imo5: Game theory problem
- imo6: Grid covering problem

**Dataset Format**: Each line in `metadata.jsonl` is a JSON object with:
- `task_id`: Unique identifier for the problem (e.g., "imo1", "imo2")
- `Question`: The mathematical problem statement

**Adding New Problems**: You can add new problems by appending JSON lines to `metadata.jsonl`:
```json
{"task_id": "your_problem_id", "Question": "Your mathematical problem statement"}
```

## Running the Main Program

```bash
# Run a specific problem (recommended to start with test for testing)
python run.py --q test


# Run a range of problems
python run.py --start 0 --end 5

# Run all problems
python run.py --start 0 --end 6
```

## Main Features

1. **Super Agent**: Responsible for solving IMO mathematical problems
2. **Guard Agent**: Acts as an IMO grader to verify the correctness of solutions
3. **Dialogue Mechanism**: Two agents engage in multi-round conversations to refine solutions
4. **Solution Recording**: Records the complete conversation history and final solution

## Parameter Description

- `--q`: Specify problem ID (highest priority), e.g., `imo4`
- `--specific_task`: Run only a specific task_id, e.g., `imo4` (overrides --start and --end)
- `--start/--end`: Specify problem range (0-5 for all 6 IMO problems)
- `--skip`: Skip previously processed problems

## Output Files

- Log files: `~/.aworld/solution_*.log`
- Result files: `~/.aworld/results.json` (contains conversation history and solutions)

## Environment Information

- **Environment Name**: `aworld_imo_env`
- **Python Version**: 3.11
- **Main Dependencies**: 
  - AWorld framework core components
  - OpenAI client
  - Environment variable management tools
  - Other necessary utility packages

## Advantages

1. **Environment Isolation**: Avoids dependency conflicts with existing `aworld_gaia_July` environment
2. **Lightweight**: Only installs packages necessary for the IMO project
3. **Reproducible**: Ensures environment consistency through `requirements.txt`
4. **Easy Management**: Independent environment for easy maintenance and cleanup

## Troubleshooting

If you encounter issues:

1. **conda command not found**: Ensure Miniconda or Anaconda is installed
2. **Dependency installation failed**: Try manual installation: `pip install -r requirements.txt`
3. **AWorld framework installation failed**: Execute manually: `cd ../../../ && pip install -e .`

## Cleanup

To remove this environment:

```bash
conda deactivate
conda env remove -n aworld_imo_env
```

## Important Notes

1. Ensure the AWorld framework is properly installed
2. Check that environment variables are correctly configured
3. IMO dataset is pre-configured in the imo folder
4. Recommended to start testing with test problem
5. The system focuses on solution quality and reasoning process rather than exact answer matching



## Acknowledgements

The IMO-related prompt code in this repository is adapted from the work of Lin Yang and Yichen Huang. We are grateful for their original implementation.

- Original Repository: [https://github.com/lyang36/IMO25](https://github.com/lyang36/IMO25)