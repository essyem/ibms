# portal/management/commands/setup_dashboard_access.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from portal.models import Customer

class Command(BaseCommand):
    help = 'Setup user groups and permissions for dashboard and reports access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-groups',
            action='store_true',
            help='Create Dashboard Users and Reports Users groups',
        )
        parser.add_argument(
            '--list-permissions',
            action='store_true',
            help='List all available dashboard/reports permissions',
        )

    def handle(self, *args, **options):
        if options['create_groups']:
            self.create_groups()
        
        if options['list_permissions']:
            self.list_permissions()
        
        if not options['create_groups'] and not options['list_permissions']:
            self.stdout.write(
                self.style.WARNING(
                    'Use --create-groups to create user groups or --list-permissions to see available permissions'
                )
            )

    def create_groups(self):
        """Create user groups with appropriate permissions"""
        
        # Get or create permissions
        content_type = ContentType.objects.get_for_model(Customer)
        
        dashboard_perm, _ = Permission.objects.get_or_create(
            codename='view_dashboard',
            name='Can view dashboard',
            content_type=content_type,
        )
        
        reports_perm, _ = Permission.objects.get_or_create(
            codename='view_reports', 
            name='Can view reports',
            content_type=content_type,
        )
        
        analytics_perm, _ = Permission.objects.get_or_create(
            codename='access_analytics',
            name='Can access analytics API',
            content_type=content_type,
        )

        # Create Dashboard Users group
        dashboard_group, created = Group.objects.get_or_create(name='Dashboard Users')
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created "Dashboard Users" group')
            )
        else:
            self.stdout.write('Dashboard Users group already exists')
            
        dashboard_group.permissions.add(dashboard_perm, analytics_perm)
        
        # Create Reports Users group  
        reports_group, created = Group.objects.get_or_create(name='Reports Users')
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created "Reports Users" group')
            )
        else:
            self.stdout.write('Reports Users group already exists')
            
        reports_group.permissions.add(reports_perm, analytics_perm)
        
        # Create Manager group (full access)
        manager_group, created = Group.objects.get_or_create(name='Managers')
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created "Managers" group')
            )
        else:
            self.stdout.write('Managers group already exists')
            
        manager_group.permissions.add(dashboard_perm, reports_perm, analytics_perm)
        
        self.stdout.write(
            self.style.SUCCESS(
                '\nGroups created successfully!\n'
                'Dashboard Users: Can access dashboard and analytics\n'
                'Reports Users: Can access reports and analytics\n'  
                'Managers: Can access both dashboard and reports\n'
            )
        )

    def list_permissions(self):
        """List all dashboard-related permissions"""
        self.stdout.write(self.style.SUCCESS('Available Dashboard/Reports Permissions:'))
        
        content_type = ContentType.objects.get_for_model(Customer)
        permissions = Permission.objects.filter(
            content_type=content_type,
            codename__in=['view_dashboard', 'view_reports', 'access_analytics']
        )
        
        for perm in permissions:
            self.stdout.write(f'  - {perm.codename}: {perm.name}')
            
        self.stdout.write(self.style.SUCCESS('\nAvailable Groups:'))
        groups = Group.objects.filter(
            name__in=['Dashboard Users', 'Reports Users', 'Managers']
        )
        
        for group in groups:
            perms = ', '.join([p.codename for p in group.permissions.all()])
            self.stdout.write(f'  - {group.name}: {perms}')
