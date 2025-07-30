from django.contrib import admin
from .models import Supplier, PurchaseOrder, PurchaseItem, PurchasePayment
from django import forms
from portal.models import Product
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from django.utils.html import format_html

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1
    fields = ('product', 'quantity', 'unit_cost', 'total')
    readonly_fields = ('total',)
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        
        # Annotate products with price display for better UX
        formset.form.base_fields['product'].queryset = Product.objects.annotate(
            price_display=Concat(
                'name', 
                Value(' - $'), 
                'unit_price',
                output_field=CharField()
            )
        ).select_related('category')
        
        # Add proper attributes to form fields
        formset.form.base_fields['unit_cost'].widget.attrs.update({
            'step': '0.01',
            'min': '0.01',
            'class': 'unit-cost-input'
        })
        
        formset.form.base_fields['quantity'].widget.attrs.update({
            'min': '1',
            'class': 'quantity-input'
        })
        
        return formset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            kwargs["queryset"] = Product.objects.annotate(
                price_display=Concat(
                    'name',
                    Value(' - $'),
                    'unit_price',
                    output_field=CharField()
                )
            ).select_related('category')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class PurchasePaymentInline(admin.TabularInline):
    model = PurchasePayment
    extra = 0
    fields = ('amount', 'payment_date', 'payment_method', 'status', 'reference')
    readonly_fields = ('status',)
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        # Allow adding payments only if PO exists
        return obj is not None

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
    inlines = [PurchaseItemInline, PurchasePaymentInline]
    list_display = ('reference', 'supplier', 'order_date', 'total', 'status', 'payment_mode', 'payment_status')
    list_filter = ('status', 'payment_mode', 'order_date')
    search_fields = ('reference', 'supplier__name', 'notes')
    readonly_fields = ('subtotal', 'total', 'created_at', 'updated_at')
    date_hierarchy = 'order_date'
    ordering = ['-order_date']
    exclude = ('site',)  # Hide site field for simplicity
    
    def payment_status(self, obj):
        """Display payment status based on related payments"""
        payments = obj.payments.all()
        if not payments.exists():
            return format_html('<span style="color: gray;">No Payments</span>')
        
        total_paid = sum(p.amount for p in payments)
        if total_paid >= obj.total:
            return format_html('<span style="color: green; font-weight: bold;">Paid</span>')
        elif total_paid > 0:
            percentage = (total_paid / obj.total) * 100
            return format_html('<span style="color: orange; font-weight: bold;">Partial ({:.1f}%)</span>', percentage)
        else:
            return format_html('<span style="color: red; font-weight: bold;">Pending</span>')
    payment_status.short_description = 'Payment Status'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "supplier":
            # Filter only active suppliers
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
            'description': 'Subtotal and Total are auto-calculated. Tax can be entered manually.'
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
            po.total = po.subtotal + (po.tax or Decimal('0.00'))
            po.save(update_fields=['subtotal', 'total'])

@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'product', 'quantity', 'unit_cost', 'total')
    search_fields = ('product__name', 'purchase_order__reference')
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
            po.total = po.subtotal + (po.tax or Decimal('0.00'))
            po.save(update_fields=['subtotal', 'total'])

@admin.register(PurchasePayment)
class PurchasePaymentAdmin(admin.ModelAdmin):
    list_display = (
        'purchase_order_ref', 
        'supplier_name', 
        'amount_paid', 
        'amount_due_display', 
        'payment_date', 
        'payment_method', 
        'status_display',
        'payment_percentage_display'
    )
    list_filter = ('status', 'payment_method', 'payment_date', 'due_date')
    search_fields = (
        'purchase_order__reference', 
        'purchase_order__supplier__name', 
        'reference', 
        'notes'
    )
    readonly_fields = (
        'balance_due', 
        'payment_percentage', 
        'created_at', 
        'updated_at'
    )
    date_hierarchy = 'payment_date'
    ordering = ['-payment_date']
    
    fieldsets = (
        ('Purchase Order Information', {
            'fields': ('purchase_order',)
        }),
        ('Payment Details', {
            'fields': ('amount', 'amount_due', 'payment_date', 'due_date', 'payment_method', 'reference')
        }),
        ('Status & Progress', {
            'fields': ('status', 'balance_due', 'payment_percentage'),
            'classes': ('collapse',)
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
    
    def purchase_order_ref(self, obj):
        """Display purchase order reference with link"""
        if obj.purchase_order:
            return format_html(
                '<a href="{}">{}</a>',
                f'/admin/procurement/purchaseorder/{obj.purchase_order.id}/change/',
                obj.purchase_order.reference
            )
        return '-'
    purchase_order_ref.short_description = 'PO Reference'
    purchase_order_ref.admin_order_field = 'purchase_order__reference'
    
    def supplier_name(self, obj):
        """Display supplier name"""
        if obj.purchase_order and obj.purchase_order.supplier:
            return obj.purchase_order.supplier.name
        return '-'
    supplier_name.short_description = 'Supplier'
    supplier_name.admin_order_field = 'purchase_order__supplier__name'
    
    def amount_paid(self, obj):
        """Display amount with currency formatting"""
        return f'${obj.amount:,.2f}'
    amount_paid.short_description = 'Amount Paid'
    amount_paid.admin_order_field = 'amount'
    
    def amount_due_display(self, obj):
        """Display amount due with currency formatting"""
        return f'${obj.amount_due:,.2f}'
    amount_due_display.short_description = 'Amount Due'
    amount_due_display.admin_order_field = 'amount_due'
    
    def status_display(self, obj):
        """Display status with color coding"""
        status_colors = {
            'paid': 'green',
            'partial': 'orange',
            'pending': 'gray',
            'overdue': 'red'
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    def payment_percentage_display(self, obj):
        """Display payment percentage with progress bar"""
        percentage = obj.payment_percentage
        if percentage >= 100:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<div style="background-color: #f0f0f0; border-radius: 10px; width: 100px; height: 20px; position: relative;">'
            '<div style="background-color: {}; width: {}%; height: 100%; border-radius: 10px;"></div>'
            '<span style="position: absolute; top: 0; left: 0; right: 0; text-align: center; line-height: 20px; font-size: 12px; font-weight: bold;">{:.1f}%</span>'
            '</div>',
            color, min(percentage, 100), percentage
        )
    payment_percentage_display.short_description = 'Progress'
    payment_percentage_display.admin_order_field = 'amount'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "purchase_order":
            # Show PO reference and supplier for better UX
            kwargs["queryset"] = PurchaseOrder.objects.select_related('supplier').order_by('-created_at')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
