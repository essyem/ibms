# finance/urls.py
from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/add/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('reports/', views.FinanceReportView.as_view(), name='finance_reports'),
    path('api/categories/', views.category_api, name='category_api'),
    '''
    path('transactions/<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),
    path('transactions/<int:pk>/document/', views.TransactionDocumentView.as_view(), name='transaction_document'),
    path('transactions/<int:pk>/export/', views.TransactionExportView.as_view(), name='transaction_export'),
    path('transactions/<int:pk>/pdf/', views.TransactionPDFView.as_view(), name='transaction_pdf'),
    path('transactions/<int:pk>/html/', views.TransactionHTMLView.as_view(), name='transaction_html'),
    path('transactions/<int:pk>/html2django/', views.TransactionHTML2DjangoView.as_view(), name='transaction_html2django'),
    path('transactions/<int:pk>/html2pdf/', views.TransactionHTML2PDFView.as_view(), name='transaction_html2pdf'),
    path('transactions/<int:pk>/html-utils/', views.TransactionHTMLUtilsView.as_view(), name='transaction_html_utils'),
    '''

]