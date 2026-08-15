#!/bin/bash

# GAIA Experience Learning System Runner
# This script provides convenient commands for running the system

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
START_IDX=0
END_IDX=10
SPLIT="validation"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed"
        exit 1
    fi
    
    # Check .env file
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        cat > .env << EOF
# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL_NAME=gpt-5.6-luna
LLM_API_KEY=your_api_key_here
# LLM_BASE_URL=https://api.openai.com/v1

# Dataset paths
GAIA_DATASET_PATH=./AWorld/examples/gaia/GAIA
AWORLD_WORKSPACE=./workspace
EOF
        print_warning "Please edit .env file with your API keys"
        exit 1
    fi
    
    print_success "Prerequisites checked"
}

# Function to setup environment
setup_environment() {
    print_info "Setting up environment..."
    
    # Create necessary directories
    mkdir -p kb_index
    mkdir -p experiences
    mkdir -p logs
    mkdir -p workspace
    
    # Check if AWorld is installed
    if [ ! -d "AWorld" ]; then
        print_error "AWorld directory not found. Please ensure AWorld is cloned in this directory."
        exit 1
    fi
    
    print_success "Environment setup complete"
}

# Function to show help
show_help() {
    cat << EOF

GAIA Experience Learning System Runner
=======================================

Usage: ./run.sh [COMMAND] [OPTIONS]

Commands:
  demo             Run the interactive demo
  learn            Run in learning mode (capture experiences)
  apply            Run with experience application
  full             Run with both learning and application
  compare          A/B compare baseline vs. experience reuse on the same tasks
  index            Index the validation dataset
  test             Run a specific test case
  help             Show this help message

Options:
  --start N        Start index (default: 0)
  --end N          End index (default: 10)
  --split TYPE     Dataset split: validation/test (default: validation)
  --task-id ID     Specific task ID to run
  --model NAME     Main agent model (overrides LLM_MODEL_NAME)
  --output PATH    Results JSON output path
  --no-preload     Don't preload knowledge base

Examples:
  ./run.sh demo                       # Run interactive demo
  ./run.sh learn --start 0 --end 5    # Learn from first 5 questions
  ./run.sh apply --start 5 --end 10   # Apply experiences to questions 5-10
  ./run.sh full                       # Run complete workflow
  ./run.sh compare --start 10 --end 20  # A/B: baseline vs. experience reuse
  ./run.sh test --task-id "task-123"  # Run specific task

Note: For a fair 'compare', first accumulate experiences on OTHER tasks, e.g.
  ./run.sh learn --start 0 --end 10
  ./run.sh compare --start 10 --end 20

EOF
}

# Parse command
COMMAND=${1:-help}
shift || true

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --start)
            START_IDX="$2"
            shift 2
            ;;
        --end)
            END_IDX="$2"
            shift 2
            ;;
        --split)
            SPLIT="$2"
            shift 2
            ;;
        --task-id)
            TASK_ID="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        --no-preload)
            NO_PRELOAD=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Compose optional pass-through args (model / output)
EXTRA_ARGS=""
if [ -n "$MODEL" ]; then
    EXTRA_ARGS="$EXTRA_ARGS --model $MODEL"
fi
if [ -n "$OUTPUT" ]; then
    EXTRA_ARGS="$EXTRA_ARGS --output $OUTPUT"
fi

# Execute command
case $COMMAND in
    demo)
        print_info "Running interactive demo..."
        check_prerequisites
        setup_environment
        python demo.py --interactive
        ;;
        
    learn)
        print_info "Running in learning mode..."
        print_info "Processing questions $START_IDX to $END_IDX from $SPLIT split"
        check_prerequisites
        setup_environment
        
        python run_with_experience.py \
            --learning-mode \
            --start "$START_IDX" \
            --end "$END_IDX" \
            --split "$SPLIT" \
            $EXTRA_ARGS
        ;;

    apply)
        print_info "Running with experience application..."
        print_info "Processing questions $START_IDX to $END_IDX from $SPLIT split"
        check_prerequisites
        setup_environment
        
        PRELOAD_FLAG=""
        if [ "$NO_PRELOAD" != true ]; then
            PRELOAD_FLAG="--preload-kb"
        fi
        
        python run_with_experience.py \
            --apply-experience \
            $PRELOAD_FLAG \
            --start "$START_IDX" \
            --end "$END_IDX" \
            --split "$SPLIT" \
            $EXTRA_ARGS
        ;;

    full)
        print_info "Running with full experience learning..."
        print_info "Processing questions $START_IDX to $END_IDX from $SPLIT split"
        check_prerequisites
        setup_environment
        
        PRELOAD_FLAG=""
        if [ "$NO_PRELOAD" != true ]; then
            PRELOAD_FLAG="--preload-kb"
        fi
        
        python run_with_experience.py \
            --learning-mode \
            --apply-experience \
            $PRELOAD_FLAG \
            --start "$START_IDX" \
            --end "$END_IDX" \
            --split "$SPLIT" \
            $EXTRA_ARGS
        ;;

    compare)
        print_info "Running A/B comparison (baseline vs. experience reuse)..."
        print_info "Evaluating questions $START_IDX to $END_IDX from $SPLIT split twice"
        check_prerequisites
        setup_environment

        PRELOAD_FLAG=""
        if [ "$NO_PRELOAD" == true ]; then
            PRELOAD_FLAG=""
        fi

        python run_with_experience.py \
            --compare \
            $PRELOAD_FLAG \
            --start "$START_IDX" \
            --end "$END_IDX" \
            --split "$SPLIT" \
            $EXTRA_ARGS
        ;;

    index)
        print_info "Indexing validation dataset..."
        check_prerequisites
        setup_environment
        
        python -c "
import asyncio
from knowledge_base import KnowledgeBase

async def index():
    kb = KnowledgeBase()
    kb.index_gaia_validation('gaia-validation.jsonl')
    stats = kb.get_statistics()
    print(f'Indexed {stats[\"total_documents\"]} documents')

asyncio.run(index())
"
        print_success "Indexing complete"
        ;;
        
    test)
        if [ -z "$TASK_ID" ]; then
            print_error "Task ID required. Use --task-id option"
            exit 1
        fi
        
        print_info "Running test for task: $TASK_ID"
        check_prerequisites
        setup_environment
        
        python run_with_experience.py \
            --learning-mode \
            --apply-experience \
            --preload-kb \
            --q "$TASK_ID"
        ;;
        
    help|--help|-h)
        show_help
        ;;
        
    *)
        print_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac

print_success "Done!"
