# finance/views.py
from django.views.generic import ListView, CreateView, DetailView, TemplateView, UpdateView
from django.urls import reverse_lazy
from .models import FinanceTransaction, Category
from .forms import TransactionForm
from django.http import JsonResponse


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