# GAIA Agent Setup Guide

## 1. Overview

This guide will help you set up and run the GAIA agent for the AWorld framework. GAIA is a benchmark dataset for evaluating AI agents' capabilities.

## 2. Prerequisites

### 1. System Requirements
- **Operating System**: macOS or Linux (Windows not fully tested)
- **Node.js**: Version 22 LTS with npm
- **Conda**: For environment management

### 2. Required Software
- `libmagic1` - File type detection
- `libreoffice` - Document processing
- `ffmpeg` - Media processing

## 3. Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/inclusionAI/AWorld.git
cd AWorld
```

### 2. Set Up Conda Environment

Create and activate a dedicated Conda environment for GAIA:

```bash
conda env create -f examples/gaia/aworld-gaia.yml
conda activate aworld-gaia
```

> **Note**: If you don't have Conda installed, download Miniconda from [here](https://www.anaconda.com/docs/getting-started/miniconda/install).

### 3. Install AWorld Framework

Install the AWorld framework and build the web UI:

```bash
# Install PDF processing dependencies
pip install "marker-pdf[full]" --no-deps

# Build web UI
sh -c "cd aworld/cmd/web/webui && npm install && npm run build"

# Install AWorld
python setup.py install
```

### 4. Install MCP Tool Dependencies

#### Install Playwright
```bash
playwright install chromium --with-deps --no-shell
```

#### Install System Dependencies

**For macOS:**
```bash
brew install libmagic
brew install ffmpeg
brew install --cask libreoffice
```

> **Note**: Install Homebrew from [brew.sh](https://brew.sh/) if not already installed.

**For Linux:**
```bash
apt-get install -y --no-install-recommends libmagic1 libreoffice ffmpeg
```

### 5. Prepare GAIA Dataset

Download the GAIA dataset from Hugging Face:

```bash
git clone git@hf.co:datasets/gaia-benchmark/GAIA examples/gaia/GAIA
```

> **⚠️ Important**: 
> - You need to configure Hugging Face SSH keys to access the GAIA repository
> - The dataset path will be used as the `GAIA_DATASET_PATH` variable in your `.env` file

### 6. Configure Environment Variables

Create the environment configuration file:

```bash
cp examples/gaia/cmd/agent_deploy/gaia_agent/.env.template examples/gaia/cmd/agent_deploy/gaia_agent/.env
```

Edit the `.env` file and replace all `{YOUR_CONFIG}` placeholders with your actual configuration values.

## 3. Running the GAIA Agent

### 1. Web UI Interface

Start the GAIA agent web interface:

```bash
cd examples/gaia/cmd && aworld web
```

### 2. Command Line Interface

Run GAIA tasks using the command line interface:

```bash
python examples/gaia/run.py --split validation --q c61d22de-5f6c-4958-a7f6-5e9707bd3466
```

## 4. Command Line Arguments

### 1. Required Arguments

| Argument | Type | Description | Default | Example |
|----------|------|-------------|---------|---------|
| `--split` | str | Dataset split to use | `validation` | `--split test` |
| `--start` | int | Start index of the dataset | `0` | `--start 10` |
| `--end` | int | End index of the dataset | `165` | `--end 100` |

### 2. Optional Arguments

| Argument | Type | Description | Example |
|----------|------|-------------|---------|
| `--q` | str | Specific question index (overrides start/end) | `--q 0-0-0-0-0` |
| `--skip` | flag | Skip previously processed questions | `--skip` |
| `--blacklist_file_path` | str | Path to blacklist file | `--blacklist_file_path blacklist.txt` |

## 5. Usage Examples

### 1. Basic Usage
Process a range of questions in the validation split:

```bash
python examples/gaia/run.py --start 10 --end 50 --split validation
```

### 2. Process Specific Question
Run a single question by its index:

```bash
python examples/gaia/run.py --q 0-0-0-0-0
```

### 3. Skip Processed Questions
Process questions while skipping previously completed ones:

```bash
python examples/gaia/run.py --start 10 --end 50 --skip
```

### 4. Use Blacklist
Skip questions listed in a blacklist file:

```bash
python examples/gaia/run.py --start 10 --end 50 --blacklist_file_path blacklist.txt
```

## 6. Expected Output

When running successfully, you should see logs similar to:

```
YYYY-MM-DD HH:MM:SS - root - INFO - Agent answer: egalitarian
YYYY-MM-DD HH:MM:SS - root - INFO - Correct answer: egalitarian
YYYY-MM-DD HH:MM:SS - examples.gaia.utils - INFO - Evaluating egalitarian as a string.
YYYY-MM-DD HH:MM:SS - root - INFO - Question 0 Correct!
```

## 7. Troubleshooting

### 1. Common Issues

1. **Dataset Access Problems**
   - Verify your Hugging Face SSH keys are correctly configured
   - Ensure you have access to the GAIA repository

2. **Installation Issues**
   - Set up a pip mirror if necessary for faster downloads
   - Ensure all system dependencies are properly installed

3. **Environment Issues**
   - Make sure you're using the correct Conda environment (`aworld-gaia`)
   - Verify Node.js version is 22 LTS

### 2. Getting Help

If you encounter issues not covered in this guide:
- Check the project's main documentation
- Review the error logs for specific error messages
- Ensure all prerequisites are properly installed
