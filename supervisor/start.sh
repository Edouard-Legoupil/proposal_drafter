#!/bin/bash
set -e

PORT=${PORT:-8080}

echo "============================================"
echo "🚀 Starting Proposal Generator on port $PORT"
echo "============================================"

# Log directory inside container
LOG_DIR="/app/log"
mkdir -p "$LOG_DIR"

# Use Gunicorn with UvicornWorker (production safe)
exec /venv/bin/gunicorn \
    backend.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --log-level info \
    --access-logfile "$LOG_DIR/access.log" \
    --error-logfile "$LOG_DIR/error.log"