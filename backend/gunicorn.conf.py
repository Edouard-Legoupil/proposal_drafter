# gunicorn.conf.py
import multiprocessing

# Server socket
bind = "0.0.0.0:8502"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stdout
loglevel = "info"
reload = True

# Timeout
timeout = 1200