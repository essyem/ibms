# models.py
from datetime import timezone
from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.sites.models import Site
from django.core.validators import MinValueValidator
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.db.models import Sum
import uuid
from django.utils import timezone
import random   
import string
from django.utils.text import gettext_lazy as _

# Multi-tenant manager for site-based filtering
class SiteManager(models.Manager):
    def get_queryset(self):
        from django.contrib.sites.models import Site
        from django.contrib.sites.shortcuts import get_current_site
        from django.conf import settings
        
        # Get current site ID from settings or default to 1
        current_site_id = getattr(settings, 'SITE_ID', 1)
        return super().get_queryset().filter(site_id=current_site_id)
    
    def all_sites(self):
        """Get objects from all sites (for admin use)"""
        return super().get_queryset()

# Abstract base model for multi-tenant models
class SiteModel(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, default=1)
    
    objects = SiteManager()
    all_objects = models.Manager()  # Access to all sites data
    
    class Meta:
        abstract = True

class Customer(SiteModel):
    customer_id = models.CharField(
        max_length=10,
        unique=True,
        editable=False
    )
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    company_name = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    tax_number = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    preferred_contact_method = models.CharField(
        max_length=10,
        choices=[('email', 'Email'), ('phone', 'Phone'), ('whatsapp', 'WhatsApp')],
        default='phone'
    )

    def save(self, *args, **kwargs):
        if not self.customer_id:
            self.customer_id = self.generate_customer_id()
        super().save(*args, **kwargs)

    @classmethod
    def generate_customer_id(cls):
        """Generate ID in format: YYMMXXXXXX"""
        now = timezone.now()
        date_part = f"{now.strftime('%y')}{now.strftime('%m')}"
        
        # Generate until unique
        while True:
            letters_part = ''.join(random.choices(string.ascii_uppercase, k=2))
            numbers_part = ''.join(random.choices(string.digits, k=4))
            customer_id = f"{date_part}{letters_part}{numbers_part}"
            if not cls.objects.filter(customer_id=customer_id).exists():
                return customer_id
    
    def __str__(self):

        return f"{self.full_name} ({self.phone})"

    class Meta:
        permissions = [
            ("view_dashboard", "Can view dashboard"),
            ("view_reports", "Can view reports"),
            ("access_analytics", "Can access analytics API"),
        ]


class Invoice(SiteModel):
    INVOICE_STATUS = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_MODES = [
        ('cash', 'Cash'),
        ('credit', 'Credit'),
        ('pos', 'POS'),
        ('split', 'Split Payment'),
    ]
    
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name='Customer'
    )

    payment_mode = models.CharField(
        max_length=10,
        choices=PAYMENT_MODES,
        default='cash'
    )
    
    split_details = models.JSONField(
        blank=True, 
        null=True,
        help_text="Details of split payment (e.g., {'cash': 100, 'pos': 50})"
    )
    
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True
    )
    date = models.DateField(auto_now_add=True, editable=False)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='draft')
    notes = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_type = models.CharField(
        max_length=10,
        choices=[('percent', 'Percentage'), ('amount', 'Fixed Amount')],
        default='percent',
        blank=True
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        editable=False
    )
    grand_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        editable=False
    )
    
    # Split payment fields
    cash_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        blank=True,
        help_text="Cash amount for split payments"
    )
    pos_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        blank=True,
        help_text="POS/Card amount for split payments"
    )
    other_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        blank=True,
        help_text="Other payment method amount"
    )
    other_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="Description of other payment method"
    )

    def save(self, *args, **kwargs):
        # Assign walk-in customer if missing
        if not self.customer:
            self.customer, _ = Customer.objects.get_or_create(
                full_name="Walk-in Customer",
                defaults={'phone': ''}
            )

        # Generate improved invoice number if needed
        if not self.invoice_number:
            from django.utils import timezone
            import random
            
            now = timezone.now()
            # Format: YYMMDD + 3-digit hex (000-FFF)
            date_part = now.strftime('%y%m%d')  # e.g., "250704" for July 4, 2025
            
            # Get last invoice for today to increment hex counter
            today_invoices = Invoice.objects.filter(
                date=now.date(),
                invoice_number__startswith=date_part
            ).order_by('-invoice_number')
            
            if today_invoices.exists():
                # Extract hex part and increment
                last_invoice = today_invoices.first()
                try:
                    hex_part = last_invoice.invoice_number[-3:]  # Last 3 characters
                    next_num = int(hex_part, 16) + 1  # Convert from hex to int and increment
                    if next_num > 0xFFF:  # Reset if exceeds 3-digit hex
                        next_num = 0
                except (ValueError, IndexError):
                    next_num = 1
            else:
                next_num = 1
            
            # Format as 3-digit hex (uppercase)
            hex_suffix = f"{next_num:03X}"
            self.invoice_number = f"{date_part}{hex_suffix}"

        super().save(*args, **kwargs)
        self.update_totals()


    def update_totals(self):
        from decimal import Decimal
        # Calculate subtotal from items
        subtotal_amount = Decimal('0.00')
        for item in self.items.all():
            subtotal_amount += item.subtotal()
        
        self.subtotal = subtotal_amount
        
        # Calculate total before discount
        self.total = self.subtotal + self.tax
        
        # Calculate discount
        if self.discount_type == 'percent':
            self.discount_amount = (self.subtotal + self.tax) * (self.discount_value / 100)
        else:
            self.discount_amount = min(self.discount_value, self.subtotal + self.tax)
        
        # Calculate grand total
        self.grand_total = (self.subtotal + self.tax) - self.discount_amount
        
        # Update only the calculated fields
        update_fields = ['subtotal', 'total', 'discount_amount', 'grand_total']
        if self.pk:  # Only update if already saved
            Invoice.objects.filter(pk=self.pk).update(
                **{field: getattr(self, field) for field in update_fields}
            )

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.customer}"

    # Set default customer for existing invoices
    # (This logic should be run outside the model class, e.g., in a migration or management command)
    # default_customer, _ = Customer.objects.get_or_create(
    #     full_name="Walk-in Customer",
    #     defaults={'phone': ''}
    # )
    # Invoice.objects.filter(customer__isnull=True).update(customer=default_customer)

class InvoiceItem(SiteModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Auto-set unit_price from product if not provided
        if self.product and not self.unit_price:
            self.unit_price = self.product.unit_price
        super().save(*args, **kwargs)
    
    def subtotal(self):
        from decimal import Decimal
        if self.unit_price is None:
            return Decimal('0.00')
        return Decimal(str(self.quantity)) * self.unit_price
    
    def __str__(self):
        return f"{self.product.name} ({self.quantity} x {self.unit_price})"


class Category(SiteModel):
    ICON_CHOICES = [
        ('fa-desktop', 'Computer Hardware'),
        ('fa-microchip', 'Electronic Components'),
        ('fa-network-wired', 'Networking'),
        ('fa-tools', 'Tools'),
        ('fa-print', 'Printers & Scanners'),
        ('fa-mobile-alt', 'Mobile Devices'),
        ('fa-shield-alt', 'Security'),
        ('fa-server', 'Servers'),
        ('fa-hdd', 'Storage'),
        ('fa-headset', 'Peripherals'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

# models.py - update the Product model
class Product(SiteModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="The price the company pays for the product",
        validators=[MinValueValidator(0)]
    )
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="The price the customer pays for the product",
        validators=[MinValueValidator(0)]
    )
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='products/', blank=True, null=True, default='None')
    is_active = models.BooleanField(default=True)
    warranty_period = models.PositiveIntegerField(help_text="In months")
    barcode = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True,     
        null=True,
        help_text="Barcode number (UPC, EAN, etc.)"
    )
    # models.py - update the profit calculation methods
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if self.cost_price is None or self.unit_price is None or self.cost_price == 0:
            return 0
        return ((self.unit_price - self.cost_price) / self.cost_price) * 100

    def profit_amount(self):
        """Calculate absolute profit amount"""
        if self.cost_price is None or self.unit_price is None:
            return None
        return self.unit_price - self.cost_price

    def clean(self):
        if self.cost_price is not None and self.unit_price is not None:
            if self.unit_price < self.cost_price:
                raise ValidationError({
                    'unit_price': "Unit price cannot be less than cost price"
                })
        elif self.cost_price is None:
            raise ValidationError({
                'cost_price': "Cost price is required"
            })
        elif self.unit_price is None:
            raise ValidationError({
                'unit_price': "Unit price is required"
            })
        
    def __str__(self):
        return f"{self.name} ({self.sku}) - {self.category.name}"


class Cart(SiteModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(SiteModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    requested_delivery_date = models.DateField(null=True, blank=True)
    special_instructions = models.TextField(null=True, blank=True)

class Order(SiteModel):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20, unique=True)
    items = models.ManyToManyField(CartItem)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_status = models.BooleanField(default=False)
    delivery_address = models.TextField()
    preferred_contact = models.CharField(max_length=100)

class ProductEnquiry(SiteModel):
    PRODUCT_CHOICES = [
        ('hardware', 'IT Hardware'),
        ('repair', 'Chip-Level Repair'),
        ('amc', 'AMC Services'),
        ('software', 'Custom Software'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    product_interest = models.CharField(max_length=20, choices=PRODUCT_CHOICES, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_contacted = models.BooleanField(default=False)

    def __str__(self):
        return f"Enquiry from {self.name} - {self.subject}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.is_contacted:  # Only send for new enquiries
            send_mail(
                f'New Product Enquiry: {self.subject}',
                f"""You have a new enquiry from {self.name} ({self.company}):

                Product Interest: {self.get_product_interest_display()}
                Message: {self.message}

                Contact them at: {self.email} or {self.phone}
                """,
                'noreply@trendzqtr.com',
                ['sales@trendzqtr.com'],
                fail_silently=True,
            )

# class Review(SiteModel):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
#     comment = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     
#     class Meta:
#         unique_together = ('product', 'user')


