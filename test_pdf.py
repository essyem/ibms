#!/usr/bin/env python
"""
Test script for PDF generation without authentication
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
django.setup()

from django.test import RequestFactory
from portal.models import Invoice
from portal.views import InvoicePDFView
import tempfile

def test_pdf_generation():
    """Test PDF generation for invoice ID 4"""
    try:
        # Get the invoice
        invoice = Invoice.objects.get(id=4)
        print(f'Testing PDF generation for invoice: {invoice.invoice_number}')
        print(f'Customer: {invoice.customer}')
        
        # Create a mock request
        factory = RequestFactory()
        request = factory.get('/admin/portal/invoice/4/pdf/?download=true')
        request.META['HTTP_HOST'] = 'localhost:8002'
        
        # Create the view and set parameters
        view = InvoicePDFView()
        view.kwargs = {'pk': 4}
        
        # Generate PDF
        print('Generating PDF...')
        response = view.get(request)
        
        print(f'Response status code: {response.status_code}')
        print(f'Content type: {response.get("Content-Type")}')
        print(f'Content length: {len(response.content)} bytes')
        
        # Check if it's a valid PDF
        if response.status_code == 200:
            if response.content.startswith(b'%PDF'):
                print('✓ Valid PDF content generated!')
                
                # Save to a test file
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    tmp_file.write(response.content)
                    print(f'PDF saved to: {tmp_file.name}')
                    
            else:
                print('✗ Content is not a valid PDF')
                print(f'Content preview: {response.content[:200].decode("utf-8", errors="ignore")}')
        else:
            print('✗ PDF generation failed')
            print(f'Response content: {response.content.decode("utf-8", errors="ignore")}')
            
    except Exception as e:
        import traceback
        print(f'Error: {e}')
        traceback.print_exc()

if __name__ == '__main__':
    test_pdf_generation()
