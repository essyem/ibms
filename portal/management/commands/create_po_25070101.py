from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from portal.models import Product
from procurement.models import PurchaseOrder, PurchaseItem, Supplier
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create purchase order 25070101 for all products without existing purchase items'

    def handle(self, *args, **options):
        reference = "25070101"
        supplier_name = "Initial Inventory Supplier"
        
        self.stdout.write(f"Creating purchase order with reference: {reference}")
        
        # Check existing
        existing_po = PurchaseOrder.objects.filter(reference=reference).first()
        if existing_po:
            self.stdout.write(f"Deleting existing PO: {existing_po}")
            existing_po.delete()

        # Get products without purchase items
        products_without_purchase = Product.objects.filter(is_active=True).exclude(
            id__in=PurchaseItem.objects.values_list('product_id', flat=True)
        )

        count = products_without_purchase.count()
        self.stdout.write(f"Found {count} products without purchase orders")

        if count == 0:
            self.stdout.write("No products to add")
            return

        with transaction.atomic():
            # Create supplier
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_name,
                defaults={
                    'contact_person': 'System',
                    'phone': 'N/A',
                    'is_active': True
                }
            )
            
            # Create purchase order
            po = PurchaseOrder.objects.create(
                supplier=supplier,
                order_date=timezone.now().date(),
                delivery_date=timezone.now().date() + timedelta(days=1),
                reference=reference,
                notes=f"Initial inventory for {count} products",
                payment_mode='credit',
                status='received',
                tax=Decimal('0.00')
            )
            
            # Create items
            for product in products_without_purchase:
                unit_cost = product.cost_price or Decimal('1.00')
                PurchaseItem.objects.create(
                    purchase_order=po,
                    product=product,
                    quantity=1,
                    unit_cost=unit_cost
                )
            
            po.update_totals()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created PO {reference} with {count} items, total: QAR {po.total}"
                )
            )
