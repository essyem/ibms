"""
Barcode generation views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.db import models
from portal.models import Product, Category
from portal.barcode_utils import BarcodeGenerator
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
import os
import base64


def convert_to_arabic_numerals(number_str):
    """Convert Western numerals to Arabic numerals"""
    arabic_numerals = {
        '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
        '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
    }
    return ''.join(arabic_numerals.get(char, char) for char in str(number_str))


def register_arabic_fonts():
    """Register Arabic fonts for ReportLab PDF generation"""
    try:
        # Try Arabic-specific fonts first (best Arabic support)
        arabic_font_paths = [
            # Noto Arabic fonts (excellent Arabic support)
            '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',
            '/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf',
            '/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf',
            # KACST Arabic fonts
            '/usr/share/fonts/truetype/kacst/KacstBook.ttf',
            '/usr/share/fonts/truetype/kacst/KacstOffice.ttf',
            '/usr/share/fonts/truetype/kacst/KacstNaskh.ttf',
        ]
        
        for font_path in arabic_font_paths:
            if os.path.exists(font_path):
                try:
                    font_name = os.path.basename(font_path).replace('.ttf', '')
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    print(f"✅ Registered Arabic font: {font_name}")
                    return font_name
                except Exception as e:
                    print(f"❌ Failed to register {font_path}: {e}")
                    continue
        
        # Fallback to DejaVu Sans (good Unicode support)
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
            print("✅ Using DejaVuSans as fallback for Arabic text")
            return 'DejaVuSans'
        except Exception as e:
            print(f"❌ Failed to register DejaVuSans: {e}")
        
        # Final fallback to built-in fonts
        print("⚠️ Using Helvetica as final fallback (limited Arabic support)")
        return 'Helvetica'
        
    except Exception as e:
        print(f"❌ Font registration error: {e}")
        return 'Helvetica'


def staff_or_superuser_required(view_func):
    """
    Decorator that checks if user is staff or superuser (without site restrictions)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("You must be a staff member or superuser to access this page.")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@staff_or_superuser_required
def barcode_generator_dashboard(request):
    """Dashboard for barcode generation"""
    # Get products without barcodes (simplified for single-site)
    products_without_barcode = Product.objects.filter(
        models.Q(barcode__isnull=True) | models.Q(barcode='')
    ).select_related('category')
    
    # Get all categories (simplified for single-site)
    categories = Category.objects.all()
    
    context = {
        'products_without_barcode': products_without_barcode,
        'categories': categories,
        'total_products_without_barcode': products_without_barcode.count(),
    }
    
    return render(request, 'admin/portal/barcode_generator_dashboard.html', context)


@staff_or_superuser_required
@require_POST
def generate_single_barcode(request, product_id):
    """Generate barcode for a single product"""
    product = get_object_or_404(Product, id=product_id)
    
    if product.barcode:
        return JsonResponse({
            'success': False,
            'error': 'Product already has a barcode'
        })
    
    result = BarcodeGenerator.generate_barcode_for_product(product)
    
    if result['success']:
        messages.success(request, f'Barcode generated for {product.name}: {result["barcode_number"]}')
    else:
        messages.error(request, f'Failed to generate barcode for {product.name}: {result.get("error", "Unknown error")}')
    
    return JsonResponse(result)


@staff_or_superuser_required
@require_POST
def generate_bulk_barcodes(request):
    """Generate barcodes for multiple products"""
    selected_products = request.POST.getlist('selected_products')
    
    if not selected_products:
        messages.error(request, 'No products selected')
        return redirect('barcode_generator_dashboard')
    
    success_count = 0
    error_count = 0
    errors = []
    
    for product_id in selected_products:
        try:
            product = Product.objects.get(id=product_id)
            if not product.barcode:
                result = BarcodeGenerator.generate_barcode_for_product(product)
                if result['success']:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{product.name}: {result.get('error', 'Unknown error')}")
            else:
                error_count += 1
                errors.append(f"{product.name}: Already has barcode")
        except Product.DoesNotExist:
            error_count += 1
            errors.append(f"Product ID {product_id}: Not found")
    
    # Show results
    if success_count > 0:
        messages.success(request, f'Successfully generated {success_count} barcode(s)')
    
    if error_count > 0:
        error_message = f'Failed to generate {error_count} barcode(s)'
        if errors:
            error_message += ': ' + '; '.join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                error_message += f' and {len(errors) - 5} more...'
        messages.error(request, error_message)
    
    return redirect('barcode_generator_dashboard')


@staff_or_superuser_required
def print_barcode_labels(request):
    """Generate printable barcode labels"""
    selected_products = request.GET.getlist('products')
    
    if not selected_products:
        messages.error(request, 'No products selected for printing')
        return redirect('barcode_generator_dashboard')
    
    products = Product.objects.filter(
        id__in=selected_products,
        barcode__isnull=False
    ).exclude(barcode='').select_related('category')
    
    if not products.exists():
        messages.error(request, 'No products with barcodes found')
        return redirect('barcode_generator_dashboard')
    
    # Register Arabic fonts
    arabic_font = register_arabic_fonts()
    print(f"🔤 Using font for Arabic text: {arabic_font}")
    
    # Generate PDF with barcode labels
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="barcode_labels.pdf"'
    
    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Helper function for centered text
    def draw_centered_text(canvas, x, y, text, font_name='Helvetica', font_size=10):
        canvas.setFont(font_name, font_size)
        text_width = canvas.stringWidth(text, font_name, font_size)
        canvas.drawString(x - text_width/2, y, text)
    
    # Label settings (matching your attachment format)
    label_width = 85 * mm
    label_height = 30 * mm
    margin_x = 12 * mm
    margin_y = 15 * mm
    labels_per_row = 2
    labels_per_col = 9
    
    x_positions = [margin_x + i * (label_width + 8 * mm) for i in range(labels_per_row)]
    y_start = height - margin_y - label_height
    
    current_x = 0
    current_y = 0
    
    for product in products:
        print(f"DEBUG: Processing product {product.id}: {product.name}")
        try:
            unit_price = product.unit_price
            print(f"DEBUG: Product {product.id} unit_price: {unit_price}")
        except AttributeError as e:
            print(f"ERROR: Product {product.id} missing unit_price: {e}")
            continue
            
        if current_y >= labels_per_col:
            p.showPage()  # New page
            current_y = 0
        
        x = x_positions[current_x]
        y = y_start - (current_y * (label_height + 3 * mm))
        
        # Company name (matching your format)
        draw_centered_text(p, x + label_width/2, y + label_height - 4 * mm, 
                          "TRENDZ TRADING & SERVICES", 'Helvetica-Bold', 7)
        
        # Unit price in QAR with Arabic numerals (replacing product name)
        # Format price: "QAR 100 | ١٠٠ ر.ق" (corrected Arabic order)
        price_value = int(product.unit_price) if product.unit_price == int(product.unit_price) else product.unit_price
        price_arabic = convert_to_arabic_numerals(str(price_value))
        
        # Create bilingual price text with proper Arabic order (ر.ق not رق)  
        english_part = f"QAR {price_value}"
        arabic_part = f"{price_arabic} ر.ق"  # Corrected: ر.ق instead of رق
        price_text = f"{english_part} | {arabic_part}"
        
        print(f"DEBUG: Price text for product {product.id}: '{price_text}'")
        draw_centered_text(p, x + label_width/2, y + label_height - 8 * mm, 
                          price_text, arabic_font, 8)
        
        # Code label
        draw_centered_text(p, x + label_width/2, y + label_height - 11 * mm, 
                          "CODE:", 'Helvetica-Bold', 6)
        
        # Barcode
        if product.barcode:
            try:
                # Generate barcode image
                ean = barcode.get('ean13', product.barcode, writer=ImageWriter())
                barcode_buffer = BytesIO()
                ean.write(barcode_buffer)
                barcode_buffer.seek(0)
                
                # Position barcode image in the center of label
                barcode_x = x + 5 * mm
                barcode_y = y + 5 * mm
                barcode_width = label_width - 10 * mm
                barcode_height = 12 * mm
                
                # Insert barcode image (you may need to adjust this based on your reportlab version)
                try:
                    from reportlab.lib.utils import ImageReader
                    img = ImageReader(barcode_buffer)
                    p.drawImage(img, barcode_x, barcode_y, barcode_width, barcode_height)
                except:
                    # Fallback: draw barcode as text representation
                    draw_centered_text(p, x + label_width/2, y + 8 * mm, 
                                     "|||||||||||||||||||||||||||||||", 'Helvetica', 10)
                
                # Barcode number below the barcode (matching your format)
                # Format barcode with spaces for readability like in your image
                formatted_barcode = ' '.join(product.barcode[i:i+1] for i in range(len(product.barcode)))
                draw_centered_text(p, x + label_width/2, y + 2 * mm, 
                                 formatted_barcode, 'Helvetica-Bold', 8)
                
            except Exception as e:
                # Fallback display
                draw_centered_text(p, x + label_width/2, y + 8 * mm, 
                                 f"Barcode: {product.barcode}", 'Helvetica', 6)
        else:
            # No barcode available
            draw_centered_text(p, x + label_width/2, y + 8 * mm, 
                             "No barcode available", 'Helvetica', 6)
        
        # Move to next position
        current_x += 1
        if current_x >= labels_per_row:
            current_x = 0
            current_y += 1
    
    p.save()
    buffer.seek(0)
    response.write(buffer.getvalue())
    buffer.close()
    
    return response


@staff_or_superuser_required
def preview_barcode(request, product_id):
    """Preview barcode for a product"""
    product = get_object_or_404(Product, id=product_id)
    
    if not product.barcode:
        return JsonResponse({
            'success': False,
            'error': 'Product does not have a barcode'
        })
    
    result = BarcodeGenerator.generate_barcode_image(product.barcode)
    
    if result['success']:
        return JsonResponse({
            'success': True,
            'image_base64': result['image_base64'],
            'barcode_number': product.barcode,
            'product_name': product.name,
            'category': product.category.name
        })
    else:
        return JsonResponse(result)


@staff_or_superuser_required
def demo_barcode_labels(request):
    """Demo view to test barcode label printing with sample data"""
    from django.db.models import Q
    
    # Get first 2 products with barcodes for demo
    products = Product.objects.exclude(
        Q(barcode__isnull=True) | Q(barcode='')
    ).select_related('category')[:2]
    
    if not products.exists():
        messages.error(request, 'No products with barcodes found for demo')
        return redirect('barcode_generator_dashboard')
    
    # Register Arabic fonts
    arabic_font = register_arabic_fonts()
    print(f"🔤 Using font for Arabic text in demo: {arabic_font}")
    
    # Generate PDF with demo labels
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="demo_barcode_labels.pdf"'
    
    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Helper function for centered text
    def draw_centered_text(canvas, x, y, text, font_name='Helvetica', font_size=10):
        canvas.setFont(font_name, font_size)
        text_width = canvas.stringWidth(text, font_name, font_size)
        canvas.drawString(x - text_width/2, y, text)
    
    # Label settings (matching your attachment format)
    label_width = 85 * mm
    label_height = 30 * mm
    margin_x = 12 * mm
    margin_y = 15 * mm
    labels_per_row = 2
    
    x_positions = [margin_x + i * (label_width + 8 * mm) for i in range(labels_per_row)]
    y_start = height - margin_y - label_height
    
    current_x = 0
    
    for i, product in enumerate(products):
        x = x_positions[current_x]
        y = y_start - (i // labels_per_row) * (label_height + 3 * mm)
        
        # Company name (matching your format)
        draw_centered_text(p, x + label_width/2, y + label_height - 4 * mm, 
                          "TRENDZ TRADING & SERVICES", 'Helvetica-Bold', 7)
        
        # Unit price in QAR with Arabic numerals (replacing product name)
        # Format price: "QAR 100 | ١٠٠ ر.ق" (corrected Arabic order)
        price_value = int(product.unit_price) if product.unit_price == int(product.unit_price) else product.unit_price
        price_arabic = convert_to_arabic_numerals(str(price_value))
        
        # Create bilingual price text with proper Arabic order (ر.ق not رق)
        english_part = f"QAR {price_value}"
        arabic_part = f"{price_arabic} ر.ق"  # Corrected: ر.ق instead of رق
        price_text = f"{english_part} | {arabic_part}"
        
        draw_centered_text(p, x + label_width/2, y + label_height - 8 * mm, 
                          price_text, arabic_font, 8)
        
        # Code label
        draw_centered_text(p, x + label_width/2, y + label_height - 11 * mm, 
                          "CODE:", 'Helvetica-Bold', 6)
        
        # Barcode representation (using simple text bars)
        if product.barcode:
            # Draw barcode as text representation
            barcode_lines = "█ █  ██ █  █ ██ █ █  ██  █ █ ██ █  █ ██ █ █"
            draw_centered_text(p, x + label_width/2, y + 8 * mm, 
                             barcode_lines, 'Helvetica', 10)
            
            # Barcode number below
            formatted_barcode = ' '.join(product.barcode[i:i+1] for i in range(len(product.barcode)))
            draw_centered_text(p, x + label_width/2, y + 2 * mm, 
                             formatted_barcode, 'Helvetica-Bold', 8)
        
        # Move to next position
        current_x = (current_x + 1) % labels_per_row
    
    p.save()
    buffer.seek(0)
    response.write(buffer.getvalue())
    buffer.close()
    
    return response
