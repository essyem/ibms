# rbac/models.py
from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.sites.models import Site
from django.utils import timezone

# Multi-tenant manager for site-based filtering
class SiteManager(models.Manager):
    def get_queryset(self):
        from django.contrib.sites.models import Site
        from django.contrib.sites.shortcuts import get_current_site
        from django.conf import settings
        
        # Get current site ID from settings or default to 1
        current_site_id = getattr(settings, 'SITE_ID', 1)
        return super().get_queryset().filter(site_id=current_site_id)
    
    def all_sites(self):
        """Get objects from all sites (for admin use)"""
        return super().get_queryset()

# Abstract base model for multi-tenant models
class SiteModel(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, default=1)
    
    objects = SiteManager()
    all_objects = models.Manager()  # Access to all sites data
    
    class Meta:
        abstract = True

# RBAC Models for Multi-tenant System
class SiteRole(models.Model):
    """Defines roles available for each site"""
    ROLE_TYPES = [
        ('admin', 'Site Administrator'),
        ('manager', 'Site Manager'),
        ('staff', 'Staff Member'),
        ('viewer', 'Viewer'),
        ('customer_service', 'Customer Service'),
        ('inventory_manager', 'Inventory Manager'),
        ('sales_rep', 'Sales Representative'),
        ('accountant', 'Accountant'),
        ('custom', 'Custom Role'),
    ]
    
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    role_type = models.CharField(max_length=20, choices=ROLE_TYPES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Permission flags for quick access
    can_view_dashboard = models.BooleanField(default=True)
    can_manage_products = models.BooleanField(default=False)
    can_manage_customers = models.BooleanField(default=False)
    can_manage_orders = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_manage_settings = models.BooleanField(default=False)
    can_access_admin = models.BooleanField(default=False)
    can_manage_finance = models.BooleanField(default=False)
    can_manage_procurement = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['site', 'name']
        verbose_name = 'Site Role'
        verbose_name_plural = 'Site Roles'
        ordering = ['site', 'name']
    
    def __str__(self):
        return f"{self.site.domain} - {self.name}"

class SiteUserProfile(SiteModel):
    """Extended user profile with site-specific information"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(SiteRole, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_site_active = models.BooleanField(default=True)
    last_login_site = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional permissions (overrides)
    permission_overrides = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ['user', 'site']
        verbose_name = 'Site User Profile'
        verbose_name_plural = 'Site User Profiles'
        ordering = ['site', 'user__username']
    
    def __str__(self):
        return f"{self.user.username} @ {self.site.domain}"
    
    def has_permission(self, permission_name):
        """Check if user has specific permission on this site"""
        # Superuser always has all permissions
        if self.user.is_superuser:
            return True
            
        # Check role permissions first
        if self.role:
            role_permission = getattr(self.role, permission_name, False)
            if role_permission:
                return True
        
        # Check permission overrides
        if permission_name in self.permission_overrides:
            return self.permission_overrides[permission_name]
            
        return False
    
    def get_permissions_summary(self):
        """Get a summary of all permissions for this user on this site"""
        permissions = {}
        
        if self.user.is_superuser:
            return {
                'all_permissions': True,
                'is_superuser': True
            }
        
        if self.role:
            # Get role permissions
            role_fields = [f for f in self.role._meta.fields if f.name.startswith('can_')]
            for field in role_fields:
                permissions[field.name] = getattr(self.role, field.name, False)
        
        # Apply overrides
        permissions.update(self.permission_overrides)
        
        return permissions

class SitePermissionLog(models.Model):
    """Log permission changes for audit trail"""
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='permission_changes_made')
    action = models.CharField(max_length=100)  # 'role_assigned', 'permission_granted', etc.
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Permission Log'
        verbose_name_plural = 'Permission Logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.action} @ {self.site.domain}"
