#!/bin/sh
set -e

# Replace environment variables in the Nginx configuration
envsubst '${BACKEND_API_URL}' < /etc/nginx/conf.d/default.template > /etc/nginx/conf.d/default.conf

# Execute the default Docker command
exec "$@"