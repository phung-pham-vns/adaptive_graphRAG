#!/bin/bash

# Quick evaluation script for Durian Pest and Disease RAG system
# This script provides shortcuts for common evaluation tasks

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

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

# Function to show help
show_help() {
    cat << EOF
${GREEN}Durian Pest and Disease RAG Evaluation Script${NC}

Usage: ./scripts/evaluate.sh [COMMAND] [OPTIONS]

${BLUE}Commands:${NC}

  ${YELLOW}ingest${NC}               Upload dataset to LangSmith
  ${YELLOW}eval${NC}                 Run evaluation
  ${YELLOW}quick${NC}                Quick test evaluation (fast)
  ${YELLOW}full${NC}                 Full evaluation (all samples, balanced config)
  ${YELLOW}accuracy${NC}             Accuracy-focused evaluation (thorough)
  ${YELLOW}compare${NC}              Show configuration comparison
  ${YELLOW}list${NC}                 List available configurations
  ${YELLOW}help${NC}                 Show this help message

${BLUE}Ingest Options:${NC}
  ./scripts/evaluate.sh ingest [--num-samples N] [--type TYPE] [--batch BATCH]

  Examples:
    ./scripts/evaluate.sh ingest                       # Upload all samples
    ./scripts/evaluate.sh ingest --num-samples 50      # Upload first 50 samples
    ./scripts/evaluate.sh ingest --type multi-hop      # Upload only multi-hop questions

${BLUE}Evaluation Options:${NC}
  ./scripts/evaluate.sh eval [--config CONFIG] [--dataset-name NAME]

  Examples:
    ./scripts/evaluate.sh eval                         # Run with balanced config
    ./scripts/evaluate.sh eval --config quick          # Run with quick config
    ./scripts/evaluate.sh eval --config accuracy       # Run with accuracy config

${BLUE}Quick Commands:${NC}
  ./scripts/evaluate.sh quick      # Equivalent to: eval --config quick
  ./scripts/evaluate.sh full       # Equivalent to: eval --config balanced
  ./scripts/evaluate.sh accuracy   # Equivalent to: eval --config accuracy

${BLUE}Available Configurations:${NC}
  - quick          : Quick test (speed-focused)
  - balanced       : Balanced performance (default)
  - accuracy       : Accuracy-focused (thorough)
  - minimal        : Minimal retrieval test
  - no-checks      : No quality checks (baseline)
  - graph-only     : Knowledge graph only
  - web-fallback   : Heavy web search

EOF
}

# Function to check environment
check_env() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        print_info "Please create a .env file with required API keys."
        exit 1
    fi
    
    # Check if LANGSMITH_API_KEY is set
    if ! grep -q "LANGSMITH_API_KEY" .env; then
        print_warning "LANGSMITH_API_KEY not found in .env file"
    fi
    
    # Check if llm_api_key is set
    if ! grep -q "llm_api_key" .env; then
        print_warning "llm_api_key (Gemini) not found in .env file"
    fi
}

# Main script
main() {
    case "${1:-help}" in
        ingest)
            print_info "Starting data ingestion..."
            check_env
            shift
            python -m src.evaluation.ingest_langsmith_new "$@"
            print_success "Data ingestion complete!"
            ;;
            
        eval)
            print_info "Starting evaluation..."
            check_env
            shift
            python -m src.evaluation.evaluate_langsmith_new "$@"
            print_success "Evaluation complete!"
            ;;
            
        quick)
            print_info "Running quick test evaluation..."
            check_env
            python -m src.evaluation.evaluate_langsmith_new --preset quick
            print_success "Quick evaluation complete!"
            ;;
            
        full)
            print_info "Running full evaluation with balanced configuration..."
            check_env
            python -m src.evaluation.evaluate_langsmith_new --preset balanced
            print_success "Full evaluation complete!"
            ;;
            
        accuracy)
            print_info "Running accuracy-focused evaluation..."
            check_env
            python -m src.evaluation.evaluate_langsmith_new --preset accuracy
            print_success "Accuracy evaluation complete!"
            ;;
            
        compare)
            print_info "Showing configuration comparison..."
            python -m src.evaluation.evaluate_langsmith_new --help
            ;;
            
        list)
            print_info "Available configurations (presets):"
            echo "  - quick          : Quick test (speed-focused)"
            echo "  - balanced       : Balanced performance (default)"
            echo "  - accuracy       : Accuracy-focused (thorough)"
            echo "  - minimal        : Minimal retrieval test"
            echo "  - no_checks      : No quality checks (baseline)"
            echo "  - graph_only     : Knowledge graph only"
            echo "  - web_fallback   : Heavy web search"
            ;;
            
        help|--help|-h)
            show_help
            ;;
            
        *)
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"




