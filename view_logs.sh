#!/bin/bash
# Enhanced Log Viewer for Trendz Portal
# Usage: ./view_logs.sh [option]

COLOR_RESET="\033[0m"
COLOR_GREEN="\033[32m"
COLOR_YELLOW="\033[33m"
COLOR_BLUE="\033[34m"
COLOR_RED="\033[31m"

print_header() {
    echo -e "${COLOR_BLUE}========================================${COLOR_RESET}"
    echo -e "${COLOR_GREEN}$1${COLOR_RESET}"
    echo -e "${COLOR_BLUE}========================================${COLOR_RESET}"
}

case "$1" in
    gunicorn-access)
        print_header "Gunicorn Access Log (Live)"
        tail -f /home/azureuser/trendzportal/logs/gunicorn_access.log
        ;;
    gunicorn-error)
        print_header "Gunicorn Error Log (Live)"
        tail -f /home/azureuser/trendzportal/logs/gunicorn_error.log
        ;;
    django)
        print_header "Django Application Log (Live)"
        tail -f /home/azureuser/trendzportal/logs/django.log
        ;;
    nginx-http)
        print_header "Nginx HTTP Access Log (Live)"
        sudo tail -f /var/log/nginx/portal_http_access.log
        ;;
    nginx-https)
        print_header "Nginx HTTPS Access Log (Live)"
        sudo tail -f /var/log/nginx/portal_https_access.log
        ;;
    nginx-error)
        print_header "Nginx Error Logs (Live)"
        sudo tail -f /var/log/nginx/portal_http_error.log /var/log/nginx/portal_https_error.log
        ;;
    all)
        print_header "All Portal Logs (Live - Combined)"
        sudo tail -f \
            /home/azureuser/trendzportal/logs/gunicorn_access.log \
            /home/azureuser/trendzportal/logs/gunicorn_error.log \
            /home/azureuser/trendzportal/logs/django.log \
            /var/log/nginx/portal_https_access.log \
            /var/log/nginx/portal_https_error.log
        ;;
    status)
        print_header "Log Files Status"
        echo -e "${COLOR_YELLOW}Gunicorn Logs:${COLOR_RESET}"
        ls -lh /home/azureuser/trendzportal/logs/gunicorn_*.log 2>/dev/null || echo "No gunicorn logs yet"
        echo ""
        echo -e "${COLOR_YELLOW}Django Logs:${COLOR_RESET}"
        ls -lh /home/azureuser/trendzportal/logs/django.log* 2>/dev/null || echo "No django logs yet"
        echo ""
        echo -e "${COLOR_YELLOW}Nginx Logs:${COLOR_RESET}"
        sudo ls -lh /var/log/nginx/portal_*.log 2>/dev/null || echo "No nginx portal logs yet"
        echo ""
        echo -e "${COLOR_YELLOW}Service Status:${COLOR_RESET}"
        sudo systemctl status portal.service --no-pager | head -10
        ;;
    errors)
        print_header "Recent Errors (Last 50 lines)"
        echo -e "${COLOR_RED}=== Gunicorn Errors ===${COLOR_RESET}"
        tail -50 /home/azureuser/trendzportal/logs/gunicorn_error.log 2>/dev/null || echo "No errors"
        echo ""
        echo -e "${COLOR_RED}=== Django Errors ===${COLOR_RESET}"
        tail -50 /home/azureuser/trendzportal/logs/django.log 2>/dev/null | grep -i error || echo "No errors"
        echo ""
        echo -e "${COLOR_RED}=== Nginx Errors ===${COLOR_RESET}"
        sudo tail -50 /var/log/nginx/portal_https_error.log 2>/dev/null || echo "No errors"
        ;;
    access)
        print_header "Recent Access Logs (Last 20 requests)"
        echo -e "${COLOR_YELLOW}=== Nginx HTTPS Access ===${COLOR_RESET}"
        sudo tail -20 /var/log/nginx/portal_https_access.log 2>/dev/null || echo "No requests yet"
        echo ""
        echo -e "${COLOR_YELLOW}=== Gunicorn Access ===${COLOR_RESET}"
        tail -20 /home/azureuser/trendzportal/logs/gunicorn_access.log 2>/dev/null || echo "No requests yet"
        ;;
    *)
        echo -e "${COLOR_GREEN}Trendz Portal - Enhanced Log Viewer${COLOR_RESET}"
        echo ""
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  gunicorn-access   - Tail Gunicorn access log"
        echo "  gunicorn-error    - Tail Gunicorn error log"
        echo "  django            - Tail Django application log"
        echo "  nginx-http        - Tail Nginx HTTP access log"
        echo "  nginx-https       - Tail Nginx HTTPS access log"
        echo "  nginx-error       - Tail Nginx error logs"
        echo "  all               - Tail all logs combined"
        echo "  status            - Show log files status and sizes"
        echo "  errors            - Show recent errors from all logs"
        echo "  access            - Show recent access logs"
        echo ""
        echo "Example: $0 all"
        ;;
esac
