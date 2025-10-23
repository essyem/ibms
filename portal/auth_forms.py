# portal/auth_forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div, HTML
from crispy_forms.bootstrap import FormActions
import re


class UserRegistrationForm(UserCreationForm):
    """Enhanced user registration form with email verification"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        help_text=_('Required. We will send verification email to this address.')
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+974 1234 5678'
        }),
        help_text=_('Optional. We may use this for order updates.')
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('I accept the Terms of Service and Privacy Policy')
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Style the form fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
        
        # Update help text
        self.fields['username'].help_text = _('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.')
        self.fields['password1'].help_text = _('Your password must contain at least 8 characters and cannot be entirely numeric.')
        
        # Add crispy forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<h3 class="mb-4 text-center">Create Your Account</h3>'),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('username', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Field('phone', css_class='form-group mb-3'),
            Row(
                Column('password1', css_class='form-group col-md-6 mb-3'),
                Column('password2', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Div(
                Field('terms_accepted', css_class='form-check-input'),
                css_class='form-check mb-4'
            ),
            FormActions(
                Submit('register', 'Create Account', css_class='btn btn-primary btn-lg w-100'),
                css_class='text-center'
            )
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(_('A user with this email address already exists.'))
        
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        # Check for valid username pattern
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError(_('Username can only contain letters, numbers, and @/./+/-/_ characters.'))
        
        return username

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        
        if phone:
            # Remove spaces and dashes for validation
            cleaned_phone = re.sub(r'[\s-]', '', phone)
            
            # Basic phone validation (Qatar format)
            if not re.match(r'^\+?[0-9]{8,15}$', cleaned_phone):
                raise ValidationError(_('Please enter a valid phone number (8-15 digits).'))
        
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        # User starts as inactive until email is verified
        user.is_active = False
        
        if commit:
            user.save()
            
            # Store phone number in user profile (we'll create a UserProfile model)
            phone = self.cleaned_data.get('phone')
            if phone:
                from .models import UserProfile
                UserProfile.objects.create(user=user, phone=phone)
        
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form with enhanced styling and validation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'autofocus': True
        })
        
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        
        # Add crispy forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<h3 class="mb-4 text-center">Welcome Back</h3>'),
            Field('username', css_class='form-group mb-3'),
            Field('password', css_class='form-group mb-4'),
            FormActions(
                Submit('login', 'Sign In', css_class='btn btn-primary btn-lg w-100'),
                css_class='text-center'
            ),
            HTML('<div class="text-center mt-3">'),
            HTML('<a href="{% url \'portal:password_reset\' %}" class="text-decoration-none">Forgot your password?</a>'),
            HTML('</div>')
        )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Allow login with email address
            if '@' in username:
                try:
                    user = User.objects.get(email=username)
                    username = user.username
                    self.cleaned_data['username'] = username
                except User.DoesNotExist:
                    pass

        return super().clean()


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset"""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
            'autofocus': True
        }),
        help_text=_('Enter the email address associated with your account.')
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if not User.objects.filter(email=email).exists():
            raise ValidationError(_('No user found with this email address.'))
        
        return email


class EmailChangeForm(forms.Form):
    """Form for changing user email address"""
    
    new_email = forms.EmailField(
        label=_('New Email Address'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new email address'
        })
    )
    
    password = forms.CharField(
        label=_('Current Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        }),
        help_text=_('Enter your current password to confirm this change.')
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_email(self):
        new_email = self.cleaned_data.get('new_email')
        
        if new_email == self.user.email:
            raise ValidationError(_('This is already your current email address.'))
        
        if User.objects.filter(email=new_email).exists():
            raise ValidationError(_('A user with this email address already exists.'))
        
        return new_email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        if not self.user.check_password(password):
            raise ValidationError(_('Invalid password.'))
        
        return password


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information"""
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        from .models import UserProfile
        model = UserProfile
        fields = ['phone', 'company_name', 'address', 'preferred_contact_method']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'preferred_contact_method': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        # Pre-populate user fields
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name

    def save(self, commit=True):
        profile = super().save(commit=commit)
        
        # Update user fields
        self.user.first_name = self.cleaned_data.get('first_name', '')
        self.user.last_name = self.cleaned_data.get('last_name', '')
        
        if commit:
            self.user.save()
        
        return profile