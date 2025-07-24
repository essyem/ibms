# rbac/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.password_validation import validate_password
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from .models import SiteRole, SiteUserProfile, SitePermissionLog
from .forms import SiteUserProfileForm, SiteRoleForm
import json
from django.views.generic import CreateView, View
from django.urls import reverse_lazy, reverse
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import EmailVerification
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin


# Basic function-based view
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('portal:index')
    else:
        form = UserCreationForm()
    return render(request, 'rbac/register.html', {'form': form})


class RegistrationView(CreateView):
    form_class = UserCreationForm
    template_name = 'rbac/register.html'
    success_url = reverse_lazy('registration_pending')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False  # User can't login until verified
        user.save()
        
        # Create and send verification
        verification = EmailVerification.create_verification(user)
        self.send_verification_email(user, verification.token)
        
        messages.info(self.request, 
                     'Please check your email to verify your account. '
                     'The link will expire in 24 hours.')
        return super().form_valid(form)

    def send_verification_email(self, user, token):
        current_site = get_current_site(self.request)
        verification_url = reverse('verify_email', kwargs={'token': token})
        full_url = f"https://{current_site.domain}{verification_url}"
        
        subject = 'Verify your Trendz Portal account'
        message = render_to_string('rbac/emails/verification_email.html', {
            'user': user,
            'verification_url': full_url,
            'expiry_hours': 24
        })
        
        send_mail(
            subject,
            message,
            None,  # Uses DEFAULT_FROM_EMAIL
            [user.email],
            html_message=message
        )

def verify_email(request, token):
    verification = get_object_or_404(EmailVerification, token=token)
    
    if verification.verified:
        messages.warning(request, 'This email has already been verified.')
    elif verification.is_expired():
        messages.error(request, 'The verification link has expired. Please request a new one.')
    else:
        user = verification.user
        user.is_active = True
        user.save()
        verification.verified = True
        verification.save()
        login(request, user)
        messages.success(request, 'Email successfully verified! You are now logged in.')
        return redirect('portal:index')
    
    return redirect('login')

def registration_pending(request):
    return render(request, 'rbac/registration_pending.html')


class ResendVerificationEmail(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_verified:  # Add this property to your User model
            messages.warning(request, 'Your email is already verified.')
            return redirect('portal:index')
            
        verification, created = EmailVerification.objects.get_or_create(
            user=request.user,
            defaults={'token': get_random_string(length=64)}
        )
        
        if not created and verification.is_expired():
            verification.token = get_random_string(length=64)
            verification.created_at = timezone.now()
            verification.save()
        
        self.send_verification_email(request.user, verification.token)
        messages.info(request, 'New verification email sent. Please check your inbox.')
        return redirect('registration_pending')
    
    def send_verification_email(self, user, token):
        # Same implementation as in RegistrationView
        ...



def rbac_permission_required(permission_name):
    """Decorator to check RBAC permissions"""
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if hasattr(request, 'user_profile'):
                if request.user_profile.has_permission(permission_name):
                    return view_func(request, *args, **kwargs)
            
            messages.error(request, f'You do not have permission to access this page.')
            return redirect('portal:dashboard')
        return wrapped_view
    return decorator

@login_required
@rbac_permission_required('can_manage_users')
def user_management(request):
    """User management dashboard"""
    current_site = get_current_site(request)
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Get all user profiles for current site
    profiles = SiteUserProfile.objects.filter(site=current_site)
    
    if search_query:
        profiles = profiles.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(department__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(profiles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get available roles
    roles = SiteRole.objects.filter(site=current_site, is_active=True)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'roles': roles,
        'current_site': current_site,
    }
    
    return render(request, 'rbac/user_management.html', context)

@login_required
@rbac_permission_required('can_manage_users')
def user_profile_create(request):
    """Create new user profile"""
    current_site = get_current_site(request)
    
    if request.method == 'POST':
        form = SiteUserProfileForm(request.POST, site=current_site)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.site = current_site
            profile.save()
            
            # Log the action
            SitePermissionLog.objects.create(
                site=current_site,
                user=profile.user,
                changed_by=request.user,
                action='user_profile_created',
                new_value={'role': profile.role.name if profile.role else None},
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'User profile created for {profile.user.username}')
            return redirect('rbac:user_management')
    else:
        form = SiteUserProfileForm(site=current_site)
    
    return render(request, 'rbac/user_profile_form.html', {
        'form': form,
        'title': 'Create User Profile',
        'current_site': current_site,
    })

@login_required
@rbac_permission_required('can_manage_users')
def user_profile_edit(request, profile_id):
    """Edit user profile"""
    current_site = get_current_site(request)
    profile = get_object_or_404(SiteUserProfile, id=profile_id, site=current_site)
    
    old_role = profile.role.name if profile.role else None
    
    if request.method == 'POST':
        form = SiteUserProfileForm(request.POST, instance=profile, site=current_site)
        if form.is_valid():
            profile = form.save()
            new_role = profile.role.name if profile.role else None
            
            # Log the action if role changed
            if old_role != new_role:
                SitePermissionLog.objects.create(
                    site=current_site,
                    user=profile.user,
                    changed_by=request.user,
                    action='role_changed',
                    old_value={'role': old_role},
                    new_value={'role': new_role},
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            
            messages.success(request, f'User profile updated for {profile.user.username}')
            return redirect('rbac:user_management')
    else:
        form = SiteUserProfileForm(instance=profile, site=current_site)
    
    return render(request, 'rbac/user_profile_form.html', {
        'form': form,
        'profile': profile,
        'title': f'Edit Profile - {profile.user.username}',
        'current_site': current_site,
    })

@login_required
@rbac_permission_required('can_manage_users')
def role_management(request):
    """Role management dashboard"""
    current_site = get_current_site(request)
    
    roles = SiteRole.objects.filter(site=current_site).order_by('name')
    
    context = {
        'roles': roles,
        'current_site': current_site,
    }
    
    return render(request, 'rbac/role_management.html', context)

@login_required
@rbac_permission_required('can_manage_users')
def role_create(request):
    """Create new role"""
    current_site = get_current_site(request)
    
    if request.method == 'POST':
        form = SiteRoleForm(request.POST)
        if form.is_valid():
            role = form.save(commit=False)
            role.site = current_site
            role.save()
            
            messages.success(request, f'Role "{role.name}" created successfully')
            return redirect('rbac:role_management')
    else:
        form = SiteRoleForm()
    
    return render(request, 'rbac/role_form.html', {
        'form': form,
        'title': 'Create Role',
        'current_site': current_site,
    })

@login_required
@rbac_permission_required('can_manage_users')
def role_edit(request, role_id):
    """Edit role"""
    current_site = get_current_site(request)
    role = get_object_or_404(SiteRole, id=role_id, site=current_site)
    
    if request.method == 'POST':
        form = SiteRoleForm(request.POST, instance=role)
        if form.is_valid():
            role = form.save()
            messages.success(request, f'Role "{role.name}" updated successfully')
            return redirect('rbac:role_management')
    else:
        form = SiteRoleForm(instance=role)
    
    return render(request, 'rbac/role_form.html', {
        'form': form,
        'role': role,
        'title': f'Edit Role - {role.name}',
        'current_site': current_site,
    })

@login_required
@require_http_methods(["POST"])
def toggle_user_status(request, profile_id):
    """Toggle user active status via AJAX"""
    current_site = get_current_site(request)
    
    # Check permission
    if not request.user.is_superuser:
        if not hasattr(request, 'user_profile') or not request.user_profile.has_permission('can_manage_users'):
            return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        profile = SiteUserProfile.objects.get(id=profile_id, site=current_site)
        profile.is_site_active = not profile.is_site_active
        profile.save()
        
        # Log the action
        SitePermissionLog.objects.create(
            site=current_site,
            user=profile.user,
            changed_by=request.user,
            action='user_status_toggled',
            new_value={'is_active': profile.is_site_active},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({
            'success': True,
            'is_active': profile.is_site_active,
            'message': f'User {"activated" if profile.is_site_active else "deactivated"} successfully'
        })
    except SiteUserProfile.DoesNotExist:
        return JsonResponse({'error': 'User profile not found'}, status=404)

@login_required
@rbac_permission_required('can_view_reports')
def permission_logs(request):
    """View permission change logs"""
    current_site = get_current_site(request)
    
    logs = SitePermissionLog.objects.filter(site=current_site).order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_site': current_site,
    }
    
    return render(request, 'rbac/permission_logs.html', context)


