from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Contacto, Perfil


# Register your models here.
admin.site.site_header = "Administración de Tienda"
admin.site.site_title = "Panel Administrativo"
admin.site.index_title = "Gestión de Usuarios, Roles y Permisos"


"""class CustomUserAdmin(UserAdmin):
    def get_fieldsets(self, request, obj=None):
        # Obtenemos los fieldsets originales convirtiéndolos a lista de forma segura
        fieldsets = list(super().get_fieldsets(request, obj))

        # Le añadimos nuestros campos extra
        fieldsets.append(
            ('Información Extra', {
             'fields': ('nombre_completo', 'imagen_avatar')})
        )
        return tuple(fieldsets)

    # Columnas que quieres que aparezcan en la lista de usuarios
    list_display = ('username', 'email', 'first_name',
                    'last_name', 'imagen_avatar', 'is_staff')"""


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Información Adicional del Perfil'


class CustomUserAdmin(UserAdmin):
    inlines = (PerfilInline,)
    # Campos visibles en el listado
    list_display = (
        'username',
        'email',
        'is_staff',
        'is_active',
    )

    # Filtros laterales
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        'groups',
    )

    # Búsqueda
    search_fields = ('username', 'email')

    # Orden por defecto
    ordering = ('username',)

    # Organización de formularios
    fieldsets = (
        ('Credenciales', {
            'fields': ('username', 'password')
        }),
        ('Información personal', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Roles y permisos', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Fechas del sistema', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    # Campos de solo lectura
    readonly_fields = ('last_login', 'date_joined')


# Registramos el modelo junto con su configuración
admin.site.unregister(User)  # se usa solamente al extender el modelo User
admin.site.register(User, CustomUserAdmin)


@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    # 1. Personalizar las columnas mostradas
    list_display = ('id', 'nombre', 'email')

    # 2. Agregar una barra de búsqueda (muy útil cuando hay muchos mensajes)
    search_fields = ('nombre', 'email')

    # 3. Hacer que las columnas se puedan ordenar (opcional)
    # El signo menos (-) ordena del más reciente al más antiguo
    ordering = ('-id',)
