from django.urls import path
from . import views


app_name = 'tienda'

urlpatterns = [

    path('', views.inicio, name="tienda"),
    # Ruta para el detalle, recibe un número entero que es el ID del producto
    path('producto/<int:producto_id>/',
         views.producto_detalle, name='producto_detalle'),

    # Ruta oculta (sin plantilla) que solo procesa el formulario de agregar al carro
    path('agregar/<int:producto_id>/', views.agregar_carro, name='agregar_carro'),
    path('carrito/', views.ver_carro, name='ver_carro'),
    path('eliminar/<int:producto_id>/',
         views.eliminar_producto, name='eliminar_producto'),
    path('vaciar/', views.vaciar_carro, name='vaciar_carro'),
    path('actualizar_carro/<int:producto_id>/',
         views.actualizar_cantidad_carro, name='actualizar_carro'),

    path('checkout/', views.checkout, name='checkout'),
    path('exito/', views.exito, name='exito'),

    # URLs para el CRUD de Productos (protegido por permisos)
    path('gestion/', views.ProductoListView.as_view(), name='producto_list'),
    path('gestion/nuevo/', views.ProductoCreateView.as_view(),
         name='producto_create'),
    path('gestion/editar/<int:pk>/',
         views.ProductoUpdateView.as_view(), name='producto_update'),
    path('gestion/eliminar/<int:pk>/',
         views.ProductoDeleteView.as_view(), name='producto_delete'),

    # URLs para la Gestión de Pedidos
    path('gestion/pedidos/', views.PedidoGestionListView.as_view(),
         name='pedido_gestion'),
    path('gestion/pedidos/cambiar-estado/<int:pedido_id>/',
         views.cambiar_estado_pedido, name='cambiar_estado_pedido'),
    path('gestion/pedidos/factura/<int:pedido_id>/',
         views.generar_factura_pdf, name='generar_factura_pdf'),

    # URLs para el CRUD de Categorías (protegido por permisos)
    path('gestion/categorias/', views.CategoriaListView.as_view(),
         name='categoria_list'),
    path('gestion/categorias/nueva/',
         views.CategoriaCreateView.as_view(), name='categoria_create'),
    path('gestion/categorias/editar/<int:pk>/',
         views.CategoriaUpdateView.as_view(), name='categoria_update'),
    path('gestion/categorias/eliminar/<int:pk>/',
         views.CategoriaDeleteView.as_view(), name='categoria_delete'),

    path('pedido/<int:pedido_id>/',
         views.pedido_detalle, name='pedido_detalle')
]
