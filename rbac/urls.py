# rbac/urls.py
from django.urls import path
from . import views 
from .views import RegistrationView


app_name = 'rbac'

urlpatterns = [
    # Registration and verification
    path('register/', RegistrationView.as_view(), name='register'),
    path('verify/<str:token>/', views.verify_email, name='verify_email'),
    path('registration-pending/', views.registration_pending, name='registration_pending'),
    path('resend-verification/', views.ResendVerificationEmail.as_view(), name='resend_verification'),
    # User management
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.user_profile_create, name='user_profile_create'),
    path('users/<int:profile_id>/edit/', views.user_profile_edit, name='user_profile_edit'),
    path('users/<int:profile_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    
    # Role management
    path('roles/', views.role_management, name='role_management'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/<int:role_id>/edit/', views.role_edit, name='role_edit'),
    
    # Permission logs
    path('permissions/logs/', views.permission_logs, name='permission_logs'),
]
