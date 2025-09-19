#!/bin/bash

# Debug script for running ablation with detailed API logging

echo "🔍 Running ablation study with API debugging enabled"
echo "=================================================="

# Enable litellm debugging
export LITELLM_LOG="DEBUG"
export DEBUG_API_CALLS="true"

# Also enable curl command logging to see exact requests
export LITELLM_PRINT_VERBOSE="true"

echo "✅ Debug settings enabled:"
echo "  - LITELLM_LOG=DEBUG"
echo "  - DEBUG_API_CALLS=true"
echo "  - LITELLM_PRINT_VERBOSE=true"
echo ""

# Run the ablation with all provided arguments
python run_ablation.py "$@"
