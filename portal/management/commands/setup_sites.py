from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Setup multi-tenant sites for TRENDZ and Al Malika'

    def handle(self, *args, **options):
        self.stdout.write('🏗️ Setting up multi-tenant sites...')
        
        # Update existing site to TRENDZ
        try:
            trendz_site = Site.objects.get(id=1)
            trendz_site.domain = 'portal.trendzqtr.com'
            trendz_site.name = 'TRENDZ Trading & Services'
            trendz_site.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Updated TRENDZ site: {trendz_site.domain}')
            )
        except Site.DoesNotExist:
            trendz_site = Site.objects.create(
                id=1,
                domain='portal.trendzqtr.com',
                name='TRENDZ Trading & Services'
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created TRENDZ site: {trendz_site.domain}')
            )
        
        # Create Al Malika site
        almalika_site, created = Site.objects.get_or_create(
            domain='almalika.trendzqtr.com',
            defaults={'name': 'Al Malika Trading & Services'}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created Al Malika site: {almalika_site.domain} (ID: {almalika_site.id})')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Al Malika site already exists: {almalika_site.domain} (ID: {almalika_site.id})')
            )
        
        # Display all sites
        self.stdout.write('\n📋 All configured sites:')
        for site in Site.objects.all():
            self.stdout.write(f'  ID: {site.id} | Domain: {site.domain} | Name: {site.name}')
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Multi-tenant sites setup complete!')
        )
