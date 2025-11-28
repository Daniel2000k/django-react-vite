from django import template

register = template.Library()

@register.filter
def currency_format(value):
    """
    Formatea un número como moneda con separadores de miles.
    Ejemplo: 12345.67 -> $12,345.67
    """
    try:
        return "${:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return value
