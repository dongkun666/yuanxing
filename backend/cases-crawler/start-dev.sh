#!/bin/bash
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

export APP_ENV=development

if [ -f ".env" ]; then
    echo "Loading .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "Warning: No .env file found. Using default settings."
fi

mkdir -p data logs

echo "Running database migrations..."
if command -v alembic &> /dev/null; then
    alembic upgrade head
else
    echo "alembic not found, trying python -m alembic..."
    python -m alembic upgrade head
fi

echo "Starting LexPrime API in development mode (hot reload enabled)..."
exec uvicorn api.main:app \
    --host "${API_HOST:-0.0.0.0}" \
    --port "${API_PORT:-8000}" \
    --reload \
    --log-level "${LOG_LEVEL:-debug}"