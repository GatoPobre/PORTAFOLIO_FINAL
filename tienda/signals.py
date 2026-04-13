from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import Pedido, Producto, Categoria
# --- Dependencias para envío de correo ---
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache
# --- Dependencias para PDF en memoria ---
from io import BytesIO
from xhtml2pdf import pisa


@receiver(pre_save, sender=Pedido)
def manejar_pre_guardado_pedido(sender, instance, **kwargs):
    """
    Signal que se dispara ANTES de guardar un Pedido.
    1. Almacena el estado anterior para usarlo en post_save.
    2. Si el estado del pedido cambia a 'ANULADO', restaura el stock de los productos.
    """
    if instance.pk:
        try:
            pedido_anterior = Pedido.objects.get(pk=instance.pk)
            # Almacenamos el estado viejo en el objeto para usarlo en post_save
            instance._old_estado = pedido_anterior.estado

            # Lógica de restauración de stock
            if instance.estado == 'ANULADO' and pedido_anterior.estado in ['PAGADO', 'ENVIADO']:
                for item in instance.items.all():
                    if item.producto:  # Asegurarse de que el producto no haya sido eliminado
                        item.producto.stock += item.cantidad
                        item.producto.save(update_fields=['stock'])
        except Pedido.DoesNotExist:
            instance._old_estado = None  # Es un objeto nuevo
    else:
        instance._old_estado = None


@receiver(post_save, sender=Pedido)
def notificar_cambio_estado_pedido(sender, instance, created, **kwargs):
    """
    Signal que se dispara DESPUÉS de guardar un Pedido.
    Si el estado del pedido ha cambiado, envía un correo de notificación al cliente.
    Si el estado es 'PAGADO', adjunta la factura en PDF.
    """
    if not created and hasattr(instance, '_old_estado') and instance._old_estado != instance.estado:
        adjuntos_pdf = None

        # --- Lógica específica para cada estado ---
        if instance.estado == 'PAGADO':
            asunto = f"Confirmación de Pago y Factura - Pedido #{instance.id}"
            template_html = 'emails/pedido_pagado.html'
            template_txt = 'emails/pedido_pagado.txt'

            # Generar PDF en memoria para adjuntarlo
            try:
                factura_html_string = render_to_string(
                    'gestion/factura_template.html', {'pedido': instance})
                buffer = BytesIO()
                pisa_status = pisa.pisaDocument(
                    BytesIO(factura_html_string.encode("UTF-8")), buffer)
                if not pisa_status.err:
                    nombre_archivo = f"factura_GatoPobre_#{instance.id}.pdf"
                    adjuntos_pdf = (
                        nombre_archivo, buffer.getvalue(), 'application/pdf')
                else:
                    print(
                        f"Error al generar PDF para adjuntar en correo (Pedido #{instance.id}): {pisa_status.err}")
            except Exception as e:
                print(
                    f"Excepción al generar PDF para adjuntar en correo (Pedido #{instance.id}): {e}")

        else:  # Para otros cambios de estado (ENVIADO, ANULADO)
            asunto = f"Actualización de tu Pedido #{instance.id} en GatoPobreTECK"
            template_html = 'emails/cambio_estado_pedido.html'
            template_txt = 'emails/cambio_estado_pedido.txt'

        # --- Lógica común de envío de correo ---
        try:
            context = {
                'pedido': instance,
                'nuevo_estado': instance.get_estado_display(),
                'es_anulado': instance.estado == 'ANULADO',
            }
            html_content = render_to_string(template_html, context)
            text_content = render_to_string(template_txt, context)

            from_email = getattr(
                settings, 'DEFAULT_FROM_EMAIL', 'noresponder@gatopobreteck.cl')
            msg = EmailMultiAlternatives(
                asunto, text_content, from_email, [instance.email])
            msg.attach_alternative(html_content, "text/html")

            # Adjuntar el PDF si se generó correctamente
            if adjuntos_pdf:
                msg.attach(adjuntos_pdf[0], adjuntos_pdf[1], adjuntos_pdf[2])

            msg.send()
        except Exception as e:
            print(
                f"Error al enviar correo de cambio de estado para pedido #{instance.id}: {e}")


@receiver(post_delete, sender=Producto)
def invalidar_cache_producto_eliminado(sender, instance, **kwargs):
    """Invalida la caché de productos cuando un producto es eliminado."""
    cache.delete('productos_base_list')
    cache.delete('categorias_con_conteo')
    cache.delete('total_productos_disponibles')


@receiver([post_save, post_delete], sender=Categoria)
def invalidar_cache_categoria(sender, instance, **kwargs):
    """Invalida la caché de categorías cuando se crea/edita/elimina una categoría."""
    cache.delete('categorias_con_conteo')
