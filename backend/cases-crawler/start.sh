#!/bin/bash
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

APP_ENV=${APP_ENV:-production}

if [ -f ".env" ]; then
    echo "Loading .env file..."
    export $(grep -v '^#' .env | xargs)
elif [ -f ".env.production" ]; then
    echo "Loading .env.production file..."
    export $(grep -v '^#' .env.production | xargs)
else
    echo "Warning: No .env file found. Using default settings."
fi

export APP_ENV=$APP_ENV

mkdir -p data logs

echo "Running database migrations..."
if command -v alembic &> /dev/null; then
    alembic upgrade head
else
    echo "alembic not found, trying python -m alembic..."
    python -m alembic upgrade head
fi

echo "Starting LexPrime API in $APP_ENV mode..."
exec uvicorn api.main:app \
    --host "${API_HOST:-0.0.0.0}" \
    --port "${API_PORT:-8000}" \
    --workers 4 \
    --log-level "${LOG_LEVEL:-info}"