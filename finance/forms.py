# finance/forms.py
from django import forms
from .models import FinanceTransaction, Category
from django.core.exceptions import ValidationError
from django.utils import timezone

class TransactionForm(forms.ModelForm):
    # Add additional fields or customization here
    document = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control-file',
            'accept': '.pdf,.jpg,.png,.doc,.docx'
        }),
        help_text="Upload supporting document (PDF, image, or Word)"
    )
    
    class Meta:
        model = FinanceTransaction
        fields = [
            'type', 'category', 'amount', 'date', 
            'description', 'payment_method', 'reference', 'document'
        ]
        widgets = {
            'type': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'filterCategories(this.value)'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'max': timezone.now().date().isoformat()
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'reference': "Payment reference number or check number",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter categories based on transaction type if type is set
        if 'type' in self.data:
            try:
                transaction_type = self.data.get('type')
                self.fields['category'].queryset = Category.objects.filter(
                    type=transaction_type
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            # Fix: Use the instance.type (which is a string) to filter categories
            self.fields['category'].queryset = Category.objects.filter(
                type=self.instance.type
            ).order_by('name')

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError("Amount must be greater than zero")
        return amount

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date > timezone.now().date():
            raise ValidationError("Date cannot be in the future")
        return date