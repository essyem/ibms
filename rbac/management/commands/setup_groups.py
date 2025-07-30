# rbac/management/commands/setup_groups.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from rbac.models import SiteRole


class Command(BaseCommand):
    help = 'Set up site-specific groups based on roles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--site',
            type=str,
            help='Set up groups for specific site (domain name)',
        )

    def handle(self, *args, **options):
        sites = [Site.objects.get(domain=options['site'])] if options['site'] else Site.objects.all()
        
        for site in sites:
            self.stdout.write(f"\nSetting up groups for site: {site.name} ({site.domain})")
            
            # Get all roles for this site
            roles = SiteRole.objects.filter(site=site)
            
            for role in roles:
                # Create group name with site prefix
                group_name = f"{site.name.lower().replace(' ', '_')}_{role.name.lower().replace(' ', '_')}"
                
                # Create or get the group
                group, created = Group.objects.get_or_create(name=group_name)
                
                if created:
                    self.stdout.write(f"  Created group: {group_name}")
                else:
                    self.stdout.write(f"  Group already exists: {group_name}")
                
                # Clear existing permissions
                group.permissions.clear()
                
                # Add permissions based on role capabilities
                permissions_to_add = []
                
                # Get content types for our models
                portal_ct = ContentType.objects.get(app_label='portal', model='product')
                auth_ct = ContentType.objects.get(app_label='auth', model='user')
                
                # Dashboard access - everyone gets this
                if role.can_view_dashboard:
                    # Add basic view permissions
                    perms = Permission.objects.filter(
                        content_type__app_label='portal',
                        codename__in=['view_product', 'view_customer', 'view_order']
                    )
                    permissions_to_add.extend(perms)
                
                # Product management
                if role.can_manage_products:
                    perms = Permission.objects.filter(
                        content_type__app_label='portal',
                        content_type__model='product'
                    )
                    permissions_to_add.extend(perms)
                
                # Customer management
                if role.can_manage_customers:
                    perms = Permission.objects.filter(
                        content_type__app_label='portal',
                        content_type__model='customer'
                    )
                    permissions_to_add.extend(perms)
                
                # Order management
                if role.can_manage_orders:
                    perms = Permission.objects.filter(
                        content_type__app_label='portal',
                        content_type__model__in=['order', 'invoice']
                    )
                    permissions_to_add.extend(perms)
                
                # User management
                if role.can_manage_users:
                    perms = Permission.objects.filter(
                        content_type__app_label='auth',
                        content_type__model='user'
                    )
                    permissions_to_add.extend(perms)
                
                # Finance management
                if role.can_manage_finance:
                    try:
                        perms = Permission.objects.filter(
                            content_type__app_label='finance'
                        )
                        permissions_to_add.extend(perms)
                    except:
                        pass  # Finance app might not be available
                
                # Procurement management
                if role.can_manage_procurement:
                    try:
                        perms = Permission.objects.filter(
                            content_type__app_label='procurement'
                        )
                        permissions_to_add.extend(perms)
                    except:
                        pass  # Procurement app might not be available
                
                # Add all permissions to the group
                if permissions_to_add:
                    group.permissions.add(*set(permissions_to_add))
                    self.stdout.write(f"    Added {len(set(permissions_to_add))} permissions")
                
        self.stdout.write(self.style.SUCCESS('\nGroups setup completed successfully!'))
