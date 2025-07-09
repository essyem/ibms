"""
Django signals to automatically sync sales and procurement data to finance app
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import datetime

from portal.models import Invoice, InvoiceItem
from procurement.models import PurchaseOrder, PurchasePayment
from .models import FinanceTransaction, Category, InventoryTransaction, FinancialSummary


def get_or_create_finance_category(name, transaction_type, site):
    """Helper function to get or create finance categories"""
    category, created = Category.objects.get_or_create(
        name=name,
        type=transaction_type,
        site=site,
        defaults={'description': f'Auto-created category for {transaction_type}'}
    )
    return category


def get_system_user():
    """Get or create a system user for auto-generated transactions"""
    user, created = User.objects.get_or_create(
        username='system_finance',
        defaults={
            'first_name': 'System',
            'last_name': 'Finance',
            'email': 'system@finance.local',
            'is_active': True,
        }
    )
    return user


@receiver(post_save, sender=Invoice)
def sync_invoice_to_finance(sender, instance, created, **kwargs):
    """Automatically create finance transaction when invoice is saved"""
    if instance.status == 'paid':  # Only sync paid invoices
        # Check if transaction already exists
        existing = FinanceTransaction.objects.filter(
            source_type='invoice',
            source_id=instance.id,
            site=instance.site
        ).first()
        
        if not existing:
            # Get or create sales category
            category = get_or_create_finance_category('Sales Revenue', 'sale', instance.site)
            
            # Create finance transaction
            transaction = FinanceTransaction.objects.create(
                type='sale_receipt',
                category=category,
                amount=instance.grand_total,
                date=instance.date,
                description=f'Sales Invoice #{instance.invoice_number} - {instance.customer.full_name if instance.customer else "Walk-in"}',
                payment_method=instance.payment_mode,
                reference=instance.invoice_number,
                source_type='invoice',
                source_id=instance.id,
                auto_generated=True,
                created_by=get_system_user(),
                site=instance.site
            )
            
            # Create inventory transactions for each item
            for item in instance.items.all():
                InventoryTransaction.objects.create(
                    product=item.product,
                    type='sale',
                    quantity=-item.quantity,  # Negative for sales (stock reduction)
                    unit_cost=item.product.cost_price,
                    unit_price=item.unit_price,
                    total_cost=item.product.cost_price * item.quantity,
                    total_revenue=item.subtotal(),
                    invoice=instance,
                    date=datetime.combine(instance.date, datetime.min.time()),
                    notes=f'Sale via Invoice #{instance.invoice_number}',
                    site=instance.site
                )
        
        # Update financial summary
        update_financial_summary(instance.site, instance.date.year, instance.date.month)


@receiver(post_save, sender=PurchaseOrder)
def sync_purchase_order_to_finance(sender, instance, created, **kwargs):
    """Automatically create finance transaction when purchase order is completed"""
    if instance.status == 'received':  # Only sync received orders
        # Check if transaction already exists
        existing = FinanceTransaction.objects.filter(
            source_type='purchase_order',
            source_id=instance.id,
            site=instance.site
        ).first()
        
        if not existing:
            # Get or create purchase category
            category = get_or_create_finance_category('Inventory Purchase', 'purchase', instance.site)
            
            # Create finance transaction
            transaction = FinanceTransaction.objects.create(
                type='purchase',
                category=category,
                amount=instance.total,
                date=instance.order_date,
                description=f'Purchase Order #{instance.reference} - {instance.supplier.name}',
                payment_method=instance.payment_mode,
                reference=instance.reference,
                source_type='purchase_order',
                source_id=instance.id,
                auto_generated=True,
                created_by=get_system_user(),
                site=instance.site
            )
            
            # Create inventory transactions for each item
            for item in instance.items.all():
                InventoryTransaction.objects.create(
                    product=item.product,
                    type='purchase',
                    quantity=item.quantity,  # Positive for purchases (stock increase)
                    unit_cost=item.unit_cost,
                    unit_price=item.product.unit_price,
                    total_cost=item.total,
                    purchase_order=instance,
                    date=datetime.combine(instance.order_date, datetime.min.time()),
                    notes=f'Purchase via PO #{instance.reference}',
                    site=instance.site
                )
        
        # Update financial summary
        update_financial_summary(instance.site, instance.order_date.year, instance.order_date.month)


@receiver(post_save, sender=PurchasePayment)
def sync_purchase_payment_to_finance(sender, instance, created, **kwargs):
    """Automatically create finance transaction when purchase payment is made"""
    if instance.amount > 0:  # Only sync actual payments
        # Check if transaction already exists
        existing = FinanceTransaction.objects.filter(
            source_type='purchase_payment',
            source_id=instance.id,
            site=instance.purchase_order.site
        ).first()
        
        if not existing:
            # Get or create payment category
            category = get_or_create_finance_category('Purchase Payments', 'expense', instance.purchase_order.site)
            
            # Create finance transaction
            transaction = FinanceTransaction.objects.create(
                type='purchase_payment',
                category=category,
                amount=instance.amount,
                date=instance.payment_date,
                description=f'Payment for PO #{instance.purchase_order.reference} - {instance.purchase_order.supplier.name}',
                payment_method=instance.payment_method,
                reference=instance.reference or f'PAY-{instance.purchase_order.reference}',
                source_type='purchase_payment',
                source_id=instance.id,
                auto_generated=True,
                created_by=get_system_user(),
                site=instance.purchase_order.site
            )
        
        # Update financial summary
        update_financial_summary(
            instance.purchase_order.site, 
            instance.payment_date.year, 
            instance.payment_date.month
        )


def update_financial_summary(site, year, month):
    """Update or create financial summary for the given month"""
    from django.db.models import Sum, Count, Avg
    
    summary, created = FinancialSummary.objects.get_or_create(
        site=site,
        year=year,
        month=month,
        defaults={
            'total_sales': Decimal('0'),
            'total_invoices': 0,
            'total_purchases': Decimal('0'),
            'total_purchase_orders': 0,
            'total_purchase_payments': Decimal('0'),
            'gross_profit': Decimal('0'),
            'profit_margin': Decimal('0'),
            'cash_inflow': Decimal('0'),
            'cash_outflow': Decimal('0'),
            'net_cash_flow': Decimal('0'),
        }
    )
    
    # Calculate sales metrics
    from portal.models import Invoice
    sales_data = Invoice.objects.filter(
        site=site,
        date__year=year,
        date__month=month,
        status='paid'
    ).aggregate(
        total=Sum('grand_total'),
        count=Count('id'),
        avg=Avg('grand_total')
    )
    
    summary.total_sales = sales_data['total'] or Decimal('0')
    summary.total_invoices = sales_data['count'] or 0
    summary.average_sale_value = sales_data['avg'] or Decimal('0')
    
    # Calculate purchase metrics
    purchase_data = PurchaseOrder.objects.filter(
        site=site,
        order_date__year=year,
        order_date__month=month,
        status='received'
    ).aggregate(
        total=Sum('total'),
        count=Count('id')
    )
    
    summary.total_purchases = purchase_data['total'] or Decimal('0')
    summary.total_purchase_orders = purchase_data['count'] or 0
    
    # Calculate payment metrics
    payment_data = PurchasePayment.objects.filter(
        purchase_order__site=site,
        payment_date__year=year,
        payment_date__month=month
    ).aggregate(total=Sum('amount'))
    
    summary.total_purchase_payments = payment_data['total'] or Decimal('0')
    
    # Calculate profit metrics
    inventory_profit = InventoryTransaction.objects.filter(
        site=site,
        date__year=year,
        date__month=month,
        type='sale'
    ).aggregate(
        revenue=Sum('total_revenue'),
        cost=Sum('total_cost')
    )
    
    total_revenue = inventory_profit['revenue'] or Decimal('0')
    total_cost = inventory_profit['cost'] or Decimal('0')
    
    summary.gross_profit = total_revenue - total_cost
    if total_revenue > 0:
        summary.profit_margin = (summary.gross_profit / total_revenue) * 100
    else:
        summary.profit_margin = Decimal('0')
    
    # Calculate cash flow
    summary.cash_inflow = summary.total_sales
    summary.cash_outflow = summary.total_purchase_payments
    summary.net_cash_flow = summary.cash_inflow - summary.cash_outflow
    
    summary.save()


# Clean up signals for deletions
@receiver(post_delete, sender=Invoice)
def cleanup_invoice_finance_data(sender, instance, **kwargs):
    """Clean up finance data when invoice is deleted"""
    FinanceTransaction.objects.filter(
        source_type='invoice',
        source_id=instance.id,
        site=instance.site
    ).delete()
    
    InventoryTransaction.objects.filter(
        invoice=instance
    ).delete()


@receiver(post_delete, sender=PurchaseOrder)
def cleanup_purchase_order_finance_data(sender, instance, **kwargs):
    """Clean up finance data when purchase order is deleted"""
    FinanceTransaction.objects.filter(
        source_type='purchase_order',
        source_id=instance.id,
        site=instance.site
    ).delete()
    
    InventoryTransaction.objects.filter(
        purchase_order=instance
    ).delete()


@receiver(post_delete, sender=PurchasePayment)
def cleanup_purchase_payment_finance_data(sender, instance, **kwargs):
    """Clean up finance data when purchase payment is deleted"""
    FinanceTransaction.objects.filter(
        source_type='purchase_payment',
        source_id=instance.id
    ).delete()
