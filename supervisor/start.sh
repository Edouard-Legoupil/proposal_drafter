#!/bin/bash
set -euo pipefail

echo "============================================================"
echo "🚀 Starting Proposal Generator - Azure Optimized"
echo "============================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# -------------------------
# Minimal System Info
# -------------------------
echo "🔧 System Information"
echo "--------------------------------------------"
echo "Hostname: $(hostname)"
echo "CPU Cores: $(nproc 2>/dev/null || echo 'unknown')"
echo "Memory: $(free -m 2>/dev/null | awk '/^Mem:/{print $2"MB"}')"
echo ""

# -------------------------
# Azure Environment Detection
# -------------------------
echo "☁️ Azure Environment"
echo "--------------------------------------------"

# Check if we're in Azure App Service
IS_AZURE=false
if [ -n "${APPSETTING_WEBSITE_SITE_NAME:-}" ] || [ -n "${WEBSITE_SITE_NAME:-}" ]; then
    IS_AZURE=true
    echo "✅ Azure App Service Detected"
    echo "   Site: ${APPSETTING_WEBSITE_SITE_NAME:-${WEBSITE_SITE_NAME:-unknown}}"
    echo "   Slot: ${WEBSITE_SLOT_NAME:-production}"
else
    echo "ℹ️ Local/Non-Azure Environment"
fi
echo ""

# -------------------------
# Port Configuration - SIMPLIFIED
# -------------------------
echo "🎯 Port Configuration"
echo "--------------------------------------------"

# Azure App Service: WEBSITES_PORT is set by platform
# Local/Other: Use PORT or default to 8080
# IMPORTANT: Container must bind to this exact port

if [ -n "${WEBSITES_PORT:-}" ]; then
    # Azure explicitly tells us which port to use
    BIND_PORT="${WEBSITES_PORT}"
    echo "🔵 Using WEBSITES_PORT from Azure: ${BIND_PORT}"
    echo "   Note: Azure routes traffic to this port"
elif [ -n "${PORT:-}" ]; then
    # Use PORT if set (common in local/dev)
    BIND_PORT="${PORT}"
    echo "🟡 Using PORT: ${BIND_PORT}"
else
    # Default fallback
    BIND_PORT="8080"
    echo "🟢 Using default: ${BIND_PORT}"
    
    if [ "$IS_AZURE" = true ]; then
        echo "   ⚠️  For Azure, set WEBSITES_PORT=8080 in Application Settings"
    fi
fi

# Validate port
if ! [[ "${BIND_PORT}" =~ ^[0-9]+$ ]] || [ "${BIND_PORT}" -lt 1 ] || [ "${BIND_PORT}" -gt 65535 ]; then
    echo "❌ ERROR: Invalid port: ${BIND_PORT}"
    exit 1
fi

echo ""
echo "✅ Final binding: 0.0.0.0:${BIND_PORT}"
echo ""

# -------------------------
# Python Configuration
# -------------------------
echo "🐍 Python Setup"
echo "--------------------------------------------"

# Check Python availability
if ! python --version >/dev/null 2>&1; then
    echo "❌ ERROR: Python not found or not in PATH"
    exit 1
fi

echo "Python: $(python --version 2>&1)"
echo ""

# Critical environment variables for Azure
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# -------------------------
# Quick App Verification
# -------------------------
echo "🔍 App Verification"
echo "--------------------------------------------"

# Check for minimal required files
REQUIRED_FILES=(
    "/app/backend/main.py"
    "/app/backend/__init__.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ ERROR: Missing required file: $file"
        echo "Directory listing:"
        ls -la /app/backend/ 2>/dev/null || echo "Cannot list /app/backend"
        exit 1
    fi
done

echo "✅ Required files present"

# Quick import test (no heavy validation)
echo -n "Testing app import: "
if python -c "from backend.main import app; print('✅ backend.main:app imported')" 2>/dev/null; then
    echo ""
else
    echo "❌ FAILED"
    echo "App import failed. Checking Python path..."
    python -c "import sys; print('Python path:', sys.path)"
    echo ""
    echo "Trying with traceback:"
    python -c "import traceback; try: from backend.main import app; print('SUCCESS') except: traceback.print_exc()" 2>&1
    exit 1
fi

# -------------------------
# Gunicorn Configuration
# -------------------------
echo "⚙️ Server Configuration"
echo "--------------------------------------------"

# Worker count - keep it simple
if [ -z "${WEB_CONCURRENCY:-}" ]; then
    # Default to 2 workers for Azure App Service (conservative)
    WEB_CONCURRENCY=2
    echo "Using default workers: ${WEB_CONCURRENCY}"
else
    echo "Using WEB_CONCURRENCY: ${WEB_CONCURRENCY}"
fi

# Important: For Azure, workers should be reasonable (2-4)
if [ "$WEB_CONCURRENCY" -gt 4 ]; then
    echo "⚠️  High worker count for Azure: ${WEB_CONCURRENCY}"
    echo "   Consider reducing to 2-4 workers"
fi

echo ""

# -------------------------
# Health Check Info
# -------------------------
echo "🏥 Health Checks"
echo "--------------------------------------------"
echo "Azure will probe: http://<container>:${BIND_PORT}/"
echo "Ensure GET / returns HTTP 200"
echo ""

# -------------------------
# START SERVER
# -------------------------
echo "============================================================"
echo "🚀 Launching Server"
echo "============================================================"
echo ""

echo "Command:"
echo "gunicorn backend.main:app \\"
echo "  --bind 0.0.0.0:${BIND_PORT} \\"
echo "  --workers ${WEB_CONCURRENCY} \\"
echo "  --worker-class uvicorn.workers.UvicornWorker \\"
echo "  --timeout 300 \\"  # Reduced from 1200 to 300 seconds (5 min)
echo "  --keep-alive 60 \\"  # Reduced from 120 to 60 seconds
echo "  --access-logfile - \\"
echo "  --error-logfile - \\"
echo "  --log-level info \\"  # Changed from debug to info (less verbose)
echo "  --preload"
echo ""
echo "Starting now..."
echo ""

# IMPORTANT: Remove the sleep and netstat checks that might cause delays
# Azure has a startup timeout (default 230s), we need to start quickly

# Launch Gunicorn with exec (replaces shell process)
exec gunicorn backend.main:app \
    --bind "0.0.0.0:${BIND_PORT}" \
    --workers "${WEB_CONCURRENCY}" \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 300 \
    --keep-alive 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload