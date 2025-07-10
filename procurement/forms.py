from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import Supplier, PurchaseOrder, PurchaseItem, PurchasePayment
from portal.models import Product

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class PurchaseOrderForm(forms.ModelForm):
    """Enhanced form for PurchaseOrder"""
    
    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_due': forms.DateInput(attrs={'type': 'date'}),
            'tax': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_reference(self):
        """Ensure reference is unique"""
        reference = self.cleaned_data.get('reference')
        
        if reference:
            existing = PurchaseOrder.objects.filter(reference=reference)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(f"Purchase order with reference '{reference}' already exists.")
        
        return reference

class PurchaseItemForm(forms.ModelForm):
    """Enhanced form for PurchaseItem with better product selection and duplicate prevention"""
    
    class Meta:
        model = PurchaseItem
        fields = ['product', 'quantity', 'unit_cost']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': '1', 'class': 'quantity-input'}),
            'unit_cost': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'unit-cost-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Enhance product queryset with better search capabilities
        self.fields['product'].queryset = Product.objects.select_related('category').filter(is_active=True)
        
        # Add helpful text to fields
        self.fields['product'].help_text = "Search by product name, SKU, barcode, or category"
        self.fields['quantity'].help_text = "Minimum quantity: 1"
        self.fields['unit_cost'].help_text = "Cost per unit in QAR"
        
        # Set initial unit cost based on product cost price if available
        # Only do this if instance exists, has a product, and no unit_cost is set
        if (self.instance and self.instance.pk and 
            hasattr(self.instance, 'product') and self.instance.product and 
            not self.instance.unit_cost):
            try:
                self.fields['unit_cost'].initial = self.instance.product.cost_price
            except:
                # If there's any issue accessing the product, just skip the auto-fill
                pass
    
    def clean_product(self):
        """Validate product selection and prevent duplicates within the same purchase order"""
        product = self.cleaned_data.get('product')
        
        # Product is not required to be set (can be empty for new forms)
        if not product:
            return product
        
        # Check for duplicates only when we have a purchase order and product
        if (hasattr(self.instance, 'purchase_order') and 
            self.instance.purchase_order and 
            product):
            
            existing_items = PurchaseItem.objects.filter(
                purchase_order=self.instance.purchase_order,
                product=product
            )
            
            # Exclude current instance if editing
            if self.instance.pk:
                existing_items = existing_items.exclude(pk=self.instance.pk)
            
            if existing_items.exists():
                raise ValidationError(
                    f"Product '{product.name}' is already added to this purchase order. "
                    f"Please edit the existing item instead of adding a duplicate."
                )
        
        return product
    
    def clean_unit_cost(self):
        """Validate unit cost"""
        unit_cost = self.cleaned_data.get('unit_cost')
        
        # Unit cost is not always required (can be set later)
        if unit_cost is not None and unit_cost <= 0:
            raise ValidationError("Unit cost must be greater than 0.")
        
        return unit_cost
    
    def clean_quantity(self):
        """Validate quantity"""
        quantity = self.cleaned_data.get('quantity')
        
        # Quantity is not always required (can be set later)
        if quantity is not None and quantity <= 0:
            raise ValidationError("Quantity must be greater than 0.")
        
        return quantity
    
    def clean(self):
        """Additional validation for the entire form"""
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        unit_cost = cleaned_data.get('unit_cost')
        
        if product and unit_cost:
            # Warning if unit cost is significantly different from product cost price
            if product.cost_price and abs(unit_cost - product.cost_price) > (product.cost_price * 0.5):
                # This is a warning, not an error - still allow the form to be saved
                pass
        
        return cleaned_data

class PurchasePaymentForm(forms.ModelForm):
    class Meta:
        model = PurchasePayment
        fields = ['amount', 'amount_due', 'due_date', 'payment_date', 'payment_method', 'reference', 'status', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'amount_due': forms.NumberInput(attrs={'step': '0.01'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If creating a new payment and a purchase order is provided, auto-fill amount_due
        if not self.instance.pk and 'initial' in kwargs and 'purchase_order' in kwargs['initial']:
            purchase_order = kwargs['initial']['purchase_order']
            self.fields['amount_due'].initial = purchase_order.total