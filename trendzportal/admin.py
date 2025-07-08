from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site

# Multi-tenant Admin Base Classes
class SiteAdminMixin:
    """
    Mixin to add site-based filtering to admin classes
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # No filtering for superusers
        current_site = get_current_site(request)
        return qs.filter(site=current_site)
    
    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:  # Only set site on creation for non-superusers
            current_site = get_current_site(request)
            obj.site = current_site
        super().save_model(request, obj, form, change)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filter foreign key choices by current site
        if hasattr(db_field.related_model, 'site') and not request.user.is_superuser:
            current_site = get_current_site(request)
            kwargs["queryset"] = db_field.related_model.objects.filter(site=current_site)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Default admin site configuration
admin.site.site_header = "Trendz Trading Administration"
admin.site.site_title = "Trendz Admin Portal"
admin.site.index_title = "Welcome to Trendz Admin"