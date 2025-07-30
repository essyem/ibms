# portal/ajax_views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from .models import Product
from django.core import serializers
import json

@require_GET
@staff_member_required
def product_search_ajax(request):
    """
    AJAX endpoint for searching products by name, barcode, or category
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'products': []})
    
    # Search in multiple fields
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(barcode__icontains=query) |
        Q(category__name__icontains=query) |
        Q(description__icontains=query),
        is_active=True
    ).select_related('category')[:20]  # Limit to 20 results
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'barcode': product.barcode or '',
            'category': product.category.name if product.category else 'No Category',
            'unit_price': float(product.unit_price),
            'stock': product.stock,
            'description': product.description or '',
            'display_text': f"{product.name} - QAR {product.unit_price} (Stock: {product.stock})"
        })
    
    return JsonResponse({'products': results})

@require_GET
@staff_member_required  
def product_barcode_lookup(request):
    """
    AJAX endpoint for looking up product by barcode
    """
    barcode = request.GET.get('barcode', '').strip()
    
    if not barcode:
        return JsonResponse({'error': 'No barcode provided'}, status=400)
    
    try:
        product = Product.objects.select_related('category').get(
            barcode=barcode,
            is_active=True
        )
        
        result = {
            'id': product.id,
            'name': product.name,
            'barcode': product.barcode,
            'category': product.category.name if product.category else 'No Category',
            'unit_price': float(product.unit_price),
            'stock': product.stock,
            'description': product.description or '',
            'display_text': f"{product.name} - QAR {product.unit_price} (Stock: {product.stock})"
        }
        
        return JsonResponse({'product': result})
        
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

@require_GET
def product_search_public(request):
    """
    Public AJAX endpoint for product search (for invoice creation form)
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'products': []})
    
    # Search in multiple fields
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(barcode__icontains=query) |
        Q(category__name__icontains=query),
        is_active=True,
        stock__gt=0  # Only show products in stock
    ).select_related('category')[:15]  # Limit to 15 results
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'barcode': product.barcode or '',
            'category': product.category.name if product.category else 'No Category',
            'unit_price': float(product.unit_price),  # This is the selling price
            'selling_price': float(product.unit_price),  # Alias for frontend compatibility
            'cost_price': float(product.cost_price),  # Cost price for calculations
            'stock': product.stock,
            'description': product.description or '',
            'display_text': f"{product.name} - QAR {product.unit_price}",
            'stock_text': f"Stock: {product.stock}"
        })
    
    return JsonResponse({'products': results})

@require_GET
def product_barcode_lookup_public(request):
    """
    Public AJAX endpoint for barcode lookup (for invoice creation form)
    """
    barcode = request.GET.get('barcode', '').strip()
    
    if not barcode:
        return JsonResponse({'error': 'No barcode provided'}, status=400)
    
    try:
        product = Product.objects.select_related('category').get(
            barcode=barcode,
            is_active=True,
            stock__gt=0
        )
        
        result = {
            'id': product.id,
            'name': product.name,
            'barcode': product.barcode,
            'category': product.category.name if product.category else 'No Category',
            'unit_price': float(product.unit_price),  # This is the selling price
            'selling_price': float(product.unit_price),  # Alias for frontend compatibility
            'cost_price': float(product.cost_price),  # Cost price for calculations
            'stock': product.stock,
            'description': product.description or '',
            'display_text': f"{product.name} - QAR {product.unit_price}",
            'stock_text': f"Stock: {product.stock}"
        }
        
        return JsonResponse({'product': result})
        
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found or out of stock'}, status=404)
