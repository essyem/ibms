# rbac/management/commands/setup_rbac.py
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from rbac.models import SiteRole, SiteUserProfile
from django.db import transaction

class Command(BaseCommand):
    help = 'Setup default RBAC roles and permissions for all sites'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--site-domain',
            type=str,
            help='Setup roles for specific site domain only',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing roles and create new ones',
        )
    
    def handle(self, *args, **options):
        site_domain = options.get('site_domain')
        reset = options.get('reset', False)
        
        if site_domain:
            try:
                sites = [Site.objects.get(domain=site_domain)]
                self.stdout.write(f"Setting up RBAC for site: {site_domain}")
            except Site.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Site with domain '{site_domain}' not found"))
                return
        else:
            sites = Site.objects.all()
            self.stdout.write(f"Setting up RBAC for all sites ({sites.count()} sites)")
        
        with transaction.atomic():
            for site in sites:
                self.setup_site_roles(site, reset)
        
        self.stdout.write(self.style.SUCCESS('RBAC setup completed successfully'))
    
    def setup_site_roles(self, site, reset=False):
        """Setup default roles for a specific site"""
        self.stdout.write(f"\nSetting up roles for: {site.domain}")
        
        if reset:
            SiteRole.objects.filter(site=site).delete()
            self.stdout.write(f"  - Cleared existing roles for {site.domain}")
        
        # Define default roles with their permissions
        default_roles = {
            'Site Administrator': {
                'role_type': 'admin',
                'description': 'Full administrative access to the site',
                'permissions': {
                    'can_view_dashboard': True,
                    'can_manage_products': True,
                    'can_manage_customers': True,
                    'can_manage_orders': True,
                    'can_view_reports': True,
                    'can_manage_users': True,
                    'can_manage_settings': True,
                    'can_access_admin': True,
                    'can_manage_finance': True,
                    'can_manage_procurement': True,
                }
            },
            'Site Manager': {
                'role_type': 'manager',
                'description': 'Management access with limited admin capabilities',
                'permissions': {
                    'can_view_dashboard': True,
                    'can_manage_products': True,
                    'can_manage_customers': True,
                    'can_manage_orders': True,
                    'can_view_reports': True,
                    'can_manage_users': False,
                    'can_manage_settings': False,
                    'can_access_admin': True,
                    'can_manage_finance': False,
                    'can_manage_procurement': True,
                }
            },
            'Inventory Manager': {
                'role_type': 'inventory_manager',
                'description': 'Manages product inventory and procurement',
                'permissions': {
                    'can_view_dashboard': True,
                    'can_manage_products': True,
                    'can_manage_customers': False,
                    'can_manage_orders': True,
                    'can_view_reports': True,
                    'can_manage_users': False,
                    'can_manage_settings': False,
                    'can_access_admin': True,
                    'can_manage_finance': False,
                    'can_manage_procurement': True,
                }
            },
            'Sales Representative': {
                'role_type': 'sales_rep',
                'description': 'Handles customer interactions and orders',
                'permissions': {
                    'can_view_dashboard': True,
                    'can_manage_products': False,
                    'can_manage_customers': True,
                    'can_manage_orders': True,
                    'can_view_reports': True,
                    'can_manage_users': False,
                    'can_manage_settings': False,
                    'can_access_admin': True,
                    'can_manage_finance': False,
                    'can_manage_procurement': False,
                }
            },
            'Customer Service': {
                'role_type': 'customer_service',
                'description': 'Customer support and basic order management',
                'permissions': {
                    'can_view_dashboard': True,
                    'can_manage_products': False,
                    'can_manage_customers': True,
                    'can_manage_orders': True,
                    'can_view_reports': False,
                    'can_manage_users': False,
                    'can_manage_settings': False,
                    'can_access_admin': True,
                    'can_manage_finance': False,
                    'can_manage_procurement': False,
                }
            },
            'Accountant': {
                'role_type': 'accountant',
                'description': 'Financial management and reporting',
                'permissions': {
                    'can_view_dashboard': True,
                    'can_manage_products': False,
                    'can_manage_customers': False,
                    'can_manage_orders': True,
                    'can_view_reports': True,
                    'can_manage_users': False,
                    'can_manage_settings': False,
                    'can_access_admin': True,
                    'can_manage_finance': True,
                    'can_manage_procurement': False,
                }
            },
            'Viewer': {
                'role_type': 'viewer',
                'description': 'Read-only access to basic information',
                'permissions': {
                    'can_view_dashboard': True,
                    'can_manage_products': False,
                    'can_manage_customers': False,
                    'can_manage_orders': False,
                    'can_view_reports': True,
                    'can_manage_users': False,
                    'can_manage_settings': False,
                    'can_access_admin': False,
                    'can_manage_finance': False,
                    'can_manage_procurement': False,
                }
            },
        }
        
        # Create the roles
        for role_name, role_config in default_roles.items():
            role, created = SiteRole.objects.get_or_create(
                site=site,
                name=role_name,
                defaults={
                    'role_type': role_config['role_type'],
                    'description': role_config['description'],
                    **role_config['permissions']
                }
            )
            
            if created:
                self.stdout.write(f"  ✓ Created role: {role_name}")
            else:
                # Update existing role permissions if reset is True
                if reset:
                    for perm, value in role_config['permissions'].items():
                        setattr(role, perm, value)
                    role.description = role_config['description']
                    role.save()
                    self.stdout.write(f"  ✓ Updated role: {role_name}")
                else:
                    self.stdout.write(f"  - Role already exists: {role_name}")
        
        # Create site profiles for existing superusers
        superusers = User.objects.filter(is_superuser=True)
        admin_role = SiteRole.objects.get(site=site, name='Site Administrator')
        
        for superuser in superusers:
            profile, created = SiteUserProfile.objects.get_or_create(
                user=superuser,
                site=site,
                defaults={
                    'role': admin_role,
                    'is_site_active': True,
                    'department': 'Administration'
                }
            )
            if created:
                self.stdout.write(f"  ✓ Created admin profile for superuser: {superuser.username}")
        
        self.stdout.write(f"  Completed setup for {site.domain}")
