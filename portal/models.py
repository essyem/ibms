# models.py
from datetime import timezone
from django.db import models, transaction
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
    status = models.CharField(max_length=20, choices=INVOICE_STATUS)
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
        if not self.invoice_number or self.invoice_number in ['Auto-generated', '']:
            print(f"🔍 MODEL SAVE: Generating invoice number (current: {self.invoice_number})")
            # Define date_part at the start
            date_part = timezone.now().strftime('%Y%m%d')  # YYYYMMDD format
        
            try:
                with transaction.atomic():
                    # Get the highest invoice number for today
                    today_invoices = Invoice.objects.filter(
                        invoice_number__startswith=date_part
                    ).order_by('-invoice_number')
                
                    if today_invoices.exists():
                        last_num = int(today_invoices.first().invoice_number[-2:])  # Get last 2 digits
                        next_num = last_num + 1
                    else:
                        next_num = 1
                
                    # Ensure we don't exceed 99 invoices per day
                    if next_num > 99:
                        raise ValueError("Maximum daily invoice limit (99) reached")
                
                    self.invoice_number = f"{date_part}{next_num:02d}"
                    print(f"🔍 MODEL SAVE: Generated invoice number: {self.invoice_number}")
                
            except Exception as e:
                # Fallback mechanism - ensure date_part is available
                fallback_num = random.randint(1, 99)
                self.invoice_number = f"{date_part}{fallback_num:02d}F"  # F for fallback
                print(f"⚠️ Used fallback invoice number: {self.invoice_number}")
            
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

    def clean(self):
        print(f"🔍 MODEL: clean() called with invoice_number: {repr(self.invoice_number)}")
        if self.invoice_number and self.invoice_number not in ['Auto-generated', '']:
            if len(self.invoice_number) not in (10, 11):  # 10 for normal, 11 for fallback (with 'F')
                print(f"🔍 MODEL: Invalid length - {len(self.invoice_number)}")
                raise ValidationError("Invoice number must be 10 digits (YYYYMMDDNN)")
            if not self.invoice_number[:8].isdigit():
                print(f"🔍 MODEL: First 8 chars not digits - {self.invoice_number[:8]}")
                raise ValidationError("First 8 characters must be digits (YYYYMMDD)")
        print(f"🔍 MODEL: Validation passed")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['invoice_number'],
                name='unique_invoice_number'
            )
        ]

    def save(self, *args, **kwargs):
        print(f"Model save - incoming status: {self.status}")
        
        # Ensure discount_value is never null
        if self.discount_value is None:
            self.discount_value = 0
            print(f"DEBUG: Set discount_value from None to 0")
        
        super().save(*args, **kwargs)
        print(f"Model save - after save status: {self.status}")

    
   

class InvoiceItem(SiteModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    use_product_price = models.BooleanField(default=True, 
                                          help_text="If True, uses product's unit price. If False, allows custom price.")
    
    def save(self, *args, **kwargs):
        # Auto-set unit_price from product only if use_product_price is True and no custom price provided
        if self.product and self.use_product_price and not self.unit_price:
            self.unit_price = self.product.unit_price
        # If use_product_price is False, keep whatever unit_price was set manually
        super().save(*args, **kwargs)
    
    def subtotal(self):
        from decimal import Decimal
        if self.unit_price is None:
            return Decimal('0.00')
        return Decimal(str(self.quantity)) * self.unit_price
    
    def __str__(self):
        return f"{self.product.name} ({self.quantity} x {self.unit_price})"


class SoldItem(SiteModel):
    """
    Tracks items sold through paid invoices without reducing master inventory stock.
    This allows for sales reporting while keeping product stock separate.
    """
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='sold_items')
    product_name = models.CharField(max_length=200, help_text="Product name at time of sale")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_sold = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, 
                               help_text="Reference to original product (may be null if product deleted)")
    
    # Additional fields for better tracking
    product_sku = models.CharField(max_length=100, blank=True, null=True)
    category_name = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['-date_sold']
        verbose_name = "Sold Item"
        verbose_name_plural = "Sold Items"
    
    def subtotal(self):
        from decimal import Decimal
        return Decimal(str(self.quantity)) * self.unit_price
    
    def __str__(self):
        return f"{self.product_name} - {self.quantity} units sold on {self.date_sold.strftime('%Y-%m-%d')}"


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
    # Optional Arabic translations for product name and description
    name_ar = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("Name (Arabic)"))
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    description_ar = models.TextField(blank=True, null=True, verbose_name=_("Description (Arabic)"))
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, help_text="For anonymous users")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Ensure one cart per user or session
        constraints = [
            models.UniqueConstraint(
                fields=['user'], 
                condition=models.Q(user__isnull=False),
                name='unique_cart_per_user'
            ),
            models.UniqueConstraint(
                fields=['session_key'], 
                condition=models.Q(session_key__isnull=False),
                name='unique_cart_per_session'
            ),
        ]
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous cart {self.session_key}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.cartitem_set.all())
    
    @property
    def total_amount(self):
        return sum(item.quantity * item.product.unit_price for item in self.cartitem_set.all())

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


