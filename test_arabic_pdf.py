#!/usr/bin/env python
"""
Test script specifically for Arabic font rendering in PDF
"""
import os
import sys
import tempfile
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
import django
django.setup()

from django.test import RequestFactory
from portal.views import InvoicePDFView
from portal.models import Invoice
from weasyprint import HTML, CSS
from django.conf import settings

def test_basic_arabic_rendering():
    """Test basic Arabic rendering with WeasyPrint"""
    print("Testing basic Arabic rendering...")
    
    # Simple Arabic HTML
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @font-face {
                font-family: 'Amiri';
                src: url('file:///home/essyem/portal/trendzportal/static/fonts/Amiri-Regular.ttf') format('truetype');
            }
            .arabic {
                font-family: 'Amiri', Arial, sans-serif;
                direction: rtl;
                text-align: right;
                font-size: 16px;
            }
        </style>
    </head>
    <body>
        <div class="arabic">شركة تريندز للتجارة والخدمات</div>
        <div class="arabic">رقم الفاتورة: 12345</div>
        <div class="arabic">التاريخ: 2025/07/01</div>
    </body>
    </html>
    """
    
    try:
        # Generate PDF
        html = HTML(string=html_content)
        css = CSS(string="""
            @font-face {
                font-family: 'Amiri';
                src: url('file:///home/essyem/portal/trendzportal/static/fonts/Amiri-Regular.ttf') format('truetype');
            }
            .arabic {
                font-family: 'Amiri', Arial, sans-serif !important;
                direction: rtl;
                text-align: right;
                font-size: 16px;
            }
        """)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            html.write_pdf(tmp_file.name, stylesheets=[css])
            print(f"✓ Basic Arabic PDF generated: {tmp_file.name}")
            print(f"  File size: {os.path.getsize(tmp_file.name)} bytes")
            return tmp_file.name
            
    except Exception as e:
        print(f"✗ Basic Arabic rendering failed: {e}")
        return None

def test_invoice_arabic_rendering():
    """Test Arabic rendering in actual invoice"""
    print("\nTesting invoice Arabic rendering...")
    
    try:
        # Get the test invoice
        invoice = Invoice.objects.get(id=4)
        print(f"Testing invoice: {invoice.invoice_number}")
        
        # Create test request
        factory = RequestFactory()
        request = factory.get('/test/')
        request.META['HTTP_HOST'] = 'localhost:8000'
        
        # Generate PDF using our view
        view = InvoicePDFView()
        view.kwargs = {'pk': 4}
        response = view.get(request)
        
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(response.content)
                print(f"✓ Invoice PDF generated: {tmp_file.name}")
                print(f"  File size: {len(response.content)} bytes")
                return tmp_file.name
        else:
            print(f"✗ Invoice PDF generation failed with status {response.status_code}")
            print(f"  Response: {response.content.decode()}")
            return None
            
    except Exception as e:
        print(f"✗ Invoice Arabic rendering failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("Arabic Font PDF Testing")
    print("=" * 40)
    
    # Check if font file exists
    font_path = '/home/essyem/portal/trendzportal/static/fonts/Amiri-Regular.ttf'
    if os.path.exists(font_path):
        print(f"✓ Font file found: {font_path}")
        print(f"  Font size: {os.path.getsize(font_path)} bytes")
    else:
        print(f"✗ Font file not found: {font_path}")
        return
    
    # Test basic Arabic rendering
    basic_pdf = test_basic_arabic_rendering()
    
    # Test invoice Arabic rendering
    invoice_pdf = test_invoice_arabic_rendering()
    
    print("\nTest Summary:")
    print("=" * 40)
    if basic_pdf:
        print(f"Basic Arabic PDF: {basic_pdf}")
    if invoice_pdf:
        print(f"Invoice Arabic PDF: {invoice_pdf}")
    
    print("\nTo view the PDFs, open them in a PDF viewer to check Arabic rendering.")

if __name__ == '__main__':
    main()
