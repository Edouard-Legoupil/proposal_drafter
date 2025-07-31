#!/bin/sh
# start.sh

# Use Cloud Run PORT env var, default to 8502 if not set
PORT="${PORT:-8502}"


set -e

echo "📦 Python path: $(which python)"
echo "🚀 Starting FastAPI on port ${PORT:-8080}"

/venv/bin/uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} &

# Wait a bit to ensure FastAPI is started before nginx
sleep 1

echo "🌐 Starting Nginx"
/usr/sbin/nginx -g "daemon off;"


echo "🚀 Starting FastAPI on port $PORT"