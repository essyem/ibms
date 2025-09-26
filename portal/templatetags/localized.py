from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def localized(obj, field_name, request=None):
    """Return the localized value for a model object field.

    Usage in template:
      {% load localized %}
      {{ product|localized:"name" }}

    This filter prefers the Arabic field (e.g., name_ar) when the current
    request session or django_language is 'ar'. If the Arabic field is empty,
    it falls back to the default field.
    """
    # Try to access request from template context if passed as second arg
    lang = None
    try:
        # If request is passed (some template engines allow passing context), use it
        if request and hasattr(request, 'session'):
            lang = request.session.get('site_language') or request.session.get('django_language')
    except Exception:
        lang = None

    # If not set via arg, try to read django translation setting from object if available
    if not lang:
        try:
            from django.utils import translation
            lang = translation.get_language()
        except Exception:
            lang = None

    # Build arabic field name
    ar_field = f"{field_name}_ar"

    # If language is Arabic, prefer the Arabic field
    if lang and lang.startswith('ar'):
        try:
            val = getattr(obj, ar_field)
            if val:
                return val
        except Exception:
            pass

    # Fallback to default field
    try:
        return getattr(obj, field_name)
    except Exception:
        return ''
