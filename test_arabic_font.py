#!/usr/bin/env python3
"""
Test script to verify Arabic font rendering with WeasyPrint
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
django.setup()

from weasyprint import HTML, CSS

def test_arabic_font():
    """Test Arabic font rendering"""
    
    # Font path
    font_dir = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Amiri-0.117')
    amiri_regular_path = os.path.join(font_dir, 'Amiri-Regular.ttf')
    
    # Check if font exists
    if not os.path.exists(amiri_regular_path):
        print(f"❌ Font not found at: {amiri_regular_path}")
        return False
    
    print(f"✅ Font found at: {amiri_regular_path}")
    
    # Create HTML with Arabic text
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Arabic Font Test</title>
    </head>
    <body>
        <h1 class="english">English Text: Trendz Trading & Services</h1>
        <h1 class="arabic">الشركة التجارية تريندز للخدمات</h1>
        <p class="arabic">مرحبا بكم في موقعنا الإلكتروني</p>
        <p class="english">Welcome to our website</p>
    </body>
    </html>
    '''
    
    # Create CSS with font
    css_content = f'''
        @font-face {{
            font-family: 'Amiri';
            src: url('file://{amiri_regular_path}') format('truetype');
            font-weight: normal;
            font-style: normal;
        }}
        
        body {{
            font-family: 'DejaVu Sans', Arial, sans-serif;
            font-size: 12px;
            margin: 20px;
        }}
        
        .arabic {{
            font-family: 'Amiri', 'DejaVu Sans', sans-serif;
            direction: rtl;
            text-align: right;
            font-size: 16px;
            line-height: 1.8;
            color: #2c3e50;
        }}
        
        .english {{
            direction: ltr;
            text-align: left;
            font-family: 'DejaVu Sans', Arial, sans-serif;
            color: #34495e;
        }}
    '''
    
    try:
        # Generate PDF
        html = HTML(string=html_content)
        css = CSS(string=css_content)
        
        # Test PDF generation
        pdf_output = '/home/azureuser/trendzportal/test_arabic_output.pdf'
        html.write_pdf(pdf_output, stylesheets=[css])
        
        print(f"✅ PDF generated successfully: {pdf_output}")
        print("✅ Arabic font test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        return False

if __name__ == "__main__":
    print("Testing Arabic font rendering with WeasyPrint...")
    test_arabic_font()
