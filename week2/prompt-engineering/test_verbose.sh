#!/bin/bash

# Test script to demonstrate verbose output

echo "🔍 Testing verbose output for ablation study"
echo "=================================================="
echo ""
echo "This will run a single task with full verbose output"
echo "showing all assistant responses, tool calls, and user interactions"
echo ""

# Run with verbose output (default)
python run_ablation.py \
    --model openai/gpt-5 \
    --env airline \
    --tone-style trump \
    --ablation-name verbose_test \
    --start-index 0 \
    --end-index 1 \
    --max-concurrency 1

echo ""
echo "=================================================="
echo "To run WITHOUT verbose output, add --no-verbose flag:"
echo "python run_ablation.py ... --no-verbose"
