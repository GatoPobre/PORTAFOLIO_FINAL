# <-- Agregamos user_logged_out
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from .models import Perfil
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib import messages

# --- SEÑAL DE LOGIN ---


@receiver(user_logged_in)
def show_login_message(sender, user, request, **kwargs):
    mensaje = f"¡Inicio de sesión exitoso! Bienvenido/a de nuevo, {user.username}."
    messages.success(request, mensaje)

    # --- LÓGICA DE FUSIÓN DE CARRITO HÍBRIDO ---
    try:
        from tienda.models import Carro, ItemCarro, Producto

        # 1. Obtener o crear el carro en la base de datos para este usuario
        carro_db, _ = Carro.objects.get_or_create(usuario=user)

        # 2. Leer lo que el usuario agregó como invitado (si hay algo)
        carro_sesion = request.session.get('carro', {})

        # 3. Fusionar datos temporales hacia la base de datos
        if carro_sesion:
            for prod_id_str, datos in carro_sesion.items():
                item_db, created = ItemCarro.objects.get_or_create(
                    carro=carro_db,
                    producto_id=int(prod_id_str),
                    defaults={'cantidad': datos['cantidad']}
                )
                # Si el producto ya estaba en la BD, sumamos las cantidades
                if not created:
                    item_db.cantidad += datos['cantidad']
                    # Validación opcional para no pasarse del stock
                    if item_db.cantidad > item_db.producto.stock:
                        item_db.cantidad = item_db.producto.stock
                    item_db.save()

    except Exception as e:
        print(f"Error fusionando carritos: {e}")


# --- SEÑAL DE LOGOUT  ---
@receiver(user_logged_out)
def show_logout_message(sender, user, request, **kwargs):
    # Usualmente se usa messages.info o messages.success para los cierres de sesión
    if user is not None:
        mensaje = f"Has cerrado sesión exitosamente. ¡Hasta pronto, {user.username}!"
    else:
        mensaje = "Has cerrado sesión exitosamente. ¡Hasta pronto!"

    messages.info(request, mensaje)

# --- SEÑALES (SIGNALS) PARA AUTOMATIZAR LA CREACIÓN DEL PERFIL ---


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea un perfil automáticamente cuando se crea un nuevo User."""
    if created:
        Perfil.objects.create(user=instance)


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Guarda el perfil automáticamente cuando el User se actualiza."""
    instance.perfil.save()
