from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site

def trendz_settings(request):
    return {
        'TRENDZ': settings.TRENDZ_SETTINGS,
        'DEBUG': settings.DEBUG,
    }

def site_context(request):
    """
    Add site-specific context to all templates (Single-site mode: TRENDZ only)
    """
    # Force TRENDZ context for single-site mode
    context = {
        'company_name': 'TRENDZ Trading & Services',
        'company_short': 'TRENDZ',
        'site_title': 'TRENDZ Trading Administration',
        'site_header': 'TRENDZ Trading Administration',
        'primary_color': '#007bff',  # Blue theme for TRENDZ
        'logo_text': 'TRENDZ',
    }
    
    return context