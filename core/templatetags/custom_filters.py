from django import template
from decimal import Decimal
import re

register = template.Library()

@register.filter
def clp(value):
    if value is None:
        return '0'
    try:
        val = Decimal(str(value))
        val_str = f"{val:.2f}"
    except:
        return str(value)
    
    if val_str.endswith('.00'):
        val_str = val_str[:-3]
    else:
        val_str = val_str.replace('.', ',')
        
    parts = val_str.split(',')
    int_part = parts[0]
    int_part = re.sub(r'\B(?=(\d{3})+(?!\d))', '.', int_part)
    
    if len(parts) > 1:
        return f"{int_part},{parts[1]}"
    return int_part
