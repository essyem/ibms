# portal/widgets.py
from django.forms import TextInput, Select
from django import forms
from django.utils.safestring import mark_safe

class IconPickerWidget(TextInput):
    template_name = 'portal/widgets/icon_picker.html'

    class Media:
        css = {
            'all': [
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
                'css/icon-picker.css'
            ]
        }
        js = [
            'js/icon-picker.js'
        ]

class ProductSearchWidget(Select):
    """
    Custom widget for product selection with search and barcode scanning
    """
    
    class Media:
        css = {
            'all': ('admin/css/product-search.css',)
        }
        js = (
            'admin/js/vendor/jquery/jquery.min.js',
            'admin/js/product-search.js',
            'admin/js/barcode-scanner.js',
        )
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'product-search-select',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        # Get the standard select element
        select_html = super().render(name, value, attrs, renderer)
        
        # Add search input and barcode scanner button
        widget_html = f"""
        <div class="product-search-container">
            <div class="search-controls">
                <input type="text" 
                       class="product-search-input form-control" 
                       placeholder="Search products by name, barcode, or category..."
                       data-target="{attrs.get('id', name) if attrs else name}">
                <button type="button" 
                        class="btn btn-primary barcode-scan-btn"
                        data-target="{attrs.get('id', name) if attrs else name}">
                    📷 Scan Barcode
                </button>
            </div>
            <div class="search-results" style="display: none;"></div>
            {select_html}
            <div class="selected-product-info" style="display: none;">
                <div class="product-details"></div>
            </div>
        </div>
        """
        
        return mark_safe(widget_html)