from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from portal.models import Product
from procurement.models import PurchaseOrder, PurchaseItem, Supplier
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create a purchase order for all products that don\'t have existing purchase items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reference',
            type=str,
            default='25070101',
            help='Purchase order reference number (default: 25070101)'
        )
        parser.add_argument(
            '--supplier-name',
            type=str,
            default='Initial Inventory Supplier',
            help='Supplier name for the purchase order'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually creating the purchase order'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if purchase order reference already exists'
        )

    def handle(self, *args, **options):
        reference = options['reference']
        supplier_name = options['supplier_name']
        dry_run = options['dry_run']
        force = options['force']

        self.stdout.write(f"Creating purchase order with reference: {reference}")
        self.stdout.write(f"Supplier: {supplier_name}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        # Check if purchase order already exists
        existing_po = PurchaseOrder.objects.filter(reference=reference).first()
        if existing_po and not force:
            self.stdout.write(
                self.style.ERROR(
                    f"Purchase order with reference '{reference}' already exists: {existing_po}. "
                    f"Use --force to recreate or choose a different reference."
                )
            )
            return

        # Get products without purchase items
        products_without_purchase = Product.objects.filter(is_active=True).exclude(
            id__in=PurchaseItem.objects.values_list('product_id', flat=True)
        ).select_related('category')

        product_count = products_without_purchase.count()
        
        if product_count == 0:
            self.stdout.write(
                self.style.SUCCESS("All active products already have purchase orders. Nothing to do.")
            )
            return

        self.stdout.write(f"Found {product_count} products without purchase orders")

        # Show sample products
        self.stdout.write("\nSample products to be added:")
        for product in products_without_purchase[:10]:
            cost_price = product.cost_price if product.cost_price else Decimal('0.00')
            self.stdout.write(
                f"  - {product.name} (SKU: {product.sku}) - Cost: QAR {cost_price}"
            )
        
        if product_count > 10:
            self.stdout.write(f"  ... and {product_count - 10} more products")

        if dry_run:
            total_cost = sum(
                (product.cost_price or Decimal('0.00')) 
                for product in products_without_purchase
            )
            self.stdout.write(f"\nEstimated total cost: QAR {total_cost}")
            self.stdout.write("Run without --dry-run to actually create the purchase order")
            return

        # Confirm before proceeding
        confirm = input(f"\nProceed to create purchase order for {product_count} products? (y/N): ")
        if confirm.lower() != 'y':
            self.stdout.write("Operation cancelled.")
            return

        try:
            with transaction.atomic():
                # Get or create supplier
                supplier, created = Supplier.objects.get_or_create(
                    name=supplier_name,
                    defaults={
                        'contact_person': 'System Generated',
                        'phone': 'N/A',
                        'email': '',
                        'address': 'Initial inventory supplier for existing products',
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(f"Created new supplier: {supplier.name}")
                else:
                    self.stdout.write(f"Using existing supplier: {supplier.name}")

                # Delete existing purchase order if force is used
                if existing_po and force:
                    self.stdout.write(f"Deleting existing purchase order: {existing_po}")
                    existing_po.delete()

                # Create purchase order
                today = timezone.now().date()
                delivery_date = today + timedelta(days=1)  # Next day delivery

                purchase_order = PurchaseOrder.objects.create(
                    supplier=supplier,
                    order_date=today,
                    delivery_date=delivery_date,
                    reference=reference,
                    notes=f"Initial inventory purchase order created on {today.strftime('%Y-%m-%d')} "
                          f"for products without existing purchase history. "
                          f"Contains {product_count} products.",
                    payment_mode='credit',
                    status='received',  # Mark as received since these are existing inventory
                    tax=Decimal('0.00')
                )

                self.stdout.write(f"Created purchase order: {purchase_order}")

                # Create purchase items
                items_created = 0
                total_cost = Decimal('0.00')
                
                for product in products_without_purchase:
                    # Use cost_price as unit_cost, default to 1.00 if not set
                    unit_cost = product.cost_price if product.cost_price else Decimal('1.00')
                    quantity = 1  # Default quantity for initial inventory
                    
                    # Create purchase item
                    PurchaseItem.objects.create(
                        purchase_order=purchase_order,
                        product=product,
                        quantity=quantity,
                        unit_cost=unit_cost
                    )
                    
                    items_created += 1
                    total_cost += unit_cost
                    
                    if items_created % 50 == 0:
                        self.stdout.write(f"  Created {items_created} purchase items...")

                # Update purchase order totals
                purchase_order.update_totals()
                purchase_order.refresh_from_db()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ Successfully created purchase order {reference}:\n"
                        f"  - Supplier: {supplier.name}\n"
                        f"  - Items: {items_created}\n"
                        f"  - Subtotal: QAR {purchase_order.subtotal}\n"
                        f"  - Total: QAR {purchase_order.total}\n"
                        f"  - Status: {purchase_order.get_status_display()}"
                    )
                )

                # Show summary by category
                self.stdout.write("\nSummary by category:")
                from django.db.models import Count
                category_summary = (
                    products_without_purchase
                    .values('category__name')
                    .annotate(count=Count('id'))
                    .order_by('-count')
                )
                
                for item in category_summary:
                    self.stdout.write(f"  - {item['category__name']}: {item['count']} products")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error creating purchase order: {str(e)}")
            )
            raise
