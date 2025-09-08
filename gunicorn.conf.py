# Gunicorn configuration file for production
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Load application code before the worker processes are forked
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = 'rto_project'

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if using HTTPS directly with gunicorn)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
