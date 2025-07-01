#!/usr/bin/env python
"""
Test with system Arabic fonts that might be available
"""
import os
import sys
import tempfile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
import django
django.setup()

from weasyprint import HTML, CSS

def test_system_fonts():
    """Test with different system Arabic fonts"""
    print("Testing system Arabic fonts...")
    
    # List of possible system Arabic fonts
    system_fonts = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', 
        '/System/Library/Fonts/Arial.ttf',  # macOS
        'C:\\Windows\\Fonts\\arial.ttf',     # Windows
    ]
    
    available_fonts = []
    for font in system_fonts:
        if os.path.exists(font):
            available_fonts.append(font)
            print(f"✓ Found: {font}")
    
    if not available_fonts:
        print("✗ No system fonts found")
        return
    
    # Test with first available font
    font_path = available_fonts[0]
    print(f"Testing with: {font_path}")
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        <div class="arabic">شركة تريندز للتجارة والخدمات</div>
        <div class="arabic">رقم الفاتورة: 12345</div>
        <div class="arabic">العميل: فيروز بافا</div>
        <div class="english">English text: Trendz Trading & Services</div>
    </body>
    </html>
    """
    
    css_content = f"""
    @font-face {{
        font-family: 'SystemFont';
        src: url('file://{font_path}') format('truetype');
    }}
    
    .arabic {{
        font-family: 'SystemFont', 'Arial Unicode MS', sans-serif;
        direction: rtl;
        text-align: right;
        font-size: 16px;
        margin: 10px 0;
        border: 1px solid #ccc;
        padding: 5px;
    }}
    
    .english {{
        font-family: 'SystemFont', Arial, sans-serif;
        direction: ltr;
        text-align: left;
        font-size: 16px;
        margin: 10px 0;
        border: 1px solid #ccc;
        padding: 5px;
    }}
    """
    
    try:
        html = HTML(string=html_content)
        css = CSS(string=css_content)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            html.write_pdf(tmp_file.name, stylesheets=[css])
            print(f"✓ System font PDF generated: {tmp_file.name}")
            
            # Copy to accessible location
            import shutil
            static_path = "/home/essyem/portal/trendzportal/static/test_system_font.pdf"
            shutil.copy2(tmp_file.name, static_path)
            print(f"✓ PDF copied to: {static_path}")
            
    except Exception as e:
        print(f"✗ System font test failed: {e}")
        import traceback
        traceback.print_exc()

def test_no_font():
    """Test with no custom fonts - rely on browser defaults"""
    print("\nTesting with default fonts only...")
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        <div class="arabic">شركة تريندز للتجارة والخدمات</div>
        <div class="arabic">رقم الفاتورة: 12345</div>
        <div class="arabic">العميل: فيروز بافا</div>
        <div class="english">English text: Trendz Trading & Services</div>
    </body>
    </html>
    """
    
    css_content = """
    .arabic {
        direction: rtl;
        text-align: right;
        font-size: 16px;
        margin: 10px 0;
        border: 1px solid #ccc;
        padding: 5px;
    }
    
    .english {
        direction: ltr;
        text-align: left;
        font-size: 16px;
        margin: 10px 0;
        border: 1px solid #ccc;
        padding: 5px;
    }
    """
    
    try:
        html = HTML(string=html_content)
        css = CSS(string=css_content)
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            html.write_pdf(tmp_file.name, stylesheets=[css])
            print(f"✓ Default font PDF generated: {tmp_file.name}")
            
            # Copy to accessible location
            import shutil
            static_path = "/home/essyem/portal/trendzportal/static/test_default_font.pdf"
            shutil.copy2(tmp_file.name, static_path)
            print(f"✓ PDF copied to: {static_path}")
            
    except Exception as e:
        print(f"✗ Default font test failed: {e}")

if __name__ == '__main__':
    print("Alternative Arabic Font Testing")
    print("=" * 50)
    test_system_fonts()
    test_no_font()
    print("\nCheck the generated PDFs to see which approach works best for Arabic text.")
