from django import forms
from .models import ProductEnquiry, Invoice, InvoiceItem, Product


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer', 'due_date', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

# forms.py
from django import forms
from .models import InvoiceItem, Product

class InvoiceItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={'class': 'product-select'})
    )
    
    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity', 'selling_price']  # Changed unit_price to selling_price
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),
            'selling_price': forms.NumberInput(attrs={'step': '0.01'}),  # Changed unit_price to selling_price
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial selling_price from product if available
        if self.instance.pk and self.instance.product:
            self.fields['selling_price'].initial = self.instance.selling_price

'''
class InvoiceItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={'class': 'product-select'})
    )
    
    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
        }

'''

class InvoiceAdminForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        discount_value = cleaned_data.get('discount_value')
        discount_type = cleaned_data.get('discount_type')
        
        if discount_type == 'percent' and discount_value > 100:
            self.add_error('discount_value', 'Percentage discount cannot exceed 100%')
        
        return cleaned_data

# forms.py - update ProductForm if you have one


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'  # or specify the fields you want
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'cost_price': forms.NumberInput(attrs={
                'step': '0.01',
                'required': 'required'
            }),
            'selling_price': forms.NumberInput(attrs={
                'step': '0.01',
                'required': 'required'
            }),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'warranty_period': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
        }
    def clean(self):
        cleaned_data = super().clean()
        cost_price = cleaned_data.get('cost_price')
        selling_price = cleaned_data.get('selling_price')
        
        if cost_price is not None and selling_price is not None:
            if selling_price < cost_price:
                self.add_error('selling_price', 
                    "Selling price cannot be less than cost price")
        
        return cleaned_data

class ProductEnquiryForm(forms.ModelForm):
    class Meta:
        model = ProductEnquiry
        fields = ['name', 'company', 'email', 'phone', 'product_interest', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'product_interest': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        
    terms_agreed = forms.BooleanField(
        required=True,
        label='I agree to Trendz\'s Terms & Conditions',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )