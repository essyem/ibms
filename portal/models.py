# models.py
from datetime import timezone
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.db.models import Sum
import uuid
from django.utils import timezone   

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer')
    company_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20)
    tax_number = models.CharField(max_length=50, blank=True)
    delivery_address = models.TextField()
    preferred_contact_method = models.CharField(
        max_length=10,
        choices=[('email', 'Email'), ('phone', 'Phone'), ('whatsapp', 'WhatsApp')],
        default='email'
    )

    def __str__(self):
        return f"{self.company_name or self.user.username}"
    pass





class Invoice(models.Model):
    INVOICE_STATUS = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        default=uuid.uuid4  # Temporary unique value
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

    def save(self, *args, **kwargs):
        if not self.invoice_number or len(str(self.invoice_number)) > 36:  # UUID length
            # Generate final invoice number
            last_invoice = Invoice.objects.order_by('-id').first()
            last_num = 0
            if last_invoice and last_invoice.invoice_number:
                try:
                    last_num = int(last_invoice.invoice_number.split('-')[-1])
                except (ValueError, IndexError):
                    pass
            self.invoice_number = f"INV-{timezone.now().year}-{last_num + 1:04d}"
        super().save(*args, **kwargs)
        self.update_totals()  # Ensure totals are updated after save

    def update_totals(self):
        # Calculate subtotal from items
        self.subtotal = self.items.aggregate(
            total=Sum('total')
        )['total'] or 0
        
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

# portal/models.py
class InvoiceItem(models.Model):
    invoice = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'Product', 
        on_delete=models.PROTECT,
        null=True,  # Allow null temporarily
        blank=True  # Allow blank in forms
    )
    quantity = models.PositiveIntegerField(default=1)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        if self.product:
            if not self.selling_price:
                self.selling_price = self.product.selling_price
            self.cost_price = self.product.cost_price
        self.total = self.quantity * self.selling_price
        super().save(*args, **kwargs)
        self.invoice.update_totals()

'''

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    cost_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        editable=False)  # Captured at time of sale
    selling_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        editable=True)  # Editable for discounts
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        if not self.pk:  # New instance
            if not self.selling_price:
                self.selling_price = self.product.selling_price
            self.cost_price = self.product.cost_price
        
        self.total = self.quantity * self.selling_price
        super().save(*args, **kwargs)
        
        # Update parent invoice
        self.invoice.update_totals()

    def __str__(self):
        return f"{self.quantity}x {self.product.name} @ {self.selling_price}"

    def save(self, *args, **kwargs):
        # Auto-capture cost price when first created
        if not self.pk:
            self.cost_price = self.product.cost_price
        
        # Calculate total
        self.total = self.quantity * self.selling_price
        
        super().save(*args, **kwargs)
        
        # Update parent invoice totals
        self.invoice.update_totals()
    '''

    
    


class Review(models.Model):
    RATINGS = [(i, str(i)) for i in range(1, 6)]
    
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=RATINGS)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.product.name} by {self.customer}"

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(
        max_length=50, 
        help_text="Font Awesome icon class (e.g. 'fa-microchip')",
        blank=True,  # Makes the field optional
        default="fa-box"  # Default icon
    )
    
    def __str__(self):
        return self.name

# models.py - update the Product model
class Product(models.Model):
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
    selling_price = models.DecimalField(
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
        if self.cost_price is None or self.selling_price is None or self.cost_price == 0:
            return 0
        return ((self.selling_price - self.cost_price) / self.cost_price) * 100

    def profit_amount(self):
        """Calculate absolute profit amount"""
        if self.cost_price is None or self.selling_price is None:
            return None
        return self.selling_price - self.cost_price
    
    def clean(self):
        if self.cost_price is not None and self.selling_price is not None:
            if self.selling_price < self.cost_price:
                raise ValidationError({
                    'selling_price': "Selling price cannot be less than cost price"
                })
        elif self.cost_price is None:
            raise ValidationError({
                'cost_price': "Cost price is required"
            })
        elif self.selling_price is None:
            raise ValidationError({
                'selling_price': "Selling price is required"
            })
        
    def __str__(self):
        return f"{self.name} ({self.sku}) - {self.category.name}"
    
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    requested_delivery_date = models.DateField(null=True, blank=True)
    special_instructions = models.TextField(null=True, blank=True)

class Order(models.Model):
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


class ProductEnquiry(models.Model):
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
