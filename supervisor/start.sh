#!/bin/sh
set -e


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

echo "🚀 Starting container entrypoint..."

# Ensure PORT is set
PORT=${PORT:-8080}
echo "📌 Cloud Run will expect Nginx to listen on PORT=$PORT"

# Replace $PORT placeholder in Nginx config
sed -i "s/\$PORT/$PORT/g" /etc/nginx/conf.d/default.conf
echo "✅ Updated Nginx config:"
grep "listen" /etc/nginx/conf.d/default.conf

# Wait up to 15 seconds for Cloud SQL socket
# echo "Waiting for Cloud SQL socket..."
# timeout=15
# elapsed=0
# while [ ! -S "/cloudsql/$DB_HOST/.s.PGSQL.5432" ] && [ $elapsed -lt $timeout ]; do
#     sleep 1
#     elapsed=$((elapsed + 1))
# done

# if [ -S "/cloudsql/$DB_HOST/.s.PGSQL.5432" ]; then
#     echo "Cloud SQL socket is ready!"
# else
#     echo "Timeout: Cloud SQL socket not available after $timeout seconds. If you are on GCP, it is an issue..."
# fi


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


# Wait for Cloud SQL (but don't block indefinitely)
# echo "Checking for Cloud SQL socket..."
# if [ -n "$DB_HOST" ] && [ ! -S "/cloudsql/$DB_HOST/.s.PGSQL.5432" ]; then
#     echo "Waiting up to 10s for Cloud SQL socket..."
#     timeout 10 bash -c 'until [ -S "/cloudsql/$0/.s.PGSQL.5432" ]; do sleep 1; done' "$DB_HOST" || \
#     echo "Warning: Cloud SQL socket not ready, proceeding anyway..."
# fi

# Start Nginx and FastAPI directly
echo "🚀 Starting Nginx and FastAPI..."

# Start Nginx in background
echo "🌐 Starting Nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!
echo "✅ Nginx started with PID: $NGINX_PID"

# Small delay to ensure Nginx starts before FastAPI
sleep 2

# Start FastAPI
echo "🐍 Starting FastAPI..."
/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8502 --log-level info &
UVICORN_PID=$!
echo "✅ FastAPI started with PID: $UVICORN_PID"

# Monitor processes in background
monitor_processes() {
    while true; do
        if ! kill -0 $NGINX_PID 2>/dev/null; then
            echo "❌ Nginx process ($NGINX_PID) died unexpectedly!"
            log_diagnostics "NGINX_PROCESS_DIED"
            exit 1
        fi
        
        if ! kill -0 $UVICORN_PID 2>/dev/null; then
            echo "❌ FastAPI process ($UVICORN_PID) died unexpectedly!"
            log_diagnostics "FASTAPI_PROCESS_DIED"
            exit 1
        fi
        
        # Log resource usage every 60 seconds
        echo "📊 Process status: Nginx($NGINX_PID)=alive, FastAPI($UVICORN_PID)=alive, Memory: $(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2}')"
        sleep 60
    done
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
    wait $NGINX_PID 2>/dev/null || true
    wait $UVICORN_PID 2>/dev/null || true
    
    echo "✅ Graceful shutdown completed at $(date)"
    exit 0
}

# Set up signal handlers with enhanced logging
trap 'graceful_shutdown SIGTERM' TERM
trap 'graceful_shutdown SIGINT' INT

# Wait for processes and capture exit codes
echo "👀 Monitoring processes..."
wait -n $NGINX_PID $UVICORN_PID
EXIT_CODE=$?

# If we get here, a process died unexpectedly
echo "❌ A process died unexpectedly with exit code: $EXIT_CODE"
log_diagnostics "PROCESS_FAILURE_$EXIT_CODE"

# Attempt to shutdown gracefully anyway
graceful_shutdown "AUTO_SHUTDOWN"

# ---  Start Supervisord ---
#echo "🚀 Handing over to supervisord for multiprocess management - Uvicorn for API and Nginx for proxying..."
#exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
#echo "🌀 Started all..."

