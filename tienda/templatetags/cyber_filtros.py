# tienda/templatetags/cyber_filtros.py
from django import template

register = template.Library()


@register.filter
def puntos(value):
    """
    Convierte un número agregando puntos como separador de miles.
    Ejemplo: 1500000 -> 1.500.000
    """
    try:
        # Formatea con comas estándar de Python y luego las cambia por puntos
        return f"{int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return value


@register.filter
def get_item(dictionary, key):
    """
    Permite acceder a un valor de un diccionario usando una variable como clave.
    Uso: {{ mi_diccionario|get_item:mi_variable_con_la_clave }}
    """
    return dictionary.get(key)


@register.filter
def estado_color(estado):
    """Devuelve un color hexadecimal según el estado del pedido."""
    colores = {
        'INGRESADO': '#00f3ff',  # Cyber Blue
        'PAGADO': '#00ff41',     # Neon Green
        'ENVIADO': '#f8f9fa',    # Blanco
        'ANULADO': '#ff003c',    # Neon Red
    }
    return colores.get(estado, '#6c757d')  # Gris por defecto
