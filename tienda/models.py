from django.contrib.auth.models import User  # <-- Asegúrate de importar esto
from django.db import models
from django.core.validators import MinValueValidator
import os
from PIL import Image
from django.core.cache import cache


class Categoria(models.Model):
    nombre = models.CharField(
        max_length=100, unique=True, verbose_name="Nombre de la Categoría")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(
        max_length=200, verbose_name="Nombre del producto")
    descripcion_corta = models.CharField(
        max_length=255, help_text="Breve descripción para la página principal")
    caracteristicas = models.TextField(
        verbose_name="Características y detalles completos")
    # Usa IntegerField si tus precios son en pesos chilenos/colombianos, o DecimalField si usas centavos.
    precio = models.IntegerField(
        verbose_name="Precio", validators=[MinValueValidator(1)])
    stock = models.PositiveIntegerField(
        default=0, verbose_name="Cantidad disponible")
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name='productos', null=True, blank=True, verbose_name="Categoría")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Así los más nuevos salen primero por defecto
        ordering = ['-fecha_creacion']
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Primero, guardamos el objeto para asegurarnos de que la imagen tiene una ruta
        # si es un objeto nuevo.
        super().save(*args, **kwargs)

        # Invalidar la caché automáticamente cuando se crea/edita un producto
        cache.delete('productos_base_list')
        cache.delete('categorias_con_conteo')
        cache.delete('total_productos_disponibles')

        # Optimización de rendimiento: redimensionar y comprimir imágenes de productos
        # Solo procesar si hay una imagen y no es ya un archivo .webp
        if self.imagen and hasattr(self.imagen, 'path') and not self.imagen.path.lower().endswith('.webp'):
            # Guardar la ruta original ANTES de cualquier cambio
            original_path = self.imagen.path
            try:
                with Image.open(original_path) as img:
                    # Convertir a RGB si la imagen tiene canal Alpha (PNG) para evitar errores
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")

                    # Redimensionar si es más grande de 800x800
                    if img.height > 800 or img.width > 800:
                        img.thumbnail((800, 800))

                    # Generar la nueva ruta con extensión .webp
                    ruta_base, _ = os.path.splitext(original_path)
                    nueva_ruta = f"{ruta_base}.webp"
                    nuevo_nombre = os.path.basename(nueva_ruta)

                    # Guardar como WebP optimizado y reemplazar el archivo en el modelo
                    img.save(nueva_ruta, 'WEBP', quality=85, optimize=True)
                    self.imagen.name = nuevo_nombre
                    # Guardar solo el campo de la imagen para evitar bucles
                    super().save(update_fields=['imagen'])

                    # Si la conversión fue exitosa y el nombre del archivo cambió, borramos el original
                    if os.path.exists(original_path) and original_path != self.imagen.path:
                        os.remove(original_path)
            except (FileNotFoundError, ValueError):  # ValueError para imágenes corruptas
                pass


class Pedido(models.Model):
    ESTADOS_PEDIDO = [
        ('INGRESADO', 'Ingresado'),
        ('PAGADO', 'Pagado'),
        ('ENVIADO', 'Enviado'),
        ('ANULADO', 'Anulado'),
    ]

    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos')
    nombre_cliente = models.CharField(
        max_length=100, verbose_name="Nombre Completo")
    email = models.EmailField(verbose_name="Correo Electrónico")
    direccion = models.CharField(
        max_length=250, verbose_name="Dirección de Envío")
    total_pagado = models.IntegerField(verbose_name="Total Pagado")
    fecha_pedido = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha del Pedido")
    estado = models.CharField(
        max_length=10, choices=ESTADOS_PEDIDO, default='INGRESADO', verbose_name="Estado del Pedido")

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_pedido']

    def __str__(self):
        return f"Pedido #{self.id} - {self.nombre_cliente}"


class ItemPedido(models.Model):
    """
    Representa un producto específico dentro de un pedido.
    Guarda el estado del producto (nombre, precio) al momento de la compra.
    """
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(
        Producto, on_delete=models.SET_NULL, null=True, verbose_name="Producto Original")
    nombre_producto = models.CharField(
        max_length=200, verbose_name="Nombre del Producto (al momento de la compra)")
    cantidad = models.PositiveIntegerField(
        verbose_name="Cantidad", validators=[MinValueValidator(1)])
    precio_unitario = models.IntegerField(
        verbose_name="Precio Unitario (al momento de la compra)", validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Item de Pedido"
        verbose_name_plural = "Items de Pedido"

    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto} en Pedido #{self.pedido.id}"


# --- MODELOS PARA CARRITO PERSISTENTE ---

class Carro(models.Model):
    """Carrito de compras persistente asociado a un usuario registrado."""
    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='carro_persistente'
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carro Persistente"
        verbose_name_plural = "Carros Persistentes"

    def __str__(self):
        return f"Carrito de {self.usuario.username}"


class ItemCarro(models.Model):
    """Producto individual dentro del carrito persistente."""
    carro = models.ForeignKey(
        Carro, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
