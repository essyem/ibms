# portal/templatetags/rbac_tags.py
from django import template
from django.contrib.sites.shortcuts import get_current_site
from rbac.models import SiteUserProfile

register = template.Library()

@register.simple_tag(takes_context=True)
def user_has_permission(context, permission_name):
    """
    Template tag to check if current user has a specific permission
    Usage: {% user_has_permission 'can_manage_products' as can_manage %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    if request.user.is_superuser:
        return True
    
    # Check if user_profile is already in request (from middleware)
    if hasattr(request, 'user_profile'):
        return request.user_profile.has_permission(permission_name)
    
    # Fallback: get profile manually
    try:
        current_site = get_current_site(request)
        user_profile = SiteUserProfile.objects.get(
            user=request.user,
            site=current_site
        )
        return user_profile.has_permission(permission_name)
    except SiteUserProfile.DoesNotExist:
        return False

@register.simple_tag(takes_context=True)
def get_user_role(context):
    """
    Get the current user's role for the current site
    Usage: {% get_user_role as user_role %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return None
    
    if request.user.is_superuser:
        return "Superuser"
    
    # Check if user_profile is already in request (from middleware)
    if hasattr(request, 'user_profile'):
        return request.user_profile.role.name if request.user_profile.role else "No Role"
    
    # Fallback: get profile manually
    try:
        current_site = get_current_site(request)
        user_profile = SiteUserProfile.objects.get(
            user=request.user,
            site=current_site
        )
        return user_profile.role.name if user_profile.role else "No Role"
    except SiteUserProfile.DoesNotExist:
        return "No Access"

@register.simple_tag(takes_context=True)
def get_user_permissions(context):
    """
    Get all permissions for the current user on current site
    Usage: {% get_user_permissions as permissions %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return {}
    
    if request.user.is_superuser:
        return {'all_permissions': True, 'is_superuser': True}
    
    # Check if user_profile is already in request (from middleware)
    if hasattr(request, 'user_profile'):
        return request.user_profile.get_permissions_summary()
    
    # Fallback: get profile manually
    try:
        current_site = get_current_site(request)
        user_profile = SiteUserProfile.objects.get(
            user=request.user,
            site=current_site
        )
        return user_profile.get_permissions_summary()
    except SiteUserProfile.DoesNotExist:
        return {}

@register.inclusion_tag('portal/rbac/permission_check.html', takes_context=True)
def show_if_permission(context, permission_name):
    """
    Inclusion tag to show/hide content based on permission
    Usage: {% show_if_permission 'can_manage_products' %}...content...{% endshow_if_permission %}
    """
    has_permission = user_has_permission(context, permission_name)
    return {
        'has_permission': has_permission,
        'permission_name': permission_name
    }

@register.filter
def has_perm(user, permission_name):
    """
    Simple filter to check permission
    Usage: {% if user|has_perm:'can_manage_products' %}
    """
    if user.is_superuser:
        return True
    
    # This is a simplified version - in production you'd want to get the site context
    # For now, just return False for non-superusers when used as a filter
    return False
