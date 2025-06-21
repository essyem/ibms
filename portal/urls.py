# portal/urls.py
from django.urls import path
from . import views
from .views import (
    ProductSearchView, product_search_fallback, barcode_scanner_view,
    barcode_scan, InvoiceCreateView, InvoiceUpdateView, InvoiceDetailView, InvoiceListView,
    get_product_details
)


urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('enquiry/', views.enquiry, name='enquiry'),
    path('terms/', views.terms, name='terms'), 
    path('products/search/', views.ProductSearchView.as_view(), name='product-search'),
    path('search/', ProductSearchView.as_view(), name='product-search'),
    path('products/', product_search_fallback, name='product-list'),
    # Add other portal-specific URLs here
    path('api/barcode-scan/', views.barcode_scan, name='barcode_scan'),
    path('barcode-scanner/', views.barcode_scanner_view, name='barcode_scanner'),
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/edit/', InvoiceUpdateView.as_view(), name='invoice_update'),
    path('api/products/<int:product_id>/', get_product_details, name='product_details'),
    path('invoices/<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='invoice_pdf'),
]