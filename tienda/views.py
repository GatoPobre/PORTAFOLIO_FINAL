"""
views.py para mi_projecto/tienda
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.db.models import Q, Count
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from .models import Producto, Pedido, ItemPedido, Carro, ItemCarro, Categoria
from .forms import ProductoForm, CategoriaForm
from django.http import JsonResponse

import json

# --- Dependencias para PDF ---
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa


def inicio(request):
    """
    Muestra la página principal de la tienda.

    Obtiene los últimos 10 productos con stock disponible y los pasa a la plantilla.
    """
    # --- LÓGICA DE CACHÉ PARA CONSULTAS PESADAS ---
    productos_cache_key = 'productos_base_list'
    categorias_cache_key = 'categorias_con_conteo'
    total_cache_key = 'total_productos_disponibles'

    productos_list = cache.get(productos_cache_key)
    if productos_list is None:
        # Si no está en caché, hacemos la consulta y la guardamos por 15 minutos
        productos_list = list(Producto.objects.select_related(
            'categoria').all().order_by('-fecha_creacion'))
        cache.set(productos_cache_key, productos_list, 900)

    categorias = cache.get(categorias_cache_key)
    if categorias is None:
        categorias = list(Categoria.objects.annotate(
            num_productos=Count('productos', filter=Q(productos__stock__gt=0))
        ).order_by('nombre'))
        cache.set(categorias_cache_key, categorias, 900)

    total_productos_disponibles = cache.get(total_cache_key)
    if total_productos_disponibles is None:
        total_productos_disponibles = Producto.objects.filter(
            stock__gt=0).count()
        cache.set(total_cache_key, total_productos_disponibles, 900)

    categoria_seleccionada = None

    # --- FILTROS Y BÚSQUEDA (se aplican sobre la lista ya cacheada) ---
    # Búsqueda por nombre o ID
    # Copiamos para no modificar la caché original
    productos_filtrados = list(productos_list)
    query = request.GET.get('q', '').strip()
    if query:
        if query.isdigit():
            query_num = int(query)
            productos_filtrados = [
                p for p in productos_filtrados if query.lower() in p.nombre.lower() or p.id == query_num]
        else:
            productos_filtrados = [
                p for p in productos_filtrados if query.lower() in p.nombre.lower()]

    # Filtro por categoría
    categoria_id = request.GET.get('categoria', '').strip()
    if categoria_id and categoria_id.isdigit():
        cat_id_num = int(categoria_id)
        productos_filtrados = [
            p for p in productos_filtrados if p.categoria and p.categoria.id == cat_id_num]
        try:
            # Obtenemos el objeto de la categoría para mostrar su nombre
            categoria_seleccionada = Categoria.objects.get(
                id=int(categoria_id))
        except Categoria.DoesNotExist:
            # Si el ID de categoría no es válido, no hacemos nada y mostramos todos
            pass

    paginator = Paginator(productos_filtrados, 10)  # 10 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'mi_boton': 'Ver productos',
        'ultimos_productos': page_obj,
        'page_obj': page_obj,
        'query': query,
        'categorias': categorias,
        'total_productos_disponibles': total_productos_disponibles,
        'categoria_seleccionada': categoria_seleccionada,
        'categoria_id': categoria_id,  # Para mantener el filtro en la paginación
    }
    return render(request, 'tienda.html', context)


def producto_detalle(request, producto_id):
    """
    Muestra la página de detalle de un producto específico.

    Recibe el ID del producto y lo busca en la base de datos.
    Si no lo encuentra, devuelve un error 404.
    """
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'producto_detalle.html', {'producto': producto})


def agregar_carro(request, producto_id):
    """
    Procesa la adición de un producto al carrito de compras en la sesión,
    validando que la cantidad no exceda el stock disponible.
    Solo responde a peticiones POST.
    """
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)
        cantidad_solicitada = int(request.POST.get('cantidad', 1))
        carro = request.session.get('carro', {})
        id_carrito = str(producto.id)

        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

        # Validación estricta: No permitir añadir si el producto está en 0
        if producto.stock <= 0:
            error_msg = f">_ ERROR: El módulo '{producto.nombre}' está agotado."
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return redirect('tienda:producto_detalle', producto_id=producto_id)

        if id_carrito in carro:
            # Si el producto ya está en el carrito, calculamos la nueva cantidad total
            cantidad_actual_en_carro = carro[id_carrito]['cantidad']
            nueva_cantidad_total = cantidad_actual_en_carro + cantidad_solicitada

            # Validar que la cantidad total no exceda el stock
            if nueva_cantidad_total > producto.stock:
                error_msg = f"Solo quedan {producto.stock} unidades disponibles. Ya tienes {cantidad_actual_en_carro} en el carrito."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tienda:producto_detalle', producto_id=producto_id)

            # Actualizar la cantidad en el carrito
            carro[id_carrito]['cantidad'] = nueva_cantidad_total
        else:
            # Si es un nuevo producto, validar que la cantidad solicitada no exceda el stock
            if cantidad_solicitada > producto.stock:
                error_msg = f"Lo sentimos, solo quedan {producto.stock} unidades de {producto.nombre} disponibles."
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('tienda:producto_detalle', producto_id=producto_id)

            # Añadir el nuevo producto al carrito
            carro[id_carrito] = {
                'nombre': producto.nombre,
                'precio': producto.precio,
                'cantidad': cantidad_solicitada,
                'imagen': producto.imagen.url if producto.imagen else None,
            }

        request.session['carro'] = carro
        success_msg = f"Se agregaron {cantidad_solicitada} unidades de {producto.nombre} a tu carrito."

        if is_ajax:
            cantidad_total = sum(item['cantidad'] for item in carro.values())
            return JsonResponse({'success': True, 'message': success_msg, 'cantidad_total': cantidad_total})

        messages.success(request, success_msg)

    return redirect('tienda:producto_detalle', producto_id=producto_id)


def ver_carro(request):
    """
    Muestra el contenido del carrito de compras.

    Obtiene el carrito de la sesión, calcula el total y lo muestra en la plantilla.
    """

    carro = request.session.get('carro', {})

    total = 0

    for item in carro.values():

        total += item['precio'] * item['cantidad']

    return render(request, 'carrito.html', {'carro': carro, 'total': total})


@require_POST
def eliminar_producto(request, producto_id):
    """
    Elimina un producto del carrito de compras en la sesión.

    Busca el producto por su ID y lo elimina del diccionario del carrito.
    """

    carro = request.session.get('carro', {})

    id_carrito = str(producto_id)

    if id_carrito in carro:
        del carro[id_carrito]

        request.session['carro'] = carro

        # --- LÓGICA DE CARRITO PERSISTENTE (HÍBRIDO) ---
        if request.user.is_authenticated:
            ItemCarro.objects.filter(
                carro__usuario=request.user, producto_id=producto_id).delete()

        # Opcional: un mensajito para confirmar
        messages.warning(request, "Producto eliminado del carrito.")

    return redirect('tienda:ver_carro')


@require_POST
def vaciar_carro(request):
    """Vacia completamente el carrito de compras en la sesión."""
    if 'carro' in request.session:
        del request.session['carro']

        # --- LÓGICA DE CARRITO PERSISTENTE (HÍBRIDO) ---
        if request.user.is_authenticated:
            ItemCarro.objects.filter(carro__usuario=request.user).delete()

        messages.warning(
            request, ">_ ALERTA: Memoria caché purgada por completo.")

    return redirect('tienda:ver_carro')


def actualizar_cantidad_carro(request, producto_id):
    """Actualiza la cantidad de un producto en el carrito vía AJAX."""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            nueva_cantidad = int(data.get('cantidad', 1))
            producto = get_object_or_404(Producto, id=producto_id)

            carro = request.session.get('carro', {})
            id_carrito = str(producto_id)

            if id_carrito in carro:
                if nueva_cantidad > producto.stock:
                    return JsonResponse({'success': False, 'error': f'>_ ERROR: Stock máximo disponible es {producto.stock}.'})

                if nueva_cantidad < 1:
                    nueva_cantidad = 1

                carro[id_carrito]['cantidad'] = nueva_cantidad
                request.session['carro'] = carro

                # --- LÓGICA DE CARRITO PERSISTENTE (HÍBRIDO) ---
                # Sincronizar el cambio de cantidad con la base de datos
                if request.user.is_authenticated:
                    carro_db, _ = Carro.objects.get_or_create(
                        usuario=request.user)
                    ItemCarro.objects.update_or_create(
                        carro=carro_db,
                        producto=producto,
                        defaults={'cantidad': nueva_cantidad}
                    )

                subtotal = carro[id_carrito]['precio'] * nueva_cantidad
                total = sum(item['precio'] * item['cantidad']
                            for item in carro.values())
                cantidad_total = sum(item['cantidad']
                                     for item in carro.values())

                return JsonResponse({'success': True, 'subtotal': subtotal, 'total': total, 'cantidad_total': cantidad_total})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Petición inválida'})


@login_required
@never_cache
def checkout(request):
    """
    Gestiona el proceso de finalización de la compra, creando un pedido,
    validando y actualizando el stock de los productos.
    - Si el carrito está vacío, redirige a la tienda.
    - Si es GET, muestra el formulario de checkout con el total.
    - Si es POST, procesa los datos del cliente, crea un nuevo objeto Pedido
      asociado al usuario (si está autenticado), vacía el carrito y redirige
      a la página de éxito.
    """
    # 1. Traemos el casillero
    carro = request.session.get('carro', {})

    # 2. Si el carro está vacío, bloqueamos el acceso y lo devolvemos
    if not carro:
        messages.warning(
            request, "Tu carrito está vacío. Agrega productos primero.")
        return redirect('tienda:tienda')

    # 3. Calculamos el total nuevamente por seguridad
    total = 0
    for item in carro.values():
        total += item['precio'] * item['cantidad']

    # 4. Cuando el cliente envía el formulario de pago
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        direccion = request.POST.get('direccion')

        with transaction.atomic():
            # --- VALIDACIÓN DE STOCK FINAL PREVINIENDO CONDICIONES DE CARRERA ---
            stock_problemas = []
            productos_a_actualizar = []

            for producto_id_str, item_data in carro.items():
                producto_id = int(producto_id_str)
                # select_for_update() BLOQUEA la fila en la BD hasta que termine la transacción
                producto = get_object_or_404(
                    Producto.objects.select_for_update(), id=producto_id)
                cantidad_en_carro = item_data['cantidad']

                if cantidad_en_carro > producto.stock:
                    stock_problemas.append(
                        f"'{producto.nombre}' (disponible: {producto.stock}, en carrito: {cantidad_en_carro})"
                    )
                else:
                    productos_a_actualizar.append(
                        {'producto': producto, 'cantidad': cantidad_en_carro, 'precio': item_data['precio']})

            if stock_problemas:
                messages.error(
                    request, f"No se pudo completar la compra debido a problemas de stock con los siguientes productos: {', '.join(stock_problemas)}. Por favor, ajusta tu carrito.")
                # Redirigir al carrito abortará la transacción implícitamente
                return redirect('tienda:ver_carro')

            # Como usamos @login_required, request.user siempre será un usuario autenticado
            usuario_actual = request.user

            # Creamos el pedido asociándolo directamente al usuario autenticado
            nuevo_pedido = Pedido.objects.create(
                usuario=usuario_actual,
                nombre_cliente=nombre,
                email=email,
                direccion=direccion,
                total_pagado=total
            )

            # --- Crear los ItemPedido y descontar stock simultáneamente ---
            for item_data in productos_a_actualizar:
                producto_obj = item_data['producto']
                cantidad_comprada = item_data['cantidad']

                ItemPedido.objects.create(
                    pedido=nuevo_pedido,
                    producto=producto_obj,
                    nombre_producto=producto_obj.nombre,
                    cantidad=cantidad_comprada,
                    precio_unitario=item_data['precio']
                )

                # Descontar stock del producto bloqueado
                producto_obj.stock -= cantidad_comprada
                producto_obj.save()

        # ¡LA MAGIA! Vaciamos el casillero borrando la variable de la sesión
        request.session['carro'] = {}

        # --- LÓGICA DE CARRITO PERSISTENTE (HÍBRIDO) ---
        # Vaciamos también el carrito en la base de datos para este usuario
        ItemCarro.objects.filter(carro__usuario=request.user).delete()

        # Lo enviamos a la página de celebración (ajusta 'tienda' al nombre real de tu app si es otro)
        messages.success(
            request, f"Se registro exitosamente tu pedido #{nuevo_pedido.id}.")
        return redirect('tienda:exito')

    # Si el método es GET (solo entró a la página a mirar), le mostramos el formulario
    return render(request, 'checkout.html', {'total': total})


@login_required
@never_cache
def exito(request):
    """Muestra la página de confirmación de pedido exitoso."""
    return render(request, 'exito.html')


@login_required
def pedido_detalle(request, pedido_id):
    """
    Vista que devuelve los detalles de un pedido y sus ítems.
    Accesible para el usuario propietario del pedido o para usuarios con permisos de gestión.
    """
    # 1. Obtenemos el pedido solo por su ID, precargando datos relacionados para eficiencia.
    pedido = get_object_or_404(Pedido.objects.prefetch_related(
        'items__producto'), id=pedido_id)

    # 2. Lógica de autorización: ¿Es el dueño del pedido O tiene permisos de gestión?
    es_dueño = pedido.usuario == request.user
    es_gestor = request.user.has_perm('tienda.view_pedido')

    if not (es_dueño or es_gestor):
        # Si no cumple ninguna condición, se lanza un error 403 (Acceso Denegado).
        raise PermissionDenied

    # 3. Si tiene permiso, renderizamos la plantilla.
    return render(request, 'pedido_detalle.html', {'pedido': pedido})


# --- VISTAS CRUD PARA PRODUCTOS (CON PERMISOS) ---

class ProductoListView(PermissionRequiredMixin, ListView):
    """
    Vista para listar todos los productos en la gestión.
    Requiere el permiso 'tienda.view_producto'.
    """
    model = Producto
    template_name = 'gestion/producto_list.html'
    context_object_name = 'productos'
    permission_required = 'tienda.view_producto'
    paginate_by = 10  # 10 productos por página
    login_url = 'miapp:login'  # Redirige aquí si no está logueado

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Gestión de Productos'
        return context


class ProductoCreateView(PermissionRequiredMixin, CreateView):
    """
    Vista para crear un nuevo producto.
    Requiere el permiso 'tienda.add_producto'.
    """
    model = Producto
    form_class = ProductoForm
    template_name = 'gestion/producto_form.html'
    success_url = reverse_lazy('tienda:producto_list')
    permission_required = 'tienda.add_producto'
    login_url = 'miapp:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registrar Nuevo Producto'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Producto creado exitosamente.')
        return super().form_valid(form)


class ProductoUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Vista para actualizar un producto existente.
    Requiere el permiso 'tienda.change_producto'.
    """
    model = Producto
    form_class = ProductoForm
    template_name = 'gestion/producto_form.html'
    success_url = reverse_lazy('tienda:producto_list')
    permission_required = 'tienda.change_producto'
    login_url = 'miapp:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Actualizar Producto'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Producto actualizado exitosamente.')
        return super().form_valid(form)


class ProductoDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Vista para eliminar un producto.
    Requiere el permiso 'tienda.delete_producto'.
    """
    model = Producto
    template_name = 'gestion/producto_confirm_delete.html'
    success_url = reverse_lazy('tienda:producto_list')
    permission_required = 'tienda.delete_producto'
    login_url = 'miapp:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Confirmar Eliminación'
        return context

    def form_valid(self, form):
        # Usamos form_valid para añadir el mensaje de éxito antes de la redirección
        messages.success(
            self.request, f'Producto "{self.object.nombre}" eliminado exitosamente.')
        return super().form_valid(form)


# --- VISTAS DE GESTIÓN DE PEDIDOS ---

class PedidoGestionListView(PermissionRequiredMixin, ListView):
    """
    Vista para listar y gestionar todos los pedidos.
    Permite filtrar por estado y buscar por cliente o ID.
    """
    model = Pedido
    template_name = 'gestion/pedido_list.html'
    context_object_name = 'pedidos'
    permission_required = 'tienda.view_pedido'
    login_url = 'miapp:login'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().select_related('usuario')

        query = self.request.GET.get('q', '').strip()
        if query:
            # Construimos los filtros de búsqueda
            q_objects = Q(nombre_cliente__icontains=query) | Q(
                email__icontains=query)
            # Si el texto de búsqueda es un número, también buscamos por ID de pedido
            if query.isdigit():
                q_objects |= Q(id=query)
            queryset = queryset.filter(q_objects)

        self.estado_actual = self.request.GET.get('estado', 'INGRESADO')
        queryset = queryset.filter(estado=self.estado_actual)

        sort = self.request.GET.get('sort', '-fecha_pedido')
        queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Gestión de Pedidos'
        context['query'] = self.request.GET.get('q', '')
        context['estado_actual'] = self.estado_actual
        context['estados_posibles'] = Pedido.ESTADOS_PEDIDO
        # Convertimos el conteo a un diccionario para fácil acceso en la plantilla
        conteo_qs = Pedido.objects.values('estado').annotate(total=Count('id'))
        context['conteo_estados'] = {item['estado']
            : item['total'] for item in conteo_qs}
        return context


@login_required
@require_POST
@permission_required('tienda.change_pedido', raise_exception=True)
def cambiar_estado_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    nuevo_estado = request.POST.get('estado')

    if not nuevo_estado or nuevo_estado not in dict(Pedido.ESTADOS_PEDIDO):
        messages.error(
            request, ">_ ERROR: Debes seleccionar un estado válido antes de aplicar los cambios.")
        return redirect(request.META.get('HTTP_REFERER', reverse_lazy('tienda:pedido_gestion')))

    # --- NUEVA LÓGICA: Evitar retroceder el estado ---
    jerarquia_estados = {
        'INGRESADO': 1,
        'PAGADO': 2,
        'ENVIADO': 3,
        'ANULADO': 4  # Estado final
    }

    nivel_actual = jerarquia_estados.get(pedido.estado, 0)
    nivel_nuevo = jerarquia_estados.get(nuevo_estado, 0)

    if nivel_nuevo <= nivel_actual:
        # Permitir desanular solo si es Superusuario y el pedido estaba ANULADO
        if pedido.estado == 'ANULADO' and request.user.is_superuser:
            pass  # El superusuario está autorizado a saltar esta restricción
        else:
            messages.warning(
                request, f">_ ADVERTENCIA: Operación denegada. No es posible retroceder el pedido #{pedido.id} a un estado anterior.")
            return redirect(request.META.get('HTTP_REFERER', reverse_lazy('tienda:pedido_gestion')))

    # --- LÓGICA DE DES-ANULACIÓN (Verificar y descontar stock) ---
    if pedido.estado == 'ANULADO' and nuevo_estado != 'ANULADO':
        with transaction.atomic():
            stock_insuficiente = []
            productos_a_actualizar = []

            for item in pedido.items.all():
                if not item.producto:
                    stock_insuficiente.append(
                        f"{item.nombre_producto} (Eliminado del sistema)")
                    continue

                # Bloqueamos la fila temporalmente para evitar condiciones de carrera (Concurrencia)
                producto_db = Producto.objects.select_for_update().get(id=item.producto.id)
                if producto_db.stock < item.cantidad:
                    stock_insuficiente.append(
                        f"{producto_db.nombre} (Faltan {item.cantidad - producto_db.stock} und.)")
                else:
                    productos_a_actualizar.append((producto_db, item.cantidad))

            if stock_insuficiente:
                messages.error(
                    request, f">_ ERROR CRÍTICO: Stock insuficiente para reactivar el pedido. {', '.join(stock_insuficiente)}")
                return redirect(request.META.get('HTTP_REFERER', reverse_lazy('tienda:pedido_gestion')))

            # Si todos tienen stock suficiente, procedemos a descontar
            for producto, cantidad in productos_a_actualizar:
                producto.stock -= cantidad
                producto.save(update_fields=['stock'])

    pedido.estado = nuevo_estado
    pedido.save()
    messages.success(
        request, f"El estado del pedido #{pedido.id} ha sido actualizado a '{pedido.get_estado_display()}'.")

    return redirect(request.META.get('HTTP_REFERER', reverse_lazy('tienda:pedido_gestion')))


@login_required
def generar_factura_pdf(request, pedido_id):
    """
    Genera una factura en formato PDF para un pedido específico.
    """
    # 1. Obtener el pedido con sus items y productos relacionados para eficiencia
    pedido = get_object_or_404(
        Pedido.objects.prefetch_related('items__producto'), id=pedido_id)

    # --- LÓGICA DE AUTORIZACIÓN ---
    # Permitir si el usuario es el dueño del pedido, o si tiene permisos de gestión.
    es_dueño = pedido.usuario == request.user
    es_gestor = request.user.has_perm('tienda.view_pedido')

    if not (es_dueño or es_gestor):
        # Lanza un error 403 si el usuario no tiene permiso.
        raise PermissionDenied

    # 2. Renderizar la plantilla HTML a una cadena de texto
    html_string = render_to_string(
        'gestion/factura_template.html', {'pedido': pedido})

    # 3. Generar el PDF usando xhtml2pdf
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)

    if pdf.err:
        messages.error(request, "Error al generar la factura PDF.")
        return redirect(request.META.get('HTTP_REFERER', reverse_lazy('tienda:pedido_gestion')))

    # 4. Crear la respuesta HTTP con el tipo de contenido correcto para PDF
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_GatoPobre_#{pedido.id}.pdf"'

    return response
# --- VISTAS CRUD PARA CATEGORÍAS (CON PERMISOS) ---


class CategoriaListView(PermissionRequiredMixin, ListView):
    """
    Vista para listar todas las categorías en la gestión.
    Requiere el permiso 'tienda.view_categoria'.
    """
    model = Categoria
    template_name = 'gestion/categoria_list.html'
    context_object_name = 'categorias'
    permission_required = 'tienda.view_categoria'
    paginate_by = 10
    login_url = 'miapp:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Gestión de Categorías'
        return context


class CategoriaCreateView(PermissionRequiredMixin, CreateView):
    """
    Vista para crear una nueva categoría.
    Requiere el permiso 'tienda.add_categoria'.
    """
    model = Categoria
    form_class = CategoriaForm
    template_name = 'gestion/categoria_form.html'
    success_url = reverse_lazy('tienda:categoria_list')
    permission_required = 'tienda.add_categoria'
    login_url = 'miapp:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registrar Nueva Categoría'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Categoría creada exitosamente.')
        return super().form_valid(form)


class CategoriaUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Vista para actualizar una categoría existente.
    Requiere el permiso 'tienda.change_categoria'.
    """
    model = Categoria
    form_class = CategoriaForm
    template_name = 'gestion/categoria_form.html'
    success_url = reverse_lazy('tienda:categoria_list')
    permission_required = 'tienda.change_categoria'
    login_url = 'miapp:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Actualizar Categoría'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Categoría actualizada exitosamente.')
        return super().form_valid(form)


class CategoriaDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Vista para eliminar una categoría.
    Requiere el permiso 'tienda.delete_categoria'.
    """
    model = Categoria
    template_name = 'gestion/categoria_confirm_delete.html'
    success_url = reverse_lazy('tienda:categoria_list')
    permission_required = 'tienda.delete_categoria'
    login_url = 'miapp:login'

    def form_valid(self, form):
        messages.success(
            self.request, f'Categoría "{self.object.nombre}" eliminada.')
        return super().form_valid(form)
