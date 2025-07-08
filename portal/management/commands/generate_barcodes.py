"""
Management command to generate barcodes for products without them
"""
from django.core.management.base import BaseCommand
from django.db import models
from portal.models import Product
from portal.barcode_utils import BarcodeGenerator


class Command(BaseCommand):
    help = 'Generate barcodes for products that don\'t have SKUs or barcodes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            help='Generate barcodes only for products in this category (by name)',
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually generating barcodes',
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Generate barcodes even for products that already have them',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.HTTP_INFO('🏷️  Barcode Generator for Products')
        )
        self.stdout.write('-' * 50)

        # Build query
        query = models.Q()
        
        if not options['force']:
            # Only products without barcodes
            query &= (models.Q(barcode__isnull=True) | models.Q(barcode=''))

        if options['category']:
            query &= models.Q(category__name__icontains=options['category'])

        products = Product.objects.filter(query).select_related('category')

        if not products.exists():
            self.stdout.write(
                self.style.SUCCESS('✅ No products need barcode generation!')
            )
            return

        self.stdout.write(
            f"Found {products.count()} product(s) that need barcodes:"
        )
        
        for product in products:
            barcode_status = "Has barcode" if product.barcode else "No barcode"
            sku_status = "Has SKU" if product.sku else "No SKU"
            self.stdout.write(
                f"  - {product.name} ({product.category.name}) - {barcode_status}, {sku_status}"
            )

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('\n🔍 DRY RUN - No barcodes were actually generated')
            )
            return

        # Confirm before proceeding
        if not options['force']:
            confirm = input('\nProceed with barcode generation? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('❌ Operation cancelled')
                return

        self.stdout.write('\n🔄 Generating barcodes...')
        
        success_count = 0
        error_count = 0
        errors = []

        for product in products:
            if product.barcode and not options['force']:
                continue
                
            self.stdout.write(f"  Generating for: {product.name}...", ending='')
            
            result = BarcodeGenerator.generate_barcode_for_product(product)
            
            if result['success']:
                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f" ✅ {result['barcode_number']}")
                )
            else:
                error_count += 1
                error_msg = result.get('error', 'Unknown error')
                errors.append(f"{product.name}: {error_msg}")
                self.stdout.write(
                    self.style.ERROR(f" ❌ {error_msg}")
                )

        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'✅ Successfully generated: {success_count} barcode(s)')
        )
        
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed: {error_count} barcode(s)')
            )
            for error in errors:
                self.stdout.write(f"   - {error}")

        if success_count > 0:
            self.stdout.write(
                self.style.HTTP_INFO(
                    f'\n🎉 Barcode generation completed! '
                    f'You can now print labels from the admin interface.'
                )
            )
