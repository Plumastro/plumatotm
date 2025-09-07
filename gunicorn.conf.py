# Gunicorn configuration for PLUMATOTM API
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
backlog = 2048

# Worker processes
workers = 1  # Single worker to avoid memory issues with heavy calculations
worker_class = "sync"
worker_connections = 1000
timeout = 300  # Increased timeout for astrological calculations (5 minutes)
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 50  # Restart more frequently to prevent memory leaks
max_requests_jitter = 10

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "plumatotm-api"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (not needed for Render)
keyfile = None
certfile = None
