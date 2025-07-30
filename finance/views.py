# finance/views.py
from django.views.generic import ListView, CreateView, DetailView, TemplateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from .models import FinanceTransaction, Category
from finance.forms import TransactionForm
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from procurement.models import PurchaseOrder, PurchasePayment


def category_api(request):
    transaction_type = request.GET.get('type', '')
    categories = Category.objects.filter(type=transaction_type).values('id', 'name')
    return JsonResponse(list(categories), safe=False)


class TransactionCreateView(CreateView):
    model = FinanceTransaction
    form_class = TransactionForm
    template_name = 'finance/transaction_form.html'
    success_url = reverse_lazy('finance:transaction_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class TransactionUpdateView(UpdateView):
    model = FinanceTransaction
    form_class = TransactionForm
    template_name = 'finance/transaction_form.html'
    success_url = reverse_lazy('finance:transaction_list')

class TransactionListView(ListView):
    model = FinanceTransaction
    template_name = 'finance/transaction_list.html'
    paginate_by = 20
    context_object_name = 'transactions'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.GET.get('type'):
            queryset = queryset.filter(type=self.request.GET['type'])
        return queryset.order_by('-date')


class TransactionCreateView(CreateView):
    model = FinanceTransaction
    form_class = TransactionForm
    template_name = 'finance/transaction_form.html'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class FinanceReportView(TemplateView):
    template_name = 'finance/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add report data to context
        return context
    
    def save(self, commit=True):
        if not self.instance.reference:
            # Generate reference like TXN-2023-001
            last_txn = FinanceTransaction.objects.order_by('-id').first()
            new_id = (last_txn.id + 1) if last_txn else 1
            self.instance.reference = f"TXN-{timezone.now().year}-{new_id:03d}"
        return super().save(commit)


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