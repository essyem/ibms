from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def mul(value, multiplier):
    """Multiply two values"""
    try:
        return Decimal(str(value)) * Decimal(str(multiplier))
    except (ValueError, TypeError, InvalidOperation):
        return 0

@register.filter
def currency(value):
    """Format currency with QAR"""
    try:
        return f"QAR {Decimal(str(value)):.2f}"
    except (ValueError, TypeError):
        return "QAR 0.00"

@register.filter
def format_phone(value):
    """Format phone number for display"""
    if not value:
        return value
    
    # Remove + and spaces for processing
    phone = str(value).replace('+', '').replace(' ', '').replace('-', '')
    
    # Format Qatar numbers (+974 XXXX XXXX)
    if phone.startswith('974') and len(phone) == 11:
        return f"+974 {phone[3:7]} {phone[7:]}"
    
    # Format other international numbers
    if len(phone) > 10:
        country_code = phone[:3]
        rest = phone[3:]
        if len(rest) >= 8:
            return f"+{country_code} {rest[:4]} {rest[4:]}"
    
    # Default formatting
    return value