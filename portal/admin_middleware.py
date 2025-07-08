# portal/admin_middleware.py
from django.http import Http404
from django.urls import resolve
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import admin

class SiteAdminMiddleware:
    """
    Middleware to restrict admin access based on the current site
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is an admin request
        if request.path.startswith('/admin/'):
            try:
                current_site = get_current_site(request)
                
                # Define which apps are allowed for each site
                site_apps = {
                    1: {  # TRENDZ site - allow all apps
                        'allowed_apps': [
                            'portal', 'finance', 'procurement', 'auth', 
                            'contenttypes', 'sessions', 'messages', 'sites',
                            'admin'
                        ]
                    },
                    2: {  # Al Malika site - restrict finance and procurement
                        'allowed_apps': [
                            'portal', 'auth', 'contenttypes', 'sessions', 
                            'messages', 'sites', 'admin'
                        ]
                    }
                }
                
                # Check if the request is for a specific app admin
                path_parts = request.path.strip('/').split('/')
                if len(path_parts) >= 2 and path_parts[0] == 'admin':
                    # Allow general admin paths like /admin/, /admin/login/, etc.
                    if len(path_parts) == 1 or path_parts[1] in ['', 'login', 'logout', 'password_change', 'password_change_done', 'jsi18n']:
                        pass
                    elif len(path_parts) >= 2:
                        app_label = path_parts[1]
                        
                        # Check if the app is allowed for this site
                        allowed_apps = site_apps.get(current_site.id, {}).get('allowed_apps', [])
                        if app_label not in allowed_apps:
                            raise Http404("This admin section is not available for this site.")
                            
            except Http404:
                raise  # Re-raise Http404 exceptions
            except Exception as e:
                # If there's any other error in site detection, allow access
                # to prevent breaking the admin entirely
                pass

        response = self.get_response(request)
        return response
