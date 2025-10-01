#!/usr/bin/env bash
set -euo pipefail

# Simple runner for src.core.workflow
# Usage examples:
#   scripts/workflow.sh -q "What are common durian diseases?"
#   scripts/workflow.sh -q "Explain pest control" --no-hallucination-check

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

# Load environment variables from .env if present
if [ -f "$REPO_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$REPO_ROOT/.env"
  set +a
fi

cd "$REPO_ROOT"

exec "$PYTHON_BIN" -m src.core.workflow "$@"


