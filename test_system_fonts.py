#!/usr/bin/env python3
"""
Test Arabic font rendering with system fonts
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
django.setup()

from weasyprint import HTML, CSS

def test_system_arabic_font():
    """Test Arabic font rendering with system fonts"""
    
    # Create HTML with Arabic text
    html_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>System Arabic Font Test</title>
    </head>
    <body>
        <h1 class="english">English: Trendz Trading & Services</h1>
        <h1 class="arabic">شركة تريندز للتجارة والخدمات</h1>
        <p class="arabic">مرحبا بكم في موقعنا الإلكتروني</p>
        <p class="english">Welcome to our website</p>
        <div class="arabic">تاريخ: ٢٠٢٥/٠٧/٠١</div>
        <div class="arabic">فاتورة رقم: ١٢٣٤٥</div>
    </body>
    </html>
    '''
    
    # Create CSS with system font
    css_content = '''
        body {
            font-family: 'DejaVu Sans', Arial, sans-serif;
            font-size: 12px;
            margin: 20px;
        }
        
        .arabic {
            font-family: 'Amiri', 'Noto Sans Arabic', 'DejaVu Sans', Arial, sans-serif !important;
            direction: rtl;
            text-align: right;
            font-size: 18px;
            line-height: 2.0;
            color: #2c3e50;
            margin: 10px 0;
        }
        
        .english {
            direction: ltr;
            text-align: left;
            font-family: 'DejaVu Sans', Arial, sans-serif;
            color: #34495e;
            margin: 10px 0;
        }
    '''
    
    try:
        # Generate PDF
        html = HTML(string=html_content)
        css = CSS(string=css_content)
        
        # Test PDF generation
        pdf_output = '/home/azureuser/trendzportal/test_system_arabic.pdf'
        html.write_pdf(pdf_output, stylesheets=[css])
        
        print(f"✅ PDF with system fonts generated: {pdf_output}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        return False

if __name__ == "__main__":
    print("Testing Arabic font rendering with system fonts...")
    test_system_arabic_font()
