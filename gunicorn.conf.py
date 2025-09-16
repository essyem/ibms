# Gunicorn configuration file for TrendzApps IBMS

# Server socket
bind = "127.0.0.1:8001"
backlog = 2048

# Worker processes
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/home/azureuser/ibms/salesportal/logs/gunicorn_access.log"
errorlog = "/home/azureuser/ibms/salesportal/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "trendzapps-ibms"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn-ibms.pid"
user = "azureuser"
group = "azureuser"
tmp_upload_dir = None

# SSL (disable for now, can be enabled later if needed)
# keyfile = None
# certfile = None

# Preload application for better performance
preload_app = True

# Environment variables
raw_env = [
    'DJANGO_SETTINGS_MODULE=trendzportal.settings',
]