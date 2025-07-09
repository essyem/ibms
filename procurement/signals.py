from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import PurchaseItem, PurchaseOrder
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

@receiver(post_save, sender=PurchaseOrder)
def update_product_cost_prices(sender, instance, **kwargs):
    """
    Update product cost prices when purchase order status changes to 'received'
    This ensures that cost prices reflect the latest purchase costs
    """
    if instance.status == 'received':
        # Update cost prices for all items in this purchase order
        for item in instance.items.all():
            product = item.product
            # Update the product's cost price to the unit cost from purchase
            if product.cost_price != item.unit_cost:
                product.cost_price = item.unit_cost
                product.save(update_fields=['cost_price'])

@receiver(post_save, sender=PurchaseItem)
def update_product_stock_and_cost(sender, instance, created, **kwargs):
    """
    Update product stock and cost price when purchase item is saved
    Only update if the purchase order is received
    """
    if instance.purchase_order.status == 'received':
        product = instance.product
        
        # Update stock (add purchased quantity)
        if created:  # Only add stock if this is a new item
            product.stock += instance.quantity
        
        # Update cost price to latest purchase cost
        if product.cost_price != instance.unit_cost:
            product.cost_price = instance.unit_cost
            
        product.save(update_fields=['stock', 'cost_price'])