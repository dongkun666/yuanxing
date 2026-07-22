#!/bin/bash
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$PROJECT_ROOT"

PORT=${PORT:-8080}
HOST=${HOST:-0.0.0.0}

if command -v http-server &> /dev/null; then
    echo "Starting frontend with http-server..."
    exec http-server "$PROJECT_ROOT" \
        -p "$PORT" \
        -a "$HOST" \
        -c-1 \
        -g \
        -m application/javascript,.js \
        -m text/css,.css \
        -m text/html,.html \
        -m application/json,.json \
        -m image/png,.png \
        -m image/jpeg,.jpg,.jpeg \
        -m image/svg+xml,.svg \
        -m application/manifest+json,.webmanifest

elif command -v python3 &> /dev/null; then
    echo "Starting frontend with Python http.server..."
    exec python3 -m http.server "$PORT" --bind "$HOST"

elif command -v python &> /dev/null; then
    echo "Starting frontend with Python http.server..."
    exec python -m http.server "$PORT" --bind "$HOST"

else
    echo "Error: No http-server or Python available."
    exit 1
fi