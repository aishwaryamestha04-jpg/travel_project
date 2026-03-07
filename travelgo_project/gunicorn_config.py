"""
Gunicorn Configuration for TravelGo Production Deployment
===========================================================
This configuration file is used by Gunicorn to run the TravelGo application
in a production environment on AWS EC2.
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended: (2 x CPU) + 1
worker_class = "sync"  # Use sync workers; can switch to gevent for async
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/travelgo/access.log"
errorlog = "/var/log/travelgo/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "travelgo"

# Server mechanics
daemon = False
pidfile = "/var/run/travelgo.pid"
umask = 0o007
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL (uncomment if needed)
# keyfile = "/etc/ssl/private/travelgo.key"
# certfile = "/etc/ssl/certs/travelgo.crt"

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print("TravelGo Gunicorn server starting...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Reloading TravelGo workers...")

def when_ready(server):
    """Called just after the server is started."""
    print(f"TravelGo server ready. Listening on: {bind}")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    print("TravelGo server shutting down...")

# Worker hooks
def worker_int(worker):
    """Called when a worker receives SIGINT or SIGQUIT."""
    print(f"Worker {worker.pid} interrupted")

def worker_abort(worker):
    """Called when a worker receives SIGABRT."""
    print(f"Worker {worker.pid} aborted")

# Monitoring
def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"Worker {worker.pid} started")

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    pass

