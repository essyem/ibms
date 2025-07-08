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
        ('sale', 'Sale'),
        ('expense', 'Expense'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('card', 'Credit Card'),
        ('other', 'Other'),
    ]
    
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
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
    
    class Meta:
        ordering = ['-date', 'site']
        verbose_name = 'Finance Transaction'
        verbose_name_plural = 'Finance Transactions'
    
    def __str__(self):
        return f"{self.site.domain}: {self.get_type_display()} - {self.category}: {self.amount} ({self.date})"