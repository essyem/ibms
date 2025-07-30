"""
WSGI config for trendzportal project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')

# Get the standard WSGI application
django_application = get_wsgi_application()

# Create custom WSGI middleware to handle ports in HOST header
class PortAwareHostMiddleware:
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        # Get the HTTP_HOST value
        http_host = environ.get('HTTP_HOST', '')
        
        # If HTTP_HOST contains a port, strip it
        if ':' in http_host:
            domain = http_host.split(':')[0]
            environ['HTTP_HOST'] = domain
        
        return self.app(environ, start_response)

# Wrap the Django application with our middleware
application = PortAwareHostMiddleware(django_application)
