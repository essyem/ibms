# finance/urls.py
from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.FinanceIndexView.as_view(), name='index'),
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/add/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_edit'),
    path('reports/', views.FinanceReportView.as_view(), name='finance_reports'),
    path('api/categories/', views.category_api, name='category_api'),
]