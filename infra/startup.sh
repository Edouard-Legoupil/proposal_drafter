#!/bin/bash
set -euo pipefail

echo "============================================================"
echo "🚀 Starting Proposal Generator - App Service Optimized"
echo "============================================================"

# -------------------------
# NLTK Data Setup
# -------------------------
export NLTK_DATA="/home/site/wwwroot/nltk_data"
mkdir -p "$NLTK_DATA"

echo "📥 Checking NLTK data..."
python - <<'PY'
import nltk, os
path = os.getenv("NLTK_DATA", "/home/site/wwwroot/nltk_data")
nltk.data.path.append(path)
try:
    nltk.download("punkt", download_dir=path)
    nltk.download("punkt_tab", download_dir=path)
    print("✅ NLTK data ready")
except Exception as e:
    print("⚠️ NLTK download failed:", e)
PY

# -------------------------
# Port Configuration
# -------------------------
# Azure App Service usually sets PORT or uses 80/8080
BIND_PORT="${PORT:-8000}"
echo "🎯 Binding to port: ${BIND_PORT}"

# -------------------------
# START SERVER
# -------------------------
echo "🚀 Launching Gunicorn"

# We use 'backend.main:app' assuming the zip deployment preserves the 'backend' folder
# in the root of the deployment (/home/site/wwwroot/backend)
# and we set PYTHONPATH to /home/site/wwwroot

exec gunicorn backend.main:app \
    --bind "0.0.0.0:${BIND_PORT}" \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 600 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
