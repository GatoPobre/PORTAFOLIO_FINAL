"""
forms.py para mi_projecto/miapp
"""
from django import forms
# validar con  expresiones regulares
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.files.uploadedfile import UploadedFile
from .models import Perfil, Contacto
from .validators import validar_correo_real


class ActualizarUsuarioForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


class ActualizarPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['nombre_completo', 'imagen_avatar']
        widgets = {
            'nombre_completo': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            # Al usar FileInput, eliminamos automáticamente la casilla de "Limpiar"
            # y los textos feos por defecto de Django.
            'imagen_avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'  # Sugiere al navegador que solo muestre imágenes
            }),
        }

    def clean_imagen_avatar(self):

        imagen_avatar = self.cleaned_data.get('imagen_avatar')

        if imagen_avatar and isinstance(imagen_avatar, UploadedFile):
            # 1. Validar el tamaño del archivo (Ejemplo: Máximo 5MB)
            tamaño_maximo = 5 * 1024 * 1024  # 5 Megabytes
            peso_megas = imagen_avatar.size / (1024 * 1024)
            peso_megas = round(peso_megas, 2)

            if imagen_avatar.size > tamaño_maximo:
                raise ValidationError(
                    f"El archivo es demasiado pesado. El máximo permitido es 5MB. Peso archivo: {peso_megas} MB")

            # 2. Validar el tipo de contenido real (MIME type)
            # Esto lee la cabecera del archivo HTTP, no solo la extensión
            tipos_permitidos = ['image/jpeg', 'image/png', 'image/webp']
            if imagen_avatar.content_type not in tipos_permitidos:
                raise ValidationError(
                    "El archivo no es una imagen válida o el formato no está soportado.")

        return imagen_avatar

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field_id = f"id_{field_name}"
            field.widget.attrs['aria-describedby'] = f"{field_id}_help {field_id}_error"
            if field.required:
                field.widget.attrs['aria-required'] = 'true'


class FormularioLoginPersonalizado(AuthenticationForm):
    # 1. Sobrescribir los mensajes de error
    error_messages = {
        'invalid_login': 'El usuario o la contraseña son incorrectos. Por favor, intenta de nuevo.',
        'inactive': 'Esta cuenta ha sido desactivada.',
    }
    # 2. Personalizar el aspecto de los campos (HTML, clases CSS, placeholders)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Personalizar el campo de usuario
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',  # Cambia esto por tus clases
            'placeholder': 'Ingresa tu usuario'
        })
        self.fields['username'].error_messages.update({
            'required': '¡Olvidaste escribir tu nombre de usuario!',
        })
        # Cambiar la etiqueta (Label)
        self.fields['username'].label = 'Usuario:'

        # Personalizar el campo de contraseña
        self.fields['password'].error_messages.update({
            'required': 'Necesitamos tu contraseña para dejarte entrar.',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña'
        })
        self.fields['password'].label = 'Contraseña:'

        # Asignar dinámicamente atributos ARIA para accesibilidad
        for field_name, field in self.fields.items():
            field_id = f"id_{field_name}"
            field.widget.attrs['aria-describedby'] = f"{field_id}_help {field_id}_error"
            if field.required:
                field.widget.attrs['aria-required'] = 'true'


class CustomUserCreationForm(UserCreationForm):
    # Definimos el Meta de forma normal, sin paréntesis
    class Meta:
        model = User
        # Aquí listamos los campos que queremos mostrar.
        # (Los campos de contraseña se agregan solos por el UserCreationForm)
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field_id = f"id_{field_name}"
            field.widget.attrs['aria-describedby'] = f"{field_id}_help {field_id}_error"
            if field.required:
                field.widget.attrs['aria-required'] = 'true'


class ContactoForm(forms.Form):

    nombre = forms.CharField(
        label='Nombre completo',
        max_length=100,
        min_length=3,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                message='No se aceptan números ni caracteres especiales.',
                code='nombre_invalido'
            )
        ],
        error_messages={
            'required': 'Este campo es obligatorio.',
            'min_length': 'El nombre debe tener al menos 3 caracteres.',
            'max_length': 'El nombre no puede tener más de 100 caracteres.',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Juan Pérez',
        })
    )
    email = forms.EmailField(
        label='Correo electrónico',
        validators=[validar_correo_real],
        error_messages={
            'required': 'Este campo es obligatorio.',
            'invalid': 'El correo electrónico no es válido.',
        },
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'nombre@ejemplo.com'
        })
    )
    mensaje = forms.CharField(
        label='Mensaje',
        min_length=10,
        max_length=500,
        error_messages={
            'required': 'Este campo es obligatorio.',
            'min_length': 'El mensaje debe tener al menos 10 caracteres.',
            'max_length': 'El mensaje no puede tener más de 500 caracteres.',
        },
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': '¿En qué te podemos ayudar?',
            'style': 'height: 120px'
        })
    )


class ContactoModelForm(forms.ModelForm):

    class Meta:
        """       
        Configuración del formulario basado en el modelo Contacto.
        Define el modelo, los campos a incluir, etiquetas, widgets y mensajes de error.

        """

        model = Contacto
        fields = ['nombre', 'email', 'mensaje']

        labels = {
            'nombre': 'Nombre completo',
            'email': 'Correo electrónico',
            'mensaje': 'Mensaje',
        }

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Juan Pérez',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'nombre@ejemplo.com'
            }),
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '¿En qué te podemos ayudar?',
                'style': 'height: 120px'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Asignar dinámicamente atributos ARIA para mejorar la accesibilidad (WCAG)
        for field_name, field in self.fields.items():
            field_id = f"id_{field_name}"
            # Vinculamos el input con sus contenedores de ayuda y/o error en la plantilla
            field.widget.attrs['aria-describedby'] = f"{field_id}_help {field_id}_error"
            if field.required:
                field.widget.attrs['aria-required'] = 'true'

        # Solo dejamos los errores genéricos que no manejan los validadores del modelo
        error_messages = {
            'nombre': {
                'required': 'Este campo es obligatorio.',
            },
            'email': {
                'required': 'Este campo es obligatorio.',
                'invalid': 'El correo electrónico no es válido.',
            },
            'mensaje': {
                'required': 'Este campo es obligatorio.',
            }
        }
