# Log Sanitization with Local LLM

This project demonstrates using a local Qwen3 8B model via Ollama to detect and sanitize Level 3 PII (Personally Identifiable Information) from conversation logs. The system loads test cases from the user-memory-evaluation framework and processes them to remove sensitive information.

## Level 3 PII Categories

Based on the privacy protection architecture, Level 3 PII includes highly sensitive information:
- Social Security Numbers (SSN)
- Credit Card Numbers
- Bank Account Numbers
- Medical Record Numbers
- Medical Diagnoses and Treatment Information
- Prescription Information
- Driver's License Numbers
- Passport Numbers
- Financial PINs
- Tax ID Numbers
- Health Insurance IDs
- Biometric Data

## Features

- **Local LLM Processing**: Uses Ollama with Qwen3 8B model for privacy-preserving PII detection
- **Internal Reasoning**: Shows the model's thinking process using `<think>` tags for transparency
- **Streaming Output**: Real-time display of thinking and PII detection progress
- **Performance Metrics**: Measures TTFT (Time to First Token), token counts, and processing speeds
- **Batch Processing**: Can process multiple test cases from user-memory-evaluation framework
- **Detailed Metrics**: Tracks prefill time, output time, tokens per second for both phases

## Installation

### 1. Install Ollama

#### macOS:
```bash
brew install ollama
ollama serve  # Run in separate terminal
```

#### Linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
systemctl start ollama
```

#### Windows:
Download from [ollama.com](https://ollama.com/download/windows)

### 2. Pull the Qwen3 Model
```bash
ollama pull qwen3:8b
```

Note: The 8B model requires approximately 4.5GB of disk space.

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Demo Mode
Run a quick demo with sample PII data:
```bash
python main.py --demo
```

### Process All Layer 3 Test Cases
Process all complex test cases from user-memory-evaluation:
```bash
python main.py
```

### Process Specific Test Case
```bash
python main.py --test-id layer3_13_emergency_medical_cascade
```

### Limit Number of Test Cases
Process only the first N test cases:
```bash
python main.py --limit 3
```

## Output Structure

The sanitized logs and metrics are saved in the `output/` directory:

```
output/
├── <test_id>_sanitized.txt    # Sanitized conversation text
├── <test_id>_summary.json     # Summary of PII found and replaced
├── performance_metrics.json   # Detailed performance metrics
└── performance_summary.json   # Aggregated performance statistics
```

## Performance Metrics

The system tracks the following metrics for each conversation:

### Timing Metrics
- **Prefill Time (TTFT)**: Time to first token in milliseconds
- **Output Time**: Time to generate all output tokens
- **Total Time**: End-to-end processing time

### Token Metrics
- **Input Tokens**: Number of tokens in the prompt
- **Output Tokens**: Number of tokens generated
- **Prefill Speed**: Tokens per second during prefill phase
- **Output Speed**: Tokens per second during generation

### Sanitization Metrics
- **PII Items Found**: Number of Level 3 PII values detected
- **Replacements Made**: Number of replacements with [REDACTED]

## Example Output

```
🚀 Starting Log Sanitization with Local LLM
============================================================
📦 Loading test cases from user-memory-evaluation...
🤖 Initializing Ollama agent...
✅ Using model: qwen3:0.6b

[1/1] Test Case: layer3_13_emergency_medical_cascade
   Title: Emergency Medical Crisis - Multi-System Coordination Response
   Conversations: 8

🔍 Processing conversation: emergency_room_001
   Found 3 PII items
   - 123-45-6789
   - 4532 1234 5678 9012
   - MRN-789456

============================================================
PERFORMANCE SUMMARY
============================================================

📊 Total Conversations Processed: 8

⏱️  Timing Metrics (milliseconds):
   Prefill (TTFT): 125.34 ms (median: 118.50)
   Output Time:    234.67 ms (median: 220.00)
   Total Time:     360.01 ms (median: 338.50)

📝 Token Metrics:
   Average Input Tokens:  450.5
   Average Output Tokens: 25.3
   Total Tokens Processed: 4206

⚡ Speed Metrics (tokens/second):
   Prefill Speed: 3592.8 tok/s
   Output Speed:  107.8 tok/s

🔒 Sanitization Results:
   Total PII Items Found:     24
   Total Replacements Made:   48
   Average PII per Conversation: 3.0
```

## Architecture

The project consists of several modules:

1. **config.py**: Configuration for Ollama model and PII categories
2. **test_loader.py**: Loads test cases from user-memory-evaluation framework
3. **agent.py**: Core sanitization logic using Ollama
4. **metrics.py**: Performance metrics collection and reporting
5. **main.py**: Main entry point and orchestration

## How It Works

1. **Test Case Loading**: The system loads conversation histories from the user-memory-evaluation framework
2. **PII Detection**: Each conversation is sent to the local Qwen3 0.6B model with a specialized prompt to detect Level 3 PII
3. **Sanitization**: Detected PII values are replaced with [REDACTED] in the original text
4. **Metrics Collection**: Performance metrics are collected for each operation
5. **Output Generation**: Sanitized logs and performance summaries are saved to the output directory

## Privacy Considerations

- All processing happens locally using Ollama - no data is sent to external APIs
- The Qwen3 0.6B model runs entirely on your local machine
- Sanitized logs replace sensitive information with [REDACTED] placeholders
- Original PII values are logged for verification but should be handled securely

## Troubleshooting

### "Ollama not found"
Make sure Ollama is installed and running:
```bash
ollama serve
```

### "Model qwen3:8b not found"
Pull the model:
```bash
ollama pull qwen3:8b
```

### "Evaluation framework not found"
Ensure the user-memory-evaluation project exists at:
```
../user-memory-evaluation/
```
