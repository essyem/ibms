from django.conf import settings

def trendz_settings(request):
    """
    Single-tenant context processor for TRENDZ Trading & Services
    """
    return {
        'TRENDZ': getattr(settings, 'TRENDZ_SETTINGS', {}),
        'DEBUG': settings.DEBUG,
        # Single-tenant TRENDZ branding
        'company_name': 'TRENDZ Trading & Services',
        'company_short': 'TRENDZ',
        'site_title': 'TRENDZ Trading Portal',
        'site_header': 'TRENDZ Trading Administration',
        'primary_color': '#007bff',
        'secondary_color': '#6c757d',
        'logo_text': 'TRENDZ',
        'company_address': 'Sofitel Complex, Msheireb Street, Doha, Qatar',
        'company_phone': '+974 30514865',
        'whatsapp_number': getattr(settings, 'WHATSAPP_BUSINESS_NUMBER', '+97430514865'),
        'company_email': 'info@trendzqtr.com',
        'company_website': 'www.trendzqtr.com',
    }