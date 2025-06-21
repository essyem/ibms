from django.conf import settings

def trendz_settings(request):
    return {
        'TRENDZ': settings.TRENDZ_SETTINGS,
        'DEBUG': settings.DEBUG,
    }