#!/bin/bash

# Full Ablation Study Script for Prompt Engineering
# This script runs all ablation experiments systematically

set -e  # Exit on error

# Configuration
MODEL="${MODEL:-openai/gpt-5}"
# Provider will be auto-detected based on model (openrouter for openai/gpt-5)
ENV="${ENV:-airline}"
NUM_TASKS="${NUM_TASKS:-10}"  # Number of tasks to run per experiment

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored headers
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to run an experiment
run_experiment() {
    local name=$1
    local args=$2
    
    echo -e "${YELLOW}Running: $name${NC}"
    echo "Arguments: $args"
    
    python run_ablation.py \
        --model $MODEL \
        --env $ENV \
        --start-index 0 \
        --end-index $NUM_TASKS \
        --ablation-name "$name" \
        $args
    
    echo -e "${GREEN}✓ Completed: $name${NC}\n"
}

# Main execution
main() {
    print_header "PROMPT ENGINEERING ABLATION STUDY"
    
    echo "Configuration:"
    echo "  Model: $MODEL"
    echo "  Provider: Auto-detected (OpenRouter for openai/gpt-5)"
    echo "  Environment: $ENV"
    echo "  Tasks per experiment: $NUM_TASKS"
    echo ""
    
    # Create results directory
    mkdir -p results_ablation
    
    # Track start time
    START_TIME=$(date +%s)
    
    print_header "1. BASELINE EXPERIMENT"
    run_experiment "baseline" ""
    
    print_header "2. TONE STYLE ABLATIONS"
    run_experiment "tone_trump" "--tone-style trump"
    run_experiment "tone_casual" "--tone-style casual"
    
    print_header "3. WIKI ORGANIZATION ABLATION"
    run_experiment "wiki_random" "--randomize-wiki"
    
    print_header "4. TOOL DESCRIPTION ABLATION"
    run_experiment "no_tool_desc" "--remove-tool-descriptions"
    
    print_header "5. COMBINED ABLATIONS"
    run_experiment "casual_wiki" "--tone-style casual --randomize-wiki"
    run_experiment "casual_no_tools" "--tone-style casual --remove-tool-descriptions"
    run_experiment "wiki_no_tools" "--randomize-wiki --remove-tool-descriptions"
    run_experiment "all_ablations" "--tone-style casual --randomize-wiki --remove-tool-descriptions"
    
    # Calculate elapsed time
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    MINUTES=$((ELAPSED / 60))
    SECONDS=$((ELAPSED % 60))
    
    print_header "EXPERIMENT COMPLETE"
    echo -e "${GREEN}All experiments completed successfully!${NC}"
    echo "Total time: ${MINUTES}m ${SECONDS}s"
    echo ""
    
    # Generate summary
    print_header "GENERATING SUMMARY"
    python analyze_results.py
}

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check Python
    if ! command -v python &> /dev/null; then
        echo -e "${RED}Error: Python not found${NC}"
        exit 1
    fi
    
    # Check required files
    for file in run_ablation.py ablation_utils.py ablation_agent.py; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}Error: Required file $file not found${NC}"
            echo "Please run this script from the prompt-engineering directory"
            exit 1
        fi
    done
    
    # Check API key based on model
    if [[ "$MODEL" == "openai/gpt-5" ]]; then
        if [ -z "$OPENROUTER_API_KEY" ]; then
            echo -e "${YELLOW}Warning: OPENROUTER_API_KEY not set for openai/gpt-5${NC}"
            echo "Please set: export OPENROUTER_API_KEY='your-key'"
            read -p "Continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    elif [ -z "$OPENAI_API_KEY" ]; then
        echo -e "${YELLOW}Warning: OPENAI_API_KEY not set${NC}"
        echo "Please set: export OPENAI_API_KEY='your-key'"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✓ Prerequisites check passed${NC}\n"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --provider)
            echo "Note: Provider is now auto-detected based on model"
            echo "      (OpenRouter for openai/gpt-5, OpenAI for others)"
            shift 2
            ;;
        --env)
            ENV="$2"
            shift 2
            ;;
        --num-tasks)
            NUM_TASKS="$2"
            shift 2
            ;;
        --quick)
            NUM_TASKS=3
            echo "Quick mode: Running only 3 tasks per experiment"
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --model MODEL        Model to use (default: openai/gpt-5)"
            echo "  --provider           (Deprecated - auto-detected based on model)"
            echo "  --env ENV           Environment to use (default: airline)"
            echo "  --num-tasks N       Number of tasks per experiment (default: 10)"
            echo "  --quick             Quick mode with 3 tasks per experiment"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run the main process
check_prerequisites
main
