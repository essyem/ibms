#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append('/home/azureuser/trendzportal')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
django.setup()

from portal.models import Invoice
from portal.templatetags.arabic_filters import arabic_display
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import arabic_reshaper
from bidi.algorithm import get_display

def test_arabic_rendering():
    print("Testing Arabic text processing...")
    
    # Test the Arabic filter
    test_texts = [
        "شركة تريندز للتجارة والخدمات",
        "رقم الفاتورة:",
        "التاريخ:",
        "تاريخ الاستحقاق:",
        "تفاصيل التحويل المصرفي",
        "البنك:",
        "بنك قطر التجاري"
    ]
    
    print("\n=== Testing Arabic Text Filter ===")
    for text in test_texts:
        processed = arabic_display(text)
        print(f"Original: {text}")
        print(f"Processed: {processed}")
        print(f"Equal: {text == processed}")
        print("-" * 50)
    
    # Test WeasyPrint with system fonts
    print("\n=== Testing WeasyPrint with Arabic Text ===")
    
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Arabic Font Test</title>
    </head>
    <body>
        <div class="arabic-text">شركة تريندز للتجارة والخدمات</div>
        <div class="arabic-text">رقم الفاتورة: 12345</div>
        <div class="arabic-text">التاريخ: 2025/07/01</div>
        <div class="english-text">Trendz Trading & Services</div>
    </body>
    </html>
    '''
    
    css_content = '''
    @font-face {
        font-family: 'Amiri';
        src: url('/usr/share/fonts/truetype/amiri/Amiri-Regular.ttf') format('truetype');
        font-weight: normal;
        font-style: normal;
    }
    
    .arabic-text {
        font-family: 'Amiri', 'Noto Sans Arabic', 'DejaVu Sans', Arial, sans-serif;
        direction: rtl;
        text-align: right;
        font-size: 16px;
        line-height: 2.0;
        margin: 10px 0;
        font-feature-settings: 'liga' 1, 'calt' 1, 'ccmp' 1, 'locl' 1;
    }
    
    .english-text {
        font-family: 'DejaVu Sans', Arial, sans-serif;
        direction: ltr;
        text-align: left;
        font-size: 16px;
        line-height: 1.5;
        margin: 10px 0;
    }
    '''
    
    try:
        # Create HTML and CSS objects
        html = HTML(string=html_content)
        css = CSS(string=css_content)
        
        # Configure font config for WeasyPrint
        font_config = FontConfiguration()
        
        # Generate PDF
        pdf_file = html.write_pdf(stylesheets=[css], font_config=font_config)
        
        # Write to file
        with open('/home/azureuser/trendzportal/test_arabic_rendering.pdf', 'wb') as f:
            f.write(pdf_file)
        
        print("✅ PDF generated successfully: test_arabic_rendering.pdf")
        print("Check the PDF to see if Arabic text renders correctly")
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_arabic_rendering()
