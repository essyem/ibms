from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from portal import barcode_views, ajax_views
from django.shortcuts import redirect

urlpatterns = [
    # Barcode admin actions (must come BEFORE admin URLs to avoid catch-all)
    path('admin/barcode/', lambda request: redirect('barcode_generator_dashboard'), name='barcode_admin_redirect'),
    path('admin/barcode/dashboard/', barcode_views.barcode_generator_dashboard, name='barcode_generator_dashboard'),
    path('admin/barcode/generate-bulk/', barcode_views.generate_bulk_barcodes, name='generate_bulk_barcodes'),
    path('admin/barcode/generate-single/<int:product_id>/', barcode_views.generate_single_barcode, name='generate_single_barcode'),
    path('admin/barcode/print-labels/', barcode_views.print_barcode_labels, name='print_barcode_labels'),
    path('admin/barcode/print/', barcode_views.print_barcode_labels, name='print_barcode_labels_legacy'),  # Legacy URL for compatibility
    path('admin/barcode/preview/<int:product_id>/', barcode_views.preview_barcode, name='preview_barcode'),
    path('admin/barcode/demo-labels/', barcode_views.demo_barcode_labels, name='demo_barcode_labels'),
    
    # Admin AJAX endpoints
    path('admin/ajax/product-search/', ajax_views.product_search_ajax, name='admin_product_search_ajax'),
    path('admin/ajax/barcode-lookup/', ajax_views.product_barcode_lookup, name='admin_product_barcode_lookup'),
    
    # Admin URLs (comes after custom admin paths)
    path('admin/', admin.site.urls),
    
    # App URLs
    path('', include('portal.urls')),  # Portal (main app) - root level
    path('rbac/', include('rbac.urls')),  # RBAC (Role-Based Access Control) app
    path('finance/', include('finance.urls')),  # Finance app
    path('procurement/', include('procurement.urls')),  # Procurement app
]

# Static and media files for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
