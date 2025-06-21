# finance/admin.py
from django.contrib import admin
from .models import Category, FinanceTransaction

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'description')
    list_filter = ('type',)
    search_fields = ('name', 'description')

@admin.register(FinanceTransaction)
class FinanceTransactionAdmin(admin.ModelAdmin):
    list_display = ('type', 'category', 'amount', 'date', 'payment_method', 'created_by')
    list_filter = ('type', 'category', 'payment_method', 'date')
    search_fields = ('description', 'reference')
    date_hierarchy = 'date'
    fieldsets = (
        (None, {
            'fields': ('type', 'category', 'amount', 'date')
        }),
        ('Details', {
            'fields': ('description', 'payment_method', 'reference', 'document')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)