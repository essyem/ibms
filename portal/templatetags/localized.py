from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def localized(obj, field_name):
    """Return the localized value for a model object field.

    Usage in template:
      {% load localized %}
      {{ product|localized:"name" }}

    This filter prefers the Arabic field (e.g., name_ar) when the current
    request session or django_language is 'ar'. If the Arabic field is empty,
    it falls back to the default field.
    """
    # Determine active language from Django translation machinery
    lang = None
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
