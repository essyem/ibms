# portal/middleware.py
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.http import Http404
from threading import local

_thread_locals = local()

class MultiTenantMiddleware:
    """
    Middleware to handle multi-tenant functionality based on domain
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the current site based on the request domain
        try:
            # Extract domain name from HTTP_HOST which may contain port number
            host = request.META.get('HTTP_HOST', '')
            domain = host.split(':')[0]  # Remove port if present
            
            # Try to find the site by domain
            try:
                current_site = Site.objects.get(domain=domain)
            except Site.DoesNotExist:
                # Try to find by full host (with port)
                current_site = get_current_site(request)
            
            # Set the current site ID in settings for use by SiteManager
            settings.SITE_ID = current_site.id
            
            # Add site information to request for templates
            request.current_site = current_site
            
            # Add site-specific company name for templates
            if current_site.id == 1:  # TRENDZ
                request.company_name = "TRENDZ Trading & Services"
                request.company_short = "TRENDZ"
            elif current_site.id == 2:  # Al Malika
                request.company_name = "Al Malika Trading & Services"
                request.company_short = "Al Malika"
            else:
                request.company_name = current_site.name
                request.company_short = current_site.name
                
        except Site.DoesNotExist:
            # If site doesn't exist, default to site 1
            settings.SITE_ID = 1
            request.current_site = Site.objects.get(id=1)
            request.company_name = "TRENDZ Trading & Services"
            request.company_short = "TRENDZ"

        response = self.get_response(request)
        return response

class SiteRedirectMiddleware:
    """
    Optional: Redirect to correct site if accessed incorrectly
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # You can add domain-specific redirects here if needed
        response = self.get_response(request)
        return response

class ThreadLocalMiddleware:
    """
    Store the current request in thread local storage
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Store request in thread local
        _thread_locals.request = request
        response = self.get_response(request)
        # Clean up after request
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return response
