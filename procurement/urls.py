from django.urls import path
from . import views

app_name = 'procurement'

urlpatterns = [
    # Suppliers
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_edit'),
    
    # Purchase Orders
    path('orders/', views.PurchaseOrderListView.as_view(), name='purchase_order_list'),
    path('orders/create/', views.PurchaseOrderCreateView.as_view(), name='purchase_order_create'),
    path('orders/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='purchase_order_detail'),
    path('orders/<int:pk>/edit/', views.PurchaseOrderUpdateView.as_view(), name='purchase_order_edit'),
]