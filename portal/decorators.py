# portal/decorators.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def superuser_required(view_func):
    """
    Decorator that requires the user to be a superuser
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin:login')
        
        if not request.user.is_superuser:
            messages.error(request, 'You need superuser privileges to access this page.')
            return redirect('admin:index')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def dashboard_access_required(view_func):
    """
    Decorator that requires the user to be either:
    1. A superuser, OR
    2. A member of 'Dashboard Users' group, OR  
    3. Have 'view_dashboard' permission
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin:login')
        
        # Check if user is superuser
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Check if user is in Dashboard Users group
        if request.user.groups.filter(name='Dashboard Users').exists():
            return view_func(request, *args, **kwargs)
        
        # Check if user has specific permission
        if request.user.has_perm('portal.view_dashboard'):
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'You do not have permission to access the dashboard.')
        return redirect('admin:index')
    
    return _wrapped_view

def reports_access_required(view_func):
    """
    Decorator that requires the user to be either:
    1. A superuser, OR
    2. A member of 'Reports Users' group, OR
    3. Have 'view_reports' permission
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin:login')
        
        # Check if user is superuser
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Check if user is in Reports Users group
        if request.user.groups.filter(name='Reports Users').exists():
            return view_func(request, *args, **kwargs)
        
        # Check if user has specific permission
        if request.user.has_perm('portal.view_reports'):
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'You do not have permission to access reports.')
        return redirect('admin:index')
    
    return _wrapped_view

def staff_or_group_required(*group_names):
    """
    Decorator that requires the user to be staff OR in one of the specified groups
    Usage: @staff_or_group_required('Dashboard Users', 'Manager')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('admin:login')
            
            # Check if user is staff or superuser
            if request.user.is_staff or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check if user is in any of the allowed groups
            user_groups = request.user.groups.values_list('name', flat=True)
            if any(group in user_groups for group in group_names):
                return view_func(request, *args, **kwargs)
            
            messages.error(request, f'You need to be staff or in one of these groups: {", ".join(group_names)}')
            return redirect('admin:index')
        
        return _wrapped_view
    return decorator
