# rbac/middleware/rbac_middleware.py
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from ..models import SiteUserProfile
import logging

logger = logging.getLogger(__name__)

class RBACMiddleware(MiddlewareMixin):
    """
    Role-Based Access Control Middleware for multi-tenant sites
    """
    
    # URLs that bypass RBAC checks
    EXEMPT_URLS = [
        '/admin/login/',
        '/admin/logout/',
        '/portal/login/',
        '/portal/logout/',
        '/api/barcode-scan/',  # Public API
        '/static/',
        '/media/',
        '/favicon.ico',
    ]
    
    # Permission requirements for different URL patterns
    PERMISSION_MAP = {
        '/admin/': 'can_access_admin',
        '/portal/products/': 'can_manage_products',
        '/portal/customers/': 'can_manage_customers',
        '/portal/orders/': 'can_manage_orders',
        '/portal/reports/': 'can_view_reports',
        '/portal/users/': 'can_manage_users',
        '/portal/settings/': 'can_manage_settings',
        '/finance/': 'can_manage_finance',
        '/procurement/': 'can_manage_procurement',
    }
    
    def process_request(self, request):
        # Skip for exempted URLs
        path = request.path
        if any(path.startswith(exempt) for exempt in self.EXEMPT_URLS):
            return None
            
        # Skip for anonymous users (let Django's auth handle it)
        if not request.user.is_authenticated:
            return None
            
        # Skip for superusers
        if request.user.is_superuser:
            return None
            
        # Get current site
        current_site = get_current_site(request)
        
        # Get or create user profile for current site
        try:
            user_profile = SiteUserProfile.objects.get(
                user=request.user,
                site=current_site
            )
            
            # Check if user is active on this site
            if not user_profile.is_site_active:
                logger.warning(f"Inactive user {request.user.username} attempted access to {current_site.domain}")
                if self._is_ajax_request(request) or path.startswith('/api/'):
                    return JsonResponse({'error': 'Access denied - account inactive on this site'}, status=403)
                messages.error(request, 'Your account is inactive on this site.')
                return redirect('portal:login')
                
        except SiteUserProfile.DoesNotExist:
            # User doesn't have access to this site
            logger.warning(f"User {request.user.username} has no profile for site {current_site.domain}")
            if self._is_ajax_request(request) or path.startswith('/api/'):
                return JsonResponse({'error': 'Access denied - no access to this site'}, status=403)
            messages.error(request, 'You do not have access to this site.')
            return redirect('portal:login')
        
        # Check specific permissions for the requested path
        required_permission = self._get_required_permission(path)
        if required_permission:
            if not user_profile.has_permission(required_permission):
                logger.warning(f"User {request.user.username} denied access to {path} - missing {required_permission}")
                if self._is_ajax_request(request) or path.startswith('/api/'):
                    return JsonResponse({'error': f'Access denied - insufficient permissions'}, status=403)
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('portal:dashboard')  # Redirect to dashboard or appropriate page
        
        # Add user profile to request for easy access
        request.user_profile = user_profile
        return None
    
    def _get_required_permission(self, path):
        """Get the required permission for a given path"""
        for url_pattern, permission in self.PERMISSION_MAP.items():
            if path.startswith(url_pattern):
                return permission
        return None
    
    def _is_ajax_request(self, request):
        """Check if request is AJAX (replacement for deprecated request.is_ajax())"""
        return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

class SiteAccessLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log user access for audit purposes
    """
    
    def process_request(self, request):
        if request.user.is_authenticated and not request.path.startswith('/static/') and not request.path.startswith('/media/'):
            current_site = get_current_site(request)
            
            # Update last login for site
            try:
                user_profile = SiteUserProfile.objects.get(
                    user=request.user,
                    site=current_site
                )
                user_profile.last_login_site = timezone.now()
                user_profile.save(update_fields=['last_login_site'])
            except SiteUserProfile.DoesNotExist:
                pass
                
        return None
