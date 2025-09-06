from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Create dummy data for Al Malika site (wrapper for populate_almalika_data)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            default='almalika.trendzqtr.com',
            help='Domain of the Al Malika site'
        )

    def handle(self, *args, **options):
        domain = options['domain']
        
        self.stdout.write(
            self.style.WARNING(
                f'🔄 This command is a wrapper for populate_almalika_data.\n'
                f'   Target domain: {domain}'
            )
        )
        
        # Check if site exists
        try:
            site = Site.objects.get(domain=domain)
            self.stdout.write(f'✅ Found site: {site.name} ({site.domain})')
        except Site.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Site with domain "{domain}" not found.\n'
                    f'   Run: python manage.py setup_sites first.'
                )
            )
            return
        
        # Call the actual populate command
        self.stdout.write('🚀 Calling populate_almalika_data...\n')
        call_command('populate_almalika_data')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n✅ Dummy data creation completed!\n'
                f'   Use this site domain in your browser: {domain}'
            )
        )
