#!/bin/bash

# Quick test with a single task for debugging
# This helps identify issues without waiting for multiple tasks

echo "🔍 Testing single task with full debugging"
echo "=================================================="

# Enable all debugging
export LITELLM_LOG="DEBUG"
export DEBUG_API_CALLS="true"
export LITELLM_PRINT_VERBOSE="true"

# Run just 1 task
python run_ablation.py \
    --model openai/gpt-5 \
    --env airline \
    --tone-style trump \
    --ablation-name debug_test \
    --start-index 0 \
    --end-index 1 \
    --max-concurrency 1
