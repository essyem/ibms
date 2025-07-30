from django.contrib import admin
from .models import Supplier, PurchaseOrder, PurchaseItem, PurchasePayment
from .forms import PurchaseOrderForm, PurchaseItemForm
from django import forms
from portal.models import Product
from django.db.models import Value, CharField
from django.db.models.functions import Concat

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1
    fields = ('product', 'quantity', 'unit_cost', 'total')
    readonly_fields = ('total',)
    autocomplete_fields = ('product',)
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        
        # Add proper attributes to form fields
        if 'unit_cost' in formset.form.base_fields:
            formset.form.base_fields['unit_cost'].widget.attrs.update({
                'step': '0.01',
                'min': '0.01',
                'class': 'unit-cost-input'
            })
        
        if 'quantity' in formset.form.base_fields:
            formset.form.base_fields['quantity'].widget.attrs.update({
                'min': '1',
                'class': 'quantity-input'
            })
        
        return formset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            kwargs["queryset"] = Product.objects.select_related('category').filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'is_active')
    search_fields = ('name', 'contact_person', 'phone')
    list_filter = ('is_active',)
    ordering = ['name']
    exclude = ('site',)  # Hide site field for simplicity
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'contact_person', 'phone', 'email', 'is_active')
        }),
        ('Address & Tax Information', {
            'fields': ('address', 'tax_id'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    change_form_template = 'admin/procurement/purchaseorder_change_form.html'
    inlines = [PurchaseItemInline]
    list_display = ('reference', 'supplier', 'order_date', 'total', 'status', 'payment_mode')
    list_filter = ('status', 'payment_mode', 'order_date')
    search_fields = ('reference', 'supplier__name', 'notes')
    readonly_fields = ('subtotal', 'total', 'created_at', 'updated_at')
    date_hierarchy = 'order_date'
    ordering = ['-order_date']
    exclude = ('site',)  # Hide site field for simplicity
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "supplier":
            # Filter only active suppliers - no site filtering needed
            kwargs["queryset"] = Supplier.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    fieldsets = (
        ('Purchase Order Details', {
            'fields': ('supplier', 'reference', 'order_date', 'delivery_date', 'status')
        }),
        ('Payment Information', {
            'fields': ('payment_mode', 'payment_due')
        }),
        ('Totals', {
            'fields': ('subtotal', 'tax', 'total'),
            'classes': ('collapse',),
            'description': 'Subtotal and Total are auto-calculated. Tax can be entered manually for international purchases.'
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Ensure totals are updated after saving
        try:
            obj.update_totals()
        except Exception as e:
            # If update_totals fails, use fallback calculation
            from decimal import Decimal
            obj.subtotal = sum(item.total for item in obj.items.all()) or Decimal('0.00')
            # Tax is manually entered, only calculate total
            obj.total = obj.subtotal + (obj.tax or Decimal('0.00'))
            obj.save(update_fields=['subtotal', 'total'])
    
    def save_formset(self, request, form, formset, change):
        """Update totals after saving formset (inline items)"""
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, PurchaseItem):
                if instance.product and not instance.unit_cost:
                    # Set default unit cost based on product cost price
                    instance.unit_cost = instance.product.cost_price
                instance.save()
        formset.save_m2m()
        # Update purchase order totals
        try:
            form.instance.update_totals()
        except Exception as e:
            # Fallback calculation
            from decimal import Decimal
            po = form.instance
            po.subtotal = sum(item.total for item in po.items.all()) or Decimal('0.00')
            # Tax is manually entered, only calculate total
            po.total = po.subtotal + (po.tax or Decimal('0.00'))
            po.save(update_fields=['subtotal', 'total'])

# Keep the separate PurchaseItem admin for standalone editing if needed
@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    change_form_template = 'admin/procurement/purchaseitem_change_form.html'
    list_display = ('purchase_order', 'product', 'quantity', 'unit_cost', 'total')
    search_fields = ('product__name', 'product__sku', 'product__barcode', 'product__category__name', 'purchase_order__reference')
    readonly_fields = ('total',)
    autocomplete_fields = ('product',)
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Ensure the purchase order totals are updated
        try:
            obj.purchase_order.update_totals()
        except Exception:
            # Fallback calculation
            from decimal import Decimal
            po = obj.purchase_order
            po.subtotal = sum(item.total for item in po.items.all()) or Decimal('0.00')
            # Tax is manually entered, only calculate total
            po.total = po.subtotal + (po.tax or Decimal('0.00'))
            po.save(update_fields=['subtotal', 'total'])

@admin.register(PurchasePayment)
class PurchasePaymentAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'amount', 'payment_date', 'payment_method', 'reference')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('purchase_order__reference', 'reference', 'purchase_order__supplier__name')
    date_hierarchy = 'payment_date'
    ordering = ['-payment_date']
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('purchase_order', 'amount', 'payment_date', 'payment_method')
        }),
        ('Reference & Notes', {
            'fields': ('reference', 'notes')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Update purchase order paid amount
        obj.purchase_order.update_paid_amount()