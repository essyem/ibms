from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiplies value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def number_to_words(value):
    """Convert number to words (English)"""
    try:
        value = int(float(value))
    except (ValueError, TypeError):
        return ""
    
    if value == 0:
        return "Zero"
    
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    def convert_hundreds(num):
        result = ""
        if num >= 100:
            result += ones[num // 100] + " Hundred "
            num %= 100
        if num >= 20:
            result += tens[num // 10] + " "
            num %= 10
        if num > 0:
            result += ones[num] + " "
        return result.strip()
    
    if value < 0:
        return "Negative " + number_to_words(-value)
    
    if value < 1000:
        return convert_hundreds(value)
    elif value < 1000000:
        thousands = value // 1000
        remainder = value % 1000
        result = convert_hundreds(thousands) + " Thousand"
        if remainder > 0:
            result += " " + convert_hundreds(remainder)
        return result
    elif value < 1000000000:
        millions = value // 1000000
        remainder = value % 1000000
        result = convert_hundreds(millions) + " Million"
        if remainder > 0:
            if remainder >= 1000:
                result += " " + number_to_words(remainder)
            else:
                result += " " + convert_hundreds(remainder)
        return result
    else:
        return str(value)  # For very large numbers, just return the number
