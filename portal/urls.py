# portal/urls.py
from django.urls import path
from . import views
from .views import (
    ProductSearchView, product_search_fallback, barcode_scanner_view,
    barcode_scan, InvoiceCreateView, InvoiceUpdateView, InvoiceDetailView, InvoiceListView,
    InvoiceDeleteView, get_product_details, dashboard_view, report_view, analytics_api, export_reports,
    CustomerListView, CustomerCreateView, CustomerDetailView, CustomerUpdateView,
    ProductListView, ProductDetailView, ProductCreateView, ProductUpdateView,
    product_delete, product_toggle_active, product_dashboard,
    PublicProductCatalogView, PublicProductDetailView
)
from .cart_views import (
    add_to_cart, update_cart_item, remove_from_cart, cart_count,
    CartView, CheckoutView, order_confirmation
)
from . import ajax_views
from .views import set_language

# Import authentication views
from .auth_views import (
    register_view, login_view, logout_view, verify_email, resend_verification,
    registration_success, password_reset_request, profile_view, change_email_view,
    check_username_availability, check_email_availability
)

# Import TOTP views
from .totp_views import (
    totp_setup, totp_disable, totp_backup_codes, totp_login_view, 
    totp_enhanced_login_view, ajax_verify_totp
)

app_name = 'portal'

urlpatterns = [
    # Main portal pages
    path('', views.index, name='index'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('reports/', report_view, name='reports'),
    path('reports/export/', export_reports, name='export_reports'),
    path('api/analytics/', analytics_api, name='analytics_api'),
    path('dashboard_summary_api/', views.dashboard_summary_api, name='dashboard_summary_api'),
    path('profile/', views.profile, name='profile'),
    path('enquiry/', views.enquiry, name='enquiry'),
    path('terms/', views.terms, name='terms'),
    
    # Authentication URLs
    path('register/', register_view, name='register'),
    path('login/', totp_enhanced_login_view, name='login'),  # Use TOTP-enhanced login
    path('logout/', logout_view, name='logout'),
    path('registration-success/', registration_success, name='registration_success'),
    path('verify-email/<int:user_id>/<str:token>/', verify_email, name='verify_email'),
    path('resend-verification/<int:user_id>/', resend_verification, name='resend_verification'),
    path('password-reset/', password_reset_request, name='password_reset'),
    path('profile/edit/', profile_view, name='profile_edit'),
    path('profile/change-email/', change_email_view, name='change_email'),
    
    # TOTP URLs
    path('totp/setup/', totp_setup, name='totp_setup'),
    path('totp/verify/', totp_login_view, name='totp_verify'),
    path('totp/disable/', totp_disable, name='totp_disable'),
    path('totp/backup-codes/', totp_backup_codes, name='totp_backup_codes'),
    
    # AJAX authentication endpoints
    path('ajax/check-username/', check_username_availability, name='check_username'),
    path('ajax/check-email/', check_email_availability, name='check_email'),
    path('ajax/verify-totp/', ajax_verify_totp, name='ajax_verify_totp'),
    
    # Product search and management
    path('products/search/', ProductSearchView.as_view(), name='product-search'),
    path('search/', ProductSearchView.as_view(), name='product-search'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/dashboard/', product_dashboard, name='product_dashboard'),
    path('products/create/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', product_delete, name='product_delete'),
    path('products/<int:pk>/toggle-active/', product_toggle_active, name='product_toggle_active'),
    path('api/products/<int:product_id>/', get_product_details, name='product_details'),
    
    # Public product catalog (e-commerce)
    path('catalog/', PublicProductCatalogView.as_view(), name='public_catalog'),
    path('catalog/<int:pk>/', PublicProductDetailView.as_view(), name='public_product_detail'),
    
    # Shopping cart and checkout
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/add/', add_to_cart, name='add_to_cart'),
    path('cart/update/', update_cart_item, name='update_cart_item'),
    path('cart/remove/', remove_from_cart, name='remove_from_cart'),
    path('cart/count/', cart_count, name='cart_count'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-confirmation/<str:order_number>/', order_confirmation, name='order_confirmation'),
    # Language switcher
    path('set-language/', set_language, name='set_language'),
    
    # Invoice management
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/edit/', InvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<int:pk>/delete/', InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('invoices/<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='invoice_pdf'),
    
    # Customer management
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/create/', CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', CustomerUpdateView.as_view(), name='customer_update'),
    
    # Barcode functionality
    path('api/barcode-scan/', barcode_scan, name='barcode_scan'),
    path('barcode-scanner/', barcode_scanner_view, name='barcode_scanner'),
    
    # AJAX endpoints for product search and barcode lookup
    path('ajax/product-search/', ajax_views.product_search_public, name='product_search_public'),
    path('ajax/barcode-lookup/', ajax_views.product_barcode_lookup_public, name='barcode_lookup_public'),
    path('ajax/customer-search/', views.customer_search, name='customer_search'),
]