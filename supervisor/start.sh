#!/bin/sh


echo "🚀 Starting GCP entrypoint script..."
echo "Set port for Nginx..."
sed -i "s/\$PORT/$PORT/g" /etc/nginx/conf.d/default.conf

# ---  Start Supervisord ---
echo "🚀 Handing over to supervisord..."
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf


### Legacy...
# Start the FastAPI application with uvicorn in the background.
# We bind it to localhost so it's not directly accessible from outside the container.
# /venv/bin/uvicorn main:app --host 0.0.0.0 --port 8502 --log-level debug &
#/venv/bin/gunicorn main:app --bind 0.0.0.0:8502 --worker-class uvicorn.workers.UvicornWorker  --forwarded-allow-ips * --workers 2  &


# Start Nginx in the foreground.
# The 'daemon off;' directive is crucial for Nginx to run as the main process.
#/usr/sbin/nginx -g "daemon off;"