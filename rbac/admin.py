# rbac/admin.py
from django.contrib import admin
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from .models import SiteRole, SiteUserProfile, SitePermissionLog

# Unregister the default User and Group admin if they're registered
try:
    admin.site.unregister(User)
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

@admin.register(SiteRole)
class SiteRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'role_type', 'is_active', 'created_at']
    list_filter = ['role_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    exclude = ('site',)  # Hide site field for simplicity
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('site', 'name', 'role_type', 'description', 'is_active')
        }),
        ('Dashboard & Basic Access', {
            'fields': ('can_view_dashboard',)
        }),
        ('Product Management', {
            'fields': ('can_manage_products',)
        }),
        ('Customer Management', {
            'fields': ('can_manage_customers',)
        }),
        ('Order Management', {
            'fields': ('can_manage_orders',)
        }),
        ('Reporting', {
            'fields': ('can_view_reports',)
        }),
        ('User Management', {
            'fields': ('can_manage_users',)
        }),
        ('System Settings', {
            'fields': ('can_manage_settings',)
        }),
        ('Admin Access', {
            'fields': ('can_access_admin',)
        }),
        ('Financial Management', {
            'fields': ('can_manage_finance',)
        }),
        ('Procurement', {
            'fields': ('can_manage_procurement',)
        }),
    )
    
    def get_queryset(self, request):
        """Always show all objects for superusers, even if no site is set."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # No filtering for superusers
        # Filter roles by current site for non-superusers
        current_site = get_current_site(request)
        return qs.filter(site=current_site)

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return super().has_module_permission(request)

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return super().has_add_permission(request)

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return super().has_view_permission(request, obj)

@admin.register(SiteUserProfile)
class SiteUserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department', 'is_site_active', 'last_login_site']
    list_filter = ['role', 'is_site_active', 'department', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_id', 'department']
    ordering = ['user__username']
    raw_id_fields = ['user']
    exclude = ('site',)  # Hide site field for simplicity
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'site', 'role')
        }),
        ('Profile Details', {
            'fields': ('department', 'employee_id', 'phone')
        }),
        ('Access Control', {
            'fields': ('is_site_active',)
        }),
        ('Permission Overrides', {
            'fields': ('permission_overrides',),
            'classes': ('collapse',),
            'description': 'JSON format for specific permission overrides'
        }),
        ('Activity', {
            'fields': ('last_login_site',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['last_login_site', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Always show all objects for superusers, even if no site is set."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # No filtering for superusers
        # Filter profiles by current site for non-superusers
        current_site = get_current_site(request)
        return qs.filter(site=current_site)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Limit role choices to current site"""
        if db_field.name == "role" and not request.user.is_superuser:
            current_site = get_current_site(request)
            kwargs["queryset"] = SiteRole.objects.filter(site=current_site, is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(SitePermissionLog)
class SitePermissionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'site', 'action', 'changed_by', 'timestamp', 'ip_address']
    list_filter = ['site', 'action', 'timestamp']
    search_fields = ['user__username', 'changed_by__username', 'action']
    ordering = ['-timestamp']
    readonly_fields = ['site', 'user', 'changed_by', 'action', 'old_value', 'new_value', 'timestamp', 'ip_address', 'user_agent']
    
    def has_add_permission(self, request):
        return False  # Logs should only be created programmatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs should be immutable
    
    def get_queryset(self, request):
        """Always show all objects for superusers, even if no site is set."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # No filtering for superusers
        # Filter logs by current site for non-superusers
        current_site = get_current_site(request)
        return qs.filter(site=current_site)

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return super().has_module_permission(request)

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return super().has_add_permission(request)

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return super().has_view_permission(request, obj)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with site-based filtering for non-superusers"""
    
    def get_queryset(self, request):
        """Always show all objects for superusers, even if no site is set."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # No filtering for superusers
        # Filter users by current site for non-superusers
        current_site = get_current_site(request)
        return qs.filter(siteuserprofile__site=current_site).distinct()
    
    def get_readonly_fields(self, request, obj=None):
        """Make sensitive fields readonly for non-superusers"""
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            readonly_fields.extend(['is_superuser', 'user_permissions'])
        return readonly_fields

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return super().has_module_permission(request)

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return super().has_add_permission(request)

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return super().has_view_permission(request, obj)

@admin.register(Group)
class GroupAdmin(BaseGroupAdmin):
    """Custom Group admin with site-based filtering for non-superusers"""
    
    def get_queryset(self, request):
        """Always show all objects for superusers, even if no site is set."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # No filtering for superusers
        # Filter groups by current site for non-superusers
        current_site = get_current_site(request)
        site_prefix = current_site.name.lower().replace(' ', '_')
        return qs.filter(name__icontains=site_prefix)

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        return super().has_module_permission(request)

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        return super().has_add_permission(request)

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return super().has_view_permission(request, obj)
