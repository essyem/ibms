from django.core.management.base import BaseCommand
from portal.models import Invoice, InvoiceItem
from django.utils import timezone
import uuid

class Command(BaseCommand):
    help = 'Fix invoice numbers and unit prices'

    def handle(self, *args, **options):
        # Fix invoices with UUID numbers (36 characters with dashes)
        uuid_invoices = Invoice.objects.filter(
            invoice_number__regex=r'^[a-f0-9-]{36}$'
        ) | Invoice.objects.filter(
            invoice_number__contains='-',
            invoice_number__iregex=r'^[a-f0-9-]+$'
        )
        
        self.stdout.write(f'Found {uuid_invoices.count()} invoices with UUID-like numbers')
        
        for invoice in uuid_invoices:
            old_number = invoice.invoice_number
            # Generate new invoice number
            now = invoice.date or timezone.now().date()
            date_part = now.strftime('%y%m%d')
            
            # Get count for that date
            existing_count = Invoice.objects.filter(
                date=now,
                invoice_number__startswith=date_part
            ).exclude(id=invoice.id).count()
            
            hex_suffix = f"{existing_count + 1:03X}"
            new_number = f"{date_part}{hex_suffix}"
            
            # Ensure uniqueness
            counter = existing_count + 1
            while Invoice.objects.filter(invoice_number=new_number).exists():
                counter += 1
                hex_suffix = f"{counter:03X}"
                new_number = f"{date_part}{hex_suffix}"
                if counter > 4095:  # 0xFFF
                    counter = 0
            
            invoice.invoice_number = new_number
            invoice.save()
            self.stdout.write(f'Updated invoice {invoice.id}: {old_number} -> {new_number}')
        
        # Fix missing unit prices
        items_missing_price = InvoiceItem.objects.filter(
            unit_price__isnull=True
        ) | InvoiceItem.objects.filter(unit_price=0)
        
        self.stdout.write(f'Found {items_missing_price.count()} items with missing unit prices')
        
        fixed_items = 0
        for item in items_missing_price:
            if item.product and item.product.unit_price:
                item.unit_price = item.product.unit_price
                item.save()
                fixed_items += 1
                self.stdout.write(f'Fixed price for {item.product.name}: {item.unit_price}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully fixed {fixed_items} item prices')
        )
