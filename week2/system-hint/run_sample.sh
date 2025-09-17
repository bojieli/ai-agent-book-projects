#!/bin/bash

# Sample script to demonstrate System-Hint Agent usage
# This script runs the sample task that analyzes week1 and week2 projects

echo "================================"
echo "System-Hint Agent Sample Task"
echo "================================"
echo ""
echo "This will analyze and summarize the AI Agent projects"
echo "in week1 and week2 directories using the System-Hint Agent."
echo ""

# Check if KIMI_API_KEY is set
if [ -z "$KIMI_API_KEY" ]; then
    echo "❌ Error: KIMI_API_KEY environment variable is not set"
    echo ""
    echo "Please set it using:"
    echo "  export KIMI_API_KEY='your-api-key-here'"
    echo ""
    exit 1
fi

echo "✅ KIMI_API_KEY is configured"
echo ""
echo "Starting analysis..."
echo "----------------------------------------"

# Run the sample task
python main.py --mode sample

echo ""
echo "Sample task completed!"
echo ""
echo "You can also try:"
echo "  - Interactive mode: python main.py"
echo "  - Custom task: python main.py --mode single --task 'Your task here'"
echo "  - Demos: python main.py --mode demo"
echo ""
