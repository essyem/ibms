# portal/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Invoice, InvoiceItem, SoldItem
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Invoice)
def handle_invoice_status_change(sender, instance, created, **kwargs):
    """
    Signal to handle invoice status changes.
    When an invoice status changes to 'paid', create SoldItem records.
    """
    if not created:  # Only for updates, not new creations
        # Check if status changed to 'paid'
        if instance.status == 'paid':
            # Check if we already have sold items for this invoice
            existing_sold_items = SoldItem.objects.filter(invoice=instance).exists()
            
            if not existing_sold_items:
                logger.info(f"📦 Invoice {instance.invoice_number} marked as PAID - Creating sold items")
                create_sold_items_from_invoice(instance)
            else:
                logger.info(f"📦 Invoice {instance.invoice_number} already has sold items recorded")

def create_sold_items_from_invoice(invoice):
    """
    Create SoldItem records from an invoice's items.
    This tracks what was sold without affecting product stock.
    """
    sold_items_created = 0
    
    for item in invoice.items.all():
        try:
            sold_item = SoldItem.objects.create(
                invoice=invoice,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price=item.unit_price or item.product.unit_price,
                product=item.product,
                product_sku=item.product.sku if hasattr(item.product, 'sku') else '',
                category_name=item.product.category.name if item.product.category else '',
                date_sold=invoice.date
            )
            sold_items_created += 1
            logger.info(f"✅ Created sold item: {sold_item.product_name} x {sold_item.quantity}")
            
        except Exception as e:
            logger.error(f"❌ Error creating sold item for {item.product.name}: {str(e)}")
    
    logger.info(f"📈 Total sold items created for invoice {invoice.invoice_number}: {sold_items_created}")

@receiver(pre_save, sender=Invoice)
def track_invoice_status_change(sender, instance, **kwargs):
    """
    Track when invoice status is about to change to provide better logging.
    """
    if instance.pk:  # Only for existing instances
        try:
            old_instance = Invoice.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                logger.info(f"🔄 Invoice {instance.invoice_number} status changing from '{old_instance.status}' to '{instance.status}'")
        except Invoice.DoesNotExist:
            pass