from django import forms
from .models import(ProductEnquiry, Invoice, InvoiceItem, 
    Product, Customer)


class InvoiceForm(forms.ModelForm):
    customer_name = forms.CharField(required=False, initial='Walk-in Customer')
    customer_phone = forms.CharField(required=False)
    
    class Meta:
        model = Invoice
        fields = [
            'customer',
            'due_date', 'invoice_number', 'status',
            'payment_mode', 'cash_amount', 'pos_amount',
            'other_amount', 'other_method', 'notes', 'tax', 
            'discount_type', 'discount_value'
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'invoice_number': forms.TextInput(attrs={'readonly': True}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'payment_mode': forms.Select(attrs={'class': 'form-control'}),
            'cash_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control', 'value': '0.00'}),
            'pos_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control', 'value': '0.00'}),
            'other_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-control', 'value': '0.00'}),
            'other_method': forms.TextInput(attrs={'placeholder': 'e.g., Bank Transfer, Check', 'class': 'form-control'}),
        }
    
    def clean_invoice_number(self):
        invoice_number = self.cleaned_data.get('invoice_number')
        print(f"🔍 FORM: clean_invoice_number called with: {repr(invoice_number)}")
        if invoice_number in [None, '', 'Auto-generated']:
            print("🔍 FORM: Returning None for auto-generation")
            return None  # Return None instead of 'Auto-generated'
        if len(invoice_number) != 10 or not invoice_number.isdigit():
            print(f"🔍 FORM: Invalid invoice number format: {invoice_number}")
            raise forms.ValidationError("Invoice number must be 10 digits (YYYYMMDDNN)")
        print(f"🔍 FORM: Valid invoice number: {invoice_number}")
        return invoice_number

    def clean(self):
        cleaned_data = super().clean()
        print(f"🔍 FORM: clean() called with invoice_number: {repr(cleaned_data.get('invoice_number'))}")
        
        # The invoice_number field validation already handles 'Auto-generated' 
        # by returning None, so no additional processing needed here
        
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f"Form initial status: {self.initial.get('status')}")
        # Make all fields optional except due_date
        self.fields['due_date'].required = True
        for field in self.fields:
            if field != 'due_date':
                self.fields[field].required = False
            
            if 'status' in self.fields:
                self.fields['status'].initial = None


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity', 'unit_price']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit_price'].widget.attrs.update({
            'class': 'form-control'
        })
        
        if self.instance and self.instance.product:
            self.fields['unit_price'].initial = self.instance.product.unit_price


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
            'unit_price': forms.NumberInput(attrs={
                'step': '0.01',
                'required': 'required'
            }),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'warranty_period': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        cost_price = cleaned_data.get('cost_price')
        unit_price = cleaned_data.get('unit_price')
        
        if cost_price is not None and unit_price is not None:
            if unit_price < cost_price:
                self.add_error('unit_price', 
                    "Unit price cannot be less than cost price")
        
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


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['full_name', 'phone', 'company_name', 'address', 'tax_number', 'preferred_contact_method']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter customer full name',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number',
                'required': True
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Company name (optional)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Customer address (optional)'
            }),
            'tax_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tax/VAT number (optional)'
            }),
            'preferred_contact_method': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make full_name and phone required
        self.fields['full_name'].required = True
        self.fields['phone'].required = True
        # Make other fields optional
        self.fields['company_name'].required = False
        self.fields['address'].required = False
        self.fields['tax_number'].required = False
        self.fields['preferred_contact_method'].required = False