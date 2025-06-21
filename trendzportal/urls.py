from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from portal import views
from portal.views import (ProductSearchView, product_search_fallback,
    InvoiceCreateView, InvoiceUpdateView, InvoiceDetailView, 
    InvoiceListView, get_product_details, InvoicePDFView)


urlpatterns = [
    # Admin URL
    path('admin/', admin.site.urls),
    path('', include('portal.urls')),
    #path('admin/login/', admin.site.login, name='admin-login'),
    #path('admin/logout/', admin.site.logout, name='admin-logout'),
    # Custom URLs
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('enquiry/', views.enquiry, name='enquiry'),
    path('terms/', views.terms, name='terms'),
    path('products/search/', ProductSearchView.as_view(), name='product-search'),
    path('search/', ProductSearchView.as_view(), name='product-search'),
    path('products/', product_search_fallback, name='product-list'),
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/edit/', InvoiceUpdateView.as_view(), name='invoice_update'),
    path('api/products/<int:product_id>/', get_product_details, name='product_details'),
    path('invoices/<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='invoice_pdf'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)