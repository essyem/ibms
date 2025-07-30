"""
Barcode generation utilities for products
"""
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
from django.utils import timezone
from django.db import models
import random
import string


class BarcodeGenerator:
    """Generate unique barcodes for products"""
    
    @staticmethod
    def generate_unique_barcode():
        """Generate a unique EAN13 barcode number"""
        # EAN13 format: 12 digits + 1 check digit
        # Use a custom prefix to identify our generated barcodes
        prefix = "290"  # Country code for internal use
        
        # Get current year and month
        now = timezone.now()
        year_month = f"{now.year % 100:02d}{now.month:02d}"
        
        # Generate random digits for the remaining positions
        while True:
            # Generate 5 random digits (3+4+5 = 12 total digits)
            random_part = ''.join(random.choices(string.digits, k=5))
            
            # Combine parts (without check digit) - should be exactly 12 digits
            barcode_without_check = f"{prefix}{year_month}{random_part}"
            
            # Ensure we have exactly 12 digits
            if len(barcode_without_check) != 12:
                continue
                
            # Calculate EAN13 check digit
            check_digit = BarcodeGenerator.calculate_ean13_check_digit(barcode_without_check)
            full_barcode = f"{barcode_without_check}{check_digit}"
            
            # Check if this barcode already exists
            from portal.models import Product
            if not Product.objects.filter(barcode=full_barcode).exists():
                return full_barcode
    
    @staticmethod
    def calculate_ean13_check_digit(code):
        """Calculate the check digit for EAN13 barcode"""
        if len(code) != 12:
            raise ValueError("Code must be 12 digits for EAN13")
        
        odd_sum = sum(int(code[i]) for i in range(0, 12, 2))
        even_sum = sum(int(code[i]) for i in range(1, 12, 2))
        
        total = odd_sum + (even_sum * 3)
        check_digit = (10 - (total % 10)) % 10
        
        return str(check_digit)
    
    @staticmethod
    def generate_barcode_image(barcode_number, format='PNG'):
        """Generate barcode image and return as base64 string"""
        try:
            # Create EAN13 barcode
            ean = barcode.get('ean13', barcode_number, writer=ImageWriter())
            
            # Generate image in memory
            buffer = BytesIO()
            ean.write(buffer)
            buffer.seek(0)
            
            # Convert to base64 for web display
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'success': True,
                'image_base64': image_base64,
                'barcode_number': barcode_number
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def generate_barcode_for_product(product):
        """Generate and assign barcode to a product"""
        if product.barcode:
            return {
                'success': False,
                'error': 'Product already has a barcode'
            }
        
        try:
            # Generate unique barcode
            barcode_number = BarcodeGenerator.generate_unique_barcode()
            
            # Assign to product
            product.barcode = barcode_number
            product.save(update_fields=['barcode'])
            
            # Generate image
            image_result = BarcodeGenerator.generate_barcode_image(barcode_number)
            
            if image_result['success']:
                return {
                    'success': True,
                    'barcode_number': barcode_number,
                    'image_base64': image_result['image_base64'],
                    'product': product
                }
            else:
                return image_result
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def bulk_generate_barcodes_for_products_without_sku():
        """Generate barcodes for all products that don't have SKU or barcode"""
        from portal.models import Product
        products_without_barcode = Product.objects.filter(
            models.Q(barcode__isnull=True) | models.Q(barcode='') |
            models.Q(sku__isnull=True) | models.Q(sku='')
        )
        
        results = []
        for product in products_without_barcode:
            if not product.barcode:  # Only generate if no barcode exists
                result = BarcodeGenerator.generate_barcode_for_product(product)
                results.append({
                    'product': product,
                    'result': result
                })
        
        return results
