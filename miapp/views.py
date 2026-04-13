"""
views.py para mi_projecto/miapp
"""
from django.contrib.auth.forms import PasswordChangeForm
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, update_session_auth_hash
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from .forms import ContactoModelForm, CustomUserCreationForm, ActualizarPerfilForm
from tienda.models import Pedido


# Create your views here.


def inicio(request):
    """Muestra la página de inicio con datos de contexto para el hero y las tarjetas de características."""
    mis_datos = {
        'titulo1': 'Desarrollo Core',
        'descripcion1': 'Forjamos la lógica de tu sistema con la eficiencia de Python y la arquitectura inquebrantable de Django.',
        'titulo2': 'Frontend & UI',
        'descripcion2': 'Interfaces ágiles, responsivas y de carga ultra rápida, optimizadas para producción mediante Bootstrap 5.',
        'titulo3': 'DevOps & Despliegue',
        'descripcion3': 'Arquitectura en contenedores y bases de datos MySQL para máxima seguridad, escalabilidad y un lanzamiento sin fisuras.',
        'mi_boton': 'Iniciar Conexión',
        'titulo_hero': 'Código limpio. Infraestructura robusta. Bienvenido a GatoPobreTECK.',
        'subtitulo_hero': '''Desarrollamos soluciones tecnológicas escalables. Desde la arquitectura del backend hasta el despliegue en producción, optimizamos cada línea de código para que tu proyecto domine la red.'''
    }

    return render(request, 'index.html', mis_datos)


def contacto(request):
    """
    Gestiona el formulario de contacto.

    - Si es GET, muestra el formulario vacío.
    - Si es POST y el formulario es válido, guarda el mensaje en la base de datos,
      muestra un mensaje de éxito y redirige.
    - Si es POST y el formulario no es válido, muestra los errores.
    """
    context = {}
    if request.method == 'POST':
        # Instanciamos el form con los datos que envió el usuario
        form = ContactoModelForm(request.POST)

        # Django valida automáticamente (ej: que el email tenga un @)
        if form.is_valid():
            # Guarda el objeto Contacto en la base de datos
            form.save()

            # Extraemos los datos limpios y seguros
            nombre = form.cleaned_data['nombre']
            messages.success(
                request, f'¡Excelente {nombre}! Hemos recibido tus datos correctamente.')
            # redireccion al formulario para evitar reenvio de formulario
            return redirect('miapp:contacto')
        else:
            messages.error(
                request, 'Hay errores en el formulario. Por favor, revísalos.')
    else:
        # Si entra por primera vez, mostramos el form vacío
        form = ContactoModelForm()

    context['form'] = form
    return render(request, 'contacto.html', context)


def politicas_privacidad(request):
    """Muestra la página estática de Políticas de Privacidad."""
    return render(request, 'politicas.html')


def register(request):
    """
    Gestiona el registro de nuevos usuarios.

    - Si es POST y el formulario es válido, crea el usuario, inicia su sesión
      y lo redirige al dashboard.
    - Si es GET, muestra el formulario de registro vacío.
    """
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("miapp:dashboard")
    else:
        form = CustomUserCreationForm()

    return render(request, "register.html", {"form": form})


class DashboardMixinView(LoginRequiredMixin, TemplateView):
    """Vista protegida que muestra el panel de control del usuario."""
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Lógica de Filtrado ---
        query = self.request.GET.get('q', '').strip()
        estado_filter = self.request.GET.get('estado', '').strip()

        # --- Lógica de Ordenamiento ---
        sort_param = self.request.GET.get('sort', '-fecha_pedido')
        valid_sort_fields = ['fecha_pedido',
                             '-fecha_pedido', 'total_pagado', '-total_pagado']
        if sort_param not in valid_sort_fields:
            sort_param = '-fecha_pedido'  # Default seguro

        # Iniciar queryset base
        pedidos_qs = self.request.user.pedidos.prefetch_related('items')

        # Aplicar filtros
        if query and query.isdigit():
            pedidos_qs = pedidos_qs.filter(id=query)

        if estado_filter:
            pedidos_qs = pedidos_qs.filter(estado=estado_filter)

        # Aplicar ordenamiento
        pedidos_qs = pedidos_qs.order_by(sort_param)

        context['total_pedidos'] = self.request.user.pedidos.count()

        # Paginación: 10 pedidos por página como máximo
        paginator = Paginator(pedidos_qs, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['pedidos'] = page_obj
        context['page_obj'] = page_obj

        # --- Pasar datos de ordenamiento y filtrado a la plantilla ---
        context['current_sort'] = sort_param
        context['next_sort_fecha'] = '-fecha_pedido' if sort_param == 'fecha_pedido' else 'fecha_pedido'
        context['next_sort_total'] = '-total_pagado' if sort_param == 'total_pagado' else 'total_pagado'
        context['query'] = query
        context['estado_filter'] = estado_filter
        context['estados_posibles'] = Pedido.ESTADOS_PEDIDO
        return context


@login_required
def actualizar_perfil(request):
    """
    Permite al usuario autenticado actualizar su perfil.

    Obtiene el perfil del usuario y procesa el formulario de actualización,
    incluyendo la subida de una nueva imagen de avatar.
    """
    # Obtenemos el perfil del usuario actual usando el related_name 'perfil'
    perfil = request.user.perfil

    if request.method == 'POST':
        # IMPORTANTE: Pasar request.FILES para que procese la nueva imagen
        form = ActualizarPerfilForm(
            request.POST, request.FILES, instance=perfil)

        if form.is_valid():
            form.save()
            messages.success(
                request, '¡Tu perfil ha sido actualizado correctamente!')
            # Cambia esto por la URL a la que quieras redirigir
            return redirect('miapp:dashboard')
    else:
        # Si es un GET, cargamos el formulario con los datos actuales del perfil
        form = ActualizarPerfilForm(instance=perfil)

    contexto = {
        'form': form
    }
    return render(request, 'actualizar_perfil.html', contexto)


@login_required
def cambiar_password(request):
    """
    Permite al usuario autenticado cambiar su contraseña.

    Utiliza el formulario `PasswordChangeForm` de Django y se asegura de que
    la sesión del usuario se mantenga activa después del cambio.
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Esta línea es VITAL: evita que Django cierre la sesión al cambiar la clave
            update_session_auth_hash(request, user)
            messages.success(
                request, ">_ PROTOCOLO DE SEGURIDAD: CLAVE ENCRIPTADA Y ACTUALIZADA.")
            return redirect('miapp:dashboard')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'cambiar_password.html', {'form': form})
