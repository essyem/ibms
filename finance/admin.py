# finance/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Category, FinanceTransaction, FinancialSummary, InventoryTransaction

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'description')
    list_filter = ('type',)
    search_fields = ('name', 'description')
    ordering = ['type', 'name']
    exclude = ('site',)  # Hide site field for simplicity

@admin.register(FinanceTransaction)
class FinanceTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_display', 
        'type_badge', 
        'category', 
        'amount_display', 
        'date', 
        'payment_method', 
        'source_display',
        'auto_generated_badge'
    )
    list_filter = ('type', 'category', 'payment_method', 'date', 'auto_generated', 'source_type')
    search_fields = ('description', 'reference')
    date_hierarchy = 'date'
    ordering = ['-date']
    exclude = ('site',)  # Hide site field for simplicity
    readonly_fields = ('auto_generated', 'source_type', 'source_id', 'created_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('type', 'category', 'amount', 'date')
        }),
        ('Details', {
            'fields': ('description', 'payment_method', 'reference', 'document')
        }),
        ('Integration Details', {
            'fields': ('auto_generated', 'source_type', 'source_id'),
            'classes': ('collapse',),
            'description': 'Information about auto-generated transactions from other apps'
        }),
        ('Recurring Settings', {
            'fields': ('recurring', 'frequency'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def transaction_display(self, obj):
        """Display transaction with icon"""
        icons = {
            'sale': '💰',
            'purchase': '🛒',
            'expense': '💸',
            'purchase_payment': '💳',
            'sale_receipt': '🧾'
        }
        icon = icons.get(obj.type, '📋')
        return f"{icon} {obj.reference or 'N/A'}"
    transaction_display.short_description = 'Transaction'
    
    def type_badge(self, obj):
        """Display transaction type with color badge"""
        colors = {
            'sale': 'green',
            'sale_receipt': 'green',
            'purchase': 'orange',
            'purchase_payment': 'red',
            'expense': 'red'
        }
        color = colors.get(obj.type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 15px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_type_display()
        )
    type_badge.short_description = 'Type'
    
    def amount_display(self, obj):
        """Display amount with currency and color coding"""
        color = 'green' if obj.type in ['sale', 'sale_receipt'] else 'red'
        amount_str = f"${obj.amount:,.2f}"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            amount_str
        )
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def source_display(self, obj):
        """Display source information with links"""
        if obj.auto_generated and obj.source_type and obj.source_id:
            if obj.source_type == 'invoice':
                return format_html(
                    '<a href="/admin/portal/invoice/{}/change/" target="_blank">📄 Invoice #{}</a>',
                    obj.source_id, obj.source_id
                )
            elif obj.source_type == 'purchase_order':
                return format_html(
                    '<a href="/admin/procurement/purchaseorder/{}/change/" target="_blank">🛒 PO #{}</a>',
                    obj.source_id, obj.source_id
                )
            elif obj.source_type == 'purchase_payment':
                return format_html(
                    '<a href="/admin/procurement/purchasepayment/{}/change/" target="_blank">💳 Payment #{}</a>',
                    obj.source_id, obj.source_id
                )
        return format_html('<span style="color: gray;">Manual Entry</span>')
    source_display.short_description = 'Source'
    
    def auto_generated_badge(self, obj):
        """Display auto-generated badge"""
        if obj.auto_generated:
            return format_html(
                '<span style="background-color: blue; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px;">AUTO</span>'
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px;">MANUAL</span>'
        )
    auto_generated_badge.short_description = 'Source'

@admin.register(FinancialSummary)
class FinancialSummaryAdmin(admin.ModelAdmin):
    list_display = (
        'period_display',
        'sales_summary',
        'purchase_summary', 
        'profit_summary',
        'cash_flow_summary',
        'updated_at'
    )
    list_filter = ('year', 'month')
    ordering = ['-year', '-month']
    exclude = ('site',)
    readonly_fields = (
        'total_sales', 'total_invoices', 'average_sale_value',
        'total_purchases', 'total_purchase_orders', 'total_purchase_payments',
        'gross_profit', 'profit_margin', 'cash_inflow', 'cash_outflow', 'net_cash_flow',
        'updated_at'
    )
    
    def period_display(self, obj):
        """Display period with calendar icon"""
        return f"📅 {obj.year}-{obj.month:02d}"
    period_display.short_description = 'Period'
    
    def sales_summary(self, obj):
        """Display sales metrics"""
        total_sales = float(obj.total_sales or 0)
        total_invoices = int(obj.total_invoices or 0)
        average_sale_value = float(obj.average_sale_value or 0)
        
        return format_html(
            '<div style="text-align: center;">'
            '<strong style="color: green;">${}</strong><br>'
            '<small>{} invoices</small><br>'
            '<small>Avg: ${}</small>'
            '</div>',
            f"{total_sales:,.2f}",
            total_invoices,
            f"{average_sale_value:,.2f}"
        )
    sales_summary.short_description = '💰 Sales'
    
    def purchase_summary(self, obj):
        """Display purchase metrics"""
        total_purchases = float(obj.total_purchases or 0)
        total_purchase_orders = int(obj.total_purchase_orders or 0)
        total_purchase_payments = float(obj.total_purchase_payments or 0)
        
        return format_html(
            '<div style="text-align: center;">'
            '<strong style="color: orange;">${}</strong><br>'
            '<small>{} orders</small><br>'
            '<small>Paid: ${}</small>'
            '</div>',
            f"{total_purchases:,.2f}",
            total_purchase_orders,
            f"{total_purchase_payments:,.2f}"
        )
    purchase_summary.short_description = '🛒 Purchases'
    
    def profit_summary(self, obj):
        """Display profit metrics"""
        gross_profit = float(obj.gross_profit or 0)
        profit_margin = float(obj.profit_margin or 0)
        color = 'green' if gross_profit >= 0 else 'red'
        
        return format_html(
            '<div style="text-align: center;">'
            '<strong style="color: {};">${}</strong><br>'
            '<small>{}% margin</small>'
            '</div>',
            color,
            f"{gross_profit:,.2f}",
            f"{profit_margin:.1f}"
        )
    profit_summary.short_description = '📈 Profit'
    
    def cash_flow_summary(self, obj):
        """Display cash flow metrics"""
        cash_inflow = float(obj.cash_inflow or 0)
        cash_outflow = float(obj.cash_outflow or 0)
        net_cash_flow = float(obj.net_cash_flow or 0)
        color = 'green' if net_cash_flow >= 0 else 'red'
        
        return format_html(
            '<div style="text-align: center;">'
            '<span style="color: green;">In: ${}</span><br>'
            '<span style="color: red;">Out: ${}</span><br>'
            '<strong style="color: {};">Net: ${}</strong>'
            '</div>',
            f"{cash_inflow:,.2f}",
            f"{cash_outflow:,.2f}",
            color,
            f"{net_cash_flow:,.2f}"
        )
    cash_flow_summary.short_description = '💸 Cash Flow'

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'type_badge',
        'quantity_display',
        'unit_cost',
        'total_cost_display',
        'profit_display',
        'date',
        'source_link'
    )
    list_filter = ('type', 'date', 'product__category')
    search_fields = ('product__name', 'product__sku', 'notes')
    date_hierarchy = 'date'
    ordering = ['-date']
    exclude = ('site',)
    readonly_fields = ('total_cost', 'total_revenue')
    
    def type_badge(self, obj):
        """Display transaction type with color badge"""
        colors = {
            'sale': 'green',
            'purchase': 'blue',
            'adjustment': 'orange',
            'return': 'red'
        }
        color = colors.get(obj.type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 15px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_type_display()
        )
    type_badge.short_description = 'Type'
    
    def quantity_display(self, obj):
        """Display quantity with direction indicator"""
        if obj.quantity > 0:
            return format_html('<span style="color: green;">▲ {}</span>', obj.quantity)
        else:
            return format_html('<span style="color: red;">▼ {}</span>', abs(obj.quantity))
    quantity_display.short_description = 'Qty'
    quantity_display.admin_order_field = 'quantity'
    
    def total_cost_display(self, obj):
        """Display total cost"""
        return f'${obj.total_cost:,.2f}'
    total_cost_display.short_description = 'Total Cost'
    total_cost_display.admin_order_field = 'total_cost'
    
    def profit_display(self, obj):
        """Display profit for sales"""
        profit = obj.profit()
        if profit != 0:
            color = 'green' if profit > 0 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">${}</span>',
                color, f"{profit:,.2f}"
            )
        return '-'
    profit_display.short_description = 'Profit'
    
    def source_link(self, obj):
        """Display source with clickable link"""
        if obj.invoice:
            return format_html(
                '<a href="/admin/portal/invoice/{}/change/" target="_blank">📄 Invoice #{}</a>',
                obj.invoice.id, obj.invoice.invoice_number
            )
        elif obj.purchase_order:
            return format_html(
                '<a href="/admin/procurement/purchaseorder/{}/change/" target="_blank">🛒 PO #{}</a>',
                obj.purchase_order.id, obj.purchase_order.reference
            )
        return '-'
    source_link.short_description = 'Source'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)