# rbac/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from .models import SiteRole, SiteUserProfile

class SiteRoleForm(forms.ModelForm):
    class Meta:
        model = SiteRole
        fields = [
            'name', 'role_type', 'description', 'is_active',
            'can_view_dashboard', 'can_manage_products', 'can_manage_customers',
            'can_manage_orders', 'can_view_reports', 'can_manage_users',
            'can_manage_settings', 'can_access_admin', 'can_manage_finance',
            'can_manage_procurement'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'role_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_dashboard': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_products': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_customers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_orders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_reports': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_users': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_settings': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_access_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_finance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_procurement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SiteUserProfileForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select a user to create a profile for"
    )
    
    class Meta:
        model = SiteUserProfile
        fields = [
            'user', 'role', 'department', 'employee_id', 
            'phone', 'is_site_active'
        ]
        
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_site_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        site = kwargs.pop('site', None)
        super().__init__(*args, **kwargs)
        
        if site:
            # Filter roles to current site only
            self.fields['role'].queryset = SiteRole.objects.filter(
                site=site, 
                is_active=True
            )
            
            # Filter users to those who don't already have a profile on this site
            existing_profiles = SiteUserProfile.objects.filter(site=site).values_list('user_id', flat=True)
            
            # If we're editing an existing profile, include the current user
            if self.instance and self.instance.pk:
                existing_profiles = existing_profiles.exclude(pk=self.instance.pk)
            
            self.fields['user'].queryset = User.objects.exclude(id__in=existing_profiles)

class UserPermissionOverrideForm(forms.Form):
    """Form for managing individual permission overrides"""
    PERMISSION_CHOICES = [
        ('can_view_dashboard', 'View Dashboard'),
        ('can_manage_products', 'Manage Products'),
        ('can_manage_customers', 'Manage Customers'),
        ('can_manage_orders', 'Manage Orders'),
        ('can_view_reports', 'View Reports'),
        ('can_manage_users', 'Manage Users'),
        ('can_manage_settings', 'Manage Settings'),
        ('can_access_admin', 'Access Admin'),
        ('can_manage_finance', 'Manage Finance'),
        ('can_manage_procurement', 'Manage Procurement'),
    ]
    
    def __init__(self, *args, **kwargs):
        user_profile = kwargs.pop('user_profile', None)
        super().__init__(*args, **kwargs)
        
        if user_profile:
            # Create fields for each permission
            for perm_key, perm_label in self.PERMISSION_CHOICES:
                # Get current value (from role or override)
                current_value = user_profile.has_permission(perm_key)
                role_value = getattr(user_profile.role, perm_key, False) if user_profile.role else False
                override_value = user_profile.permission_overrides.get(perm_key)
                
                # Create a choice field for each permission
                choices = [
                    ('inherit', f'Inherit from role ({role_value})'),
                    ('true', 'Grant'),
                    ('false', 'Deny'),
                ]
                
                if override_value is None:
                    initial = 'inherit'
                elif override_value:
                    initial = 'true'
                else:
                    initial = 'false'
                
                self.fields[perm_key] = forms.ChoiceField(
                    choices=choices,
                    initial=initial,
                    label=perm_label,
                    widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
                    required=False
                )
    
    def save(self, user_profile):
        """Save the permission overrides"""
        overrides = {}
        
        for perm_key, _ in self.PERMISSION_CHOICES:
            value = self.cleaned_data[perm_key]
            if value == 'true':
                overrides[perm_key] = True
            elif value == 'false':
                overrides[perm_key] = False
            # If 'inherit', don't add to overrides (use role default)
        
        user_profile.permission_overrides = overrides
        user_profile.save()
        return user_profile
