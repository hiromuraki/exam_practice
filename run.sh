#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

export DATA_DIR="./data"
echo "📚 Reading questions from: $DATA_DIR"
echo "🚀 Starting on http://0.0.0.0:8000"
exec uv run uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
