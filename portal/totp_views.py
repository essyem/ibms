# portal/totp_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.urls import reverse
from django.utils.crypto import get_random_string
import pyotp
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
import json

from .models import UserProfile
from .auth_forms import CustomAuthenticationForm


@login_required
def totp_setup(request):
    """TOTP setup view - generate secret and QR code"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if profile.totp_enabled:
        messages.info(request, 'TOTP is already enabled for your account.')
        return redirect('portal:profile_edit')
    
    if request.method == 'POST':
        # Verify the provided TOTP code
        code = request.POST.get('totp_code', '').strip()
        
        if not code:
            messages.error(request, 'Please enter the TOTP code from your authenticator app.')
            return render(request, 'registration/totp_setup.html', get_totp_context(request, profile))
        
        # Get the secret from session (more secure than storing in form)
        secret = request.session.get('totp_setup_secret')
        if not secret:
            messages.error(request, 'Setup session expired. Please start over.')
            return redirect('portal:totp_setup')
        
        # Verify the code
        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            # Code is correct, save the secret and enable TOTP
            profile.totp_secret = secret
            profile.totp_enabled = True
            
            # Generate backup codes
            backup_codes = profile.generate_backup_codes()
            profile.save()
            
            # Clear the setup session
            if 'totp_setup_secret' in request.session:
                del request.session['totp_setup_secret']
            
            messages.success(request, 'Two-Factor Authentication has been successfully enabled!')
            
            # Show backup codes
            return render(request, 'registration/totp_backup_codes.html', {
                'backup_codes': backup_codes,
                'is_setup': True
            })
        else:
            messages.error(request, 'Invalid TOTP code. Please try again.')
    
    return render(request, 'registration/totp_setup.html', get_totp_context(request, profile))


def get_totp_context(request, profile):
    """Generate TOTP setup context with QR code"""
    # Generate or retrieve secret from session
    secret = request.session.get('totp_setup_secret')
    if not secret:
        secret = pyotp.random_base32()
        request.session['totp_setup_secret'] = secret
    
    # Create TOTP instance
    totp = pyotp.TOTP(secret)
    
    # Generate provisioning URI
    issuer_name = getattr(settings, 'SITE_NAME', 'TRENDZ Trading')
    account_name = f"{profile.user.email}"
    provisioning_uri = totp.provisioning_uri(
        name=account_name,
        issuer_name=issuer_name
    )
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Convert to base64 for HTML embedding
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        'secret': secret,
        'qr_code_base64': qr_code_base64,
        'provisioning_uri': provisioning_uri,
        'issuer_name': issuer_name,
        'account_name': account_name,
    }


@login_required
def totp_disable(request):
    """Disable TOTP for user"""
    if request.method == 'POST':
        password = request.POST.get('password')
        
        if not password or not request.user.check_password(password):
            messages.error(request, 'Invalid password. Please try again.')
            return render(request, 'registration/totp_disable.html')
        
        profile = get_object_or_404(UserProfile, user=request.user)
        profile.totp_enabled = False
        profile.totp_secret = None
        profile.backup_codes = []
        profile.save()
        
        messages.success(request, 'Two-Factor Authentication has been disabled.')
        return redirect('portal:profile_edit')
    
    return render(request, 'registration/totp_disable.html')


@login_required
def totp_backup_codes(request):
    """View and regenerate backup codes"""
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if not profile.totp_enabled:
        messages.error(request, 'TOTP is not enabled for your account.')
        return redirect('portal:profile_edit')
    
    if request.method == 'POST':
        # Regenerate backup codes
        if request.POST.get('action') == 'regenerate':
            password = request.POST.get('password')
            
            if not password or not request.user.check_password(password):
                messages.error(request, 'Invalid password. Please try again.')
                return render(request, 'registration/totp_backup_codes.html', {
                    'backup_codes': profile.backup_codes,
                    'show_regenerate_form': True
                })
            
            backup_codes = profile.generate_backup_codes()
            messages.success(request, 'New backup codes have been generated. Previous codes are no longer valid.')
            
            return render(request, 'registration/totp_backup_codes.html', {
                'backup_codes': backup_codes,
                'is_regenerated': True
            })
    
    return render(request, 'registration/totp_backup_codes.html', {
        'backup_codes': profile.backup_codes
    })


def totp_login_view(request):
    """TOTP verification during login"""
    # Check if user is in TOTP verification phase
    user_id = request.session.get('totp_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('portal:login')
    
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        profile = UserProfile.objects.get(user=user)
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('portal:login')
    
    if request.method == 'POST':
        code = request.POST.get('totp_code', '').strip()
        use_backup = request.POST.get('use_backup', False)
        
        if not code:
            messages.error(request, 'Please enter a verification code.')
            return render(request, 'registration/totp_verify.html')
        
        verified = False
        
        if use_backup:
            # Check backup code
            if code in profile.backup_codes:
                # Remove used backup code
                profile.backup_codes.remove(code)
                profile.save()
                verified = True
                messages.info(request, f'Backup code used. You have {len(profile.backup_codes)} backup codes remaining.')
        else:
            # Check TOTP code
            if profile.totp_secret:
                totp = pyotp.TOTP(profile.totp_secret)
                verified = totp.verify(code)
        
        if verified:
            # Complete login
            login(request, user)
            
            # Clear TOTP session
            if 'totp_user_id' in request.session:
                del request.session['totp_user_id']
            
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            
            # Redirect to next or dashboard
            next_url = request.session.get('totp_next_url') or 'portal:dashboard'
            if 'totp_next_url' in request.session:
                del request.session['totp_next_url']
            
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid verification code. Please try again.')
    
    return render(request, 'registration/totp_verify.html', {
        'user': user,
        'backup_codes_remaining': len(profile.backup_codes) if profile.backup_codes else 0
    })


def totp_enhanced_login_view(request):
    """Enhanced login view with TOTP support"""
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
                
                # Check if TOTP is enabled
                if profile.totp_enabled and profile.totp_secret:
                    # Store user ID in session for TOTP verification
                    request.session['totp_user_id'] = user.id
                    request.session['totp_next_url'] = request.GET.get('next') or request.POST.get('next') or 'portal:dashboard'
                    
                    return redirect('portal:totp_verify')
                
                # Normal login (no TOTP)
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


@csrf_exempt
@require_http_methods(["POST"])
def ajax_verify_totp(request):
    """AJAX endpoint for TOTP verification during setup"""
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip()
        secret = data.get('secret', '').strip()
        
        if not code or not secret:
            return JsonResponse({'valid': False, 'message': 'Code and secret required'})
        
        totp = pyotp.TOTP(secret)
        is_valid = totp.verify(code)
        
        return JsonResponse({
            'valid': is_valid,
            'message': 'Valid code' if is_valid else 'Invalid code'
        })
        
    except Exception as e:
        return JsonResponse({'valid': False, 'message': str(e)})