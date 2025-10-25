# Gunicorn configuration file for TrendzApps IBMS

# Server socket - Unix socket for Nginx connection
bind = "unix:/home/azureuser/trendzportal/portal.sock"
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

# Logging - Enhanced with detailed information
accesslog = "/home/azureuser/trendzportal/logs/gunicorn_access.log"
errorlog = "/home/azureuser/trendzportal/logs/gunicorn_error.log"
loglevel = "info"
# Enhanced access log format with timing and detailed info
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s %(p)s'
# Format: client_ip - user [time] "request" status bytes "referer" "user_agent" request_time process_id

# Capture stdout/stderr to logs
capture_output = True
# Enable access log
enable_stdio_inheritance = True

# Process naming
proc_name = "trendzapps-ibms"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn-ibms.pid"
# user and group managed by systemd service
tmp_upload_dir = None

# SSL (disable for now, can be enabled later if needed)
# keyfile = None
# certfile = None

# Preload application for better performance (disabled for socket binding issues)
preload_app = False

# Environment variables
raw_env = [
    'DJANGO_SETTINGS_MODULE=trendzportal.settings',
]