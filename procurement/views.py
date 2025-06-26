from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from procurement.models import Supplier, PurchaseOrder
from procurement.forms import SupplierForm, PurchaseOrderForm

class SupplierListView(ListView):
    model = Supplier
    template_name = 'procurement/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 20

class SupplierCreateView(CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'procurement/supplier_form.html'
    success_url = reverse_lazy('supplier_list')

class SupplierUpdateView(UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'procurement/supplier_form.html'
    success_url = reverse_lazy('supplier_list')

class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    template_name = 'procurement/purchase_order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    ordering = ['-order_date']

class PurchaseOrderCreateView(CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'procurement/purchase_order_form.html'
    success_url = reverse_lazy('purchase_order_list')

class PurchaseOrderUpdateView(UpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'procurement/purchase_order_form.html'
    success_url = reverse_lazy('purchase_order_list')

class PurchaseOrderDetailView(DetailView):
    model = PurchaseOrder
    template_name = 'procurement/purchase_order_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['payments'] = self.object.payments.all()
        return context