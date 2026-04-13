"""
validators.py para mi_projecto/miapp
"""
from django.core.exceptions import ValidationError

# Definición de la lista negra de dominios temporales
DOMINIOS_TEMPORALES = [
    'yopmail.com',
    '10minutemail.com',
    'mailinator.com',
    'guerrillamail.com',
    'tempmail.com',
    'temp-mail.org',
    'mula.com'
    # Puedes ir agregando más dominios a esta lista según lo necesites
]


def validar_correo_real(value):
    """Valida que el correo electrónico no pertenezca a un dominio de correos temporales.

    Args:
        value: El correo electrónico a validar.

    Raises:
        ValidationError: Si el correo electrónico pertenece a un dominio de correos temporales. 

    """
    # 'value' es el correo completo, ej: "usuario@yopmail.com"
    # Dividimos por el '@' y tomamos la última parte (el dominio) en minúsculas
    dominio = value.split('@')[-1].lower()

    if dominio in DOMINIOS_TEMPORALES:
        raise ValidationError(message='No se aceptan correos temporales. Por favor, usa una cuenta válida.',
                              code='correo_invalido'
                              )
