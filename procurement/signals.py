from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PurchaseItem
from decimal import Decimal

@receiver(post_save, sender=PurchaseItem)
@receiver(post_delete, sender=PurchaseItem)
def update_purchase_order_totals(sender, instance, **kwargs):
    try:
        if hasattr(instance.purchase_order, 'update_totals'):
            instance.purchase_order.update_totals()
    except Exception:
        # Fallback calculation if there are any issues
        po = instance.purchase_order
        po.subtotal = sum(item.total for item in po.items.all()) or Decimal('0.00')
        # Tax is manually entered, only calculate total
        po.total = po.subtotal + (po.tax or Decimal('0.00'))
        po.save(update_fields=['subtotal', 'total'])