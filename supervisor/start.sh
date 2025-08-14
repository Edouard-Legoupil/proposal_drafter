#!/bin/sh
set -e

echo "🚀 Starting container entrypoint..."

# Ensure PORT is set
PORT=${PORT:-8080}
echo "📌 Cloud Run will expect Nginx to listen on PORT=$PORT"

# Replace $PORT placeholder in Nginx config
sed -i "s/\$PORT/$PORT/g" /etc/nginx/conf.d/default.conf
echo "✅ Updated Nginx config:"
grep "listen" /etc/nginx/conf.d/default.conf


# ---  Start Supervisord ---
echo "🚀 Handing over to supervisord for multiprocess management - Uvicorn for API and Nginx for proxying..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
echo "🌀 Started all..."
