from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiplies value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
