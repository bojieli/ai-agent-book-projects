#!/bin/bash
# Parallel data generation script for H100x8 GPU setup
# This uses ALL 8 GPUs by running 2 instances in parallel

set -e

echo "=========================================="
echo "Parallel Data Generation for H100x8"
echo "=========================================="
echo ""

# Configuration
INPUT_FILE=${1:-"./example-data/multilingual.txt"}
OUTPUT_FILE=${2:-"./data/prompt_distillation_lang.jsonl"}
MODEL_NAME="Qwen/Qwen3-30B-A3B-Thinking-2507"

echo "Configuration:"
echo "  Input file: $INPUT_FILE"
echo "  Output file: $OUTPUT_FILE"
echo "  Model: $MODEL_NAME"
echo "  Strategy: 2 parallel instances, each using TP=4"
echo ""

if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ Input file not found: $INPUT_FILE"
    exit 1
fi

# Check if output file exists
if [ -f "$OUTPUT_FILE" ]; then
    echo "⚠️  Output file already exists: $OUTPUT_FILE"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    rm "$OUTPUT_FILE"
fi

# Create temp directory for split files
TEMP_DIR="./data/temp_$$"
mkdir -p "$TEMP_DIR"

echo "Splitting dataset into 2 parts..."
TOTAL_LINES=$(wc -l < "$INPUT_FILE")
HALF_LINES=$((TOTAL_LINES / 2))

head -n $HALF_LINES "$INPUT_FILE" > "$TEMP_DIR/part1.txt"
tail -n +$((HALF_LINES + 1)) "$INPUT_FILE" > "$TEMP_DIR/part2.txt"

PART1_LINES=$(wc -l < "$TEMP_DIR/part1.txt")
PART2_LINES=$(wc -l < "$TEMP_DIR/part2.txt")

echo "  Part 1: $PART1_LINES lines (GPU 0-3)"
echo "  Part 2: $PART2_LINES lines (GPU 4-7)"
echo ""

# Setup signal handler to kill both processes on Ctrl+C
cleanup() {
    echo ""
    echo "🛑 Caught interrupt signal (Ctrl+C)"
    echo "Killing both processes..."
    if [ ! -z "$PID1" ] && kill -0 $PID1 2>/dev/null; then
        echo "  Killing Instance 1 (PID $PID1)..."
        kill -TERM $PID1 2>/dev/null || true
    fi
    if [ ! -z "$PID2" ] && kill -0 $PID2 2>/dev/null; then
        echo "  Killing Instance 2 (PID $PID2)..."
        kill -TERM $PID2 2>/dev/null || true
    fi
    # Wait a moment for graceful shutdown
    sleep 2
    # Force kill if still running
    if [ ! -z "$PID1" ] && kill -0 $PID1 2>/dev/null; then
        echo "  Force killing Instance 1..."
        kill -9 $PID1 2>/dev/null || true
    fi
    if [ ! -z "$PID2" ] && kill -0 $PID2 2>/dev/null; then
        echo "  Force killing Instance 2..."
        kill -9 $PID2 2>/dev/null || true
    fi
    # Cleanup temp files
    echo "  Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
    echo "✅ Cleanup complete"
    exit 130
}

trap cleanup SIGINT SIGTERM

# Run both instances in parallel
echo "Starting parallel data generation..."
echo ""

# Instance 1: GPU 0-3
echo "Starting Instance 1 on GPUs 0-3..."
CUDA_VISIBLE_DEVICES=0,1,2,3 python create_data.py \
    --input_file "$TEMP_DIR/part1.txt" \
    --output_file "$TEMP_DIR/part1.jsonl" \
    --model_name "$MODEL_NAME" \
    --temperature 0.15 \
    --tensor_parallel_size 4 \
    --max_retries 3 \
    > "$TEMP_DIR/instance1.log" 2>&1 &
PID1=$!

echo "Instance 1 is running (PID: $PID1)"

# Instance 2: GPU 4-7
echo "Starting Instance 2 on GPUs 4-7..."
CUDA_VISIBLE_DEVICES=4,5,6,7 python create_data.py \
    --input_file "$TEMP_DIR/part2.txt" \
    --output_file "$TEMP_DIR/part2.jsonl" \
    --model_name "$MODEL_NAME" \
    --temperature 0.15 \
    --tensor_parallel_size 4 \
    --max_retries 3 \
    > "$TEMP_DIR/instance2.log" 2>&1 &
PID2=$!

echo "Instance 2 is running (PID: $PID2)"
echo ""
echo "Both instances are running. You can monitor GPU usage with:"
echo "  watch -n 1 nvidia-smi"
echo "Instance output is logged to:"
echo "  $TEMP_DIR/instance1.log"
echo "  $TEMP_DIR/instance2.log"
echo ""

# Wait for both to complete
echo "Waiting for both instances to complete..."
echo "  Instance 1 (PID $PID1): GPU 0-3"
echo "  Instance 2 (PID $PID2): GPU 4-7"
echo ""

# `|| STATUS=` keeps a non-zero child exit from killing the script under
# set -e — otherwise everything below (logs, combined check, cleanup)
# is unreachable and the sibling instance is orphaned.
STATUS1=0; wait $PID1 || STATUS1=$?
echo ""
echo "Instance 1 completed with status: $STATUS1"
if [ $STATUS1 -ne 0 ]; then
    echo "Instance 1 log:"
    cat "$TEMP_DIR/instance1.log" | tail -50
fi

STATUS2=0; wait $PID2 || STATUS2=$?
echo ""
echo "Instance 2 completed with status: $STATUS2"
if [ $STATUS2 -ne 0 ]; then
    echo "Instance 2 log:"
    cat "$TEMP_DIR/instance2.log" | tail -50
fi

echo ""

# Check if both succeeded
if [ $STATUS1 -ne 0 ] || [ $STATUS2 -ne 0 ]; then
    echo "❌ One or both instances failed!"
    echo "   Instance 1 status: $STATUS1"
    echo "   Instance 2 status: $STATUS2"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Combine results
echo "Combining results..."
cat "$TEMP_DIR/part1.jsonl" "$TEMP_DIR/part2.jsonl" > "$OUTPUT_FILE"

# Show statistics
PART1_COUNT=$(wc -l < "$TEMP_DIR/part1.jsonl")
PART2_COUNT=$(wc -l < "$TEMP_DIR/part2.jsonl")
TOTAL_COUNT=$((PART1_COUNT + PART2_COUNT))

echo ""
echo "=========================================="
echo "✅ Parallel data generation complete!"
echo "=========================================="
echo "Part 1: $PART1_COUNT / $PART1_LINES samples ($(awk "BEGIN {printf \"%.2f\", $PART1_COUNT/$PART1_LINES*100}")%)"
echo "Part 2: $PART2_COUNT / $PART2_LINES samples ($(awk "BEGIN {printf \"%.2f\", $PART2_COUNT/$PART2_LINES*100}")%)"
echo "Total:  $TOTAL_COUNT / $TOTAL_LINES samples ($(awk "BEGIN {printf \"%.2f\", $TOTAL_COUNT/$TOTAL_LINES*100}")%)"
echo ""
echo "Output: $OUTPUT_FILE"
echo ""

# Cleanup
rm -rf "$TEMP_DIR"

echo "All 8 GPUs were utilized! 🚀"

