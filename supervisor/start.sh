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

# Wait for Cloud SQL socket to be available
# echo "Waiting for Cloud SQL socket..."
# while [ ! -S "/cloudsql/$DB_HOST/.s.PGSQL.5432" ]; do
#   sleep 1
# done
# echo "Cloud SQL socket is ready!"

# # Optional: try a simple connection using psql to ensure DB is up
# if ! PGPASSWORD=$DB_PASSWORD psql -h "/cloudsql/$DB_HOST" -U $DB_USER -d $DB_NAME -c '\q'; then
#   echo "Database not ready, exiting..."
#   exit 1
# fi

# Wait up to 15 seconds for Cloud SQL socket
echo "Waiting for Cloud SQL socket..."
timeout=15
elapsed=0
while [ ! -S "/cloudsql/$DB_HOST/.s.PGSQL.5432" ] && [ $elapsed -lt $timeout ]; do
    sleep 1
    elapsed=$((elapsed + 1))
done

if [ -S "/cloudsql/$DB_HOST/.s.PGSQL.5432" ]; then
    echo "Cloud SQL socket is ready!"
else
    echo "Timeout: Cloud SQL socket not available after $timeout seconds. If you are on GCP, it is an issue..."
fi

# ---  Start Supervisord ---
echo "🚀 Handing over to supervisord for multiprocess management - Uvicorn for API and Nginx for proxying..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
echo "🌀 Started all..."
