from django import template

register = template.Library()


@register.filter
def currency_format(value):
    """
    Formatea un número como moneda con puntos cada mil y sin decimales si es .00
    Ejemplo: 1234567.89 → 1.234.568 (redondea)
                1000.00 → 1.000
                500.50 → 501 (redondea)
                123.45 → 123
    """
    try:
        # Convertir a float si no lo es
        num = float(value)
        
        # Redondear sin decimales
        num = round(num)
        
        # Formatear con puntos cada mil
        return "{:,}".format(num).replace(",", ".")
    except (ValueError, TypeError):
        return value


@register.filter
def currency_format_decimal(value):
    """
    Formatea un número como moneda con puntos cada mil y 2 decimales si son diferentes a .00
    Ejemplo: 1234567.89 → 1.234.567,89
                1000.00 → 1.000
                500.50 → 500,50
    """
    try:
        num = float(value)
        
        # Verificar si tiene decimales significativos
        if num % 1 == 0:
            # Sin decimales
            return "{:,}".format(int(num)).replace(",", ".")
        else:
            # Con 2 decimales
            formatted = "{:,.2f}".format(num)
            # Reemplazar comas por puntos (separador de miles) y punto por coma (decimales)
            return formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return value
