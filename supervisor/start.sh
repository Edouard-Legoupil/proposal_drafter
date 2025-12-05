#!/bin/bash
set -e
set -o pipefail

echo "============================================================"
echo "🚀 Starting Proposal Generator on Azure WebApp (FULL DEBUG)"
echo "============================================================"
echo ""

# -------------------------
# System Info
# -------------------------
echo "🔧 System Information"
echo "--------------------------------------------"
date
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -r)"
echo ""
echo "💽 Disk Usage:"
df -h
echo ""
echo "💾 Memory:"
free -h
echo ""


# -------------------------
# Environment Variables
# -------------------------
echo "🔍 Environment Variables (filtered)"
echo "--------------------------------------------"
env | sort
echo ""

# -------------------------
# Python Info
# -------------------------
echo "🐍 Python & Dependencies"
echo "--------------------------------------------"
python --version
echo "PYTHONPATH=$PYTHONPATH"
echo ""
echo "📚 Installed Packages:"
pip list --format=columns
echo ""

# -------------------------
# Filesystem check
# -------------------------
echo "🗂 Filesystem checks"
echo "--------------------------------------------"
echo "📁 Backend directory:"
ls -l /app/backend
echo ""
echo "📁 Frontend build:"
ls -l /app/frontend/dist
echo ""
echo "📁 Knowledge directory:"
ls -l /app/knowledge
echo ""

# -------------------------
# Environment Variables for Azure
# -------------------------
# Set Azure-specific environment variables
export WEBSITES_PORT=${PORT}
export WEBSITES_CONTAINER_START_TIME_LIMIT=1800  # 30 minutes startup time
export PYTHONUNBUFFERED=1  # Ensure logs are streamed immediately

echo "📋 Azure Environment Variables:"
echo "WEBSITES_CONTAINER_START_TIME_LIMIT=${WEBSITES_CONTAINER_START_TIME_LIMIT}"
echo ""

# Create a simple health check file for Azure (optional)
echo "Creating health check file..."
echo "healthy" > /tmp/healthz

echo "============================================================"
echo "Port Management"
echo "============================================================"
# Use WEBSITES_PORT if defined (Azure), otherwise default to 8080
# Azure injects WEBSITES_PORT or uses PORT
PORT=${WEBSITES_PORT:-${PORT:-8080}}
echo "Azure expects app on port: ${PORT}"
echo "WEBSITES_PORT=${WEBSITES_PORT}"
echo "Using PORT=${PORT}"
echo ""

echo "============================================================"
echo "🔥 Starting Gunicorn on port ${PORT} (Azure STDOUT/STDERR logging enabled)"
echo "============================================================"

# On App Service, WEBSITES_PORT (set in App Settings) tells the platform to route to this same port.
exec gunicorn backend.main:app \
  --bind 0.0.0.0:${PORT} \
  --workers ${WEB_CONCURRENCY:-2} \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 1200 \
  --keep-alive 120 \
  --access-logfile - \
  --error-logfile - \
  --log-level debug \
  --preload
