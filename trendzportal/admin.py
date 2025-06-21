from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.formats import base_formats
from import_export.widgets import ForeignKeyWidget
from portal.models import Product
from django.contrib.admin import AdminSite
from portal.resources import ProductResource
from django.utils.translation import gettext_lazy as _
from portal.models import (CartItem, Product, Category, Order, Customer, 
    Review, Cart, ProductEnquiry, Invoice)
from django.utils.html import format_html
from django import forms
from django.urls import reverse, path
from portal.views import InvoicePDFView  # Make sure this import is correct


# admin.py
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'date', 'due_date', 'status', 'total', 'pdf_actions')
    list_filter = ('status', 'date', 'customer')
    search_fields = ('invoice_number', 'customer__company_name')
    readonly_fields = ('subtotal', 'tax', 'total', 'invoice_number')
    fieldsets = (
        (None, {
            'fields': ('invoice_number', 'customer', 'date', 'due_date', 'status')
        }),
        ('Financials', {
            'fields': ('subtotal', 'tax', 'total', 'notes')
        }),
    )
    
    def pdf_actions(self, obj):
        return format_html(
            '<a class="button" href="{}" target="_blank">PDF</a>&nbsp;'
            '<a class="button" href="{}" download>Download</a>',
            reverse('admin:invoice_pdf', args=[obj.pk]),
            reverse('admin:invoice_pdf_download', args=[obj.pk])
        )
    pdf_actions.short_description = 'Actions'
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/pdf/',
                self.admin_site.admin_view(InvoicePDFView.as_view()),
                name='invoice_pdf'),
            path('<int:pk>/pdf/download/',
                self.admin_site.admin_view(InvoicePDFView.as_view()),
                name='invoice_pdf_download'),
        ]
        return custom_urls + urls
        
# Define choices for icons
ICON_CHOICES = [
    ('fa-microchip', 'Microchip'),
    ('fa-server', 'Server'),
    ('fa-laptop', 'Laptop'),
    ('fa-network-wired', 'Network'),
    ('fa-hdd', 'Hard Drive'),
]

class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
            'icon': forms.TextInput(attrs={
                'placeholder': 'e.g. fa-microchip'
            })
        }
# First try standard import, fallback to dummy class if package not installed
try:
    from import_export.admin import ImportExportModelAdmin
    from import_export import resources

    class ProductResource(resources.ModelResource):
        class Meta:
            model = Product
            fields = ('id', 'name', 'category__name', 'sku', 'price', 'stock', 'warranty_period')
            
except ImportError:
    ImportExportModelAdmin = admin.ModelAdmin
    print("django-import-export not installed, using standard admin")


class ProductResource(resources.ModelResource):
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(Category, 'name')
    )

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'sku', 'price', 'stock', 'warranty_period', 'is_active')
        export_order = fields
        skip_unchanged = True
        report_skipped = True

# admin.py - modify the ProductAdmin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'cost_price', 'selling_price', 'profit_display', 'margin_display')
    list_editable = ('cost_price', 'selling_price')
    
    # Custom display methods to handle None values
    def profit_display(self, obj):
        profit = obj.profit_amount()
        return f"${profit:.2f}" if profit is not None else "-"
    profit_display.short_description = "Profit"
    
    def margin_display(self, obj):
        margin = obj.profit_margin()
        return f"{margin:.2f}%" if margin is not None else "-"
    margin_display.short_description = "Margin"
    
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'sku', 'description')
        }),
        ('Pricing', {
            'fields': ('cost_price', 'selling_price', 'profit_display', 'margin_display')
        }),
        ('Inventory', {
            'fields': ('stock', 'barcode', 'warranty_period')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = ('profit_display', 'margin_display')
    
    def get_readonly_fields(self, request, obj=None):
        # Make profit fields read-only
        return super().get_readonly_fields(request, obj) + ('profit_display', 'margin_display')

'''
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'cost_price', 'selling_price', 'profit_amount', 'profit_margin')
    list_editable = ('cost_price', 'selling_price')
    readonly_fields = ('profit_amount', 'profit_margin')
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'sku', 'description')
        }),
        ('Pricing', {
            'fields': ('cost_price', 'selling_price', 'profit_amount', 'profit_margin')
        }),
        ('Inventory', {
            'fields': ('stock', 'barcode', 'warranty_period')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
'''

class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    change_list_template = 'admin/import_export/change_list.html'  # Critical line
    
    list_display = ('name', 'category', 'price', 'stock', 'warranty_period', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku', 'description')
    list_editable = ('price', 'stock', 'is_active')
    list_per_page = 25
    
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'sku')
        }),
        ('Details', {
            'fields': ('description', 'price', 'stock', 'image', 'warranty_period', 'is_active')
        }),
    )


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = ('id', 'name', 'category__name', 'sku', 'price', 'stock', 'warranty_period')
        export_order = fields


@admin.register(ProductEnquiry)
class ProductEnquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'email', 'product_interest', 'submitted_at', 'is_contacted')
    list_filter = ('is_contacted', 'product_interest', 'submitted_at')
    search_fields = ('name', 'email', 'company', 'subject')
    list_editable = ('is_contacted',)
    date_hierarchy = 'submitted_at'
    ordering = ('-submitted_at',)
# Register other models
admin.site.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ('name', 'icon_preview', 'description_short')
    search_fields = ('name', 'description')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Icon Settings', {
            'fields': ('icon',),
            'description': 'Optional: Choose from <a href="https://fontawesome.com/icons" target="_blank">Font Awesome icons</a>'
        }),
    )
    
class CategoryAdminForm(forms.ModelForm):
    icon = forms.ChoiceField(choices=ICON_CHOICES, required=False)
    
    class Meta:
        model = Category
        fields = '__all__'

    def icon_preview(self, obj):
        return format_html(f'<i class="fas {obj.icon}"></i> {obj.icon}') if obj.icon else "-"
    icon_preview.short_description = "Icon"
    
    def description_short(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_short.short_description = "Description"
    def icon_preview(self, obj):
        return format_html(f'<i class="fas {obj.icon}"></i> {obj.icon}') if obj.icon else "-"
    icon_preview.short_description = "Icon"
    
    def description_short(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_short.short_description = "Description"


admin.site.register(Order)
admin.site.register(Customer)
admin.site.register(Review)
admin.site.register(Cart)
admin.site.register(CartItem)

# Default admin site configuration
admin.site.site_header = "TRENDZ Trading Administration"
admin.site.site_title = "TRENDZ Admin Portal"
admin.site.index_title = "Welcome to TRENDZ Admin"
