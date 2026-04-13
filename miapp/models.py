"""
models.py para mi_projecto/miapp
"""
from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator, FileExtensionValidator
from django.contrib.auth.models import User
from PIL import Image
from .validators import validar_correo_real


class Perfil(models.Model):
    # Relación 1 a 1 con el modelo User de Django
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='perfil')

    # Campos adicionales
    nombre_completo = models.CharField(max_length=200, blank=True, null=True,
                                       validators=[
                                           MinLengthValidator(
                                               3, message='El nombre debe tener al menos 3 caracteres.'),
                                           RegexValidator(
                                               regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                                               message='No se aceptan números ni caracteres especiales.',
                                               code='nombre_invalido'
                                           )
                                       ]
                                       )
    imagen_avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        default='avatars/default.png',
        validators=[FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )

    def save(self, *args, **kwargs):
        # 1. Primero dejamos que Django guarde el perfil y la imagen original
        super().save(*args, **kwargs)

        # 2. Verificamos si el perfil tiene una imagen asociada
        if self.imagen_avatar and hasattr(self.imagen_avatar, 'path'):
            try:
                # Usamos 'with' para asegurar que el archivo se cierre automáticamente de la memoria (PEP8)
                with Image.open(self.imagen_avatar.path) as img:
                    # Definimos el tamaño máximo (ej. 300x300 px)
                    tamaño_maximo = (300, 300)

                    # Si la imagen es más grande que nuestro límite...
                    if img.height > tamaño_maximo[0] or img.width > tamaño_maximo[1]:
                        # Redimensiona manteniendo la proporción exacta
                        img.thumbnail(tamaño_maximo)

                        # Guardamos sobrescribiendo la anterior con optimización
                        img.save(self.imagen_avatar.path,
                                 quality=85, optimize=True)
            except FileNotFoundError:
                # Evita errores si la imagen por defecto no está en el disco al crear el perfil
                pass

    def __str__(self):
        return f'{self.user.username}'


class Contacto(models.Model):
    """
    Modelo para representar un mensaje de contacto.

    Campos: nombre, email, mensaje.

    Validaciones:max_length, validators.

    """
    nombre = models.CharField(
        max_length=100,
        validators=[
            MinLengthValidator(
                3, message='El nombre debe tener al menos 3 caracteres.'),
            RegexValidator(
                regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                message='No se aceptan números ni caracteres especiales.',
                code='nombre_invalido'
            )
        ]
    )

    email = models.EmailField(
        validators=[validar_correo_real]
    )

    mensaje = models.TextField(  # Usamos TextField para textos largos
        max_length=500,
        validators=[
            MinLengthValidator(
                10, message='El mensaje debe tener al menos 10 caracteres.')
        ]
    )

    def __str__(self):
        return f"Mensaje de: {self.nombre}"
