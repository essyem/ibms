# finance/urls.py
from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Finance Dashboard
    path('', views.FinanceIndexView.as_view(), name='index'),
    
    # Transactions
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/add/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_edit'),
    
    # Reports
    path('reports/', views.FinanceReportView.as_view(), name='finance_reports'),
    
    # Daily Revenue Management
    path('daily-revenue/', views.DailyRevenueDashboardView.as_view(), name='daily_revenue_dashboard'),
    path('daily-revenue/list/', views.DailyRevenueListView.as_view(), name='daily_revenue_list'),
    path('daily-revenue/add/', views.DailyRevenueCreateView.as_view(), name='daily_revenue_create'),
    path('daily-revenue/<int:pk>/', views.DailyRevenueDetailView.as_view(), name='daily_revenue_detail'),
    path('daily-revenue/<int:pk>/edit/', views.DailyRevenueUpdateView.as_view(), name='daily_revenue_edit'),
    path('daily-revenue/<int:pk>/pdf/', views.daily_revenue_pdf, name='daily_revenue_pdf'),
    path('daily-revenue/<int:pk>/print/', views.daily_revenue_print, name='daily_revenue_print'),
    path('daily-revenue/quick-entry/', views.daily_revenue_quick_entry, name='daily_revenue_quick_entry'),
    
    # API endpoints
    path('api/categories/', views.category_api, name='category_api'),
]