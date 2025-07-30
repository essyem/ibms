# portal/management/commands/manage_dashboard_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Manage dashboard and reports access for users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--grant-dashboard',
            type=str,
            help='Grant dashboard access to user (username)',
        )
        parser.add_argument(
            '--grant-reports', 
            type=str,
            help='Grant reports access to user (username)',
        )
        parser.add_argument(
            '--grant-manager',
            type=str,
            help='Grant manager access (both dashboard and reports) to user (username)',
        )
        parser.add_argument(
            '--revoke-access',
            type=str,
            help='Revoke all dashboard/reports access from user (username)',
        )
        parser.add_argument(
            '--list-users',
            action='store_true',
            help='List all users and their dashboard/reports access',
        )
        parser.add_argument(
            '--create-test-user',
            action='store_true',
            help='Create test users for demonstration',
        )

    def handle(self, *args, **options):
        if options['grant_dashboard']:
            self.grant_dashboard_access(options['grant_dashboard'])
        
        if options['grant_reports']:
            self.grant_reports_access(options['grant_reports'])
        
        if options['grant_manager']:
            self.grant_manager_access(options['grant_manager'])
        
        if options['revoke_access']:
            self.revoke_access(options['revoke_access'])
        
        if options['list_users']:
            self.list_users()
        
        if options['create_test_user']:
            self.create_test_users()

    def grant_dashboard_access(self, username):
        """Grant dashboard access to a user"""
        try:
            user = User.objects.get(username=username)
            group = Group.objects.get(name='Dashboard Users')
            user.groups.add(group)
            self.stdout.write(
                self.style.SUCCESS(f'Granted dashboard access to {username}')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} not found')
            )
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Dashboard Users group not found. Run setup_dashboard_access first.')
            )

    def grant_reports_access(self, username):
        """Grant reports access to a user"""
        try:
            user = User.objects.get(username=username)
            group = Group.objects.get(name='Reports Users')
            user.groups.add(group)
            self.stdout.write(
                self.style.SUCCESS(f'Granted reports access to {username}')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} not found')
            )

    def grant_manager_access(self, username):
        """Grant manager access (both dashboard and reports) to a user"""
        try:
            user = User.objects.get(username=username)
            group = Group.objects.get(name='Managers')
            user.groups.add(group)
            self.stdout.write(
                self.style.SUCCESS(f'Granted manager access to {username}')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} not found')
            )

    def revoke_access(self, username):
        """Revoke all dashboard/reports access from a user"""
        try:
            user = User.objects.get(username=username)
            groups = Group.objects.filter(
                name__in=['Dashboard Users', 'Reports Users', 'Managers']
            )
            user.groups.remove(*groups)
            self.stdout.write(
                self.style.SUCCESS(f'Revoked dashboard/reports access from {username}')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} not found')
            )

    def list_users(self):
        """List all users and their dashboard/reports access"""
        self.stdout.write(self.style.SUCCESS('Users and their dashboard/reports access:\n'))
        
        users = User.objects.all().prefetch_related('groups')
        
        for user in users:
            access_type = []
            
            if user.is_superuser:
                access_type.append('SUPERUSER (Full Access)')
            else:
                user_groups = user.groups.values_list('name', flat=True)
                
                if 'Managers' in user_groups:
                    access_type.append('Manager (Dashboard + Reports)')
                else:
                    if 'Dashboard Users' in user_groups:
                        access_type.append('Dashboard Access')
                    if 'Reports Users' in user_groups:
                        access_type.append('Reports Access')
                
                if not access_type and not user.is_superuser:
                    access_type.append('No Access')
            
            status = 'Active' if user.is_active else 'Inactive'
            self.stdout.write(
                f'  {user.username} ({user.email or "no email"}) - {status}: {", ".join(access_type)}'
            )

    def create_test_users(self):
        """Create test users for demonstration"""
        test_users = [
            ('dashboard_user', 'Dashboard Users', 'password123'),
            ('reports_user', 'Reports Users', 'password123'),
            ('manager_user', 'Managers', 'password123'),
        ]
        
        for username, group_name, password in test_users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@trendzqtr.com',
                    'is_staff': True,  # Allow admin access
                    'first_name': username.replace('_', ' ').title(),
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Created test user: {username}')
                )
            else:
                self.stdout.write(f'Test user {username} already exists')
            
            # Add to appropriate group
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
        
        self.stdout.write(
            self.style.SUCCESS(
                '\nTest users created with password: password123\n'
                '- dashboard_user: Only dashboard access\n'
                '- reports_user: Only reports access\n'  
                '- manager_user: Both dashboard and reports access\n'
            )
        )
