#!/bin/bash
set -e
set -o pipefail

echo "============================================================"
echo "🚀 Starting Proposal Generator on Azure WebApp (FULL DEBUG)"
echo "============================================================"
echo "Using PORT=${PORT:-8080}"
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
echo "🌐 Network info skipped (ip/ss not installed in Azure container)"
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
# Gunicorn options
# -------------------------
GUNICORN_CMD="gunicorn \
    -c /app/backend/gunicorn.conf.py \
    backend.main:app \
    --bind 0.0.0.0:${PORT:-8080} \
    --access-logfile - \
    --error-logfile - \
    --log-level debug"

echo "============================================================"
echo "🔥 Starting Gunicorn (Azure STDOUT/STDERR logging enabled)"
echo "============================================================"
exec $GUNICORN_CMD