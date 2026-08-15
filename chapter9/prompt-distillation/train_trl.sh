#!/bin/bash
# Training script using Hugging Face TRL (more common and easier to use than verl)
#
# This script uses the widely-adopted TRL SFTTrainer instead of verl.
# Benefits:
# - Works directly with JSONL (no parquet conversion needed)
# - Better documentation and community support
# - Simpler setup and fewer dependencies
# - Standard Hugging Face workflow

set -x

# Default configuration
MODEL_NAME=${1:-"Qwen/Qwen3-30B-A3B-Instruct-2507"}
OUTPUT_DIR=${2:-"./models/prompt_distillation_trl"}
TRAIN_FILE=${3:-"./data/prompt_distillation_lang.jsonl"}

echo "============================================"
echo "Prompt Distillation Training with TRL"
echo "============================================"
echo "Model: $MODEL_NAME"
echo "Output: $OUTPUT_DIR"
echo "Train file: $TRAIN_FILE"
echo "============================================"
echo ""

# Check if training file exists
if [ ! -f "$TRAIN_FILE" ]; then
    echo "❌ Training file not found: $TRAIN_FILE"
    echo "Please run data generation first:"
    echo "  python create_data.py"
    exit 1
fi

# Run training with OpenAI-style hyperparameters
python train_sft_trl.py \
    --model_name "$MODEL_NAME" \
    --output_dir "$OUTPUT_DIR" \
    --train_file "$TRAIN_FILE" \
    --use_lora \
    --lora_rank 32 \
    --lora_alpha 16 \
    --num_train_epochs 1 \
    --per_device_train_batch_size 4 \
    --gradient_accumulation_steps 4 \
    --learning_rate 2e-4 \
    --max_length 2048 \
    --warmup_ratio 0.03 \
    --lr_scheduler_type cosine_with_min_lr

echo ""
echo "============================================"
echo "✅ Training Complete!"
echo "============================================"
echo "Model saved to: $OUTPUT_DIR"
