#!/bin/sh
# start.sh

set -e

echo "🔍 START.SH executing"
echo "📂 Current dir: $(pwd)"
echo "📦 Uvicorn path: $(which uvicorn || echo 'Not found')"
echo "🐍 Python version: $(python3 --version)"

echo "🚀 Starting FastAPI on port $PORT"
/venv/bin/uvicorn main:app --host 0.0.0.0 --port $PORT &

sleep 1
echo "🌐 Starting Nginx"
/usr/sbin/nginx -g "daemon off;"