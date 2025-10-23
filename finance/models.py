# finance/models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from portal.models import SiteManager

# Base model with site field
class FinanceSiteModel(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, default=1, related_name='%(app_label)s_%(class)s_set')
    
    objects = SiteManager()
    all_objects = models.Manager()  # Access to all sites data
    
    class Meta:
        abstract = True

class Category(FinanceSiteModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type_choices = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('expense', 'Expense'),
    ]
    type = models.CharField(max_length=10, choices=type_choices)
    
    class Meta:
        unique_together = ['site', 'name', 'type']
        verbose_name_plural = 'Finance Categories'
        ordering = ['site', 'type', 'name']
    
    def __str__(self):
        return f"{self.site.domain}: {self.get_type_display()}: {self.name}"

class FinanceTransaction(FinanceSiteModel):
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('purchase_payment', 'Purchase Payment'),
        ('sale', 'Sale'),
        ('sale_receipt', 'Sale Receipt'),
        ('expense', 'Expense'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('credit', 'Credit'),
        ('pos', 'POS'),
        ('bank', 'Bank Transfer'),
        ('transfer', 'Transfer'),
        ('card', 'Credit Card'),
        ('other', 'Other'),
    ]
    
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='bank')
    reference = models.CharField(max_length=50, blank=True)
    recurring = models.BooleanField(default=False)
    frequency = models.CharField(max_length=10, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ], blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    document = models.FileField(upload_to='finance_documents/', blank=True, null=True)
    
    # Auto-sync fields for ERP integration
    auto_generated = models.BooleanField(default=False, help_text="True if auto-generated from procurement/sales")
    source_type = models.CharField(max_length=20, blank=True, help_text="Source model type (invoice, purchase_order, etc.)")
    source_id = models.PositiveIntegerField(blank=True, null=True, help_text="Source model ID")
    
    class Meta:
        ordering = ['-date', 'site']
        verbose_name = 'Finance Transaction'
        verbose_name_plural = 'Finance Transactions'
    
    def __str__(self):
        return f"{self.site.domain}: {self.get_type_display()} - QAR {self.amount}"


class FinancialSummary(FinanceSiteModel):
    """Monthly/Yearly financial summary for business intelligence"""
    year = models.IntegerField()
    month = models.IntegerField()
    
    # Sales metrics
    total_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_invoices = models.IntegerField(default=0)
    average_sale_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Purchase metrics
    total_purchases = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_purchase_orders = models.IntegerField(default=0)
    total_purchase_payments = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Profit metrics
    gross_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    
    # Cash flow metrics
    cash_inflow = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash_outflow = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_cash_flow = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['site', 'year', 'month']
        ordering = ['-year', '-month', 'site']
        verbose_name = 'Financial Summary'
        verbose_name_plural = 'Financial Summaries'
    
    def __str__(self):
        return f"{self.site.domain}: {self.year}-{self.month:02d} Summary"


class InventoryTransaction(FinanceSiteModel):
    """Track inventory movements for cost analysis and profit calculations"""
    TRANSACTION_TYPES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
    ]
    
    product = models.ForeignKey('portal.Product', on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()  # Positive for inbound, negative for outbound
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Source tracking
    invoice = models.ForeignKey('portal.Invoice', on_delete=models.CASCADE, null=True, blank=True)
    purchase_order = models.ForeignKey('procurement.PurchaseOrder', on_delete=models.CASCADE, null=True, blank=True)
    
    date = models.DateTimeField()
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date', 'site']
        verbose_name = 'Inventory Transaction'
        verbose_name_plural = 'Inventory Transactions'
    
    def profit(self):
        """Calculate profit for sales transactions"""
        if self.total_revenue and self.total_cost:
            return self.total_revenue - self.total_cost
        return 0
    
    def __str__(self):
        return f"{self.site.domain}: {self.product.name} - {self.type} ({self.quantity})"


class DailyRevenue(FinanceSiteModel):
    """Daily revenue tracking with automated calculations"""
    date = models.DateField(unique=True)
    
    # Manual entry fields
    daily_cash_sales = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Manual entry: Cash sales for the day"
    )
    daily_pos_sales = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Manual entry: POS/Card sales for the day"
    )
    daily_service_revenue = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Manual entry: Service revenue for the day"
    )
    daily_purchase = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Manual entry: Purchase expenses for the day"
    )
    
    # Auto-calculated field
    daily_revenue = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Auto-calculated: Cash Sales + POS Sales + Service Revenue - Purchase"
    )
    
    # Additional tracking fields
    notes = models.TextField(blank=True, help_text="Daily notes or comments")
    entered_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Print tracking
    printed_count = models.IntegerField(default=0, help_text="Number of times printed")
    last_printed_at = models.DateTimeField(null=True, blank=True)
    last_printed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True,
        related_name='daily_revenue_prints'
    )
    
    class Meta:
        ordering = ['-date', 'site']
        unique_together = ['site', 'date']
        verbose_name = 'Daily Revenue'
        verbose_name_plural = 'Daily Revenues'
    
    def save(self, *args, **kwargs):
        """Auto-calculate daily revenue on save"""
        self.calculate_daily_revenue()
        super().save(*args, **kwargs)
    
    def calculate_daily_revenue(self):
        """Calculate daily revenue: Cash + POS + Service - Purchase"""
        self.daily_revenue = (
            self.daily_cash_sales + 
            self.daily_pos_sales + 
            self.daily_service_revenue - 
            self.daily_purchase
        )
        return self.daily_revenue
    
    def total_sales(self):
        """Total sales (Cash + POS + Service)"""
        return self.daily_cash_sales + self.daily_pos_sales + self.daily_service_revenue
    
    def net_profit_margin(self):
        """Calculate profit margin percentage"""
        total_sales = self.total_sales()
        if total_sales > 0:
            return (self.daily_revenue / total_sales) * 100
        return 0
    
    def mark_printed(self, user):
        """Mark as printed and update tracking"""
        from django.utils import timezone
        self.printed_count += 1
        self.last_printed_at = timezone.now()
        self.last_printed_by = user
        self.save(update_fields=['printed_count', 'last_printed_at', 'last_printed_by'])
    
    def __str__(self):
        return f"{self.site.domain}: {self.date} - QAR {self.daily_revenue:,.2f}"