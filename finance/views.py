# finance/views.py
from django.views.generic import ListView, CreateView, DetailView, TemplateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.conf import settings
import json
from datetime import date, timedelta

from .models import FinanceTransaction, Category, DailyRevenue
from finance.forms import TransactionForm
from procurement.models import PurchaseOrder, PurchasePayment

# Import for PDF generation
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


def category_api(request):
    transaction_type = request.GET.get('type', '')
    categories = Category.objects.filter(type=transaction_type).values('id', 'name')
    return JsonResponse(list(categories), safe=False)


class FinanceIndexView(TemplateView):
    template_name = 'finance/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current date info
        today = timezone.now().date()
        current_month_start = today.replace(day=1)
        
        # Calculate today's summary
        today_transactions = FinanceTransaction.objects.filter(date=today)
        today_income = today_transactions.filter(
            type__in=['sale', 'sale_receipt']
        ).aggregate(total=Sum('amount'))['total'] or 0
        today_expense = today_transactions.filter(
            type__in=['purchase', 'expense']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate month's summary
        month_transactions = FinanceTransaction.objects.filter(date__gte=current_month_start)
        month_income = month_transactions.filter(
            type__in=['sale', 'sale_receipt']
        ).aggregate(total=Sum('amount'))['total'] or 0
        month_expense = month_transactions.filter(
            type__in=['purchase', 'expense']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Recent transactions
        recent_transactions = FinanceTransaction.objects.select_related('category').order_by('-created_at')[:10]
        
        context.update({
            'total_transactions': FinanceTransaction.objects.count(),
            'recent_transactions': recent_transactions,
            'today_income': today_income,
            'today_expense': today_expense,
            'today_net': today_income - today_expense,
            'month_income': month_income,
            'month_expense': month_expense,
            'month_net': month_income - month_expense,
        })
        return context


class TransactionCreateView(CreateView):
    model = FinanceTransaction
    form_class = TransactionForm
    template_name = 'finance/transaction_form.html'
    success_url = reverse_lazy('finance:transaction_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Transaction created successfully!')
        return super().form_valid(form)

class TransactionUpdateView(UpdateView):
    model = FinanceTransaction
    form_class = TransactionForm
    template_name = 'finance/transaction_form.html'
    success_url = reverse_lazy('finance:transaction_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Transaction updated successfully!')
        return super().form_valid(form)

class TransactionListView(ListView):
    model = FinanceTransaction
    template_name = 'finance/transaction_list.html'
    paginate_by = 20
    context_object_name = 'transactions'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        transaction_type = self.request.GET.get('type')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if transaction_type:
            queryset = queryset.filter(type=transaction_type)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        return queryset.order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate totals for the filtered queryset
        transactions = self.get_queryset()
        
        total_income = transactions.filter(
            type__in=['sale', 'sale_receipt']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_expenses = transactions.filter(
            type__in=['purchase', 'expense']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        net_balance = total_income - total_expenses
        
        context.update({
            'total_transactions': transactions.count(),
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_balance': net_balance,
        })
        
        return context


class TransactionDetailView(DetailView):
    model = FinanceTransaction
    template_name = 'finance/transaction_detail.html'
    context_object_name = 'transaction'

class FinanceReportView(TemplateView):
    template_name = 'finance/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add report data to context
        transactions = FinanceTransaction.objects.all()
        context.update({
            'total_transactions': transactions.count(),
            'total_income': transactions.filter(
                type__in=['sale', 'sale_receipt']
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'total_expenses': transactions.filter(
                type__in=['purchase', 'expense']
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'transactions_by_type': transactions.values('type').annotate(
                count=Count('id'),
                total=Sum('amount')
            ),
        })
        return context


# Purchase Payment Views
class PurchasePaymentListView(ListView):
    model = PurchasePayment
    template_name = 'portal/purchase_payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payments = PurchasePayment.objects.all()
        
        context.update({
            'total_payments': payments.count(),
            'pending_count': payments.filter(status='pending').count(),
            'overdue_count': payments.filter(status='overdue').count(),
            'total_due': payments.aggregate(total=Sum('amount_due'))['total'] or 0,
            'total_paid': payments.aggregate(total=Sum('amount_paid'))['total'] or 0,
            'total_outstanding': payments.aggregate(
                total=Sum('amount_due') - Sum('amount_paid')
            )['total'] or 0,
        })
        return context


class PurchasePaymentCreateView(CreateView):
    model = PurchasePayment
    template_name = 'portal/purchase_payment_form.html'
    fields = ['purchase_order', 'amount_due', 'due_date', 'payment_method', 'notes']
    success_url = reverse_lazy('finance:purchase_payment_list')
    
    def get_initial(self):
        initial = super().get_initial()
        order_id = self.request.GET.get('order')
        if order_id:
            try:
                order = PurchaseOrder.objects.get(pk=order_id)
                initial['purchase_order'] = order
                initial['amount_due'] = order.total
            except PurchaseOrder.DoesNotExist:
                pass
        return initial
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Purchase payment record created successfully!')
        return super().form_valid(form)


class PurchasePaymentDetailView(DetailView):
    model = PurchasePayment
    template_name = 'portal/purchase_payment_detail.html'
    context_object_name = 'payment'


class PurchasePaymentUpdateView(UpdateView):
    model = PurchasePayment
    template_name = 'portal/purchase_payment_form.html'
    fields = ['amount_paid', 'payment_date', 'payment_method', 'payment_reference', 'notes']
    success_url = reverse_lazy('finance:purchase_payment_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment updated successfully!')
        return super().form_valid(form)


class PurchasePaymentPayView(UpdateView):
    """Quick payment recording view"""
    model = PurchasePayment
    template_name = 'portal/purchase_payment_pay.html'
    fields = ['amount_paid', 'payment_date', 'payment_method', 'payment_reference']
    success_url = reverse_lazy('finance:purchase_payment_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['remaining_balance'] = self.object.balance_due
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Payment of QAR {form.instance.amount_paid} recorded successfully!')
        return super().form_valid(form)


# Daily Revenue Views
class DailyRevenueListView(LoginRequiredMixin, ListView):
    model = DailyRevenue
    template_name = 'finance/daily_revenue_list.html'
    context_object_name = 'revenues'
    paginate_by = 31  # About a month
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by date range if provided
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        return queryset.order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        revenues = self.get_queryset()
        
        # Calculate totals
        context.update({
            'total_cash_sales': revenues.aggregate(total=Sum('daily_cash_sales'))['total'] or 0,
            'total_pos_sales': revenues.aggregate(total=Sum('daily_pos_sales'))['total'] or 0,
            'total_service_revenue': revenues.aggregate(total=Sum('daily_service_revenue'))['total'] or 0,
            'total_purchases': revenues.aggregate(total=Sum('daily_purchase'))['total'] or 0,
            'total_revenue': revenues.aggregate(total=Sum('daily_revenue'))['total'] or 0,
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        })
        return context


class DailyRevenueCreateView(LoginRequiredMixin, CreateView):
    model = DailyRevenue
    template_name = 'finance/daily_revenue_form.html'
    fields = ['date', 'daily_cash_sales', 'daily_pos_sales', 'daily_service_revenue', 'daily_purchase', 'notes']
    success_url = reverse_lazy('finance:daily_revenue_list')
    
    def get_initial(self):
        initial = super().get_initial()
        # Default to today's date
        initial['date'] = date.today()
        return initial
    
    def form_valid(self, form):
        form.instance.entered_by = self.request.user
        messages.success(self.request, f'Daily revenue for {form.instance.date} created successfully!')
        return super().form_valid(form)


class DailyRevenueUpdateView(LoginRequiredMixin, UpdateView):
    model = DailyRevenue
    template_name = 'finance/daily_revenue_form.html'
    fields = ['date', 'daily_cash_sales', 'daily_pos_sales', 'daily_service_revenue', 'daily_purchase', 'notes']
    success_url = reverse_lazy('finance:daily_revenue_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Daily revenue for {form.instance.date} updated successfully!')
        return super().form_valid(form)


class DailyRevenueDetailView(LoginRequiredMixin, DetailView):
    model = DailyRevenue
    template_name = 'finance/daily_revenue_detail.html'
    context_object_name = 'revenue'


class DailyRevenueDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'finance/daily_revenue_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current month data
        today = date.today()
        current_month_start = today.replace(day=1)
        
        # Recent revenues
        recent_revenues = DailyRevenue.objects.filter(
            date__gte=current_month_start
        ).order_by('-date')[:10]
        
        # Monthly totals
        monthly_revenues = DailyRevenue.objects.filter(date__gte=current_month_start)
        monthly_totals = monthly_revenues.aggregate(
            total_cash=Sum('daily_cash_sales'),
            total_pos=Sum('daily_pos_sales'),
            total_service=Sum('daily_service_revenue'),
            total_purchase=Sum('daily_purchase'),
            total_revenue=Sum('daily_revenue')
        )
        
        # Weekly comparison
        week_ago = today - timedelta(days=7)
        this_week = DailyRevenue.objects.filter(date__gte=week_ago).aggregate(
            total=Sum('daily_revenue')
        )['total'] or 0
        
        last_week_start = week_ago - timedelta(days=7)
        last_week = DailyRevenue.objects.filter(
            date__gte=last_week_start, date__lt=week_ago
        ).aggregate(total=Sum('daily_revenue'))['total'] or 0
        
        context.update({
            'recent_revenues': recent_revenues,
            'monthly_totals': monthly_totals,
            'this_week_revenue': this_week,
            'last_week_revenue': last_week,
            'week_change': this_week - last_week,
            'total_entries': DailyRevenue.objects.count(),
        })
        
        return context


@login_required
def daily_revenue_pdf(request, pk):
    """Generate PDF for a single daily revenue record"""
    if not WEASYPRINT_AVAILABLE:
        messages.error(request, 'PDF generation is not available. Please install WeasyPrint.')
        return redirect('finance:daily_revenue_list')
    
    revenue = get_object_or_404(DailyRevenue, pk=pk)
    
    # Mark as printed
    revenue.mark_printed(request.user)
    
    # Render HTML template
    html_string = render_to_string('finance/daily_revenue_pdf.html', {
        'revenue': revenue,
        'generated_at': timezone.now(),
        'generated_by': request.user,
    })
    
    # Generate PDF
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()
    
    # Return PDF response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="daily_revenue_{revenue.date}.pdf"'
    return response


@login_required
def daily_revenue_print(request, pk):
    """Generate printable version for a single daily revenue record"""
    revenue = get_object_or_404(DailyRevenue, pk=pk)
    
    # Mark as printed
    revenue.mark_printed(request.user)
    
    return render_to_string('finance/daily_revenue_print.html', {
        'revenue': revenue,
        'generated_at': timezone.now(),
        'generated_by': request.user,
    })


@login_required
def daily_revenue_quick_entry(request):
    """AJAX endpoint for quick daily revenue entry"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            revenue, created = DailyRevenue.objects.get_or_create(
                date=data['date'],
                defaults={
                    'daily_cash_sales': data.get('cash_sales', 0),
                    'daily_pos_sales': data.get('pos_sales', 0),
                    'daily_service_revenue': data.get('service_revenue', 0),
                    'daily_purchase': data.get('purchase', 0),
                    'entered_by': request.user,
                    'notes': data.get('notes', ''),
                }
            )
            
            if not created:
                # Update existing
                revenue.daily_cash_sales = data.get('cash_sales', revenue.daily_cash_sales)
                revenue.daily_pos_sales = data.get('pos_sales', revenue.daily_pos_sales)
                revenue.daily_service_revenue = data.get('service_revenue', revenue.daily_service_revenue)
                revenue.daily_purchase = data.get('purchase', revenue.daily_purchase)
                revenue.notes = data.get('notes', revenue.notes)
                revenue.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Daily revenue for {revenue.date} {"created" if created else "updated"} successfully!',
                'daily_revenue': float(revenue.daily_revenue),
                'created': created
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})