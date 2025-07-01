#!/usr/bin/env python
"""
Test the updated invoice with logo
"""
import os
import sys
import tempfile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
import django
django.setup()

from django.test import RequestFactory
from portal.views import InvoicePDFView
from portal.models import Invoice

def test_invoice_with_logo():
    """Test invoice PDF generation with logo"""
    print("Testing invoice PDF with logo...")
    
    try:
        # Get the test invoice
        invoice = Invoice.objects.get(id=4)
        print(f"Testing invoice: {invoice.invoice_number}")
        print(f"Customer: {invoice.customer}")
        
        # Create test request
        factory = RequestFactory()
        request = factory.get('/test/')
        request.META['HTTP_HOST'] = 'localhost:8000'
        
        # Generate PDF using our view
        view = InvoicePDFView()
        view.kwargs = {'pk': 4}
        response = view.get(request)
        
        if response.status_code == 200:
            # Save to static directory for easy access
            static_path = "/home/essyem/portal/trendzportal/static/invoice_with_logo.pdf"
            with open(static_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✓ Invoice with logo PDF generated!")
            print(f"  File size: {len(response.content)} bytes")
            print(f"  Saved to: {static_path}")
            return True
        else:
            print(f"✗ PDF generation failed with status {response.status_code}")
            print(f"  Response: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"✗ Invoice with logo test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Testing Invoice PDF with Logo")
    print("=" * 40)
    test_invoice_with_logo()
