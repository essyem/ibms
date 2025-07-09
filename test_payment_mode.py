#!/usr/bin/env python
"""
Test script to verify payment mode functionality
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
django.setup()

from portal.models import Invoice
from portal.forms import InvoiceForm

def test_payment_mode():
    print("=== Testing Payment Mode Functionality ===\n")
    
    # Test 1: Check form fields
    print("1. Testing InvoiceForm fields:")
    form = InvoiceForm()
    payment_fields = [field for field in form.fields.keys() 
                     if 'payment' in field.lower() or 'cash' in field.lower() 
                     or 'pos' in field.lower() or 'other' in field.lower()]
    
    for field in payment_fields:
        print(f"   ✓ {field}: {type(form.fields[field]).__name__}")
    
    # Test 2: Check model fields
    print("\n2. Testing Invoice model fields:")
    model_payment_fields = [field.name for field in Invoice._meta.get_fields() 
                           if 'payment' in field.name.lower() or 'cash' in field.name.lower() 
                           or 'pos' in field.name.lower() or 'other' in field.name.lower()]
    
    for field in model_payment_fields:
        field_obj = Invoice._meta.get_field(field)
        print(f"   ✓ {field}: {type(field_obj).__name__}")
    
    # Test 3: Check payment mode choices
    print("\n3. Testing payment mode choices:")
    for choice in Invoice.PAYMENT_MODES:
        print(f"   ✓ {choice[0]}: {choice[1]}")
    
    # Test 4: Test form instantiation with payment data
    print("\n4. Testing form with payment mode data:")
    test_data = {
        'payment_mode': 'split',
        'cash_amount': '100.00',
        'pos_amount': '50.00',
        'other_amount': '25.00',
        'other_method': 'Bank Transfer'
    }
    
    form_with_data = InvoiceForm(data=test_data)
    print(f"   ✓ Form with split payment data created successfully")
    print(f"   ✓ Payment mode field value: {form_with_data['payment_mode'].value()}")
    
    # Test 5: Check if payment mode field has the right widget
    payment_mode_field = form.fields['payment_mode']
    print(f"\n5. Payment mode field details:")
    print(f"   ✓ Field type: {type(payment_mode_field).__name__}")
    print(f"   ✓ Widget type: {type(payment_mode_field.widget).__name__}")
    print(f"   ✓ Choices count: {len(payment_mode_field.choices)}")
    
    print("\n=== All tests completed successfully! ===")

if __name__ == '__main__':
    test_payment_mode()
