# portal/auth_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.conf import settings
import json

from .auth_forms import (
    UserRegistrationForm, 
    CustomAuthenticationForm, 
    PasswordResetRequestForm,
    EmailChangeForm,
    UserProfileForm
)
from .models import UserProfile, UserEmailVerification


def register_view(request):
    """User registration view with email verification"""
    if request.user.is_authenticated:
        return redirect('portal:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                
                # Create UserProfile
                profile, created = UserProfile.objects.get_or_create(user=user)
                if hasattr(form, 'cleaned_data'):
                    phone = form.cleaned_data.get('phone')
                    if phone:
                        profile.phone = phone
                        profile.save()
                
                # Send verification email
                send_verification_email(user)
                
                messages.success(
                    request, 
                    f'Account created successfully! Please check your email ({user.email}) for verification link.'
                )
                
                return redirect('portal:registration_success')
            
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            # Form has validation errors
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """Enhanced login view with email verification check"""
    if request.user.is_authenticated:
        return redirect('portal:dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Check if email is verified
                profile, created = UserProfile.objects.get_or_create(user=user)
                
                if not profile.email_verified and not user.is_superuser:
                    messages.warning(
                        request,
                        f'Please verify your email address ({user.email}) before logging in. '
                        f'<a href="{reverse("portal:resend_verification", kwargs={"user_id": user.id})}" '
                        f'class="alert-link">Resend verification email</a>'
                    )
                    return render(request, 'registration/login.html', {'form': form})
                
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                # Redirect to next page or dashboard
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('portal:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Logout view with confirmation"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('portal:index')
    
    return render(request, 'registration/logout_confirm.html')


def send_verification_email(user):
    """Send email verification email to user"""
    try:
        profile, created = UserProfile.objects.get_or_create(user=user)
        token = profile.generate_verification_token()
        
        verification_url = f"{settings.SITE_URL or 'http://localhost:8010'}" \
                          f"{reverse('portal:verify_email', kwargs={'user_id': user.id, 'token': token})}"
        
        # Render email content
        html_content = render_to_string('emails/email_verification.html', {
            'user': user,
            'verification_url': verification_url,
            'site_name': getattr(settings, 'SITE_NAME', 'TRENDZ Trading & Services')
        })
        
        plain_content = strip_tags(html_content)
        
        # Send email
        send_mail(
            subject=f'Verify your email address - {getattr(settings, "SITE_NAME", "TRENDZ")}',
            message=plain_content,
            html_message=html_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@trendzqtr.com'),
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False


def verify_email(request, user_id, token):
    """Verify user email with token"""
    try:
        user = get_object_or_404(User, id=user_id)
        profile = get_object_or_404(UserProfile, user=user)
        
        if profile.email_verified:
            messages.info(request, 'Your email is already verified.')
            return redirect('portal:login')
        
        if profile.is_verification_token_valid(token):
            profile.verify_email()
            messages.success(
                request,
                'Email verified successfully! You can now log in to your account.'
            )
            
            # Auto-login the user
            login(request, user)
            return redirect('portal:dashboard')
        else:
            messages.error(
                request,
                'Invalid or expired verification link. '
                f'<a href="{reverse("portal:resend_verification", kwargs={"user_id": user.id})}" '
                f'class="alert-link">Request a new verification email</a>'
            )
    
    except Exception as e:
        messages.error(request, f'Verification failed: {str(e)}')
    
    return redirect('portal:login')


def resend_verification(request, user_id):
    """Resend email verification"""
    try:
        user = get_object_or_404(User, id=user_id)
        profile = get_object_or_404(UserProfile, user=user)
        
        if profile.email_verified:
            messages.info(request, 'Your email is already verified.')
            return redirect('portal:login')
        
        # Check rate limiting (max 3 emails per hour)
        recent_verifications = UserEmailVerification.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timezone.timedelta(hours=1)
        ).count()
        
        if recent_verifications >= 3:
            messages.warning(
                request,
                'Too many verification emails sent. Please wait an hour before requesting another.'
            )
            return redirect('portal:login')
        
        # Send new verification email
        if send_verification_email(user):
            messages.success(
                request,
                f'Verification email sent to {user.email}. Please check your inbox.'
            )
        else:
            messages.error(request, 'Failed to send verification email. Please try again later.')
    
    except Exception as e:
        messages.error(request, f'Failed to resend verification: {str(e)}')
    
    return redirect('portal:login')


def registration_success(request):
    """Registration success page"""
    return render(request, 'registration/registration_success.html')


def password_reset_request(request):
    """Request password reset"""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # Send password reset email (use Django's built-in functionality)
                from django.contrib.auth.forms import PasswordResetForm
                reset_form = PasswordResetForm({'email': email})
                if reset_form.is_valid():
                    reset_form.save(
                        request=request,
                        use_https=request.is_secure(),
                        email_template_name='registration/password_reset_email.html',
                    )
                    messages.success(
                        request,
                        f'Password reset instructions have been sent to {email}'
                    )
                    return redirect('portal:login')
                
            except User.DoesNotExist:
                # Don't reveal that the email doesn't exist
                messages.success(
                    request,
                    f'If an account with email {email} exists, '
                    'password reset instructions have been sent.'
                )
                return redirect('portal:login')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'registration/password_reset_form.html', {'form': form})


@login_required
def profile_view(request):
    """User profile view and edit"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.user, request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('portal:profile')
    else:
        form = UserProfileForm(request.user, instance=profile)
    
    return render(request, 'registration/profile.html', {
        'form': form,
        'profile': profile
    })


@login_required
def change_email_view(request):
    """Change email address with verification"""
    if request.method == 'POST':
        form = EmailChangeForm(request.user, request.POST)
        if form.is_valid():
            new_email = form.cleaned_data['new_email']
            
            # Update user email and mark as unverified
            request.user.email = new_email
            request.user.save()
            
            profile = request.user.profile
            profile.email_verified = False
            profile.save()
            
            # Send verification email to new address
            if send_verification_email(request.user):
                messages.success(
                    request,
                    f'Email changed to {new_email}. '
                    'Please check your new email for verification instructions.'
                )
            else:
                messages.warning(
                    request,
                    'Email changed but failed to send verification. '
                    'Please request verification manually.'
                )
            
            return redirect('portal:profile')
    else:
        form = EmailChangeForm(request.user)
    
    return render(request, 'registration/change_email.html', {'form': form})


@csrf_exempt
@require_http_methods(["POST"])
def check_username_availability(request):
    """AJAX endpoint to check username availability"""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        
        if not username:
            return JsonResponse({'available': False, 'message': 'Username required'})
        
        if len(username) < 3:
            return JsonResponse({'available': False, 'message': 'Username too short'})
        
        exists = User.objects.filter(username=username).exists()
        
        return JsonResponse({
            'available': not exists,
            'message': 'Username available' if not exists else 'Username already taken'
        })
        
    except Exception as e:
        return JsonResponse({'available': False, 'message': str(e)})


@csrf_exempt
@require_http_methods(["POST"])  
def check_email_availability(request):
    """AJAX endpoint to check email availability"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        
        if not email:
            return JsonResponse({'available': False, 'message': 'Email required'})
        
        exists = User.objects.filter(email=email).exists()
        
        return JsonResponse({
            'available': not exists,
            'message': 'Email available' if not exists else 'Email already registered'
        })
        
    except Exception as e:
        return JsonResponse({'available': False, 'message': str(e)})