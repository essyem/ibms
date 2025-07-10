from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.urls import reverse_lazy
from procurement.models import Supplier, PurchaseOrder, PurchasePayment
from procurement.forms import SupplierForm, PurchaseOrderForm, PurchasePaymentForm

class SupplierListView(ListView):
    model = Supplier
    template_name = 'portal/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 20

class SupplierCreateView(CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'portal/supplier_form.html'
    success_url = reverse_lazy('procurement:supplier_list')

class SupplierUpdateView(UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'portal/supplier_form.html'
    success_url = reverse_lazy('procurement:supplier_list')

class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    template_name = 'portal/purchase_order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    ordering = ['-order_date']

class PurchaseOrderCreateView(CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'portal/purchase_order_form.html'
    success_url = reverse_lazy('procurement:purchase_order_list')

class PurchaseOrderUpdateView(UpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'portal/purchase_order_form.html'
    success_url = reverse_lazy('procurement:purchase_order_list')

class PurchaseOrderDetailView(DetailView):
    model = PurchaseOrder
    template_name = 'portal/purchase_order_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['payments'] = self.object.payments.all()
        return context

class PurchasePaymentListView(ListView):
    model = PurchasePayment
    template_name = 'portal/purchase_payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    ordering = ['-payment_date']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add summary statistics
        payments = PurchasePayment.objects.all()
        context['total_pending'] = payments.filter(status='pending').count()
        context['total_overdue'] = payments.filter(status='overdue').count()
        context['total_paid'] = payments.filter(status='paid').count()
        context['total_partial'] = payments.filter(status='partial').count()
        return context

class PurchasePaymentCreateView(CreateView):
    model = PurchasePayment
    form_class = PurchasePaymentForm
    template_name = 'portal/purchase_payment_form.html'
    success_url = reverse_lazy('procurement:purchase_payment_list')

class PurchasePaymentUpdateView(UpdateView):
    model = PurchasePayment
    form_class = PurchasePaymentForm
    template_name = 'portal/purchase_payment_form.html'
    success_url = reverse_lazy('procurement:purchase_payment_list')

class PurchasePaymentDetailView(DetailView):
    model = PurchasePayment
    template_name = 'portal/purchase_payment_detail.html'

class ProcurementDashboardView(TemplateView):
    template_name = 'portal/procurement_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get summary statistics
        context['total_suppliers'] = Supplier.objects.filter(is_active=True).count()
        context['total_orders'] = PurchaseOrder.objects.count()
        context['pending_orders'] = PurchaseOrder.objects.filter(status='ordered').count()
        context['total_payments'] = PurchasePayment.objects.count()
        context['overdue_payments'] = PurchasePayment.objects.filter(status='overdue').count()
        
        # Recent data
        context['recent_orders'] = PurchaseOrder.objects.order_by('-created_at')[:5]
        context['recent_payments'] = PurchasePayment.objects.order_by('-created_at')[:5]
        
        return context