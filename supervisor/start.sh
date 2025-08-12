#!/bin/bash

# Start the FastAPI application with uvicorn in the background.
# We bind it to localhost so it's not directly accessible from outside the container.
/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8502 --log-level debug &

# Start Nginx in the foreground.
# The 'daemon off;' directive is crucial for Nginx to run as the main process.
/usr/sbin/nginx -g "daemon off;"