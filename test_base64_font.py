#!/usr/bin/env python
"""
Test base64 font embedding for Arabic PDF generation
"""
import os
import sys
import tempfile
import base64

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
import django
django.setup()

from django.test import RequestFactory
from portal.views import InvoicePDFView
from portal.models import Invoice
from weasyprint import HTML, CSS
from django.conf import settings

def test_base64_arabic_font():
    """Test base64 embedded Arabic font"""
    print("Testing base64 embedded Arabic font...")
    
    # Load and encode font
    font_path = '/home/essyem/portal/trendzportal/static/fonts/Amiri-Regular.ttf'
    
    try:
        with open(font_path, 'rb') as f:
            font_data = base64.b64encode(f.read()).decode()
        print(f"✓ Font loaded and encoded: {len(font_data)} characters")
        
        # Create test HTML with embedded font
        font_src = f'data:font/truetype;charset=utf-8;base64,{font_data}'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @font-face {{
                    font-family: 'Amiri';
                    src: url('{font_src}') format('truetype');
                    font-weight: normal;
                    font-style: normal;
                }}
                .arabic {{
                    font-family: 'Amiri', Arial, sans-serif;
                    direction: rtl;
                    text-align: right;
                    font-size: 18px;
                    line-height: 2;
                    font-feature-settings: "liga" 1, "calt" 1, "kern" 1, "curs" 1;
                }}
                .test-section {{
                    margin: 20px 0;
                    padding: 10px;
                    border: 1px solid #ccc;
                }}
            </style>
        </head>
        <body>
            <div class="test-section">
                <h2>Arabic Font Test - Embedded Base64</h2>
                <div class="arabic">شركة تريندز للتجارة والخدمات</div>
                <div class="arabic">رقم الفاتورة: ١٢٣٤٥</div>
                <div class="arabic">التاريخ: ٢٠٢٥/٠٧/٠١</div>
                <div class="arabic">تفاصيل التحويل المصرفي</div>
                <div class="arabic">البنك: بنك قطر التجاري</div>
            </div>
        </body>
        </html>
        """
        
        # Generate PDF with embedded font
        html = HTML(string=html_content)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            html.write_pdf(tmp_file.name)
            print(f"✓ Base64 font PDF generated: {tmp_file.name}")
            print(f"  File size: {os.path.getsize(tmp_file.name)} bytes")
            return tmp_file.name
            
    except Exception as e:
        print(f"✗ Base64 font test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_updated_invoice_pdf():
    """Test the updated invoice PDF with base64 font"""
    print("\nTesting updated invoice PDF...")
    
    try:
        # Get the test invoice
        invoice = Invoice.objects.get(id=4)
        print(f"Testing invoice: {invoice.invoice_number}")
        
        # Create test request
        factory = RequestFactory()
        request = factory.get('/test/')
        request.META['HTTP_HOST'] = 'localhost:8000'
        
        # Generate PDF using our updated view
        view = InvoicePDFView()
        view.kwargs = {'pk': 4}
        response = view.get(request)
        
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(response.content)
                print(f"✓ Updated invoice PDF generated: {tmp_file.name}")
                print(f"  File size: {len(response.content)} bytes")
                return tmp_file.name
        else:
            print(f"✗ Updated invoice PDF failed with status {response.status_code}")
            print(f"  Response: {response.content.decode()}")
            return None
            
    except Exception as e:
        print(f"✗ Updated invoice test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("Arabic Font Base64 Embedding Test")
    print("=" * 50)
    
    # Test base64 font embedding
    base64_pdf = test_base64_arabic_font()
    
    # Test updated invoice
    invoice_pdf = test_updated_invoice_pdf()
    
    print("\nTest Results:")
    print("=" * 50)
    if base64_pdf:
        print(f"Base64 Font Test PDF: {base64_pdf}")
    if invoice_pdf:
        print(f"Updated Invoice PDF: {invoice_pdf}")
    
    # Copy to accessible location
    if base64_pdf:
        os.system(f"cp {base64_pdf} /home/essyem/portal/trendzportal/static/test_base64_arabic.pdf")
        print("✓ Base64 test PDF copied to: static/test_base64_arabic.pdf")
    
    if invoice_pdf:
        os.system(f"cp {invoice_pdf} /home/essyem/portal/trendzportal/static/test_updated_invoice.pdf")
        print("✓ Updated invoice PDF copied to: static/test_updated_invoice.pdf")

if __name__ == '__main__':
    main()
