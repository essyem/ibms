from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div, HTML
from crispy_forms.bootstrap import FormActions
from .models import(ProductEnquiry, Invoice, InvoiceItem, 
    Product, Customer, Quotation, QuotationItem, PaymentReceipt)


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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-3'),
                Column('company', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-3'),
                Column('phone', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('product_interest', css_class='form-group col-md-6 mb-3'),
                Column('subject', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('message', css_class='form-group mb-3'),
            Div(
                Field('terms_agreed', css_class='form-check-input'),
                css_class='form-check mb-3'
            ),
            FormActions(
                Submit('submit', 'Send Enquiry', css_class='btn btn-primary btn-lg'),
                css_class='text-center'
            )
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
        
        # Add crispy forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('full_name', css_class='form-group col-md-6 mb-3'),
                Column('phone', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('company_name', css_class='form-group col-md-6 mb-3'),
                Column('tax_number', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('preferred_contact_method', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('address', css_class='form-group mb-3'),
            FormActions(
                Submit('submit', 'Save Customer', css_class='btn btn-success'),
                css_class='text-end'
            )
        )


# =============================================================================
# QUOTATION FORMS
# =============================================================================

class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = [
            'customer', 'valid_until', 'status', 'notes', 'terms_conditions',
            'discount_type', 'discount_value', 'tax_rate'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'valid_until': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes or special instructions'
            }),
            'terms_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Terms and conditions for this quotation'
            }),
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'discount_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Tax rate (%)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default validity date (30 days from now)
        from datetime import date, timedelta
        if not self.instance.pk:
            self.fields['valid_until'].initial = date.today() + timedelta(days=30)


class QuotationItemForm(forms.ModelForm):
    class Meta:
        model = QuotationItem
        fields = ['product', 'quantity', 'unit_price', 'use_product_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'use_product_price': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# =============================================================================
# PAYMENT RECEIPT FORMS
# =============================================================================

class PaymentReceiptForm(forms.ModelForm):
    # Remove customer from visible fields - it will be auto-populated from invoice
    class Meta:
        model = PaymentReceipt
        fields = [
            'invoice', 'payment_method', 'amount_received', 
            'amount_due', 'reference_number', 'notes'
        ]
        widgets = {
            # Invoice field will be replaced with search functionality in template
            'invoice': forms.HiddenInput(),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'amount_received': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Amount received from customer'
            }),
            'amount_due': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Total amount due',
                'readonly': True  # Will be auto-populated from invoice
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Transaction/Reference number (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make invoice optional (can be cash payment without invoice)
        self.fields['invoice'].required = False