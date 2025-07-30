from django import template
import arabic_reshaper
from bidi.algorithm import get_display

register = template.Library()

@register.filter
def arabic_display(text):
    """Process Arabic text for proper display in PDFs"""
    if not text:
        return text
    
    try:
        # Reshape Arabic text for proper connection of letters
        reshaped_text = arabic_reshaper.reshape(text)
        # Apply bidirectional algorithm
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception:
        # If processing fails, return original text
        return text
