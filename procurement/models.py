from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.contrib.sites.models import Site
from portal.models import SiteManager

# Base model with site field for procurement
class ProcurementSiteModel(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, default=1, related_name='%(app_label)s_%(class)s_set')
    
    objects = SiteManager()
    all_objects = models.Manager()  # Access to all sites data
    
    class Meta:
        abstract = True

class Supplier(ProcurementSiteModel):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['site', 'name']
        ordering = ['site', 'name']
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'

    def __str__(self):
        return f"{self.site.domain}: {self.name}"

class PurchaseOrder(ProcurementSiteModel):
    PAYMENT_MODES = [
        ('cash', 'Cash'),
        ('credit', 'Credit'),
        ('bank', 'Bank Transfer'),
        ('split', 'Split Payment'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    order_date = models.DateField()
    delivery_date = models.DateField()
    reference = models.CharField(max_length=50, unique=True)
    notes = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODES, default='credit')
    payment_due = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ], default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['site', 'reference']
        ordering = ['-created_at', 'site']
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'

    def update_totals(self):
        items = self.items.all()
        self.subtotal = sum(item.total for item in items) or Decimal('0.00')
        # Tax is manually entered, only calculate total
        self.total = self.subtotal + (self.tax or Decimal('0.00'))
        self.save(update_fields=['subtotal', 'total']) 

    def __str__(self):
        return f"{self.site.domain}: PO-{self.reference}"

class PurchaseItem(models.Model):  # Note: This doesn't inherit from SiteModel directly but gets site from PurchaseOrder
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('portal.Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.total = Decimal(str(self.quantity)) * self.unit_cost
        super().save(*args, **kwargs)
        # Use try-except to handle any method call issues
        try:
            self.purchase_order.update_totals()
        except AttributeError:
            # Fallback calculation if update_totals method is not available
            po = self.purchase_order
            po.subtotal = sum(item.total for item in po.items.all()) or Decimal('0.00')
            # Tax is manually entered, only calculate total
            po.total = po.subtotal + (po.tax or Decimal('0.00'))
            po.save(update_fields=['subtotal', 'total'])
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def delete(self, *args, **kwargs):
        purchase_order = self.purchase_order
        super().delete(*args, **kwargs)
        try:
            purchase_order.update_totals()
        except AttributeError:
            # Fallback calculation
            purchase_order.subtotal = sum(item.total for item in purchase_order.items.all()) or Decimal('0.00')
            # Tax is manually entered, only calculate total
            purchase_order.total = purchase_order.subtotal + (purchase_order.tax or Decimal('0.00'))
            purchase_order.save(update_fields=['subtotal', 'total'])

class PurchasePayment(models.Model):
    """Enhanced payment tracking for purchase orders"""
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('transfer', 'Bank Transfer'),
        ('card', 'Credit Card'),
        ('other', 'Other'),
    ]
    
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Payment amount")
    amount_due = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total amount due for this purchase order")
    payment_date = models.DateField()
    due_date = models.DateField(blank=True, null=True, help_text="Payment due date")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='transfer')
    reference = models.CharField(max_length=100, blank=True, help_text="Bank reference, cheque number, etc.")
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Purchase Payment'
        verbose_name_plural = 'Purchase Payments'

    def save(self, *args, **kwargs):
        # Auto-set amount_due from purchase order if not set
        if not self.amount_due and self.purchase_order:
            self.amount_due = self.purchase_order.total
            
        # Auto-calculate status based on payment amount
        if self.amount == 0:
            self.status = 'pending'
        elif self.amount < self.amount_due:
            self.status = 'partial'
        else:
            self.status = 'paid'
            
        # Check if overdue
        from django.utils import timezone
        if self.due_date and self.due_date < timezone.now().date() and self.status != 'paid':
            self.status = 'overdue'
            
        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        amount_due = self.amount_due or 0
        amount = self.amount or 0
        return amount_due - amount

    @property
    def payment_percentage(self):
        amount_due = self.amount_due or 0
        amount = self.amount or 0
        if amount_due == 0:
            return 0
        return (amount / amount_due) * 100

    def __str__(self):
        return f"Payment for PO-{self.purchase_order.reference} - {self.get_status_display()}"