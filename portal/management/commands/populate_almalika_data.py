from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from portal.models import Category, Product, Customer
from decimal import Decimal

class Command(BaseCommand):
    help = 'Populate sample data for Al Malika site'

    def handle(self, *args, **options):
        self.stdout.write('🌟 Populating sample data for Al Malika site...')
        
        # Get Al Malika site
        try:
            almalika_site = Site.objects.get(domain='almalika.trendzqtr.com')
        except Site.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Al Malika site not found. Run setup_sites command first.')
            )
            return
        
        # Create categories for Al Malika
        categories_data = [
            {'name': 'Electronics', 'description': 'Electronic devices and gadgets', 'icon': 'fa-laptop'},
            {'name': 'Accessories', 'description': 'Electronic accessories and parts', 'icon': 'fa-microchip'},
            {'name': 'Services', 'description': 'Technical services and support', 'icon': 'fa-tools'},
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                site=almalika_site,
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon']
                }
            )
            if created:
                self.stdout.write(f'✅ Created category: {category.name}')
            else:
                self.stdout.write(f'⚠️ Category already exists: {category.name}')
        
        # Create sample products for Al Malika
        electronics_cat = Category.objects.get(site=almalika_site, name='Electronics')
        accessories_cat = Category.objects.get(site=almalika_site, name='Accessories')
        
        products_data = [
            {
                'category': electronics_cat,
                'name': 'Premium Laptop Stand',
                'sku': 'AM-LAPTOP-001',
                'description': 'Adjustable aluminum laptop stand',
                'cost_price': Decimal('45.00'),
                'selling_price': Decimal('65.00'),
                'stock': 25,
                'warranty_period': 12,
            },
            {
                'category': accessories_cat,
                'name': 'Wireless Mouse Pad',
                'sku': 'AM-MOUSE-001',
                'description': 'Ergonomic wireless charging mouse pad',
                'cost_price': Decimal('15.00'),
                'selling_price': Decimal('25.00'),
                'stock': 50,
                'warranty_period': 6,
            },
            {
                'category': electronics_cat,
                'name': 'USB-C Hub',
                'sku': 'AM-HUB-001',
                'description': '7-in-1 USB-C hub with HDMI',
                'cost_price': Decimal('30.00'),
                'selling_price': Decimal('45.00'),
                'stock': 20,
                'warranty_period': 24,
            },
        ]
        
        for prod_data in products_data:
            product, created = Product.objects.get_or_create(
                site=almalika_site,
                sku=prod_data['sku'],
                defaults=prod_data
            )
            if created:
                self.stdout.write(f'✅ Created product: {product.name}')
            else:
                self.stdout.write(f'⚠️ Product already exists: {product.name}')
        
        # Create sample customers for Al Malika
        customers_data = [
            {
                'full_name': 'Ahmed Al-Rashid',
                'phone': '+974-1234-5678',
                'company_name': 'Al-Rashid Technologies',
                'preferred_contact_method': 'phone',
            },
            {
                'full_name': 'Fatima Al-Zahra',
                'phone': '+974-9876-5432',
                'company_name': 'Al-Zahra Consulting',
                'preferred_contact_method': 'email',
            },
        ]
        
        for cust_data in customers_data:
            customer, created = Customer.objects.get_or_create(
                site=almalika_site,
                phone=cust_data['phone'],
                defaults=cust_data
            )
            if created:
                self.stdout.write(f'✅ Created customer: {customer.full_name}')
            else:
                self.stdout.write(f'⚠️ Customer already exists: {customer.full_name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Sample data population completed for Al Malika site!'
            )
        )
        
        # Summary
        self.stdout.write('\n📊 Al Malika Site Data Summary:')
        self.stdout.write(f'Categories: {Category.objects.filter(site=almalika_site).count()}')
        self.stdout.write(f'Products: {Product.objects.filter(site=almalika_site).count()}')
        self.stdout.write(f'Customers: {Customer.objects.filter(site=almalika_site).count()}')
