# Enhanced Logging Guide - Trendz Portal

## Overview
This document describes the enhanced logging configuration for the Trendz Portal application, including Gunicorn, Nginx, and Django logs.

## Log Locations

### Gunicorn Logs
Located in: `/home/azureuser/trendzportal/logs/`

- **gunicorn_access.log** - HTTP access logs with detailed request information
  - Format: client_ip - user [time] "request" status bytes "referer" "user_agent" request_time process_id
  - Example: `192.168.1.1 - - [23/Oct/2025:17:50:00] "GET /api/customers HTTP/1.1" 200 1234 "-" "Mozilla/5.0" 0.123 12345`

- **gunicorn_error.log** - Application errors, worker crashes, and startup issues
  - Level: INFO (shows worker starts, stops, and errors)

- **gunicorn_stdout.log** - Standard output from Gunicorn workers
- **gunicorn_stderr.log** - Standard error output from Gunicorn workers

### Django Application Logs
Located in: `/home/azureuser/trendzportal/logs/`

- **django.log** - Django application logs (queries, warnings, errors)
  - Configured in `settings.py` LOGGING configuration
  - Rotated daily, kept for 30 days

### Nginx Logs
Located in: `/var/log/nginx/`

- **portal_http_access.log** - HTTP requests (port 80, redirects to HTTPS)
  - Enhanced format with upstream info and timing

- **portal_https_access.log** - HTTPS requests (port 443, main traffic)
  - Format includes:
    - Client IP, user, timestamp
    - Request method, URI, protocol
    - Status code, bytes sent
    - Referer and User-Agent
    - X-Forwarded-For header
    - Upstream server address and status
    - Request time and upstream response time

- **portal_http_error.log** - HTTP-related errors
- **portal_https_error.log** - HTTPS-related errors

## Log Format Details

### Nginx Detailed Format
```
$remote_addr - $remote_user [$time_local] "$request"
$status $body_bytes_sent "$http_referer"
"$http_user_agent" "$http_x_forwarded_for"
upstream: $upstream_addr upstream_status: $upstream_status
request_time: $request_time upstream_response_time: $upstream_response_time
```

**Fields Explanation:**
- `remote_addr` - Client IP address
- `remote_user` - Authenticated username (if any)
- `time_local` - Local time when request was received
- `request` - Full request line (method, URI, protocol)
- `status` - HTTP response status code
- `body_bytes_sent` - Number of bytes sent to client
- `http_referer` - Referer URL
- `http_user_agent` - Client user agent string
- `http_x_forwarded_for` - Client IP if behind proxy
- `upstream_addr` - Backend server address (Unix socket)
- `upstream_status` - Status code from backend
- `request_time` - Total request processing time
- `upstream_response_time` - Backend processing time

### Gunicorn Enhanced Format
```
%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s %(p)s
```

**Fields Explanation:**
- `%(h)s` - Remote address
- `%(l)s` - '-' (remote logname)
- `%(u)s` - Remote user
- `%(t)s` - Request timestamp
- `%(r)s` - Request line (method, path, protocol)
- `%(s)s` - Status code
- `%(b)s` - Response length
- `%(f)s` - Referer
- `%(a)s` - User agent
- `%(L)s` - Request time in seconds (decimal)
- `%(p)s` - Process ID

## Log Rotation

All logs are automatically rotated using `logrotate`:

**Configuration**: `/etc/logrotate.d/trendzportal`

**Schedule**:
- Frequency: Daily
- Retention: 30 days
- Compression: Yes (delayed by 1 day)
- Action on rotate: Reload respective services

**Manual rotation test**:
```bash
sudo logrotate -f /etc/logrotate.d/trendzportal
```

## Viewing Logs

### Using the Enhanced Log Viewer Script

```bash
# View all logs combined (recommended for live monitoring)
./view_logs.sh all

# View specific log files
./view_logs.sh gunicorn-access
./view_logs.sh gunicorn-error
./view_logs.sh django
./view_logs.sh nginx-https
./view_logs.sh nginx-error

# Check log file status and sizes
./view_logs.sh status

# View recent errors only
./view_logs.sh errors

# View recent access logs
./view_logs.sh access
```

### Using Standard Tools

```bash
# Tail logs in real-time
tail -f /home/azureuser/trendzportal/logs/gunicorn_access.log
tail -f /home/azureuser/trendzportal/logs/django.log
sudo tail -f /var/log/nginx/portal_https_access.log

# View last N lines
tail -100 /home/azureuser/trendzportal/logs/gunicorn_error.log

# Search for errors
grep -i error /home/azureuser/trendzportal/logs/gunicorn_error.log
grep -i "500" /var/log/nginx/portal_https_access.log

# Search with context
grep -C 5 "exception" /home/azureuser/trendzportal/logs/django.log

# Follow multiple logs
tail -f /home/azureuser/trendzportal/logs/*.log
```

## Service Management

### Check Service Status
```bash
sudo systemctl status portal.service
sudo systemctl status nginx
```

### View Service Logs (systemd journal)
```bash
sudo journalctl -u portal.service -f
sudo journalctl -u nginx -f
```

### Restart Services
```bash
# Restart Gunicorn
sudo systemctl restart portal.service

# Reload Nginx (graceful, no downtime)
sudo systemctl reload nginx

# Restart Nginx
sudo systemctl restart nginx
```

## Troubleshooting

### No Logs Being Written

1. **Check service status**:
   ```bash
   sudo systemctl status portal.service
   ```

2. **Check file permissions**:
   ```bash
   ls -la /home/azureuser/trendzportal/logs/
   ```

3. **Check disk space**:
   ```bash
   df -h
   ```

4. **Restart services**:
   ```bash
   sudo systemctl restart portal.service
   sudo systemctl reload nginx
   ```

### High Error Rate

1. **Check error logs**:
   ```bash
   ./view_logs.sh errors
   ```

2. **Check Django errors**:
   ```bash
   tail -100 /home/azureuser/trendzportal/logs/django.log | grep ERROR
   ```

3. **Check Nginx upstream errors**:
   ```bash
   sudo grep "upstream" /var/log/nginx/portal_https_error.log
   ```

### Slow Response Times

1. **Check request timing in Nginx logs**:
   ```bash
   sudo grep "request_time" /var/log/nginx/portal_https_access.log | tail -50
   ```

2. **Check Gunicorn response times**:
   ```bash
   tail -50 /home/azureuser/trendzportal/logs/gunicorn_access.log
   ```

3. **Find slow requests (>1 second)**:
   ```bash
   # Nginx logs
   sudo awk '$NF > 1.0' /var/log/nginx/portal_https_access.log
   ```

## Performance Analysis

### Request Statistics

**Count requests by status code**:
```bash
# Nginx
sudo awk '{print $(NF-11)}' /var/log/nginx/portal_https_access.log | sort | uniq -c

# Gunicorn
awk '{print $9}' /home/azureuser/trendzportal/logs/gunicorn_access.log | sort | uniq -c
```

**Average response time**:
```bash
# Nginx (requests in last hour)
sudo awk '{print $(NF)}' /var/log/nginx/portal_https_access.log | \
    awk '{sum+=$1; n++} END {print sum/n}'
```

**Top URLs by request count**:
```bash
# Nginx
sudo awk '{print $7}' /var/log/nginx/portal_https_access.log | \
    sort | uniq -c | sort -rn | head -20
```

**Top client IPs**:
```bash
# Nginx
sudo awk '{print $1}' /var/log/nginx/portal_https_access.log | \
    sort | uniq -c | sort -rn | head -20
```

## Log File Sizes

**Check current sizes**:
```bash
du -sh /home/azureuser/trendzportal/logs/*
sudo du -sh /var/log/nginx/portal_*
```

**Monitor log growth**:
```bash
watch -n 5 'ls -lh /home/azureuser/trendzportal/logs/'
```

## Configuration Files

- **Gunicorn**: `/home/azureuser/trendzportal/gunicorn.conf.py`
- **Systemd Service**: `/etc/systemd/system/portal.service`
- **Nginx**: `/etc/nginx/sites-available/trendzportal`
- **Log Rotation**: `/etc/logrotate.d/trendzportal`
- **Django Logging**: `trendzportal/settings.py` (LOGGING dict)

## Best Practices

1. **Regular Monitoring**: Use `./view_logs.sh all` during deployments
2. **Error Alerts**: Set up monitoring tools to alert on error spikes
3. **Log Analysis**: Regularly review logs for patterns and issues
4. **Disk Space**: Monitor `/home/azureuser/trendzportal/logs/` and `/var/log/nginx/`
5. **Performance**: Use log data to identify slow endpoints
6. **Security**: Review access logs for suspicious patterns

## Support

For issues or questions about logging:
1. Check this guide first
2. Review service status: `sudo systemctl status portal.service`
3. Check recent errors: `./view_logs.sh errors`
4. Review configuration files for any modifications
