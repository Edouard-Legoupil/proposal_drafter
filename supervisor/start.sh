#!/bin/sh


echo "🚀 Starting GCP entrypoint script..."
echo "Set port for Nginx..."
sed -i "s/\$PORT/$PORT/g" /etc/nginx/conf.d/default.conf

# ---  Start Supervisord ---
echo "🚀 Handing over to supervisord..."
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
