from django.core.management.base import BaseCommand
from portal.models import Product
from procurement.models import PurchaseOrder, PurchaseItem
from django.db import transaction
from decimal import Decimal

class Command(BaseCommand):
    help = 'Synchronize procurement purchases with portal inventory'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--purchase-order',
            type=str,
            help='Specific purchase order reference to process'
        )
        parser.add_argument(
            '--update-stock',
            action='store_true',
            help='Update product stock quantities'
        )
        parser.add_argument(
            '--update-cost',
            action='store_true',
            help='Update product cost prices based on latest purchases'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔄 Procurement-Portal Inventory Sync')
        )
        
        if options['purchase_order']:
            self.process_specific_po(options['purchase_order'], options)
        else:
            self.process_all_received_pos(options)
    
    def process_specific_po(self, po_ref, options):
        """Process a specific purchase order"""
        try:
            po = PurchaseOrder.objects.get(reference=po_ref)
            self.stdout.write(f"📦 Processing PO: {po.reference}")
            
            if po.status != 'received':
                self.stdout.write(
                    self.style.WARNING(f"⚠️  PO {po.reference} status is '{po.status}', not 'received'")
                )
                if not options['dry_run']:
                    response = input("Continue anyway? (y/n): ")
                    if response.lower() != 'y':
                        return
            
            self.update_inventory_from_po(po, options)
            
        except PurchaseOrder.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Purchase Order {po_ref} not found")
            )
    
    def process_all_received_pos(self, options):
        """Process all received purchase orders"""
        received_pos = PurchaseOrder.objects.filter(status='received')
        
        self.stdout.write(f"📋 Found {received_pos.count()} received purchase orders")
        
        for po in received_pos:
            self.stdout.write(f"📦 Processing PO: {po.reference}")
            self.update_inventory_from_po(po, options)
    
    def update_inventory_from_po(self, po, options):
        """Update inventory based on purchase order items"""
        
        with transaction.atomic():
            for item in po.items.all():
                product = item.product
                
                self.stdout.write(f"   📄 Product: {product.name}")
                self.stdout.write(f"      Current Stock: {product.stock}")
                self.stdout.write(f"      Current Cost: QAR {product.cost_price}")
                
                updates_made = []
                
                # Update stock if requested
                if options['update_stock']:
                    new_stock = product.stock + item.quantity
                    if not options['dry_run']:
                        product.stock = new_stock
                    updates_made.append(f"Stock: {product.stock} → {new_stock}")
                
                # Update cost price if requested
                if options['update_cost']:
                    if not options['dry_run']:
                        product.cost_price = item.unit_cost
                    updates_made.append(f"Cost: QAR {product.cost_price} → QAR {item.unit_cost}")
                
                if updates_made:
                    if options['dry_run']:
                        self.stdout.write(f"      🔍 Would update: {', '.join(updates_made)}")
                    else:
                        product.save()
                        self.stdout.write(f"      ✅ Updated: {', '.join(updates_made)}")
                else:
                    self.stdout.write(f"      ℹ️  No updates needed")
    
    def calculate_average_cost(self, product):
        """Calculate average cost from all purchase items"""
        purchase_items = PurchaseItem.objects.filter(product=product)
        
        if not purchase_items.exists():
            return product.cost_price
        
        total_cost = sum(item.total for item in purchase_items)
        total_quantity = sum(item.quantity for item in purchase_items)
        
        if total_quantity > 0:
            return total_cost / total_quantity
        
        return product.cost_price
