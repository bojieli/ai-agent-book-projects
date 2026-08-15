# Korean Mistral Model Evaluation Guide

This guide explains how to use the evaluation script to test your trained Korean Mistral models.

## Overview

After running `continued-pretrain.py`, you'll have two saved models:
- `lora_model_pretrained/` - Model after Korean pretraining (before instruction finetuning)
- `lora_model/` - Final model after instruction finetuning

## Quick Start

### Basic Evaluation (Final Finetuned Model)

```bash
python evaluate_model.py
```

This will:
- Load the final finetuned model from `lora_model/`
- Run 6 test cases (Korean + English, Wikipedia + Instructions)
- Use default parameters (max_new_tokens=150)

### Evaluate Pretrained Model (Before SFT)

```bash
python evaluate_model.py --pretrained
```

This loads the model after Korean pretraining but before instruction finetuning.

## Command Line Options

### Model Selection

```bash
# Evaluate the pretrained model
python evaluate_model.py --pretrained

# Evaluate a custom model path
python evaluate_model.py --model_path path/to/your/model

# Load in full precision (more memory, higher quality)
python evaluate_model.py --load_in_4bit False
```

### Generation Parameters

```bash
# Generate more tokens
python evaluate_model.py --max_new_tokens 300

# Use sampling for more creative outputs
python evaluate_model.py --use_sampling --temperature 0.8 --top_p 0.95
```

### All Available Options

| Option | Default | Description |
|--------|---------|-------------|
| `--model_path` | `lora_model` | Path to saved LoRA model |
| `--pretrained` | `False` | Load pretrained model (before SFT) |
| `--max_seq_length` | `2048` | Maximum sequence length |
| `--load_in_4bit` | `True` | Use 4-bit quantization |
| `--max_new_tokens` | `150` | Maximum tokens to generate |
| `--use_sampling` | `False` | Enable sampling (vs greedy) |
| `--temperature` | `0.7` | Sampling temperature (creativity) |
| `--top_p` | `0.9` | Top-p nucleus sampling |

## Example Use Cases

### Compare Models Side-by-Side

```bash
# First, test the pretrained model
python evaluate_model.py --pretrained > results_pretrained.txt

# Then, test the finetuned model
python evaluate_model.py > results_finetuned.txt

# Compare the outputs
diff results_pretrained.txt results_finetuned.txt
```

### Creative vs Deterministic Generation

```bash
# Deterministic (greedy decoding) - same output every time
python evaluate_model.py

# Creative (sampling) - different output each time
python evaluate_model.py --use_sampling --temperature 0.7

# Very creative (higher temperature)
python evaluate_model.py --use_sampling --temperature 1.0

# More focused (lower temperature)
python evaluate_model.py --use_sampling --temperature 0.3
```

### Long-Form Generation

```bash
# Generate longer responses
python evaluate_model.py --max_new_tokens 500
```

## Test Cases

### Evaluation Script (evaluate_model.py)
Runs 6 test cases on a single model:

1. **Korean Wikipedia Article (Artificial Intelligence)** - Tests encyclopedic writing in Korean
2. **English Wikipedia Article (Artificial Intelligence)** - Ensures English preservation
3. **Korean Instruction (Explain Kimchi)** - Tests instruction-following for cultural topics
4. **English Instruction (Explain Thanksgiving Turkey)** - Tests English instruction-following
5. **Korean Instruction (Introduce Seoul)** - Tests factual knowledge in Korean
6. **Korean Instruction (Explain K-pop)** - Tests modern cultural knowledge

### Comparison Script (compare_models.py)
Runs 5 test cases across 3 models (15 total outputs):

1. **Korean Wikipedia - AI** - Shows Korean capability progression
2. **English Wikipedia - AI** - Validates English preservation (encyclopedic writing)
3. **Korean Instruction - Kimchi** - Shows instruction-following improvement
4. **Korean Instruction - Seoul** - Tests factual accuracy improvement
5. **English Instruction - Thanksgiving** - Validates English preservation (instruction-following)

The comparison script includes both English Wikipedia AND English Instruction tests to comprehensively validate that English capabilities remain strong throughout all training stages.

## Understanding the Output

### Color Coding
- 🔵 **Blue**: Loading and setup information
- 🟡 **Yellow**: Parameters and configuration
- 🟢 **Green**: Successful operations and output
- 🔴 **Red**: Errors
- 🔵 **Cyan**: Prompts and tips

### Evaluation Metrics (Manual)

When evaluating outputs, consider:

1. **Fluency**: Is the Korean grammatically correct?
2. **Factual Accuracy**: Are the facts correct?
3. **Instruction Following**: Does it answer the question?
4. **Coherence**: Does it make logical sense?
5. **Cultural Appropriateness**: Is cultural information accurate?

## Troubleshooting

### "Model path does not exist"
Make sure you've run `continued-pretrain.py` first to train and save the models.

### Out of Memory
Try:
```bash
# Use 4-bit quantization
python evaluate_model.py --load_in_4bit

# Reduce max sequence length
python evaluate_model.py --max_seq_length 1024

# Generate fewer tokens
python evaluate_model.py --max_new_tokens 100
```

### Outputs Too Short
Increase max tokens:
```bash
python evaluate_model.py --max_new_tokens 300
```

### Want Different Outputs Each Time
Enable sampling:
```bash
python evaluate_model.py --use_sampling
```

## Tips for Best Results

1. **Start with defaults**: Run with no arguments first
2. **Compare stages**: Test both `--pretrained` and final model
3. **Use sampling for variety**: Add `--use_sampling` for creative outputs
4. **Monitor GPU memory**: Check the memory stats in output

## Expected Performance

### Baseline Model (No Training)
- ❌ Korean: Poor, repetitive, often nonsensical
- ✅ English: Good, coherent, accurate

### Pretrained Model (After Korean Training)
- ⚠️ Korean: Improved fluency, better vocabulary
- ✅ English: Maintained quality
- ⚠️ Instructions: Better than baseline, but not perfect

### Finetuned Model (After SFT)
- ✅ Korean: Fluent, accurate, follows instructions
- ✅ English: Maintained quality
- ✅ Instructions: Good instruction-following in both languages

## Advanced Usage

### Batch Testing Multiple Configurations

Create a shell script:

```bash
#!/bin/bash
# test_configs.sh

echo "Testing different temperatures..."

for temp in 0.3 0.7 1.0; do
    echo "=== Testing temperature=$temp ==="
    python evaluate_model.py --use_sampling --temperature $temp \
        --max_new_tokens 150 > results_temp_${temp}.txt
done

echo "Testing different token lengths..."

for tokens in 100 200 300; do
    echo "=== Testing max_new_tokens=$tokens ==="
    python evaluate_model.py --max_new_tokens $tokens \
        > results_tokens_${tokens}.txt
done
```

### Custom Test Prompts

Modify the `run_evaluation()` function in `evaluate_model.py` to add your own test cases.

## References

- Main training script: `continued-pretrain.py`
- Unsloth documentation: https://docs.unsloth.ai
- Generation parameters: https://huggingface.co/docs/transformers/main_classes/text_generation

## Support

If you encounter issues:
1. Check that training completed successfully
2. Verify model files exist in `lora_model/` or `lora_model_pretrained/`
3. Ensure you have sufficient GPU memory
4. Try reducing `--max_seq_length` or `--max_new_tokens`

