import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# DEVELOPMENT ENVIRONMENT CONFIGURATION
# ============================================================================

# Environment indicator
ENVIRONMENT = 'development'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'p5AYcy43r8Wi0ChlcvDh0YddX1UtcmxtqyQtRnFD85rIiQ3sjs30vwDy0Xfiv1Fvv7w='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allowed hosts for development - allows all hosts and common development addresses
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '192.168.100.2',
    'testserver',
    'ibms.trendzapps.com',  # Production domain
    '20.173.49.190',        # Production IP
    '*'  # Allow all hosts in development
]

# CSRF trusted origins - fix for the origin checking error
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8010',
    'http://localhost:8010',
    'http://0.0.0.0:8010',
    'http://127.0.0.1:8005',
    'http://localhost:8005',
    'http://0.0.0.0:8005',
    'http://127.0.0.1:8006',
    'http://localhost:8006',
    'http://0.0.0.0:8006',
    'http://127.0.0.1:8011',
    'http://localhost:8011',
    'http://0.0.0.0:8011',
    'https://ibms.trendzapps.com',  # Production HTTPS
    'http://ibms.trendzapps.com',   # Production HTTP (if needed)
]

# CSRF settings for development - environment-based configuration
CSRF_COOKIE_SECURE = DEBUG == False  # Only secure cookies in production
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

# Security settings - environment-based configuration
# For development, you can enable HTTPS redirect by setting FORCE_HTTPS=True environment variable
FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'False').lower() == 'true'

if not DEBUG or FORCE_HTTPS:
    # Production or forced HTTPS settings
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
else:
    # Development settings - no HTTPS redirect by default
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_PROXY_SSL_HEADER = None
    SESSION_COOKIE_SECURE = False

# Security settings that are always enabled
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Allow iframe for development tools
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Session settings - environment-based configuration
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24 hours

# Site ID for Django sites framework
SITE_ID = 1

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'import_export',
    'django_extensions',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    
    # Local apps
    'rbac',
    'portal',
    'finance',
    'procurement',
    'trendzportal',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be first for CORS
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'portal.middleware.ThreadLocalMiddleware',
]

# URL configuration
ROOT_URLCONF = 'trendzportal.urls'

# Template configuration - Single Tenant
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'portal.context_processors.trendz_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'trendzportal.wsgi.application'

# Database configuration for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ibms_db',
        'USER': 'dbadmin',
        'PASSWORD': '0penP@$$',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 0,  # Disable persistent connections for development
        'OPTIONS': {
            'connect_timeout': 30,
        }
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Currency Configuration
DEFAULT_CURRENCY = 'QAR'
CURRENCY_SYMBOL = 'QAR'
CURRENCY_FORMAT = 'QAR {amount:,.2f}'

LANGUAGES = [
    ('en', 'English'),
    ('ar', 'Arabic'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Authentication settings
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = 'portal:dashboard'
LOGOUT_REDIRECT_URL = '/'  # Redirect to root landing page after logout

# Admin logout redirect - ensures admin logout also goes to landing page
ADMIN_LOGOUT_URL = 'portal:index'

# Email backend for development - prints to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8010",
    "http://127.0.0.1:8010",
    "http://0.0.0.0:8010",
    "http://192.168.100.2:8010",
    "http://127.0.0.1:8005",
    "http://localhost:8005",
    "http://127.0.0.1:50123",
    "http://localhost:50123",
    "http://127.0.0.1:8001",
    "http://localhost:8001",
    "https://ibms.trendzapps.com",  # Production HTTPS
    "http://ibms.trendzapps.com",   # Production HTTP
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
}

# Crispy Forms settings
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Admin customization
ADMIN_SITE_HEADER = "TrendzApps IBMS Admin"
ADMIN_SITE_TITLE = "TrendzApps IBMS Portal"
ADMIN_INDEX_TITLE = "Welcome to TrendzApps IBMS Administration"

# Custom application settings
TRENDZ_SETTINGS = {
    'COMPANY_NAME': 'TrendzApps IBMS',
    'SUPPORT_EMAIL': 'support@trendzapps.com',
    'PHONE_NUMBER': '+974 3051 4865',
}

# Development tools
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Logging configuration
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django_error.log',
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'portal': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'finance': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'procurement': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'rbac': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Load local settings if available
try:
    from .local_settings import *
    print("✅ Local settings loaded successfully")
except ImportError:
    print("⚠️  No local settings found, using default development settings")

# Business contact settings for e-commerce features
WHATSAPP_BUSINESS_NUMBER = '+97430514865'  # Qatar business phone number

print(f"🔧 Django running in {ENVIRONMENT} mode with DEBUG={DEBUG}")
print(f"🌐 Allowed hosts: {ALLOWED_HOSTS}")
print(f"🔒 CSRF trusted origins: {CSRF_TRUSTED_ORIGINS}")
print(f"🔐 HTTPS redirect: {'ON' if SECURE_SSL_REDIRECT else 'OFF'} (Force HTTPS: {FORCE_HTTPS})")