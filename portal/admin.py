from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.formats import base_formats
from import_export.widgets import ForeignKeyWidget
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from portal.models import (CartItem, Product, Category, Order, Customer, 
        Cart, ProductEnquiry, Invoice, InvoiceItem, SoldItem)
from portal.widgets import ProductSearchWidget
from django.utils.html import format_html
from django import forms
from django.urls import reverse, path
from django.views import View
from portal.views import InvoicePDFView
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.http import HttpResponse
from io import BytesIO
import uuid
from django.db.models import Sum, Value, CharField
from django.db.models.functions import Concat
from portal.forms import InvoiceItemForm
from xhtml2pdf import pisa
from django.db import models
from django.contrib.sites.shortcuts import get_current_site
from . import barcode_views
from django.contrib.admin.views.decorators import staff_member_required
from .resources import ProductResource

# Admin integration for barcode functionality
class BarcodeAdminMixin:
    """Mixin to add barcode functionality to admin"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('barcode-dashboard/', 
                 self.admin_site.admin_view(barcode_views.barcode_generator_dashboard), 
                 name='barcode_dashboard'),
            path('barcode-generate-bulk/', 
                 self.admin_site.admin_view(barcode_views.generate_bulk_barcodes), 
                 name='generate_bulk_barcodes'),
            path('barcode-generate-single/<int:product_id>/', 
                 self.admin_site.admin_view(barcode_views.generate_single_barcode), 
                 name='generate_single_barcode'),
            path('barcode-print-labels/', 
                 self.admin_site.admin_view(barcode_views.print_barcode_labels), 
                 name='print_barcode_labels'),
            path('barcode-preview/<int:product_id>/', 
                 self.admin_site.admin_view(barcode_views.preview_barcode), 
                 name='preview_barcode'),
            path('barcode-demo-labels/', 
                 self.admin_site.admin_view(barcode_views.demo_barcode_labels), 
                 name='demo_barcode_labels'),
        ]
        return custom_urls + urls

# Unregister Invoice if already registered
if admin.site.is_registered(Invoice):
    admin.site.unregister(Invoice)

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('product', 'quantity', 'unit_price', 'subtotal')
    readonly_fields = ('subtotal',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'product':
            kwargs['widget'] = ProductSearchWidget()
            kwargs['queryset'] = Product.objects.filter(is_active=True).select_related('category')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        
        # Properly annotated queryset with output_field specified
        formset.form.base_fields['product'].queryset = Product.objects.filter(
            is_active=True
        ).annotate(
            price_display=Concat(
                'name', 
                Value(' - QAR '), 
                'unit_price',
                output_field=CharField()
            )
        ).select_related('category')
        
        if 'unit_price' in formset.form.base_fields:
            formset.form.base_fields['unit_price'].widget.attrs.update({
                'step': '0.01',
                'min': '0.01',
                'class': 'unit-price-input'
            })
        else:
            raise KeyError("'unit_price' field is missing in the form base fields.")

        return formset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            kwargs["queryset"] = Product.objects.annotate(
                price_display=Concat(
                    'name',
                    Value(' - QAR '),
                    'unit_price',
                    output_field=CharField()
                )
            ).select_related('category')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline]
    list_display = ('invoice_number', 'customer_name', 'date', 'status', 'grand_total', 'payment_mode_display', 'pdf_actions', )
    exclude = ('site',)  # Hide site field for simplicity
    fieldsets = (
        ('Customer & Invoice Details', {
            'fields': ('customer', 'due_date', 'status')
        }),
        ('Pricing Details', {
            'fields': (
                ('subtotal', 'tax'),
                ('discount_type', 'discount_value', 'discount_amount'),
                ('total', 'grand_total')
            ),
            'classes': ('wide',)
        }),
        ('Payment Details', {
            'fields': ('payment_mode',),
            'classes': ('wide',)
        }),
        ('Split Payment Details', {
            'fields': ('cash_amount', 'pos_amount', 'other_amount', 'other_method'),
            'classes': ('collapse',),
            'description': 'Only applicable when payment mode is "Split Payment"'
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('date', 'subtotal', 'tax', 'discount_amount', 'total', 'grand_total')
    list_filter = ('status', 'date', 'due_date', 'payment_mode')
    search_fields = ('invoice_number', 'customer__name', 'notes')
    date_hierarchy = 'date'
    ordering = ('-date',)
    actions = ['mark_as_paid', 'mark_as_unpaid']
    
    def save_model(self, request, obj, form, change):
        if not change and not obj.invoice_number:
            obj.invoice_number = str(uuid.uuid4())  # Temporary unique ID
        super().save_model(request, obj, form, change)
        obj.update_totals()
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing invoice
            return self.readonly_fields + ('tax',)
        return self.readonly_fields
    
    def customer_name(self, obj):
        return obj.customer.full_name if obj.customer else "Walk-in"
    customer_name.short_description = 'Customer'

    def payment_mode_display(self, obj):
        return dict(Invoice.PAYMENT_MODES).get(obj.payment_mode, "Unknown")
    payment_mode_display.short_description = 'Payment Mode'

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, InvoiceItem):
                # Always ensure unit_price is set from product
                if instance.product:
                    if not instance.unit_price or instance.unit_price == 0:
                        instance.unit_price = instance.product.unit_price
                instance.save()
        
        # Handle deleted objects
        for obj in formset.deleted_objects:
            obj.delete()
            
        formset.save_m2m()
        form.instance.update_totals()

    class Media:
        js = (
            'admin/js/invoice_items.js',
            'admin/js/invoice_admin.js',
        )
        css = {
            'all': ('admin/css/invoice_admin.css',)
        }

    def pdf_actions(self, obj):
        """
        Creates PDF action buttons for admin list view
        """
        return format_html(
            '<a class="button" href="{}" target="_blank" style="padding: 5px 10px; background: #417690; color: white; text-decoration: none; border-radius: 4px; margin-right: 5px;">View PDF</a>'
            '<a class="button" href="{}?download=true" style="padding: 5px 10px; background: #79aec8; color: white; text-decoration: none; border-radius: 4px;">Download PDF</a>',
            reverse('admin:invoice_pdf', args=[obj.pk]),
            reverse('admin:invoice_pdf', args=[obj.pk])
        )
    pdf_actions.short_description = 'PDF Actions'
    pdf_actions.allow_tags = True

    def get_urls(self):
        """
        Adds custom URLs for PDF handling
        """
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/pdf/',
                InvoicePDFView.as_view(),
                name='invoice_pdf'),
        ]
        return custom_urls + urls


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product', 'quantity', 'unit_price', 'subtotal')
    search_fields = ('invoice__invoice_number', 'product__name')
    list_filter = ('invoice__status',)
    exclude = ('site',)  # Hide site field for simplicity


class ProductResource(resources.ModelResource):
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(Category, 'name')
    )

    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'sku', 'cost_price', 'unit_price', 'stock', 'warranty_period', 'is_active')
        export_order = fields
        skip_unchanged = True
        report_skipped = True


ICON_CHOICES = [
    ('fa-microchip', 'Microchip'),
    ('fa-server', 'Server'),
    ('fa-laptop', 'Laptop'),
    ('fa-network-wired', 'Network'),
    ('fa-hdd', 'Hard Drive'),
]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'full_name', 'phone')
    readonly_fields = ('customer_id',)
    search_fields = ('customer_id', 'full_name')
    exclude = ('site',)  # Hide site field for simplicity


class CategoryAdminForm(forms.ModelForm):
    """Form for Category admin."""
    icon = forms.ChoiceField(choices=ICON_CHOICES, required=False)
    
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

    class ProductResourceExport(resources.ModelResource):
        class Meta:
            model = Product
            fields = ('id', 'name', 'category__name', 'sku', 'cost_price', 'unit_price', 'stock', 'warranty_period')

except ImportError:
    ImportExportModelAdmin = admin.ModelAdmin
    print("django-import-export not installed, using standard admin")


@admin.register(Product)
class ProductAdmin(BarcodeAdminMixin, ImportExportModelAdmin):
    resource_class = ProductResource
    change_list_template = 'admin/import_export/change_list.html'
    exclude = ('site',)  # Hide site field for simplicity

    list_display = ('name', 'category', 'sku', 'barcode_display', 'unit_price', 'cost_price', 'stock', 'warranty_period', 'is_active')
    list_filter = ('category', 'is_active', 'barcode')
    search_fields = ('name', 'sku', 'description', 'barcode', 'category__name')
    list_editable = ('unit_price', 'stock', 'is_active')
    list_per_page = 25
    actions = ['generate_barcodes_for_selected']
    
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'sku')
        }),
        ('Details', {
            'fields': ('description', 'cost_price', 'unit_price', 'stock', 'warranty_period', 'is_active')
        }),
        ('Barcode & Media', {
            'fields': ('barcode', 'image'),
            'description': 'Barcode will be auto-generated if left empty'
        }),
    )
    
    def barcode_display(self, obj):
        if obj.barcode:
            return format_html(
                '<code style="background: #f8f9fa; padding: 2px 4px; border-radius: 3px;">{}</code>',
                obj.barcode
            )
        else:
            return format_html(
                '<span style="color: #dc3545;">No Barcode</span>'
            )
    barcode_display.short_description = 'Barcode'
    
    def generate_barcodes_for_selected(self, request, queryset):
        """Admin action to generate barcodes for selected products"""
        from portal.barcode_utils import BarcodeGenerator
        
        # Filter products without barcodes
        products_without_barcode = queryset.filter(
            models.Q(barcode__isnull=True) | models.Q(barcode='')
        )
        
        if not products_without_barcode.exists():
            self.message_user(request, "All selected products already have barcodes.", level='warning')
            return
        
        success_count = 0
        error_count = 0
        
        for product in products_without_barcode:
            result = BarcodeGenerator.generate_barcode_for_product(product)
            if result['success']:
                success_count += 1
            else:
                error_count += 1
        
        if success_count > 0:
            self.message_user(
                request, 
                f'Successfully generated {success_count} barcode(s).', 
                level='success'
            )
        
        if error_count > 0:
            self.message_user(
                request, 
                f'Failed to generate {error_count} barcode(s).', 
                level='error'
            )
    
    generate_barcodes_for_selected.short_description = "🏷️ Generate barcodes for selected products"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('barcode-generator/', 
                 self.admin_site.admin_view(self.barcode_generator_view), 
                 name='product_barcode_generator'),
        ]
        return custom_urls + urls
    
    def barcode_generator_view(self, request):
        """Redirect to barcode generator dashboard"""
        from django.shortcuts import redirect
        return redirect('barcode_generator_dashboard')
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Count products without barcodes
        products_without_barcode = self.get_queryset(request).filter(
            models.Q(barcode__isnull=True) | models.Q(barcode='')
        ).count()
        
        extra_context['products_without_barcode'] = products_without_barcode
        extra_context['show_barcode_generator'] = products_without_barcode > 0
        
        return super().changelist_view(request, extra_context)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username',)
    exclude = ('site',)  # Hide site field for simplicity


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'requested_delivery_date')
    search_fields = ('product__name', 'cart__user__username')
    exclude = ('site',)  # Hide site field for simplicity


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'payment_method', 'total_price', 'status', 'order_date', 'delivery_zone')
    search_fields = ('order_number', 'customer_name', 'customer_email', 'customer_phone', 'user__username')
    list_filter = ('payment_method', 'status', 'order_date', 'delivery_zone')
    exclude = ('site',)  # Hide site field for simplicity
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'total_price', 'order_date')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'transfer_receipt'),
            'description': 'Bank transfer receipt is required for Bank Transfer payments.'
        }),
        ('Delivery Address', {
            'fields': ('delivery_zone', 'delivery_street', 'delivery_building', 'delivery_flat', 'delivery_additional_info'),
            'description': 'Detailed delivery address information for accurate delivery.'
        }),
        ('Legacy Fields', {
            'fields': ('delivery_address', 'preferred_contact'),
            'classes': ('collapse',),
            'description': 'Legacy fields maintained for backward compatibility.'
        }),
    )
    
    readonly_fields = ('order_date', 'order_number')
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of orders with payment receipts"""
        if obj and obj.transfer_receipt:
            return False
        return super().has_delete_permission(request, obj)
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form based on payment method"""
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.payment_method == 'cod' and 'transfer_receipt' in form.base_fields:
            form.base_fields['transfer_receipt'].help_text = 'Not applicable for Cash on Delivery orders.'
        return form


@admin.register(ProductEnquiry)
class ProductEnquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'product_interest', 'submitted_at', 'is_contacted')
    search_fields = ('name', 'email', 'phone')
    exclude = ('site',)  # Hide site field for simplicity


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ('name', 'icon_preview', 'description_short')
    search_fields = ('name', 'description')
    exclude = ('site',)  # Hide site field for simplicity
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Icon Settings', {
            'fields': ('icon',),
            'description': 'Optional: Choose from <a href="https://fontawesome.com/icons" target="_blank">Font Awesome icons</a>'
        }),
    )
    
    def icon_preview(self, obj):
        return format_html(f'<i class="fas {obj.icon}"></i> {obj.icon}') if obj.icon else "-"
    icon_preview.short_description = "Icon"
    
    def description_short(self, obj):
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
    description_short.short_description = "Description"


@admin.register(SoldItem)
class SoldItemAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'quantity', 'unit_price', 'subtotal_display', 'invoice_number', 'date_sold', 'customer_name')
    list_filter = ('date_sold', 'category_name', 'product_name')
    search_fields = ('product_name', 'product_sku', 'invoice__invoice_number', 'invoice__customer__full_name')
    readonly_fields = ('invoice', 'product_name', 'quantity', 'unit_price', 'date_sold', 'product', 'product_sku', 'category_name')
    ordering = ('-date_sold',)
    
    def subtotal_display(self, obj):
        return f"QAR {obj.subtotal():.2f}"
    subtotal_display.short_description = "Subtotal"
    
    def invoice_number(self, obj):
        return obj.invoice.invoice_number
    invoice_number.short_description = "Invoice #"
    
    def customer_name(self, obj):
        return obj.invoice.customer.company_name or obj.invoice.customer.full_name
    customer_name.short_description = "Customer"
    
    def has_add_permission(self, request):
        # Prevent manual addition - these should only be created by signals
        return False
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing - these are historical records
        return False
    
    def get_queryset(self, request):
        # Order by date sold descending by default
        qs = super().get_queryset(request)
        return qs.select_related('invoice', 'invoice__customer', 'product').order_by('-date_sold')


# Register a simple admin class for barcode management
