#!/usr/bin/env python
"""
Simple inventory test for the Django admin or shell
"""

# Test the enhanced InvoiceItem model validation
from portal.models import Product, Invoice, InvoiceItem, Customer
from decimal import Decimal
from django.core.exceptions import ValidationError

def test_basic_inventory():
    print("Testing basic inventory functionality...")
    
    # Create test product
    try:
        product = Product.objects.create(
            name="Test Product Basic",
            unit_price=Decimal('15.00'),
            stock=3,
            description="Basic test product"
        )
        print(f"✓ Created product with stock: {product.stock}")
        
        # Create test customer  
        customer = Customer.objects.create(
            full_name="Test Customer",
            phone="1234567890"
        )
        print("✓ Created test customer")
        
        # Create test invoice
        invoice = Invoice.objects.create(
            customer=customer,
            invoice_number="TEST001",
            subtotal=Decimal('30.00'),
            grand_total=Decimal('30.00')
        )
        print("✓ Created test invoice")
        
        # Test 1: Valid stock reduction
        print("\nTest 1: Valid stock reduction (2 units from 3 available)")
        invoice_item = InvoiceItem.objects.create(
            invoice=invoice,
            product=product,
            quantity=2,
            unit_price=product.unit_price
        )
        
        product.refresh_from_db()
        print(f"✓ Stock reduced to: {product.stock}")
        
        # Test 2: Try invalid stock (should fail)
        print("\nTest 2: Invalid stock test (5 units when only 1 available)")
        try:
            invalid_item = InvoiceItem(
                invoice=invoice,
                product=product,
                quantity=5,
                unit_price=product.unit_price
            )
            invalid_item.clean()  # This should raise ValidationError
            invalid_item.save()
            print("✗ ERROR: Invalid item was saved!")
        except ValidationError as e:
            print(f"✓ Validation correctly prevented invalid stock: {e}")
            
        # Clean up
        invoice.delete()
        product.delete() 
        customer.delete()
        print("\n✓ Test completed and cleaned up")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")

if __name__ == "__main__":
    test_basic_inventory()
