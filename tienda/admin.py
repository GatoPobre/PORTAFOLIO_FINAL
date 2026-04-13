from django.contrib import admin
from .models import Producto, Pedido, ItemPedido, Categoria


class ItemPedidoInline(admin.StackedInline):
    model = ItemPedido
    extra = 0  # No mostrar campos vacíos por defecto
    readonly_fields = ('producto', 'cantidad', 'precio_unitario')


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_creacion')
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    # 1. ¿Qué columnas queremos ver en la lista principal?
    list_display = ('nombre', 'categoria', 'precio', 'stock',
                    'fecha_creacion', 'tiene_imagen')

    # 2. ¿Por qué campos queremos poder buscar? (Aparecerá una barra de búsqueda)
    search_fields = ('nombre', 'descripcion_corta', 'caracteristicas')

    # 3. ¿Qué filtros queremos en la barra lateral derecha?
    list_filter = ('categoria', 'fecha_creacion',)

    # 4. Campos que no se pueden editar (solo lectura)
    readonly_fields = ('fecha_creacion',)

    # 5. Orden por defecto en el panel (opcional, si quieres sobreescribir el del modelo)
    ordering = ('-fecha_creacion',)

    # 6. Un pequeño método personalizado para mostrar si el producto tiene foto o no
    def tiene_imagen(self, obj):
        return bool(obj.imagen)
    tiene_imagen.short_description = '¿Tiene Foto?'
    tiene_imagen.boolean = True  # Muestra un ícono de check/cruz en lugar de True/False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # Mostrar los ítems del pedido directamente en el pedido
    inlines = [ItemPedidoInline]

    # 1. Las columnas que verás en la tabla principal de pedidos
    list_display = ('id', 'nombre_cliente', 'email',
                    'total_pagado', 'fecha_pedido')

    # 2. Una barra de búsqueda para encontrar clientes rápido
    search_fields = ('nombre_cliente', 'email', 'direccion')

    # 3. Filtros laterales (muy útil para ver las ventas de "Hoy" o de esta semana)
    list_filter = ('fecha_pedido',)
    date_hierarchy = 'fecha_pedido'  # Permite navegar por fechas

    # 4. Campos de solo lectura (por seguridad, no queremos que alguien cambie
    # por error el total que ya pagó el cliente o la fecha original)
    readonly_fields = ('fecha_pedido', 'total_pagado',
                       'nombre_cliente', 'email', 'direccion')

    # 5. Ordenamos para que los pedidos más recientes aparezcan siempre arriba
    ordering = ('-fecha_pedido',)

    # Agrupar campos en el formulario de detalle del pedido
    fieldsets = (
        (None, {'fields': ('usuario', 'nombre_cliente',
         'email', 'direccion', 'total_pagado')}),
        ('Información del Sistema', {'fields': ('fecha_pedido',)}),
    )
