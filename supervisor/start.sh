#!/bin/bash
set -e

echo "🚀 Starting container entrypoint..."
echo "📅 Container start time: $(date)"
echo "🔍 Process ID: $$"

# Ensure PORT is set
PORT=${PORT:-8080}
echo "🌐 Cloud Run will expect Nginx to listen on PORT=$PORT"

# Function to log diagnostic information
log_diagnostics() {
    echo "📊 ===== DIAGNOSTICS REPORT ($(date)) ====="
    echo "📋 Signal received: $1"
    
    # Process information
    echo "👥 Process tree:"
    ps auxf || echo "ps command failed"
    
    echo "📈 Memory usage:"
    free -m || echo "free command failed"
    
    echo "💾 Disk usage:"
    df -h || echo "df command failed"
    
    echo "📦 Container memory limits (cgroup):"
    if [ -f /sys/fs/cgroup/memory/memory.limit_in_bytes ]; then
        memory_limit=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes)
        echo "Memory limit: $((memory_limit / 1024 / 1024))MB"
    else
        echo "No cgroup memory limit found"
    fi
    
    echo "🔥 CPU usage (top 5 processes):"
    ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -6 || echo "ps sort failed"
    
    echo "🌐 Network connections:"
    netstat -tuln || echo "netstat command failed"
    
    echo "🔗 Nginx status:"
    if pgrep nginx > /dev/null; then
        echo "Nginx is running (PID: $(pgrep nginx))"
    else
        echo "Nginx is not running"
    fi
    
    echo "🐍 Python processes:"
    pgrep -af python || echo "No Python processes found"
    
    echo "📡 Active connections to Nginx:"
    if command -v ss &> /dev/null; then
        ss -t | grep :$PORT || echo "No active connections on port $PORT"
    else
        netstat -t | grep :$PORT || echo "No active connections on port $PORT"
    fi
    
    echo "🧪 Recent application errors:"
    tail -n 50 /app/log/*.log 2>/dev/null || echo "No log files found"
    
    echo "🔄 Recent system events:"
    dmesg | tail -n 20 2>/dev/null || echo "dmesg not available"
    
    echo "📝 Environment variables:"
    printenv | grep -E "(PORT|MEMORY|CPU|CLOUD_RUN|K_|GOOGLE)" || echo "No relevant env vars found"
    
    echo "⏰ Uptime: $(uptime)"
    echo "📊 ===== END DIAGNOSTICS ====="
}

# Replace $PORT placeholder in Nginx config
sed -i "s/\$PORT/$PORT/g" /etc/nginx/conf.d/default.conf
echo "✅ Updated Nginx config to listen on port $PORT"

# --- Preflight checks ---
echo "🔎 Preflight checks..."
python3 -c "import importlib; importlib.import_module('backend.main')" \
    && echo "✅ FastAPI module backend.main:app is importable" \
    || { echo "❌ ERROR: Cannot import backend.main"; exit 1; }

# Wait for Cloud SQL socket with timeout
if [ -n "$DB_HOST" ]; then
    echo "🗄️ Waiting for Cloud SQL socket at /cloudsql/$DB_HOST/.s.PGSQL.5432"
    timeout=15
    elapsed=0
    while [ ! -S "/cloudsql/$DB_HOST/.s.PGSQL.5432" ] && [ $elapsed -lt $timeout ]; do
        sleep 1
        elapsed=$((elapsed + 1))
        echo "⏳ Waiting for Cloud SQL socket... ($elapsed/$timeout seconds)"
    done
    
    if [ -S "/cloudsql/$DB_HOST/.s.PGSQL.5432" ]; then
        echo "✅ Cloud SQL socket is ready!"
    else
        echo "⚠️ Timeout: Cloud SQL socket not available after $timeout seconds"
    fi
else
    echo "ℹ️ No DB_HOST specified, skipping Cloud SQL wait"
fi

# Start Nginx and FastAPI directly
echo "🚀 Starting Nginx and FastAPI..."


# --- Start FastAPI with enhanced logging ---
echo "🐍 Starting FastAPI (logging to /app/log/uvicorn_startup.log)..."
/venv/bin/uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8502 \
    --log-level debug \
    > /app/log/uvicorn_startup.log 2>&1 &
UVICORN_PID=$!

# Wait a few seconds to confirm FastAPI starts
sleep 5

echo "🔎 Verifying FastAPI port..."
ss -ltnp
tail -n 50 /app/log/uvicorn_startup.log


if ! kill -0 $UVICORN_PID 2>/dev/null; then
    echo "❌ FastAPI failed to start! Dumping logs:"
    cat /app/log/uvicorn_startup.log
    exit 1
else
    echo "✅ FastAPI process started (PID: $UVICORN_PID)"
fi

# --- Immediate health check ---
echo "🧪 Checking FastAPI health endpoint..."
if curl --silent --fail http://127.0.0.1:8502/api/health; then
    echo "✅ FastAPI health check passed"
else
    echo "⚠️ FastAPI health check failed (but process is running)"
    echo "----- Startup logs -----"
    tail -n 50 /app/log/uvicorn_startup.log
fi

echo "----- Uvicorn Startup Logs -----"
cat /app/log/uvicorn_startup.log || echo "No uvicorn logs found"

# --- Start Nginx ---
echo "🌐 Starting Nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!
echo "✅ Nginx started with PID: $NGINX_PID"

# --- Monitor both processes ---
monitor_processes() {
    while true; do
        if ! kill -0 $NGINX_PID 2>/dev/null; then
            echo "❌ Nginx process died unexpectedly!"
            break
        fi

        if ! kill -0 $UVICORN_PID 2>/dev/null; then
            echo "❌ FastAPI process died unexpectedly! Dumping recent logs:"
            tail -n 50 /app/log/uvicorn_startup.log
            break
        fi

        echo "📊 Nginx($NGINX_PID)=alive, FastAPI($UVICORN_PID)=alive"
        sleep 30
    done
    echo "⚠️ One of the core services stopped. Exiting..."
    exit 1
}


# Start monitoring in background
monitor_processes &
MONITOR_PID=$!

# Enhanced graceful shutdown function
graceful_shutdown() {
    SIGNAL=$1
    echo "🛑 Received $SIGNAL signal at $(date)"
    
    # Log comprehensive diagnostics
    log_diagnostics $SIGNAL
    
    echo "🔁 Starting graceful shutdown sequence..."
    
    # Stop monitoring first
    kill $MONITOR_PID 2>/dev/null || true
    
    # Stop Nginx gracefully
    echo "🌐 Stopping Nginx (PID: $NGINX_PID)..."
    kill -TERM $NGINX_PID 2>/dev/null || true
    
    # Stop FastAPI gracefully
    echo "🐍 Stopping FastAPI (PID: $UVICORN_PID)..."
    kill -TERM $UVICORN_PID 2>/dev/null || true
    
    # Wait for processes to finish
    echo "⏳ Waiting for processes to terminate..."
    # Use a simple wait loop instead of wait -n
    for pid in $NGINX_PID $UVICORN_PID; do
        while kill -0 $pid 2>/dev/null; do
            sleep 0.5
        done
    done
    
    echo "✅ Graceful shutdown completed at $(date)"
    exit 0
}

# Set up signal handlers with enhanced logging
trap 'graceful_shutdown SIGTERM' TERM
trap 'graceful_shutdown SIGINT' INT

# Use a simple wait loop instead of wait -n (compatible with basic shell)
echo "👀 Monitoring processes..."
while true; do
    # Check if either process has died
    if ! kill -0 $NGINX_PID 2>/dev/null; then
        echo "❌ Nginx process ($NGINX_PID) died unexpectedly!"
        log_diagnostics "NGINX_PROCESS_DIED"
        break
    fi
    
    if ! kill -0 $UVICORN_PID 2>/dev/null; then
        echo "❌ FastAPI process ($UVICORN_PID) died unexpectedly!"
        log_diagnostics "FASTAPI_PROCESS_DIED"
        break
    fi
    
    # Sleep briefly to avoid busy waiting
    sleep 5
done

# Attempt to shutdown gracefully anyway
graceful_shutdown "AUTO_SHUTDOWN"

# ---  Start Supervisord ---
#echo "🚀 Handing over to supervisord for multiprocess management - Uvicorn for API and Nginx for proxying..."
#exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
#echo "🌀 Started all..."

