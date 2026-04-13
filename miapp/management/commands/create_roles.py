# miapp/management/commands/create_roles.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.db.utils import OperationalError
from django.contrib.contenttypes.models import ContentType
from tienda.models import Producto, Categoria, Pedido


class Command(BaseCommand):
    """
    Comandos para crear roles y asignar permisos.

    """
    help = 'Crea roles para la tienda y asigna permisos'

    def handle(self, *args, **options):
        # Definimos los permisos por modelo para que sea más fácil de gestionar
        permisos_producto = [
            'add_producto', 'change_producto', 'delete_producto', 'view_producto']
        permisos_categoria = [
            'add_categoria', 'change_categoria', 'delete_categoria', 'view_categoria']
        permisos_pedido = ['view_pedido', 'change_pedido']

        configuracion_roles = {
            'Administrador': [
                {'modelo': Producto, 'permisos': permisos_producto},
                {'modelo': Categoria, 'permisos': permisos_categoria},
                {'modelo': Pedido, 'permisos': permisos_pedido},
            ],
            'Gestor de Inventario': [
                {'modelo': Producto, 'permisos': [
                    'add_producto', 'change_producto', 'view_producto']},
                {'modelo': Categoria, 'permisos': [
                    'add_categoria', 'change_categoria', 'view_categoria']},
            ],
            'Gestor de Ventas': [
                {'modelo': Producto, 'permisos': ['view_producto']},
                {'modelo': Categoria, 'permisos': ['view_categoria']},
                {'modelo': Pedido, 'permisos': permisos_pedido},
            ],
            'Cliente': [
                # Un cliente normal no necesita permisos de modelo para comprar.
            ],
        }

        try:
            for rol, configuraciones in configuracion_roles.items():
                grupo, created = Group.objects.get_or_create(name=rol)
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f"Grupo '{rol}' creado."))
                else:
                    self.stdout.write(
                        f"Grupo '{rol}' ya existe. Actualizando permisos.")

                # Limpiar permisos existentes para que las actualizaciones a los roles surtan efecto
                grupo.permissions.clear()

                for config in configuraciones:
                    modelo = config['modelo']
                    permisos_codename = config['permisos']

                    content_type = ContentType.objects.get_for_model(modelo)

                    for codename in permisos_codename:
                        try:
                            permiso = Permission.objects.get(
                                codename=codename, content_type=content_type)
                            grupo.permissions.add(permiso)
                        except Permission.DoesNotExist:
                            self.stdout.write(self.style.WARNING(
                                f"  - Permiso '{codename}' para modelo '{modelo.__name__}' no encontrado. Omitiendo."))
        except (OperationalError, ContentType.DoesNotExist) as e:
            self.stdout.write(self.style.ERROR(
                f"Error: {e}. Asegúrate de haber ejecutado 'python manage.py migrate' primero."))
            return
        self.stdout.write(self.style.SUCCESS(
            "Proceso de creación de roles finalizado."))

        # --- Crear Usuarios de Prueba ---
        self.stdout.write("--- Creando usuarios de prueba ---")
        usuarios_prueba = [
            {'username': 'cliente', 'password': 'pera1234', 'grupo': 'Cliente'},
            {'username': 'gestor', 'password': 'pera1234',
                'grupo': 'Gestor de Inventario'},
        ]

        for data in usuarios_prueba:
            user, created = User.objects.get_or_create(
                username=data['username'])
            if created:
                user.set_password(data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Usuario '{data['username']}' creado exitosamente."))
            else:
                self.stdout.write(f"Usuario '{data['username']}' ya existe.")

            # Asignar el grupo al usuario
            try:
                grupo = Group.objects.get(name=data['grupo'])
                user.groups.add(grupo)
                self.stdout.write(self.style.SUCCESS(
                    f"  - Rol '{data['grupo']}' asignado a '{data['username']}'."))
            except Group.DoesNotExist:
                self.stdout.write(self.style.ERROR(
                    f"  - Error: El grupo '{data['grupo']}' no fue encontrado."))
