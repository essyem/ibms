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
        Review, Cart, ProductEnquiry, Invoice, InvoiceItem)
from django.utils.html import format_html
from django import forms
from django.urls import reverse, path
from django.views import View  # Add this import for View
from portal.views import InvoicePDFView  # Make sure this import is correct
from django.shortcuts import get_object_or_404  # <-- Add this import
from django.template.loader import get_template  # <-- Add this import
from django.http import HttpResponse  # <-- Add this import
from io import BytesIO  # <-- Add this import
import uuid
from django.db.models import Sum
from django.db.models import Value, CharField, CharField
from django.db.models.functions import Concat
from portal.forms import InvoiceItemForm  # Ensure this import is correct
from xhtml2pdf import pisa  # <-- Add this import

# portal/admin.py
if admin.site.is_registered(Invoice):
    admin.site.unregister(Invoice)

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('product', 'quantity', 'selling_price', 'cost_price', 'total')
    readonly_fields = ('cost_price', 'total')
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        
        # Properly annotated queryset with output_field specified
        formset.form.base_fields['product'].queryset = Product.objects.annotate(
            price_display=Concat(
                'name', 
                Value(' - $'), 
                'selling_price',
                output_field=CharField()
            )
        ).select_related('category')
        
        formset.form.base_fields['selling_price'].widget.attrs.update({
            'step': '0.01',
            'min': '0.01',
            'class': 'selling-price-input'
        })
        
        return formset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            kwargs["queryset"] = Product.objects.annotate(
                price_display=Concat(
                    'name',
                    Value(' - $'),
                    'selling_price',
                    output_field=CharField()
                )
            ).select_related('category')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline]
    list_display = ('invoice_number', 'customer_name', 'date', 'due_date', 'status', 'grand_total', 'payment_mode_display', 'pdf_actions', )
    fieldsets = (
        (None, {
            'fields': ('customer', 'due_date', 'status', 'notes')
        }),
        ('Pricing', {
            'fields': (
                ('subtotal', 'tax'),
                ('discount_type', 'discount_value', 'discount_amount'),
                ('total', 'grand_total')
            ),
            'classes': ('wide',)
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
                if instance.product and not instance.selling_price:
                    instance.selling_price = instance.product.selling_price
                instance.save()
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
            reverse('admin:invoice_pdf', args=[obj.pk])  # Same URL but with download param
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
                self.admin_site.admin_view(InvoicePDFView.as_view()),
                name='invoice_pdf'),
        ]
        return custom_urls + urls
    

    

    
@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product_name', 'quantity', 'selling_price', 'cost_price', 'total_amount')
    list_filter = ('invoice__status', 'product__category')
    search_fields = ('invoice__invoice_number', 'product__name')
    fieldsets = (
        (None, {
            'fields': ('invoice', 'product', 'quantity', 'selling_price')
        }),
        ('Financials', {
            'fields': ('cost_price', 'total'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('cost_price', 'total')
    
    def product_name(self, obj):
        return obj.product.name if obj.product else "No Product"
    product_name.short_description = 'Product'
    
    def total_amount(self, obj):
        return obj.total if obj.product else "N/A"
    total_amount.short_description = 'Total'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'invoice')


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


ICON_CHOICES = [
    ('fa-microchip', 'Microchip'),
    ('fa-server', 'Server'),
    ('fa-laptop', 'Laptop'),
    ('fa-network-wired', 'Network'),
    ('fa-hdd', 'Hard Drive'),
]

# portal/admin.py
class InvoicePDFView(View):
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=self.kwargs['pk'])
        download = 'download' in request.GET  # Check for ?download=true
        
        # PDF generation code
        template = get_template('portal/invoice_pdf.html')
        html = template.render({'invoice': invoice})
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = f"Invoice_{invoice.invoice_number}.pdf"
            content = "attachment" if download else "inline"
            response['Content-Disposition'] = f'{content}; filename="{filename}"'
            return response
        return HttpResponse("Error generating PDF", status=400)

# ...existing code...

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'full_name', 'phone')
    readonly_fields = ('customer_id',)
    search_fields = ('customer_id', 'full_name')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'sku', 'cost_price', 'selling_price', 'stock', 'warranty_period', 'is_active', 'profit_display', 'margin_display')
    list_editable = ('cost_price', 'selling_price', 'stock', 'is_active')
    search_fields = ('name', 'sku', 'description')
    list_filter = ('category', 'is_active')
    list_per_page = 25

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

    def profit_display(self, obj):
        profit = obj.profit_amount()
        return f"${profit:.2f}" if profit is not None else "-"
    profit_display.short_description = "Profit"

    def margin_display(self, obj):
        margin = obj.profit_margin()
        return f"{margin:.2f}%" if margin is not None else "-"
    margin_display.short_description = "Margin"

    def get_readonly_fields(self, request, obj=None):
        return super().get_readonly_fields(request, obj) + ('profit_display', 'margin_display')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            kwargs["queryset"] = Product.objects.annotate(
                price_info=Concat(
                    'name', Value(' - $'), 
                    'selling_price',
                    output_field=CharField()
                )
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CategoryAdminForm(forms.ModelForm):
    """Form for Category admin (placeholder)."""
    pass
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
admin.site.register(Review)
admin.site.register(Cart)

# Default admin site configuration
admin.site.site_header = "TRENDZ Trading Administration"
admin.site.site_title = "TRENDZ Admin Portal"
admin.site.index_title = "Welcome to TRENDZ Admin"




