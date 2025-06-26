from django.contrib import admin
from .models import Supplier, PurchaseOrder, PurchaseItem, PurchasePayment

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'is_active')
    search_fields = ('name', 'contact_person', 'phone')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('reference', 'supplier', 'order_date', 'total', 'status')
    list_filter = ('status', 'payment_mode')
    search_fields = ('reference', 'supplier__name')

@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'product', 'quantity', 'unit_cost', 'total')
    search_fields = ('product__name', 'purchase_order__reference')

@admin.register(PurchasePayment)
class PurchasePaymentAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'amount', 'payment_date', 'payment_method')
    list_filter = ('payment_method',)
    search_fields = ('purchase_order__reference', 'reference')