from django.core.management.base import BaseCommand
from django.db.models import Avg
from decimal import Decimal
from portal.models import Product
from procurement.models import PurchaseItem, PurchaseOrder

class Command(BaseCommand):
    help = 'Sync product cost prices with latest purchase costs and fix price issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--update-method',
            choices=['latest', 'average', 'lowest'],
            default='latest',
            help='Method to calculate cost price: latest (most recent purchase), average (average of all purchases), lowest (minimum purchase cost)',
        )
        parser.add_argument(
            '--received-only',
            action='store_true',
            help='Only consider purchase orders with received status',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        update_method = options['update_method']
        received_only = options['received_only']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get all products
        products = Product.objects.all()
        
        updated_count = 0
        errors = []
        
        for product in products:
            try:
                # Get purchase items for this product
                purchase_items = PurchaseItem.objects.filter(product=product)
                
                if received_only:
                    purchase_items = purchase_items.filter(purchase_order__status='received')
                
                if not purchase_items.exists():
                    self.stdout.write(
                        self.style.WARNING(f'No purchase data found for {product.name} (SKU: {product.sku})')
                    )
                    continue
                
                # Calculate new cost price based on method
                if update_method == 'latest':
                    # Get the most recent purchase item
                    latest_item = purchase_items.order_by('-purchase_order__created_at').first()
                    new_cost_price = latest_item.unit_cost if latest_item else product.cost_price
                    
                elif update_method == 'average':
                    # Calculate average cost price
                    avg_cost = purchase_items.aggregate(avg_cost=Avg('unit_cost'))['avg_cost']
                    new_cost_price = Decimal(str(avg_cost)).quantize(Decimal('0.01')) if avg_cost else product.cost_price
                    
                elif update_method == 'lowest':
                    # Get the lowest cost price
                    lowest_item = purchase_items.order_by('unit_cost').first()
                    new_cost_price = lowest_item.unit_cost if lowest_item else product.cost_price
                
                # Check if cost price needs updating
                if product.cost_price != new_cost_price:
                    old_cost_price = product.cost_price
                    
                    if not dry_run:
                        product.cost_price = new_cost_price
                        product.save(update_fields=['cost_price'])
                    
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated {product.name} (SKU: {product.sku}): '
                            f'Cost Price: QAR {old_cost_price} → QAR {new_cost_price}'
                        )
                    )
                    
                    # Check if selling price is still appropriate
                    if product.unit_price < new_cost_price:
                        self.stdout.write(
                            self.style.ERROR(
                                f'WARNING: {product.name} selling price (QAR {product.unit_price}) '
                                f'is less than new cost price (QAR {new_cost_price})'
                            )
                        )
                
            except Exception as e:
                error_msg = f'Error processing {product.name} (SKU: {product.sku}): {str(e)}'
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(error_msg))
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(f'Products processed: {products.count()}')
        self.stdout.write(f'Products updated: {updated_count}')
        self.stdout.write(f'Errors: {len(errors)}')
        
        if errors:
            self.stdout.write('\nErrors encountered:')
            for error in errors:
                self.stdout.write(self.style.ERROR(error))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN completed - No actual changes made'))
        else:
            self.stdout.write(self.style.SUCCESS('\nCost price sync completed successfully!'))
        
        # Additional recommendations
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.HTTP_INFO('Recommendations:'))
        self.stdout.write('1. Review products with selling price less than cost price')
        self.stdout.write('2. Ensure all purchase orders are marked as "received" when goods arrive')
        self.stdout.write('3. Run this command periodically to keep cost prices updated')
        self.stdout.write('4. Consider setting up automated signals for real-time updates')
